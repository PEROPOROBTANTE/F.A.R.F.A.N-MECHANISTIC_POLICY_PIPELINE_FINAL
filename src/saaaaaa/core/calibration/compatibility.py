"""
Method compatibility system.

This module loads and validates compatibility mappings that define
how well each method works in different contexts (Q, D, P).

Compatibility Scores (from theoretical model):
    1.0 = Primary (designed for this context)
    0.7 = Secondary (works well, not optimal)
    0.3 = Compatible (limited effectiveness)
    0.1 = Undeclared (penalty - not validated)
"""
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from .data_structures import CompatibilityMapping

if TYPE_CHECKING:
    from .data_structures import LayerScore

logger = logging.getLogger(__name__)


class CompatibilityRegistry:
    """
    Registry of method compatibility mappings.

    This loads from a JSON file that defines which methods work
    in which contexts (questions, dimensions, policies).
    """

    def __init__(self, config_path: Path | str) -> None:
        """
        Initialize registry from configuration file.

        Args:
            config_path: Path to method_compatibility.json
        """
        self.config_path = Path(config_path)
        self.mappings: dict[str, CompatibilityMapping] = {}
        self._load()

    def _load(self) -> None:
        """Load compatibility mappings from JSON."""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Compatibility config not found: {self.config_path}\n"
                f"Create this file with method compatibility definitions."
            )

        with open(self.config_path, encoding='utf-8') as f:
            data = json.load(f)

        # Validate structure
        if "method_compatibility" not in data:
            raise ValueError(
                "Config must have 'method_compatibility' key at top level"
            )

        # Load each method's compatibility
        for method_id, compat_data in data["method_compatibility"].items():
            self.mappings[method_id] = CompatibilityMapping(
                method_id=method_id,
                questions=compat_data.get("questions", {}),
                dimensions=compat_data.get("dimensions", {}),
                policies=compat_data.get("policies", {}),
            )

            logger.info(
                "compatibility_loaded",
                extra={
                    "method": method_id,
                    "num_questions": len(compat_data.get("questions", {})),
                    "num_dimensions": len(compat_data.get("dimensions", {})),
                    "num_policies": len(compat_data.get("policies", {})),
                }
            )

        logger.info(
            "compatibility_registry_loaded",
            extra={"total_methods": len(self.mappings)}
        )

    def get(self, method_id: str) -> CompatibilityMapping:
        """
        Get compatibility mapping for a method.

        If method not found, returns a mapping with all penalties (0.1).
        """
        if method_id not in self.mappings:
            logger.warning(
                "method_compatibility_not_found",
                extra={
                    "method": method_id,
                    "default_score": 0.1
                }
            )
            # Return empty mapping (will default to 0.1 penalties)
            return CompatibilityMapping(
                method_id=method_id,
                questions={},
                dimensions={},
                policies={},
            )

        return self.mappings[method_id]

    def validate_anti_universality(self, threshold: float = 0.9) -> dict[str, bool]:
        """
        Check Anti-Universality Theorem for all methods.

        Returns:
            Dict mapping method_id to compliance status (True = compliant)

        Raises:
            ValueError if any method violates the theorem
        """
        results = {}
        violations = []

        for method_id, mapping in self.mappings.items():
            is_compliant = mapping.check_anti_universality(threshold)
            results[method_id] = is_compliant

            if not is_compliant:
                violations.append(method_id)
                logger.error(
                    "anti_universality_violation",
                    extra={
                        "method": method_id,
                        "avg_q": sum(mapping.questions.values()) / len(mapping.questions) if mapping.questions else 0,
                        "avg_d": sum(mapping.dimensions.values()) / len(mapping.dimensions) if mapping.dimensions else 0,
                        "avg_p": sum(mapping.policies.values()) / len(mapping.policies) if mapping.policies else 0,
                    }
                )

        if violations:
            raise ValueError(
                f"Anti-Universality Theorem violated by methods: {violations}\n"
                f"No method can have avg compatibility ≥ {threshold} across ALL contexts."
            )

        return results


