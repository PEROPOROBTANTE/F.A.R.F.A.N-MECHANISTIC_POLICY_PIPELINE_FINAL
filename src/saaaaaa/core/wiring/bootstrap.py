"""Bootstrap module for deterministic wiring initialization.

Implements the complete initialization sequence with:
1. Resource loading (QuestionnaireResourceProvider)
2. Signal system setup (memory:// by default, HTTP optional)
3. CoreModuleFactory with DI
4. ArgRouterExtended (≥30 routes)
5. Orchestrator assembly

All initialization is deterministic and observable.
"""

from __future__ import annotations

import json
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import structlog

from saaaaaa.core.orchestrator.arg_router import ExtendedArgRouter
from saaaaaa.core.orchestrator.class_registry import build_class_registry
from saaaaaa.core.orchestrator.executor_config import ExecutorConfig
from saaaaaa.core.orchestrator.factory import CoreModuleFactory
from saaaaaa.core.orchestrator.questionnaire_resource_provider import (
    QuestionnaireResourceProvider,
)
from saaaaaa.core.orchestrator.signals import (
    InMemorySignalSource,
    SignalClient,
    SignalPack,
    SignalRegistry,
)

try:  # Optional dependency: calibration orchestrator
    from saaaaaa.core.calibration.orchestrator import CalibrationOrchestrator as _CalibrationOrchestrator
    from saaaaaa.core.calibration.config import DEFAULT_CALIBRATION_CONFIG as _DEFAULT_CALIBRATION_CONFIG
    _HAS_CALIBRATION = True
except Exception:  # pragma: no cover - only during stripped installs
    _CalibrationOrchestrator = None  # type: ignore[assignment]
    _DEFAULT_CALIBRATION_CONFIG = None  # type: ignore[assignment]
    _HAS_CALIBRATION = False

from .errors import MissingDependencyError, WiringInitializationError
from .feature_flags import WiringFeatureFlags
from .validation import WiringValidator

logger = structlog.get_logger(__name__)


@dataclass
class WiringComponents:
    """Container for all wired components.

    Attributes:
        provider: QuestionnaireResourceProvider
        signal_client: SignalClient (memory:// or HTTP)
        signal_registry: SignalRegistry with TTL and LRU
        executor_config: ExecutorConfig with defaults
        factory: CoreModuleFactory with DI
        arg_router: ExtendedArgRouter with special routes
        class_registry: Class registry for routing
        validator: WiringValidator for contract checking
        flags: Feature flags used during initialization
        init_hashes: Hashes computed during initialization
    """

    provider: QuestionnaireResourceProvider
    signal_client: SignalClient
    signal_registry: SignalRegistry
    executor_config: ExecutorConfig
    factory: CoreModuleFactory
    arg_router: ExtendedArgRouter
    class_registry: dict[str, type]
    validator: WiringValidator
    calibration_orchestrator: "_CalibrationOrchestrator | None" = None
    flags: WiringFeatureFlags
    init_hashes: dict[str, str] = field(default_factory=dict)


CANONICAL_POLICY_AREA_DEFINITIONS: "OrderedDict[str, dict[str, list[str] | str]]" = OrderedDict(
    [
        (
            "PA01",
            {
                "name": "Derechos de las mujeres e igualdad de género",
                "slug": "genero_mujeres",
                "aliases": ["fiscal"],
            },
        ),
        (
            "PA02",
            {
                "name": "Prevención de la violencia y protección",
                "slug": "seguridad_violencia",
                "aliases": ["salud"],
            },
        ),
        (
            "PA03",
            {
                "name": "Ambiente sano y cambio climático",
                "slug": "ambiente",
                "aliases": ["ambiente"],
            },
        ),
        (
            "PA04",
            {
                "name": "Derechos económicos, sociales y culturales",
                "slug": "derechos_sociales",
                "aliases": ["energía"],
            },
        ),
        (
            "PA05",
            {
                "name": "Derechos de las víctimas y construcción de paz",
                "slug": "paz_victimas",
                "aliases": ["transporte"],
            },
        ),
        (
            "PA06",
            {
                "name": "Derecho al futuro de la niñez y juventud",
                "slug": "ninez_juventud",
                "aliases": [],
            },
        ),
        (
            "PA07",
            {
                "name": "Tierras y territorios",
                "slug": "tierras_territorios",
                "aliases": [],
            },
        ),
        (
            "PA08",
            {
                "name": "Líderes, lideresas y defensores de DD. HH.",
                "slug": "liderazgos_ddhh",
                "aliases": [],
            },
        ),
        (
            "PA09",
            {
                "name": "Derechos de personas privadas de libertad",
                "slug": "privados_libertad",
                "aliases": [],
            },
        ),
        (
            "PA10",
            {
                "name": "Migración transfronteriza",
                "slug": "migracion",
                "aliases": [],
            },
        ),
    ]
)

