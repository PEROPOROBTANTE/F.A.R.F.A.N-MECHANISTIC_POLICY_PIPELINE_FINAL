"""Bayesian Module Factory - Dependency Injection for 19 Bayesian Module Classes.

This factory creates Bayesian module instances with injected resources from the questionnaire.
It eliminates pattern duplication by providing a single source of truth via
QuestionnaireResourceProvider.

Design Principles:
- Constructor injection of questionnaire resources
- Single factory instance per questionnaire
- Lazy instantiation of modules
- Full traceability of resource injection
- Type-safe module creation

NOTE: This factory is distinct from factory.py (CoreModuleFactory).
      - factory.py: General-purpose factory for contracts, loaders, processors
      - bayesian_module_factory.py: Specialized factory for Bayesian analysis modules
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from .questionnaire_resource_provider import (
    Pattern,
    QuestionnaireResourceProvider,
    ValidationSpec,
)
from .signal_loader import build_all_signal_packs
from .signals import (
    InMemorySignalSource,
    SignalClient,
    SignalRegistry,
)

if TYPE_CHECKING:
    from pathlib import Path

logger = structlog.get_logger(__name__)


class BayesianModuleFactory:
    """
    Factory for creating module instances with injected questionnaire resources.

    This factory creates instances of the 19 core module classes, injecting
    patterns, validations, and other resources extracted from the questionnaire.

    Module Classes (19):
    1. BayesianNumericalAnalyzer
    2. BayesianEvidenceScorer
    3. BayesianMechanismInference
    4. BayesianTemporalCoherence
    5. BayesianSourceReliability
    6. BayesianCoherenceValidator
    7. BayesianIndicatorExtractor
    8. BayesianCausalChainBuilder
    9. BayesianPolicyAreaClassifier
    10. BayesianRiskAssessment
    11. BayesianStakeholderMapper
    12. BayesianConstraintAnalyzer
    13. BayesianBudgetValidator
    14. BayesianGovernanceEvaluator
    15. BayesianImplementationPlanner
    16. BayesianMonitoringFramework
    17. BayesianImpactPredictor
    18. BayesianAlignmentChecker
    19. BayesianQualityController

    Usage:
        factory = BayesianModuleFactory(questionnaire_data)
        analyzer = factory.create_bayesian_numerical_analyzer()
        scorer = factory.create_bayesian_evidence_scorer()
    """

    def __init__(
        self,
        questionnaire_data: dict[str, Any],
        signal_registry=None,
        signal_client=None,
        enable_signals: bool = True,
    ) -> None:
        """
        Initialize factory with questionnaire data and optional signal infrastructure.

        Args:
            questionnaire_data: Parsed questionnaire monolith JSON
            signal_registry: Optional SignalRegistry for cross-cut signal propagation
            signal_client: Optional SignalClient for fetching signals
            enable_signals: Enable automatic signal infrastructure (default: True)
        """
        self._provider = QuestionnaireResourceProvider(questionnaire_data)
        self._questionnaire_data = questionnaire_data
        self._instances: dict[str, Any] = {}

        # Extract resources upfront
        self._all_patterns = self._provider.extract_all_patterns()
        self._temporal_patterns = self._provider.get_temporal_patterns()
        self._indicator_patterns = self._provider.get_indicator_patterns()
        self._source_patterns = self._provider.get_source_patterns()
        self._territorial_patterns = self._provider.get_territorial_patterns()
        self._validations = self._provider.extract_all_validations()

        # Auto-create signal infrastructure if enabled
        if enable_signals:
            if signal_client is None:
                # Create in-memory signal source
                memory_source = InMemorySignalSource()

                # Load ALL 10 policy areas from monolith
                logger.info("loading_signal_packs_from_monolith")
                all_packs = build_all_signal_packs(questionnaire_data)

                for pa_code, signal_pack in all_packs.items():
                    memory_source.register(pa_code, signal_pack)
                    logger.debug(
                        "signal_pack_registered",
                        policy_area=pa_code,
                        patterns=len(signal_pack.patterns),
                    )

                self.signal_client = SignalClient(
                    base_url="memory://",
                    memory_source=memory_source,
                )
                logger.info(
                    "signal_client_created",
                    transport="memory",
                    policy_areas=len(all_packs),
                )
            else:
                self.signal_client = signal_client

            if signal_registry is None:
                # Create and pre-populate registry
                self._signal_registry = SignalRegistry(max_size=100, default_ttl_s=86400)

                # Pre-populate registry with all policy areas
                for pa_code in [f"PA{i:02d}" for i in range(1, 11)]:
                    pack = self.signal_client.fetch_signal_pack(pa_code)
                    if pack:
                        self._signal_registry.put(pa_code, pack)
                        logger.debug(
                            "signal_registry_preloaded",
                            policy_area=pa_code,
                        )

                logger.info(
                    "signal_registry_created",
                    size=len(self._signal_registry._cache),
                    max_size=100,
                )
            else:
                self._signal_registry = signal_registry
        else:
            self.signal_client = signal_client
            self._signal_registry = signal_registry

        logger.info(
            "core_module_factory_initialized",
            total_patterns=len(self._all_patterns),
            temporal=len(self._temporal_patterns),
            indicators=len(self._indicator_patterns),
            sources=len(self._source_patterns),
            validations=len(self._validations),
            has_signal_registry=self._signal_registry is not None,
            signals_enabled=enable_signals,
        )

    @classmethod
    def from_provider(cls, provider: QuestionnaireResourceProvider) -> BayesianModuleFactory:
        """
        Create factory from existing provider.

        Args:
            provider: QuestionnaireResourceProvider instance

        Returns:
            CoreModuleFactory instance
        """
        # Access internal data (requires provider to expose it)
        return cls(provider._data)

    def get_provider(self) -> QuestionnaireResourceProvider:
        """Get the underlying resource provider."""
        return self._provider

    def get_signal_registry(self):
        """Get the signal registry if available."""
        return self._signal_registry

    # ==========================
    # Module Creation Methods
    # ==========================

    def create_bayesian_numerical_analyzer(self) -> BayesianNumericalAnalyzer:
        """
        Create BayesianNumericalAnalyzer with indicator patterns.

        Returns:
            Configured BayesianNumericalAnalyzer instance
        """
        if "numerical_analyzer" not in self._instances:
            self._instances["numerical_analyzer"] = BayesianNumericalAnalyzer(
                indicator_patterns=self._indicator_patterns,
                temporal_patterns=self._temporal_patterns,
            )
            logger.debug("created_bayesian_numerical_analyzer")

        return self._instances["numerical_analyzer"]

    def create_bayesian_evidence_scorer(self) -> BayesianEvidenceScorer:
        """
        Create BayesianEvidenceScorer with source patterns.

        Returns:
            Configured BayesianEvidenceScorer instance
        """
        if "evidence_scorer" not in self._instances:
            self._instances["evidence_scorer"] = BayesianEvidenceScorer(
                source_patterns=self._source_patterns,
                validations=self._validations,
            )
            logger.debug("created_bayesian_evidence_scorer")

        return self._instances["evidence_scorer"]

    def create_bayesian_mechanism_inference(self) -> BayesianMechanismInference:
        """
        Create BayesianMechanismInference with causal patterns.

        Returns:
            Configured BayesianMechanismInference instance
        """
        if "mechanism_inference" not in self._instances:
            # Get coherence patterns (cross_reference, etc.)
            coherence_patterns = [
                p for p in self._all_patterns
                if p.category in ("coherence", "cross_reference")
            ]

            self._instances["mechanism_inference"] = BayesianMechanismInference(
                coherence_patterns=coherence_patterns,
            )
            logger.debug("created_bayesian_mechanism_inference")

        return self._instances["mechanism_inference"]

    def create_bayesian_temporal_coherence(self) -> BayesianTemporalCoherence:
        """
        Create BayesianTemporalCoherence with temporal patterns.

        Returns:
            Configured BayesianTemporalCoherence instance
        """
        if "temporal_coherence" not in self._instances:
            self._instances["temporal_coherence"] = BayesianTemporalCoherence(
                temporal_patterns=self._temporal_patterns,
            )
            logger.debug("created_bayesian_temporal_coherence")

        return self._instances["temporal_coherence"]

    def create_bayesian_source_reliability(self) -> BayesianSourceReliability:
        """
        Create BayesianSourceReliability with source patterns.

        Returns:
            Configured BayesianSourceReliability instance
        """
        if "source_reliability" not in self._instances:
            self._instances["source_reliability"] = BayesianSourceReliability(
                source_patterns=self._source_patterns,
            )
            logger.debug("created_bayesian_source_reliability")

        return self._instances["source_reliability"]

    def create_all_modules(self) -> dict[str, Any]:
        """
        Create all 19 module instances.

        Returns:
            Dict mapping module names to instances
        """
        modules = {
            "numerical_analyzer": self.create_bayesian_numerical_analyzer(),
            "evidence_scorer": self.create_bayesian_evidence_scorer(),
            "mechanism_inference": self.create_bayesian_mechanism_inference(),
            "temporal_coherence": self.create_bayesian_temporal_coherence(),
            "source_reliability": self.create_bayesian_source_reliability(),
        }

        # TODO: Create remaining 14 modules when class stubs are available
        logger.info(
            "all_modules_created",
            count=len(modules),
            modules=list(modules.keys()),
        )

        return modules

    def get_resource_statistics(self) -> dict[str, Any]:
        """
        Get statistics about injected resources.

        Returns:
            Dict with resource counts and metadata
        """
        return self._provider.get_pattern_statistics()

    def load_catalog(self, path: Path | None = None) -> dict[str, Any]:
        """
        Load method catalog JSON file.

        Args:
            path: Path to catalog file. Defaults to config/rules/METODOS/catalogo_completo_canonico.json

        Returns:
            Loaded catalog data
        """
        # Import here to avoid circular dependency
        from saaaaaa.core.orchestrator.factory import load_catalog as _load_catalog
        return _load_catalog(path)


# ==========================
# Module Class Stubs
# ==========================
# TODO: Replace with actual implementations from the codebase

class BayesianNumericalAnalyzer:
    """Stub for BayesianNumericalAnalyzer with injected patterns."""

    def __init__(
        self,
        indicator_patterns: list[Pattern],
        temporal_patterns: list[Pattern],
    ) -> None:
        self.indicator_patterns = indicator_patterns
        self.temporal_patterns = temporal_patterns
        logger.debug(
            "bayesian_numerical_analyzer_init",
            indicators=len(indicator_patterns),
            temporal=len(temporal_patterns),
        )


class BayesianEvidenceScorer:
    """Stub for BayesianEvidenceScorer with injected patterns."""

    def __init__(
        self,
        source_patterns: list[Pattern],
        validations: list[ValidationSpec],
    ) -> None:
        self.source_patterns = source_patterns
        self.validations = validations
        logger.debug(
            "bayesian_evidence_scorer_init",
            sources=len(source_patterns),
            validations=len(validations),
        )


class BayesianMechanismInference:
    """Stub for BayesianMechanismInference with injected patterns."""

    def __init__(self, coherence_patterns: list[Pattern]) -> None:
        self.coherence_patterns = coherence_patterns
        logger.debug(
            "bayesian_mechanism_inference_init",
            coherence=len(coherence_patterns),
        )


class BayesianTemporalCoherence:
    """Stub for BayesianTemporalCoherence with injected patterns."""

    def __init__(self, temporal_patterns: list[Pattern]) -> None:
        self.temporal_patterns = temporal_patterns
        logger.debug(
            "bayesian_temporal_coherence_init",
            temporal=len(temporal_patterns),
        )


class BayesianSourceReliability:
    """Stub for BayesianSourceReliability with injected patterns."""

    def __init__(self, source_patterns: list[Pattern]) -> None:
        self.source_patterns = source_patterns
        logger.debug(
            "bayesian_source_reliability_init",
            sources=len(source_patterns),
        )
