# CALIBRATION SYSTEM ZERO TOLERANCE AUDIT REPORT

**Date:** 2025-11-26
**Branch:** `claude/fake-real-executor-migration-01DkQrq2dtSN3scUvzNVKqGy`
**Phase:** Phase 2 - Folder Restructuring & Integration
**Auditor:** Claude Code Agent

---

## EXECUTIVE SUMMARY

### Verdict: ❌ **FAILING** - Multiple ZERO TOLERANCE violations detected

The existing calibration system has good foundations but **VIOLATES** the user's explicit ZERO TOLERANCE requirements in **10 critical areas**. The system allows parallel instances, has hardcoded values scattered in code, and lacks enforcement mechanisms.

**User's Explicit Requirement:**
> "ZERO TOLERANCE policy for: hardcoded calibration values, parallel systems, any shortcuts or approximations"

---

## 🚨 CRITICAL VIOLATIONS (ZERO TOLERANCE)

### 1. ❌ **CalibrationOrchestrator is NOT a Singleton**

**Location:** `src/saaaaaa/core/calibration/orchestrator.py:50-77`

**Violation:**
```python
class CalibrationOrchestrator:
    def __init__(self, config=None, ...):  # Can instantiate multiple times
        self.config = config or DEFAULT_CALIBRATION_CONFIG
        # ... initialization
```

**Evidence:**
- Regular class definition (line 50)
- No singleton pattern enforcement
- Can create unlimited instances: `orch1 = CalibrationOrchestrator()`, `orch2 = CalibrationOrchestrator()`

**Impact:**
- Violates "only 1 CalibrationOrchestrator" requirement
- Breaks single source of truth principle
- Multiple instances can load different configs → non-determinism

**Required Fix:**
- Implement thread-safe singleton pattern with `_instance` class variable
- Prevent direct instantiation via `__new__`
- Provide `get_instance()` class method

---

### 2. ❌ **IntrinsicScoreLoader is NOT a Singleton**

**Location:** `src/saaaaaa/core/calibration/intrinsic_loader.py:24-83`

**Violation:**
```python
class IntrinsicScoreLoader:
    def __init__(self, calibration_path: Path | str = "config/intrinsic_calibration.json"):
        # Can instantiate multiple times
        self.calibration_path = Path(calibration_path)
        # ...
```

**Evidence:**
- Uses lazy loading pattern but NOT a singleton
- Multiple instances can load from different files
- No prevention of parallel instantiation

**Impact:**
- Violates "only 1 IntrinsicCalibrationLoader" requirement
- Different parts of code could load different calibration files
- Memory waste (JSON loaded multiple times)

**Required Fix:**
- Same singleton pattern as CalibrationOrchestrator
- Enforce single instance system-wide

---

### 3. ❌ **MethodParameterLoader is NOT a Singleton**

**Location:** `src/saaaaaa/core/calibration/parameter_loader.py:22-65`

**Violation:**
```python
class MethodParameterLoader:
    def __init__(self, parameters_path: Path | str = "config/method_parameters.json"):
        # Can instantiate multiple times
        self.parameters_path = Path(parameters_path)
        # ...
```

**Evidence:**
- Same issue as IntrinsicScoreLoader
- No singleton enforcement

**Impact:**
- Violates "only 1 ParameterLoader" requirement
- Parallel parameter systems possible

**Required Fix:**
- Implement singleton pattern

---

### 4. ❌ **Hardcoded Choquet Aggregation Weights in Code**

**Location:** `src/saaaaaa/core/calibration/config.py:306-326`

