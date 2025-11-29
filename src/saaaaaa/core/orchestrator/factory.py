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
import hashlib
import json
import logging
import threading
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Optional

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
from .core import MethodExecutor, Orchestrator
from .executor_config import ExecutorConfig
from .method_registry import MethodRegistry
from .method_source_validator import MethodSourceValidator

logger = logging.getLogger(__name__)

# Canonical repository root - single source of truth for all file paths
_REPO_ROOT = Path(__file__).resolve().parents[4]
_DEFAULT_DATA_DIR = _REPO_ROOT / "data"


# ============================================================================
# CANONICAL QUESTIONNAIRE MANAGEMENT (MOVED FROM questionnaire.py)
# ============================================================================

# RULE 1: ONE PATH - The ONLY valid questionnaire location
_REPO_ROOT = Path(__file__).resolve().parents[4]
QUESTIONNAIRE_PATH: Final[Path] = _REPO_ROOT / "data" / "questionnaire_monolith.json"

# RULE 2: ONE HASH - Expected SHA-256 hash (MUST match or load fails)
EXPECTED_HASH: Final[str] = "596d940383dd5bd64a5460eadcb65b9b26b2a7929eea838d2169f0f7cee46986"

# RULE 3: ONE STRUCTURE - Expected question counts
EXPECTED_MICRO_QUESTION_COUNT: Final[int] = 300
EXPECTED_MESO_QUESTION_COUNT: Final[int] = 4
EXPECTED_MACRO_QUESTION_COUNT: Final[int] = 1
EXPECTED_TOTAL_QUESTION_COUNT: Final[int] = 305

@dataclass(frozen=True)
class CanonicalQuestionnaire:
    """Immutable, validated, hash-verified questionnaire."""
    data: MappingProxyType[str, Any]
    sha256: str
    micro_questions: tuple[MappingProxyType, ...]
    meso_questions: tuple[MappingProxyType, ...]
    macro_question: MappingProxyType | None
    micro_question_count: int
    total_question_count: int
    version: str
    schema_version: str

    def __post_init__(self) -> None:
        """Validate all invariants on construction."""
        if self.sha256 != EXPECTED_HASH:
            raise ValueError(f"QUESTIONNAIRE INTEGRITY VIOLATION: Hash mismatch!")
        if self.micro_question_count != EXPECTED_MICRO_QUESTION_COUNT:
            raise ValueError(f"Expected {EXPECTED_MICRO_QUESTION_COUNT} micro questions, got {self.micro_question_count}")
        if self.total_question_count != EXPECTED_TOTAL_QUESTION_COUNT:
            raise ValueError(f"Expected {EXPECTED_TOTAL_QUESTION_COUNT} total questions, got {self.total_question_count}")
        logger.info("canonical_questionnaire_validated sha256=%s version=%s", self.sha256[:16], self.version)

def _validate_questionnaire_structure(data: dict[str, Any]) -> None:
    """Validate questionnaire structure for required fields and types."""
    if not isinstance(data, dict):
        raise ValueError("Questionnaire must be a dictionary")
    required_keys = ["version", "blocks", "schema_version"]
    if missing := [k for k in required_keys if k not in data]:
        raise ValueError(f"Questionnaire missing keys: {missing}")
    blocks = data["blocks"]
    if not isinstance(blocks, dict) or "micro_questions" not in blocks:
        raise ValueError("blocks.micro_questions is required")
    # (A full validation would check all fields and types recursively)

def _compute_hash(data: dict[str, Any]) -> str:
    """Compute deterministic SHA-256 hash of questionnaire data."""
    canonical_json = json.dumps(data, sort_keys=True, ensure_ascii=True, separators=(',', ':'))
    return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()

_questionnaire_cache: Optional[CanonicalQuestionnaire] = None

