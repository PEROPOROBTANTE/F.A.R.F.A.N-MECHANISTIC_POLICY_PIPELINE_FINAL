"""
Aggregation Module - Hierarchical Score Aggregation System

This module implements the complete aggregation pipeline for the policy analysis system:
- FASE 4: Dimension aggregation (60 dimensions: 6 × 10 policy areas)
- FASE 5: Policy area aggregation (10 areas)
- FASE 6: Cluster aggregation (4 MESO questions)
- FASE 7: Macro evaluation (1 holistic question)

Requirements:
- Validation of weights, thresholds, and hermeticity
- Comprehensive logging and abortability at each level
- No strategic simplification
- Full alignment with monolith specifications
- Uses canonical notation for dimension and policy area validation

Architecture:
- DimensionAggregator: Aggregates 5 micro questions → 1 dimension score
- AreaPolicyAggregator: Aggregates 6 dimension scores → 1 area score
- ClusterAggregator: Aggregates multiple area scores → 1 cluster score
- MacroAggregator: Aggregates all cluster scores → 1 holistic evaluation
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

T = TypeVar('T')


@dataclass(frozen=True)
class AggregationSettings:
    """Resolved aggregation settings derived from the questionnaire monolith."""

    dimension_group_by_keys: list[str]
    area_group_by_keys: list[str]
    cluster_group_by_keys: list[str]
    dimension_question_weights: dict[str, dict[str, float]]
    policy_area_dimension_weights: dict[str, dict[str, float]]
    cluster_policy_area_weights: dict[str, dict[str, float]]
    macro_cluster_weights: dict[str, float]
    dimension_expected_counts: dict[tuple[str, str], int]
    area_expected_dimension_counts: dict[str, int]

    @classmethod
    def from_monolith(cls, monolith: dict[str, Any] | None) -> AggregationSettings:
        """Build aggregation settings from canonical questionnaire data."""
        if not monolith:
            return cls(
                dimension_group_by_keys=["policy_area", "dimension"],
                area_group_by_keys=["area_id"],
                cluster_group_by_keys=["cluster_id"],
                dimension_question_weights={},
                policy_area_dimension_weights={},
                cluster_policy_area_weights={},
                macro_cluster_weights={},
                dimension_expected_counts={},
                area_expected_dimension_counts={},
            )

        blocks = monolith.get("blocks", {})
        niveles = blocks.get("niveles_abstraccion", {})
        policy_areas = niveles.get("policy_areas", [])
        clusters = niveles.get("clusters", [])
        micro_questions = blocks.get("micro_questions", [])

        aggregation_block = (
            monolith.get("aggregation")
            or blocks.get("aggregation")
            or monolith.get("rubric", {}).get("aggregation")
            or {}
        )

        # Map question_id → base_slot for later normalization
        question_slot_lookup: dict[str, str] = {}
        dimension_slot_map: dict[str, set[str]] = defaultdict(set)
        dimension_expected_counts: dict[tuple[str, str], int] = defaultdict(int)

        for question in micro_questions:
            qid = question.get("question_id")
            dim_id = question.get("dimension_id") or question.get("dimension")
            area_id = question.get("policy_area_id") or question.get("policy_area")
            base_slot = question.get("base_slot")

            if dim_id and qid and not base_slot:
                base_slot = f"{dim_id}-{qid}"

            if qid and base_slot:
                question_slot_lookup[qid] = base_slot
                dimension_slot_map[dim_id].add(base_slot)

            if area_id and dim_id:
                dimension_expected_counts[(area_id, dim_id)] += 1

        area_expected_dimension_counts: dict[str, int] = {}
        for area in policy_areas:
            area_id = area.get("policy_area_id") or area.get("id")
            if not area_id:
                continue
            dims = area.get("dimension_ids") or []
            area_expected_dimension_counts[area_id] = len(dims)

        group_by_block = aggregation_block.get("group_by_keys") or {}
        dimension_group_by_keys = cls._coerce_str_list(
            group_by_block.get("dimension"),
            fallback=["policy_area", "dimension"],
        )
        area_group_by_keys = cls._coerce_str_list(
            group_by_block.get("area"),
            fallback=["area_id"],
        )
        cluster_group_by_keys = cls._coerce_str_list(
            group_by_block.get("cluster"),
            fallback=["cluster_id"],
        )

        dimension_question_weights = cls._build_dimension_weights(
            aggregation_block.get("dimension_question_weights") or {},
            question_slot_lookup,
            dimension_slot_map,
        )
        policy_area_dimension_weights = cls._build_area_dimension_weights(
            aggregation_block.get("policy_area_dimension_weights") or {},
            policy_areas,
        )
        cluster_policy_area_weights = cls._build_cluster_weights(
            aggregation_block.get("cluster_policy_area_weights") or {},
            clusters,
        )
        macro_cluster_weights = cls._build_macro_weights(
            aggregation_block.get("macro_cluster_weights") or {},
            clusters,
        )

        return cls(
            dimension_group_by_keys=dimension_group_by_keys,
            area_group_by_keys=area_group_by_keys,
            cluster_group_by_keys=cluster_group_by_keys,
            dimension_question_weights=dimension_question_weights,
            policy_area_dimension_weights=policy_area_dimension_weights,
            cluster_policy_area_weights=cluster_policy_area_weights,
            macro_cluster_weights=macro_cluster_weights,
            dimension_expected_counts=dict(dimension_expected_counts),
            area_expected_dimension_counts=area_expected_dimension_counts,
        )

    @staticmethod
    def _coerce_str_list(value: Any, *, fallback: list[str]) -> list[str]:
        if isinstance(value, list) and all(isinstance(item, str) for item in value):
            return value or fallback
        return fallback

    @staticmethod
    def _normalize_weights(weight_map: dict[str, float]) -> dict[str, float]:
        if not weight_map:
            return {}
        # Discard negative weights and normalize remaining ones
        positive_map = {k: float(v) for k, v in weight_map.items() if isinstance(v, (float, int)) and float(v) >= 0.0}
        if not positive_map:
            equal = 1.0 / len(weight_map)
            return {k: equal for k in weight_map}
        total = sum(positive_map.values())
        if total <= 0:
            equal = 1.0 / len(positive_map)
            return {k: equal for k in positive_map}
        return {k: value / total for k, value in positive_map.items()}

    @classmethod
    def _build_dimension_weights(
        cls,
        raw_weights: dict[str, dict[str, Any]],
        question_slot_lookup: dict[str, str],
        dimension_slot_map: dict[str, set[str]],
    ) -> dict[str, dict[str, float]]:
        dimension_weights: dict[str, dict[str, float]] = {}
        if raw_weights:
            for dim_id, weights in raw_weights.items():
                resolved: dict[str, float] = {}
                for qid, weight in weights.items():
                    slot = question_slot_lookup.get(qid, qid)
                    try:
                        resolved[slot] = float(weight)
                    except (TypeError, ValueError):
                        continue
                if resolved:
                    dimension_weights[dim_id] = cls._normalize_weights(resolved)

        if not dimension_weights:
            for dim_id, slots in dimension_slot_map.items():
                if not slots:
                    continue
                equal = 1.0 / len(slots)
                dimension_weights[dim_id] = {slot: equal for slot in slots}

        return dimension_weights

    @classmethod
    def _build_area_dimension_weights(
        cls,
        raw_weights: dict[str, dict[str, Any]],
        policy_areas: list[dict[str, Any]],
    ) -> dict[str, dict[str, float]]:
        area_weights: dict[str, dict[str, float]] = {}
        if raw_weights:
            for area_id, weights in raw_weights.items():
                resolved: dict[str, float] = {}
                for dim_id, value in weights.items():
                    try:
                        resolved[dim_id] = float(value)
                    except (TypeError, ValueError):
                        continue
                if resolved:
                    area_weights[area_id] = cls._normalize_weights(resolved)

        if not area_weights:
            for area in policy_areas:
                area_id = area.get("policy_area_id") or area.get("id")
                dims = area.get("dimension_ids") or []
                if not area_id or not dims:
                    continue
                equal = 1.0 / len(dims)
                area_weights[area_id] = {dim: equal for dim in dims}

        return area_weights

    @classmethod
    def _build_cluster_weights(
        cls,
        raw_weights: dict[str, dict[str, Any]],
        clusters: list[dict[str, Any]],
    ) -> dict[str, dict[str, float]]:
        cluster_weights: dict[str, dict[str, float]] = {}
        if raw_weights:
            for cluster_id, weights in raw_weights.items():
                resolved: dict[str, float] = {}
                for area_id, value in weights.items():
                    try:
                        resolved[area_id] = float(value)
                    except (TypeError, ValueError):
                        continue
                if resolved:
                    cluster_weights[cluster_id] = cls._normalize_weights(resolved)

        if not cluster_weights:
            for cluster in clusters:
                cluster_id = cluster.get("cluster_id")
                area_ids = cluster.get("policy_area_ids") or []
                if not cluster_id or not area_ids:
                    continue
                equal = 1.0 / len(area_ids)
                cluster_weights[cluster_id] = {area_id: equal for area_id in area_ids}

        return cluster_weights

    @classmethod
    def _build_macro_weights(
        cls,
        raw_weights: dict[str, Any],
        clusters: list[dict[str, Any]],
    ) -> dict[str, float]:
        if raw_weights:
            resolved = {}
            for cluster_id, weight in raw_weights.items():
                try:
                    resolved[cluster_id] = float(weight)
                except (TypeError, ValueError):
                    continue
            normalized = cls._normalize_weights(resolved)
            if normalized:
                return normalized

        cluster_ids = [cluster.get("cluster_id") for cluster in clusters if cluster.get("cluster_id")]
        if not cluster_ids:
            return {}
        equal = 1.0 / len(cluster_ids)
        return {cluster_id: equal for cluster_id in cluster_ids}

def group_by(items: Iterable[T], key_func: Callable[[T], tuple]) -> dict[tuple, list[T]]:
    """
    Groups a sequence of items into a dictionary based on a key function.

    This utility function iterates over a collection, applies a key function to each
    item, and collects items into lists, keyed by the result of the key function.

    The key function must return a tuple. This is because dictionary keys must be
    hashable, and tuples are hashable whereas lists are not. Using a tuple allows
    for grouping by multiple attributes.

    If the input iterable `items` is empty, this function will return an empty
    dictionary.

    Example:
        >>> from dataclasses import dataclass
        >>> @dataclass
        ... class Record:
        ...     category: str
        ...     value: int
        ...
        >>> data = [Record("A", 1), Record("B", 2), Record("A", 3)]
        >>> group_by(data, key_func=lambda r: (r.category,))
        {('A',): [Record(category='A', value=1), Record(category='A', value=3)],
         ('B',): [Record(category='B', value=2)]}

    Args:
        items: An iterable of items to be grouped.
        key_func: A callable that accepts an item and returns a tuple to be
                  used as the grouping key.

    Returns:
        A dictionary where keys are the result of the key function and values are
        lists of items belonging to that group.
    """
    grouped = defaultdict(list)
    for item in items:
        grouped[key_func(item)].append(item)
    return dict(grouped)

def validate_scored_results(results: list[dict[str, Any]]) -> list[ScoredResult]:
    """
    Validates a list of dictionaries and converts them to ScoredResult objects.

    Args:
        results: A list of dictionaries representing scored results.

    Returns:
        A list of ScoredResult objects.

    Raises:
        ValidationError: If any of the dictionaries are invalid.
    """
    validated_results = []
    required_keys = {
        "question_global": int, "base_slot": str, "policy_area": str, "dimension": str,
        "score": float, "quality_level": str, "evidence": dict, "raw_results": dict
    }
    for i, res_dict in enumerate(results):
        missing_keys = set(required_keys.keys()) - set(res_dict.keys())
        if missing_keys:
            raise ValidationError(
                f"Invalid ScoredResult at index {i}: missing keys {missing_keys}"
            )
        for key, expected_type in required_keys.items():
            if not isinstance(res_dict[key], expected_type):
                raise ValidationError(
                    f"Invalid type for key '{key}' at index {i}. "
                    f"Expected {expected_type}, got {type(res_dict[key])}."
                )
        try:
            validated_results.append(ScoredResult(**res_dict))
        except TypeError as e:
            raise ValidationError(f"Invalid ScoredResult at index {i}: {e}") from e
    return validated_results

# Import canonical notation for validation
try:
    from saaaaaa.core.canonical_notation import get_all_dimensions, get_all_policy_areas
    HAS_CANONICAL_NOTATION = True
except ImportError:
    HAS_CANONICAL_NOTATION = False

logger = logging.getLogger(__name__)

@dataclass
class ScoredResult:
    """Represents a single, scored micro-question, forming the input for aggregation."""
    question_global: int
    base_slot: str
    policy_area: str
    dimension: str
    score: float
    quality_level: str
    evidence: dict[str, Any]
    raw_results: dict[str, Any]

@dataclass
class DimensionScore:
    """Represents the aggregated score for a single dimension within a policy area."""
    dimension_id: str
    area_id: str
    score: float
    quality_level: str
    contributing_questions: list[int]
    validation_passed: bool = True
    validation_details: dict[str, Any] = field(default_factory=dict)

@dataclass
class AreaScore:
    """Represents the aggregated score for a policy area, based on its constituent dimensions."""
    area_id: str
    area_name: str
    score: float
    quality_level: str
    dimension_scores: list[DimensionScore]
    validation_passed: bool = True
    validation_details: dict[str, Any] = field(default_factory=dict)
    cluster_id: str | None = None  # Used for grouping into clusters

@dataclass
class ClusterScore:
    """Represents the aggregated score for a MESO cluster, based on its policy areas."""
    cluster_id: str
    cluster_name: str
    areas: list[str]
    score: float
    coherence: float  # Coherence metric for the scores within this cluster
    variance: float
    weakest_area: str | None
    area_scores: list[AreaScore]
    validation_passed: bool = True
    validation_details: dict[str, Any] = field(default_factory=dict)

@dataclass
class MacroScore:
    """Represents the final, holistic macro evaluation score for the entire system."""
    score: float
    quality_level: str
    cross_cutting_coherence: float  # Coherence across all clusters
    systemic_gaps: list[str]
    strategic_alignment: float
    cluster_scores: list[ClusterScore]
    validation_passed: bool = True
    validation_details: dict[str, Any] = field(default_factory=dict)

class AggregationError(Exception):
    """Base exception for aggregation errors."""
    pass

class ValidationError(AggregationError):
    """Raised when validation fails."""
    pass

class WeightValidationError(ValidationError):
    """Raised when weight validation fails."""
    pass

class ThresholdValidationError(ValidationError):
    """Raised when threshold validation fails."""
    pass

class HermeticityValidationError(ValidationError):
    """Raised when hermeticity validation fails."""
    pass

class CoverageError(AggregationError):
    """Raised when coverage requirements are not met."""
    pass

class DimensionAggregator:
    """
    Aggregates micro question scores into dimension scores.

    Responsibilities:
    - Aggregate 5 micro questions (Q1-Q5) per dimension
    - Validate weights sum to 1.0
    - Apply rubric thresholds
    - Ensure coverage (abort if insufficient)
    - Provide detailed logging
    """

    def __init__(
        self,
        monolith: dict[str, Any] | None = None,
        abort_on_insufficient: bool = True,
        aggregation_settings: AggregationSettings | None = None,
    ) -> None:
        """
        Initialize dimension aggregator.

        Args:
            monolith: Questionnaire monolith configuration (optional, required for run())
            abort_on_insufficient: Whether to abort on insufficient coverage

        Raises:
            ValueError: If monolith is None and required for operations
        """
        self.monolith = monolith
        self.abort_on_insufficient = abort_on_insufficient
        self.aggregation_settings = aggregation_settings or AggregationSettings.from_monolith(monolith)
        self.dimension_group_by_keys = (
            self.aggregation_settings.dimension_group_by_keys or ["policy_area", "dimension"]
        )

        # Extract configuration if monolith provided
        if monolith is not None:
            self.scoring_config = monolith["blocks"]["scoring"]
            self.niveles = monolith["blocks"]["niveles_abstraccion"]
        else:
            self.scoring_config = None
            self.niveles = None

        logger.info("DimensionAggregator initialized")

        # Validate canonical notation if available
        if HAS_CANONICAL_NOTATION:
            try:
                canonical_dims = get_all_dimensions()
                canonical_areas = get_all_policy_areas()
                logger.info(
                    f"Canonical notation loaded: {len(canonical_dims)} dimensions, "
                    f"{len(canonical_areas)} policy areas"
                )
            except Exception as e:
                logger.warning(f"Could not load canonical notation: {e}")

    def validate_dimension_id(self, dimension_id: str) -> bool:
        """
        Validate dimension ID against canonical notation.

        Args:
            dimension_id: Dimension ID to validate (e.g., "DIM01")

        Returns:
            True if dimension ID is valid

        Raises:
            ValidationError: If dimension ID is invalid and abort_on_insufficient is True
        """
        if not HAS_CANONICAL_NOTATION:
            logger.debug("Canonical notation not available, skipping validation")
            return True

        try:
            canonical_dims = get_all_dimensions()
            # Check if dimension_id is a valid code
            valid_codes = {info.code for info in canonical_dims.values()}
            if dimension_id in valid_codes:
                return True

            msg = f"Invalid dimension ID: {dimension_id}. Valid codes: {sorted(valid_codes)}"
            logger.error(msg)
            if self.abort_on_insufficient:
                raise ValidationError(msg)
            return False
        except Exception as e:
            logger.warning(f"Could not validate dimension ID: {e}")
            return True  # Don't fail if validation can't be performed

    def validate_policy_area_id(self, area_id: str) -> bool:
        """
        Validate policy area ID against canonical notation.

        Args:
            area_id: Policy area ID to validate (e.g., "PA01")

        Returns:
            True if policy area ID is valid

        Raises:
            ValidationError: If policy area ID is invalid and abort_on_insufficient is True
        """
        if not HAS_CANONICAL_NOTATION:
            logger.debug("Canonical notation not available, skipping validation")
            return True

        try:
            canonical_areas = get_all_policy_areas()
            if area_id in canonical_areas:
                return True

            msg = f"Invalid policy area ID: {area_id}. Valid codes: {sorted(canonical_areas.keys())}"
            logger.error(msg)
            if self.abort_on_insufficient:
                raise ValidationError(msg)
            return False
        except Exception as e:
            logger.warning(f"Could not validate policy area ID: {e}")
            return True  # Don't fail if validation can't be performed

    def validate_weights(self, weights: list[float]) -> tuple[bool, str]:
        """
        Ensures that a list of weights sums to 1.0 within a small tolerance.

        Args:
            weights: A list of floating-point weights.

        Returns:
            A tuple containing a boolean indicating validity and a descriptive message.

        Raises:
            WeightValidationError: If `abort_on_insufficient` is True and validation fails.
        """
        if not weights:
            msg = "No weights provided"
            logger.error(msg)
            if self.abort_on_insufficient:
                raise WeightValidationError(msg)
            return False, msg

        weight_sum = sum(weights)
        tolerance = 1e-6

        if abs(weight_sum - 1.0) > tolerance:
            msg = f"Weight sum validation failed: sum={weight_sum:.6f}, expected=1.0"
            logger.error(msg)
            if self.abort_on_insufficient:
                raise WeightValidationError(msg)
            return False, msg

        logger.debug(f"Weight validation passed: sum={weight_sum:.6f}")
        return True, "Weights valid"

    def validate_coverage(
        self,
        results: list[ScoredResult],
        expected_count: int = 5
    ) -> tuple[bool, str]:
        """
        Checks if the number of results meets a minimum expectation.

        Args:
            results: A list of ScoredResult objects.
            expected_count: The minimum number of results required.

        Returns:
            A tuple containing a boolean indicating validity and a descriptive message.

        Raises:
            CoverageError: If `abort_on_insufficient` is True and coverage is insufficient.
        """
        actual_count = len(results)

        if actual_count < expected_count:
            msg = (
                f"Coverage validation failed: "
                f"expected {expected_count} questions, got {actual_count}"
            )
            logger.error(msg)
            if self.abort_on_insufficient:
                raise CoverageError(msg)
            return False, msg

        logger.debug(f"Coverage validation passed: {actual_count}/{expected_count} questions")
        return True, "Coverage sufficient"

    def calculate_weighted_average(
        self,
        scores: list[float],
        weights: list[float] | None = None
    ) -> float:
        """
        Calculates a weighted average, defaulting to an equal weighting if none provided.

        Args:
            scores: A list of scores to be averaged.
            weights: An optional list of weights. If None, equal weights are assumed.

        Returns:
            The calculated weighted average.

        Raises:
            WeightValidationError: If the weights are invalid (e.g., mismatched length).
        """
        if not scores:
            return 0.0

        if weights is None:
            # Equal weights
            weights = [1.0 / len(scores)] * len(scores)

        # Validate weights length matches scores length
        if len(weights) != len(scores):
            msg = (
                f"Weight length mismatch: {len(weights)} weights for {len(scores)} scores"
            )
            logger.error(msg)
            raise WeightValidationError(msg)

        # Validate weights sum to 1.0
        valid, msg = self.validate_weights(weights)
        if not valid:
            # If validation failed and abort_on_insufficient is False,
            # validate_weights already logged the error and returned False
            # We should raise here to avoid silent failure
            raise WeightValidationError(msg)

        # Calculate weighted sum
        weighted_sum = sum(s * w for s, w in zip(scores, weights, strict=False))

        logger.debug(
            f"Weighted average calculated: "
            f"scores={scores}, weights={weights}, result={weighted_sum:.4f}"
        )

        return weighted_sum

    def apply_rubric_thresholds(
        self,
        score: float,
        thresholds: dict[str, float] | None = None
    ) -> str:
        """
        Apply rubric thresholds to determine quality level.

        Args:
            score: Aggregated score (0-3 range)
            thresholds: Optional threshold definitions (dict with keys: EXCELENTE, BUENO, ACEPTABLE)
                       Each value should be a normalized threshold (0-1 range)

        Returns:
            Quality level (EXCELENTE, BUENO, ACEPTABLE, INSUFICIENTE)
        """
        # Clamp score to valid range [0, 3]
        clamped_score = max(0.0, min(3.0, score))

        # Normalize to 0-1 range
        normalized_score = clamped_score / 3.0

        # Use provided thresholds or defaults
        if thresholds:
            excellent_threshold = thresholds.get('EXCELENTE', 0.85)
            good_threshold = thresholds.get('BUENO', 0.70)
            acceptable_threshold = thresholds.get('ACEPTABLE', 0.55)
        else:
            excellent_threshold = 0.85
            good_threshold = 0.70
            acceptable_threshold = 0.55

        # Apply thresholds
        if normalized_score >= excellent_threshold:
            quality = "EXCELENTE"
        elif normalized_score >= good_threshold:
            quality = "BUENO"
        elif normalized_score >= acceptable_threshold:
            quality = "ACEPTABLE"
        else:
            quality = "INSUFICIENTE"

        logger.debug(
            f"Rubric applied: score={score:.4f}, "
            f"normalized={normalized_score:.4f}, quality={quality}"
        )

        return quality

    def aggregate_dimension(
        self,
        scored_results: list[ScoredResult],
        group_by_values: dict[str, Any],
        weights: list[float] | None = None,
    ) -> DimensionScore:
        """
        Aggregate a single dimension from micro question results.

        Args:
            scored_results: List of scored results for this dimension/area.
            group_by_values: Dictionary of grouping keys and their values.
            weights: Optional weights for questions (defaults to equal weights).

        Returns:
            DimensionScore with aggregated score and quality level.

        Raises:
            ValidationError: If validation fails.
            CoverageError: If coverage is insufficient.
        """
        dimension_id = group_by_values.get("dimension", "UNKNOWN")
        area_id = group_by_values.get("policy_area", "UNKNOWN")
        logger.info(f"Aggregating dimension {dimension_id} for area {area_id}")

        validation_details = {}

        # In this context, scored_results are already grouped, so we can use them directly.
        dim_results = scored_results

        expected_count = self._expected_question_count(area_id, dimension_id)

        # Validate coverage
        try:
            coverage_valid, coverage_msg = self.validate_coverage(
                dim_results,
                expected_count=expected_count or 5,
            )
            validation_details["coverage"] = {
                "valid": coverage_valid,
                "message": coverage_msg,
                "count": len(dim_results)
            }
        except CoverageError as e:
            logger.error(f"Coverage validation failed for {dimension_id}/{area_id}: {e}")
            # Return minimal score if aborted
            return DimensionScore(
                dimension_id=dimension_id,
                area_id=area_id,
                score=0.0,
                quality_level="INSUFICIENTE",
                contributing_questions=[],
                validation_passed=False,
                validation_details={"error": str(e), "type": "coverage"}
            )

        if not dim_results:
            logger.warning(f"No results for dimension {dimension_id}/{area_id}")
            return DimensionScore(
                dimension_id=dimension_id,
                area_id=area_id,
                score=0.0,
                quality_level="INSUFICIENTE",
                contributing_questions=[],
                validation_passed=False,
                validation_details={"error": "No results", "type": "empty"}
            )

        # Extract scores
        scores = [r.score for r in dim_results]

        # Calculate weighted average
        resolved_weights = weights or self._resolve_dimension_weights(dimension_id, dim_results)
        try:
            avg_score = self.calculate_weighted_average(scores, resolved_weights)
            validation_details["weights"] = {
                "valid": True,
                "weights": resolved_weights if resolved_weights else "equal",
                "score": avg_score
            }
        except WeightValidationError as e:
            logger.error(f"Weight validation failed for {dimension_id}/{area_id}: {e}")
            return DimensionScore(
                dimension_id=dimension_id,
                area_id=area_id,
                score=0.0,
                quality_level="INSUFICIENTE",
                contributing_questions=[r.question_global for r in dim_results],
                validation_passed=False,
                validation_details={"error": str(e), "type": "weights"}
            )

        # Apply rubric thresholds
        quality_level = self.apply_rubric_thresholds(avg_score)
        validation_details["rubric"] = {
            "score": avg_score,
            "quality_level": quality_level
        }
        # Add score_max for downstream normalization
        validation_details["score_max"] = 3.0

        logger.info(
            f"✓ Dimension {dimension_id}/{area_id}: "
            f"score={avg_score:.4f}, quality={quality_level}"
        )

        return DimensionScore(
            dimension_id=dimension_id,
            area_id=area_id,
            score=avg_score,
            quality_level=quality_level,
            contributing_questions=[r.question_global for r in dim_results],
            validation_passed=True,
            validation_details=validation_details
        )

    def run(
        self,
        scored_results: list[ScoredResult],
        group_by_keys: list[str]
    ) -> list[DimensionScore]:
        """
        Run the dimension aggregation process.

        Args:
            scored_results: List of all scored results.
            group_by_keys: List of keys to group by.

        Returns:
            A list of DimensionScore objects.
        """
        def key_func(r):
            return tuple(getattr(r, key) for key in group_by_keys)
        grouped_results = group_by(scored_results, key_func)

        dimension_scores = []
        for group_key, results in grouped_results.items():
            group_by_values = dict(zip(group_by_keys, group_key, strict=False))
            score = self.aggregate_dimension(results, group_by_values)
            dimension_scores.append(score)

        return dimension_scores

    def _expected_question_count(self, area_id: str, dimension_id: str) -> int | None:
        if not self.aggregation_settings.dimension_expected_counts:
            return None
        return self.aggregation_settings.dimension_expected_counts.get((area_id, dimension_id))

    def _resolve_dimension_weights(
        self,
        dimension_id: str,
        dim_results: list[ScoredResult],
    ) -> list[float] | None:
        mapping = self.aggregation_settings.dimension_question_weights.get(dimension_id)
        if not mapping:
            return None

        weights: list[float] = []
        for result in dim_results:
            slot = result.base_slot
            weight = mapping.get(slot)
            if weight is None:
                logger.debug(
                    "Missing weight for slot %s in dimension %s – falling back to equal weights",
                    slot,
                    dimension_id,
                )
                return None
            weights.append(weight)

        total = sum(weights)
        if total <= 0:
            return None
        return [w / total for w in weights]

def run_aggregation_pipeline(
    scored_results: list[dict[str, Any]],
    monolith: dict[str, Any],
    abort_on_insufficient: bool = True
) -> list[ClusterScore]:
    """
    Orchestrates the end-to-end aggregation pipeline.

    This function provides a high-level entry point to the aggregation system,
    demonstrating the sequential wiring of the aggregator components. It ensures
    that data flows from raw scored results through dimension, area, and
    finally cluster aggregation in a controlled and validated manner.

    Note on Parallelization: This implementation is sequential. For very large
    datasets, the `group_by` operations in each aggregator's `run` method
    could be parallelized (e.g., using `concurrent.futures`) to process
    independent groups concurrently.

    Args:
        scored_results: A list of dictionaries, each representing a raw scored result.
        monolith: The central monolith configuration object.
        abort_on_insufficient: If True, the pipeline will stop on validation errors.

    Returns:
        A list of aggregated ClusterScore objects.
    """
    # 1. Input Validation (Pre-flight check)
    validated_scored_results = validate_scored_results(scored_results)

    aggregation_settings = AggregationSettings.from_monolith(monolith)

    # 2. FASE 4: Dimension Aggregation
    dim_aggregator = DimensionAggregator(
        monolith,
        abort_on_insufficient,
        aggregation_settings=aggregation_settings,
    )
    dimension_scores = dim_aggregator.run(
        validated_scored_results,
        group_by_keys=dim_aggregator.dimension_group_by_keys,
    )

    # 3. FASE 5: Area Policy Aggregation
    area_aggregator = AreaPolicyAggregator(
        monolith,
        abort_on_insufficient,
        aggregation_settings=aggregation_settings,
    )
    area_scores = area_aggregator.run(
        dimension_scores,
        group_by_keys=area_aggregator.area_group_by_keys,
    )

    # 4. FASE 6: Cluster Aggregation
    cluster_aggregator = ClusterAggregator(
        monolith,
        abort_on_insufficient,
        aggregation_settings=aggregation_settings,
    )
    cluster_definitions = monolith["blocks"]["niveles_abstraccion"]["clusters"]
    cluster_scores = cluster_aggregator.run(
        area_scores,
        cluster_definitions
    )

    return cluster_scores

    def run(
        self,
        scored_results: list[ScoredResult],
        group_by_keys: list[str]
    ) -> list[DimensionScore]:
        """
        Run the dimension aggregation process.

        Args:
            scored_results: List of all scored results.
            group_by_keys: List of keys to group by.

        Returns:
            A list of DimensionScore objects.
        """
        def key_func(r):
            return tuple(getattr(r, key) for key in group_by_keys)
        grouped_results = group_by(scored_results, key_func)

        dimension_scores = []
        for group_key, results in grouped_results.items():
            group_by_values = dict(zip(group_by_keys, group_key, strict=False))
            score = self.aggregate_dimension(results, group_by_values)
            dimension_scores.append(score)

        return dimension_scores

class AreaPolicyAggregator:
    """
    Aggregates dimension scores into policy area scores.

    Responsibilities:
    - Aggregate 6 dimension scores per policy area
    - Validate dimension completeness
    - Apply area-level rubric thresholds
    - Ensure hermeticity (no dimension overlap)
    """

    def __init__(
        self,
        monolith: dict[str, Any] | None = None,
        abort_on_insufficient: bool = True,
        aggregation_settings: AggregationSettings | None = None,
    ) -> None:
        """
        Initialize area aggregator.

        Args:
            monolith: Questionnaire monolith configuration (optional, required for run())
            abort_on_insufficient: Whether to abort on insufficient coverage

        Raises:
            ValueError: If monolith is None and required for operations
        """
        self.monolith = monolith
        self.abort_on_insufficient = abort_on_insufficient
        self.aggregation_settings = aggregation_settings or AggregationSettings.from_monolith(monolith)
        self.area_group_by_keys = self.aggregation_settings.area_group_by_keys or ["area_id"]

        # Extract configuration if monolith provided
        if monolith is not None:
            self.scoring_config = monolith["blocks"]["scoring"]
            self.niveles = monolith["blocks"]["niveles_abstraccion"]
            self.policy_areas = self.niveles["policy_areas"]
            self.dimensions = self.niveles["dimensions"]
        else:
            self.scoring_config = None
            self.niveles = None
            self.policy_areas = None
            self.dimensions = None

        logger.info("AreaPolicyAggregator initialized")

    def validate_hermeticity(
        self,
        dimension_scores: list[DimensionScore],
        area_id: str
    ) -> tuple[bool, str]:
        """
        Validate hermeticity (no dimension overlap/gaps).
        Uses scoped validation based on policy_area.dimension_ids from monolith.

        Args:
            dimension_scores: List of dimension scores for the area
            area_id: Policy area ID

        Returns:
            Tuple of (is_valid, message)

        Raises:
            HermeticityValidationError: If hermeticity is violated
        """
        # Get expected dimensions for this specific policy area
        area_def = next(
            (a for a in self.policy_areas if a["policy_area_id"] == area_id),
            None
        )

        if area_def and "dimension_ids" in area_def:
            expected_dimension_ids = set(area_def["dimension_ids"])
        else:
            # Fallback to all global dimensions if not specified
            expected_dimension_ids = {d["dimension_id"] for d in self.dimensions}

        actual_dimension_ids = {d.dimension_id for d in dimension_scores}
        len(expected_dimension_ids)
        len(dimension_scores)

        # Check for missing dimensions
        missing_dims = expected_dimension_ids - actual_dimension_ids
        if missing_dims:
            msg = (
                f"Hermeticity violation for area {area_id}: "
                f"missing dimensions {missing_dims}"
            )
            logger.error(msg)
            if self.abort_on_insufficient:
                raise HermeticityValidationError(msg)
            return False, msg

        # Check for unexpected dimensions
        extra_dims = actual_dimension_ids - expected_dimension_ids
        if extra_dims:
            msg = (
                f"Hermeticity violation for area {area_id}: "
                f"unexpected dimensions {extra_dims}"
            )
            logger.error(msg)
            if self.abort_on_insufficient:
                raise HermeticityValidationError(msg)
            return False, msg

        # Check for duplicate dimensions
        dimension_ids = [d.dimension_id for d in dimension_scores]
        if len(dimension_ids) != len(set(dimension_ids)):
            msg = f"Hermeticity violation for area {area_id}: duplicate dimensions found"
            logger.error(msg)
            if self.abort_on_insufficient:
                raise HermeticityValidationError(msg)
            return False, msg

        logger.debug(f"Hermeticity validation passed for area {area_id}")
        return True, "Hermeticity validated"

    def normalize_scores(self, dimension_scores: list[DimensionScore]) -> list[float]:
        """
        Normalize dimension scores to 0-1 range.

        Args:
            dimension_scores: List of dimension scores

        Returns:
            List of normalized scores
        """
        normalized = []
        for d in dimension_scores:
            # Extract max_expected from validation_details or default to 3.0
            max_expected = d.validation_details.get('score_max', 3.0) if d.validation_details else 3.0
            normalized.append(max(0.0, min(max_expected, d.score)) / max_expected)

        logger.debug(f"Scores normalized: {normalized}")
        return normalized

    def apply_rubric_thresholds(
        self,
        score: float,
        thresholds: dict[str, float] | None = None
    ) -> str:
        """
        Apply area-level rubric thresholds.

        Args:
            score: Aggregated score (0-3 range)
            thresholds: Optional threshold definitions (dict with keys: EXCELENTE, BUENO, ACEPTABLE)
                       Each value should be a normalized threshold (0-1 range)

        Returns:
            Quality level (EXCELENTE, BUENO, ACEPTABLE, INSUFICIENTE)
        """
        # Clamp score to valid range [0, 3]
        clamped_score = max(0.0, min(3.0, score))

        # Normalize to 0-1 range
        normalized_score = clamped_score / 3.0

        # Use provided thresholds or defaults
        if thresholds:
            excellent_threshold = thresholds.get('EXCELENTE', 0.85)
            good_threshold = thresholds.get('BUENO', 0.70)
            acceptable_threshold = thresholds.get('ACEPTABLE', 0.55)
        else:
            excellent_threshold = 0.85
            good_threshold = 0.70
            acceptable_threshold = 0.55

        # Apply thresholds
        if normalized_score >= excellent_threshold:
            quality = "EXCELENTE"
        elif normalized_score >= good_threshold:
            quality = "BUENO"
        elif normalized_score >= acceptable_threshold:
            quality = "ACEPTABLE"
        else:
            quality = "INSUFICIENTE"

        logger.debug(
            f"Area rubric applied: score={score:.4f}, "
            f"normalized={normalized_score:.4f}, quality={quality}"
        )

        return quality

    def aggregate_area(
        self,
        dimension_scores: list[DimensionScore],
        group_by_values: dict[str, Any],
        weights: list[float] | None = None,
    ) -> AreaScore:
        """
        Aggregate a single policy area from dimension scores.

        Args:
            dimension_scores: List of dimension scores for this area.
            group_by_values: Dictionary of grouping keys and their values.
            weights: Optional list of weights for dimension scores.

        Returns:
            AreaScore with aggregated score and quality level.

        Raises:
            ValidationError: If validation fails.
        """
        area_id = group_by_values.get("area_id", "UNKNOWN")
        logger.info(f"Aggregating policy area {area_id}")

        validation_details = {}

        # The dimension_scores are already grouped.
        area_dim_scores = dimension_scores

        # Validate hermeticity
        try:
            hermetic_valid, hermetic_msg = self.validate_hermeticity(area_dim_scores, area_id)
            validation_details["hermeticity"] = {
                "valid": hermetic_valid,
                "message": hermetic_msg,
                "dimension_count": len(area_dim_scores)
            }
        except HermeticityValidationError as e:
            logger.error(f"Hermeticity validation failed for area {area_id}: {e}")
            # Get area name
            area_name = next(
                (a["i18n"]["keys"]["label_es"] for a in self.policy_areas
                 if a["policy_area_id"] == area_id),
                area_id
            )
            return AreaScore(
                area_id=area_id,
                area_name=area_name,
                score=0.0,
                quality_level="INSUFICIENTE",
                dimension_scores=[],
                validation_passed=False,
                validation_details={"error": str(e), "type": "hermeticity"}
            )

        if not area_dim_scores:
            logger.warning(f"No dimension scores for area {area_id}")
            area_name = next(
                (a["i18n"]["keys"]["label_es"] for a in self.policy_areas
                 if a["policy_area_id"] == area_id),
                area_id
            )
            return AreaScore(
                area_id=area_id,
                area_name=area_name,
                score=0.0,
                quality_level="INSUFICIENTE",
                dimension_scores=[],
                validation_passed=False,
                validation_details={"error": "No dimensions", "type": "empty"}
            )

        # Normalize scores
        normalized = self.normalize_scores(area_dim_scores)
        validation_details["normalization"] = {
            "original": [d.score for d in area_dim_scores],
            "normalized": normalized
        }

        # Calculate weighted average score
        scores = [d.score for d in area_dim_scores]
        resolved_weights = weights or self._resolve_area_weights(area_id, area_dim_scores)
        avg_score = DimensionAggregator().calculate_weighted_average(scores, weights=resolved_weights)

        # Apply rubric thresholds
        quality_level = self.apply_rubric_thresholds(avg_score)
        validation_details["rubric"] = {
            "score": avg_score,
            "quality_level": quality_level
        }

        # Get area name
        area_name = next(
            (a["i18n"]["keys"]["label_es"] for a in self.policy_areas
             if a["policy_area_id"] == area_id),
            area_id
        )

        logger.info(
            f"✓ Policy area {area_id} ({area_name}): "
            f"score={avg_score:.4f}, quality={quality_level}"
        )

        return AreaScore(
            area_id=area_id,
            area_name=area_name,
            score=avg_score,
            quality_level=quality_level,
            dimension_scores=area_dim_scores,
            validation_passed=True,
            validation_details=validation_details
        )

    def run(
        self,
        dimension_scores: list[DimensionScore],
        group_by_keys: list[str]
    ) -> list[AreaScore]:
        """
        Run the area aggregation process.

        Args:
            dimension_scores: List of all dimension scores.
            group_by_keys: List of keys to group by.

        Returns:
            A list of AreaScore objects.
        """
        def key_func(d):
            return tuple(getattr(d, key) for key in group_by_keys)
        grouped_scores = group_by(dimension_scores, key_func)

        area_scores = []
        for group_key, scores in grouped_scores.items():
            group_by_values = dict(zip(group_by_keys, group_key, strict=False))
            score = self.aggregate_area(scores, group_by_values, weights=None)
            area_scores.append(score)

        return area_scores

    def _resolve_area_weights(
        self,
        area_id: str,
        dimension_scores: list[DimensionScore],
    ) -> list[float] | None:
        mapping = self.aggregation_settings.policy_area_dimension_weights.get(area_id)
        if not mapping:
            return None

        weights: list[float] = []
        for dim_score in dimension_scores:
            weight = mapping.get(dim_score.dimension_id)
            if weight is None:
                logger.debug(
                    "Missing weight for dimension %s in area %s – falling back to equal weights",
                    dim_score.dimension_id,
                    area_id,
                )
                return None
            weights.append(weight)

        total = sum(weights)
        if total <= 0:
            return None
        return [w / total for w in weights]

class ClusterAggregator:
    """
    Aggregates policy area scores into cluster scores (MESO level).

    Responsibilities:
    - Aggregate multiple area scores per cluster
    - Apply cluster-specific weights
    - Calculate coherence metrics
    - Validate cluster hermeticity
    """

    PENALTY_WEIGHT = 0.3  # Max 30% penalty for extreme imbalance
    MAX_SCORE = 3.0

    def __init__(
        self,
        monolith: dict[str, Any] | None = None,
        abort_on_insufficient: bool = True,
        aggregation_settings: AggregationSettings | None = None,
    ) -> None:
        """
        Initialize cluster aggregator.

        Args:
            monolith: Questionnaire monolith configuration (optional, required for run())
            abort_on_insufficient: Whether to abort on insufficient coverage

        Raises:
            ValueError: If monolith is None and required for operations
        """
        self.monolith = monolith
        self.abort_on_insufficient = abort_on_insufficient
        self.aggregation_settings = aggregation_settings or AggregationSettings.from_monolith(monolith)
        self.cluster_group_by_keys = self.aggregation_settings.cluster_group_by_keys or ["cluster_id"]

        # Extract configuration if monolith provided
        if monolith is not None:
            self.scoring_config = monolith["blocks"]["scoring"]
            self.niveles = monolith["blocks"]["niveles_abstraccion"]
            self.clusters = self.niveles["clusters"]
        else:
            self.scoring_config = None
            self.niveles = None
            self.clusters = None

        logger.info("ClusterAggregator initialized")

    def validate_cluster_hermeticity(
        self,
        cluster_def: dict[str, Any],
        area_scores: list[AreaScore]
    ) -> tuple[bool, str]:
        """
        Validate cluster hermeticity.

        Args:
            cluster_def: Cluster definition from monolith
            area_scores: List of area scores for this cluster

        Returns:
            Tuple of (is_valid, message)

        Raises:
            HermeticityValidationError: If hermeticity is violated
        """
        expected_areas = cluster_def.get("policy_area_ids", [])
        actual_areas = [a.area_id for a in area_scores]

        # Check for duplicate areas
        if len(actual_areas) != len(set(actual_areas)):
            msg = (
                f"Cluster hermeticity violation: "
                f"duplicate areas found for cluster {cluster_def['cluster_id']}"
            )
            logger.error(msg)
            if self.abort_on_insufficient:
                raise HermeticityValidationError(msg)
            return False, msg

        # Check that all expected areas are present
        missing_areas = set(expected_areas) - set(actual_areas)
        if missing_areas:
            msg = (
                f"Cluster hermeticity violation: "
                f"missing areas {missing_areas} for cluster {cluster_def['cluster_id']}"
            )
            logger.error(msg)
            if self.abort_on_insufficient:
                raise HermeticityValidationError(msg)
            return False, msg

        # Check for unexpected areas
        extra_areas = set(actual_areas) - set(expected_areas)
        if extra_areas:
            msg = (
                f"Cluster hermeticity violation: "
                f"unexpected areas {extra_areas} for cluster {cluster_def['cluster_id']}"
            )
            logger.error(msg)
            if self.abort_on_insufficient:
                raise HermeticityValidationError(msg)
            return False, msg

        logger.debug(f"Cluster hermeticity validated for {cluster_def['cluster_id']}")
        return True, "Cluster hermeticity validated"

    def apply_cluster_weights(
        self,
        area_scores: list[AreaScore],
        weights: list[float] | None = None
    ) -> float:
        """
        Apply cluster-specific weights to area scores.

        Args:
            area_scores: List of area scores
            weights: Optional weights (defaults to equal weights)

        Returns:
            Weighted average score

        Raises:
            WeightValidationError: If weights validation fails
        """
        scores = [a.score for a in area_scores]

        if weights is None:
            # Equal weights
            weights = [1.0 / len(scores)] * len(scores)

        # Validate weights length matches scores length
        if len(weights) != len(scores):
            msg = (
                f"Cluster weight length mismatch: "
                f"{len(weights)} weights for {len(scores)} area scores"
            )
            logger.error(msg)
            if self.abort_on_insufficient:
                raise WeightValidationError(msg)

        # Validate weights sum to 1.0
        weight_sum = sum(weights)
        tolerance = 1e-6
        if abs(weight_sum - 1.0) > tolerance:
            msg = f"Cluster weight validation failed: sum={weight_sum:.6f}"
            logger.error(msg)
            if self.abort_on_insufficient:
                raise WeightValidationError(msg)

        # Calculate weighted average
        weighted_avg = sum(s * w for s, w in zip(scores, weights, strict=False))

        logger.debug(
            f"Cluster weights applied: scores={scores}, "
            f"weights={weights}, result={weighted_avg:.4f}"
        )

        return weighted_avg

    def analyze_coherence(self, area_scores: list[AreaScore]) -> float:
        """
        Analyze cluster coherence.

        Coherence is measured as the inverse of standard deviation.
        Higher coherence means scores are more consistent.

        Args:
            area_scores: List of area scores

        Returns:
            Coherence value (0-1, where 1 is perfect coherence)
        """
        scores = [a.score for a in area_scores]

        if len(scores) <= 1:
            return 1.0

        # Calculate mean
        mean = sum(scores) / len(scores)

        # Calculate standard deviation
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        std_dev = variance ** 0.5

        # Convert to coherence (inverse relationship)
        # Normalize by max possible std dev (3.0 for 0-3 range)
        max_std = 3.0
        coherence = max(0.0, 1.0 - (std_dev / max_std))

        logger.debug(
            f"Coherence analysis: mean={mean:.4f}, "
            f"std_dev={std_dev:.4f}, coherence={coherence:.4f}"
        )

        return coherence

    def aggregate_cluster(
        self,
        area_scores: list[AreaScore],
        group_by_values: dict[str, Any],
        weights: list[float] | None = None,
    ) -> ClusterScore:
        """
        Aggregate a single MESO cluster from area scores.

        Args:
            area_scores: List of area scores for this cluster.
            group_by_values: Dictionary of grouping keys and their values.
            weights: Optional cluster-specific weights.

        Returns:
            ClusterScore with aggregated score and coherence.

        Raises:
            ValidationError: If validation fails.
        """
        cluster_id = group_by_values.get("cluster_id", "UNKNOWN")
        logger.info(f"Aggregating cluster {cluster_id}")

        validation_details = {}

        # Get cluster definition
        cluster_def = next(
            (c for c in self.clusters if c["cluster_id"] == cluster_id), None
        )

        if not cluster_def:
            logger.error(f"Cluster definition not found: {cluster_id}")
            return ClusterScore(
                cluster_id=cluster_id,
                cluster_name=cluster_id,
                areas=[],
                score=0.0,
                coherence=0.0,
                variance=0.0,
                weakest_area=None,
                area_scores=[],
                validation_passed=False,
                validation_details={"error": "Definition not found", "type": "config"},
            )

        cluster_name = cluster_def["i18n"]["keys"]["label_es"]
        expected_areas = cluster_def["policy_area_ids"]

        # The area_scores are already grouped.
        cluster_area_scores = area_scores

        # Validate hermeticity
        try:
            hermetic_valid, hermetic_msg = self.validate_cluster_hermeticity(
                cluster_def,
                cluster_area_scores
            )
            validation_details["hermeticity"] = {
                "valid": hermetic_valid,
                "message": hermetic_msg
            }
        except HermeticityValidationError as e:
            logger.error(f"Cluster hermeticity validation failed: {e}")
            return ClusterScore(
                cluster_id=cluster_id,
                cluster_name=cluster_name,
                areas=expected_areas,
                score=0.0,
                coherence=0.0,
                variance=0.0,
                weakest_area=None,
                area_scores=[],
                validation_passed=False,
                validation_details={"error": str(e), "type": "hermeticity"}
            )

        if not cluster_area_scores:
            logger.warning(f"No area scores for cluster {cluster_id}")
            return ClusterScore(
                cluster_id=cluster_id,
                cluster_name=cluster_name,
                areas=expected_areas,
                score=0.0,
                coherence=0.0,
                variance=0.0,
                weakest_area=None,
                area_scores=[],
                validation_passed=False,
                validation_details={"error": "No areas", "type": "empty"}
            )

        # Apply cluster weights
        resolved_weights = weights or self._resolve_cluster_weights(cluster_id, cluster_area_scores)
        try:
            weighted_score = self.apply_cluster_weights(cluster_area_scores, resolved_weights)
            validation_details["weights"] = {
                "valid": True,
                "weights": resolved_weights if resolved_weights else "equal",
                "score": weighted_score
            }
        except WeightValidationError as e:
            logger.error(f"Cluster weight validation failed: {e}")
            return ClusterScore(
                cluster_id=cluster_id,
                cluster_name=cluster_name,
                areas=expected_areas,
                score=0.0,
                coherence=0.0,
                variance=0.0,
                weakest_area=None,
                area_scores=cluster_area_scores,
                validation_passed=False,
                validation_details={"error": str(e), "type": "weights"}
            )

        # Analyze coherence and variance metrics
        coherence = self.analyze_coherence(cluster_area_scores)
        scores_array = [a.score for a in cluster_area_scores]
        if scores_array:
            mean_score = sum(scores_array) / len(scores_array)
            variance = sum((score - mean_score) ** 2 for score in scores_array) / len(scores_array)
        else:
            variance = 0.0
        weakest_area = min(cluster_area_scores, key=lambda a: a.score, default=None)

        std_dev = variance ** 0.5
        normalized_std = min(std_dev / self.MAX_SCORE, 1.0) if std_dev > 0 else 0.0
        penalty_factor = 1.0 - (normalized_std * self.PENALTY_WEIGHT)
        adjusted_score = weighted_score * penalty_factor

        validation_details["coherence"] = {
            "value": coherence,
            "interpretation": "high" if coherence > 0.8 else "medium" if coherence > 0.6 else "low"
        }
        validation_details["variance"] = variance
        if weakest_area:
            validation_details["weakest_area"] = weakest_area.area_id
        validation_details["imbalance_penalty"] = {
            "std_dev": std_dev,
            "penalty_factor": penalty_factor,
            "raw_score": weighted_score,
            "adjusted_score": adjusted_score,
        }

        logger.info(
            f"✓ Cluster {cluster_id} ({cluster_name}): "
            f"score={adjusted_score:.4f}, coherence={coherence:.4f}"
        )

        return ClusterScore(
            cluster_id=cluster_id,
            cluster_name=cluster_name,
            areas=expected_areas,
            score=adjusted_score,
            coherence=coherence,
            variance=variance,
            weakest_area=weakest_area.area_id if weakest_area else None,
            area_scores=cluster_area_scores,
            validation_passed=True,
            validation_details=validation_details
        )

    def run(
        self,
        area_scores: list[AreaScore],
        cluster_definitions: list[dict[str, Any]]
    ) -> list[ClusterScore]:
        """
        Run the cluster aggregation process.

        Args:
            area_scores: List of all area scores.
            cluster_definitions: List of cluster definitions from the monolith.

        Returns:
            A list of ClusterScore objects.
        """
        # Create a mapping from area_id to cluster_id
        area_to_cluster = {}
        for cluster in cluster_definitions:
            for area_id in cluster["policy_area_ids"]:
                area_to_cluster[area_id] = cluster["cluster_id"]

        # Assign cluster_id to each area score
        for score in area_scores:
            score.cluster_id = area_to_cluster.get(score.area_id)

        def key_func(area_score: AreaScore) -> tuple:
            return tuple(getattr(area_score, key) for key in self.cluster_group_by_keys)

        grouped_scores = group_by([s for s in area_scores if hasattr(s, 'cluster_id')], key_func)

        cluster_scores = []
        for group_key, scores in grouped_scores.items():
            group_by_values = dict(zip(self.cluster_group_by_keys, group_key, strict=False))
            score = self.aggregate_cluster(scores, group_by_values)
            cluster_scores.append(score)

        return cluster_scores

    def _resolve_cluster_weights(
        self,
        cluster_id: str,
        area_scores: list[AreaScore],
    ) -> list[float] | None:
        mapping = self.aggregation_settings.cluster_policy_area_weights.get(cluster_id)
        if not mapping:
            return None

        weights: list[float] = []
        for area_score in area_scores:
            weight = mapping.get(area_score.area_id)
            if weight is None:
                logger.debug(
                    "Missing weight for area %s in cluster %s – falling back to equal weights",
                    area_score.area_id,
                    cluster_id,
                )
                return None
            weights.append(weight)

        total = sum(weights)
        if total <= 0:
            return None
        return [w / total for w in weights]

class MacroAggregator:
    """
    Performs holistic macro evaluation (Q305).

    Responsibilities:
    - Aggregate all cluster scores
    - Calculate cross-cutting coherence
    - Identify systemic gaps
    - Assess strategic alignment
    """

    def __init__(
        self,
        monolith: dict[str, Any] | None = None,
        abort_on_insufficient: bool = True,
        aggregation_settings: AggregationSettings | None = None,
    ) -> None:
        """
        Initialize macro aggregator.

        Args:
            monolith: Questionnaire monolith configuration (optional, required for run())
            abort_on_insufficient: Whether to abort on insufficient coverage

        Raises:
            ValueError: If monolith is None and required for operations
        """
        self.monolith = monolith
        self.abort_on_insufficient = abort_on_insufficient
        self.aggregation_settings = aggregation_settings or AggregationSettings.from_monolith(monolith)

        # Extract configuration if monolith provided
        if monolith is not None:
            self.scoring_config = monolith["blocks"]["scoring"]
            self.niveles = monolith["blocks"]["niveles_abstraccion"]
        else:
            self.scoring_config = None
            self.niveles = None

        logger.info("MacroAggregator initialized")

    def calculate_cross_cutting_coherence(
        self,
        cluster_scores: list[ClusterScore]
    ) -> float:
        """
        Calculate cross-cutting coherence across all clusters.

        Args:
            cluster_scores: List of cluster scores

        Returns:
            Cross-cutting coherence value (0-1)
        """
        scores = [c.score for c in cluster_scores]

        if len(scores) <= 1:
            return 1.0

        # Calculate mean
        mean = sum(scores) / len(scores)

        # Calculate standard deviation
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        std_dev = variance ** 0.5

        # Convert to coherence
        max_std = 3.0
        coherence = max(0.0, 1.0 - (std_dev / max_std))

        logger.debug(
            f"Cross-cutting coherence: mean={mean:.4f}, "
            f"std_dev={std_dev:.4f}, coherence={coherence:.4f}"
        )

        return coherence

    def identify_systemic_gaps(
        self,
        area_scores: list[AreaScore]
    ) -> list[str]:
        """
        Identify systemic gaps (areas with INSUFICIENTE quality).

        Args:
            area_scores: List of area scores

        Returns:
            List of area names with systemic gaps
        """
        gaps = []
        for area in area_scores:
            if area.quality_level == "INSUFICIENTE":
                gaps.append(area.area_name)
                logger.warning(f"Systemic gap identified: {area.area_name}")

        logger.info(f"Systemic gaps identified: {len(gaps)}")
        return gaps

    def assess_strategic_alignment(
        self,
        cluster_scores: list[ClusterScore],
        dimension_scores: list[DimensionScore]
    ) -> float:
        """
        Assess strategic alignment across all levels.

        Args:
            cluster_scores: List of cluster scores
            dimension_scores: List of dimension scores

        Returns:
            Strategic alignment score (0-1)
        """
        # Calculate average cluster coherence
        cluster_coherence = (
            sum(c.coherence for c in cluster_scores) / len(cluster_scores)
            if cluster_scores else 0.0
        )

        # Calculate dimension validation rate
        validated_dims = sum(1 for d in dimension_scores if d.validation_passed)
        validation_rate = validated_dims / len(dimension_scores) if dimension_scores else 0.0

        # Strategic alignment is weighted combination
        alignment = (0.6 * cluster_coherence) + (0.4 * validation_rate)

        logger.debug(
            f"Strategic alignment: cluster_coherence={cluster_coherence:.4f}, "
            f"validation_rate={validation_rate:.4f}, alignment={alignment:.4f}"
        )

        return alignment

    def apply_rubric_thresholds(
        self,
        score: float,
        thresholds: dict[str, float] | None = None
    ) -> str:
        """
        Apply macro-level rubric thresholds.

        Args:
            score: Aggregated macro score (0-3 range)
            thresholds: Optional threshold definitions (dict with keys: EXCELENTE, BUENO, ACEPTABLE)
                       Each value should be a normalized threshold (0-1 range)

        Returns:
            Quality level (EXCELENTE, BUENO, ACEPTABLE, INSUFICIENTE)
        """
        # Clamp score to valid range [0, 3]
        clamped_score = max(0.0, min(3.0, score))

        # Normalize to 0-1 range
        normalized_score = clamped_score / 3.0

        # Use provided thresholds or defaults
        if thresholds:
            excellent_threshold = thresholds.get('EXCELENTE', 0.85)
            good_threshold = thresholds.get('BUENO', 0.70)
            acceptable_threshold = thresholds.get('ACEPTABLE', 0.55)
        else:
            excellent_threshold = 0.85
            good_threshold = 0.70
            acceptable_threshold = 0.55

        # Apply thresholds
        if normalized_score >= excellent_threshold:
            quality = "EXCELENTE"
        elif normalized_score >= good_threshold:
            quality = "BUENO"
        elif normalized_score >= acceptable_threshold:
            quality = "ACEPTABLE"
        else:
            quality = "INSUFICIENTE"

        logger.debug(
            f"Macro rubric applied: score={score:.4f}, "
            f"normalized={normalized_score:.4f}, quality={quality}"
        )

        return quality

    def evaluate_macro(
        self,
        cluster_scores: list[ClusterScore],
        area_scores: list[AreaScore],
        dimension_scores: list[DimensionScore]
    ) -> MacroScore:
        """
        Perform holistic macro evaluation (Q305).

        Args:
            cluster_scores: List of cluster scores (MESO level)
            area_scores: List of area scores
            dimension_scores: List of dimension scores

        Returns:
            MacroScore with holistic evaluation
        """
        logger.info("Performing macro holistic evaluation (Q305)")

        validation_details = {}

        if not cluster_scores:
            logger.error("No cluster scores available for macro evaluation")
            return MacroScore(
                score=0.0,
                quality_level="INSUFICIENTE",
                cross_cutting_coherence=0.0,
                systemic_gaps=[],
                strategic_alignment=0.0,
                cluster_scores=[],
                validation_passed=False,
                validation_details={"error": "No clusters", "type": "empty"}
            )

        # Calculate cross-cutting coherence
        cross_cutting_coherence = self.calculate_cross_cutting_coherence(cluster_scores)
        validation_details["coherence"] = {
            "value": cross_cutting_coherence,
            "clusters": len(cluster_scores)
        }

        # Identify systemic gaps
        systemic_gaps = self.identify_systemic_gaps(area_scores)
        validation_details["gaps"] = {
            "count": len(systemic_gaps),
            "areas": systemic_gaps
        }

        # Assess strategic alignment
        strategic_alignment = self.assess_strategic_alignment(
            cluster_scores,
            dimension_scores
        )
        validation_details["alignment"] = {
            "value": strategic_alignment
        }

        # Calculate overall macro score (weighted average of clusters)
        macro_score = self._calculate_macro_score(cluster_scores)

        # Apply quality rubric
        quality_level = self.apply_rubric_thresholds(macro_score)
        validation_details["rubric"] = {
            "score": macro_score,
            "quality_level": quality_level
        }

        logger.info(
            f"✓ Macro evaluation (Q305): score={macro_score:.4f}, "
            f"quality={quality_level}, coherence={cross_cutting_coherence:.4f}, "
            f"alignment={strategic_alignment:.4f}, gaps={len(systemic_gaps)}"
        )

        return MacroScore(
            score=macro_score,
            quality_level=quality_level,
            cross_cutting_coherence=cross_cutting_coherence,
            systemic_gaps=systemic_gaps,
            strategic_alignment=strategic_alignment,
            cluster_scores=cluster_scores,
            validation_passed=True,
            validation_details=validation_details
        )

    def _calculate_macro_score(self, cluster_scores: list[ClusterScore]) -> float:
        weights = self.aggregation_settings.macro_cluster_weights
        if not cluster_scores:
            return 0.0
        if not weights:
            return sum(c.score for c in cluster_scores) / len(cluster_scores)

        resolved_weights: list[float] = []
        for cluster in cluster_scores:
            weight = weights.get(cluster.cluster_id)
            if weight is None:
                logger.debug(
                    "Missing macro weight for cluster %s – falling back to equal weights",
                    cluster.cluster_id,
                )
                return sum(c.score for c in cluster_scores) / len(cluster_scores)
            resolved_weights.append(weight)

        total = sum(resolved_weights)
        if total <= 0:
            return sum(c.score for c in cluster_scores) / len(cluster_scores)

        normalized = [w / total for w in resolved_weights]
        return sum(
            cluster.score * weight
            for cluster, weight in zip(cluster_scores, normalized, strict=False)
        )