**Violation:**
```python
linear_weights: dict[str, float] = field(default_factory=lambda: {
    "b": 0.122951,      # HARDCODED IN CODE
    "u": 0.098361,      # HARDCODED IN CODE
    "q": 0.081967,      # HARDCODED IN CODE
    "d": 0.065574,      # HARDCODED IN CODE
    "p": 0.049180,      # HARDCODED IN CODE
    "C": 0.081967,      # HARDCODED IN CODE
    "chain": 0.065574,  # HARDCODED IN CODE
    "m": 0.034426,      # HARDCODED IN CODE
})

interaction_weights: dict[tuple[str, str], float] = field(default_factory=lambda: {
    ("u", "chain"): 0.15,   # HARDCODED IN CODE
    ("chain", "C"): 0.12,   # HARDCODED IN CODE
    ("q", "d"): 0.08,       # HARDCODED IN CODE
    ("d", "p"): 0.05,       # HARDCODED IN CODE
})
```

**Evidence:**
- Weights embedded directly in Python code
- NOT loaded from `config/calibration_config.json` or similar
- Violates "all values from JSON files" requirement

**Impact:**
- Cannot modify Choquet weights without code changes
- No audit trail for weight changes
- Violates zero hardcoded values policy

**Required Fix:**
- Create `config/choquet_weights.json`
- Load weights from JSON
- Keep only default fallbacks in code

---

### 5. ❌ **Hardcoded UNCALIBRATED_PENALTY Value**

**Location:** `src/saaaaaa/core/calibration/base_layer.py:45`

**Violation:**
```python
# Penalty score for methods without calibration data
UNCALIBRATED_PENALTY = 0.1  # HARDCODED
```

**Evidence:**
- Class constant hardcoded to 0.1
- Used in line 220 when method not found
- No way to configure without code change

**Impact:**
- Violates zero hardcoded values policy
- Cannot adjust penalty without editing code

**Required Fix:**
- Load from `config/calibration_config.json` under `penalties.uncalibrated`
- Keep as configurable parameter

---

### 6. ❌ **Hardcoded Quality Thresholds in Base Layer**

**Location:** `src/saaaaaa/core/calibration/base_layer.py:40-42`

**Violation:**
```python
# Default quality thresholds (used if not in config)
DEFAULT_EXCELLENT_THRESHOLD = 0.8   # HARDCODED
DEFAULT_GOOD_THRESHOLD = 0.6        # HARDCODED
DEFAULT_ACCEPTABLE_THRESHOLD = 0.4  # HARDCODED
```

**Evidence:**
- Class constants with hardcoded values
- "Default" suggests these might be used frequently
- Lines 244-251 use these for quality classification

**Impact:**
- Cannot adjust quality bands without code changes
- Violates zero hardcoded values policy

**Required Fix:**
- Load from `config/calibration_config.json` under `quality_thresholds.base_layer`
- Remove class constants

---

### 7. ❌ **Hardcoded Penalty Scores in Orchestrator**

**Location:** `src/saaaaaa/core/calibration/orchestrator.py:302-382`

**Violation:**
```python
# Line 302-307: Hardcoded penalty 0.1 for missing base evaluator
layer_scores[LayerID.BASE] = LayerScore(
    layer=LayerID.BASE,
    score=BaseLayerEvaluator.UNCALIBRATED_PENALTY,  # Reference to hardcoded value
    rationale="BASE layer: intrinsic calibration not available (penalty applied)",
    metadata={"penalty": True, "reason": "no_calibration_file"}
)

# Lines 362-382: Hardcoded penalty 0.1 for missing contextual data
layer_scores[LayerID.QUESTION] = LayerScore(
    layer=LayerID.QUESTION,
    score=0.1,  # HARDCODED
    rationale="No compatibility data - penalty applied",
    metadata={"penalty": True}
)
# ... repeated for DIMENSION and POLICY with same 0.1 value
```

**Evidence:**
- Multiple hardcoded 0.1 penalty scores
- Same penalty for different failure scenarios
- No centralized configuration

**Impact:**
- Duplicate hardcoded values across codebase
- Cannot configure penalties independently
- Violates DRY and zero hardcoded values

**Required Fix:**
- Centralize all penalty values in `config/calibration_config.json`
- Load via singleton ConfigLoader

---

### 8. ❌ **Hardcoded Weights and Thresholds in UnitLayerConfig**

**Location:** `src/saaaaaa/core/calibration/config.py:39-145`

