# Phase 7 Task Construction - Quick Reference

## At a Glance

**Purpose**: Convert validated schemas to executable tasks  
**Input**: Phase6SchemaValidationOutput  
**Output**: Phase7TaskConstructionOutput  
**Contract**: 300 tasks, zero duplicates, all fields validated

---

## Quick Start

```python
from src.farfan_pipeline.core.phases import (
    phase6_schema_validation,
    phase7_task_construction,
)

# Step 1: Validate schemas
phase6_output = phase6_schema_validation(raw_questions, raw_chunks)

# Step 2: Construct tasks
phase7_output = phase7_task_construction(phase6_output)

# Step 3: Check result
if phase7_output.construction_passed:
    print(f"✅ {phase7_output.task_count} tasks ready")
    for task in phase7_output.tasks:
        print(f"  - {task.task_id}")
else:
    print(f"❌ Construction failed")
    for error in phase7_output.construction_errors:
        print(f"  - {error}")
```

---

## Task ID Format

```
MQC-{question_global:03d}_{policy_area_id}

Examples:
  MQC-000_PA01  ← question_global=0, policy_area_id="PA01"
  MQC-042_PA05  ← question_global=42, policy_area_id="PA05"
  MQC-299_PA10  ← question_global=299, policy_area_id="PA10"
```

**Key Points**:
- Three-character zero-padding enforced
- Duplicate detection at Phase 7.1
- Format validation before construction

---

## ExecutableTask Fields

| Field | Type | Validation | Source |
|-------|------|------------|--------|
| task_id | str | Non-empty, format | Generated |
| question_id | str | Non-empty | Question |
| question_global | int | 0-999 | Question |
| policy_area_id | str | Non-empty | Question |
| dimension_id | str | Non-empty | Question |
| chunk_id | str | Non-empty | Chunk |
| patterns | list[dict] | List type | Question |
| signals | dict | Dict type | Question |
| creation_timestamp | str | ISO 8601 | Generated |
| expected_elements | list[dict] | List type | Question |
| metadata | dict | Dict type | Constructed |

---

## Error Handling Patterns

### KeyError (Missing Field)
```python
# Automatic handling via safe accessors
question_id = _safe_get_attribute(
    question, "question_id", context, errors, ""
)
# Error accumulated: "Field 'question_id' not found in question[0]: KeyError"
```

### TypeError (Wrong Type)
```python
# Type validation before operations
if not _validate_field_list_type("patterns", patterns, context, errors):
    return None  # Early return
# Error accumulated: "Field 'patterns' has invalid type: expected list, got dict"
```

### ValueError (Invalid Value)
```python
# Range validation
if not _validate_field_integer_range(
    "question_global", value, context, 0, 999, errors
):
    return None
# Error accumulated: "Field 'question_global' has invalid value: 1000 not in range [0, 999]"
```

---

## Common Issues & Solutions

### Issue: "Phase 6 schema validation failed"
**Cause**: Invalid input data  
**Solution**: Fix raw_questions or raw_chunks  
**Check**: `phase6_output.validation_errors`

### Issue: "Task count mismatch: expected 300"
**Cause**: Not enough valid question-chunk pairs  
**Solution**: Ensure 300 questions with matching chunks  
**Check**: `phase6_output.question_count`, `phase6_output.chunk_count`

### Issue: "Duplicate task IDs detected"
**Cause**: Duplicate question_global + policy_area_id combinations  
**Solution**: Ensure unique (question_global, policy_area_id) pairs  
**Check**: `phase7_output.duplicate_task_ids`

### Issue: "Field 'X' not found"
**Cause**: Missing required field in question or chunk  
**Solution**: Add missing field to input data  
**Check**: `phase7_output.construction_errors`

### Issue: "Field 'X' has invalid type"
**Cause**: Wrong data type for field  
**Solution**: Convert field to correct type  
**Check**: Error message shows expected vs actual type

---

## Processing Order

Phase 7 executes in strict sequential order:

```
Phase 7.1: Identifier Generation
  ├─ For each question:
  │  ├─ Extract question_global
  │  ├─ Extract policy_area_id
  │  ├─ Validate both fields
  │  ├─ Generate task_id = f"MQC-{question_global:03d}_{policy_area_id}"
  │  └─ Store in task_id_map
  └─ Check for duplicates

Phase 7.2: Task Construction
  ├─ For each question:
  │  ├─ Get task_id from task_id_map
  │  ├─ Find matching chunk (by policy_area_id + dimension_id)
  │  ├─ Validate fields in order (see Field Processing Order)
  │  ├─ Construct ExecutableTask
  │  └─ Add to task list
  └─ Return Phase7TaskConstructionOutput
```