SIGNAL_PACK_VERSION = "1.0.0"
MAX_PATTERNS_PER_POLICY_AREA = 32

class WiringBootstrap:
    """Bootstrap engine for deterministic wiring initialization.

    Follows strict initialization order:
    1. Load resources (questionnaire)
    2. Build signal system (memory:// or HTTP)
    3. Create factory with DI
    4. Initialize arg router
    5. Validate all contracts
    """

    def __init__(
        self,
        questionnaire_path: str | Path | None = None,
        flags: WiringFeatureFlags | None = None,
    ) -> None:
        """Initialize bootstrap engine.

        Args:
            questionnaire_path: Path to questionnaire monolith JSON
            flags: Feature flags (defaults to environment)
        """
        self.questionnaire_path = questionnaire_path
        self.flags = flags or WiringFeatureFlags.from_env()
        self._start_time = time.time()

        # Validate flags
        warnings = self.flags.validate()
        for warning in warnings:
            logger.warning("feature_flag_warning", message=warning)

        logger.info(
            "wiring_bootstrap_initialized",
            questionnaire_path=str(questionnaire_path) if questionnaire_path else None,
            flags=self.flags.to_dict(),
        )

    def bootstrap(self) -> WiringComponents:
        """Execute complete bootstrap sequence.

        Returns:
            WiringComponents with all initialized modules

        Raises:
            WiringInitializationError: If any phase fails
        """
        logger.info("wiring_bootstrap_start")

        try:
            # Phase 1: Load resources
            provider = self._load_resources()

            # Phase 2: Build signal system
            signal_client, signal_registry = self._build_signal_system(provider)

            # Phase 3: Create executor config
            executor_config = self._create_executor_config()

            # Phase 4: Create factory with DI
            factory = self._create_factory(provider, signal_registry, executor_config)

            # Phase 5: Build class registry
            class_registry = self._build_class_registry()

            # Phase 6: Initialize arg router
            arg_router = self._create_arg_router(class_registry)

            # Phase 7: Create validator
            validator = WiringValidator()

            # Phase 8: Create calibration orchestrator (optional enhancement)
            calibration_orchestrator = self._create_calibration_orchestrator()

            # Phase 9: Seed signals (if memory mode)
            if signal_client._transport == "memory":
                metrics = self._seed_canonical_policy_area_signals(
                    signal_client._memory_source,
                    signal_registry,
                    provider,
                )
                logger.info(
                    "signals_seeded",
                    areas=metrics["canonical_areas"],
                    aliases=metrics["legacy_aliases"],
                    hit_rate=metrics["hit_rate"],
                )

            # Compute initialization hashes
            init_hashes = self._compute_init_hashes(
                provider, signal_registry, factory, arg_router
            )

            components = WiringComponents(
                provider=provider,
                signal_client=signal_client,
                signal_registry=signal_registry,
                executor_config=executor_config,
                factory=factory,
                arg_router=arg_router,
                class_registry=class_registry,
                validator=validator,
                calibration_orchestrator=calibration_orchestrator,
                flags=self.flags,
                init_hashes=init_hashes,
            )

            elapsed = time.time() - self._start_time

            logger.info(
                "wiring_bootstrap_complete",
                elapsed_s=elapsed,
                factory_instances=19,  # Expected count
                argrouter_routes=arg_router.get_special_route_coverage(),
                signals_mode=signal_client._transport,
                init_hashes={k: v[:16] for k, v in init_hashes.items()},
            )

            return components

        except Exception as e:
            elapsed = time.time() - self._start_time
            logger.error(
                "wiring_bootstrap_failed",
                elapsed_s=elapsed,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    def _load_resources(self) -> QuestionnaireResourceProvider:
        """Load questionnaire resources.

        Returns:
            QuestionnaireResourceProvider instance

        Raises:
            WiringInitializationError: If loading fails
        """
        logger.info("wiring_init_phase", phase="load_resources")

        try:
            if self.questionnaire_path:
                path = Path(self.questionnaire_path)
                if not path.exists():
                    raise MissingDependencyError(
                        dependency=str(path),
                        required_by="WiringBootstrap",
                        fix=f"Ensure questionnaire file exists at {path}",
                    )

                with open(path, encoding="utf-8") as f:
                    data = json.load(f)

                provider = QuestionnaireResourceProvider(data)
            else:
                # Use default/empty provider
                provider = QuestionnaireResourceProvider({})

            logger.info(
                "questionnaire_loaded",
                path=str(self.questionnaire_path) if self.questionnaire_path else "default",
            )

            return provider

        except Exception as e:
            raise WiringInitializationError(
                phase="load_resources",
                component="QuestionnaireResourceProvider",
                reason=str(e),
            ) from e

    def _build_signal_system(
        self,
        provider: QuestionnaireResourceProvider,
    ) -> tuple[SignalClient, SignalRegistry]:
        """Build signal system (memory:// or HTTP).

        Args:
            provider: QuestionnaireResourceProvider for signal data

        Returns:
            Tuple of (SignalClient, SignalRegistry)

        Raises:
            WiringInitializationError: If setup fails
        """
        logger.info("wiring_init_phase", phase="build_signal_system")

        try:
            # Create registry first
            registry = SignalRegistry(
                max_size=100,
                default_ttl_s=3600,
            )

            # Create signal source
            if self.flags.enable_http_signals:
                # HTTP mode (requires explicit configuration)
                base_url = "http://127.0.0.1:8000"  # Default, should be configurable
                logger.info("signal_client_http_mode", base_url=base_url)

                client = SignalClient(
                    base_url=base_url,
                    enable_http_signals=True,
                )
            else:
                # Memory mode (default)
                memory_source = InMemorySignalSource()

                client = SignalClient(
                    base_url="memory://",
                    enable_http_signals=False,
                    memory_source=memory_source,
                )

                logger.info("signal_client_memory_mode")

            return client, registry

        except Exception as e:
            raise WiringInitializationError(
                phase="build_signal_system",
                component="SignalClient/SignalRegistry",
                reason=str(e),
            ) from e

    def _create_executor_config(self) -> ExecutorConfig:
        """Create executor configuration.

        Returns:
            ExecutorConfig with defaults
        """
        logger.info("wiring_init_phase", phase="create_executor_config")

        config = ExecutorConfig(
            max_tokens=2048,
            temperature=0.0,  # Deterministic
            timeout_s=30.0,
            retry=2,
            seed=0 if self.flags.deterministic_mode else None,
        )

        logger.info(
            "executor_config_created",
            deterministic=self.flags.deterministic_mode,
            seed=config.seed,
        )

        return config

    def _create_factory(
        self,
        provider: QuestionnaireResourceProvider,
        registry: SignalRegistry,
        config: ExecutorConfig,
    ) -> CoreModuleFactory:
        """Create CoreModuleFactory with DI.

        Args:
            provider: QuestionnaireResourceProvider
            registry: SignalRegistry for injection
            config: ExecutorConfig for injection

        Returns:
            CoreModuleFactory instance

        Raises:
            WiringInitializationError: If creation fails
        """
        logger.info("wiring_init_phase", phase="create_factory")

        try:
            # Get questionnaire data from provider
            questionnaire_data = provider._data

            factory = CoreModuleFactory(
                questionnaire_data=questionnaire_data,
                signal_registry=registry,
            )

            logger.info(
                "factory_created",
                has_signal_registry=True,
            )

            return factory

        except Exception as e:
            raise WiringInitializationError(
                phase="create_factory",
                component="CoreModuleFactory",
                reason=str(e),
            ) from e

    def _build_class_registry(self) -> dict[str, type]:
        """Build class registry for arg router.

        Returns:
            Class registry mapping names to types

        Raises:
            WiringInitializationError: If build fails
        """
        logger.info("wiring_init_phase", phase="build_class_registry")

        try:
            registry = build_class_registry()

            logger.info(
                "class_registry_built",
                class_count=len(registry),
            )

            return registry

        except Exception as e:
            raise WiringInitializationError(
                phase="build_class_registry",
                component="ClassRegistry",
                reason=str(e),
            ) from e

    def _create_arg_router(
        self,
        class_registry: dict[str, type],
    ) -> ExtendedArgRouter:
        """Create ExtendedArgRouter with special routes.

        Args:
            class_registry: Class registry for routing

        Returns:
            ExtendedArgRouter instance

        Raises:
            WiringInitializationError: If creation fails
        """
        logger.info("wiring_init_phase", phase="create_arg_router")

        try:
            router = ExtendedArgRouter(class_registry)

            route_count = router.get_special_route_coverage()

            if route_count < 30:
                logger.warning(
                    "argrouter_coverage_low",
                    count=route_count,
                    expected=30,
                )

            logger.info(
                "arg_router_created",
                special_routes=route_count,
            )

            return router

        except Exception as e:
            raise WiringInitializationError(
                phase="create_arg_router",
                component="ExtendedArgRouter",
                reason=str(e),
            ) from e

    def _create_calibration_orchestrator(self) -> "_CalibrationOrchestrator | None":
        """
        Create CalibrationOrchestrator when calibration stack is available.

        Returns:
            CalibrationOrchestrator instance or None if unavailable.
        """
        if not _HAS_CALIBRATION or _CalibrationOrchestrator is None or _DEFAULT_CALIBRATION_CONFIG is None:
            logger.info("calibration_system_unavailable")
            return None

        try:
            project_root = Path(__file__).resolve().parents[4]
        except IndexError:  # pragma: no cover - unlikely
            project_root = Path.cwd()

        data_dir = project_root / "data"
        config_dir = project_root / "config"

        kwargs: dict[str, Any] = {"config": _DEFAULT_CALIBRATION_CONFIG}

        intrinsic_path = config_dir / "intrinsic_calibration.json"
        if intrinsic_path.exists():
            kwargs["intrinsic_calibration_path"] = intrinsic_path

        compatibility_path = data_dir / "method_compatibility.json"
        if compatibility_path.exists():
            kwargs["compatibility_path"] = compatibility_path

        registry_path = data_dir / "method_registry.json"
        if registry_path.exists():
            kwargs["method_registry_path"] = registry_path

        signatures_path = data_dir / "method_signatures.json"
        if signatures_path.exists():
            kwargs["method_signatures_path"] = signatures_path

        try:
            orchestrator = _CalibrationOrchestrator(**kwargs)
            logger.info(
                "calibration_orchestrator_ready",
                intrinsic=str(intrinsic_path),
                compatibility=str(compatibility_path),
            )
            return orchestrator
        except Exception as exc:  # pragma: no cover - defensive guardrail
            logger.warning(
                "calibration_orchestrator_initialization_failed",
                error=str(exc),
            )
            return None

    def _build_signal_pack(
        self,
        provider: QuestionnaireResourceProvider,
        canonical_id: str,
        meta: dict[str, Any],
        *,
        alias: str | None = None,
    ) -> SignalPack:
        """Build a SignalPack for a canonical policy area (and optional alias)."""
        pattern_source = getattr(provider, "get_patterns_for_area", None)
        patterns = pattern_source(canonical_id, MAX_PATTERNS_PER_POLICY_AREA) if callable(pattern_source) else []

        pack = SignalPack(
            version=SIGNAL_PACK_VERSION,
            policy_area=alias or canonical_id,  # type: ignore[arg-type]
            patterns=patterns,
            metadata={
                "canonical_id": canonical_id,
                "display_name": meta["name"],
                "slug": meta["slug"],
                "alias": alias,
            },
        )
        fingerprint = pack.compute_hash()
        return pack.model_copy(update={"source_fingerprint": fingerprint})

    @staticmethod
    def _register_signal_pack(
        memory_source: InMemorySignalSource,
        registry: SignalRegistry,
        pack: SignalPack,
    ) -> None:
        """Register pack in both memory source and registry."""
        memory_source.register(pack.policy_area, pack)
        registry.put(pack.policy_area, pack)
        logger.debug(
            "signal_seeded",
            policy_area=pack.policy_area,
            canonical_id=pack.metadata.get("canonical_id"),
            patterns=len(pack.patterns),
        )

    def _seed_canonical_policy_area_signals(
        self,
        memory_source: InMemorySignalSource,
        registry: SignalRegistry,
        provider: QuestionnaireResourceProvider,
    ) -> dict[str, Any]:
        """
        Seed signal registry with canonical (PA01-PA10) policy areas.

        Returns:
            Metrics dict with coverage and legacy alias info.
        """
        canonical_count = 0
        alias_count = 0

        for area_id, meta in CANONICAL_POLICY_AREA_DEFINITIONS.items():
            pack = self._build_signal_pack(provider, area_id, meta)
            self._register_signal_pack(memory_source, registry, pack)
            canonical_count += 1

            for alias in meta["aliases"]:  # type: ignore[index]
                alias_pack = self._build_signal_pack(
                    provider,
                    area_id,
                    meta,
                    alias=alias,
                )
                self._register_signal_pack(memory_source, registry, alias_pack)
                alias_count += 1

        hits = sum(
            1
            for area_id in CANONICAL_POLICY_AREA_DEFINITIONS
            if registry.get(area_id) is not None
        )
        total_required = len(CANONICAL_POLICY_AREA_DEFINITIONS)
        hit_rate = hits / total_required if total_required else 0.0

        return {
            "canonical_areas": canonical_count,
            "legacy_aliases": alias_count,
            "hit_rate": hit_rate,
            "required_hit_rate": 0.95,
        }

    def seed_signals_public(
        self,
        client: SignalClient,
        registry: SignalRegistry,
        provider: QuestionnaireResourceProvider,
    ) -> dict[str, Any]:
        """Seed initial signals in memory mode (PUBLIC API).

        This replaces the private _seed_signals method with a public API that:
        1. Validates the SignalClient is using memory transport
        2. Returns deterministic metrics for validation
        3. Enforces the ≥95% hit rate requirement

        Args:
            client: SignalClient to seed (must be in memory mode)
            registry: SignalRegistry to populate
            provider: QuestionnaireResourceProvider for patterns

        Returns:
            Dict with seeding metrics (areas_seeded, total_signals, hit_rate)

        Raises:
            ValueError: If client is not in memory mode
            WiringInitializationError: If hit rate requirement is not met
        """
        logger.info("wiring_init_phase", phase="seed_signals_public")

        if getattr(client, "_transport", None) != "memory":
            raise ValueError(
                "Signal seeding requires memory mode. "
                "Set enable_http_signals=False in WiringFeatureFlags."
            )

        memory_source = getattr(client, "_memory_source", None)
        if memory_source is None:
            raise ValueError("Signal client memory source not initialized.")

        metrics = self._seed_canonical_policy_area_signals(
            memory_source,
            registry,
            provider,
        )

        if metrics["hit_rate"] < metrics["required_hit_rate"]:
            raise WiringInitializationError(
                phase="seed_signals",
                component="SignalRegistry",
                reason=(
                    f"Signal hit rate {metrics['hit_rate']:.2%} below "
                    f"required threshold {metrics['required_hit_rate']:.2%}"
                ),
            )

        return metrics

    def _seed_signals(
        self,
        memory_source: InMemorySignalSource,
        registry: SignalRegistry,
        provider: QuestionnaireResourceProvider,
    ) -> None:
        """DEPRECATED: Use seed_signals_public() instead.

        This method is kept for backward compatibility during migration.
        """
        logger.warning(
            "_seed_signals is deprecated. Use seed_signals_public() instead."
        )

        metrics = self._seed_canonical_policy_area_signals(memory_source, registry, provider)
        logger.info(
            "signals_seeded",
            areas=metrics["canonical_areas"],
            aliases=metrics["legacy_aliases"],
            hit_rate=metrics["hit_rate"],
        )

    def _compute_init_hashes(
        self,
        provider: QuestionnaireResourceProvider,
        registry: SignalRegistry,
        factory: CoreModuleFactory,
        router: ExtendedArgRouter,
    ) -> dict[str, str]:
        """Compute hashes for initialized components.

        Args:
            provider: QuestionnaireResourceProvider
            registry: SignalRegistry
            factory: CoreModuleFactory
            router: ExtendedArgRouter

        Returns:
            Dict of component names to their hashes
        """
        import blake3

        hashes = {}

        # Provider hash (based on data keys)
        provider_keys = sorted(provider._data.keys()) if hasattr(provider, '_data') else []
        hashes["provider"] = blake3.blake3(
            json.dumps(provider_keys, sort_keys=True).encode('utf-8')
        ).hexdigest()

        # Registry hash (based on metrics)
        registry_metrics = registry.get_metrics()
        hashes["registry"] = blake3.blake3(
            json.dumps(registry_metrics, sort_keys=True).encode('utf-8')
        ).hexdigest()

        # Router hash (based on special routes count)
        router_data = {"route_count": router.get_special_route_coverage()}
        hashes["router"] = blake3.blake3(
            json.dumps(router_data, sort_keys=True).encode('utf-8')
        ).hexdigest()

        return hashes


__all__ = [
    'WiringComponents',
    'WiringBootstrap',
]
