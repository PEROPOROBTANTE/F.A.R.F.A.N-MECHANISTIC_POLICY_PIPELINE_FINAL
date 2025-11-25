"""
Factory module for core module initialization with dependency injection.

This module is responsible for:
1. Reading data from disk (catalogs, schemas, documents, etc.)
2. Constructing InputContracts for core modules
3. Initializing core modules with injected dependencies
4. Managing I/O operations so core modules remain pure

Architectural Pattern:
- Factory reads from disk
- Factory constructs contracts
- Factory injects dependencies into core modules
- Core modules remain I/O-free and testable

QUESTIONNAIRE INTEGRITY PROTOCOL:
- Questionnaire loading is now in questionnaire.py module
- All consumers MUST import from questionnaire module
- Use questionnaire.load_questionnaire() which returns CanonicalQuestionnaire

Version: 3.0.0
Status: Refactored to be fully aligned with questionnaire.py
"""

import copy
import json
import logging
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from ..contracts import (
    CDAFFrameworkInputContract,
    ContradictionDetectorInputContract,
    DocumentData,
    EmbeddingPolicyInputContract,
    PDETAnalyzerInputContract,
    PolicyProcessorInputContract,
    SemanticAnalyzerInputContract,
    SemanticChunkingInputContract,
    TeoriaCambioInputContract,
)
from .core import MethodExecutor
from .executor_config import ExecutorConfig
from .questionnaire import (
    EXPECTED_HASH,
    EXPECTED_MACRO_QUESTION_COUNT,
    EXPECTED_MESO_QUESTION_COUNT,
    EXPECTED_MICRO_QUESTION_COUNT,
    EXPECTED_TOTAL_QUESTION_COUNT,
    QUESTIONNAIRE_PATH,
    CanonicalQuestionnaire,
    load_questionnaire,
)

logger = logging.getLogger(__name__)

# Canonical repository root - single source of truth for all file paths
_REPO_ROOT = Path(__file__).resolve().parents[4]
_DEFAULT_DATA_DIR = _REPO_ROOT / "data"

@dataclass(frozen=True)
class ProcessorBundle:
    """Aggregated orchestrator dependencies built by the factory.

    Attributes:
        method_executor: Preconfigured :class:`MethodExecutor` instance ready for
            execution.
        questionnaire: The canonical, immutable questionnaire object.
        factory: The :class:`CoreModuleFactory` used to construct ancillary
            input contracts for downstream processors.
        signal_registry: Optional signal registry populated during factory wiring.
        executor_config: Canonical :class:`ExecutorConfig` used for all question
            executors.
    """

    method_executor: MethodExecutor
    questionnaire: CanonicalQuestionnaire
    factory: "CoreModuleFactory"
    signal_registry: Any | None
    executor_config: ExecutorConfig

# ============================================================================
# FILE I/O OPERATIONS
# ============================================================================

def load_catalog(path: Path | None = None) -> dict[str, Any]:
    """Load method catalog JSON file.

    Args:
        path: Path to catalog file. Defaults to config/rules/METODOS/catalogo_completo_canonico.json
              relative to repository root.

    Returns:
        Loaded catalog data

    Raises:
        FileNotFoundError: If catalog file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    if path is None:
        path = _REPO_ROOT / "config" / "rules" / "METODOS" / "catalogo_completo_canonico.json"

    logger.info(f"Loading catalog from {path}")

    with open(path, encoding='utf-8') as f:
        return json.load(f)

def load_method_map(path: Path | None = None) -> dict[str, Any]:
    """Load method-class mapping JSON file.

    Args:
        path: Path to method map file. Defaults to COMPLETE_METHOD_CLASS_MAP.json
              relative to repository root.

    Returns:
        Loaded method map data

    Raises:
        FileNotFoundError: If method map file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    if path is None:
        path = _REPO_ROOT / "COMPLETE_METHOD_CLASS_MAP.json"

    logger.info(f"Loading method map from {path}")

    with open(path, encoding='utf-8') as f:
        return json.load(f)

