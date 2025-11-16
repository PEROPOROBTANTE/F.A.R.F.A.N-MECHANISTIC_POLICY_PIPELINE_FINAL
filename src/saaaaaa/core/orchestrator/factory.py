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

Version: 2.0.0
Status: Questionnaire module refactored to questionnaire.py
"""

import copy
import json
import logging
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
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
from . import get_questionnaire_provider
from .core import MethodExecutor
from .questionnaire import (
    CanonicalQuestionnaire,
    EXPECTED_HASH,
    EXPECTED_MACRO_QUESTION_COUNT,
    EXPECTED_MICRO_QUESTION_COUNT,
    EXPECTED_MESO_QUESTION_COUNT,
    EXPECTED_TOTAL_QUESTION_COUNT,
    QUESTIONNAIRE_PATH,
    load_questionnaire,
)

logger = logging.getLogger(__name__)

# Canonical repository root - single source of truth for all file paths
_REPO_ROOT = Path(__file__).resolve().parents[4]
_DEFAULT_DATA_DIR = _REPO_ROOT / "data"

# NOTE: Questionnaire integrity constants and CanonicalQuestionnaire are now in questionnaire.py
# Import them from there: from .questionnaire import CanonicalQuestionnaire, EXPECTED_HASH, etc.

@dataclass(frozen=True)
class ProcessorBundle:
    """Aggregated orchestrator dependencies built by the factory.

    Attributes:
        method_executor: Preconfigured :class:`MethodExecutor` instance ready for
            execution.  This object encapsulates dynamic class loading via the
            orchestrator registry.
        questionnaire: Read-only view of the questionnaire monolith payload.
            Consumers must treat this mapping as immutable.
        factory: The :class:`CoreModuleFactory` used to construct ancillary
            input contracts for downstream processors.
    """

    method_executor: MethodExecutor
    questionnaire: Mapping[str, Any]
    factory: "CoreModuleFactory"

# ============================================================================
# FILE I/O OPERATIONS
# ============================================================================
# NOTE: Questionnaire loading functions moved to questionnaire.py
# load_questionnaire() and validate_questionnaire_structure() are now there


def load_questionnaire_monolith(path: Path | None = None) -> dict[str, Any]:
    """DEPRECATED: Use questionnaire.load_questionnaire() instead.

    ⚠️  QUESTIONNAIRE INTEGRITY VIOLATION WARNING ⚠️
    This function bypasses the CanonicalQuestionnaire type system and returns
    a mutable dict. This is UNSAFE and defeats questionnaire integrity checks.

    MIGRATION PATH:
        # Old (UNSAFE):
        monolith = load_questionnaire_monolith()

        # New (SAFE):
        from saaaaaa.core.orchestrator.questionnaire import load_questionnaire
        questionnaire = load_questionnaire()  # Returns CanonicalQuestionnaire

    Args:
        path: IGNORED - Parameter is ignored, always loads from canonical path

    Returns:
        Mutable questionnaire dict (UNSAFE, DEPRECATED)

    Raises:
        DeprecationWarning: Always warns about deprecation
    """
    import warnings
    warnings.warn(
        "\n"
        "════════════════════════════════════════════════════════════════════════\n"
        "⚠️  QUESTIONNAIRE INTEGRITY VIOLATION: load_questionnaire_monolith() ⚠️\n"
        "════════════════════════════════════════════════════════════════════════\n"
        "This function is DEPRECATED and will be REMOVED in a future version.\n"
        "\n"
        "PROBLEMS:\n"
        "  • Returns mutable dict instead of immutable CanonicalQuestionnaire\n"
        "  • No hash verification (integrity violation)\n"
        "  • No type safety (can be modified in-flight)\n"
        "\n"
        "MIGRATION:\n"
        "  from saaaaaa.core.orchestrator.questionnaire import load_questionnaire\n"
        "  questionnaire = load_questionnaire()  # Type-safe, hash-verified\n"
        "\n"
        "════════════════════════════════════════════════════════════════════════\n",
        DeprecationWarning,
        stacklevel=2
    )

    if path is not None:
        logger.warning(
            "load_questionnaire_monolith: path parameter is IGNORED. "
            "Questionnaire always loads from canonical path."
        )

    canonical = load_questionnaire()
    # Return mutable copy for backward compatibility (UNSAFE)
    return dict(canonical.data)

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

    This function loads the canonical notation from questionnaire_monolith.json
    via the canonical loader and returns the dimension definitions.

    Args:
        questionnaire_path: Optional path to questionnaire file (IGNORED for integrity)

    Returns:
        Dictionary mapping dimension keys (D1-D6) to dimension info with code, name, label

    Example:
        >>> dims = get_canonical_dimensions()
        >>> dims['D1']
        {'code': 'DIM01', 'name': 'INSUMOS', 'label': 'Diagnóstico y Recursos'}

    Note:
        Uses canonical questionnaire loader for integrity verification.
        The questionnaire_path parameter is ignored to enforce single source of truth.
    """
    if questionnaire_path is not None:
        logger.warning(
            "get_canonical_dimensions: questionnaire_path parameter is IGNORED. "
            "Dimensions always load from canonical questionnaire path for integrity."
        )

    # Use canonical loader for hash verification and immutability
    canonical = load_questionnaire()

    if 'canonical_notation' not in canonical.data:
        raise KeyError("canonical_notation section missing from questionnaire")

    if 'dimensions' not in canonical.data['canonical_notation']:
        raise KeyError("dimensions section missing from canonical_notation")

    # Return deep copy to prevent side-effects on nested dictionaries
    import copy
    return copy.deepcopy(canonical.data['canonical_notation']['dimensions'])

