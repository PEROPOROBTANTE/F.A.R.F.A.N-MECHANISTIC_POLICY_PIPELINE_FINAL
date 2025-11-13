# Macro Prompts - Strategic Analysis System

## Overview

This module implements 5 strategic macro-level analysis prompts designed to enhance the MACRO-level analysis in the SAAAAAA policy analysis system. These prompts provide comprehensive evaluation of:

1. **Coverage & Structural Gap Assessment**
2. **Inter-Level Contradiction Detection**
3. **Bayesian Portfolio Composition**
4. **Implementation Roadmap Optimization**
5. **Peer Normalization & Confidence Scaling**

## Architecture

```
macro_prompts.py
├── CoverageGapStressor          # Prompt 1: Coverage analysis
├── ContradictionScanner         # Prompt 2: Contradiction detection
├── BayesianPortfolioComposer   # Prompt 3: Bayesian integration
├── RoadmapOptimizer            # Prompt 4: Roadmap generation
├── PeerNormalizer              # Prompt 5: Peer comparison
└── MacroPromptsOrchestrator    # Unified orchestrator
```

## Integration with Report Assembly

The macro prompts are automatically invoked during `generate_macro_convergence()` in `report_assembly.py`. Results are included in the `MacroLevelConvergence.metadata["macro_prompts_results"]` field.

### Flow

```
ReportAssembler.generate_macro_convergence()
    ↓
    _apply_macro_prompts()
    ↓
    MacroPromptsOrchestrator.execute_all()
    ↓
    {
        coverage_analysis: {...},
        contradiction_report: {...},
        bayesian_portfolio: {...},
        implementation_roadmap: {...},
        peer_normalization: {...}
    }
```

## Prompt 1: Coverage & Structural Gap Stressor

**Role:** Structural Integrity Auditor [systems design]

**Goal:** Evaluate if absence of clusters or dimensions erodes macro score validity.