class ContextualLayerEvaluator:
    """
    Evaluates the three contextual layers: @q, @d, @p.

    These scores are direct lookups from the compatibility registry.
    """

    def __init__(self, registry: CompatibilityRegistry) -> None:
        self.registry = registry

    def _evaluate_question_raw(self, method_id: str, question_id: str) -> float:
        """
        Internal: Evaluate @q (question compatibility) - returns raw float.

        Returns score ∈ {1.0, 0.7, 0.3, 0.1}
        """
        mapping = self.registry.get(method_id)
        score = mapping.get_question_score(question_id)

        logger.debug(
            "question_compatibility",
            extra={
                "method": method_id,
                "question": question_id,
                "score": score
            }
        )

        return score

    def _evaluate_dimension_raw(self, method_id: str, dimension: str) -> float:
        """
        Internal: Evaluate @d (dimension compatibility) - returns raw float.

        Returns score ∈ {1.0, 0.7, 0.3, 0.1}
        """
        mapping = self.registry.get(method_id)
        score = mapping.get_dimension_score(dimension)

        logger.debug(
            "dimension_compatibility",
            extra={
                "method": method_id,
                "dimension": dimension,
                "score": score
            }
        )

        return score

    def _evaluate_policy_raw(self, method_id: str, policy_area: str) -> float:
        """
        Internal: Evaluate @p (policy area compatibility) - returns raw float.

        Returns score ∈ {1.0, 0.7, 0.3, 0.1}
        """
        mapping = self.registry.get(method_id)
        score = mapping.get_policy_score(policy_area)

        logger.debug(
            "policy_compatibility",
            extra={
                "method": method_id,
                "policy": policy_area,
                "score": score
            }
        )

        return score

    # Public methods for backward compatibility
    def evaluate_question(self, method_id: str, question_id: str) -> float:
        """Evaluate @q - backward compatibility (returns float)."""
        return self._evaluate_question_raw(method_id, question_id)

    def evaluate_dimension(self, method_id: str, dimension: str) -> float:
        """Evaluate @d - backward compatibility (returns float)."""
        return self._evaluate_dimension_raw(method_id, dimension)

    def evaluate_policy(self, method_id: str, policy_area: str) -> float:
        """Evaluate @p - backward compatibility (returns float)."""
        return self._evaluate_policy_raw(method_id, policy_area)

    def evaluate_all_contextual(
        self,
        method_id: str,
        question_id: str,
        dimension: str,
        policy_area: str
    ) -> dict[str, float]:
        """
        Evaluate all three contextual layers at once.

        Returns:
            Dict with keys 'q', 'd', 'p' and their scores
        """
        return {
            'q': self._evaluate_question_raw(method_id, question_id),
            'd': self._evaluate_dimension_raw(method_id, dimension),
            'p': self._evaluate_policy_raw(method_id, policy_area),
        }

    # New LayerScore-based methods
    def evaluate_question_layer(self, method_id: str, question_id: str) -> "LayerScore":  # type: ignore
        """
        Evaluate @q layer and return LayerScore.

        Args:
            method_id: Method identifier
            question_id: Question ID (e.g., "Q001")

        Returns:
            LayerScore for QUESTION layer
        """
        from .data_structures import LayerID, LayerScore

        score = self._evaluate_question_raw(method_id, question_id)

        # Interpret score level
        if score == 1.0:
            level = "primary"
        elif score == 0.7:
            level = "secondary"
        elif score == 0.3:
            level = "compatible"
        else:
            level = "undeclared (penalty)"

        return LayerScore(
            layer=LayerID.QUESTION,
            score=score,
            rationale=f"Question compatibility for {question_id}: {level}",
            metadata={
                "method": method_id,
                "question": question_id,
                "compatibility_level": level,
            }
        )

    def evaluate_dimension_layer(self, method_id: str, dimension: str) -> "LayerScore":  # type: ignore
        """
        Evaluate @d layer and return LayerScore.

        Args:
            method_id: Method identifier
            dimension: Dimension code (e.g., "DIM01")

        Returns:
            LayerScore for DIMENSION layer
        """
        from .data_structures import LayerID, LayerScore

        score = self._evaluate_dimension_raw(method_id, dimension)

        # Interpret score level
        if score == 1.0:
            level = "primary"
        elif score == 0.7:
            level = "secondary"
        elif score == 0.3:
            level = "compatible"
        else:
            level = "undeclared (penalty)"

        return LayerScore(
            layer=LayerID.DIMENSION,
            score=score,
            rationale=f"Dimension compatibility for {dimension}: {level}",
            metadata={
                "method": method_id,
                "dimension": dimension,
                "compatibility_level": level,
            }
        )

    def evaluate_policy_layer(self, method_id: str, policy_area: str) -> "LayerScore":  # type: ignore
        """
        Evaluate @p layer and return LayerScore.

        Args:
            method_id: Method identifier
            policy_area: Policy area code (e.g., "PA01")

        Returns:
            LayerScore for POLICY layer
        """
        from .data_structures import LayerID, LayerScore

        score = self._evaluate_policy_raw(method_id, policy_area)

        # Interpret score level
        if score == 1.0:
            level = "primary"
        elif score == 0.7:
            level = "secondary"
        elif score == 0.3:
            level = "compatible"
        else:
            level = "undeclared (penalty)"

        return LayerScore(
            layer=LayerID.POLICY,
            score=score,
            rationale=f"Policy compatibility for {policy_area}: {level}",
            metadata={
                "method": method_id,
                "policy_area": policy_area,
                "compatibility_level": level,
            }
        )
