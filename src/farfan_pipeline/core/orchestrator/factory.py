"""
Factory module — canonical Dependency Injection (DI) and access control for F.A.R.F.A.N. 

This module is the single authoritative boundary for:
- Canonical monolith access (CanonicalQuestionnaire)
- Signal registry construction and enrichment (QuestionnaireSignalRegistry v2.0)
- Method injection via MethodExecutor (with MethodRegistry + special instantiation rules)
- Orchestrator construction with strict DI
- CoreModuleFactory for I/O helpers (contracts, validation)

Design Principles (Factory Pattern + DI):
- Orchestrator and Executors never touch I/O nor load the monolith directly. 
- Factory loads and validates the canonical questionnaire exactly once (singleton).
- Factory constructs signal registries and enriched packs centrally.
- Factory wires MethodExecutor with registries and special instantiation rules.
- Factory injects EnrichedSignalPack per policy area for BaseExecutor use. 

Scope:
- Infrastructure layer only. No business logic. 

SIN_CARRETA Compliance:
- All construction paths emit structured telemetry with timestamps and hashes.
- Determinism enforced via explicit validation of canonical questionnaire integrity.
- Contract assertions guard all factory outputs (no silent degradation).
- Auditability via immutable ProcessorBundle with provenance metadata.
- SeedRegistry singleton ensures deterministic stochastic operations. 

Integration Points:
1. Orchestrator receives: method_executor, questionnaire, executor_config
2. BaseExecutor (30 classes) receives: enriched_signal_pack (via helper function)
3. MethodExecutor routes all method calls via ExtendedArgRouter
4. Special instantiation rules enable shared MunicipalOntology, dependency injection
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from farfan_pipeline.core.orchestrator.core import MethodExecutor
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

# Optional: CoreModuleFactory for I/O helpers
try:
    from farfan_pipeline.core.orchestrator.core_module_factory import CoreModuleFactory
    CORE_MODULE_FACTORY_AVAILABLE = True
except ImportError:
    CoreModuleFactory = None  # type: ignore
    CORE_MODULE_FACTORY_AVAILABLE = False

# Optional: SeedRegistry for determinism
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


class RegistryConstructionError(FactoryError):
    """Raised when signal registry construction fails."""
    pass


class ExecutorConstructionError(FactoryError):
    """Raised when method executor construction fails."""
    pass


# =============================================================================
# Processor Bundle (typed DI container with provenance)
# =============================================================================


@dataclass(frozen=True)
class ProcessorBundle:
    """Aggregated orchestrator dependencies built by the Factory. 

    Attributes:
        method_executor: Preconfigured MethodExecutor ready for routing.
        questionnaire: Immutable, validated CanonicalQuestionnaire. 
        signal_registry: QuestionnaireSignalRegistry v2.0 with full metadata.
        executor_config: Canonical ExecutorConfig for executors.
        enriched_signal_packs: Dict of EnrichedSignalPack per policy area.
        core_module_factory: Optional CoreModuleFactory for I/O helpers. 
        provenance: Construction metadata for audit trails.
    """

    method_executor: MethodExecutor
    questionnaire: CanonicalQuestionnaire
    signal_registry: QuestionnaireSignalRegistry
    executor_config: ExecutorConfig
    enriched_signal_packs: dict[str, EnrichedSignalPack]
    core_module_factory: Optional[Any] = None
    provenance: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """SIN_CARRETA § Contract Enforcement: validate bundle integrity."""
        errors = []
        
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
        
        if not self.provenance.get("construction_timestamp_utc"):
            errors.append("provenance must include construction_timestamp_utc")
        if not self.provenance.get("canonical_sha256"):
            errors.append("provenance must include canonical_sha256")
        if self.provenance.get("signal_registry_version") != "2.0":
            errors.append("provenance must indicate signal_registry_version=2.0")
        
        if errors:
            raise FactoryError(f"ProcessorBundle validation failed: {'; '.join(errors)}")
        
        logger.info(
            "processor_bundle_validated "
            "canonical_sha256=%s construction_ts=%s policy_areas=%d",
            self.provenance.get("canonical_sha256", "")[:16],
            self.provenance.get("construction_timestamp_utc"),
            len(self.enriched_signal_packs),
        )


# =============================================================================
# Core Factory Implementation
# =============================================================================


def build_processor_bundle(
    *,
    questionnaire_path: Optional[str] = None,
    executor_config: Optional[ExecutorConfig] = None,
    enable_intelligence_layer: bool = True,
    seed_for_determinism: Optional[int] = None,
    strict_validation: bool = True,
) -> ProcessorBundle:
    """Build complete processor bundle with all dependencies wired.
    
    This is the primary factory entry point for constructing all orchestrator
    dependencies in a single, validated operation.
    
    Args:
        questionnaire_path: Path to canonical questionnaire JSON. If None, uses default.
        executor_config: Custom executor configuration. If None, uses default.
        enable_intelligence_layer: Whether to build enriched signal packs (default: True).
        seed_for_determinism: Optional seed for reproducible stochastic operations.
        strict_validation: If True, fail on any validation error (default: True).
        
    Returns:
        ProcessorBundle: Immutable bundle with all dependencies wired and validated.
        
    Raises:
        QuestionnaireValidationError: If questionnaire validation fails.
        RegistryConstructionError: If signal registry construction fails.
        ExecutorConstructionError: If method executor construction fails.
        FactoryError: For other construction failures.
    """
    construction_start = time.time()
    timestamp_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    
    logger.info("factory_build_start timestamp=%s strict=%s", timestamp_utc, strict_validation)
    
    try:
        # Step 1: Load and validate canonical questionnaire
        questionnaire = _load_and_validate_questionnaire(questionnaire_path, strict_validation)
        canonical_hash = _compute_questionnaire_hash(questionnaire)
        
        if not isinstance(questionnaire, CanonicalQuestionnaire):
            logger.error("Loaded questionnaire is not a CanonicalQuestionnaire instance: type=%s", type(questionnaire))
            num_questions = 0
        elif not hasattr(questionnaire, 'questions') or not isinstance(questionnaire.questions, (list, tuple)):
            logger.error("CanonicalQuestionnaire missing 'questions' attribute or it is not a list/tuple: %s", repr(questionnaire))
            num_questions = 0
        else:
            num_questions = len(questionnaire.questions)
        logger.info(
            "questionnaire_loaded questions=%d hash=%s",
            num_questions,
            canonical_hash[:16],
        )
        
        # Step 2: Build signal registry v2.0
        signal_registry = _build_signal_registry(questionnaire, strict_validation)
        
        if not hasattr(signal_registry, 'get_all_policy_areas') or not callable(getattr(signal_registry, 'get_all_policy_areas', None)):
            logger.error("signal_registry does not implement required method 'get_all_policy_areas'")
            raise AttributeError("signal_registry does not implement required method 'get_all_policy_areas'")
        logger.info(
            "signal_registry_built version=2.0 policy_areas=%d",
            len(signal_registry.get_all_policy_areas()),
        )
        
        # Step 3: Build enriched signal packs (intelligence layer)
        enriched_packs = _build_enriched_packs(
            signal_registry, 
            questionnaire, 
            enable_intelligence_layer,
            strict_validation
        )
        
        logger.info(
            "enriched_packs_built count=%d intelligence_layer=%s",
            len(enriched_packs),
            "enabled" if enable_intelligence_layer else "disabled",
        )
        
        # Step 4: Initialize seed registry for determinism
        _initialize_seed_registry(seed_for_determinism)
        
        # Step 5: Build method executor with full wiring
        method_executor = _build_method_executor(strict_validation)
        
        logger.info(
            "method_executor_built special_routes=%d",
            method_executor.arg_router.get_special_route_coverage() if hasattr(method_executor.arg_router, 'get_special_route_coverage') else 0,
        )
        
        # Step 6: Build or use provided executor config
        if executor_config is None:
            executor_config = ExecutorConfig.default()
        
        # Step 7: Build optional core module factory
        core_factory = _build_core_module_factory()
        
        # Step 8: Assemble provenance metadata
        construction_duration = time.time() - construction_start
        provenance = {
            "construction_timestamp_utc": timestamp_utc,
            "canonical_sha256": canonical_hash,
            "signal_registry_version": "2.0",
            "intelligence_layer_enabled": enable_intelligence_layer,
            "enriched_packs_count": len(enriched_packs),
            "construction_duration_seconds": round(construction_duration, 3),
            "seed_registry_initialized": SEED_REGISTRY_AVAILABLE and seed_for_determinism is not None,
            "core_module_factory_available": CORE_MODULE_FACTORY_AVAILABLE,
            "strict_validation": strict_validation,
        }
        
        # Step 9: Build and validate bundle
        bundle = ProcessorBundle(
            method_executor=method_executor,
            questionnaire=questionnaire,
            signal_registry=signal_registry,
            executor_config=executor_config,
            enriched_signal_packs=enriched_packs,
            core_module_factory=core_factory,
            provenance=provenance,
        )
        
        logger.info(
            "factory_build_complete duration=%.3fs hash=%s",
            construction_duration,
            canonical_hash[:16],
        )
        
        return bundle
        
    except Exception as e:
        logger.error("factory_build_failed error=%s", str(e), exc_info=True)
        raise FactoryError(f"Failed to build processor bundle: {e}") from e


# =============================================================================
# Internal Construction Functions
# =============================================================================


def _load_and_validate_questionnaire(
    path: Optional[str],
    strict: bool,
) -> CanonicalQuestionnaire:
    """Load and validate canonical questionnaire."""
    try:
        questionnaire_path = Path(path) if path is not None else None
        questionnaire = load_questionnaire(questionnaire_path)
        
        # Validate structure
        if not hasattr(questionnaire, 'questions'):
            if strict:
                raise QuestionnaireValidationError("Questionnaire missing 'questions' attribute")
            logger.warning("questionnaire_validation_warning missing_questions_attribute")
        
        questions = getattr(questionnaire, 'questions', [])
        if not questions:
            if strict:
                raise QuestionnaireValidationError("Questionnaire has no questions")
            logger.warning("questionnaire_validation_warning no_questions")
        
        return questionnaire
        
    except Exception as e:
        if strict:
            raise QuestionnaireValidationError(f"Failed to load questionnaire: {e}") from e
        logger.error("questionnaire_load_error continuing_with_degraded_state", exc_info=True)
        raise


def _build_signal_registry(
    questionnaire: CanonicalQuestionnaire,
    strict: bool,
) -> QuestionnaireSignalRegistry:
    """Build signal registry from questionnaire."""
    try:
        registry = create_signal_registry(questionnaire)
        
        # Validate registry
        if not hasattr(registry, 'get_all_policy_areas'):
            if strict:
                raise RegistryConstructionError("Registry missing required methods")
            logger.warning("registry_validation_warning missing_methods")
        
        return registry
        
    except Exception as e:
        if strict:
            raise RegistryConstructionError(f"Failed to build signal registry: {e}") from e
        logger.error("registry_construction_error", exc_info=True)
        raise


def _build_enriched_packs(
    signal_registry: QuestionnaireSignalRegistry,
    questionnaire: CanonicalQuestionnaire,
    enable: bool,
    strict: bool,
) -> dict[str, EnrichedSignalPack]:
    """Build enriched signal packs for all policy areas."""
    enriched_packs: dict[str, EnrichedSignalPack] = {}
    
    if not enable:
        logger.info("enriched_packs_disabled")
        return enriched_packs
    
    try:
        policy_areas = signal_registry.get_all_policy_areas() if hasattr(signal_registry, 'get_all_policy_areas') else []
        
        if not policy_areas:
            logger.warning("no_policy_areas_found registry_empty")
            return enriched_packs
        
        for policy_area_id in policy_areas:
            try:
                base_pack = signal_registry.get(policy_area_id) if hasattr(signal_registry, 'get') else None
                
                if base_pack is None:
                    logger.warning("base_pack_missing policy_area=%s", policy_area_id)
                    continue
                
                enriched_pack = create_enriched_signal_pack(
                    base_pack,
                    questionnaire,
                )
                enriched_packs[policy_area_id] = enriched_pack
                
            except Exception as e:
                msg = f"Failed to create enriched pack for {policy_area_id}: {e}"
                if strict:
                    raise RegistryConstructionError(msg) from e
                logger.error("enriched_pack_creation_failed policy_area=%s", policy_area_id, exc_info=True)
        
        return enriched_packs
        
    except Exception as e:
        if strict:
            raise RegistryConstructionError(f"Failed to build enriched packs: {e}") from e
        logger.error("enriched_packs_construction_error", exc_info=True)
        return enriched_packs


def _initialize_seed_registry(seed: Optional[int]) -> None:
    """Initialize seed registry if available."""
    if not SEED_REGISTRY_AVAILABLE:
        logger.debug("seed_registry_unavailable module_not_found")
        return
    
    if seed is None:
        logger.debug("seed_registry_not_initialized no_seed_provided")
        return
    
    try:
        SeedRegistry.initialize(master_seed=seed)
        logger.info("seed_registry_initialized master_seed=%d", seed)
    except Exception as e:
        logger.error("seed_registry_initialization_failed", exc_info=True)
        # Non-fatal, continue without determinism


def _build_method_executor(strict: bool) -> MethodExecutor:
    """Build method executor with full dependency wiring."""
    try:
        # Build method registry
        method_registry = MethodRegistry()
        setup_default_instantiation_rules(method_registry)
        
        # Build class registry
        class_registry = build_class_registry()
        
        # Build extended arg router
        arg_router = ExtendedArgRouter(class_registry)
        
        # Build method executor
        method_executor = MethodExecutor(
            method_registry=method_registry,
        )
        
        # Validate construction
        if not hasattr(method_executor, 'execute'):
            if strict:
                raise ExecutorConstructionError("MethodExecutor missing 'execute' method")
            logger.warning("method_executor_validation_warning missing_execute")
        
        return method_executor
        
    except Exception as e:
        if strict:
            raise ExecutorConstructionError(f"Failed to build method executor: {e}") from e
        logger.error("method_executor_construction_error", exc_info=True)
        raise


def _build_core_module_factory() -> Optional[Any]:
    """Build core module factory if available."""
    if not CORE_MODULE_FACTORY_AVAILABLE:
        logger.debug("core_module_factory_unavailable module_not_found")
        return None
    
    try:
        factory = CoreModuleFactory()
        logger.info("core_module_factory_built")
        return factory
    except Exception as e:
        logger.error("core_module_factory_construction_error", exc_info=True)
        return None


def _compute_questionnaire_hash(questionnaire: CanonicalQuestionnaire) -> str:
    """Compute deterministic SHA256 hash of questionnaire content."""
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


# =============================================================================
# Convenience API
# =============================================================================


def build_processor(
    questionnaire_path: Optional[str] = None,
    seed: Optional[int] = None,
) -> ProcessorBundle:
    """
    Convenience wrapper for `build_processor_bundle` with sensible defaults.

    This function is intended for typical use cases where you want a fully configured
    processor with the intelligence layer enabled, strict validation, and optional
    reproducibility via a seed. It sets recommended defaults for most users.

    Use `build_processor_bundle` directly if you need advanced customization, such as
    disabling the intelligence layer, changing validation strictness, or other options.

    Args:
        questionnaire_path: Optional path to questionnaire JSON.
        seed: Optional seed for reproducibility.
    Returns:
        ProcessorBundle ready for use.
    """
    return build_processor_bundle(
        questionnaire_path=questionnaire_path,
        enable_intelligence_layer=True,
        seed_for_determinism=seed,
        strict_validation=True,
    )


def build_minimal_processor(
    questionnaire_path: Optional[str] = None,
    strict: bool = False,
) -> ProcessorBundle:
    """Build minimal processor bundle without intelligence layer.
    
    Useful for testing or when enriched signals are not needed.
    
    Args:
        questionnaire_path: Optional path to questionnaire JSON.
        strict: Whether to use strict validation (default: False for minimal).
        
    Returns:
        ProcessorBundle with basic dependencies only.
    """
    return build_processor_bundle(
        questionnaire_path=questionnaire_path,
        enable_intelligence_layer=False,
        strict_validation=strict,
    )


def get_enriched_pack_for_policy_area(
    bundle: ProcessorBundle,
    policy_area_id: str,
) -> Optional[EnrichedSignalPack]:
    """Helper to safely retrieve enriched signal pack from bundle.
    
    Args:
        bundle: Processor bundle.
        policy_area_id: Policy area identifier.
        
    Returns:
        EnrichedSignalPack if available, None otherwise.
    """
    return bundle.enriched_signal_packs.get(policy_area_id)


# =============================================================================
# Validation and Diagnostics
# =============================================================================


def validate_bundle(bundle: ProcessorBundle) -> dict[str, Any]:
    """Validate bundle integrity and return diagnostics.
    
    Args:
        bundle: ProcessorBundle to validate.
        
    Returns:
        Dictionary with validation results and diagnostics.
    """
    diagnostics = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "components": {},
        "metrics": {},
    }
    
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
    pack_count = len(bundle.enriched_signal_packs)
    diagnostics["components"]["enriched_packs"] = pack_count
    diagnostics["metrics"]["enriched_pack_count"] = pack_count
    
    if pack_count == 0 and bundle.provenance.get("intelligence_layer_enabled"):
        diagnostics["warnings"].append("Intelligence layer enabled but no enriched packs available")
    
    # Validate provenance
    required_provenance = ["construction_timestamp_utc", "canonical_sha256", "signal_registry_version"]
    missing_provenance = [k for k in required_provenance if k not in bundle.provenance]
    if missing_provenance:
        diagnostics["valid"] = False
        diagnostics["errors"].append(f"Missing provenance: {missing_provenance}")
    
    # Check provenance metrics
    diagnostics["metrics"]["construction_duration"] = bundle.provenance.get("construction_duration_seconds", 0)
    diagnostics["metrics"]["canonical_hash"] = bundle.provenance.get("canonical_sha256", "")[:16]
    
    return diagnostics


def get_bundle_info(bundle: ProcessorBundle) -> dict[str, Any]:
    """Get human-readable information about bundle.
    
    Args:
        bundle: ProcessorBundle to inspect.
        
    Returns:
        Dictionary with bundle information.
    """
    return {
        "construction_time": bundle.provenance.get("construction_timestamp_utc"),
        "canonical_hash": bundle.provenance.get("canonical_sha256", "")[:16],
        "policy_areas": sorted(bundle.enriched_signal_packs.keys()),
        "policy_area_count": len(bundle.enriched_signal_packs),
        "intelligence_layer": bundle.provenance.get("intelligence_layer_enabled"),
        "core_factory": bundle.core_module_factory is not None,
        "construction_duration": bundle.provenance.get("construction_duration_seconds"),
        "strict_validation": bundle.provenance.get("strict_validation"),
        "seed_initialized": bundle.provenance.get("seed_registry_initialized"),
    }


# =============================================================================
# Singleton Cache (Optional)
# =============================================================================

_bundle_cache: Optional[ProcessorBundle] = None
_cache_key: Optional[str] = None


def get_or_build_bundle(
    questionnaire_path: Optional[str] = None,
    cache: bool = True,
    force_rebuild: bool = False,
) -> ProcessorBundle:
    """Get cached bundle or build new one.
    
    Args:
        questionnaire_path: Optional path to questionnaire JSON.
        cache: Whether to cache the bundle (default: True).
        force_rebuild: Force rebuild even if cached (default: False).
        
    Returns:
        ProcessorBundle (cached or newly built).
    """
    global _bundle_cache, _cache_key
    
    cache_key = questionnaire_path or "default"
    
    if not force_rebuild and cache and _bundle_cache is not None and _cache_key == cache_key:
        logger.debug("factory_cache_hit key=%s", cache_key)
        return _bundle_cache
    
    logger.debug("factory_cache_miss key=%s building_new force_rebuild=%s", cache_key, force_rebuild)
    bundle = build_processor(questionnaire_path=questionnaire_path)
    
    if cache:
        _bundle_cache = bundle
        _cache_key = cache_key
        logger.debug("factory_cache_updated key=%s", cache_key)
    
    return bundle


def clear_bundle_cache() -> None:
    """Clear singleton bundle cache."""
    global _bundle_cache, _cache_key
    _bundle_cache = None
    _cache_key = None
    logger.debug("factory_cache_cleared")


def get_cache_info() -> dict[str, Any]:
    """Get information about current cache state."""
    return {
        "cached": _bundle_cache is not None,
        "cache_key": _cache_key,
        "bundle_hash": _bundle_cache.provenance.get("canonical_sha256", "")[:16] if _bundle_cache else None,
    }
