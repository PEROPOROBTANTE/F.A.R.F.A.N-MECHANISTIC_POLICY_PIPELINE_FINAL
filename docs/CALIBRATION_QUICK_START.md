# 🚀 Calibration System - Quick Start Guide

## Overview

The calibration system automatically validates methods based on their intrinsic quality, data flow integrity, and contextual appropriateness. It eliminates hardcoded thresholds and provides consistent, traceable validation decisions.

---

## Basic Usage

### 1. Validate a Single Method

```python
from src.saaaaaa.core.calibration.orchestrator import CalibrationOrchestrator
from src.saaaaaa.core.calibration.parameter_loader import MethodParameterLoader
from src.saaaaaa.core.calibration.validator import CalibrationValidator
from src.saaaaaa.core.calibration.data_structures import ContextTuple
from src.saaaaaa.core.calibration.pdt_structure import PDTStructure

# Setup (do once)
orchestrator = CalibrationOrchestrator(
    intrinsic_calibration_path="config/intrinsic_calibration.json"
)
parameter_loader = MethodParameterLoader("config/method_parameters.json")
validator = CalibrationValidator(orchestrator, parameter_loader)

# Prepare context and PDT
context = ContextTuple(
    question_id="D1Q1",
    dimension="D1_LINEA_BASE",
    policy_area="infraestructura",
    unit_id="plan_2024"
)
pdt = PDTStructure(...)  # Your parsed PDT

# Validate
result = validator.validate_method(
    method_id="D1Q1_Executor",
    method_version="1.0.0",
    context=context,
    pdt_structure=pdt
)

# Check result
if result.decision == "PASS":
    print(f"✓ Method validated! Score: {result.calibration_score:.3f}")
else:
    print(f"✗ Validation failed: {result.failure_reason}")
    print(f"  Details: {result.failure_details}")
    for rec in result.recommendations:
        print(f"  → {rec}")
```

### 2. Validate All 30 Executors for a Plan

```python
# Validate complete plan
report = validator.validate_plan_executors(
    plan_id="plan_bogota_2024",
    context=context,
    pdt_structure=pdt
)

# Summary
print(f"Overall Decision: {report.overall_decision}")
print(f"Pass Rate: {report.pass_rate():.1%}")
print(f"Passed: {report.passed} / {report.total_methods}")
print(f"Failed: {report.failed}")

# Failed methods
for result in report.method_results:
    if result.decision == "FAIL":
        print(f"  ✗ {result.method_id}: {result.failure_reason}")

# Export to JSON
import json
with open(f"validation_{report.plan_id}.json", "w") as f:
    json.dump(report.to_dict(), f, indent=2)
```

### 3. Get Calibration Scores (Without Validation)

```python
# Just compute scores
calibration_result = orchestrator.calibrate(
    method_id="D1Q1_Executor",
    method_version="1.0.0",
    context=context,
    pdt_structure=pdt
)

print(f"Final Score: {calibration_result.final_score:.3f}")

# Layer breakdown
for layer_id, layer_score in calibration_result.layer_scores.items():
    print(f"  {layer_id.value}: {layer_score.score:.3f} - {layer_score.rationale}")
```

---

## Configuration

### Quality Thresholds

Global quality levels are defined in `config/method_parameters.json`:

```json
{
  "_global_thresholds": {
    "quality_levels": {
      "excellent": 0.85,
      "good": 0.70,
      "acceptable": 0.55,
      "insufficient": 0.0
    }
  }
}
```

**Usage:**

```python
loader = MethodParameterLoader()
thresholds = loader.get_quality_thresholds()

if score >= thresholds["excellent"]:
    level = "EXCELENTE"
elif score >= thresholds["good"]:
    level = "BUENO"
elif score >= thresholds["acceptable"]:
    level = "ACEPTABLE"
else:
    level = "INSUFICIENTE"
```

### Executor Thresholds

Each executor has a specific validation threshold:

```python
loader = MethodParameterLoader()

# Get threshold for specific executor
threshold = loader.get_executor_threshold("D4Q1_Executor")
print(f"D4Q1 requires score >= {threshold}")  # 0.80 (financial is strict)

# Check if executor requires all layers
requires_all = loader.executor_requires_all_layers("D4Q1_Executor")
print(f"Requires all 8 layers: {requires_all}")  # True
```

### Role-Based Thresholds

For non-executor methods, thresholds are based on role:

```python
loader = MethodParameterLoader()

# Get threshold by role
analyzer_threshold = loader.get_validation_threshold_for_role("analyzer")  # 0.70
utility_threshold = loader.get_validation_threshold_for_role("utility")    # 0.30
```

