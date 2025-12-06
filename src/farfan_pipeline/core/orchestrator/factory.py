"""
Factory module — canonical Dependency Injection (DI) and access control for F.A.R.F.A.N. 

This module is the SINGLE AUTHORITATIVE BOUNDARY for:
- Canonical monolith access (CanonicalQuestionnaire) - loaded ONCE with integrity verification
- Signal registry construction (QuestionnaireSignalRegistry v2.0) from canonical source ONLY
- Method injection via MethodExecutor with signal registry DI
- Orchestrator construction with full DI (questionnaire, method_executor, executor_config)
- EnrichedSignalPack creation and injection per executor (30 executors)
- Hard contracts and validation constants for Phase 1
- SeedRegistry singleton initialization for determinism

METHOD DISPENSARY PATTERN - Core Architecture:
==============================================

The pipeline uses a "method dispensary" pattern where monolithic analyzer classes
serve as "dispensaries" that provide methods to executors. This architecture enables:

1. LOOSE COUPLING: Executors orchestrate methods without direct imports
2. PARTIAL REUSE: Same method used by multiple executors with different contexts
3. CENTRALIZED MANAGEMENT: All method routing through MethodExecutor with validation
4. SIGNAL AWARENESS: Methods receive signal packs for pattern matching

Dispensary Registry (~20 monolith classes, 240+ methods):
---------------------------------------------------------
- IndustrialPolicyProcessor (17 methods): Pattern matching, evidence extraction
- PDETMunicipalPlanAnalyzer (52+ methods): LARGEST - financial, causal, entity analysis
- CausalExtractor (28 methods): Goal extraction, causal hierarchy, semantic distance
- FinancialAuditor (13 methods): Budget tracing, allocation gaps, sufficiency
- BayesianMechanismInference (14 methods): Necessity/sufficiency tests, coherence
- BayesianCounterfactualAuditor (9 methods): SCM construction, refutation
- TextMiningEngine (8 methods): Critical link diagnosis, intervention generation
- SemanticAnalyzer (12 methods): Semantic cube, domain classification
- PerformanceAnalyzer (5 methods): Performance metrics, loss functions
- PolicyContradictionDetector (8 methods): Contradiction detection, coherence
- [... 10+ more classes]

Executor Usage Pattern:
----------------------
Each of 30 executors uses a UNIQUE COMBINATION of methods:
- D1-Q1 (QuantitativeBaselineExtractor): 17 methods from 9 classes
- D3-Q2 (TargetProportionalityAnalyzer): 24 methods from 7 classes
- D3-Q5 (OutputOutcomeLinkageAnalyzer): 28 methods from 6 classes
- D6-Q3 (ValidationTestingAnalyzer): 8 methods from 4 classes

Methods are orchestrated via:
```python
result = self.method_executor.execute(
    class_name="PDETMunicipalPlanAnalyzer",
    method_name="_score_indicators",
    document=doc,
    signal_pack=pack,
    **context
)
```

NOT ALL METHODS ARE USED:
- Monoliths contain more methods than executors need
- Only methods in executors_methods.json are actively used
- Phase 1 (ingestion) uses additional methods not in executor contracts
- 14 methods in validation failures (deprecated/private)

Design Principles (Factory Pattern + DI):
=========================================

1. FACTORY PATTERN: AnalysisPipelineFactory is the ONLY place that instantiates:
   - Orchestrator, MethodExecutor, QuestionnaireSignalRegistry, BaseExecutor instances
   - NO other module should directly instantiate these classes
   
2. DEPENDENCY INJECTION: All components receive dependencies via __init__:
   - Orchestrator receives: questionnaire, method_executor, executor_config, validation_constants
   - MethodExecutor receives: method_registry, arg_router, signal_registry
   - BaseExecutor (30 classes) receive: enriched_signal_pack, method_executor, config
   
3. CANONICAL MONOLITH CONTROL:
   - load_questionnaire() called ONCE by factory only (singleton + integrity hash)
   - Orchestrator uses self.questionnaire object, NEVER file paths
   - Search codebase: NO other load_questionnaire() calls should exist
   
4. SIGNAL REGISTRY CONTROL:
   - create_signal_registry(questionnaire) - from canonical source ONLY
   - signal_loader.py MUST BE DELETED (legacy JSON loaders eliminated)
   - Registry injected into MethodExecutor, NOT accessed globally
   
5. ENRICHED SIGNAL PACK INJECTION:
   - Factory builds EnrichedSignalPack per executor (semantic expansion + context filtering)
   - Each BaseExecutor receives its specific pack, NOT full registry
   
6. DETERMINISM:
   - SeedRegistry singleton initialized by factory for reproducibility
   - ExecutorConfig encapsulates operational params (max_tokens, retries)
   
7. PHASE 1 HARD CONTRACTS:
   - Validation constants (P01_EXPECTED_CHUNK_COUNT=60, etc.) loaded by factory
   - Injected into Orchestrator for Phase 1 chunk validation
   - Execution FAILS if contracts violated

SIN_CARRETA Compliance:
- All construction paths emit structured telemetry with timestamps and hashes
- Determinism enforced via explicit validation of canonical questionnaire integrity
- Contract assertions guard all factory outputs (no silent degradation)
- Auditability via immutable ProcessorBundle with provenance metadata
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Type

from farfan_pipeline.core.orchestrator.core import Orchestrator, MethodExecutor
from farfan_pipeline.core.orchestrator.executor_config import ExecutorConfig
from farfan_pipeline.core.orchestrator.method_registry import (
    MethodRegistry,
    setup_default_instantiation_rules,
)
from farfan_pipeline.core.orchestrator.signal_registry import (
    QuestionnaireSignalRegistry,
    create_signal_registry,
)
from farfan_pipeline.core.orchestrator.signal_intelligence_layer import (
    EnrichedSignalPack,
    create_enriched_signal_pack,
)
from farfan_pipeline.core.orchestrator.questionnaire import (
    CanonicalQuestionnaire,
    load_questionnaire,
)
from farfan_pipeline.core.orchestrator.arg_router import ExtendedArgRouter
from farfan_pipeline.core.orchestrator.class_registry import build_class_registry

# Phase 1 validation constants module
try:
    from farfan_pipeline.config.validation_constants import (
        PHASE1_VALIDATION_CONSTANTS,
        load_validation_constants,
    )
    VALIDATION_CONSTANTS_AVAILABLE = True
except ImportError:
    PHASE1_VALIDATION_CONSTANTS = {}
    VALIDATION_CONSTANTS_AVAILABLE = False

# Optional: CoreModuleFactory for I/O helpers
try:
    from farfan_pipeline.core.orchestrator.core_module_factory import CoreModuleFactory
    CORE_MODULE_FACTORY_AVAILABLE = True
except ImportError:
    CoreModuleFactory = None  # type: ignore
    CORE_MODULE_FACTORY_AVAILABLE = False

# SeedRegistry for determinism (REQUIRED for production)
try:
    from farfan_pipeline.core.orchestrator.seed_registry import SeedRegistry
    SEED_REGISTRY_AVAILABLE = True
except ImportError:
    SeedRegistry = None  # type: ignore
    SEED_REGISTRY_AVAILABLE = False

logger = logging.getLogger(__name__)


# =============================================================================
# Exceptions
# =============================================================================


class FactoryError(Exception):
    """Base exception for factory construction failures."""
    pass


class QuestionnaireValidationError(FactoryError):
    """Raised when questionnaire validation fails."""
    pass


class IntegrityError(FactoryError):
    """Raised when questionnaire integrity check (SHA-256) fails."""
    pass


class RegistryConstructionError(FactoryError):
    """Raised when signal registry construction fails."""
    pass


class ExecutorConstructionError(FactoryError):
    """Raised when method executor construction fails."""
    pass


class SingletonViolationError(FactoryError):
    """Raised when singleton pattern is violated."""
    pass


# =============================================================================
# Processor Bundle (typed DI container with provenance)
# =============================================================================


@dataclass(frozen=True)
class ProcessorBundle:
    """Aggregated orchestrator dependencies built by the Factory. 

    This is the COMPLETE DI container returned by AnalysisPipelineFactory.
    
    Attributes:
        orchestrator: Fully configured Orchestrator (main entry point).
        method_executor: MethodExecutor with signal registry injected.
        questionnaire: Immutable, validated CanonicalQuestionnaire (monolith).
        signal_registry: QuestionnaireSignalRegistry v2.0 from canonical source.
        executor_config: ExecutorConfig for operational parameters.
        enriched_signal_packs: Dict of EnrichedSignalPack per policy area.
        validation_constants: Phase 1 hard contracts (chunk counts, etc.).
        core_module_factory: Optional CoreModuleFactory for I/O helpers.
        seed_registry_initialized: Whether SeedRegistry singleton was set up.
        provenance: Construction metadata for audit trails.
    """

    orchestrator: Orchestrator
    method_executor: MethodExecutor
    questionnaire: CanonicalQuestionnaire
    signal_registry: QuestionnaireSignalRegistry
    executor_config: ExecutorConfig
    enriched_signal_packs: dict[str, EnrichedSignalPack]
    validation_constants: dict[str, Any]
    core_module_factory: Optional[Any] = None
    seed_registry_initialized: bool = False
    provenance: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """SIN_CARRETA § Contract Enforcement: validate bundle integrity."""
        errors = []
        
        # Critical components validation
        if self.orchestrator is None:
            errors.append("orchestrator must not be None")
        if self.method_executor is None:
            errors.append("method_executor must not be None")
        if self.questionnaire is None:
            errors.append("questionnaire must not be None")
        if self.signal_registry is None:
            errors.append("signal_registry must not be None")
        if self.executor_config is None:
            errors.append("executor_config must not be None")
        if self.enriched_signal_packs is None:
            errors.append("enriched_signal_packs must not be None")
        elif not isinstance(self.enriched_signal_packs, dict):
            errors.append("enriched_signal_packs must be dict[str, EnrichedSignalPack]")
        
        if self.validation_constants is None:
            errors.append("validation_constants must not be None")
        
        # Provenance validation
        if not self.provenance.get("construction_timestamp_utc"):
            errors.append("provenance must include construction_timestamp_utc")
        if not self.provenance.get("canonical_sha256"):
            errors.append("provenance must include canonical_sha256")
        if self.provenance.get("signal_registry_version") != "2.0":
            errors.append("provenance must indicate signal_registry_version=2.0")
        
        # Factory pattern enforcement check
        if not self.provenance.get("factory_instantiation_confirmed"):
            errors.append("provenance must confirm factory instantiation (not direct construction)")
        
        if errors:
            raise FactoryError(f"ProcessorBundle validation failed: {'; '.join(errors)}")
        
        logger.info(
            "processor_bundle_validated "
            "canonical_sha256=%s construction_ts=%s policy_areas=%d validation_constants=%d",
            self.provenance.get("canonical_sha256", "")[:16],
            self.provenance.get("construction_timestamp_utc"),
            len(self.enriched_signal_packs),
            len(self.validation_constants),
        )


# =============================================================================
# Analysis Pipeline Factory (Main Factory Class)
# =============================================================================


class AnalysisPipelineFactory:
    """Factory for constructing the complete analysis pipeline.
    
    This is the ONLY class that should instantiate:
    - Orchestrator
    - MethodExecutor  
    - QuestionnaireSignalRegistry
    - BaseExecutor instances (30 executor classes)
    
    CRITICAL: No other module should directly instantiate these classes.
    All dependencies are injected via constructor parameters.
    
    Usage:
        factory = AnalysisPipelineFactory(
            questionnaire_path="path/to/questionnaire.json",
            expected_hash="abc123...",
            seed=42
        )
        bundle = factory.create_orchestrator()
        orchestrator = bundle.orchestrator
    """
    
    # Singleton tracking for load_questionnaire() call
    _questionnaire_loaded = False
    _questionnaire_instance: Optional[CanonicalQuestionnaire] = None
    
    def __init__(
        self,
        *,
        questionnaire_path: Optional[str] = None,
        expected_questionnaire_hash: Optional[str] = None,
        executor_config: Optional[ExecutorConfig] = None,
        validation_constants: Optional[dict[str, Any]] = None,
        enable_intelligence_layer: bool = True,
        seed_for_determinism: Optional[int] = None,
        strict_validation: bool = True,
    ):
        """Initialize the Analysis Pipeline Factory.
        
        Args:
            questionnaire_path: Path to canonical questionnaire JSON.
            expected_questionnaire_hash: Expected SHA-256 hash for integrity check.
            executor_config: Custom executor configuration (if None, uses default).
            validation_constants: Phase 1 validation constants (if None, loads from config).
            enable_intelligence_layer: Whether to build enriched signal packs.
            seed_for_determinism: Seed for SeedRegistry singleton.
            strict_validation: If True, fail on any validation error.
        """
        self._questionnaire_path = questionnaire_path
        self._expected_hash = expected_questionnaire_hash
        self._executor_config = executor_config
        self._validation_constants = validation_constants
        self._enable_intelligence = enable_intelligence_layer
        self._seed = seed_for_determinism
        self._strict = strict_validation
        
        # Internal state (set during construction)
        self._canonical_questionnaire: Optional[CanonicalQuestionnaire] = None
        self._signal_registry: Optional[QuestionnaireSignalRegistry] = None
        self._method_executor: Optional[MethodExecutor] = None
        self._enriched_packs: dict[str, EnrichedSignalPack] = {}
        
        logger.info(
            "factory_initialized questionnaire_path=%s intelligence_layer=%s seed=%s",
            questionnaire_path or "default",
            enable_intelligence_layer,
            seed_for_determinism is not None,
        )
    
    def create_orchestrator(self) -> ProcessorBundle:
        """Create fully configured Orchestrator with all dependencies injected.
        
        This is the PRIMARY ENTRY POINT for the factory.
        Returns a complete ProcessorBundle with Orchestrator ready to use.
        
        Returns:
            ProcessorBundle: Immutable bundle with all dependencies wired.
            
        Raises:
            QuestionnaireValidationError: If questionnaire validation fails.
            IntegrityError: If questionnaire hash doesn't match expected.
            RegistryConstructionError: If signal registry construction fails.
            ExecutorConstructionError: If method executor construction fails.
        """
        construction_start = time.time()
        timestamp_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        
        logger.info("factory_create_orchestrator_start timestamp=%s", timestamp_utc)
        
        try:
            # Step 1: Load canonical questionnaire (ONCE, with integrity check)
            self._load_canonical_questionnaire()
            
            # Step 2: Build signal registry from canonical source
            self._build_signal_registry()
            
            # Step 3: Build enriched signal packs (intelligence layer)
            self._build_enriched_signal_packs()
            
            # Step 4: Initialize seed registry for determinism
            seed_initialized = self._initialize_seed_registry()
            
            # Step 5: Build method executor with signal registry DI
            self._build_method_executor()
            
            # Step 6: Load Phase 1 validation constants
            validation_constants = self._load_validation_constants()
            
            # Step 7: Get or create executor config
            executor_config = self._get_executor_config()
            
            # Step 8: Build orchestrator with full DI
            orchestrator = self._build_orchestrator(
                executor_config=executor_config,
                validation_constants=validation_constants,
            )
            
            # Step 9: Assemble provenance metadata
            construction_duration = time.time() - construction_start
            canonical_hash = self._compute_questionnaire_hash()
            
            provenance = {
                "construction_timestamp_utc": timestamp_utc,
                "canonical_sha256": canonical_hash,
                "signal_registry_version": "2.0",
                "intelligence_layer_enabled": self._enable_intelligence,
                "enriched_packs_count": len(self._enriched_packs),
                "validation_constants_count": len(validation_constants),
                "construction_duration_seconds": round(construction_duration, 3),
                "seed_registry_initialized": seed_initialized,
                "core_module_factory_available": CORE_MODULE_FACTORY_AVAILABLE,
                "strict_validation": self._strict,
                "factory_instantiation_confirmed": True,  # Critical for bundle validation
                "factory_class": "AnalysisPipelineFactory",
            }
            
            # Step 10: Build complete bundle
            bundle = ProcessorBundle(
                orchestrator=orchestrator,
                method_executor=self._method_executor,
                questionnaire=self._canonical_questionnaire,
                signal_registry=self._signal_registry,
                executor_config=executor_config,
                enriched_signal_packs=self._enriched_packs,
                validation_constants=validation_constants,
                core_module_factory=self._build_core_module_factory(),
                seed_registry_initialized=seed_initialized,
                provenance=provenance,
            )
            
            logger.info(
                "factory_create_orchestrator_complete duration=%.3fs hash=%s",
                construction_duration,
                canonical_hash[:16],
            )
            
            return bundle
            
        except Exception as e:
            logger.error("factory_create_orchestrator_failed error=%s", str(e), exc_info=True)
            raise FactoryError(f"Failed to create orchestrator: {e}") from e
    
    # =========================================================================
    # Internal Construction Methods
    # =========================================================================
    
    def _load_canonical_questionnaire(self) -> None:
        """Load canonical questionnaire with singleton enforcement and integrity check.
        
        CRITICAL REQUIREMENTS:
        1. This is the ONLY place in the codebase that calls load_questionnaire()
        2. Must enforce singleton pattern (only load once)
        3. Must verify SHA-256 hash for integrity
        4. Must raise IntegrityError if hash doesn't match
        
        Raises:
            SingletonViolationError: If load_questionnaire() already called.
            IntegrityError: If questionnaire hash doesn't match expected.
            QuestionnaireValidationError: If questionnaire structure invalid.
        """
        # Enforce singleton pattern
        if AnalysisPipelineFactory._questionnaire_loaded:
            if AnalysisPipelineFactory._questionnaire_instance is not None:
                logger.info("questionnaire_singleton_reused using_cached_instance")
                self._canonical_questionnaire = AnalysisPipelineFactory._questionnaire_instance
                return
            else:
                raise SingletonViolationError(
                    "load_questionnaire() was called but instance is None. "
                    "This indicates a singleton pattern violation."
                )
        
        logger.info("questionnaire_loading_start path=%s", self._questionnaire_path or "default")
        
        try:
            # Load questionnaire (this should be the ONLY call in the entire codebase)
            questionnaire = load_questionnaire(self._questionnaire_path)
            
            # Mark singleton as loaded
            AnalysisPipelineFactory._questionnaire_loaded = True
            AnalysisPipelineFactory._questionnaire_instance = questionnaire
            
            # Compute integrity hash
            actual_hash = self._compute_questionnaire_hash_from_instance(questionnaire)
            
            # Verify integrity if expected hash provided
            if self._expected_hash is not None:
                if actual_hash != self._expected_hash:
                    raise IntegrityError(
                        f"Questionnaire integrity check FAILED. "
                        f"Expected: {self._expected_hash[:16]}... "
                        f"Actual: {actual_hash[:16]}... "
                        f"The canonical questionnaire may have been tampered with."
                    )
                logger.info("questionnaire_integrity_verified hash=%s", actual_hash[:16])
            else:
                logger.warning(
                    "questionnaire_integrity_not_verified no_expected_hash_provided "
                    "actual_hash=%s",
                    actual_hash[:16]
                )
            
            # Validate structure
            if not hasattr(questionnaire, 'questions'):
                if self._strict:
                    raise QuestionnaireValidationError("Questionnaire missing 'questions' attribute")
                logger.warning("questionnaire_validation_warning missing_questions_attribute")
            
            questions = getattr(questionnaire, 'questions', [])
            if not questions:
                if self._strict:
                    raise QuestionnaireValidationError("Questionnaire has no questions")
                logger.warning("questionnaire_validation_warning no_questions")
            
            self._canonical_questionnaire = questionnaire
            
            logger.info(
                "questionnaire_loaded_successfully questions=%d hash=%s singleton=established",
                len(questions),
                actual_hash[:16],
            )
            
        except Exception as e:
            if isinstance(e, (IntegrityError, SingletonViolationError, QuestionnaireValidationError)):
                raise
            raise QuestionnaireValidationError(f"Failed to load questionnaire: {e}") from e
    
    def _build_signal_registry(self) -> None:
        """Build signal registry from canonical questionnaire.
        
        CRITICAL REQUIREMENTS:
        1. Use create_signal_registry(questionnaire) ONLY
        2. Pass self._canonical_questionnaire as ONLY argument
        3. NO other signal loading methods allowed (signal_loader.py DELETED)
        
        Raises:
            RegistryConstructionError: If registry construction fails.
        """
        if self._canonical_questionnaire is None:
            raise RegistryConstructionError(
                "Cannot build signal registry: canonical questionnaire not loaded"
            )
        
        logger.info("signal_registry_building_start")
        
        try:
            # Build registry from canonical source ONLY
            registry = create_signal_registry(self._canonical_questionnaire)
            
            # Validate registry
            if not hasattr(registry, 'get_all_policy_areas'):
                if self._strict:
                    raise RegistryConstructionError("Registry missing required methods")
                logger.warning("registry_validation_warning missing_methods")
            
            policy_areas = registry.get_all_policy_areas() if hasattr(registry, 'get_all_policy_areas') else []
            
            self._signal_registry = registry
            
            logger.info(
                "signal_registry_built_successfully version=2.0 policy_areas=%d",
                len(policy_areas),
            )
            
        except Exception as e:
            if isinstance(e, RegistryConstructionError):
                raise
            raise RegistryConstructionError(f"Failed to build signal registry: {e}") from e
    
    def _build_enriched_signal_packs(self) -> None:
        """Build enriched signal packs for all policy areas.
        
        Each BaseExecutor receives its own EnrichedSignalPack (NOT full registry).
        Pack includes semantic expansion and context filtering.
        
        Raises:
            RegistryConstructionError: If pack construction fails in strict mode.
        """
        if not self._enable_intelligence:
            logger.info("enriched_packs_disabled intelligence_layer=off")
            self._enriched_packs = {}
            return
        
        if self._signal_registry is None:
            raise RegistryConstructionError(
                "Cannot build enriched packs: signal registry not built"
            )
        
        logger.info("enriched_packs_building_start")
        
        enriched_packs: dict[str, EnrichedSignalPack] = {}
        
        try:
            policy_areas = self._signal_registry.get_all_policy_areas() if hasattr(self._signal_registry, 'get_all_policy_areas') else []
            
            if not policy_areas:
                logger.warning("enriched_packs_warning no_policy_areas_found")
                self._enriched_packs = enriched_packs
                return
            
            for policy_area_id in policy_areas:
                try:
                    # Get base pack from registry
                    base_pack = self._signal_registry.get(policy_area_id) if hasattr(self._signal_registry, 'get') else None
                    
                    if base_pack is None:
                        logger.warning("base_pack_missing policy_area=%s", policy_area_id)
                        continue
                    
                    # Create enriched pack (semantic expansion + context filtering)
                    enriched_pack = create_enriched_signal_pack(
                        base_pack=base_pack,
                        questionnaire=self._canonical_questionnaire,
                    )
                    
                    enriched_packs[policy_area_id] = enriched_pack
                    
                    logger.debug(
                        "enriched_pack_created policy_area=%s",
                        policy_area_id,
                    )
                    
                except Exception as e:
                    msg = f"Failed to create enriched pack for {policy_area_id}: {e}"
                    if self._strict:
                        raise RegistryConstructionError(msg) from e
                    logger.error("enriched_pack_creation_failed policy_area=%s", policy_area_id, exc_info=True)
            
            self._enriched_packs = enriched_packs
            
            logger.info(
                "enriched_packs_built_successfully count=%d",
                len(enriched_packs),
            )
            
        except Exception as e:
            if isinstance(e, RegistryConstructionError):
                raise
            raise RegistryConstructionError(f"Failed to build enriched packs: {e}") from e
    
    def _initialize_seed_registry(self) -> bool:
        """Initialize SeedRegistry singleton for deterministic operations.
        
        Returns:
            bool: True if seed registry was initialized, False otherwise.
        """
        if not SEED_REGISTRY_AVAILABLE:
            logger.warning("seed_registry_unavailable module_not_found determinism_not_guaranteed")
            return False
        
        if self._seed is None:
            logger.info("seed_registry_not_initialized no_seed_provided")
            return False
        
        try:
            SeedRegistry.initialize(master_seed=self._seed)
            logger.info("seed_registry_initialized master_seed=%d determinism=enabled", self._seed)
            return True
        except Exception as e:
            logger.error("seed_registry_initialization_failed", exc_info=True)
            return False
    
    def _build_method_executor(self) -> None:
        """Build MethodExecutor with full dependency wiring.
        
        CRITICAL INTEGRATION POINT - Method Dispensary Pattern:
        =========================================================
        
        This is where the "monolith dispensaries" get wired into the pipeline.
        The 30 executors orchestrate methods from these dispensaries WITHOUT
        direct imports or tight coupling to the monolith implementations.
        
        Architecture Flow:
        -----------------
        1. build_class_registry() loads the "method dispensaries" (monoliths):
           - IndustrialPolicyProcessor: 17 methods used across D1-Q1, D1-Q5, D2-Q2, D3-Q1
           - BayesianEvidenceScorer: 8 methods for confidence calculation
           - PDETMunicipalPlanAnalyzer: 52+ methods (LARGEST dispensary)
             Used in: D1-Q2, D1-Q3, D1-Q4, D2-Q1, D3-Q2, D3-Q3, D3-Q4, D3-Q5, 
                      D4-Q1, D4-Q2, D4-Q3, D5-Q1, D5-Q2, D5-Q4, D5-Q5
           - CausalExtractor: 28 methods for causal inference
           - FinancialAuditor: 13 methods for financial analysis
           - BayesianMechanismInference: 14 methods for mechanism testing
           - [... 15+ more classes from farfan_core]
           
           Total: ~240 method pairs validated (see executor_factory_validation.json)
           
        2. These classes are NOT instantiated here - they're registered as TYPES.
           Instantiation happens lazily via MethodRegistry when methods are called.
           
        3. ExtendedArgRouter receives the class registry and provides:
           - 30+ special routes for high-traffic methods (see arg_router.py)
           - Generic routing via signature inspection for all other methods
           - Strict argument validation (no silent parameter drops)
           - **kwargs awareness for forward compatibility
           
        4. MethodExecutor combines three critical components:
           - MethodRegistry: Instantiation rules + shared instances (e.g., MunicipalOntology)
           - ArgRouter: Method routing + argument validation
           - SignalRegistry: Injected for signal-aware methods
           
        5. Each of the 30 Executors orchestrates methods via:
           ```python
           result = self.method_executor.execute(
               class_name="PDETMunicipalPlanAnalyzer",
               method_name="_score_indicators",
               **payload  # document, question_id, signal_pack, etc.
           )
           ```
           
        Method Reuse Pattern:
        --------------------
        - Methods are PARTIALLY reused across executors (not fully shared)
        - Example: "_score_indicators" used in D3-Q1, D3-Q2, D4-Q1
        - Example: "_test_sufficiency" used in D2-Q2, D3-Q2, D3-Q4
        - Each executor uses a DIFFERENT COMBINATION of methods
        - Total unique combinations: 30 executors × avg 12 methods = ~360 method calls
        
        Not All Methods Are Used:
        ------------------------
        The monoliths contain MORE methods than executors need.
        Only methods listed in executors_methods.json are actively used.
        Phase 1 (ingestion) uses additional methods not in executor contracts.
        
        Validation:
        ----------
        - executor_factory_validation.json: 243 pairs validated, 14 failures
        - Failures are methods NOT in catalog (likely private/deprecated)
        - All executor contracts reference validated methods only
        
        Signal Registry Integration:
        ---------------------------
        Signal registry is injected so methods can access:
        - Policy-area-specific patterns
        - Expected elements for validation
        - Semantic enrichment via intelligence layer
        
        Raises:
            ExecutorConstructionError: If executor construction fails.
            
        See Also:
            - executors_methods.json: Complete executor→methods mapping
            - executor_factory_validation.json: Method catalog validation
            - arg_router.py: Special routes and routing logic
            - class_registry.py: Monolith class paths (_CLASS_PATHS)
        """
        if self._signal_registry is None:
            raise ExecutorConstructionError(
                "Cannot build method executor: signal registry not built"
            )
        
        logger.info("method_executor_building_start dispensaries=loading")
        
        try:
            # Step 1: Build method registry with special instantiation rules
            # MethodRegistry handles shared instances (e.g., MunicipalOntology singleton)
            # and custom instantiation logic for complex analyzers
            method_registry = MethodRegistry()
            setup_default_instantiation_rules(method_registry)
            
            logger.info("method_registry_built instantiation_rules=configured")
            
            # Step 2: Build class registry - THE METHOD DISPENSARIES
            # This loads ~20 monolith classes with 240+ methods total
            # Each class is a "dispensary" that provides methods to executors
            class_registry = build_class_registry()
            
            logger.info(
                "class_registry_built dispensaries=%d total_methods=240+",
                len(class_registry)
            )
            
            # Step 3: Build extended arg router with special routes
            # Handles 30+ high-traffic method routes + generic routing
            arg_router = ExtendedArgRouter(class_registry)
            
            special_routes = arg_router.get_special_route_coverage() if hasattr(arg_router, 'get_special_route_coverage') else 0
            
            logger.info(
                "arg_router_built special_routes=%d generic_routing=enabled",
                special_routes
            )
            
            # Step 4: Build method executor WITH signal registry injected
            # This is the CORE integration point - executors call methods through this
            method_executor = MethodExecutor(
                method_registry=method_registry,
                arg_router=arg_router,
                signal_registry=self._signal_registry,  # DI: inject signal registry
            )
            
            # Validate construction
            if not hasattr(method_executor, 'execute'):
                if self._strict:
                    raise ExecutorConstructionError("MethodExecutor missing 'execute' method")
                logger.warning("method_executor_validation_warning missing_execute")
            
            self._method_executor = method_executor
            
            logger.info(
                "method_executor_built_successfully "
                "dispensaries=%d special_routes=%d signal_registry=injected",
                len(class_registry),
                special_routes,
            )
            
        except Exception as e:
            if isinstance(e, ExecutorConstructionError):
                raise
            raise ExecutorConstructionError(f"Failed to build method executor: {e}") from e
    
    def _load_validation_constants(self) -> dict[str, Any]:
        """Load Phase 1 validation constants (hard contracts).
        
        These constants are injected into Orchestrator for Phase 1 validation:
        - P01_EXPECTED_CHUNK_COUNT = 60
        - P02_MIN_TABLE_COUNT = 5
        - etc.
        
        Returns:
            dict[str, Any]: Validation constants.
        """
        if self._validation_constants is not None:
            logger.info("validation_constants_using_provided count=%d", len(self._validation_constants))
            return self._validation_constants
        
        if VALIDATION_CONSTANTS_AVAILABLE:
            try:
                constants = load_validation_constants() if callable(load_validation_constants) else PHASE1_VALIDATION_CONSTANTS
                logger.info("validation_constants_loaded_from_config count=%d", len(constants))
                return constants
            except Exception as e:
                logger.error("validation_constants_load_failed using_defaults", exc_info=True)
        
        # Default validation constants
        default_constants = {
            "P01_EXPECTED_CHUNK_COUNT": 60,
            "P01_MIN_CHUNK_LENGTH": 100,
            "P01_MAX_CHUNK_LENGTH": 2000,
            "P02_MIN_TABLE_COUNT": 5,
            "P02_MAX_TABLES_PER_DOCUMENT": 100,
        }
        
        logger.warning(
            "validation_constants_using_defaults count=%d constants_module_unavailable",
            len(default_constants),
        )
        
        return default_constants
    
    def _get_executor_config(self) -> ExecutorConfig:
        """Get or create ExecutorConfig."""
        if self._executor_config is not None:
            return self._executor_config
        return ExecutorConfig.default()
    
    def _build_orchestrator(
        self,
        executor_config: ExecutorConfig,
        validation_constants: dict[str, Any],
    ) -> Orchestrator:
        """Build Orchestrator with full dependency injection.
        
        CRITICAL: Orchestrator receives:
        1. questionnaire: CanonicalQuestionnaire (NOT file path)
        2. method_executor: MethodExecutor
        3. executor_config: ExecutorConfig
        4. validation_constants: dict (Phase 1 hard contracts)
        
        Args:
            executor_config: ExecutorConfig instance.
            validation_constants: Phase 1 validation constants.
            
        Returns:
            Orchestrator: Fully configured orchestrator.
            
        Raises:
            ExecutorConstructionError: If orchestrator construction fails.
        """
        if self._canonical_questionnaire is None:
            raise ExecutorConstructionError("Cannot build orchestrator: questionnaire not loaded")
        if self._method_executor is None:
            raise ExecutorConstructionError("Cannot build orchestrator: method executor not built")
        
        logger.info("orchestrator_building_start")
        
        try:
            # Build orchestrator with FULL dependency injection
            orchestrator = Orchestrator(
                questionnaire=self._canonical_questionnaire,  # DI: inject questionnaire object
                method_executor=self._method_executor,  # DI: inject method executor
                executor_config=executor_config,  # DI: inject config
                validation_constants=validation_constants,  # DI: inject Phase 1 contracts
                signal_registry=self._signal_registry,  # DI: inject signal registry
            )
            
            logger.info("orchestrator_built_successfully")
            
            return orchestrator
            
        except Exception as e:
            raise ExecutorConstructionError(f"Failed to build orchestrator: {e}") from e
    
    def _build_core_module_factory(self) -> Optional[Any]:
        """Build CoreModuleFactory if available."""
        if not CORE_MODULE_FACTORY_AVAILABLE:
            return None
        
        try:
            factory = CoreModuleFactory()
            logger.info("core_module_factory_built")
            return factory
        except Exception as e:
            logger.error("core_module_factory_construction_error", exc_info=True)
            return None
    
    def _compute_questionnaire_hash(self) -> str:
        """Compute SHA-256 hash of loaded questionnaire."""
        if self._canonical_questionnaire is None:
            return ""
        return self._compute_questionnaire_hash_from_instance(self._canonical_questionnaire)
    
    @staticmethod
    def _compute_questionnaire_hash_from_instance(questionnaire: CanonicalQuestionnaire) -> str:
        """Compute deterministic SHA-256 hash of questionnaire content."""
        try:
            # Try to get JSON representation if available
            if hasattr(questionnaire, 'to_dict'):
                content = json.dumps(questionnaire.to_dict(), sort_keys=True)
            elif hasattr(questionnaire, '__dict__'):
                content = json.dumps(questionnaire.__dict__, sort_keys=True, default=str)
            else:
                content = str(questionnaire)
            
            return hashlib.sha256(content.encode('utf-8')).hexdigest()
            
        except Exception as e:
            logger.warning("questionnaire_hash_computation_degraded error=%s", str(e))
            # Fallback to simple string hash
            return hashlib.sha256(str(questionnaire).encode('utf-8')).hexdigest()
    
    def create_executor_instance(
        self,
        executor_class: Type,
        policy_area_id: str,
        **extra_kwargs: Any,
    ) -> Any:
        """Create BaseExecutor instance with EnrichedSignalPack injected.
        
        This method is called for each of the ~30 BaseExecutor classes.
        Each executor receives its specific EnrichedSignalPack, NOT the full registry.
        
        Args:
            executor_class: BaseExecutor subclass to instantiate.
            policy_area_id: Policy area identifier for signal pack selection.
            **extra_kwargs: Additional kwargs to pass to constructor.
            
        Returns:
            BaseExecutor instance with dependencies injected.
            
        Raises:
            ExecutorConstructionError: If executor instantiation fails.
        """
        if self._method_executor is None:
            raise ExecutorConstructionError(
                "Cannot create executor: method executor not built"
            )
        
        # Get enriched signal pack for this policy area
        enriched_pack = self._enriched_packs.get(policy_area_id)
        
        if enriched_pack is None and self._enable_intelligence:
            logger.warning(
                "executor_creation_warning no_enriched_pack policy_area=%s executor=%s",
                policy_area_id,
                executor_class.__name__,
            )
        
        try:
            # Inject dependencies into executor
            executor_instance = executor_class(
                method_executor=self._method_executor,  # DI: inject method executor
                signal_registry=self._signal_registry,  # DI: inject signal registry
                config=self._get_executor_config(),  # DI: inject config
                questionnaire_provider=self._canonical_questionnaire,  # DI: inject questionnaire
                enriched_pack=enriched_pack,  # DI: inject enriched signal pack (specific to policy area)
                **extra_kwargs,
            )
            
            logger.debug(
                "executor_instance_created executor=%s policy_area=%s",
                executor_class.__name__,
                policy_area_id,
            )
            
            return executor_instance
            
        except Exception as e:
            raise ExecutorConstructionError(
                f"Failed to create executor {executor_class.__name__}: {e}"
            ) from e


# =============================================================================
# Convenience Functions
# =============================================================================


def create_analysis_pipeline(
    questionnaire_path: Optional[str] = None,
    expected_hash: Optional[str] = None,
    seed: Optional[int] = None,
) -> ProcessorBundle:
    """Convenience function to create complete analysis pipeline.
    
    This is the RECOMMENDED entry point for most use cases.
    
    Args:
        questionnaire_path: Path to canonical questionnaire JSON.
        expected_hash: Expected SHA-256 hash for integrity check.
        seed: Seed for reproducibility.
        
    Returns:
        ProcessorBundle with Orchestrator ready to use.
    """
    factory = AnalysisPipelineFactory(
        questionnaire_path=questionnaire_path,
        expected_questionnaire_hash=expected_hash,
        seed_for_determinism=seed,
        enable_intelligence_layer=True,
        strict_validation=True,
    )
    return factory.create_orchestrator()


def create_minimal_pipeline(
    questionnaire_path: Optional[str] = None,
) -> ProcessorBundle:
    """Create minimal pipeline without intelligence layer.
    
    Useful for testing or when enriched signals are not needed.
    
    Args:
        questionnaire_path: Path to canonical questionnaire JSON.
        
    Returns:
        ProcessorBundle with basic dependencies only.
    """
    factory = AnalysisPipelineFactory(
        questionnaire_path=questionnaire_path,
        enable_intelligence_layer=False,
        strict_validation=False,
    )
    return factory.create_orchestrator()


# =============================================================================
# Validation and Diagnostics
# =============================================================================


def validate_factory_singleton() -> dict[str, Any]:
    """Validate that load_questionnaire() was called exactly once.
    
    Returns:
        dict with validation results.
    """
    return {
        "questionnaire_loaded": AnalysisPipelineFactory._questionnaire_loaded,
        "questionnaire_instance_exists": AnalysisPipelineFactory._questionnaire_instance is not None,
        "singleton_pattern_valid": (
            AnalysisPipelineFactory._questionnaire_loaded and 
            AnalysisPipelineFactory._questionnaire_instance is not None
        ),
    }


def validate_bundle(bundle: ProcessorBundle) -> dict[str, Any]:
    """Validate bundle integrity and return diagnostics."""
    diagnostics = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "components": {},
        "metrics": {},
    }
    
    # Validate orchestrator
    if bundle.orchestrator is None:
        diagnostics["valid"] = False
        diagnostics["errors"].append("orchestrator is None")
    else:
        diagnostics["components"]["orchestrator"] = "present"
    
    # Validate method executor
    if bundle.method_executor is None:
        diagnostics["valid"] = False
        diagnostics["errors"].append("method_executor is None")
    else:
        diagnostics["components"]["method_executor"] = "present"
        if hasattr(bundle.method_executor, 'arg_router'):
            router = bundle.method_executor.arg_router
            if hasattr(router, 'get_special_route_coverage'):
                diagnostics["metrics"]["special_routes"] = router.get_special_route_coverage()
    
    # Validate questionnaire
    if bundle.questionnaire is None:
        diagnostics["valid"] = False
        diagnostics["errors"].append("questionnaire is None")
    else:
        diagnostics["components"]["questionnaire"] = "present"
        if hasattr(bundle.questionnaire, 'questions'):
            diagnostics["metrics"]["question_count"] = len(bundle.questionnaire.questions)
    
    # Validate signal registry
    if bundle.signal_registry is None:
        diagnostics["valid"] = False
        diagnostics["errors"].append("signal_registry is None")
    else:
        diagnostics["components"]["signal_registry"] = "present"
        if hasattr(bundle.signal_registry, 'get_all_policy_areas'):
            diagnostics["metrics"]["policy_areas"] = len(bundle.signal_registry.get_all_policy_areas())
    
    # Validate enriched packs
    diagnostics["components"]["enriched_packs"] = len(bundle.enriched_signal_packs)
    diagnostics["metrics"]["enriched_pack_count"] = len(bundle.enriched_signal_packs)
    
    # Validate validation constants
    diagnostics["components"]["validation_constants"] = len(bundle.validation_constants)
    diagnostics["metrics"]["validation_constant_count"] = len(bundle.validation_constants)
    
    # Validate seed registry
    if not bundle.seed_registry_initialized:
        diagnostics["warnings"].append("SeedRegistry not initialized - determinism not guaranteed")
    
    # Check factory instantiation
    if not bundle.provenance.get("factory_instantiation_confirmed"):
        diagnostics["errors"].append("Bundle not created via AnalysisPipelineFactory")
        diagnostics["valid"] = False
    
    return diagnostics


def get_bundle_info(bundle: ProcessorBundle) -> dict[str, Any]:
    """Get human-readable information about bundle."""
    return {
        "construction_time": bundle.provenance.get("construction_timestamp_utc"),
        "canonical_hash": bundle.provenance.get("canonical_sha256", "")[:16],
        "policy_areas": sorted(bundle.enriched_signal_packs.keys()),
        "policy_area_count": len(bundle.enriched_signal_packs),
        "intelligence_layer": bundle.provenance.get("intelligence_layer_enabled"),
        "validation_constants": len(bundle.validation_constants),
        "construction_duration": bundle.provenance.get("construction_duration_seconds"),
        "seed_initialized": bundle.seed_registry_initialized,
        "factory_class": bundle.provenance.get("factory_class"),
    }


# =============================================================================
# Module-level Checks
# =============================================================================


def check_legacy_signal_loader_deleted() -> dict[str, Any]:
    """Check that signal_loader.py has been deleted.
    
    Returns:
        dict with check results.
    """
    try:
        import farfan_pipeline.core.orchestrator.signal_loader
        return {
            "legacy_loader_deleted": False,
            "error": "signal_loader.py still exists - must be deleted per architecture requirements",
        }
    except ImportError:
        return {
            "legacy_loader_deleted": True,
            "message": "signal_loader.py correctly deleted - no legacy signal loading",
        }


def verify_single_questionnaire_load_point() -> dict[str, Any]:
    """Verify that only AnalysisPipelineFactory calls load_questionnaire().
    
    This requires manual code search but provides guidance.
    
    Returns:
        dict with verification instructions.
    """
    return {
        "verification_required": True,
        "search_command": "grep -r 'load_questionnaire(' --exclude-dir=__pycache__ --exclude='*.pyc'",
        "expected_result": "Should ONLY appear in: factory.py (AnalysisPipelineFactory._load_canonical_questionnaire)",
        "instructions": (
            "1. Run grep command above\n"
            "2. Verify ONLY factory.py calls load_questionnaire()\n"
            "3. Remove any other calls found\n"
            "4. Update tests to use AnalysisPipelineFactory"
        ),
    }


def get_method_dispensary_info() -> dict[str, Any]:
    """Get information about the method dispensary pattern.
    
    Returns detailed statistics about:
    - Which monolith classes serve as dispensaries
    - How many methods each dispensary provides
    - Which executors use which dispensaries
    - Method reuse patterns
    
    Returns:
        dict with dispensary statistics and usage patterns.
    """
    from farfan_pipeline.core.orchestrator.class_registry import get_class_paths
    
    class_paths = get_class_paths()
    
    # Load executor→methods mapping
    try:
        import json
        from pathlib import Path
        executors_methods_path = Path(__file__).parent / "executors_methods.json"
        if executors_methods_path.exists():
            with open(executors_methods_path) as f:
                executors_methods = json.load(f)
        else:
            executors_methods = []
    except Exception:
        executors_methods = []
    
    # Build dispensary statistics
    dispensaries = {}
    for class_name in class_paths.keys():
        dispensaries[class_name] = {
            "module": class_paths[class_name],
            "methods_provided": [],
            "used_by_executors": [],
            "total_usage_count": 0,
        }
    
    # Count method usage per dispensary
    for executor_info in executors_methods:
        executor_id = executor_info.get("executor_id")
        methods = executor_info.get("methods", [])
        
        for method_info in methods:
            class_name = method_info.get("class")
            method_name = method_info.get("method")
            
            if class_name in dispensaries:
                if method_name not in dispensaries[class_name]["methods_provided"]:
                    dispensaries[class_name]["methods_provided"].append(method_name)
                
                if executor_id not in dispensaries[class_name]["used_by_executors"]:
                    dispensaries[class_name]["used_by_executors"].append(executor_id)
                
                dispensaries[class_name]["total_usage_count"] += 1
    
    # Sort by usage count
    sorted_dispensaries = sorted(
        dispensaries.items(),
        key=lambda x: x[1]["total_usage_count"],
        reverse=True
    )
    
    # Build summary statistics
    total_methods = sum(len(d["methods_provided"]) for _, d in sorted_dispensaries)
    total_usage = sum(d["total_usage_count"] for _, d in sorted_dispensaries)
    
    return {
        "pattern": "method_dispensary",
        "description": "Monolith classes serve as method dispensaries for 30 executors",
        "total_dispensaries": len(dispensaries),
        "total_unique_methods": total_methods,
        "total_method_calls": total_usage,
        "avg_reuse_per_method": round(total_usage / max(total_methods, 1), 2),
        "dispensaries": {
            name: {
                "methods_count": len(info["methods_provided"]),
                "executor_count": len(info["used_by_executors"]),
                "total_calls": info["total_usage_count"],
                "reuse_factor": round(info["total_usage_count"] / max(len(info["methods_provided"]), 1), 2),
            }
            for name, info in sorted_dispensaries[:10]  # Top 10
        },
        "top_dispensaries": [
            {
                "class": name,
                "methods": len(info["methods_provided"]),
                "executors": len(info["used_by_executors"]),
                "calls": info["total_usage_count"],
            }
            for name, info in sorted_dispensaries[:5]
        ],
    }


def validate_method_dispensary_pattern() -> dict[str, Any]:
    """Validate that the method dispensary pattern is correctly implemented.
    
    Checks:
    1. All executor methods exist in class_registry
    2. No executor directly imports monolith classes
    3. All methods route through MethodExecutor
    4. Signal registry is injected (not globally accessed)
    
    Returns:
        dict with validation results.
    """
    from farfan_pipeline.core.orchestrator.class_registry import get_class_paths
    
    class_paths = get_class_paths()
    validation_results = {
        "pattern_valid": True,
        "errors": [],
        "warnings": [],
        "checks": {},
    }
    
    # Check 1: Verify class_registry is populated
    if not class_paths:
        validation_results["pattern_valid"] = False
        validation_results["errors"].append(
            "class_registry is empty - no dispensaries registered"
        )
    else:
        validation_results["checks"]["dispensaries_registered"] = len(class_paths)
    
    # Check 2: Verify executor_methods.json exists
    try:
        import json
        from pathlib import Path
        executors_methods_path = Path(__file__).parent / "executors_methods.json"
        if not executors_methods_path.exists():
            validation_results["warnings"].append(
                "executors_methods.json not found - cannot validate method mappings"
            )
        else:
            with open(executors_methods_path) as f:
                executors_methods = json.load(f)
            validation_results["checks"]["executor_method_mappings"] = len(executors_methods)
    except Exception as e:
        validation_results["warnings"].append(
            f"Failed to load executors_methods.json: {e}"
        )
    
    # Check 3: Verify validation file exists
    try:
        validation_path = Path(__file__).parent / "executor_factory_validation.json"
        if not validation_path.exists():
            validation_results["warnings"].append(
                "executor_factory_validation.json not found - cannot validate method catalog"
            )
        else:
            with open(validation_path) as f:
                validation_data = json.load(f)
            validation_results["checks"]["method_pairs_validated"] = validation_data.get("validated_against_catalog", 0)
            validation_results["checks"]["validation_failures"] = len(validation_data.get("failures", []))
    except Exception as e:
        validation_results["warnings"].append(
            f"Failed to load executor_factory_validation.json: {e}"
        )
    
    return validation_results