"""
Scoring Module - TYPE_A through TYPE_F Modality Implementation

This module implements the scoring system for the SAAAAAA policy analysis framework.
It provides:
- Application of 6 scoring modalities (TYPE_A through TYPE_F)
- Validation of evidence structure vs modality
- Assignment of quality levels
- Structured logging with strict abortability
- Reproducible ScoredResult outputs

Preconditions:
- Evidence and modality must be declared
- Evidence structure must match modality requirements

Invariants:
- Score range is maintained per modality definition
- Evidence structure is validated before scoring

Postconditions:
- ScoredResult is reproducible with same inputs
- No fallback or partial heuristic scoring
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from decimal import ROUND_DOWN, ROUND_HALF_EVEN, ROUND_HALF_UP, Decimal, InvalidOperation
from enum import Enum
from numbers import Real
from typing import Any, ClassVar
from saaaaaa import get_parameter_loader
from saaaaaa.core.calibration.decorators import calibrated_method

logger = logging.getLogger(__name__)

class ScoringModality(Enum):
    """Scoring modality types."""
    TYPE_A = "TYPE_A"  # Bayesian: Numerical claims, gaps, risks
    TYPE_B = "TYPE_B"  # DAG: Causal chains, ToC completeness
    TYPE_C = "TYPE_C"  # Coherence: Inverted contradictions
    TYPE_D = "TYPE_D"  # Pattern: Baseline data, formalization
    TYPE_E = "TYPE_E"  # Financial: Budget traceability
    TYPE_F = "TYPE_F"  # Beach: Mechanism inference, plausibility

class QualityLevel(Enum):
    """Quality level classifications."""
    EXCELENTE = "EXCELENTE"
    BUENO = "BUENO"
    ACEPTABLE = "ACEPTABLE"
    INSUFICIENTE = "INSUFICIENTE"

class ScoringError(Exception):
    """Base exception for scoring errors."""
    pass

class ModalityValidationError(ScoringError):
    """Exception raised when evidence structure doesn't match modality requirements."""
    pass

class EvidenceStructureError(ScoringError):
    """Exception raised when evidence structure is invalid."""
    pass

