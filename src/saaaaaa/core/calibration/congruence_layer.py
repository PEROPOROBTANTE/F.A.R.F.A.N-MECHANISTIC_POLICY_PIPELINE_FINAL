"""
Congruence Layer (@C) - Full Implementation.

Evaluates method ensemble congruence using three components:
- c_scale: Range compatibility
- c_sem: Semantic overlap (Jaccard index)
- c_fusion: Fusion rule validity

Formula: C_play(G|ctx) = c_scale · c_sem · c_fusion
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


class CongruenceLayerEvaluator:
    """
    Evaluates congruence of method ensembles.

    Attributes:
        registry: Dictionary mapping method IDs to their metadata
    """

    def __init__(self, method_registry: dict[str, Any]) -> None:
        """
        Initialize evaluator with method registry.

        Args:
            method_registry: Dict with method metadata (output_range, semantic_tags, etc.)
        """
        self.registry = method_registry
        logger.info("congruence_evaluator_initialized", extra={"num_methods": len(method_registry)})

    def evaluate(
        self,
        method_ids: list[str],
        subgraph_id: str,
        fusion_rule: str = "weighted_average",
        provided_inputs: list[str] = None
    ) -> float:
        """
        Evaluate congruence of method ensemble.

        Formula: C_play(G|ctx) = c_scale · c_sem · c_fusion

        Args:
            method_ids: List of methods in the subgraph
            subgraph_id: Identifier for this subgraph
            fusion_rule: How outputs are combined (weighted_average, max, min, product)
            provided_inputs: List of actual inputs provided

        Returns:
            C_play ∈ [0.0, 1.0]
        """
        # Edge case: Single method = perfect congruence, but only if method exists
        if len(method_ids) < 2:
            method_id = method_ids[0] if method_ids else None
            if method_id is not None and method_id in self.registry:
                logger.debug("congruence_single_method", extra={"score": 1.0, "method_id": method_id})
                return 1.0
            else:
                logger.warning("congruence_single_method_missing", extra={"score": 0.0, "method_id": method_id})
                return 0.0

        logger.info(
            "congruence_evaluation_start",
            extra={
                "methods": method_ids,
                "subgraph": subgraph_id,
                "fusion": fusion_rule
            }
        )

        # Component 1: Scale congruence (c_scale)
        c_scale = self._compute_scale_congruence(method_ids)
        logger.debug("c_scale_computed", extra={"score": c_scale})

        # Component 2: Semantic congruence (c_sem)
        c_sem = self._compute_semantic_congruence(method_ids)
        logger.debug("c_sem_computed", extra={"score": c_sem})

        # Component 3: Fusion validity (c_fusion)
        c_fusion = self._compute_fusion_validity(
            method_ids, fusion_rule, provided_inputs or []
        )
        logger.debug("c_fusion_computed", extra={"score": c_fusion})

        # Final score: Product of three components
        C_play = c_scale * c_sem * c_fusion

        logger.info(
            "congruence_computed",
            extra={
                "C_play": C_play,
                "c_scale": c_scale,
                "c_sem": c_sem,
                "c_fusion": c_fusion,
                "subgraph": subgraph_id
            }
        )

        return C_play

    def _compute_scale_congruence(self, method_ids: list[str]) -> float:
        """
        Compute c_scale: Range compatibility.

        Scoring:
            1.0: All ranges identical
            0.8: All ranges convertible (within [0,1])
            0.0: Incompatible ranges

        Returns:
            c_scale ∈ {0.0, 0.8, 1.0}
        """
        ranges = []
        for method_id in method_ids:
            if method_id not in self.registry:
                logger.warning("method_not_registered", extra={"method": method_id})
                return 0.0

            method_data = self.registry[method_id]
            output_range = method_data.get("output_range")

            if output_range is None:
                logger.warning("no_output_range", extra={"method": method_id})
                return 0.0

            ranges.append(tuple(output_range))

        # Check if all ranges are identical
        first_range = ranges[0]
        if all(r == first_range for r in ranges):
            logger.debug("ranges_identical", extra={"range": first_range})
            return 1.0

        # Check if all ranges are in [0,1] (convertible)
        all_in_unit = all(r == (0.0, 1.0) for r in ranges)
        if all_in_unit:
            logger.debug("ranges_convertible", extra={"note": "all in [0,1]"})
            return 0.8

        # Incompatible ranges
        logger.warning("ranges_incompatible", extra={"ranges": ranges})
        return 0.0

    def _compute_semantic_congruence(self, method_ids: list[str]) -> float:
        """
        Compute c_sem: Semantic overlap (Jaccard index).

        Formula: |intersection| / |union| of semantic tags

        Returns:
            c_sem ∈ [0.0, 1.0]
        """
        tag_sets = []

        for method_id in method_ids:
            if method_id not in self.registry:
                logger.warning("method_not_registered", extra={"method": method_id})
                return 0.0

            tags = self.registry[method_id].get("semantic_tags", [])
            if not isinstance(tags, (list, set)):
                tags = []
            tag_sets.append(set(tags))

        if not tag_sets:
            return 0.0

        # Compute intersection and union
        intersection = tag_sets[0]
        union = tag_sets[0]

        for tags in tag_sets[1:]:
            intersection = intersection.intersection(tags)
            union = union.union(tags)

        # Jaccard index
        if len(union) == 0:
            logger.warning("no_semantic_tags", extra={"methods": method_ids})
            return 0.0

        jaccard = len(intersection) / len(union)

        logger.debug(
            "semantic_congruence",
            extra={
                "intersection": list(intersection),
                "union_size": len(union),
                "jaccard": jaccard
            }
        )

        return jaccard

    def _compute_fusion_validity(
        self,
        method_ids: list[str],
        fusion_rule: str,
        provided_inputs: list[str]
    ) -> float:
        """
        Compute c_fusion: Fusion rule validity.

        Scoring:
            1.0: Rule valid AND all inputs present
            0.5: Rule valid BUT some inputs missing
            0.0: Rule invalid

        Returns:
            c_fusion ∈ {0.0, 0.5, 1.0}
        """
        # Check if fusion rule is valid
        valid_rules = ["weighted_average", "max", "min", "product", "custom"]
        if fusion_rule not in valid_rules:
            logger.warning(
                "invalid_fusion_rule",
                extra={"rule": fusion_rule, "valid": valid_rules}
            )
            return 0.0

        # Collect all fusion requirements
        all_requirements = set()
        for method_id in method_ids:
            if method_id not in self.registry:
                return 0.0

            requirements = self.registry[method_id].get("fusion_requirements", [])
            all_requirements.update(requirements)

        # Check if provided inputs cover all requirements
        provided = set(provided_inputs)
        missing = all_requirements - provided

        if not missing:
            # All inputs provided
            logger.debug(
                "fusion_valid",
                extra={"rule": fusion_rule, "all_inputs_present": True}
            )
            return 1.0
        else:
            # Some inputs missing
            logger.warning(
                "fusion_partial",
                extra={
                    "rule": fusion_rule,
                    "missing": list(missing),
                    "provided": list(provided)
                }
            )
            return 0.5