---

## Understanding Validation Decisions

### Decision Types

- **`PASS`** - Method meets threshold, safe to use
- **`FAIL`** - Method below threshold, DO NOT use
- **`CONDITIONAL_PASS`** - Plan partially validated, review required
- **`SKIPPED`** - Method excluded from calibration

### Failure Reasons

| Reason | Meaning | Action |
|--------|---------|--------|
| `BASE_LAYER_LOW` | Code quality issues | Improve code: add tests, docs, refactor |
| `CHAIN_LAYER_FAIL` | Missing inputs | Verify data flow, check dependencies |
| `CONGRUENCE_FAIL` | Method incompatibility | Review method ensemble |
| `UNIT_LAYER_FAIL` | PDT quality low | Improve PDT structure |
| `CONTEXTUAL_FAIL` | Wrong context | Use different method for this context |
| `META_LAYER_FAIL` | Governance issues | Improve traceability, logging |

### Example: Handling Failures

```python
result = validator.validate_method(...)

if result.decision == "FAIL":
    if result.failure_reason == "BASE_LAYER_LOW":
        # Code quality issue
        logger.error(f"Method {result.method_id} has low code quality")
        logger.info("Recommendations:")
        for rec in result.recommendations:
            logger.info(f"  - {rec}")
        # Don't use this method, use fallback
        use_fallback_method()

    elif result.failure_reason == "CHAIN_LAYER_FAIL":
        # Missing inputs
        logger.error("Required inputs not available")
        # Verify upstream methods executed
        verify_dependencies()
```

---

## Layer System

### 8 Calibration Layers

All executors are evaluated on **8 layers**:

1. **@b (BASE)** - Intrinsic code quality (from `intrinsic_calibration.json`)
2. **@u (UNIT)** - PDT structure quality
3. **@q (QUESTION)** - Question compatibility
4. **@d (DIMENSION)** - Dimension compatibility
5. **@p (POLICY)** - Policy area compatibility
6. **@C (CONGRUENCE)** - Method ensemble compatibility
7. **@chain (CHAIN)** - Data flow integrity
8. **@m (META)** - Governance and traceability

### Layer Requirements by Role

| Role | Layers | Count | Rationale |
|------|--------|-------|-----------|
| Analyzer | All 8 | 8 | Complex analysis requires full rigor |
| Processor | @b, @u, @chain, @m | 4 | Processing doesn't need contextual |
| Utility | @b, @chain, @m | 3 | Minimal for helpers |

**Check required layers:**

```python
resolver = orchestrator.layer_resolver

required = resolver.get_required_layers("my.method.name")
print(f"Method requires: {[l.value for l in required]}")

skipped = resolver.get_skipped_layers("my.method.name")
print(f"Method skips: {[l.value for l in skipped]}")
```

---

## Advanced Usage

### Custom Thresholds

Override threshold for testing:

```python
result = validator.validate_method(
    method_id="D1Q1_Executor",
    method_version="1.0.0",
    context=context,
    pdt_structure=pdt,
    override_threshold=0.90  # Force very strict validation
)
```

### Accessing Raw Calibration Data

```python
from src.saaaaaa.core.calibration.intrinsic_loader import IntrinsicScoreLoader

loader = IntrinsicScoreLoader()

# Get full method data
data = loader.get_method_data("my.method.name")
print(f"Theory: {data['b_theory']}")
print(f"Implementation: {data['b_impl']}")
print(f"Deployment: {data['b_deploy']}")
print(f"Role: {data['layer']}")

# Check if method is calibrated
if loader.is_calibrated("my.method.name"):
    score = loader.get_score("my.method.name")
    print(f"Intrinsic score: {score:.3f}")
```

### Batch Validation

```python
methods_to_validate = [
    "D1Q1_Executor",
    "D1Q2_Executor",
    "D1Q3_Executor"
]

results = []
for method in methods_to_validate:
    result = validator.validate_method(
        method_id=method,
        method_version="1.0.0",
        context=context,
        pdt_structure=pdt
    )
    results.append(result)

# Summary
passed = sum(1 for r in results if r.decision == "PASS")
print(f"Batch validation: {passed}/{len(results)} passed")
```

---

## Troubleshooting

### Method Not in intrinsic_calibration.json

```python
loader = IntrinsicScoreLoader()

if not loader.is_calibrated("my.method"):
    print("Method not calibrated!")
    print("Options:")
    print("  1. Re-run calibration triage script")
    print("  2. Method will use default score (0.5)")
```

