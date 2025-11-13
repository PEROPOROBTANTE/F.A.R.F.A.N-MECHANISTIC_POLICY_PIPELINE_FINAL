"""Compatibility shim for :mod:`saaaaaa.analysis.scoring.scoring`."""
from __future__ import annotations

from saaaaaa.analysis.scoring import scoring as _impl

ScoringModality = _impl.ScoringModality
QualityLevel = _impl.QualityLevel
ScoringError = _impl.ScoringError
ModalityValidationError = _impl.ModalityValidationError
EvidenceStructureError = _impl.EvidenceStructureError
ScoredResult = _impl.ScoredResult
ModalityConfig = _impl.ModalityConfig
ScoringValidator = _impl.ScoringValidator
apply_scoring = _impl.apply_scoring
determine_quality_level = _impl.determine_quality_level
apply_rounding = _impl.apply_rounding
score_type_a = _impl.score_type_a
score_type_b = _impl.score_type_b
score_type_c = _impl.score_type_c
score_type_d = _impl.score_type_d
score_type_e = _impl.score_type_e
score_type_f = _impl.score_type_f

__all__ = [
    "ScoringModality",
    "QualityLevel",
    "ScoringError",
    "ModalityValidationError",
    "EvidenceStructureError",
    "ScoredResult",
    "ModalityConfig",
    "ScoringValidator",
    "apply_scoring",
    "determine_quality_level",
    "apply_rounding",
    "score_type_a",
    "score_type_b",
    "score_type_c",
    "score_type_d",
    "score_type_e",
    "score_type_f",
]