def get_canonical_policy_areas(questionnaire_path: Path | None = None) -> dict[str, dict[str, str]]:
    """
    Get canonical policy area definitions from questionnaire monolith.

    This function loads the canonical notation from questionnaire_monolith.json
    via the canonical loader and returns the policy area definitions.

    Args:
        questionnaire_path: Optional path to questionnaire file (IGNORED for integrity)

    Returns:
        Dictionary mapping policy area codes (PA01-PA10) to policy area info with name, legacy_id

    Example:
        >>> areas = get_canonical_policy_areas()
        >>> areas['PA01']
        {'name': 'Derechos de las mujeres e igualdad de género', 'legacy_id': 'P1'}

    Note:
        Uses canonical questionnaire loader for integrity verification.
        The questionnaire_path parameter is ignored to enforce single source of truth.
    """
    if questionnaire_path is not None:
        logger.warning(
            "get_canonical_policy_areas: questionnaire_path parameter is IGNORED. "
            "Policy areas always load from canonical questionnaire path for integrity."
        )

    # Use canonical loader for hash verification and immutability
    canonical = load_questionnaire()

    if 'canonical_notation' not in canonical.data:
        raise KeyError("canonical_notation section missing from questionnaire")

    if 'policy_areas' not in canonical.data['canonical_notation']:
        raise KeyError("policy_areas section missing from canonical_notation")

    # Return deep copy to prevent side-effects on nested dictionaries
    import copy
    return copy.deepcopy(canonical.data['canonical_notation']['policy_areas'])

