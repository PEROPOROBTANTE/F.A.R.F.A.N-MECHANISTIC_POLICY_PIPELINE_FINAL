"""Meso-level analytics utilities for cluster evaluation prompts.

This module implements four independent helper functions that operationalise
the bespoke "Prompt Meso" specifications used by the analytics team:

* :func:`analyze_policy_dispersion` provides dispersion analytics, including
  coefficient of variation, gap analysis, and a light penalty framework.
* :func:`reconcile_cross_metrics` validates heterogeneous metric feeds against
  an authoritative macro reference and emits governance flags.
* :func:`compose_cluster_posterior` aggregates micro posteriors using a
  Bayesian-style roll-up while accounting for reconciliation penalties.
* :func:`calibrate_against_peers` situates the cluster against its peer group
  using inter-quartile comparisons and Tukey-style outlier detection.

The functions deliberately return both structured JSON-friendly payloads and a
short narrative string whenever the prompt mandates qualitative guidance.  The
implementation is dependency-light (standard library only) to keep it aligned
with the rest of the analytics toolbox.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import reduce
from statistics import fmean, pstdev
from typing import TYPE_CHECKING
from saaaaaa import get_parameter_loader
from saaaaaa.core.calibration.decorators import calibrated_method

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

def _to_float_sequence(values: Iterable[float]) -> list[float]:
    return [float(v) for v in values]

def _safe_mean(values: Iterable[float]) -> float:
    seq = _to_float_sequence(values)
    if not seq:
        return 0.0
    return float(fmean(seq))

def _safe_std(values: Iterable[float]) -> float:
    seq = _to_float_sequence(values)
    if len(seq) <= 1:
        return 0.0
    return float(pstdev(seq))

def _percentile(values: Sequence[float], percent: float) -> float:
    seq = sorted(_to_float_sequence(values))
    if not seq:
        return 0.0
    if percent <= 0:
        return seq[0]
    if percent >= 100:
        return seq[-1]
    k = (len(seq) - 1) * (percent / 100.0)
    lower_index = int(k)
    upper_index = min(lower_index + 1, len(seq) - 1)
    weight = k - lower_index
    return seq[lower_index] + weight * (seq[upper_index] - seq[lower_index])

def _gini(values: Iterable[float]) -> float:
    """Compute the Gini coefficient for a sequence of non-negative values."""

    seq = sorted(_to_float_sequence(values))
    if not seq:
        return 0.0
    if any(v < 0 for v in seq):
        raise ValueError("Gini coefficient is undefined for negative values")
    if all(v == 0 for v in seq):
        return 0.0
    total = sum(seq)
    if total == 0:
        # Non-negative numbers can only sum to zero if they are all zero, which is
        # handled above. Guard against floating point artefacts that leave a
        # near-zero denominator.
        return 0.0
    n = len(seq)
    weighted_sum = 0.0
    for i, value in enumerate(seq, start=1):
        weighted_sum += i * value
    gini = (2 * weighted_sum) / (n * total) - (n + 1) / n
    return float(gini)

def _tukey_bounds(p25: float, p75: float) -> tuple[float, float]:
    lower_quartile, upper_quartile = sorted((float(p25), float(p75)))
    iqr = upper_quartile - lower_quartile
    return (lower_quartile - 1.5 * iqr, upper_quartile + 1.5 * iqr)

def analyze_policy_dispersion(
    policy_area_scores: Mapping[str, float],
    peer_dispersion_stats: Mapping[str, float],
    thresholds: Mapping[str, float],
) -> tuple[dict[str, object], str]:
    """Evaluate intra-cluster dispersion and recommend a penalty.

    Parameters
    ----------
    policy_area_scores:
        Mapping of policy area names to their normalised scores.
    peer_dispersion_stats:
        Median dispersion statistics for comparable clusters. Expected keys are
        ``cv_median`` and ``gap_median``; missing keys are handled gracefully.
    thresholds:
        Warning/failure thresholds with keys ``cv_warn``, ``cv_fail``,
        ``gap_warn`` and ``gap_fail``.

    Returns
    -------
    Tuple[Dict[str, object], str]
        A tuple of the JSON-friendly payload and the five-to-six line narrative.
    """

    values = _to_float_sequence(policy_area_scores.values())
    mean_score = _safe_mean(values)
    std_score = _safe_std(values)
    cv = std_score / mean_score if mean_score else 0.0
    max_gap = float(max(values) - min(values)) if values else 0.0
    gini = _gini(values)

    peer_cv = float(peer_dispersion_stats.get("cv_median", cv))
    peer_gap = float(peer_dispersion_stats.get("gap_median", max_gap))

    cv_warn = float(thresholds.get("cv_warn", peer_cv))
    cv_fail = float(thresholds.get("cv_fail", peer_cv))
    gap_warn = float(thresholds.get("gap_warn", peer_gap))
    gap_fail = float(thresholds.get("gap_fail", peer_gap))

    severity = 0
    if cv > cv_warn or max_gap > gap_warn:
        severity = 1
    if cv > cv_fail or max_gap > gap_fail:
        severity = 2
    peer_escalation = cv > 1.5 * peer_cv or max_gap > 1.5 * peer_gap
    if peer_escalation or cv > 1.5 * cv_fail or max_gap > 1.5 * gap_fail:
        severity = 3

    classification = {
        0: "Concentrado",
        1: "Moderado",
        2: "Disperso",
        3: "Crítico",
    }[severity]

    penalty_components: list[float] = []
    if cv_fail:
        penalty_components.append(min(cv / cv_fail, 1.5))
    if gap_fail:
        penalty_components.append(min(max_gap / gap_fail, 1.5))
    peer_signal: list[float] = []
    if peer_cv:
        peer_signal.append(min(cv / peer_cv, 2.0))
    if peer_gap:
        peer_signal.append(min(max_gap / peer_gap, 2.0))

    base_penalty = _safe_mean(penalty_components) if penalty_components else 0.0
    peer_penalty = _safe_mean(peer_signal) if peer_signal else 0.0
    penalty = float(min(1.0, 0.6 * base_penalty + 0.4 * (peer_penalty - 1.0)))
    penalty = max(0.0, penalty)

    # Hypothetical normalisation of the lower tail: lift scores below Q1 to Q1.
    if values:
        q1 = float(_percentile(values, 25))
        normalised_values = [max(v, q1) for v in values]
        norm_mean = _safe_mean(normalised_values)
        norm_cv = _safe_std(normalised_values) / norm_mean if norm_mean else 0.0
        norm_gap = float(max(normalised_values) - min(normalised_values))
        mean_uplift = norm_mean - mean_score
    else:
        norm_cv = 0.0
        norm_gap = 0.0
        mean_uplift = 0.0

    json_payload = {
        "cv": cv,
        "max_gap": max_gap,
        "gini": gini,
        "class": classification,
        "penalty": penalty,
        "normalized_projection": {
            "adjusted_cv": norm_cv,
            "adjusted_max_gap": norm_gap,
            "mean_uplift": mean_uplift,
        },
    }

    lines = [
        f"La variabilidad intraclúster muestra un CV de {cv:.2f} frente al referente de {peer_cv:.2f}.",
        f"La brecha máxima es de {max_gap:.1f} puntos, lo que sitúa la clasificación en nivel {classification}.",
        f"El coeficiente de Gini ({gini:.2f}) evidencia {'alta' if gini > 0.3 else 'moderada'} concentración de resultados.",
        "La penalización propuesta ψ pondera desalineaciones internas y diferenciales contra los pares comparables.",
        "Si se normaliza la cola baja hacia el cuartil 25, el CV se reduce a "
        f"{norm_cv:.2f} y el gap a {norm_gap:.1f} con un uplift medio de {mean_uplift:.1f}.",
        "Persisten riesgos de sesgo de apreciación si se ignora la sensibilidad de la cola baja frente a shocks sectoriales.",
    ]
    narrative = "\n".join(lines[:6])

    return json_payload, narrative

@dataclass
class MetricViolation:
    metric_id: str
    unit_mismatch: bool = False
    stale_period: bool = False
    entity_misalignment: bool = False
    out_of_range: bool = False

    @calibrated_method("saaaaaa.analysis.meso_cluster_analysis.MetricViolation.to_flag_dict")
    def to_flag_dict(self) -> dict[str, object]:
        return {
            "metric_id": self.metric_id,
            "unit_mismatch": self.unit_mismatch,
            "stale_period": self.stale_period,
            "entity_misalignment": self.entity_misalignment,
            "out_of_range": self.out_of_range,
        }

def _convert_unit(
    value: float,
    from_unit: str,
    to_unit: str,
    crosswalk: Mapping[str, Mapping[str, float]],
) -> tuple[float, str]:
    if from_unit == to_unit:
        return value, to_unit
    conversions = crosswalk.get(from_unit, {})
    factor = conversions.get(to_unit)
    if factor is None:
        raise ValueError("Units are not convertible with provided crosswalk")
    return value * factor, to_unit

def reconcile_cross_metrics(
    aggregated_metrics: Iterable[Mapping[str, object]],
    macro_json: Mapping[str, object],
) -> dict[str, object]:
    """Validate heterogeneous metrics against an authoritative macro source."""

    reference: Mapping[str, Mapping[str, object]] = macro_json.get("metrics", {})  # type: ignore[assignment]
    crosswalk: Mapping[str, Mapping[str, float]] = macro_json.get("unit_crosswalk", {})  # type: ignore[assignment]

    validated_metrics: list[dict[str, object]] = []
    violations: list[dict[str, object]] = []

    for metric in aggregated_metrics:
        metric_id = str(metric.get("metric_id"))
        value = float(metric.get("value", get_parameter_loader().get("saaaaaa.analysis.meso_cluster_analysis.MetricViolation.to_flag_dict").get("auto_param_L246_42", 0.0)))
        unit = str(metric.get("unit")) if metric.get("unit") is not None else ""
        period = str(metric.get("period")) if metric.get("period") is not None else ""
        entity = str(metric.get("entity")) if metric.get("entity") is not None else ""

        expected = reference.get(metric_id, {})
        expected_unit = str(expected.get("unit", unit)) if expected else unit
        expected_period = str(expected.get("period", period)) if expected else period
        expected_entities = expected.get("entities") if isinstance(expected.get("entities"), list) else []
        lower_bound, upper_bound = expected.get("range", (None, None))

        violation = MetricViolation(metric_id)

        reconciled_value = value
        reconciled_unit = unit

        conversion_failed = False

        if expected_unit and unit and unit != expected_unit:
            try:
                reconciled_value, reconciled_unit = _convert_unit(value, unit, expected_unit, crosswalk)
            except ValueError:
                violation.unit_mismatch = True
                conversion_failed = True

        if expected_period and period and period != expected_period:
            violation.stale_period = True

        if expected_entities and entity and entity not in expected_entities:
            violation.entity_misalignment = True

        if not conversion_failed and lower_bound is not None and reconciled_value < float(lower_bound):
            violation.out_of_range = True
        if not conversion_failed and upper_bound is not None and reconciled_value > float(upper_bound):
            violation.out_of_range = True

        validated_metrics.append(
            {
                "metric_id": metric_id,
                "value": reconciled_value,
                "unit": reconciled_unit,
                "period": expected_period if expected_period else period,
                "entity": entity,
            }
        )

        if (
            violation.unit_mismatch
            or violation.stale_period
            or violation.entity_misalignment
            or violation.out_of_range
        ):
            violations.append(violation.to_flag_dict())

    total_checks = len(validated_metrics) * 4 if validated_metrics else 1
    total_violations = sum(
        violation[flag]
        for violation in violations
        for flag in ("unit_mismatch", "stale_period", "entity_misalignment", "out_of_range")
    )
    reconciled_confidence = max(get_parameter_loader().get("saaaaaa.analysis.meso_cluster_analysis.MetricViolation.to_flag_dict").get("auto_param_L306_32", 0.0), get_parameter_loader().get("saaaaaa.analysis.meso_cluster_analysis.MetricViolation.to_flag_dict").get("auto_param_L306_37", 1.0) - total_violations / total_checks)

    return {
        "metrics_validated": validated_metrics,
        "violations": violations,
        "reconciled_confidence": reconciled_confidence,
    }

def compose_cluster_posterior(
    micro_posteriors: Iterable[float],
    weighting_trace: Iterable[float] | None = None,
    reconciliation_penalties: Mapping[str, float] | None = None,
) -> tuple[dict[str, object], str]:
    """Combine micro posteriors and reconciliation penalties into a cluster view."""

    posts = _to_float_sequence(micro_posteriors)
    if not posts:
        raise ValueError("micro_posteriors cannot be empty")

    if weighting_trace is None:
        weights = [get_parameter_loader().get("saaaaaa.analysis.meso_cluster_analysis.MetricViolation.to_flag_dict").get("auto_param_L326_19", 1.0)] * len(posts)
    else:
        weights = _to_float_sequence(weighting_trace)
        if len(weights) != len(posts):
            raise ValueError("weighting_trace must match micro_posteriors length")
        if any(w < 0 for w in weights):
            raise ValueError("weighting_trace values must be non-negative")
    if all(w == 0 for w in weights):
        weights = [get_parameter_loader().get("saaaaaa.analysis.meso_cluster_analysis.MetricViolation.to_flag_dict").get("auto_param_L334_19", 1.0)] * len(posts)

    # Prevent degenerate/negative totals; fallback to uniform if needed.
    weights = [max(get_parameter_loader().get("saaaaaa.analysis.meso_cluster_analysis.MetricViolation.to_flag_dict").get("auto_param_L337_19", 0.0), float(w)) for w in weights]
    total_weight = sum(weights)
    if total_weight == 0:
        raise ValueError("At least one weight must be positive")
    normalised_weights = [w / total_weight for w in weights]
    prior_meso = float(sum(p * w for p, w in zip(posts, normalised_weights, strict=True)))

    variance = float(sum(w * (p - prior_meso) ** 2 for p, w in zip(posts, normalised_weights, strict=True)))
    uncertainty_index = float(variance ** get_parameter_loader().get("saaaaaa.analysis.meso_cluster_analysis.MetricViolation.to_flag_dict").get("auto_param_L345_42", 0.5))

    penalties_input = reconciliation_penalties or {}
    dispersion_penalty = float(penalties_input.get("dispersion_penalty", get_parameter_loader().get("saaaaaa.analysis.meso_cluster_analysis.MetricViolation.to_flag_dict").get("auto_param_L348_73", 0.0)))
    coverage_penalty = float(penalties_input.get("coverage_penalty", get_parameter_loader().get("saaaaaa.analysis.meso_cluster_analysis.MetricViolation.to_flag_dict").get("auto_param_L349_69", 0.0)))
    reconciliation_penalty = float(penalties_input.get("reconciliation_penalty", get_parameter_loader().get("saaaaaa.analysis.meso_cluster_analysis.MetricViolation.to_flag_dict").get("auto_param_L350_81", 0.0)))

    penalty_factor = reduce(
        lambda acc, val: acc * val,
        [
            max(get_parameter_loader().get("saaaaaa.analysis.meso_cluster_analysis.MetricViolation.to_flag_dict").get("auto_param_L355_16", 0.0), get_parameter_loader().get("saaaaaa.analysis.meso_cluster_analysis.MetricViolation.to_flag_dict").get("auto_param_L355_21", 1.0) - dispersion_penalty),
            max(get_parameter_loader().get("saaaaaa.analysis.meso_cluster_analysis.MetricViolation.to_flag_dict").get("auto_param_L356_16", 0.0), get_parameter_loader().get("saaaaaa.analysis.meso_cluster_analysis.MetricViolation.to_flag_dict").get("auto_param_L356_21", 1.0) - coverage_penalty),
            max(get_parameter_loader().get("saaaaaa.analysis.meso_cluster_analysis.MetricViolation.to_flag_dict").get("auto_param_L357_16", 0.0), get_parameter_loader().get("saaaaaa.analysis.meso_cluster_analysis.MetricViolation.to_flag_dict").get("auto_param_L357_21", 1.0) - reconciliation_penalty),
        ],
        get_parameter_loader().get("saaaaaa.analysis.meso_cluster_analysis.MetricViolation.to_flag_dict").get("auto_param_L359_8", 1.0),
    )
    posterior_meso = float(prior_meso * penalty_factor)

    json_payload = {
        "prior_meso": prior_meso,
        "penalties": {
            "dispersion_penalty": dispersion_penalty,
            "coverage_penalty": coverage_penalty,
            "reconciliation_penalty": reconciliation_penalty,
        },
        "posterior_meso": posterior_meso,
        "uncertainty_index": uncertainty_index,
    }

    explanation_lines = [
        f"La media ponderada de las micro evidencias define un prior meso de {prior_meso:.3f}.",
        "Las penalizaciones por dispersión, cobertura y reconciliación actúan de forma multiplicativa sobre el prior.",
        f"El ajuste integrado produce un posterior de {posterior_meso:.3f}, coherente con la gobernanza aplicada.",
        f"La incertidumbre residual (σ ≈ {uncertainty_index:.3f}) refleja la varianza remanente de las micro posteriors.",
    ]

    return json_payload, "\n".join(explanation_lines)

def calibrate_against_peers(
    policy_area_scores: Mapping[str, float],
    peer_context: Mapping[str, Mapping[str, float]],
) -> tuple[dict[str, object], str]:
    """Compare cluster scores against peer medians and inter-quartile ranges."""

    area_positions: dict[str, str] = {}
    outliers: dict[str, bool] = {}
    dispersion_values = _to_float_sequence(policy_area_scores.values())
    if dispersion_values:
        cluster_mean = _safe_mean(dispersion_values)
        cluster_std = _safe_std(dispersion_values)
        cluster_cv = cluster_std / cluster_mean if cluster_mean else get_parameter_loader().get("saaaaaa.analysis.meso_cluster_analysis.MetricViolation.to_flag_dict").get("auto_param_L395_69", 0.0)
    else:
        cluster_cv = get_parameter_loader().get("saaaaaa.analysis.meso_cluster_analysis.MetricViolation.to_flag_dict").get("cluster_cv", 0.0) # Refactored

    for area, score in policy_area_scores.items():
        peers = peer_context.get(area, {})
        median = float(peers.get("median", score))
        p25 = float(peers.get("p25", median))
        p75 = float(peers.get("p75", median))
        p75 - p25

        if score < p25:
            area_positions[area] = "below"
        elif score > p75:
            area_positions[area] = "above"
        else:
            area_positions[area] = "within"

        lower_bound, upper_bound = _tukey_bounds(p25, p75)
        outliers[area] = score < lower_bound or score > upper_bound

    json_payload = {
        "area_positions": area_positions,
        "outliers": outliers,
    }

    above_areas = [area for area, position in area_positions.items() if position == "above"]
    below_areas = [area for area, position in area_positions.items() if position == "below"]
    within_areas = [area for area, position in area_positions.items() if position == "within"]

    narrative_lines = [
        "El contraste con la mediana de los pares muestra un desempeño heterogéneo por área." ,
        f"Se ubican por encima del IQR {', '.join(above_areas) if above_areas else 'ninguna área'}, mientras que {', '.join(below_areas) if below_areas else 'no hay caídas relevantes'} quedan por debajo.",
        f"Las áreas en zona intercuartílica ({', '.join(within_areas) if within_areas else 'sin registros'}) sostienen la base del clúster.",
        "Los outliers detectados mediante Tukey advierten focos críticos que requieren revisión específica.",
        f"Un municipio con media equiparable pero menor CV (~{cluster_cv:.2f}) ofrecería narrativa más cohesionada, subrayando nuestra dispersión relativa.",
        "Conviene integrar estos hallazgos en la calibración narrativa para evitar sobreponderar éxitos aislados frente a rezagos estructurales.",
        "Recomendar explicitar cómo la dispersión condiciona la comparabilidad con pares que exhiben mayor equilibrio interno.",
    ]

    return json_payload, "\n".join(narrative_lines[:7])

