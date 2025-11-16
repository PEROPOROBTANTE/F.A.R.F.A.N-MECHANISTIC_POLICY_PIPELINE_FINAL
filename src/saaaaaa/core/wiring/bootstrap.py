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
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import structlog

from saaaaaa.core.orchestrator.arg_router import ExtendedArgRouter
from saaaaaa.core.orchestrator.class_registry import build_class_registry
from saaaaaa.core.orchestrator.bayesian_module_factory import BayesianModuleFactory
from saaaaaa.core.orchestrator.executor_config import ExecutorConfig
from saaaaaa.core.orchestrator.questionnaire_resource_provider import (
    QuestionnaireResourceProvider,
)
from saaaaaa.core.orchestrator.signals import (
    InMemorySignalSource,
    SignalClient,
    SignalPack,
    SignalRegistry,
)

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
    flags: WiringFeatureFlags
    init_hashes: dict[str, str] = field(default_factory=dict)


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
    ):
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
            
            # Phase 8: Seed signals (if memory mode)
            if signal_client._transport == "memory":
                self._seed_signals(signal_client._memory_source, signal_registry, provider)
            
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
    
    def _seed_signals(
        self,
        memory_source: InMemorySignalSource,
        registry: SignalRegistry,
        provider: QuestionnaireResourceProvider,
    ) -> None:
        """Seed initial signals in memory mode.
        
        Args:
            memory_source: InMemorySignalSource to seed
            registry: SignalRegistry to populate
            provider: QuestionnaireResourceProvider for patterns
        """
        logger.info("wiring_init_phase", phase="seed_signals")
        
        # Create default signal packs for common policy areas
        policy_areas = ["fiscal", "salud", "ambiente", "energía", "transporte"]
        
        for area in policy_areas:
            # Extract patterns from provider for this area
            patterns = provider.get_patterns_for_area(area) if hasattr(provider, 'get_patterns_for_area') else []
            
            pack = SignalPack(
                version="1.0.0",
                policy_area=area,  # type: ignore[arg-type]
                patterns=patterns[:10] if patterns else [],  # Limit to 10 patterns
                indicators=[],
                regex=[],
                verbs=[],
                entities=[],
                thresholds={},
                ttl_s=3600,
            )
            
            # Register in memory source
            memory_source.register(area, pack)
            
            # Also put in registry for immediate availability
            registry.put(area, pack)
            
            logger.debug("signal_seeded", policy_area=area, patterns=len(pack.patterns))
        
        logger.info("signals_seeded", areas=len(policy_areas))
    
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