def load_schema(path: Path | None = None) -> dict[str, Any]:
    """Load questionnaire schema JSON file.

    Args:
        path: Path to schema file. Defaults to schemas/questionnaire_monolith.schema.json
              relative to repository root.

    Returns:
        Loaded schema data
    
    Raises:
        FileNotFoundError: If schema file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    if path is None:
        path = _REPO_ROOT / "schemas" / "questionnaire_monolith.schema.json"

    logger.info(f"Loading schema from {path}")

    with open(path, encoding='utf-8') as f:
        return json.load(f)

def load_document(file_path: Path) -> DocumentData:
    """Load a document and construct DocumentData contract.

    This handles file I/O and parsing, providing structured data to core modules.

    Args:
        file_path: Path to document file

    Returns:
        DocumentData contract with parsed content
    """
    logger.info(f"Loading document from {file_path}")

    # Read file
    with open(file_path, encoding='utf-8') as f:
        raw_text = f.read()

    # Basic parsing (to be enhanced)
    sentences = raw_text.split('.')
    sentences = [s.strip() for s in sentences if s.strip()]

    return DocumentData(
        raw_text=raw_text,
        sentences=sentences,
        tables=[],  # Table extraction to be implemented
        metadata={
            'file_path': str(file_path),
            'file_name': file_path.name,
            'num_sentences': len(sentences),
        }
    )

def save_results(results: dict[str, Any], output_path: Path) -> None:
    """Save analysis results to file.

    This is the ONLY place that should write analysis results.
    Core modules return data via contracts; the factory handles persistence.

    Args:
        results: Analysis results to save
        output_path: Path to output file
    """
    logger.info(f"Saving results to {output_path}")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

# ============================================================================
# CONTRACT CONSTRUCTORS
# ============================================================================

def construct_semantic_analyzer_input(
    document: DocumentData,
    **kwargs: Any
) -> SemanticAnalyzerInputContract:
    """Construct input contract for SemanticAnalyzer.

    Args:
        document: Loaded document data
        **kwargs: Additional parameters

    Returns:
        Typed input contract
    """
    return SemanticAnalyzerInputContract(
        text=document['raw_text'],
        segments=kwargs.get('segments', document['sentences']),
        ontology_params=kwargs.get('ontology_params', {}),
    )

def construct_cdaf_input(
    document: DocumentData,
    plan_name: str,
    **kwargs: Any
) -> CDAFFrameworkInputContract:
    """Construct input contract for CDAFFramework.

    Args:
        document: Loaded document data
        plan_name: Name of the development plan
        **kwargs: Additional parameters

    Returns:
        Typed input contract
    """
    return CDAFFrameworkInputContract(
        document_text=document['raw_text'],
        plan_metadata={
            'plan_name': plan_name,
            **document['metadata'],
            **kwargs.get('plan_metadata', {}),
        },
        config=kwargs.get('config', {}),
    )

def construct_pdet_input(
    document: DocumentData,
    **kwargs: Any
) -> PDETAnalyzerInputContract:
    """Construct input contract for PDETMunicipalPlanAnalyzer.

    Args:
        document: Loaded document data
        **kwargs: Additional parameters

    Returns:
        Typed input contract
    """
    return PDETAnalyzerInputContract(
        document_content=document['raw_text'],
        extract_tables=kwargs.get('extract_tables', True),
        config=kwargs.get('config', {}),
    )

def construct_teoria_cambio_input(
    document: DocumentData,
    **kwargs: Any
) -> TeoriaCambioInputContract:
    """Construct input contract for TeoriaCambio.

    Args:
        document: Loaded document data
        **kwargs: Additional parameters

    Returns:
        Typed input contract
    """
    return TeoriaCambioInputContract(
        document_text=document['raw_text'],
        strategic_goals=kwargs.get('strategic_goals', []),
        config=kwargs.get('config', {}),
    )

def construct_contradiction_detector_input(
    document: DocumentData,
    plan_name: str,
    **kwargs: Any
) -> ContradictionDetectorInputContract:
    """Construct input contract for PolicyContradictionDetector.

    Args:
        document: Loaded document data
        plan_name: Name of the development plan
        **kwargs: Additional parameters

    Returns:
        Typed input contract
    """
    return ContradictionDetectorInputContract(
        text=document['raw_text'],
        plan_name=plan_name,
        dimension=kwargs.get('dimension'),
        config=kwargs.get('config', {}),
    )

def construct_embedding_policy_input(
    document: DocumentData,
    **kwargs: Any
) -> EmbeddingPolicyInputContract:
    """Construct input contract for embedding policy analysis.

    Args:
        document: Loaded document data
        **kwargs: Additional parameters

    Returns:
        Typed input contract
    """
    return EmbeddingPolicyInputContract(
        text=document['raw_text'],
        dimensions=kwargs.get('dimensions', []),
        model_config=kwargs.get('model_config', {}),
    )

def construct_semantic_chunking_input(
    document: DocumentData,
    **kwargs: Any
) -> SemanticChunkingInputContract:
    """Construct input contract for semantic chunking.

    Args:
        document: Loaded document data
        **kwargs: Additional parameters

    Returns:
        Typed input contract
    """
    return SemanticChunkingInputContract(
        text=document['raw_text'],
        preserve_structure=kwargs.get('preserve_structure', True),
        config=kwargs.get('config', {}),
    )

def construct_policy_processor_input(
    document: DocumentData,
    **kwargs: Any
) -> PolicyProcessorInputContract:
    """Construct input contract for IndustrialPolicyProcessor.

    Args:
        document: Loaded document data
        **kwargs: Additional parameters

    Returns:
        Typed input contract
    """
    return PolicyProcessorInputContract(
        data=kwargs.get('data', document['raw_text']),
        text=document['raw_text'],
        sentences=document['sentences'],
        tables=document['tables'],
        config=kwargs.get('config', {}),
    )

# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

class CoreModuleFactory:
    """Factory for constructing core modules with injected dependencies.

    This factory:
    1. Loads data from disk
    2. Constructs contracts
    3. Initializes core modules
    4. Manages all I/O operations

    Usage:
        factory = CoreModuleFactory()
        document = factory.load_document(Path("plan.txt"))

        # Construct input contract
        input_contract = factory.construct_semantic_analyzer_input(document)

        # Use with core module (once modules are refactored)
        # analyzer = SemanticAnalyzer()
        # result = analyzer.analyze(input_contract)
    """

    def __init__(self, data_dir: Path | None = None) -> None:
        """Initialize factory.

        Args:
            data_dir: Optional directory for data files
        """
        self.data_dir = data_dir or _DEFAULT_DATA_DIR
        self.questionnaire_cache: dict[str, Any] | None = None
        self.catalog_cache: dict[str, Any] | None = None

    def get_questionnaire(self) -> dict[str, Any]:
        """Get questionnaire monolith data (cached).

        Uses canonical loader for hash verification.

        Returns:
            Questionnaire data (dict for backward compatibility)
        """
        if self.questionnaire_cache is None:
            questionnaire_path = self.data_dir / "questionnaire_monolith.json"
            # Use canonical loader for hash verification
            canonical_q = load_questionnaire(questionnaire_path)
            self.questionnaire_cache = dict(canonical_q.data)
            # Also set it in the global provider for backward compatibility
            get_questionnaire_provider().set_data(self.questionnaire_cache)
            logger.info(
                "factory_loaded_questionnaire",
                sha256=canonical_q.sha256[:16] + "...",
                question_count=canonical_q.total_question_count,
            )
        return self.questionnaire_cache

    @property
    def catalog(self) -> dict[str, Any]:
        """Get method catalog data (cached).

        Returns:
            Method catalog data
        """
        if self.catalog_cache is None:
            self.catalog_cache = load_catalog()
        return self.catalog_cache

    def load_document(self, file_path: Path) -> DocumentData:
        """Load document and return structured data.

        Args:
            file_path: Path to document

        Returns:
            Parsed document data
        """
        return load_document(file_path)

    def save_results(self, results: dict[str, Any], output_path: Path) -> None:
        """Save analysis results.

        Args:
            results: Results to save
            output_path: Output file path
        """
        save_results(results, output_path)

    def load_catalog(self, path: Path | None = None) -> dict[str, Any]:
        """Load method catalog JSON file.

        Args:
            path: Path to catalog file. Defaults to config/rules/METODOS/catalogo_completo_canonico.json
                  relative to repository root.

        Returns:
            Loaded catalog data
        """
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
) -> ProcessorBundle:
    """Create a processor bundle with orchestrator dependencies wired together.

    Args:
        questionnaire_path: Optional path to the questionnaire monolith. When
            provided, it overrides the factory's default resolution logic.
        data_dir: Optional directory for ancillary data files such as the
            questionnaire. Useful for tests that operate inside temporary
            directories.
        factory: Pre-existing :class:`CoreModuleFactory` instance. When omitted
            the function creates a new factory configured with ``data_dir``.
        enable_signals: Enable signal infrastructure (default: True)

    Returns:
        A :class:`ProcessorBundle` containing a ready-to-use method executor,
        the questionnaire payload (as an immutable mapping) and the factory.

    Note:
        Uses load_questionnaire() for hash verification and immutability.

    Raises:
        TypeError: If parameters have incorrect types
    """

    # Runtime type checks (defensive programming)
    if questionnaire_path is not None and not isinstance(questionnaire_path, Path):
        raise TypeError(
            f"questionnaire_path must be Path or None, got {type(questionnaire_path).__name__}. "
            f"build_processor() requires keyword arguments only."
        )

    if data_dir is not None and not isinstance(data_dir, Path):
        raise TypeError(
            f"data_dir must be Path or None, got {type(data_dir).__name__}"
        )

    if factory is not None and not isinstance(factory, CoreModuleFactory):
        raise TypeError(
            f"factory must be CoreModuleFactory or None, got {type(factory).__name__}"
        )

    if not isinstance(enable_signals, bool):
        raise TypeError(
            f"enable_signals must be bool, got {type(enable_signals).__name__}"
        )

    core_factory = factory or CoreModuleFactory(data_dir=data_dir)

    if questionnaire_path is not None:
        # Use canonical loader for hash verification
        canonical_q = load_questionnaire(questionnaire_path)
        questionnaire_data = dict(canonical_q.data)  # Convert for backward compat
        core_factory.questionnaire_cache = copy.deepcopy(questionnaire_data)
        # Initialize the global provider with this data
        get_questionnaire_provider().set_data(questionnaire_data)
        logger.info(
            "build_processor_using_canonical_loader",
            path=str(questionnaire_path),
            sha256=canonical_q.sha256[:16] + "...",
            question_count=canonical_q.total_question_count,
        )
    else:
        questionnaire_data = core_factory.get_questionnaire()

    questionnaire_snapshot = MappingProxyType(copy.deepcopy(questionnaire_data))

    # Build signal infrastructure if enabled
    signal_registry = None
    if enable_signals:
        try:
            from .bayesian_module_factory import BayesianModuleFactory as SignalFactory

            # Create signal-enabled factory
            signal_factory = SignalFactory(
                questionnaire_data=questionnaire_data,
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
        questionnaire=questionnaire_snapshot,
        factory=core_factory,
    )

# ============================================================================
# HASH AND VALIDATION UTILITIES
# ============================================================================

def compute_monolith_hash(monolith: dict[str, Any]) -> str:
    """
    Compute deterministic SHA-256 hash of questionnaire monolith.
    
    This function ensures:
    - Key order independence via sort_keys=True
    - Consistent unicode handling via ensure_ascii=True
    - No whitespace variation via separators
    
    Args:
        monolith: Questionnaire monolith dictionary
        
    Returns:
        Hexadecimal SHA-256 hash string
    """
    import hashlib
    
    serialized = json.dumps(
        monolith,
        sort_keys=True,
        ensure_ascii=True,  # Consistent unicode handling
        separators=(',', ':'),  # No whitespace
    )
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


# NOTE: validate_questionnaire_structure() moved to questionnaire.py
# For backward compatibility, keep this stub that delegates to questionnaire module
def validate_questionnaire_structure(data: dict[str, Any]) -> None:
    """DEPRECATED: Import from questionnaire module instead.
    
    This stub is maintained for backward compatibility only.
    Use: from .questionnaire import _validate_questionnaire_structure
    
    Args:
        data: Questionnaire data to validate
        
    Raises:
        ValueError: If validation fails
        TypeError: If top-level structure is invalid
    """
    from .questionnaire import _validate_questionnaire_structure
    return _validate_questionnaire_structure(data)

# ============================================================================
# MIGRATION HELPERS
# ============================================================================

def migrate_io_from_module(module_name: str, line_numbers: list[int]) -> None:
    """Helper to track I/O migration progress.

    This is a placeholder function to document which I/O operations
    have been migrated from core modules to the factory.

    Args:
        module_name: Name of the module being migrated
        line_numbers: Line numbers of I/O operations migrated
    """
    logger.info(
        f"Migrating {len(line_numbers)} I/O operations from {module_name}: "
        f"lines {line_numbers}"
    )

# TODO: Migrate I/O operations from core modules
# Track progress:
# - Analyzer_one.py: 72 I/O operations to migrate
# - dereck_beach.py: 40 I/O operations to migrate
# - financiero_viabilidad_tablas.py: Multiple operations to migrate
# - teoria_cambio.py: Some operations to migrate
# Others are clean

__all__ = [
    # Questionnaire integrity types and constants (re-exported from questionnaire.py)
    'CanonicalQuestionnaire',
    'EXPECTED_HASH',
    'EXPECTED_MACRO_QUESTION_COUNT',
    'EXPECTED_MICRO_QUESTION_COUNT',
    'EXPECTED_MESO_QUESTION_COUNT',
    'EXPECTED_TOTAL_QUESTION_COUNT',
    'QUESTIONNAIRE_PATH',
    # Canonical loader (use this!)
    'load_questionnaire',
    # Factory classes
    'CoreModuleFactory',
    'ProcessorBundle',
    # Legacy/deprecated (use load_questionnaire instead)
    'load_questionnaire_monolith',
    # Hash computation (for backward compatibility, prefer questionnaire module)
    'compute_monolith_hash',
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
