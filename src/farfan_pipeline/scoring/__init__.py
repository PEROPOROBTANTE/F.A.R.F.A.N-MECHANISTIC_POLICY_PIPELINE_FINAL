"""Scoring module package.

This package provides backward compatibility for code that imports
scoring classes from farfan_core.scoring.
"""

from farfan_pipeline.analysis.scoring.scoring import (
    EvidenceStructureError,
    ModalityConfig,
    ModalityValidationError,
    QualityLevel,
    ScoredResult,
    ScoringError,
    ScoringModality,
    ScoringValidator,
    apply_rounding,
    apply_scoring,
    clamp,
    determine_quality_level,
    score_type_a,
    score_type_b,
    score_type_c,
    score_type_d,
    score_type_e,
    score_type_f,
)

__all__ = [
    "EvidenceStructureError",
    "ModalityConfig",
    "ModalityValidationError",
    "QualityLevel",
    "ScoredResult",
    "ScoringError",
    "ScoringModality",
    "ScoringValidator",
    "apply_rounding",
    "apply_scoring",
    "clamp",
    "determine_quality_level",
    "score_type_a",
    "score_type_b",
    "score_type_c",
    "score_type_d",
    "score_type_e",
    "score_type_f",
]
