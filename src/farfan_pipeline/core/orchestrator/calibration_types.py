"""Calibration Types Module.

Defines core data structures for method calibration including intrinsic scores
and layer-based runtime evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MethodCalibration:
    """Calibration parameters for a method.

    Attributes:
        score_min: Minimum acceptable score
        score_max: Maximum acceptable score
        min_evidence_snippets: Minimum evidence snippets required
        max_evidence_snippets: Maximum evidence snippets to consider
        contradiction_tolerance: Tolerance for contradictions (0.0-1.0)
        uncertainty_penalty: Penalty for uncertainty (0.0-1.0)
        aggregation_weight: Weight in aggregation
        sensitivity: Sensitivity parameter (0.0-1.0)
        requires_numeric_support: Whether numeric support is required
        requires_temporal_support: Whether temporal support is required
        requires_source_provenance: Whether source provenance is required
    """
    score_min: float = 0.0
    score_max: float = 1.0
    min_evidence_snippets: int = 1
    max_evidence_snippets: int = 10
    contradiction_tolerance: float = 0.3
    uncertainty_penalty: float = 0.5
    aggregation_weight: float = 1.0
    sensitivity: float = 0.5
    requires_numeric_support: bool = False
    requires_temporal_support: bool = False
    requires_source_provenance: bool = True


@dataclass(frozen=True)
class IntrinsicScores:
    """Intrinsic calibration scores (@b) for a method.

    Attributes:
        b_theory: Theoretical soundness score (0.0-1.0)
        b_impl: Implementation quality score (0.0-1.0)
        b_deploy: Deployment readiness score (0.0-1.0)
    """
    b_theory: float
    b_impl: float
    b_deploy: float

    def average(self) -> float:
        """Compute average intrinsic score."""
        return (self.b_theory + self.b_impl + self.b_deploy) / 3.0


@dataclass(frozen=True)
class RuntimeLayers:
    """Runtime calibration layers for dynamic evaluation.

    Attributes:
        chain: Chain of evidence score (@chain)
        quality: Quality of data/evidence (@q)
        density: Data density score (@d)
        provenance: Provenance traceability (@p)
        coverage: Coverage completeness (@C)
        uncertainty: Uncertainty quantification (@u)
        mechanism: Mechanistic explanation (@m)
    """
    chain: float = 0.0
    quality: float = 0.0
    density: float = 0.0
    provenance: float = 0.0
    coverage: float = 0.0
    uncertainty: float = 0.0
    mechanism: float = 0.0

    def to_dict(self) -> dict[str, float]:
        """Convert to dictionary for logging."""
        return {
            'chain': self.chain,
            'quality': self.quality,
            'density': self.density,
            'provenance': self.provenance,
            'coverage': self.coverage,
            'uncertainty': self.uncertainty,
            'mechanism': self.mechanism
        }


@dataclass
class LayerRequirements:
    """Layer requirements from canonical inventory.

    Attributes:
        required_layers: List of required layer names
        weights: Dictionary mapping layer names to weights
        aggregation_method: 'choquet_integral' or 'weighted_sum'
    """
    required_layers: list[str]
    weights: dict[str, float]
    aggregation_method: str = 'weighted_sum'

    def validate(self) -> None:
        """Validate layer requirements."""
        if not self.required_layers:
            raise ValueError("No required layers specified")
        if self.aggregation_method not in ('choquet_integral', 'weighted_sum'):
            raise ValueError(f"Invalid aggregation method: {self.aggregation_method}")
        for layer in self.required_layers:
            if layer not in self.weights:
                raise ValueError(f"Missing weight for required layer: {layer}")


__all__ = [
    'MethodCalibration',
    'IntrinsicScores',
    'RuntimeLayers',
    'LayerRequirements'
]
