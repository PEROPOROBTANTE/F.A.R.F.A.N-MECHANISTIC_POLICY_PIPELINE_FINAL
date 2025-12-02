"""Calibration Context Module.

This module provides context-aware calibration capabilities for the orchestrator.
It defines context types, modifiers, and functions to adjust calibration parameters
based on question context, policy area, and unit of analysis.

Design Principles:
- Context is immutable and copied on modification
- Modifiers are composable and applied in sequence
- Context inference from question IDs is deterministic
- All adjustments are traceable and reversible
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, replace
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .calibration_types import MethodCalibration

logger = logging.getLogger(__name__)


class PolicyArea(Enum):
    """Policy area classifications for context-aware calibration."""
    UNKNOWN = "unknown"
    FISCAL = "fiscal"
    SOCIAL = "social"
    INFRASTRUCTURE = "infrastructure"
    ENVIRONMENTAL = "environmental"
    GOVERNANCE = "governance"
    ECONOMIC = "economic"
    HEALTH = "health"
    EDUCATION = "education"
    SECURITY = "security"
    CULTURE = "culture"


class UnitOfAnalysis(Enum):
    """Unit of analysis for question context."""
    UNKNOWN = "unknown"
    BASELINE_GAP = "baseline_gap"
    INTERVENTION = "intervention"
    OUTCOME = "outcome"
    MECHANISM = "mechanism"
    CONTEXT = "context"
    TIMEFRAME = "timeframe"
    STAKEHOLDER = "stakeholder"
    RESOURCE = "resource"
    RISK = "risk"
    ASSUMPTION = "assumption"


@dataclass(frozen=True)
class CalibrationContext:
    """Context information for calibration adjustment.

    Attributes:
        question_id: Question identifier (e.g., "D1Q1")
        dimension: Dimension number (1-10)
        question_num: Question number within dimension
        policy_area: Policy area classification
        unit_of_analysis: Unit of analysis for the question
        method_position: Position of method in execution sequence (0-based)
        total_methods: Total number of methods to execute
    """
    question_id: str
    dimension: int = 0
    question_num: int = 0
    policy_area: PolicyArea = PolicyArea.UNKNOWN
    unit_of_analysis: UnitOfAnalysis = UnitOfAnalysis.UNKNOWN
    method_position: int = 0
    total_methods: int = 0

    @classmethod
    def from_question_id(cls, question_id: str) -> CalibrationContext:
        """Create context from question ID.

        Parses question IDs in format "D{dimension}Q{question}" (case-insensitive).
        Examples: "D1Q1", "d2q5", "D10Q25"

        Args:
            question_id: Question identifier string

        Returns:
            CalibrationContext with parsed dimension and question number
        """
        # Parse question ID format: D{dimension}Q{question}
        pattern = r"[dD](\d+)[qQ](\d+)"
        match = re.match(pattern, question_id)

        if match:
            dimension = int(match.group(1))
            question_num = int(match.group(2))
            return cls(
                question_id=question_id,
                dimension=dimension,
                question_num=question_num
            )
        else:
            logger.warning(f"Invalid question ID format: {question_id}")
            return cls(question_id=question_id, dimension=0, question_num=0)

    def with_policy_area(self, policy_area: PolicyArea) -> CalibrationContext:
        """Create a copy with updated policy area.

        Args:
            policy_area: New policy area

        Returns:
            New CalibrationContext with updated policy_area
        """
        return replace(self, policy_area=policy_area)

    def with_unit_of_analysis(self, unit_of_analysis: UnitOfAnalysis) -> CalibrationContext:
        """Create a copy with updated unit of analysis.

        Args:
            unit_of_analysis: New unit of analysis

        Returns:
            New CalibrationContext with updated unit_of_analysis
        """
        return replace(self, unit_of_analysis=unit_of_analysis)

    def with_method_position(self, position: int, total: int) -> CalibrationContext:
        """Create a copy with updated method position.

        Args:
            position: Position in method execution sequence (0-based)
            total: Total number of methods

        Returns:
            New CalibrationContext with updated method_position and total_methods
        """
        return replace(self, method_position=position, total_methods=total)


@dataclass(frozen=True)
class CalibrationModifier:
    """Modifier for adjusting calibration parameters based on context.

    All multipliers default to 1.0 (no change). Values outside valid ranges
    are clamped during application.

    Attributes:
        min_evidence_multiplier: Multiplier for min_evidence_snippets
        max_evidence_multiplier: Multiplier for max_evidence_snippets
        contradiction_tolerance_multiplier: Multiplier for contradiction_tolerance
        uncertainty_penalty_multiplier: Multiplier for uncertainty_penalty
        aggregation_weight_multiplier: Multiplier for aggregation_weight
        sensitivity_multiplier: Multiplier for sensitivity
    """
    min_evidence_multiplier: float = 1.0
    max_evidence_multiplier: float = 1.0
    contradiction_tolerance_multiplier: float = 1.0
    uncertainty_penalty_multiplier: float = 1.0
    aggregation_weight_multiplier: float = 1.0
    sensitivity_multiplier: float = 1.0

    def apply(self, calibration: MethodCalibration) -> MethodCalibration:
        """Apply modifier to a calibration.

        Args:
            calibration: Base MethodCalibration to modify

        Returns:
            New MethodCalibration with adjusted parameters
        """
        # Import at runtime to avoid circular dependency at module load time
        from .calibration_types import MethodCalibration

        # Apply multipliers and clamp to valid ranges
        min_evidence = int(calibration.min_evidence_snippets * self.min_evidence_multiplier)
        max_evidence = int(calibration.max_evidence_snippets * self.max_evidence_multiplier)

        # Ensure min <= max
        if min_evidence > max_evidence:
            min_evidence, max_evidence = max_evidence, min_evidence

        # Clamp evidence counts to reasonable ranges
        min_evidence = max(1, min_evidence)
        max_evidence = max(min_evidence, min(100, max_evidence))

        # Apply multipliers and clamp to [0.0, 1.0]
        contradiction_tolerance = max(0.0, min(1.0,
            calibration.contradiction_tolerance * self.contradiction_tolerance_multiplier
        ))

        uncertainty_penalty = max(0.0, min(1.0,
            calibration.uncertainty_penalty * self.uncertainty_penalty_multiplier
        ))

        aggregation_weight = max(0.0,
            calibration.aggregation_weight * self.aggregation_weight_multiplier
        )

        sensitivity = max(0.0, min(1.0,
            calibration.sensitivity * self.sensitivity_multiplier
        ))

        return MethodCalibration(
            score_min=calibration.score_min,
            score_max=calibration.score_max,
            min_evidence_snippets=min_evidence,
            max_evidence_snippets=max_evidence,
            contradiction_tolerance=contradiction_tolerance,
            uncertainty_penalty=uncertainty_penalty,
            aggregation_weight=aggregation_weight,
            sensitivity=sensitivity,
            requires_numeric_support=calibration.requires_numeric_support,
            requires_temporal_support=calibration.requires_temporal_support,
            requires_source_provenance=calibration.requires_source_provenance,
        )


# Dimension-specific modifiers
_DIMENSION_MODIFIERS = {
    1: CalibrationModifier(min_evidence_multiplier=1.3, sensitivity_multiplier=1.1),
    2: CalibrationModifier(max_evidence_multiplier=1.2, contradiction_tolerance_multiplier=0.8),
    3: CalibrationModifier(min_evidence_multiplier=1.2, uncertainty_penalty_multiplier=0.9),
    4: CalibrationModifier(sensitivity_multiplier=1.2),
    5: CalibrationModifier(min_evidence_multiplier=1.1, max_evidence_multiplier=1.1),
    6: CalibrationModifier(contradiction_tolerance_multiplier=0.9),
    7: CalibrationModifier(uncertainty_penalty_multiplier=0.85),
    8: CalibrationModifier(aggregation_weight_multiplier=1.15),
    9: CalibrationModifier(sensitivity_multiplier=1.15),
    10: CalibrationModifier(min_evidence_multiplier=1.4, sensitivity_multiplier=1.2),
}

# Policy area modifiers
_POLICY_AREA_MODIFIERS = {
    PolicyArea.FISCAL: CalibrationModifier(
        min_evidence_multiplier=1.3,
        sensitivity_multiplier=1.1
    ),
    PolicyArea.SOCIAL: CalibrationModifier(
        max_evidence_multiplier=1.2,
        uncertainty_penalty_multiplier=0.9
    ),
    PolicyArea.INFRASTRUCTURE: CalibrationModifier(
        contradiction_tolerance_multiplier=0.8,
        sensitivity_multiplier=1.1
    ),
    PolicyArea.ENVIRONMENTAL: CalibrationModifier(
        min_evidence_multiplier=1.2,
        uncertainty_penalty_multiplier=0.85
    ),
}

# Unit of analysis modifiers
_UNIT_OF_ANALYSIS_MODIFIERS = {
    UnitOfAnalysis.BASELINE_GAP: CalibrationModifier(
        min_evidence_multiplier=1.4,
        sensitivity_multiplier=1.2
    ),
    UnitOfAnalysis.INTERVENTION: CalibrationModifier(
        contradiction_tolerance_multiplier=0.9,
        sensitivity_multiplier=1.1
    ),
    UnitOfAnalysis.OUTCOME: CalibrationModifier(
        min_evidence_multiplier=1.3,
        uncertainty_penalty_multiplier=0.8
    ),
    UnitOfAnalysis.MECHANISM: CalibrationModifier(
        max_evidence_multiplier=1.2,
        sensitivity_multiplier=1.15
    ),
}


def resolve_contextual_calibration(
    base_calibration: MethodCalibration,
    context: CalibrationContext | None = None
) -> MethodCalibration:
    """Resolve calibration with context-aware adjustments.

    Applies modifiers based on:
    1. Dimension (if context.dimension > 0)
    2. Policy area (if not UNKNOWN)
    3. Unit of analysis (if not UNKNOWN)

    Args:
        base_calibration: Base MethodCalibration
        context: Optional CalibrationContext with adjustment information

    Returns:
        Adjusted MethodCalibration
    """
    if context is None:
        return base_calibration

    result = base_calibration

    # Apply dimension modifier
    if context.dimension > 0 and context.dimension in _DIMENSION_MODIFIERS:
        modifier = _DIMENSION_MODIFIERS[context.dimension]
        result = modifier.apply(result)
        logger.debug(f"Applied dimension {context.dimension} modifier")

    # Apply policy area modifier
    if context.policy_area != PolicyArea.UNKNOWN:
        if context.policy_area in _POLICY_AREA_MODIFIERS:
            modifier = _POLICY_AREA_MODIFIERS[context.policy_area]
            result = modifier.apply(result)
            logger.debug(f"Applied policy area {context.policy_area.value} modifier")

    # Apply unit of analysis modifier
    if context.unit_of_analysis != UnitOfAnalysis.UNKNOWN:
        if context.unit_of_analysis in _UNIT_OF_ANALYSIS_MODIFIERS:
            modifier = _UNIT_OF_ANALYSIS_MODIFIERS[context.unit_of_analysis]
            result = modifier.apply(result)
            logger.debug(f"Applied unit of analysis {context.unit_of_analysis.value} modifier")

    return result


def infer_context_from_question_id(question_id: str) -> CalibrationContext:
    """Infer context from question ID.

    This is a convenience function that creates a CalibrationContext from
    a question ID. Additional context can be added using the with_* methods.

    Args:
        question_id: Question identifier (e.g., "D1Q1")

    Returns:
        CalibrationContext with inferred dimension and question number
    """
    return CalibrationContext.from_question_id(question_id)


__all__ = [
    "CalibrationContext",
    "CalibrationModifier",
    "PolicyArea",
    "UnitOfAnalysis",
    "resolve_contextual_calibration",
    "infer_context_from_question_id",
]
