"""
Chain Layer (@chain) - Full Implementation.

Validates data flow integrity for method chains.
Discrete scoring system: {1.0, 0.8, 0.6, 0.3, 0.0}
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


class ChainLayerEvaluator:
    """
    Validates chain integrity for method execution.

    Attributes:
        signatures: Dictionary mapping method IDs to their input/output signatures
    """

    def __init__(self, method_signatures: dict[str, Any]) -> None:
        """
        Initialize evaluator with method signatures.

        Args:
            method_signatures: Dict with method input/output signatures
        """
        self.signatures = method_signatures
        logger.info("chain_evaluator_initialized", extra={"num_methods": len(method_signatures)})

    def evaluate(
        self,
        method_id: str,
        provided_inputs: list[str],
        upstream_outputs: dict[str, str] = None
    ) -> float:
        """
        Validate chain integrity for a method.

        Discrete scoring: {1.0, 0.8, 0.6, 0.3, 0.0}

        Args:
            method_id: Method to validate
            provided_inputs: Inputs being provided
            upstream_outputs: Types from upstream (for type checking)

        Returns:
            Chain score ∈ {0.0, 0.3, 0.6, 0.8, 1.0}
        """
        if method_id not in self.signatures:
            logger.warning("method_signature_missing", extra={"method": method_id})
            return 0.0  # Undeclared method

        sig = self.signatures[method_id]
        required = set(sig.get("required_inputs", []))
        optional = set(sig.get("optional_inputs", []))
        critical_optional = set(sig.get("critical_optional", []))
        provided = set(provided_inputs)

        logger.info(
            "chain_validation_start",
            extra={
                "method": method_id,
                "required": list(required),
                "provided": list(provided)
            }
        )

        # Check 1: Required inputs (HARD FAILURE if missing)
        missing_required = required - provided
        if missing_required:
            logger.error(
                "chain_hard_mismatch",
                extra={
                    "method": method_id,
                    "missing_required": list(missing_required)
                }
            )
            return 0.0  # Hard mismatch

        # Check 2: Critical optional inputs
        missing_critical = critical_optional - provided
        if missing_critical:
            logger.warning(
                "chain_missing_critical_optional",
                extra={
                    "method": method_id,
                    "missing": list(missing_critical)
                }
            )
            return 0.3  # Missing critical optional

        # Check 3: Regular optional inputs
        missing_optional = (optional - critical_optional) - provided
        if missing_optional:
            logger.info(
                "chain_missing_optional",
                extra={
                    "method": method_id,
                    "missing": list(missing_optional)
                }
            )
            # Check severity: if many missing, lower score
            optional_count = len(optional - critical_optional)
            missing_count = len(missing_optional)
            if optional_count > 0:
                ratio = missing_count / optional_count
                if ratio > 0.5:
                    return 0.6  # Many optional missing
                else:
                    return 0.8  # Some optional missing

        # All inputs present
        logger.info("chain_valid", extra={"method": method_id, "score": 1.0})
        return 1.0

    def validate_chain_sequence(
        self,
        method_sequence: list[str],
        initial_inputs: list[str]
    ) -> dict[str, float]:
        """
        Validate entire chain of methods.

        Args:
            method_sequence: Ordered list of methods
            initial_inputs: Inputs available at start

        Returns:
            Dict mapping method_id to chain score
        """
        results = {}
        available_inputs = set(initial_inputs)

        for method_id in method_sequence:
            # Validate this method
            score = self.evaluate(method_id, list(available_inputs))
            results[method_id] = score

            # Add this method's output to available inputs
            # (simplified - assumes output name matches method)
            available_inputs.add(f"{method_id}_output")

        return results

    def compute_chain_quality(
        self,
        method_scores: dict[str, float]
    ) -> float:
        """
        Compute overall chain quality.

        Formula: Minimum score in chain (weakest link)

        Returns:
            Overall quality ∈ [0.0, 1.0]
        """
        if not method_scores:
            return 0.0

        # Weakest link principle
        min_score = min(method_scores.values())

        logger.info(
            "chain_quality_computed",
            extra={
                "min_score": min_score,
                "num_methods": len(method_scores)
            }
        )

        return min_score
