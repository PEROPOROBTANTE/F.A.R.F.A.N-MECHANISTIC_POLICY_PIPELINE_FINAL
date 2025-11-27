"""Calibration Types Module.

This module defines the core data structures for calibration to avoid circular dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class MethodCalibration:
    """Calibration parameters for an orchestrator method.

    Attributes:
        score_min: Minimum score value (typically 0.0)
        score_max: Maximum score value (typically 1.0)
        min_evidence_snippets: Minimum number of evidence snippets required
        max_evidence_snippets: Maximum number of evidence snippets to collect
        contradiction_tolerance: Tolerance for contradictory evidence (0.0-1.0)
        uncertainty_penalty: Penalty for uncertain evidence (0.0-1.0)
        aggregation_weight: Weight in aggregation (typically 1.0)
        sensitivity: Method sensitivity to input variations (0.0-1.0)
        requires_numeric_support: Whether method requires numeric evidence
        requires_temporal_support: Whether method requires temporal evidence
        requires_source_provenance: Whether method requires source provenance
    """
    score_min: float
    score_max: float
    min_evidence_snippets: int
    max_evidence_snippets: int
    contradiction_tolerance: float
    uncertainty_penalty: float
    aggregation_weight: float
    sensitivity: float
    requires_numeric_support: bool
    requires_temporal_support: bool
    requires_source_provenance: bool

    def __post_init__(self):
        """Validate calibration parameters."""
        if not 0.0 <= self.score_min <= self.score_max <= 1.0:
            raise ValueError(f"Invalid score range: [{self.score_min}, {self.score_max}]")
        if not 0 <= self.min_evidence_snippets <= self.max_evidence_snippets:
            raise ValueError(
                f"Invalid evidence range: [{self.min_evidence_snippets}, {self.max_evidence_snippets}]"
            )
        if not 0.0 <= self.contradiction_tolerance <= 1.0:
            raise ValueError(f"Invalid contradiction_tolerance: {self.contradiction_tolerance}")
        if not 0.0 <= self.uncertainty_penalty <= 1.0:
            raise ValueError(f"Invalid uncertainty_penalty: {self.uncertainty_penalty}")
        if not 0.0 <= self.sensitivity <= 1.0:
            raise ValueError(f"Invalid sensitivity: {self.sensitivity}")