@dataclass(frozen=True)
class ScoredResult:
    """
    Reproducible scored result for a question.

    Attributes:
        question_global: Global question number (1-300)
        base_slot: Question slot identifier
        policy_area: Policy area ID (PA01-PA10)
        dimension: Dimension ID (DIM01-DIM06)
        modality: Scoring modality used (TYPE_A through TYPE_F)
        score: Raw score value
        normalized_score: Normalized score (0-1)
        quality_level: Quality level classification
        evidence_hash: SHA-256 hash of evidence for reproducibility
        metadata: Additional scoring metadata
        timestamp: ISO timestamp of scoring
    """
    question_global: int
    base_slot: str
    policy_area: str
    dimension: str
    modality: str
    score: float
    normalized_score: float
    quality_level: str
    evidence_hash: str
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))

    @calibrated_method("saaaaaa.analysis.scoring.scoring.ScoredResult.to_dict")
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return asdict(self)

    @staticmethod
    def compute_evidence_hash(evidence: dict[str, Any]) -> str:
        """
        Compute reproducible hash of evidence.

        Args:
            evidence: Evidence dictionary

        Returns:
            SHA-256 hash as hex string
        """
        canonical = json.dumps(evidence, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

@dataclass
class ModalityConfig:
    """
    Configuration for a scoring modality.

    Attributes:
        name: Modality name
        description: Modality description
        score_range: Min and max score values
        rounding_mode: Rounding mode (half_up, bankers, truncate)
        rounding_precision: Decimal precision for rounding
        required_evidence_keys: Required keys in evidence
        expected_elements: Expected number of elements (if applicable)
        deterministic: Whether scoring is deterministic
    """
    name: str
    description: str
    score_range: tuple[float, float]
    rounding_mode: str = "half_up"
    rounding_precision: int = 2
    required_evidence_keys: list[str] = field(default_factory=list)
    expected_elements: int | None = None
    deterministic: bool = True

    @calibrated_method("saaaaaa.analysis.scoring.scoring.ModalityConfig.validate_evidence")
    def validate_evidence(self, evidence: dict[str, Any]) -> None:
        """
        Validate evidence structure against modality requirements.

        Args:
            evidence: Evidence dictionary to validate

        Raises:
            EvidenceStructureError: If evidence is missing required keys
            ModalityValidationError: If evidence structure doesn't match modality
        """
        if not isinstance(evidence, dict):
            raise EvidenceStructureError(
                f"Evidence must be a dictionary, got {type(evidence).__name__}"
            )

        # Check required keys
        missing_keys = [key for key in self.required_evidence_keys if key not in evidence]
        if missing_keys:
            raise EvidenceStructureError(
                f"Evidence missing required keys for {self.name}: {missing_keys}"
            )

        # Validate expected elements if applicable
        if self.expected_elements is not None:
            elements = evidence.get("elements", [])
            if not isinstance(elements, list):
                raise ModalityValidationError(
                    f"{self.name} requires 'elements' to be a list, got {type(elements).__name__}"
                )

class ScoringValidator:
    """Validates evidence structure against modality requirements."""

    # Modality configurations
    MODALITY_CONFIGS: ClassVar[dict[ScoringModality, ModalityConfig]] = {
        ScoringModality.TYPE_A: ModalityConfig(
            name="TYPE_A",
            description="Bayesian: Numerical claims, gaps, risks",
            score_range=(get_parameter_loader().get("saaaaaa.analysis.scoring.scoring.ModalityConfig.validate_evidence").get("auto_param_L182_25", 0.0), 3.0),
            required_evidence_keys=["elements", "confidence"],
            expected_elements=4,
        ),
        ScoringModality.TYPE_B: ModalityConfig(
            name="TYPE_B",
            description="DAG: Causal chains, ToC completeness",
            score_range=(get_parameter_loader().get("saaaaaa.analysis.scoring.scoring.ModalityConfig.validate_evidence").get("auto_param_L189_25", 0.0), 3.0),
            required_evidence_keys=["elements", "completeness"],
            expected_elements=3,
        ),
        ScoringModality.TYPE_C: ModalityConfig(
            name="TYPE_C",
            description="Coherence: Inverted contradictions",
            score_range=(get_parameter_loader().get("saaaaaa.analysis.scoring.scoring.ModalityConfig.validate_evidence").get("auto_param_L196_25", 0.0), 3.0),
            required_evidence_keys=["elements", "coherence_score"],
            expected_elements=2,
        ),
        ScoringModality.TYPE_D: ModalityConfig(
            name="TYPE_D",
            description="Pattern: Baseline data, formalization",
            score_range=(get_parameter_loader().get("saaaaaa.analysis.scoring.scoring.ModalityConfig.validate_evidence").get("auto_param_L203_25", 0.0), 3.0),
            required_evidence_keys=["elements", "pattern_matches"],
            expected_elements=3,
        ),
        ScoringModality.TYPE_E: ModalityConfig(
            name="TYPE_E",
            description="Financial: Budget traceability",
            score_range=(get_parameter_loader().get("saaaaaa.analysis.scoring.scoring.ModalityConfig.validate_evidence").get("auto_param_L210_25", 0.0), 3.0),
            required_evidence_keys=["elements", "traceability"],
        ),
        ScoringModality.TYPE_F: ModalityConfig(
            name="TYPE_F",
            description="Beach: Mechanism inference, plausibility",
            score_range=(get_parameter_loader().get("saaaaaa.analysis.scoring.scoring.ModalityConfig.validate_evidence").get("auto_param_L216_25", 0.0), 3.0),
            required_evidence_keys=["elements", "plausibility"],
        ),
    }

    @classmethod
    def validate(
        cls,
        evidence: dict[str, Any],
        modality: ScoringModality,
    ) -> None:
        """
        Validate evidence structure against modality.

        Args:
            evidence: Evidence dictionary
            modality: Scoring modality

        Raises:
            ModalityValidationError: If validation fails

        Note:
            This function has strict abortability - any validation failure
            will raise an exception and halt processing.
        """
        config = cls.MODALITY_CONFIGS.get(modality)
        if not config:
            raise ModalityValidationError(f"Unknown modality: {modality}")

        logger.info(f"Validating evidence for {modality.value}")

        try:
            config.validate_evidence(evidence)
            logger.info(f"✓ Evidence validation passed for {modality.value}")
        except (EvidenceStructureError, ModalityValidationError) as e:
            logger.exception(f"✗ Evidence validation failed for {modality.value}: {e}")
            raise

    @classmethod
    def get_config(cls, modality: ScoringModality) -> ModalityConfig:
        """Get configuration for a modality."""
        config = cls.MODALITY_CONFIGS.get(modality)
        if not config:
            raise ModalityValidationError(f"Unknown modality: {modality}")
        return config

def clamp(value: float, lower: float, upper: float) -> float:
    """Clamp *value* to the inclusive range ``[lower, upper]``."""

    if lower > upper:
        raise ValueError("Lower bound cannot exceed upper bound")

    return min(max(value, lower), upper)

def apply_rounding(
    value: float,
    mode: str = "half_up",
    precision: int = 2,
) -> float:
    """
    Apply rounding to a numeric value.

    Args:
        value: Value to round
        mode: Rounding mode (half_up, bankers, truncate)
        precision: Decimal precision

    Returns:
        Rounded value
    """
    if precision < 0:
        raise ValueError("Precision must be non-negative")

    decimal_value = Decimal(str(value))
    quantize_exp = Decimal(10) ** -precision

    if mode == "half_up":
        rounding_mode = ROUND_HALF_UP
    elif mode == "bankers":
        rounding_mode = ROUND_HALF_EVEN
    elif mode == "truncate":
        rounding_mode = ROUND_DOWN
    else:
        raise ValueError(f"Unknown rounding mode: {mode}")

    try:
        rounded = decimal_value.quantize(quantize_exp, rounding=rounding_mode)
    except InvalidOperation as exc:
        raise ValueError(f"Failed to round value {value}: {exc}") from exc

    return float(rounded)

def _validate_quality_thresholds(thresholds: dict[str, float]) -> dict[str, float]:
    """Validate custom quality thresholds.

    Returns a copy of *thresholds* with float values if validation succeeds.
    """

    if not isinstance(thresholds, dict):
        raise ValueError("Quality thresholds must be provided as a dictionary")

    required_keys = ("EXCELENTE", "BUENO", "ACEPTABLE")
    missing = [key for key in required_keys if key not in thresholds]
    if missing:
        raise ValueError(f"Missing quality thresholds for: {', '.join(missing)}")

    validated: dict[str, float] = {}
    for key in required_keys:
        value = thresholds[key]

        if isinstance(value, bool) or not isinstance(value, (int, float, Decimal, Real)):
            raise ValueError(
                f"Threshold for {key} must be a real number between 0 and 1"
            )

        numeric_value = float(value)
        if math.isnan(numeric_value) or math.isinf(numeric_value):
            raise ValueError(f"Threshold for {key} cannot be NaN or infinite")

        if not get_parameter_loader().get("saaaaaa.analysis.scoring.scoring.ModalityConfig.validate_evidence").get("auto_param_L335_15", 0.0) <= numeric_value <= get_parameter_loader().get("saaaaaa.analysis.scoring.scoring.ModalityConfig.validate_evidence").get("auto_param_L335_39", 1.0):
            raise ValueError(
                f"Threshold for {key} must be between 0 and 1 inclusive"
            )

        validated[key] = numeric_value

    if not (
        validated["EXCELENTE"] >= validated["BUENO"] >= validated["ACEPTABLE"]
    ):
        raise ValueError(
            "Quality thresholds must satisfy EXCELENTE >= BUENO >= ACEPTABLE"
        )

    return validated

def score_type_a(evidence: dict[str, Any], config: ModalityConfig) -> tuple[float, dict[str, Any]]:
    """
    Score TYPE_A evidence: Bayesian numerical claims, gaps, risks.

    Expects:
    - elements: List of up to 4 elements
    - confidence: Bayesian confidence score (0-1)

    Scoring:
    - Count elements (max 4)
    - Weight by confidence
    - Scale to 0-3 range

    Args:
        evidence: Evidence dictionary
        config: Modality configuration

    Returns:
        Tuple of (score, metadata)
    """
    elements = evidence.get("elements", [])
    confidence = evidence.get("confidence", get_parameter_loader().get("saaaaaa.analysis.scoring.scoring.ModalityConfig.validate_evidence").get("auto_param_L372_44", 0.0))

    if not isinstance(elements, list):
        raise ModalityValidationError("TYPE_A: 'elements' must be a list")

    if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
        raise ModalityValidationError("TYPE_A: 'confidence' must be a number between 0 and 1")

    # Count valid elements (up to expected)
    element_count = min(len(elements), config.expected_elements or 4)

    max_elements = config.expected_elements or 4
    max_score = config.score_range[1] if config.score_range else 3.0
    min_score = config.score_range[0] if config.score_range else get_parameter_loader().get("saaaaaa.analysis.scoring.scoring.ModalityConfig.validate_evidence").get("auto_param_L385_65", 0.0)

    # Calculate raw score: count weighted by confidence, scale to range
    max_elements = config.expected_elements if config.expected_elements is not None else 4
    scale = config.score_range[1] if config.score_range else 3.0
    raw_score = (element_count / max(1, max_elements)) * scale * confidence

    # Clamp to valid range
    score = max(min_score, min(max_score, raw_score))

    metadata = {
        "element_count": element_count,
        "confidence": confidence,
        "raw_score": raw_score,
        "expected_elements": config.expected_elements,
        "max_score": max_score,
    }

    logger.info(
        f"TYPE_A score: {score:.2f} "
        f"(elements={element_count}, confidence={confidence:.2f})"
    )

    return score, metadata

def score_type_b(evidence: dict[str, Any], config: ModalityConfig) -> tuple[float, dict[str, Any]]:
    """
    Score TYPE_B evidence: DAG causal chains, ToC completeness.

    Expects:
    - elements: List of causal chain elements (up to 3)
    - completeness: DAG completeness score (0-1)

    Scoring:
    - Count causal elements (max 3)
    - Weight by completeness
    - Each element worth 1 point

    Args:
        evidence: Evidence dictionary
        config: Modality configuration

    Returns:
        Tuple of (score, metadata)
    """
    elements = evidence.get("elements", [])
    completeness = evidence.get("completeness", get_parameter_loader().get("saaaaaa.analysis.scoring.scoring.ModalityConfig.validate_evidence").get("auto_param_L431_48", 0.0))

    if not isinstance(elements, list):
        raise ModalityValidationError("TYPE_B: 'elements' must be a list")

    if not isinstance(completeness, (int, float)) or not (0 <= completeness <= 1):
        raise ModalityValidationError("TYPE_B: 'completeness' must be a number between 0 and 1")

    # Count valid elements (up to expected)
    element_count = min(len(elements), config.expected_elements or 3)

    # Calculate raw score: each element worth 1 point, weighted by completeness
    raw_score = float(element_count) * completeness

    # Clamp to valid range
    score = max(config.score_range[0], min(config.score_range[1], raw_score))

    metadata = {
        "element_count": element_count,
        "completeness": completeness,
        "raw_score": raw_score,
        "expected_elements": config.expected_elements,
    }

    logger.info(
        f"TYPE_B score: {score:.2f} "
        f"(elements={element_count}, completeness={completeness:.2f})"
    )

    return score, metadata

def score_type_c(evidence: dict[str, Any], config: ModalityConfig) -> tuple[float, dict[str, Any]]:
    """
    Score TYPE_C evidence: Coherence via inverted contradictions.

    Expects:
    - elements: List of coherence elements (up to 2)
    - coherence_score: Inverted contradiction score (0-1, higher is better)

    Scoring:
    - Count coherence elements (max 2)
    - Scale by coherence score
    - Scale to 0-3 range

    Args:
        evidence: Evidence dictionary
        config: Modality configuration

    Returns:
        Tuple of (score, metadata)
    """
    elements = evidence.get("elements", [])
    coherence_score = evidence.get("coherence_score", get_parameter_loader().get("saaaaaa.analysis.scoring.scoring.ModalityConfig.validate_evidence").get("auto_param_L483_54", 0.0))

    if not isinstance(elements, list):
        raise ModalityValidationError("TYPE_C: 'elements' must be a list")

    if not isinstance(coherence_score, (int, float)) or not (0 <= coherence_score <= 1):
        raise ModalityValidationError("TYPE_C: 'coherence_score' must be a number between 0 and 1")

    # Count valid elements (up to expected)
    element_count = min(len(elements), config.expected_elements or 2)

    # Calculate raw score: scale elements to range, weighted by coherence
    raw_score = (element_count / 2.0) * 3.0 * coherence_score

    # Clamp to valid range
    score = max(config.score_range[0], min(config.score_range[1], raw_score))

    metadata = {
        "element_count": element_count,
        "coherence_score": coherence_score,
        "raw_score": raw_score,
        "expected_elements": config.expected_elements,
    }

    logger.info(
        f"TYPE_C score: {score:.2f} "
        f"(elements={element_count}, coherence={coherence_score:.2f})"
    )

    return score, metadata

def score_type_d(evidence: dict[str, Any], config: ModalityConfig) -> tuple[float, dict[str, Any]]:
    """
    Score TYPE_D evidence: Pattern matching for baseline data.

    Expects:
    - elements: List of pattern matches (up to 3)
    - pattern_matches: Number of successful pattern matches

    Scoring:
    - Count pattern matches (max 3)
    - Weight by match quality if available
    - Scale to 0-3 range

    Args:
        evidence: Evidence dictionary
        config: Modality configuration

    Returns:
        Tuple of (score, metadata)
    """
    elements = evidence.get("elements", [])
    pattern_matches = evidence.get("pattern_matches", 0)

    if not isinstance(elements, list):
        raise ModalityValidationError("TYPE_D: 'elements' must be a list")

    if not isinstance(pattern_matches, (int, float)) or pattern_matches < 0:
        raise ModalityValidationError("TYPE_D: 'pattern_matches' must be a non-negative number")

    # Count valid elements (up to expected)
    element_count = min(len(elements), config.expected_elements or 3)

    # Use actual pattern matches if available, otherwise use element count
    match_count = min(pattern_matches, element_count) if pattern_matches > 0 else element_count

    # Calculate raw score: scale to 0-3 range
    raw_score = (match_count / 3.0) * 3.0

    # Clamp to valid range
    score = max(config.score_range[0], min(config.score_range[1], raw_score))

    metadata = {
        "element_count": element_count,
        "pattern_matches": match_count,
        "raw_score": raw_score,
        "expected_elements": config.expected_elements,
    }

    logger.info(
        f"TYPE_D score: {score:.2f} "
        f"(elements={element_count}, matches={match_count})"
    )

    return score, metadata

def score_type_e(evidence: dict[str, Any], config: ModalityConfig) -> tuple[float, dict[str, Any]]:
    """
    Score TYPE_E evidence: Financial budget traceability.

    Expects:
    - elements: List of budget elements
    - traceability: Boolean or numeric traceability score

    Scoring:
    - Boolean presence check
    - If numeric traceability provided, use that
    - Scale to 0-3 range

    Args:
        evidence: Evidence dictionary
        config: Modality configuration

    Returns:
        Tuple of (score, metadata)
    """
    elements = evidence.get("elements", [])
    traceability = evidence.get("traceability", False)

    if not isinstance(elements, list):
        raise ModalityValidationError("TYPE_E: 'elements' must be a list")

    # Handle both boolean and numeric traceability
    if isinstance(traceability, bool):
        traceability_score = get_parameter_loader().get("saaaaaa.analysis.scoring.scoring.ModalityConfig.validate_evidence").get("auto_param_L597_29", 1.0) if traceability else get_parameter_loader().get("saaaaaa.analysis.scoring.scoring.ModalityConfig.validate_evidence").get("auto_param_L597_54", 0.0)
    elif isinstance(traceability, (int, float)):
        if not (0 <= traceability <= 1):
            raise ModalityValidationError("TYPE_E: numeric 'traceability' must be between 0 and 1")
        traceability_score = float(traceability)
    else:
        raise ModalityValidationError("TYPE_E: 'traceability' must be boolean or numeric")

    # Count valid elements
    element_count = len(elements)
    has_elements = element_count > 0

    # Calculate raw score: presence check weighted by traceability
    raw_score = 3.0 * traceability_score if has_elements else get_parameter_loader().get("saaaaaa.analysis.scoring.scoring.ModalityConfig.validate_evidence").get("auto_param_L610_62", 0.0)

    # Clamp to valid range
    score = max(config.score_range[0], min(config.score_range[1], raw_score))

    metadata = {
        "element_count": element_count,
        "traceability": traceability_score,
        "raw_score": raw_score,
        "has_elements": has_elements,
    }

    logger.info(
        f"TYPE_E score: {score:.2f} "
        f"(elements={element_count}, traceability={traceability_score:.2f})"
    )

    return score, metadata

def score_type_f(evidence: dict[str, Any], config: ModalityConfig) -> tuple[float, dict[str, Any]]:
    """
    Score TYPE_F evidence: Beach mechanism inference and plausibility.

    Expects:
    - elements: List of mechanism elements
    - plausibility: Plausibility score (0-1)

    Scoring:
    - Continuous scale based on plausibility
    - Weight by element presence
    - Scale to 0-3 range

    Args:
        evidence: Evidence dictionary
        config: Modality configuration

    Returns:
        Tuple of (score, metadata)
    """
    elements = evidence.get("elements", [])
    plausibility = evidence.get("plausibility", get_parameter_loader().get("saaaaaa.analysis.scoring.scoring.ModalityConfig.validate_evidence").get("auto_param_L650_48", 0.0))

    if not isinstance(elements, list):
        raise ModalityValidationError("TYPE_F: 'elements' must be a list")

    if not isinstance(plausibility, (int, float)) or not (0 <= plausibility <= 1):
        raise ModalityValidationError("TYPE_F: 'plausibility' must be a number between 0 and 1")

    # Count valid elements
    element_count = len(elements)

    # Calculate raw score: continuous scale weighted by plausibility
    raw_score = 3.0 * plausibility if element_count > 0 else get_parameter_loader().get("saaaaaa.analysis.scoring.scoring.ModalityConfig.validate_evidence").get("auto_param_L662_61", 0.0)

    # Clamp to valid range
    score = max(config.score_range[0], min(config.score_range[1], raw_score))

    metadata = {
        "element_count": element_count,
        "plausibility": plausibility,
        "raw_score": raw_score,
    }

    logger.info(
        f"TYPE_F score: {score:.2f} "
        f"(elements={element_count}, plausibility={plausibility:.2f})"
    )

    return score, metadata

# Scoring function registry
SCORING_FUNCTIONS = {
    ScoringModality.TYPE_A: score_type_a,
    ScoringModality.TYPE_B: score_type_b,
    ScoringModality.TYPE_C: score_type_c,
    ScoringModality.TYPE_D: score_type_d,
    ScoringModality.TYPE_E: score_type_e,
    ScoringModality.TYPE_F: score_type_f,
}

def determine_quality_level(
    normalized_score: float,
    thresholds: dict[str, float] | None = None,
) -> QualityLevel:
    """
    Determine quality level from normalized score.

    Args:
        normalized_score: Score normalized to 0-1 range
        thresholds: Optional custom thresholds

    Returns:
        Quality level

    Note:
        Default thresholds:
        - EXCELENTE: >= get_parameter_loader().get("saaaaaa.analysis.scoring.scoring.ModalityConfig.validate_evidence").get("auto_param_L706_24", 0.85)
        - BUENO: >= get_parameter_loader().get("saaaaaa.analysis.scoring.scoring.ModalityConfig.validate_evidence").get("auto_param_L707_20", 0.70)
        - ACEPTABLE: >= get_parameter_loader().get("saaaaaa.analysis.scoring.scoring.ModalityConfig.validate_evidence").get("auto_param_L708_24", 0.55)
        - INSUFICIENTE: < get_parameter_loader().get("saaaaaa.analysis.scoring.scoring.ModalityConfig.validate_evidence").get("auto_param_L709_26", 0.55)
    """
    if thresholds is None:
        thresholds = {
            "EXCELENTE": get_parameter_loader().get("saaaaaa.analysis.scoring.scoring.ModalityConfig.validate_evidence").get("auto_param_L713_25", 0.85),
            "BUENO": get_parameter_loader().get("saaaaaa.analysis.scoring.scoring.ModalityConfig.validate_evidence").get("auto_param_L714_21", 0.70),
            "ACEPTABLE": get_parameter_loader().get("saaaaaa.analysis.scoring.scoring.ModalityConfig.validate_evidence").get("auto_param_L715_25", 0.55),
        }

    thresholds = _validate_quality_thresholds(thresholds)

    # Clamp score to account for minor floating-point drift
    normalized_score = clamp(float(normalized_score), get_parameter_loader().get("saaaaaa.analysis.scoring.scoring.ModalityConfig.validate_evidence").get("auto_param_L721_54", 0.0), get_parameter_loader().get("saaaaaa.analysis.scoring.scoring.ModalityConfig.validate_evidence").get("auto_param_L721_59", 1.0))

    if normalized_score >= thresholds["EXCELENTE"]:
        return QualityLevel.EXCELENTE
    elif normalized_score >= thresholds["BUENO"]:
        return QualityLevel.BUENO
    elif normalized_score >= thresholds["ACEPTABLE"]:
        return QualityLevel.ACEPTABLE
    else:
        return QualityLevel.INSUFICIENTE

def apply_scoring(
    question_global: int,
    base_slot: str,
    policy_area: str,
    dimension: str,
    evidence: dict[str, Any],
    modality: str,
    quality_thresholds: dict[str, float] | None = None,
) -> ScoredResult:
    """
    Apply scoring to evidence using specified modality.

    This is the main entry point for scoring. It:
    1. Validates evidence structure against modality
    2. Applies modality-specific scoring function
    3. Normalizes score to 0-1 range
    4. Determines quality level
    5. Returns reproducible ScoredResult

    Args:
        question_global: Global question number (1-300)
        base_slot: Question slot identifier
        policy_area: Policy area ID (PA01-PA10)
        dimension: Dimension ID (DIM01-DIM06)
        evidence: Evidence dictionary
        modality: Scoring modality (TYPE_A through TYPE_F)
        quality_thresholds: Optional custom quality thresholds

    Returns:
        ScoredResult

    Raises:
        ModalityValidationError: If evidence validation fails
        ScoringError: If scoring fails

    Note:
        This function has strict abortability. Any validation or scoring
        error will raise an exception and halt processing. No fallback
        or partial scoring is performed.
    """
    logger.info(
        f"Scoring question {question_global} ({base_slot}) "
        f"using {modality}"
    )

    # Parse modality
    try:
        modality_enum = ScoringModality(modality)
    except ValueError as e:
        raise ModalityValidationError(
            f"Invalid modality: {modality}. "
            f"Must be one of: {[m.value for m in ScoringModality]}"
        ) from e

    # Validate evidence structure
    ScoringValidator.validate(evidence, modality_enum)

    # Get modality configuration
    config = ScoringValidator.get_config(modality_enum)

    # Get scoring function
    scoring_func = SCORING_FUNCTIONS.get(modality_enum)
    if not scoring_func:
        raise ScoringError(f"No scoring function for {modality}")

    # Apply scoring
    try:
        score, metadata = scoring_func(evidence, config)
    except (ModalityValidationError, EvidenceStructureError, ScoringError) as e:
        logger.exception(f"Scoring failed for {modality}: {e}")
        raise ScoringError(f"Scoring failed for {modality}: {e}") from e
    except Exception as e:
        logger.exception(f"Unexpected error in scoring {modality}: {e}")
        raise ScoringError(f"Unexpected error in scoring {modality}: {e}") from e

    # Apply rounding
    rounded_score = apply_rounding(
        score,
        mode=config.rounding_mode,
        precision=config.rounding_precision,
    )

    min_score, max_score = config.score_range
    if max_score <= min_score:
        raise ScoringError(
            f"Invalid score range for {modality}: {config.score_range}"
        )

    # Guard against errant modality implementations
    clamped_score = clamp(rounded_score, min_score, max_score)
    score_clamped = not math.isclose(clamped_score, rounded_score, rel_tol=1e-9, abs_tol=1e-9)

    # Normalize score to 0-1 range
    normalized_score = (clamped_score - min_score) / (max_score - min_score)
    normalized_score = clamp(normalized_score, get_parameter_loader().get("saaaaaa.analysis.scoring.scoring.ModalityConfig.validate_evidence").get("auto_param_L826_47", 0.0), get_parameter_loader().get("saaaaaa.analysis.scoring.scoring.ModalityConfig.validate_evidence").get("auto_param_L826_52", 1.0))

    # Determine quality level
    quality_level = determine_quality_level(normalized_score, quality_thresholds)

    # Compute evidence hash for reproducibility
    evidence_hash = ScoredResult.compute_evidence_hash(evidence)

    # Build result
    result = ScoredResult(
        question_global=question_global,
        base_slot=base_slot,
        policy_area=policy_area,
        dimension=dimension,
        modality=modality,
        score=rounded_score,
        normalized_score=normalized_score,
        quality_level=quality_level.value,
        evidence_hash=evidence_hash,
        metadata={
            **metadata,
            "score_range": config.score_range,
            "rounding_mode": config.rounding_mode,
            "rounding_precision": config.rounding_precision,
            "score_clamped": score_clamped,
        },
    )

    logger.info(
        f"✓ Scoring complete: score={rounded_score:.2f}, "
        f"normalized={normalized_score:.2f}, quality={quality_level.value}"
    )

    return result

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
]
