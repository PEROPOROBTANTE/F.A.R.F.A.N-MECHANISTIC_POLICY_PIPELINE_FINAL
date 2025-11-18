# DEPRECATION NOTICE: intrinsic_calibration.json

**Date**: 2025-11-18
**Status**: DEPRECATED - DO NOT USE
**Replacement**: Layer-based calibration system in `src/saaaaaa/core/calibration/`

---

## Why This File Is Deprecated

The `config/intrinsic_calibration.json` file represents an **INCORRECT** calibration approach that does NOT conform to the canonical specification in `canonic_calibration_methods.md`.

### Problems with This Approach

1. **Wrong Data Structure**:
   - Stores individual `b_theory`, `b_impl`, `b_deploy` scores per method
   - Does NOT use the 8-layer system (@b, @chain, @u, @q, @d, @p, @C, @m)
   - Missing role-based layer requirements

2. **No Choquet Fusion**:
   - Does NOT apply 2-additive Choquet aggregation
   - Missing interaction terms between layers
   - Violates Definition 5.1 from canonical specification

3. **Not Centralized**:
   - Each method has individual calibration entries
   - No role-based structure
   - Violates "NO CALIBRATION IN SCRIPTS" directive

4. **Wrong Module Usage**:
   - Used by `src/saaaaaa/core/orchestrator/calibration_registry.py`
   - `calibration_registry.py` also uses WRONG `MethodCalibration` dataclass
   - Should use `CalibrationOrchestrator` from `src/saaaaaa/core/calibration/`

---

## Correct Calibration System

### Location

```
src/saaaaaa/core/calibration/
├── __init__.py                  # Main exports
├── orchestrator.py              # CalibrationOrchestrator (MAIN ENTRY POINT)
├── choquet_aggregator.py        # 2-additive Choquet fusion
├── base_layer.py                # @b layer evaluator
├── unit_layer.py                # @u layer evaluator
├── chain_layer.py               # @chain layer evaluator
├── meta_layer.py                # @m layer evaluator
├── congruence_layer.py          # @C layer evaluator
├── compatibility.py             # @q, @d, @p layer evaluators
├── layer_requirements.py        # Role → Layer mapping
└── data_structures.py           # LayerID, CalibrationResult, etc.
```

### Configuration Files

```
config/fusion_specification.json      # Choquet weights per role
config/canonical_method_catalog.json  # Method metadata and roles
```

### Usage Example

```python
from saaaaaa.core.calibration import CalibrationOrchestrator, CalibrationSubject

# Initialize orchestrator
orchestrator = CalibrationOrchestrator(
    intrinsic_path="config/intrinsic_calibration.json",  # Still reads base scores
    parameter_path="config/method_parameters.json"
)

# Create calibration subject
subject = CalibrationSubject(
    method_id="src.module.Class.method",
    context=(Q, D, P, U),  # Question, Dimension, Policy, Unit quality
    role="META_TOOL"
)

# Calibrate (returns CalibrationResult with all layer scores + final Cal)
result = orchestrator.calibrate(subject)

print(f"Final Score: {result.final_score}")
print(f"Layer Scores: {result.layer_scores}")
```

### Correct Process

1. **Method** → **Triage** (3-question automaton from rubric)
   - If excluded → NO CALIBRATION
   - If required → Continue

2. **Determine Role** (Definition 4.1)
   - INGEST_PDM, STRUCTURE, EXTRACT, SCORE_Q, AGGREGATE, REPORT, META_TOOL, TRANSFORM

3. **Map Role → Layers** (Definition 4.2)
   - Example: META_TOOL → [@b, @chain, @m]

4. **Evaluate Each Layer** (Definitions 3.1-3.6)
   - @b: Intrinsic quality (b_theory, b_impl, b_deploy)
   - @chain: Chain compatibility
   - @m: Meta governance/observability
   - etc.

5. **Apply Choquet Fusion** (Definition 5.1)
   ```
   Cal(I) = Σ(a_ℓ · x_ℓ) + Σ(a_ℓk · min(x_ℓ, x_k))
   ```
   - Weights from `config/fusion_specification.json`

6. **Return CalibrationResult**
   - final_score: Final calibration score [0,1]
   - layer_scores: Dict[LayerID, float]
   - interaction_terms: Dict[tuple, float]

---

## Migration Path

### DO NOT USE

```python
# WRONG - DEPRECATED
from saaaaaa.core.orchestrator.calibration_registry import resolve_calibration

cal = resolve_calibration("ClassName", "method_name")
# Returns MethodCalibration (wrong structure)
```

### USE INSTEAD

```python
# CORRECT - Layer-based system
from saaaaaa.core.calibration import CalibrationOrchestrator

orchestrator = CalibrationOrchestrator()
result = orchestrator.calibrate(subject)
# Returns CalibrationResult with proper layer scores
```

---

## Status

- **intrinsic_calibration.json**: DEPRECATED (but still read for @b layer base scores)
- **calibration_registry.py**: DEPRECATED (use CalibrationOrchestrator instead)
- **Layer-based system**: ACTIVE AND CORRECT

---

## References

- **Canonical Specification**: `canonic_calibration_methods.md`
- **Fusion Weights**: `config/fusion_specification.json`
- **Rubric**: `config/intrinsic_calibration_rubric.json`
- **Method Catalog**: `config/canonical_method_catalog.json`

---

**DO NOT ADD NEW ENTRIES TO THIS FILE. USE THE LAYER-BASED CALIBRATION SYSTEM.**
