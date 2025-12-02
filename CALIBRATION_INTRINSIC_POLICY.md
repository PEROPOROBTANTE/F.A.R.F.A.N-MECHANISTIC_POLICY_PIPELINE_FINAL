# Calibration Intrinsic Policy

**Document Version**: 1.0.0  
**Last Updated**: 2025-12-02  
**Status**: Active

---

## Purpose

This document defines the distinction between **intrinsic constants** (code-resident) and **externalizable parameters** (config-resident) for the F.A.R.F.A.N calibration system, enforcing **Constraint 4**: No Hardcoded Calibration Parameters.

---

## Core Principle

> [!CAUTION]
> **Calibration parameters MUST be externalized to configuration files**. Only parameters proven to be intrinsic to the algorithm's mathematical correctness may remain in code, and they MUST be documented in this policy.

---

## Decision Tree: Should This Be Externalized?

```
Is the value related to calibration/quality assessment?
├─ YES → Ask: Does changing it affect METHOD QUALITY SCORES?
│         ├─ YES → **EXTERNALIZE** to config
│         └─ NO  → Continue to next question
└─ NO  → Ask: Is it a numerical constant with theoretical justification?
          ├─ YES → MAY remain in code (document below)
          └─ NO  → **EXTERNALIZE** to config
```

---

## Category 1: EXTERNALIZE to Config

These parameters **MUST** be in config files, **NOT** in code:

### 1.1 Layer Weights
**Location**: `config/canonic_inventorry_methods_layers.json`

```json
{
  "method_id": {
    "linear_weights": {
      "@b": 0.167,
      "@chain": 0.125,
      ...
    },
    "interactions": {
      "@u×@chain": 0.125,
      ...
    }
  }
}
```

**Rationale**: Different methods may require different layer weightings based on their role and domain.

---

### 1.2 Quality Thresholds
**Location**: Various config files (e.g., `intrinsic_calibration.json`)

**Examples**:
- Test coverage threshold: `coverage >= 0.8`
- Stability coefficient: `CV < 0.1`
- Failure rate threshold: `failure_rate< 0.01`
- @b score marginal quality: `b_score_threshold = 0.7`

**Rationale**: Thresholds represent domain-specific quality expectations that evolve over time.

---

### 1.3 Interaction Coefficients
**Location**: `config/canonic_inventorry_methods_layers.json`

**Examples** (from canonical analysis):
```python
# ❌ FORBIDDEN in code
a_u_chain = 0.125  # Plan quality limits wiring

# ✅ CORRECT in config
{
  "interactions": {
    "@u×@chain": 0.125
  }
}
```

---

### 1.4 Domain-Specific Cutoffs
**Location**: Method-specific config or calibration files

**Examples**:
- Bayesian prior: `alpha = 2.0` (domain-tuned)
- Confidence interval width: `ci_width = 0.95`
- Semantic similarity cutoff: `sim_threshold = 0.75`

**Rationale**: These are calibration parameters that may need adjustment based on empirical performance.

---

##Category 2: MAY Remain in Code (Intrinsic Constants)

These constants are **permitted** in code but **MUST** be listed here with justification:

### 2.1 Numerical Stability Tolerances

| Constant | Value | Location | Justification |
|:---------|:------|:---------|:--------------|
| `epsilon` | `1e-9` | Various numerical functions | Standard floating-point comparison tolerance |
| `min_denominator` | `1e-12` | Division operations | Prevents division by zero |
| `convergence_tol` | `1e-6` | Iterative algorithms | Standard convergence criterion |

**Rationale**: These are mathematical requirements, not calibration parameters.

---

### 2.2 Algorithm Hyperparameters (Theorem-Proven)

| Constant | Value | Location | Justification |
|:---------|:------|:---------|:--------------|
| `bayesian_alpha_uniform` | `1.0` | Bayesian priors | Uniform Dirichlet prior (theoretical default) |
| `e` | `2.71828...` | Exponential functions | Mathematical constant |
| `pi` | `3.14159...` | Trigonometric functions | Mathematical constant |

