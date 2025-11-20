# Aggregation Phase (Phases 4–7) – Canonical Contract

_Last updated: 2025-11-17_

This document is the single source of truth for the aggregation hierarchy. Any change to the code **must** be reflected here; all other aggregation notes are considered historical.

## 1. Hierarchy Overview

```
Micro questions (ScoredMicroQuestion) → Dimensions → Policy Areas → Clusters → Macro Evaluation
```

- Dimensions: `D1` … `D6`
- Policy Areas: `PA01` … `PA10`
- Clusters: `CL01` … `CL04`
- Macro layer: single holistic evaluation (`Q305`)

The taxonomy (IDs, counts, and membership) is read from the canonical questionnaire monolith and enforced through `AggregationSettings`.

## 2. Contracts per Phase

| Phase | Entry Point | Input | Output | Notes |
| --- | --- | --- | --- | --- |
| 4 – Dimension aggregation | `DimensionAggregator.run` | `List[ScoredMicroQuestion]` converted into `ScoredResult` objects | `List[DimensionScore]` (one per `(dimension_id, policy_area_id)` pair) | Requires `score`, `policy_area`, `dimension`, `base_slot` for every micro result. |
| 5 – Policy area aggregation | `AreaPolicyAggregator.run` | `List[DimensionScore]` | `List[AreaScore]` (one per policy area) | Validates hermeticity (no missing/duplicate dimensions), honors weights per area. |
| 6 – Cluster aggregation | `ClusterAggregator.run` | `List[AreaScore]` + cluster definitions from monolith | `List[ClusterScore]` (one per cluster) | Each item includes `coherence`, `variance`, and `weakest_area`. Hermeticity must match cluster definitions exactly. |
| 7 – Macro evaluation | `MacroAggregator.evaluate_macro` via `_evaluate_macro` | `List[ClusterScore]`, `List[AreaScore]`, `List[DimensionScore]` | `MacroScoreDict` (`macro_score`, `macro_score_normalized`, `cluster_scores`, `cross_cutting_coherence`, `systemic_gaps`, `strategic_alignment`, `quality_band`) | Quality band computed from rubric thresholds (defaults: 0.85 / 0.70 / 0.55). |

The orchestrator supplies the questionnaire monolith once per run; all aggregators receive an `AggregationSettings` instance derived from that monolith so they use the same group-by keys, expected counts, and weights.

## 3. Algorithms and Fallbacks

### DimensionAggregator
- Groups by `aggregation_settings.dimension_group_by_keys` (default `["policy_area", "dimension"]`).
- Validates coverage: expected counts come from monolith (number of micro questions per dimension/area pair) with a default of 5.
- Weights:
  - Uses canonical `dimension_question_weights` when provided; otherwise equal weights.
  - Rejects invalid weights (sum ≠ 1.0 or negative) and fails fast.
- Thresholds:
  - Quality levels derived from rubric (score normalized by `score_max = 3.0`).

### AreaPolicyAggregator
- Group-by defaults to `["area_id"]`.
- Ensures each area has the expected number of dimensions (from monolith).
- Optional weights per dimension (`policy_area_dimension_weights`); falls back to equal weights when any dimension weight is missing.
- Applies rubric thresholds identical to dimension level.

### ClusterAggregator
- Hydrates `AreaScore.cluster_id` using monolith cluster definitions before grouping (`aggregation_settings.cluster_group_by_keys`, default `["cluster_id"]`).
- Hermeticity checks:
  - No duplicate areas.
  - All expected areas present.
  - No unexpected areas.
- Weight resolution: `cluster_policy_area_weights` or equal weights.
- Metrics recorded for each cluster:
  - `coherence`: inverse standard deviation of member area scores.
  - `variance`: population variance of area scores.
  - `weakest_area`: ID of the lowest-scoring policy area.
- **Imbalance penalty:** after computing the weighted average, the score is multiplied by `1 - 0.3 * min(std_dev / 3.0, 1)`; this reduces up to 30 % of the score when dispersion reaches the maximum possible standard deviation (3.0). The raw score, penalty factor, and adjusted score are logged inside `validation_details["imbalance_penalty"]`.

### MacroAggregator
- Requires the four `ClusterScore` entries plus deduplicated `AreaScore` and `DimensionScore` inputs.
- Computes:
  - Cross-cutting coherence (inverse std dev across cluster scores).
  - Systemic gaps (areas with `quality_level == "INSUFICIENTE"`).
  - Strategic alignment (`0.6 * cluster_coherence + 0.4 * dimension_validation_rate`).
  - Macro score: weighted average of cluster scores (`macro_cluster_weights` or equal weights).
  - Quality band via rubric thresholds (EXCELENTE, BUENO, ACEPTABLE, INSUFICIENTE).
- `_evaluate_macro` returns a `MacroScoreDict` that exposes the MacroScore dataclass plus the derived metrics above.

## 4. Invariants & Validation Rules

1. **ID Taxonomy**
   - Dimensions `DIM01`…`DIM06`
   - Policy areas `PA01`…`PA10`
   - Clusters `CL01`…`CL04` with monolith-defined memberships.
2. **Counts**
   - Dimensions: 6 × 10 = 60 combinations expected.
   - Areas: 10.
   - Clusters: 4.
3. **Score Range**
   - All aggregation scores stay in `[0.0, 3.0]`.
4. **Weights**
   - Non-negative; normalized to 1.0 within tolerance `1e-6`.
5. **Coverage**
   - Missing micro questions trigger `CoverageError` (if `abort_on_insufficient=True`) or mark `validation_passed=False`.
6. **Monolith Integrity**
   - Aggregation never reads files directly. It consumes the in-memory monolith injected via orchestrator/config.
7. **Thread Safety & Determinism**
   - Aggregation is pure Python computation over provided lists; no async IO or global state.

## 5. Testing & Hardening Checklist

Before declaring the phase stable:

1. `python3 -m compileall src/saaaaaa/processing/aggregation.py src/saaaaaa/core/orchestrator/core.py`.
2. `python3 -m pytest tests/test_aggregation.py tests/test_macro_score_dict.py` (or full suite) – must report:
   - 60 `DimensionScore` entries in generated fixtures.
   - 10 `AreaScore` entries covering `PA01`…`PA10`.
   - 4 `ClusterScore` entries with `variance` and `weakest_area` populated.
   - `MacroScoreDict` instance containing `quality_band` consistent with rubric.
3. Review `AggregationSettings.from_monolith(...)` output to confirm IDs and weights match the canonical monolith hash.
4. Confirm no other files define `DimensionAggregator`, `AreaPolicyAggregator`, `ClusterAggregator`, `MacroAggregator`, `DimensionScore`, `AreaScore`, `ClusterScore`, `MacroScoreDict`.

Any deviation from these invariants must block release until resolved.