### Inputs
- `convergence_by_dimension`: Scores by dimension (D1-D6)
- `missing_clusters`: List of missing cluster names
- `dimension_coverage`: {D1..D6: % questions answered}
- `policy_area_coverage`: {P#: %}

### Mandates
1. Calculate `coverage_index` (weighted average)
2. If `dimension_coverage < τ` in critical dimensions (D3, D6) → degrade `global_confidence`
3. Simulate impact if missing clusters were completed (`predictive_uplift`)

### Output
```json
{
  "coverage_index": 0.85,
  "degraded_confidence": 0.78,
  "predictive_uplift": {
    "CLUSTER_X": 0.15,
    "D3_completion": 0.12
  },
  "dimension_coverage": {...},
  "policy_area_coverage": {...},
  "critical_dimensions_below_threshold": ["D3"]
}
```

### Usage
```python
from macro_prompts import CoverageGapStressor

stressor = CoverageGapStressor(
    critical_dimensions=["D3", "D6"],
    coverage_threshold=0.70
)

result = stressor.evaluate(
    convergence_by_dimension={"D1": 0.8, "D2": 0.75, ...},
    missing_clusters=["CLUSTER_X"],
    dimension_coverage={"D1": 0.9, "D2": 0.85, ...},
    policy_area_coverage={"P1": 0.8, "P2": 0.75, ...},
    baseline_confidence=1.0
)
```

## Prompt 2: Inter-Level Contradiction Scan

**Role:** Consistency Inspector [data governance]

**Goal:** Detect contradictions micro↔meso↔macro.

### Inputs
- `micro_claims`: Extracted from `MicroLevelAnswer.evidence`
- `meso_summary_signals`: Summary from meso clusters
- `macro_narratives`: Draft macro statements

### Mandates
1. Align claims by entity/theme/dimension
2. Flag contradiction if macro affirms X and ≥k micro deny X with posterior ≥ θ
3. Suggest correction: "rephrase / downgrade confidence / request re-execution"

### Output
```json
{
  "contradictions": [
    {
      "dimension": "D1",
      "type": "micro_macro_contradiction",
      "contradicting_claims": 5,
      "threshold": 3
    }
  ],
  "suggested_actions": [
    {
      "dimension": "D1",
      "action": "downgrade_confidence",
      "reason": "5 micro claims suggest lower confidence"
    }
  ],
  "consistency_score": 0.82,
  "micro_meso_alignment": 0.85,
  "meso_macro_alignment": 0.88
}
```

### Usage
```python
from macro_prompts import ContradictionScanner

scanner = ContradictionScanner(
    contradiction_threshold=3,
    posterior_threshold=0.7
)

result = scanner.scan(
    micro_claims=[...],
    meso_summary_signals={...},
    macro_narratives={...}
)
```

## Prompt 3: Bayesian Portfolio Composer

**Role:** Global Bayesian Integrator [causal inference]

**Goal:** Integrate all posteriors (micro and meso) into a global causal portfolio.

### Inputs
- `meso_posteriors`: Posterior probabilities by cluster
- `cluster_weights`: Weighting trace
- `reconciliation_penalties`: Coverage, dispersion, contradictions

### Mandates
1. Calculate `prior_global` (weighted meso average)
2. Apply hierarchical penalties (coverage, structural dispersion, contradictions)
3. Recalculate `posterior_global` and variance

### Output
```json
{
  "prior_global": 0.75,
  "penalties_applied": {
    "coverage": 0.1,
    "dispersion": 0.05,
    "contradictions": 0.08
  },
  "posterior_global": 0.68,
  "var_global": 0.04,
  "confidence_interval": [0.60, 0.76]
}
```

### Usage
```python
from macro_prompts import BayesianPortfolioComposer

composer = BayesianPortfolioComposer(default_variance=0.05)

result = composer.compose(
    meso_posteriors={"CL01": 0.8, "CL02": 0.75},
    cluster_weights={"CL01": 0.6, "CL02": 0.4},
    reconciliation_penalties={"coverage": 0.1, "dispersion": 0.05}
)
```

## Prompt 4: Roadmap Optimizer

**Role:** Execution Strategist [operations design]

**Goal:** Generate sequenced 0-3m / 3-6m / 6-12m roadmap prioritizing impact/cost.

### Inputs
- `critical_gaps`: List of gaps to address
- `dependency_graph`: {gap_id: [prerequisite_ids]}
- `effort_estimates`: {gap_id: person-months}
- `impact_scores`: {gap_id: 0.0-1.0}

### Mandates
1. Order by ratio `impact/effort` and dependencies
2. Assign to time window minimum without prerequisite collision
3. Estimate uplift expected per phase

### Output
```json
{
  "phases": [
    {
      "name": "0-3m",
      "actions": [...],
      "effort": 8.0,
      "max_effort": 9.0
    },
    ...
  ],
  "total_expected_uplift": 2.4,
  "critical_path": ["GAP_1", "GAP_2", "GAP_3"],
  "resource_requirements": {
    "0-3m": {
      "total_effort_months": 8.0,
      "recommended_team_size": 3,
      "num_actions": 4
    }
  }
}
```

### Usage
```python
from macro_prompts import RoadmapOptimizer

optimizer = RoadmapOptimizer()

result = optimizer.optimize(
    critical_gaps=[{"id": "GAP_1", "name": "..."}],
    dependency_graph={"GAP_1": [], "GAP_2": ["GAP_1"]},
    effort_estimates={"GAP_1": 2.0, "GAP_2": 3.0},
    impact_scores={"GAP_1": 0.9, "GAP_2": 0.8}
)
```

## Prompt 5: Peer Normalization & Confidence Scaling

**Role:** Macro Peer Evaluator [evaluation design]

**Goal:** Adjust macro classification considering regional comparatives.

### Inputs
- `convergence_by_policy_area`: Scores by policy area
- `peer_distributions`: {policy_area → {mean, std}}
- `baseline_confidence`: Starting confidence

### Mandates
1. Calculate z-scores
2. Penalize if >k areas are < -1.0 z
3. Increase confidence if all within ±0.5 z and low dispersion

### Output
```json
{
  "z_scores": {
    "P1": 0.5,
    "P2": -0.3,
    "P3": 1.2
  },
  "adjusted_confidence": 0.88,
  "peer_position": "above_average",
  "outlier_areas": ["P3"]
}
```

### Usage
```python
from macro_prompts import PeerNormalizer

normalizer = PeerNormalizer(
    penalty_threshold=3,
    outlier_z_threshold=2.0
)

result = normalizer.normalize(
    convergence_by_policy_area={"P1": 0.75, "P2": 0.78, ...},
    peer_distributions={
        "P1": {"mean": 0.75, "std": 0.1},
        "P2": {"mean": 0.75, "std": 0.1}
    },
    baseline_confidence=0.85
)
```

## Unified Orchestrator

For convenience, all 5 prompts can be executed together:

```python
from macro_prompts import MacroPromptsOrchestrator

orchestrator = MacroPromptsOrchestrator()

results = orchestrator.execute_all({
    "convergence_by_dimension": {...},
    "convergence_by_policy_area": {...},
    "missing_clusters": [...],
    "dimension_coverage": {...},
    "policy_area_coverage": {...},
    "micro_claims": [...],
    "meso_summary_signals": {...},
    "macro_narratives": {...},
    "meso_posteriors": {...},
    "cluster_weights": {...},
    "critical_gaps": [...],
    "dependency_graph": {...},
    "effort_estimates": {...},
    "impact_scores": {...},
    "peer_distributions": {...},
    "baseline_confidence": 0.85
})

# Results contain all 5 analyses
print(results["coverage_analysis"])
print(results["contradiction_report"])
print(results["bayesian_portfolio"])
print(results["implementation_roadmap"])
print(results["peer_normalization"])
```

## Testing

### Unit Tests
```bash
python3 -m unittest tests.test_macro_prompts -v
```

**Coverage:**
- 23 unit tests covering all 5 prompt macros
- Tests for initialization, basic functionality, edge cases
- Tests for data validation and error handling

### Integration Tests
```bash
python3 -m unittest tests.test_macro_prompts_integration -v
```

**Coverage:**
- 8 integration tests
- Tests for end-to-end flow with ReportAssembler
- Tests for data extraction and transformation
- Tests for all 5 prompts in real-world scenarios

### All Tests
```bash
python3 -m unittest tests.test_macro_prompts tests.test_macro_prompts_integration tests.test_report_assembly_producer -v
```

**Total:** 42 tests (all passing)

## Performance

- **Coverage Gap Stressor:** ~0.001s per analysis
- **Contradiction Scanner:** ~0.001s per analysis
- **Bayesian Portfolio Composer:** <0.001s per analysis
- **Roadmap Optimizer:** ~0.001s per analysis
- **Peer Normalizer:** <0.001s per analysis

**Total overhead:** ~0.005s added to macro convergence generation

## Data Structures

All 5 prompts return dataclasses that can be easily serialized:

```python
from dataclasses import asdict

coverage = stressor.evaluate(...)
json_result = asdict(coverage)  # Convert to dict for JSON serialization
```

## Error Handling

The integration with `report_assembly.py` is graceful:

- If `macro_prompts` module is not available, `ReportAssembler` continues without it
- Check `MACRO_PROMPTS_AVAILABLE` flag to verify availability
- Prompts results are optional in `MacroLevelConvergence.metadata`

## Future Enhancements

1. **Machine Learning Integration:** Use ML models for better uplift predictions
2. **Historical Peer Data:** Connect to database for real peer distributions
3. **Advanced Dependency Analysis:** Implement critical path method (CPM) for roadmap
4. **Semantic Contradiction Detection:** Use NLP for better contradiction scanning
5. **Adaptive Thresholds:** Learn optimal thresholds from historical data

## References

- **Report Assembly:** `report_assembly.py`
- **Test Suite:** `tests/test_macro_prompts.py`, `tests/test_macro_prompts_integration.py`
- **Main Documentation:** `README.md`

## Version

**Current Version:** 1.0.0

**Compatibility:** Python 3.10+

**Integration Version:** report_assembly.py v3.1.0

## Authors

Integration Team, 2025

## License

Same as parent project