**Violation:**
```python
@dataclass(frozen=True)
class UnitLayerConfig:
    w_S: float = 0.25  # HARDCODED weight
    w_M: float = 0.25  # HARDCODED weight
    w_I: float = 0.25  # HARDCODED weight
    w_P: float = 0.25  # HARDCODED weight

    # ... 100+ more hardcoded parameters

    max_placeholder_ratio: float = 0.10  # HARDCODED threshold
    min_unique_values_ratio: float = 0.5  # HARDCODED threshold
    # ... many more
```

**Evidence:**
- Dataclass with 50+ hardcoded default values
- Weights, thresholds, minimums all in code
- Line 191: `from_env()` method exists but not used

**Impact:**
- All unit layer parameters hardcoded
- Cannot configure without code changes
- Violates zero hardcoded values policy

**Required Fix:**
- Create `config/unit_layer_config.json`
- Load all parameters from JSON
- Keep dataclass for validation only

---

### 9. ❌ **Missing @calibrated_method Decorator**

**Location:** Nowhere - decorator doesn't exist

**Violation:**
- User explicitly requested: "Implement `@calibrated_method` decorator"
- No decorator found in codebase
- No enforcement mechanism for calibration

**Evidence:**
```bash
$ grep -r "@calibrated_method" src/
# No results
```

**Impact:**
- Methods can be executed without calibration
- No compile-time enforcement of calibration policy
- Cannot track which methods use calibration

**Required Fix:**
- Implement decorator in `src/saaaaaa/core/calibration/decorators.py`
- Decorator should:
  - Check method exists in calibration system
  - Enforce minimum quality threshold
  - Log calibration scores
  - Raise exception if calibration fails

---

### 10. ❌ **Missing Verification Scripts**

**Location:** Nowhere - scripts don't exist

**Violation:**
- User requested: "Create verification scripts to detect unanchored methods"
- User requested: "Run test_no_parallel_systems()"
- No scripts found to enforce ZERO TOLERANCE

**Evidence:**
```bash
$ find scripts/ -name "*verify*" -o -name "*detect*" -o -name "*parallel*"
# No results
```

**Impact:**
- No automated enforcement of zero tolerance policy
- Cannot detect violations at CI/CD time
- Manual verification required

**Required Fix:**
- Create `scripts/verify_no_hardcoded_calibrations.py`
- Create `scripts/verify_singleton_enforcement.py`
- Create `tests/test_no_parallel_systems.py`
- Integrate into CI/CD pipeline

---

## ✅ COMPLIANT AREAS (Good Practices Found)

### 1. ✅ **Lazy Loading with Thread Safety**

**Location:** `intrinsic_loader.py:84-169`, `parameter_loader.py:67-121`

**Good Practice:**
- Double-checked locking pattern
- Thread-safe initialization
- Lazy loading for performance

### 2. ✅ **Loading from JSON Files**

**Location:** `intrinsic_loader.py:112-145`, `base_layer.py:101-190`

**Good Practice:**
- Calibration scores loaded from `intrinsic_calibration.json`
- Parameters loaded from `method_parameters.json`
- Weights loaded from JSON `_base_weights` section

### 3. ✅ **Frozen Dataclasses for Immutability**

**Location:** `config.py:20, 224, 280, 383`

**Good Practice:**
- All config classes frozen (`frozen=True`)
- Prevents accidental mutation
- Hashable for caching

### 4. ✅ **Validation in __post_init__**

**Location:** `config.py:147-189, 271-277, 338-363`

**Good Practice:**
- Mathematical constraints enforced
- Weights sum to 1.0 checked
- Thresholds bounded to [0, 1]

### 5. ✅ **Comprehensive Logging**

**Location:** Throughout all modules

**Good Practice:**
- Structured logging with `logger.info/warning/debug`
- Extra context included
- Audit trail friendly

---

## 📊 VIOLATION SEVERITY MATRIX