---

## Field Processing Order

When constructing a single task, fields are processed in this order:

1. **task_id** (from task_id_map)
2. **question_id** (validate non-empty string)
3. **question_global** (validate int, range 0-999)
4. **policy_area_id** (validate non-empty string)
5. **dimension_id** (validate non-empty string)
6. **chunk_id** (validate non-empty string)
7. **patterns** (validate list type)
8. **signals** (validate dict type)
9. **creation_timestamp** (generate ISO 8601)
10. **expected_elements** (validate list type)
11. **metadata** (construct dict)

**All validation completes before dataclass constructor is called.**

---

## Metadata Dictionary

Constructed metadata includes:

```python
metadata = {
    "base_slot": str,              # From question
    "cluster_id": str,             # From question
    "document_position": int,      # From chunk
    "phase7_version": str,         # "1.0.0"
    "question_metadata": dict,     # From Phase 6
    "chunk_metadata": dict,        # From Phase 6
    "pattern_count": int,          # len(patterns)
    "signal_count": int,           # len(signals)
    "expected_element_count": int, # len(expected_elements)
}
```

---

## Testing

### Unit Test Example
```python
def test_phase7_construction():
    questions = [create_valid_question(i) for i in range(5)]
    chunks = [create_valid_chunk(i) for i in range(5)]
    
    phase6_output = phase6_schema_validation(questions, chunks)
    phase7_output = phase7_task_construction(phase6_output)
    
    assert phase7_output.construction_passed
    assert phase7_output.task_count == 5
    assert len(phase7_output.construction_errors) == 0
```

### Integration Test Example
```python
def test_phase6_7_8_pipeline():
    questions = [create_valid_question(i) for i in range(20)]
    chunks = [create_valid_chunk(i) for i in range(20)]
    
    phase6_output = phase6_schema_validation(questions, chunks)
    assert phase6_output.schema_validation_passed
    
    phase7_output = phase7_task_construction(phase6_output)
    assert phase7_output.construction_passed
    
    phase8_output = phase8_execution_plan_assembly(phase7_output)
    assert phase8_output.assembly_passed
    assert phase8_output.execution_plan is not None
```

---

## Performance

Typical performance for 300 tasks:

- Phase 6 validation: ~50ms
- Phase 7.1 identifier generation: ~10ms
- Phase 7.2 task construction: ~100ms
- Phase 8 plan assembly: ~20ms

**Total**: ~180ms for complete Phase 6-7-8 pipeline

---

## Debugging

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Intermediate Results
```python
phase6_output = phase6_schema_validation(questions, chunks)
print(f"Phase 6: {phase6_output.question_count} questions validated")

phase7_output = phase7_task_construction(phase6_output)
print(f"Phase 7: {phase7_output.task_count} tasks constructed")
print(f"Errors: {phase7_output.construction_errors}")
print(f"Warnings: {phase7_output.construction_warnings}")
```

### Inspect Task Details
```python
for task in phase7_output.tasks:
    print(f"Task {task.task_id}:")
    print(f"  question_id: {task.question_id}")
    print(f"  question_global: {task.question_global}")
    print(f"  policy_area_id: {task.policy_area_id}")
    print(f"  dimension_id: {task.dimension_id}")
    print(f"  chunk_id: {task.chunk_id}")
```

---

## API Reference

### `phase6_schema_validation()`
```python
def phase6_schema_validation(
    raw_questions: list[dict[str, Any]],
    raw_chunks: list[dict[str, Any]],
) -> Phase6SchemaValidationOutput:
    """Validate question and chunk schemas."""
```

### `phase7_task_construction()`
```python
def phase7_task_construction(
    phase6_output: Phase6SchemaValidationOutput,
) -> Phase7TaskConstructionOutput:
    """Construct executable tasks from validated schemas."""
```

### `phase8_execution_plan_assembly()`
```python
def phase8_execution_plan_assembly(
    phase7_output: Phase7TaskConstructionOutput,
    plan_id: str | None = None,
) -> Phase8ExecutionPlanOutput:
    """Assemble tasks into immutable execution plan."""
```

---

## Related Documentation

- **Full Audit Report**: `docs/phases/phase_7/PHASE7_AUDIT_IMPLEMENTATION.md`
- **Implementation Summary**: `PHASE7_IMPLEMENTATION_SUMMARY.md`
- **Phase 7 Doctrine**: `docs/phases/phase_7/P07-EN_v1.0.md`
- **Integration Tests**: `tests/test_phase6_7_8_integration.py`

---

**Quick Reference Version**: 1.0.0  
**Last Updated**: 2025-01-19
