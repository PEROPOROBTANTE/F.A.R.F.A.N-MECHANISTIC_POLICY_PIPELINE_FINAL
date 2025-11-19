"""
Layer requirements resolver.

This module determines which calibration layers (@b, @u, @q, @d, @p, @C, @chain, @m)
should be evaluated for a given method based on its role/layer designation.

Design:
- Maps method roles (analyzer, processor, etc.) to required calibration layers
- Always includes @b (base layer) for every method
- Uses conservative defaults (all layers) for unknown roles
- Integrates with IntrinsicScoreLoader to read role from calibration JSON
- SPECIAL CASE: Executors (D1Q1-D6Q5) ALWAYS use all 8 layers regardless of role
"""
import logging
import re
from typing import Set

from .data_structures import LayerID
from .intrinsic_loader import IntrinsicScoreLoader

logger = logging.getLogger(__name__)


class LayerRequirementsResolver:
    """
    Resolves which calibration layers are required for a method based on its role.

    The resolver maps logical roles (from the 'layer' field in intrinsic calibration)
    to the set of calibration layers that must be evaluated.

    Theoretical Model:
        - Analyzer methods: All 8 layers (most rigorous)
        - Processor/Ingest/Structure/Extract: Core + Unit + Meta
        - Aggregate: Core + Contextual + Congruence + Meta
        - Report: Core + Congruence + Meta
        - Utility/Transform/Orchestrator/Meta: Core + Chain + Meta (minimal)
        - Unknown: All 8 layers (conservative fallback)

    Where "Core" = @b (base) + @chain (always required for integrity).

    Usage:
        resolver = LayerRequirementsResolver(intrinsic_loader)

        # Get required layers for a method
        layers = resolver.get_required_layers("my_module.MyClass.analyze")
        # Returns: {"b", "u", "q", "d", "p", "C", "chain", "m"}

        # Check if a specific layer should be skipped
        if resolver.should_skip_layer("my_module.Util.format", "q"):
            print("Question layer not needed for utility methods")
    """

    # Role-to-layers mapping based on theoretical requirements
    ROLE_LAYER_MAP: dict[str, set[LayerID]] = {
        # Analytical methods: Full rigor (all 8 layers)
        "analyzer": {
            LayerID.BASE,
            LayerID.UNIT,
            LayerID.QUESTION,
            LayerID.DIMENSION,
            LayerID.POLICY,
            LayerID.CONGRUENCE,
            LayerID.CHAIN,
            LayerID.META
        },

        # Processing/ingestion: Core + Unit + Meta
        "processor": {
            LayerID.BASE,
            LayerID.UNIT,
            LayerID.CHAIN,
            LayerID.META
        },
        "ingest": {
            LayerID.BASE,
            LayerID.UNIT,
            LayerID.CHAIN,
            LayerID.META
        },
        "ingestion": {  # ADDED: Found in JSON as "ingestion" (29 methods)
            LayerID.BASE,
            LayerID.UNIT,
            LayerID.CHAIN,
            LayerID.META
        },
        "structure": {
            LayerID.BASE,
            LayerID.UNIT,
            LayerID.CHAIN,
            LayerID.META
        },
        "extract": {
            LayerID.BASE,
            LayerID.UNIT,
            LayerID.CHAIN,
            LayerID.META
        },

        # Aggregation: Core + Contextual + Congruence + Meta
        "aggregate": {
            LayerID.BASE,
            LayerID.CHAIN,
            LayerID.DIMENSION,
            LayerID.POLICY,
            LayerID.CONGRUENCE,
            LayerID.META
        },

        # Reporting: Core + Congruence + Meta
        "report": {
            LayerID.BASE,
            LayerID.CHAIN,
            LayerID.CONGRUENCE,
            LayerID.META
        },

        # Infrastructure: Minimal (Core + Meta only)
        "meta": {
            LayerID.BASE,
            LayerID.CHAIN,
            LayerID.META
        },
        "transform": {
            LayerID.BASE,
            LayerID.CHAIN,
            LayerID.META
        },
        "utility": {
            LayerID.BASE,
            LayerID.CHAIN,
            LayerID.META
        },
        "orchestrator": {
            LayerID.BASE,
            LayerID.CHAIN,
            LayerID.META
        },

        # ADDED: Executor type (2 methods in JSON - script executors, not D1Q1-D6Q5)
        "executor": {
            LayerID.BASE,
            LayerID.CHAIN,
            LayerID.META
        },

        # ADDED: Unknown type (227 methods) - Use conservative approach
        "unknown": {
            LayerID.BASE,
            LayerID.UNIT,
            LayerID.QUESTION,
            LayerID.DIMENSION,
            LayerID.POLICY,
            LayerID.CONGRUENCE,
            LayerID.CHAIN,
            LayerID.META
        },
    }

    # Conservative fallback: All layers
    DEFAULT_LAYERS: set[LayerID] = {
        LayerID.BASE,
        LayerID.UNIT,
        LayerID.QUESTION,
        LayerID.DIMENSION,
        LayerID.POLICY,
        LayerID.CONGRUENCE,
        LayerID.CHAIN,
        LayerID.META
    }

    # Executor detection pattern: D[1-6]Q[1-5]_Executor
    EXECUTOR_PATTERN: re.Pattern[str] = re.compile(r'D[1-6]Q[1-5]_Executor')

    def __init__(self, intrinsic_loader: IntrinsicScoreLoader) -> None:
        """
        Initialize the resolver.

        Args:
            intrinsic_loader: Loader for intrinsic calibration data
        """
        self.intrinsic_loader = intrinsic_loader

        logger.debug("layer_requirements_resolver_initialized")

        # Validate that all mappings include BASE
        for role, layers in self.ROLE_LAYER_MAP.items():
            if LayerID.BASE not in layers:
                raise ValueError(
                    f"Role '{role}' mapping must include LayerID.BASE (@b) - "
                    f"base layer is required for all methods"
                )

    @classmethod
    def is_executor(cls, method_id: str) -> bool:
        """
        Determine if a method belongs to one of the 30 executors (D1Q1-D6Q5).

        Args:
            method_id: Full method identifier

        Returns:
            True if method belongs to an executor class

        Examples:
            >>> LayerRequirementsResolver.is_executor(
            ...     "src.saaaaaa.core.orchestrator.executors.D1Q1_Executor.execute"
            ... )
            True
            >>> LayerRequirementsResolver.is_executor(
            ...     "src.saaaaaa.processing.SomeClass.method"
            ... )
            False
        """
        return bool(cls.EXECUTOR_PATTERN.search(method_id))

    def get_required_layers(self, method_id: str) -> set[LayerID]:
        """
        Get the set of calibration layers required for a method.

        CRITICAL: If method belongs to one of the 30 executors (D1Q1-D6Q5),
        ALL 8 LAYERS are ALWAYS required, regardless of role designation.

        Args:
            method_id: Full method identifier (e.g., "module.Class.method")

        Returns:
            Set of LayerID enums representing required layers.
            Always includes LayerID.BASE at minimum.

        Examples:
            >>> resolver.get_required_layers(
            ...     "src.saaaaaa.core.orchestrator.executors.D1Q1_Executor.execute"
            ... )
            {LayerID.BASE, LayerID.UNIT, ..., LayerID.META}  # ALL 8 layers (executor)

            >>> resolver.get_required_layers("analyzer.PatternExtractor.analyze")
            {LayerID.BASE, LayerID.UNIT, ..., LayerID.META}  # All 8 layers (analyzer)

            >>> resolver.get_required_layers("utils.format_string")
            {LayerID.BASE, LayerID.CHAIN, LayerID.META}  # Minimal layers (utility)
        """
        # SPECIAL CASE: Executors ALWAYS require all 8 layers
        if self.is_executor(method_id):
            logger.info(
                "executor_detected_forcing_all_8_layers",
                extra={
                    "method_id": method_id,
                    "reason": "executors_require_maximum_rigor"
                }
            )
            return self.DEFAULT_LAYERS.copy()

        # Get role from intrinsic loader
        role = self.intrinsic_loader.get_layer(method_id)

        if role is None:
            logger.info(
                "method_role_unknown_using_conservative",
                extra={
                    "method_id": method_id,
                    "fallback": "all_layers"
                }
            )
            return self.DEFAULT_LAYERS.copy()

        # Look up role in mapping
        required_layers = self.ROLE_LAYER_MAP.get(role.lower())

        if required_layers is None:
            logger.warning(
                "unrecognized_role_using_conservative",
                extra={
                    "method_id": method_id,
                    "role": role,
                    "fallback": "all_layers"
                }
            )
            return self.DEFAULT_LAYERS.copy()

        logger.debug(
            "layer_requirements_resolved",
            extra={
                "method_id": method_id,
                "role": role,
                "required_layers": [layer.value for layer in required_layers],
                "layer_count": len(required_layers)
            }
        )

        return required_layers.copy()

    def should_skip_layer(self, method_id: str, layer: LayerID | str) -> bool:
        """
        Determine if a specific layer should be skipped for a method.

        Args:
            method_id: Full method identifier
            layer: Layer to check (LayerID enum or string like "q", "d", etc.)

        Returns:
            True if the layer should be skipped (not required),
            False if the layer should be evaluated

        Examples:
            >>> resolver.should_skip_layer("utils.format", LayerID.QUESTION)
            True  # Utility methods don't need question compatibility

            >>> resolver.should_skip_layer("utils.format", LayerID.BASE)
            False  # Base layer always required

            >>> resolver.should_skip_layer("analyzer.extract", "q")
            False  # Analyzers need all layers
        """
        # Convert string to LayerID if needed
        if isinstance(layer, str):
            try:
                layer = LayerID(layer)
            except ValueError:
                logger.warning(
                    "invalid_layer_id",
                    extra={"layer": layer, "method_id": method_id}
                )
                return False  # Don't skip if we can't parse the layer

        required_layers = self.get_required_layers(method_id)
        should_skip = layer not in required_layers

        if should_skip:
            logger.debug(
                "layer_skipped",
                extra={
                    "method_id": method_id,
                    "layer": layer.value,
                    "reason": "not_required_for_role"
                }
            )

        return should_skip

    def get_layer_summary(self, method_id: str) -> str:
        """
        Get a human-readable summary of required layers for a method.

        Args:
            method_id: Full method identifier

        Returns:
            Readable string describing the layer configuration

        Example:
            >>> resolver.get_layer_summary("analyzer.MyClass.analyze")
            "analyzer role → 8 layers: @b, @u, @q, @d, @p, @C, @chain, @m"
        """
        role = self.intrinsic_loader.get_layer(method_id)
        required_layers = self.get_required_layers(method_id)

        layer_order: dict[str, int] = {
            "b": 0,
            "u": 1,
            "q": 2,
            "d": 3,
            "p": 4,
            "C": 5,
            "chain": 6,
            "m": 7
        }
        layer_names = ", ".join(
            f"@{layer.value}" for layer in sorted(
                required_layers,
                key=lambda x: layer_order.get(x.value, 999)
            )
        )

        if role:
            return f"{role} role → {len(required_layers)} layers: {layer_names}"
        else:
            return f"unknown role → {len(required_layers)} layers (conservative): {layer_names}"

    def get_skipped_layers(self, method_id: str) -> set[LayerID]:
        """
        Get the set of layers that will be skipped for a method.

        Args:
            method_id: Full method identifier

        Returns:
            Set of LayerID enums that will NOT be evaluated

        Example:
            >>> resolver.get_skipped_layers("utils.format")
            {LayerID.QUESTION, LayerID.DIMENSION, LayerID.POLICY, ...}
        """
        required = self.get_required_layers(method_id)
        all_layers: set[LayerID] = {
            LayerID.BASE,
            LayerID.UNIT,
            LayerID.QUESTION,
            LayerID.DIMENSION,
            LayerID.POLICY,
            LayerID.CONGRUENCE,
            LayerID.CHAIN,
            LayerID.META
        }
        return all_layers - required