def get_canonical_dimensions(questionnaire_path: Path | None = None) -> dict[str, dict[str, str]]:
    """
    Get canonical dimension definitions from questionnaire monolith.

    Args:
        questionnaire_path: Optional path to questionnaire file (IGNORED for integrity)

    Returns:
        Dictionary mapping dimension keys (D1-D6) to dimension info.
    """
    if questionnaire_path is not None:
        logger.warning(
            "get_canonical_dimensions: questionnaire_path parameter is IGNORED. "
            "Dimensions always load from canonical questionnaire path for integrity."
        )

    canonical = load_questionnaire()

    if 'canonical_notation' not in canonical.data:
        raise KeyError("canonical_notation section missing from questionnaire")

    if 'dimensions' not in canonical.data['canonical_notation']:
        raise KeyError("dimensions section missing from canonical_notation")

    return copy.deepcopy(canonical.data['canonical_notation']['dimensions'])

def get_canonical_policy_areas(questionnaire_path: Path | None = None) -> dict[str, dict[str, str]]:
    """
    Get canonical policy area definitions from questionnaire monolith.

    Args:
        questionnaire_path: Optional path to questionnaire file (IGNORED for integrity)

    Returns:
        Dictionary mapping policy area codes (PA01-PA10) to policy area info.
    """
    if questionnaire_path is not None:
        logger.warning(
            "get_canonical_policy_areas: questionnaire_path parameter is IGNORED. "
            "Policy areas always load from canonical questionnaire path for integrity."
        )

    canonical = load_questionnaire()

    if 'canonical_notation' not in canonical.data:
        raise KeyError("canonical_notation section missing from questionnaire")

    if 'policy_areas' not in canonical.data['canonical_notation']:
        raise KeyError("policy_areas section missing from canonical_notation")

    return copy.deepcopy(canonical.data['canonical_notation']['policy_areas'])

def load_schema(path: Path | None = None) -> dict[str, Any]:
    """Load questionnaire schema JSON file.

    Args:
        path: Path to schema file. Defaults to schemas/questionnaire_monolith.schema.json
              relative to repository root.
    """
    if path is None:
        path = _REPO_ROOT / "schemas" / "questionnaire_monolith.schema.json"

    logger.info(f"Loading schema from {path}")

    with open(path, encoding='utf-8') as f:
        return json.load(f)

def load_document(file_path: Path) -> DocumentData:
    """Load a document and construct DocumentData contract."""
    logger.info(f"Loading document from {file_path}")

    with open(file_path, encoding='utf-8') as f:
        raw_text = f.read()

    sentences = [s.strip() for s in raw_text.split('.') if s.strip()]

    return DocumentData(
        raw_text=raw_text,
        sentences=sentences,
        tables=[],
        metadata={
            'file_path': str(file_path),
            'file_name': file_path.name,
            'num_sentences': len(sentences),
        }
    )

def save_results(results: dict[str, Any], output_path: Path) -> None:
    """Save analysis results to file."""
    logger.info(f"Saving results to {output_path}")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

# ============================================================================
# CONTRACT CONSTRUCTORS
# ============================================================================


def construct_semantic_analyzer_input(document: DocumentData, **kwargs) -> SemanticAnalyzerInputContract:
    """Constructs the input for the SemanticAnalyzer."""
    return SemanticAnalyzerInputContract(
        text=document['raw_text'],
        segments=document['sentences'],
        ontology_params=kwargs.get('ontology_params', {})
    )

def construct_cdaf_input(document: DocumentData, **kwargs) -> CDAFFrameworkInputContract:
    """Constructs the input for the CDAFFramework."""
    return CDAFFrameworkInputContract(
        document_text=document['raw_text'],
        plan_metadata=document['metadata'],
        config=kwargs.get('config', {})
    )

def construct_pdet_input(document: DocumentData, **kwargs) -> PDETAnalyzerInputContract:
    """Constructs the input for the PDETAnalyzer."""
    return PDETAnalyzerInputContract(
        document_content=document['raw_text'],
        extract_tables=kwargs.get('extract_tables', True),
        config=kwargs.get('config', {})
    )

