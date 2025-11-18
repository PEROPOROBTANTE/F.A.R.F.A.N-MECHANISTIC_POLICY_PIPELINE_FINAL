# FASE 5.2: Detailed Migration Plan

## Summary

Total hardcoded values found: **579**
- Type A (Scores): 2
- Type B (Thresholds): 81
- Type C (Weights): 8
- Type D (Constants): 388
- Uncategorized: 100

## Critical Findings

### 🚨 URGENT: Weight Inconsistency Detected

**Two different sets of weights found:**

1. **base_layer.py** (lines 36-38):
   ```python
   THEORY_WEIGHT = 0.4
   IMPL_WEIGHT = 0.4
   DEPLOY_WEIGHT = 0.2
   ```
   Sum: 1.0 ✓

2. **intrinsic_loader.py** (lines 53-55):
   ```python
   DEFAULT_W_THEORY = 0.4
   DEFAULT_W_IMPL = 0.35
   DEFAULT_W_DEPLOY = 0.25
   ```
   Sum: 1.0 ✓

**Problem**: Two different weight sets for the same computation (b_theory + b_impl + b_deploy)!

**Resolution**:
- Investigate which is correct
- Unify to single source of truth
- Migrate to `config/calibration_config.py` under `_base_weights`

---

## Type C: Weights - TO MIGRATE

### Real Weights (6 values)

| File | Line | Variable | Value | Destination |
|------|------|----------|-------|-------------|
| `base_layer.py` | 36 | THEORY_WEIGHT | 0.4 | `calibration_config.py:_base_weights:w_th` |
| `base_layer.py` | 37 | IMPL_WEIGHT | 0.4 | `calibration_config.py:_base_weights:w_imp` |
| `base_layer.py` | 38 | DEPLOY_WEIGHT | 0.2 | `calibration_config.py:_base_weights:w_dep` |
| `intrinsic_loader.py` | 53 | DEFAULT_W_THEORY | 0.4 | Remove (use config) |
| `intrinsic_loader.py` | 54 | DEFAULT_W_IMPL | 0.35 | Remove (use config) |
| `intrinsic_loader.py` | 55 | DEFAULT_W_DEPLOY | 0.25 | Remove (use config) |

**Action Plan:**
1. Investigate which weight set is currently used in production
2. Update `config/calibration_config.py` with correct weights
3. Remove hardcoded weights from both files
4. Update classes to load from config

### False Positives (2 values - NOT weights)

| File | Line | Variable | Category | Action |
|------|------|----------|----------|--------|
| `unit_layer.py` | 206 | total_weight | Type D | Keep (initialization) |
| `unit_layer.py` | 207 | weighted_score | Type D | Keep (initialization) |

---

## Type B: Thresholds - TO MIGRATE

### High Priority Thresholds (11 identified)

| File | Line | Value | Context | Destination |
|------|------|-------|---------|-------------|
| `base_layer.py` | 182 | 0.80 | Quality level "excellent" | `method_parameters.json:quality_levels:excellent` |
| `base_layer.py` | 184 | 0.60 | Quality level "good" | `method_parameters.json:quality_levels:good` |
| `base_layer.py` | 186 | 0.40 | Quality level "acceptable" | `method_parameters.json:quality_levels:acceptable` |
| `compatibility.py` | 264 | 1.00 | Full compatibility | `method_parameters.json:compatibility_levels:full` |
| `compatibility.py` | 266 | 0.70 | High compatibility | `method_parameters.json:compatibility_levels:high` |
| `compatibility.py` | 268 | 0.30 | Low compatibility | `method_parameters.json:compatibility_levels:low` |
| `compatibility.py` | 300 | 1.00 | Dimension full compat | (duplicate) |
| `compatibility.py` | 302 | 0.70 | Dimension high compat | (duplicate) |
| `compatibility.py` | 304 | 0.30 | Dimension low compat | (duplicate) |
| `chain_layer.py` | 108 | 0.50 | Partial coverage threshold | `method_parameters.json:chain_layer:partial_coverage` |
| `validator.py` | multiple | various | Validation thresholds | Already in method_parameters.json? |

### Technical Comparisons (70+ values - KEEP)

Many threshold comparisons are technical (e.g., `> 0.0` checks for positive values, `< 1e-6` for near-zero). These should NOT be migrated as they are functional requirements, not configurable parameters.

**Action Plan:**
1. Manually review each threshold comparison
2. Migrate only **business logic thresholds** (quality levels, validation cutoffs)
3. Keep **technical comparisons** (epsilon checks, boundary validations)

---

## Type A: Scores - NO MIGRATION NEEDED

Both "scores" found are initialization to 0.0:

| File | Line | Variable | Context | Action |
|------|------|----------|---------|--------|
| `unit_layer.py` | 214 | score | Initialization | Keep |
| `unit_layer.py` | 265 | total_struct_score | Initialization | Keep |

**Conclusion**: No actual scores hardcoded. All scores correctly loaded from `intrinsic_calibration.json` ✅

---

## Type D: Constants - SELECTIVE MIGRATION

388 constants found, mostly:
- Initialization values (0.0, 1.0)
- Boundary checks (0.0, 1.0)
- Technical epsilons (1e-6)

**Action**: Review sample to identify any that should be configurable parameters.

### Candidates for Migration

TBD after manual review of `Uncategorized` section.

---

## Uncategorized: 100 Values - MANUAL REVIEW REQUIRED

These values need manual categorization:
- Values between 0.2-0.5 (could be weights or thresholds)
- Context-specific constants
- Functional parameters

**Action**: Review JSON file and categorize each.

---

## Migration Priority

### Phase 5.3-5.5 Priority Order

1. **CRITICAL**: Resolve weight inconsistency
2. **HIGH**: Migrate weights (Type C)
3. **HIGH**: Migrate quality level thresholds (Type B)
4. **MEDIUM**: Migrate compatibility thresholds (Type B)
5. **LOW**: Review uncategorized for additional migrations

---

## Expected Outcomes

### After Migration

1. **Zero hardcoded weights**: All in `calibration_config.py`
2. **Zero hardcoded quality thresholds**: All in `method_parameters.json`
3. **Zero hardcoded validation thresholds**: All in `method_parameters.json`
4. **Behavior unchanged**: Regression tests pass
5. **Single source of truth**: No conflicts or duplicates

---

## Risks

1. **Weight inconsistency**: Must resolve before migration
2. **Threshold semantics**: Some may be technical, not business logic
3. **Test coverage**: Need comprehensive regression tests
4. **Breaking changes**: Classes must be updated to load from config

---

## Next Steps

1. ✅ Complete Phase 5.1 (scan complete)
2. ⏳ **Current**: Phase 5.2 - Manual review of weights inconsistency
3. 🔜 Phase 5.3 - Migrate weights
4. 🔜 Phase 5.4 - Migrate thresholds
5. 🔜 Phase 5.5 - Update config
6. 🔜 Phase 5.6 - Regression tests
