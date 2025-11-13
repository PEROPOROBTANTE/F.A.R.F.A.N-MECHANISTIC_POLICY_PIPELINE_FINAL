# Contract V2 Quick Reference Card

## Import Statements

```python
# V2 Contracts
from saaaaaa.utils.contracts import (
    AnalysisInputV2,
    AnalysisOutputV2,
    DocumentMetadataV2,
    ProcessedTextV2,
    ExecutionContextV2,
    # Exceptions
    ContractValidationError,
    DataIntegrityError,
    FlowCompatibilityError,
    SystemConfigError,
    # Utilities
    StructuredLogger,
    compute_content_digest,
    utc_now_iso,
)

# Deterministic Execution
from saaaaaa.utils.deterministic_execution import (
    DeterministicSeedManager,
    DeterministicExecutor,
    enforce_utc_now,
)

# Adapters (for migration)
from saaaaaa.utils.contract_adapters import (
    adapt_analysis_input_v1_to_v2,
    adapt_document_metadata_v1_to_v2,
    v2_to_v1_dict,
    validate_flow_compatibility,
)
```

## Common Patterns

### Create Analysis Input
```python
# ✅ GOOD: Auto-computes digest
input_data = AnalysisInputV2.create_from_text(
    text="Policy text",
    document_id="DOC-123",
    policy_unit_id="PDM-001"
)

# ❌ BAD: Manual fields
input_data = AnalysisInputV2(
    text="...",
    input_digest="...",  # Error-prone
    payload_size_bytes=len("...")
)
```

### Deterministic Processing
```python
manager = DeterministicSeedManager(base_seed=42)

with manager.scoped_seed("operation_name") as seed:
    # All random ops use this seed
    result = process_with_random()
# Seed auto-restored
```

### Structured Logging
```python
logger = StructuredLogger(__name__)

logger.log_execution(
    operation="process",
    correlation_id=input.correlation_id,
    success=True,
    latency_ms=10.5
)
# Outputs JSON to stdout
```

### Error Handling
```python
try:
    process(data)
except ValidationError as e:
    raise ContractValidationError(
        "Invalid input", 
        field="text"
    ) from e
# Auto-generates event_id
```

### Flow Validation
```python
validate_flow_compatibility(
    producer_output=stage1_output,
    consumer_expected_fields=["text", "doc_id"],
    producer_name="stage1",
    consumer_name="stage2"
)
```

### V1 to V2 Migration
```python
# Adapt V1 dict to V2
v2_input = adapt_analysis_input_v1_to_v2(
    v1_dict, 
    policy_unit_id="PDM-001"
)

# Process with V2
result = process_v2(v2_input)

# Convert back to V1 if needed
v1_output = v2_to_v1_dict(result)
```

## Field Quick Reference

### All V2 Contracts Include:
- `schema_version: str` - Always "2.0.0"
- `timestamp_utc: str` - ISO-8601 with 'Z' suffix
- `correlation_id: str` - UUID for tracing

### AnalysisInputV2:
- `text: str` - Input text (min 1 char)
- `document_id: str` - Document identifier
- `policy_unit_id: str` - Policy unit ID
- `input_digest: str` - SHA-256 (64 hex chars)
- `payload_size_bytes: int` - Size in bytes

### AnalysisOutputV2:
- `dimension: str` - Analysis dimension
- `category: str` - Result category
- `confidence: float` - Score in [0.0, 1.0]
- `matches: List[str]` - Evidence matches
- `output_digest: str` - SHA-256 (64 hex chars)
- `policy_unit_id: str` - Policy unit ID
- `processing_latency_ms: float` - Latency

## Validation Rules

### Confidence Score:
- Must be in [0.0, 1.0]
- Rounded to 6 decimals for stability
- Raises `ContractValidationError` if out of range

### Timestamps:
- Must be UTC (ISO-8601)
- Must end with 'Z' or '+00:00'
- Raises `ContractValidationError` if not UTC

### SHA-256 Digests:
- Must be exactly 64 hexadecimal characters
- Lowercase a-f, 0-9
- Computed with `compute_content_digest()`

### Policy Unit ID:
- Required in all operations
- Format: "PDM-NNN" or similar
- Links all artifacts to policy document

## Determinism Checklist

- [ ] Use `DeterministicSeedManager` for random operations
- [ ] Use `utc_now_iso()` for timestamps (not `datetime.now()`)
- [ ] Use `enforce_utc_now()` for datetime objects
- [ ] Compute digests with `compute_content_digest()`
- [ ] Set PYTHONHASHSEED env var for full determinism

## Exception Hierarchy

```
Exception
├── ContractValidationError  # Contract violations
├── DataIntegrityError       # Hash mismatches
├── SystemConfigError        # Config errors
└── FlowCompatibilityError   # Stage mismatches
```

All include `event_id` for debugging.

## Testing Pattern

```python
if __name__ == "__main__":
    # Run doctests
    import doctest
    doctest.testmod(verbose=True)
    
    # Integration tests
    processor = MyProcessor("PDM-001")
    result = processor.process(...)
    
    assert isinstance(result, AnalysisOutputV2)
    assert 0.0 <= result.confidence <= 1.0
    assert len(result.output_digest) == 64
    
    print("✓ All tests passed!")
```

## Performance Notes

- Contract validation: ~0.1-0.5ms
- Digest computation: ~1-2ms
- Logging: ~0.1ms
- **Total overhead: < 5ms/stage**

## Common Gotchas

❌ **Don't:**
```python
# Manual digest (error-prone)
digest = hashlib.sha256(text).hexdigest()

# Local time
timestamp = datetime.now()

# Generic exceptions
raise ValueError("Bad input")

# Print statements
print("Processing...")
```

✅ **Do:**
```python
# Auto-computed digest
input = AnalysisInputV2.create_from_text(...)

# UTC time
timestamp = utc_now_iso()

# Domain-specific exceptions
raise ContractValidationError("...", field="...")

# Structured logging
logger.log_execution(...)
```

## Migration Timeline

1. **Phase 1**: New components use V2 directly
2. **Phase 2**: Wrap existing with adapters
3. **Phase 3**: Migrate internals to V2
4. **Phase 4**: Remove V1 contracts (future)

## Support

- **Migration Guide**: `CONTRACT_V2_MIGRATION_GUIDE.md`
- **Examples**: `examples/enhanced_policy_processor_v2_example.py`
- **Summary**: `CONTRACT_HARDENING_IMPLEMENTATION_SUMMARY.md`
- **Tests**: All modules have `if __name__ == "__main__"` tests