**Rationale**: These values are derived from mathematical theory, not empirical tuning.

---

### 2.3 Data Structure Limits

| Constant | Value | Location | Justification |
|:---------|:------|:---------|:--------------|
| `MAX_INT` | `sys.maxsize` | Bounds checking | System-defined limit |
| `UTF8_BOM` | `\\ufeff` | Text processing | Unicode standard |

**Rationale**: System or standard-defined limits, not calibration parameters.

---

## Whitelisted Code Constants

### Approved Intrinsic Constants (Current)

```python
# src/farfan_pipeline/core/calibration/orchestrator.py
EPSILON = 1e-9  # Numerical stability tolerance
# Justification: Standard floating-point comparison tolerance
# Last reviewed: 2025-12-02

# src/farfan_pipeline/processing/bayesian_analyzer.py
DIRICHLET_ALPHA_UNIFORM = 1.0  # Uniform prior
# Justification: Theoretical default for non-informative prior (Gelman et al. 2013)
# Last reviewed: 2025-12-02
```

**Process to Add New Constant**:
1. Propose in code review
2. Justify theoretical/mathematical basis
3. Add to this document
4. Get approval from calibration team

---

## Examples: Before & After

### Example 1: Layer Weights

❌ **BEFORE (FORBIDDEN)**:
```python
def calibrate_method(self, method_id, context):
    a_b = 0.167  # Hardcoded weight
    a_chain = 0.125
    score = a_b * x_b + a_chain * x_chain + ...
```

✅ **AFTER (CORRECT)**:
```python
def calibrate_method(self, method_id, context):
    config = self.load_layer_config(method_id)
    a_b = config['linear_weights']['@b']
    a_chain = config['linear_weights']['@chain']
    score = a_b * x_b + a_chain * x_chain + ...
```

---

### Example 2: Thresholds

❌ **BEFORE (FORBIDDEN)**:
```python
def compute_b_impl(self, coverage):
    if coverage >= 0.8:  # Hardcoded threshold
        return 1.0
    return coverage / 0.8
```

✅ **AFTER (CORRECT)**:
```python
def compute_b_impl(self, coverage):
    threshold = self.config['coverage_threshold']  # From config
    if coverage >= threshold:
        return 1.0
    return coverage / threshold
```

---

### Example 3: Intrinsic Constant (ALLOWED)

✅ **ALLOWED** (but must be documented here):
```python
def safe_divide(numerator, denominator):
    EPSILON = 1e-9  # Numerical stability tolerance
    if abs(denominator) < EPSILON:
        return 0.0
    return numerator / denominator
```

**Justification**: `EPSILON` is a mathematical constant for numerical stability, not a calibration parameter.

---

## Enforcement

### Automated Checks

1. **`test_no_hardcoded_calibrations.py`**:
   - Scans code for regex patterns: `threshold\s*=\s*0\.\d+`, `weight\s*=\s*0\.\d+`
   - Whitelists constants listed in this document
   - **CI/CD**: Fails build if violations found

2. **`apply_calibration_rubric.py`**:
   - Flags suspected hardcoded parameters during calibration computation
   - Generates warnings in output

### Manual Review

- All PRs touching calibration code require policy review
- New magic numbers trigger mandatory justification
- Quarterly audit of whitelisted constants

---

## Policy Updates

**Version History**:
- v1.0.0 (2025-12-02): Initial policy establishment

**Amendment Process**:
1. Propose change via GitHub issue
2. Calibration team review
3. Update this document
4. Update test whitelists
5. Announce in team meeting

---

## References

- **Constraint 4**: Implementation Plan § "No Hardcoded Calibration Parameters"
- **Canonical Analysis**: `CALIBRATION_CANONICAL_COHERENCE_ANALYSIS.md` § 3-5
- **Test Suite**: `tests/calibration_system/test_no_hardcoded_calibrations.py`