def construct_teoria_cambio_input(document: DocumentData, **kwargs) -> TeoriaCambioInputContract:
    """Constructs the input for the TeoriaCambio."""
    return TeoriaCambioInputContract(
        document_text=document['raw_text'],
        strategic_goals=kwargs.get('strategic_goals', []),
        config=kwargs.get('config', {})
    )

def construct_contradiction_detector_input(document: DocumentData, **kwargs) -> ContradictionDetectorInputContract:
    """Constructs the input for the ContradictionDetector."""
    return ContradictionDetectorInputContract(
        text=document['raw_text'],
        plan_name=document['metadata'].get('file_name', 'Unknown'),
        dimension=kwargs.get('dimension'),
        config=kwargs.get('config', {})
    )

def construct_embedding_policy_input(document: DocumentData, **kwargs) -> EmbeddingPolicyInputContract:
    """Constructs the input for the EmbeddingPolicy."""
    return EmbeddingPolicyInputContract(
        text=document['raw_text'],
        dimensions=kwargs.get('dimensions', []),
        model_config=kwargs.get('model_config', {})
    )

def construct_semantic_chunking_input(document: DocumentData, **kwargs) -> SemanticChunkingInputContract:
    """Constructs the input for the SemanticChunking."""
    return SemanticChunkingInputContract(
        text=document['raw_text'],
        preserve_structure=kwargs.get('preserve_structure', True),
        config=kwargs.get('config', {})
    )

def construct_policy_processor_input(document: DocumentData, **kwargs) -> PolicyProcessorInputContract:
    """Constructs the input for the PolicyProcessor."""
    return PolicyProcessorInputContract(
        data={},
        text=document['raw_text'],
        sentences=document['sentences'],
        tables=document['tables'],
        config=kwargs.get('config', {})
    )

# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

class CoreModuleFactory:
    """Factory for constructing core modules with injected dependencies."""

    def __init__(self, data_dir: Path | None = None) -> None:
        """Initialize factory."""
        self.data_dir = data_dir or _DEFAULT_DATA_DIR
        self.questionnaire_cache: CanonicalQuestionnaire | None = None
        self.catalog_cache: dict[str, Any] | None = None
        self._lock = threading.Lock()

    def get_questionnaire(self) -> CanonicalQuestionnaire:
        """Get the canonical questionnaire object (cached)."""
        with self._lock:
            if self.questionnaire_cache is None:
                questionnaire_path = self.data_dir / "questionnaire_monolith.json"
                canonical_q = load_questionnaire(questionnaire_path)
                self.questionnaire_cache = canonical_q
                logger.info(
                    "factory_loaded_questionnaire",
                    sha256=canonical_q.sha256[:16] + "...",
                    question_count=canonical_q.total_question_count,
                )
            return self.questionnaire_cache

    @property
    def catalog(self) -> dict[str, Any]:
        """Get method catalog data (cached)."""
        with self._lock:
            if self.catalog_cache is None:
                self.catalog_cache = load_catalog()
            return self.catalog_cache

    def load_document(self, file_path: Path) -> DocumentData:
        """Load document and return structured data."""
        return load_document(file_path)

    def save_results(self, results: dict[str, Any], output_path: Path) -> None:
        """Save analysis results."""
        save_results(results, output_path)

    def load_catalog(self, path: Path | None = None) -> dict[str, Any]:
        """Load method catalog JSON file."""
        return load_catalog(path)

    # Contract constructor methods
    construct_semantic_analyzer_input = construct_semantic_analyzer_input
    construct_cdaf_input = construct_cdaf_input
    construct_pdet_input = construct_pdet_input
    construct_teoria_cambio_input = construct_teoria_cambio_input
    construct_contradiction_detector_input = construct_contradiction_detector_input
    construct_embedding_policy_input = construct_embedding_policy_input
    construct_semantic_chunking_input = construct_semantic_chunking_input
    construct_policy_processor_input = construct_policy_processor_input

