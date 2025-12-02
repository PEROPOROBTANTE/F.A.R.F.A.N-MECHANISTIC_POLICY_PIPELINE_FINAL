"""
Scoring Package

Implements TYPE_A through TYPE_F scoring modalities with strict validation
and reproducible results.

NOTE: Evidence and MicroQuestionScorer are NOT in this package.
They exist in the parent MODULE: farfan_core/analysis/scoring.py
Import them directly from there: `from farfan_core.analysis.scoring import Evidence`
"""

# Import from this package's scoring.py
from .scoring import (
    EvidenceStructureError,
    ModalityConfig,
    ModalityValidationError,
    QualityLevel,
    ScoredResult,
    ScoringError,
    ScoringModality,
    ScoringValidator,
    apply_scoring,
    determine_quality_level,
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
    "apply_scoring",
    "determine_quality_level",
]

# ARCHITECTURAL NOTE FOR MAINTAINERS:
# Evidence and MicroQuestionScorer live in farfan_core/analysis/scoring.py (module)
# This __init__.py is for farfan_core/analysis/scoring/ (package)
# These are SEPARATE namespaces. Import Evidence from the module directly.