### Layer Evaluation Errors

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Calibrate with detailed logs
result = orchestrator.calibrate(...)
# Check logs for which layer failed
```

### Threshold Too Strict

```python
# Check what threshold is being used
loader = MethodParameterLoader()

# For executor
threshold = loader.get_executor_threshold("D4Q1_Executor")
print(f"Current threshold: {threshold}")

# To adjust: edit config/method_parameters.json
# Then reload:
loader = MethodParameterLoader()  # Fresh instance
```

---

## Best Practices

### 1. Always Validate Before Execution

```python
# ✓ Good
result = validator.validate_method(...)
if result.decision == "PASS":
    output = execute_method(...)
else:
    logger.error(f"Validation failed: {result.failure_reason}")
    raise ValidationError(result.failure_details)

# ✗ Bad
output = execute_method(...)  # No validation!
```

### 2. Log Calibration Scores

```python
logger.info(f"Method: {method_id}")
logger.info(f"Score: {result.calibration_score:.3f} / {result.threshold:.3f}")
logger.info(f"Decision: {result.decision}")
for layer, score in result.layer_scores.items():
    logger.debug(f"  {layer}: {score:.3f}")
```

### 3. Handle Failures Gracefully

```python
try:
    result = validator.validate_method(...)
    if result.decision == "FAIL":
        # Use fallback or skip
        return use_fallback_method()
except Exception as e:
    logger.error(f"Validation error: {e}")
    # Decide: fail safe or fail fast?
    return None  # Fail safe
```

### 4. Export Validation Reports

```python
import json
from datetime import datetime

report = validator.validate_plan_executors(...)

# Save with timestamp
filename = f"validation_{report.plan_id}_{datetime.now():%Y%m%d_%H%M%S}.json"
with open(filename, "w") as f:
    json.dump(report.to_dict(), f, indent=2)

logger.info(f"Validation report saved: {filename}")
```

---

## Performance Tips

1. **Reuse orchestrator instances** - Initialization loads large JSON files
   ```python
   # ✓ Do once
   orchestrator = CalibrationOrchestrator(...)
   validator = CalibrationValidator(orchestrator, ...)

   # Use many times
   for method in methods:
       validator.validate_method(...)
   ```

2. **Lazy loading is automatic** - JSON files load only on first access

3. **Cache parameter loader** - Don't create new instances unnecessarily

---

## Integration with Existing Code

### Replace Hardcoded Thresholds

**Before:**
```python
# ✗ Hardcoded
if score >= 0.85:
    quality = "EXCELENTE"
elif score >= 0.70:
    quality = "BUENO"
```

**After:**
```python
# ✓ Centralized
loader = MethodParameterLoader()
thresholds = loader.get_quality_thresholds()

if score >= thresholds["excellent"]:
    quality = "EXCELENTE"
elif score >= thresholds["good"]:
    quality = "BUENO"
```

### Add Validation to Executors

```python
class D1Q1_Executor(AdvancedDataFlowExecutor):
    def execute(self, doc, method_executor):
        # Validate before execution
        if self.calibration_orchestrator:
            validator = CalibrationValidator(
                self.calibration_orchestrator,
                MethodParameterLoader()
            )
            result = validator.validate_method(
                method_id="D1Q1_Executor",
                method_version="1.0.0",
                context=self.context,
                pdt_structure=self.pdt
            )

            if result.decision == "FAIL":
                logger.error(f"Executor validation failed: {result.failure_reason}")
                raise ExecutorValidationError(result.failure_details)

        # Execute
        return self.execute_with_optimization(...)
```

---

## FAQ

**Q: What happens if a method is not in intrinsic_calibration.json?**
A: It uses a default score (0.5) and logs a warning. Method should be re-calibrated.

**Q: Can I adjust thresholds without changing code?**
A: Yes! Edit `config/method_parameters.json` and restart.

**Q: What if I want stricter validation?**
A: Increase thresholds in `method_parameters.json`. For executors, edit the `"threshold"` field.

**Q: How do I know which layer caused a failure?**
A: Check `result.failure_reason` and `result.failure_details`. Also check `result.layer_scores`.

**Q: Can I skip validation for specific methods?**
A: Add them to `intrinsic_calibration.json` with `"calibration_status": "excluded"`.

---

## Next Steps

- See `CALIBRATION_IMPLEMENTATION_REPORT.md` for technical details
- Check `tests/test_calibration_integration.py` for examples
- Review `config/method_parameters.json` to understand configuration

**Support:** Check logs with `logging.DEBUG` level for detailed diagnostics.