def build_processor(
    *,
    questionnaire_path: Path | None = None,
    data_dir: Path | None = None,
    factory: Optional["CoreModuleFactory"] = None,
    enable_signals: bool = True,
    executor_config: ExecutorConfig | None = None,
) -> ProcessorBundle:
    """Create a processor bundle with orchestrator dependencies wired together."""

    # Runtime type checks
    if questionnaire_path is not None and not isinstance(questionnaire_path, Path):
        raise TypeError(f"questionnaire_path must be Path or None, got {type(questionnaire_path).__name__}.")
    if data_dir is not None and not isinstance(data_dir, Path):
        raise TypeError(f"data_dir must be Path or None, got {type(data_dir).__name__}")
    if factory is not None and not isinstance(factory, CoreModuleFactory):
        raise TypeError(f"factory must be CoreModuleFactory or None, got {type(factory).__name__}")
    if not isinstance(enable_signals, bool):
        raise TypeError(f"enable_signals must be bool, got {type(enable_signals).__name__}")
    if executor_config is not None and not isinstance(executor_config, ExecutorConfig):
        raise TypeError(f"executor_config must be ExecutorConfig or None, got {type(executor_config).__name__}")

    core_factory = factory or CoreModuleFactory(data_dir=data_dir)
    effective_config = executor_config or ExecutorConfig()

    if questionnaire_path:
        canonical_q = load_questionnaire(questionnaire_path)
        core_factory.questionnaire_cache = canonical_q
        logger.info(
            "build_processor_using_canonical_loader",
            path=str(questionnaire_path),
            sha256=canonical_q.sha256[:16] + "...",
            question_count=canonical_q.total_question_count,
        )
    else:
        canonical_q = core_factory.get_questionnaire()

    # Build signal infrastructure if enabled
    signal_registry = None
    if enable_signals:
        try:
            from .bayesian_module_factory import BayesianModuleFactory as SignalFactory

            signal_factory = SignalFactory(
                questionnaire_data=canonical_q.data,  # Pass the immutable data view
                enable_signals=True,
            )
            signal_registry = signal_factory._signal_registry

            logger.info(
                "signals_enabled_in_processor",
                enabled=True,
                registry_size=len(signal_registry._cache) if signal_registry else 0,
            )
        except Exception as e:
            logger.warning(
                "signal_initialization_failed",
                error=str(e),
                fallback="continuing without signals"
            )
            signal_registry = None

    executor = MethodExecutor(signal_registry=signal_registry)

    return ProcessorBundle(
        method_executor=executor,
        questionnaire=canonical_q,
        factory=core_factory,
        signal_registry=signal_registry,
        executor_config=effective_config,
    )

# ============================================================================
# MIGRATION HELPERS
# ============================================================================

def migrate_io_from_module(module_name: str, line_numbers: list[int]) -> None:
    """Helper to track I/O migration progress."""
    logger.info(
        f"Migrating {len(line_numbers)} I/O operations from {module_name}: "
        f"lines {line_numbers}"
    )

__all__ = [
    # Questionnaire integrity types and constants
    'CanonicalQuestionnaire',
    'EXPECTED_HASH',
    'EXPECTED_MACRO_QUESTION_COUNT',
    'EXPECTED_MICRO_QUESTION_COUNT',
    'EXPECTED_MESO_QUESTION_COUNT',
    'EXPECTED_TOTAL_QUESTION_COUNT',
    'QUESTIONNAIRE_PATH',
    'load_questionnaire',
    # Factory classes
    'CoreModuleFactory',
    'ProcessorBundle',
    # Other loaders
    'load_catalog',
    'load_method_map',
    'get_canonical_dimensions',
    'get_canonical_policy_areas',
    'load_schema',
    'load_document',
    'save_results',
    # Contract constructors
    'construct_semantic_analyzer_input',
    'construct_cdaf_input',
    'construct_pdet_input',
    'construct_teoria_cambio_input',
    'construct_contradiction_detector_input',
    'construct_embedding_policy_input',
    'construct_semantic_chunking_input',
    'construct_policy_processor_input',
    # Builder
    'build_processor',
]
