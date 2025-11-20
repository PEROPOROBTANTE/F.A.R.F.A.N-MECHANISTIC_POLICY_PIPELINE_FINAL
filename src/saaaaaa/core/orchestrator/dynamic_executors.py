"""
Dynamic Executor Factory - Runtime Generation from Logic JSON
==============================================================

Generates executor classes dynamically from executor_logic.json at runtime.
No hardcoded executor classes - all driven by canonical notation.

Architecture:
- Reads executor_logic.json
- Generates executor classes on-the-fly
- Integrates with AnswerAssembler
- Wires to core orchestrator

Author: F.A.R.F.A.N Team
Date: 2025-11-20
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class DynamicExecutorFactory:
    """
    Factory that generates executor classes dynamically from executor_logic.json.
    """

    def __init__(self, logic_path: Optional[str] = None):
        """
        Initialize factory with executor logic.

        Args:
            logic_path: Path to executor_logic.json (defaults to config/executor_logic.json)
        """
        self.logic_path = logic_path or self._get_default_logic_path()
        self.logic = self._load_logic()
        self.executors_cache = {}

    def _get_default_logic_path(self) -> str:
        """Get default path for executor logic JSON."""
        base_path = Path(__file__).parent.parent.parent.parent
        return str(base_path / "config" / "executor_logic.json")

    def _load_logic(self) -> Dict[str, Any]:
        """Load executor logic from JSON."""
        try:
            with open(self.logic_path, 'r', encoding='utf-8') as f:
                logic = json.load(f)
            logger.info(f"Loaded executor logic v{logic.get('version')}: {len(logic['executors'])} executors")
            return logic
        except FileNotFoundError:
            logger.error(f"Executor logic not found: {self.logic_path}")
            return {"executors": {}}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing executor logic: {e}")
            return {"executors": {}}

    def get_executor_class(self, question_id: str):
        """
        Get or create executor class for question_id.

        Args:
            question_id: Question ID (e.g., "D1-Q1")

        Returns:
            Executor class for the question
        """
        # Check cache first
        if question_id in self.executors_cache:
            return self.executors_cache[question_id]

        # Get logic for this question
        executor_logic = self.logic['executors'].get(question_id)
        if not executor_logic:
            raise ValueError(f"No executor logic found for {question_id}")

        # Generate executor class dynamically
        executor_class = self._create_executor_class(question_id, executor_logic)

        # Cache it
        self.executors_cache[question_id] = executor_class

        return executor_class

    def _create_executor_class(self, question_id: str, logic: Dict[str, Any]):
        """
        Dynamically create an executor class.

        Args:
            question_id: Question ID
            logic: Executor logic dictionary

        Returns:
            Dynamically generated executor class
        """
        # Import base class - delayed to avoid circular imports and heavy dependencies
        try:
            from .executors import AdvancedDataFlowExecutor
        except ImportError as e:
            logger.error(f"Failed to import AdvancedDataFlowExecutor: {e}")
            raise

        # Extract method sequence
        method_sequence = [
            (m['class'], m['method'])
            for m in logic['method_sequence']
        ]

        # Create class dynamically
        class_name = question_id.replace('-', 'Q') + '_Executor'
        question_text = logic.get('question_text', question_id)[:80]

        # Define methods for the dynamic class
        def __init__(
            self,
            method_executor,
            signal_registry=None,
            config=None,
            calibration_orchestrator=None
        ):
            """Initialize dynamic executor."""
            # Import here to avoid circular imports
            from .executor_config import ExecutorConfig

            if config is None:
                config = ExecutorConfig()

            AdvancedDataFlowExecutor.__init__(
                self,
                method_executor,
                signal_registry,
                config,
                calibration_orchestrator
            )
            self._question_id = question_id
            self._method_sequence = method_sequence
            self._validate_method_sequences()
            self._validate_calibrations()

        def _get_method_sequence(self) -> List[Tuple[str, str]]:
            """Return canonical method sequence."""
            return self._method_sequence

        def execute(self, doc, method_executor):
            """
            Execute method sequence and assemble answer.

            Args:
                doc: Document to analyze
                method_executor: Method executor instance

            Returns:
                Dict with method_results and assembled answer
            """
            from .answer_assembler import AnswerAssembler

            # Execute method sequence
            method_seq = self._get_method_sequence()
            method_results = self.execute_with_optimization(doc, method_executor, method_seq)

            # Assemble doctoral answer
            assembler = AnswerAssembler()
            answer = assembler.assemble_answer(
                question_id=self._question_id,
                method_results=method_results,
                policy_area=getattr(doc, 'policy_area', None)
            )

            return {
                "method_results": method_results,
                "answer": answer
            }

        def _extract(self, results):
            """Extract values from results."""
            vals = [v for v in results.values() if v is not None]
            return vals[:4] if vals else []

        # Create the class dynamically
        DynamicExecutorClass = type(
            class_name,
            (AdvancedDataFlowExecutor,),
            {
                '__init__': __init__,
                '_get_method_sequence': _get_method_sequence,
                'execute': execute,
                '_extract': _extract,
                '__doc__': f"{question_id}: {question_text}",
                '__module__': __name__,
            }
        )

        return DynamicExecutorClass

    def get_all_executors(self) -> Dict[str, Any]:
        """
        Get all executor classes as a dictionary.

        Returns:
            Dict mapping question IDs to executor classes (ready for orchestrator)
        """
        all_executors = {}

        for question_id in self.logic['executors'].keys():
            try:
                executor_class = self.get_executor_class(question_id)
                all_executors[question_id] = executor_class
                logger.debug(f"Generated executor: {question_id}")
            except Exception as e:
                logger.error(f"Failed to generate executor for {question_id}: {e}")

        logger.info(f"Generated {len(all_executors)} executor classes dynamically")
        return all_executors


# Global factory instance
_factory = None


def get_factory() -> DynamicExecutorFactory:
    """Get or create global factory instance."""
    global _factory
    if _factory is None:
        _factory = DynamicExecutorFactory()
    return _factory


def get_all_executors() -> Dict[str, Any]:
    """
    Get all executor classes for orchestrator wiring.

    This is the main entry point for the orchestrator.

    Returns:
        Dict mapping question IDs to executor classes
    """
    factory = get_factory()
    return factory.get_all_executors()


def get_executor(question_id: str):
    """
    Get specific executor class.

    Args:
        question_id: Question ID (e.g., "D1-Q1")

    Returns:
        Executor class
    """
    factory = get_factory()
    return factory.get_executor_class(question_id)


# Expose all executors as module-level attributes for backward compatibility
def __getattr__(name: str):
    """
    Dynamic attribute access for backward compatibility.

    Allows: from .dynamic_executors import D1Q1_Executor
    """
    if name.endswith('_Executor'):
        # Convert D1Q1_Executor to D1-Q1
        question_id = name.replace('_Executor', '').replace('Q', '-Q')
        try:
            return get_executor(question_id)
        except ValueError:
            raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