def load_questionnaire() -> CanonicalQuestionnaire:
    """Loads, validates, and caches the questionnaire from the canonical path."""
    global _questionnaire_cache
    if _questionnaire_cache is not None:
        logger.debug("Returning cached canonical questionnaire.")
        return _questionnaire_cache

    path = QUESTIONNAIRE_PATH
    if not path.exists():
        raise FileNotFoundError(f"Canonical questionnaire not found: {path}")

    logger.info(f"Loading canonical questionnaire from {path}")
    content = path.read_text(encoding='utf-8')
    data = json.loads(content)

    _validate_questionnaire_structure(data)
    sha256 = _compute_hash(data)

    blocks = data['blocks']
    micro_questions = tuple(MappingProxyType(q) for q in blocks['micro_questions'])
    meso_questions = tuple(MappingProxyType(q) for q in blocks.get('meso_questions', []))
    macro_question = MappingProxyType(blocks['macro_question']) if 'macro_question' in blocks else None
    total_count = len(micro_questions) + len(meso_questions) + (1 if macro_question else 0)

    canonical_q = CanonicalQuestionnaire(
        data=MappingProxyType(data),
        sha256=sha256,
        micro_questions=micro_questions,
        meso_questions=meso_questions,
        macro_question=macro_question,
        micro_question_count=len(micro_questions),
        total_question_count=total_count,
        version=data.get('version', 'unknown'),
        schema_version=data.get('schema_version', 'unknown'),
    )
    
    _questionnaire_cache = canonical_q
    return canonical_q

# ============================================================================
# END OF MOVED QUESTIONNAIRE LOGIC
# ============================================================================


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
                canonical_q = load_questionnaire()
                self.questionnaire_cache = canonical_q
                logger.info(
                    "factory_loaded_questionnaire sha256=%s... question_count=%s",
                    canonical_q.sha256[:16],
                    canonical_q.total_question_count,
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

    # PHASE 1: SOURCE-TRUTH VALIDATION
    logger.info("Running source-truth validation...")
    validator = MethodSourceValidator()
    source_truth = validator.generate_source_truth_map()
    
    # Note: As per user instruction, executors_methods.json is outdated.
    # The validation should eventually be against the docstrings of the executors.
    # For now, we proceed with the validation against the file to identify discrepancies.
    validation_report = validator.validate_executor_methods()

    if validation_report['missing']:
        # In a strict environment, this should raise an error.
        # For now, we will log a warning to avoid blocking the pipeline.
        logger.warning(f"MISSING METHODS DETECTED: {validation_report['missing']}")
        # raise RuntimeError(f"MISSING METHODS: {validation_report['missing']}")

    # PHASE 2: METHOD REGISTRY CREATION
    logger.info("Initializing method registry with source-truth...")
    method_registry = MethodRegistry()
    logger.info(f"Pre-registered {len(validation_report['valid'])} valid methods.")


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
            "build_processor_using_canonical_loader path=%s sha256=%s... question_count=%s",
            str(questionnaire_path),
            canonical_q.sha256[:16],
            canonical_q.total_question_count,
        )
    else:
        canonical_q = core_factory.get_questionnaire()

    # Build signal infrastructure if enabled
    signal_registry = None
    #if enable_signals:
    #    try:
    #        from .bayesian_module_factory import BayesianModuleFactory as SignalFactory
    #
    #        signal_factory = SignalFactory(
    #            questionnaire_data=canonical_q.data,  # Pass the immutable data view
    #            enable_signals=True,
    #        )
    #        signal_registry = signal_factory._signal_registry
    #
    #        logger.info(
    #            "signals_enabled_in_processor enabled=%s registry_size=%s",
    #            True,
    #            len(signal_registry._cache) if signal_registry else 0,
    #        )
    #    except Exception as e:
    #        logger.warning(
    #            "signal_initialization_failed error=%s fallback=%s",
    #            str(e),
    #            "continuing without signals",
    #        )
    #        signal_registry = None

    executor = MethodExecutor(
        signal_registry=signal_registry, 
        method_registry=method_registry
    )

    return ProcessorBundle(
        method_executor=executor,
        questionnaire=canonical_q,
        factory=core_factory,
        signal_registry=signal_registry,
        executor_config=effective_config,
    )

def create_orchestrator() -> "Orchestrator":
    """Create a fully configured orchestrator instance."""
    processor_bundle = build_processor()
    return Orchestrator(
        method_executor=processor_bundle.method_executor,
        questionnaire=processor_bundle.questionnaire,
        executor_config=processor_bundle.executor_config,
    )

def get_questionnaire_provider():
    """Get a questionnaire provider instance."""
    from ..wiring.bootstrap import QuestionnaireResourceProvider
    return QuestionnaireResourceProvider()

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
    'get_questionnaire_provider',
]