| # | Violation | Severity | Fix Effort | Blocks Phase | Priority |
|---|-----------|----------|-----------|---------------|----------|
| 1 | CalibrationOrchestrator not singleton | CRITICAL | Medium | Phase 5 | P0 |
| 2 | IntrinsicScoreLoader not singleton | CRITICAL | Medium | Phase 5 | P0 |
| 3 | MethodParameterLoader not singleton | CRITICAL | Medium | Phase 5 | P0 |
| 4 | Hardcoded Choquet weights | CRITICAL | High | Phase 4 | P0 |
| 5 | Hardcoded UNCALIBRATED_PENALTY | HIGH | Low | Phase 4 | P1 |
| 6 | Hardcoded quality thresholds | HIGH | Low | Phase 4 | P1 |
| 7 | Hardcoded penalty scores in orchestrator | HIGH | Medium | Phase 4 | P1 |
| 8 | Hardcoded UnitLayerConfig parameters | CRITICAL | High | Phase 4 | P0 |
| 9 | Missing @calibrated_method decorator | CRITICAL | Medium | Phase 4 | P0 |
| 10 | Missing verification scripts | HIGH | Medium | Phase 5 | P1 |

---

## 🔧 REQUIRED FIXES SUMMARY

### Immediate Actions (P0 - Blocking)

1. **Implement Singleton Pattern** for all 3 loaders/orchestrators
2. **Create JSON Config Files**:
   - `config/choquet_weights.json` - Choquet aggregation weights
   - `config/unit_layer_config.json` - Unit layer parameters
   - `config/calibration_penalties.json` - All penalty values
   - `config/quality_thresholds.json` - All threshold values
3. **Implement @calibrated_method Decorator**
4. **Refactor Config Loading** - Load all values from JSON

### Secondary Actions (P1 - High Priority)

1. **Create Verification Scripts**:
   - `scripts/verify_no_hardcoded_calibrations.py`
   - `scripts/verify_singleton_enforcement.py`
   - `tests/test_no_parallel_systems.py`
2. **Centralize Penalty Management**
3. **Add Config Validation Layer**

---

## 📋 COMPLIANCE CHECKLIST

- [ ] **Singleton Pattern Enforced**
  - [ ] CalibrationOrchestrator singleton
  - [ ] IntrinsicScoreLoader singleton
  - [ ] MethodParameterLoader singleton
- [ ] **Zero Hardcoded Values**
  - [ ] All Choquet weights in JSON
  - [ ] All penalties in JSON
  - [ ] All thresholds in JSON
  - [ ] All unit layer params in JSON
- [ ] **Enforcement Mechanisms**
  - [ ] @calibrated_method decorator implemented
  - [ ] Verification scripts created
  - [ ] test_no_parallel_systems() passing
- [ ] **Single Source of Truth**
  - [ ] Only 1 intrinsic_calibration.json
  - [ ] Only 1 method_parameters.json
  - [ ] Only 1 LAYER_REQUIREMENTS definition
  - [ ] Only 1 CalibrationOrchestrator instance

---

## 🎯 SUCCESS CRITERIA

Migration Phase 4 is complete when:

1. ✅ **All P0 violations resolved**
2. ✅ **`scripts/verify_no_hardcoded_calibrations.py` passes with 0 violations**
3. ✅ **`tests/test_no_parallel_systems.py` passes**
4. ✅ **All calibration values loaded from JSON**
5. ✅ **Singleton pattern prevents parallel instances**
6. ✅ **@calibrated_method decorator enforces calibration**

---

## 📚 REFERENCES

- **User Blueprint:** Original instructions for Phase 2-5 folder restructuring
- **Formal Spec:** MIGRATION_ARTIFACTS_FAKE_TO_REAL/01_DOCUMENTATION/CALIBRATION_MIGRATION_CONTRACT.md
- **Mathematical Model:** canonic_calibration_methods.md (8-layer architecture)
- **Zero Tolerance Policy:** "Be strict and severe, do not lose the maximum goal of sight: complete and full integration of calibration and parametrization system"

---

**Report Generated:** 2025-11-26
**Next Action:** Begin implementing P0 fixes (singleton patterns + JSON config files)
