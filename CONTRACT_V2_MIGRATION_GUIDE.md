# Contract System V2 Migration Guide

## Overview

This guide documents the migration from V1 (TypedDict-based) to V2 (Pydantic-based) contracts in the F.A.R.F.A.N policy analysis pipeline. The V2 contract system enforces strict validation, deterministic execution, cryptographic verification, and comprehensive observability.

## Key Improvements in V2

### 1. **Explicit I/O with Static Types**
- All contracts are Pydantic `BaseModel` with strict validation
- Frozen/immutable models prevent accidental mutations
- Complete type hints throughout

### 2. **Cryptographic Verification**
- `content_digest`: SHA-256 hash of input/output content
- Deterministic hashing for reproducibility
- Content integrity verification across pipeline stages

### 3. **Temporal Metadata**
- `timestamp_utc`: ISO-8601 UTC timestamps (no local time)
- `schema_version`: Semantic versioning for contract evolution
- `correlation_id`: UUID for distributed tracing

### 4. **Policy Context**
- `policy_unit_id`: Unique identifier for policy units (e.g., "PDM-001")
- Links all artifacts to specific policy documents

### 5. **Determinism**
- Seed management for all stochastic operations
- UTC-only timestamps (no local time dependencies)
- Reproducible event IDs

### 6. **Observability**
- Structured JSON logging with correlation IDs
- Processing latency tracking (`processing_latency_ms`)
- Payload size monitoring (`payload_size_bytes`)
- No PII logging

### 7. **Error Handling**
- Domain-specific exceptions with event IDs:
  - `ContractValidationError`: Contract violations
  - `DataIntegrityError`: Hash mismatches, data corruption
  - `SystemConfigError`: Configuration errors
  - `FlowCompatibilityError`: Pipeline stage mismatches
- No `except: pass` allowed
- Clear differentiation between data and system errors

## Contract Comparison

### DocumentMetadata

**V1 (TypedDict):**
```python
{
    "file_path": str,
    "file_name": str,
    "num_pages": int,
    "file_size_bytes": int,
    "file_hash": str  # Unspecified hash type
}
```

**V2 (Pydantic):**
```python
DocumentMetadataV2(
    # V2-specific fields
    schema_version="2.0.0",
    timestamp_utc="2024-01-01T00:00:00Z",
    correlation_id="550e8400-e29b-41d4-a716-446655440000",
    policy_unit_id="PDM-001",
    content_digest="abc123...",  # SHA-256 (64 hex chars)
    
    # V1-compatible fields
    file_path="/path/to/doc.pdf",
    file_name="doc.pdf",
    num_pages=10,
    file_size_bytes=1024000,
    encoding="utf-8",
    
    # Optional fields
    pdf_metadata={"author": "..."},
    author="John Doe",
    title="Policy Document",
    creation_date="2024-01-01"
)
```

### AnalysisInput

**V1 (TypedDict):**
```python
{
    "text": str,
    "document_id": str,
    "metadata": dict | None,
    "context": dict | None,
    "sentences": list[str] | None
}
```

**V2 (Pydantic):**
```python
AnalysisInputV2(
    # V2-specific fields
    schema_version="2.0.0",
    timestamp_utc="2024-01-01T00:00:00Z",
    correlation_id="...",
    policy_unit_id="PDM-001",
    input_digest="abc123...",  # SHA-256 of text
    payload_size_bytes=1024,
    
    # V1-compatible fields
    text="Policy text to analyze",
    document_id="DOC-123",
    metadata={"key": "value"},
    context={"execution": "context"},
    sentences=["Sentence 1.", "Sentence 2."]
)
```

## Migration Strategies

### Strategy 1: Gradual Migration (Recommended)

Migrate components incrementally while maintaining V1 compatibility:

```python
from saaaaaa.utils.contracts import AnalysisInputV2
from saaaaaa.utils.contract_adapters import (
    adapt_analysis_input_v1_to_v2,
    v2_to_v1_dict
)

def process_analysis(raw_input: dict, policy_unit_id: str) -> dict:
    """Process analysis with V2 contracts internally, V1 externally."""
    
    # Adapt V1 input to V2
    v2_input = adapt_analysis_input_v1_to_v2(raw_input, policy_unit_id)
    
    # Process with V2 contracts
    v2_result = internal_process_v2(v2_input)
    
    # Convert V2 output back to V1 dict for backward compatibility
    v1_output = v2_to_v1_dict(v2_result)
    
    return v1_output
```

### Strategy 2: Full V2 Migration

Migrate entire component to V2:

```python
from saaaaaa.utils.contracts import (
    AnalysisInputV2,
    AnalysisOutputV2,
    StructuredLogger
)
from saaaaaa.utils.deterministic_execution import DeterministicExecutor

class V2PolicyProcessor:
    """Policy processor with V2 contracts."""
    
    def __init__(self, policy_unit_id: str):
        self.policy_unit_id = policy_unit_id
        self.logger = StructuredLogger(__name__)
        self.executor = DeterministicExecutor(base_seed=42)
    
    @executor.deterministic(operation_name="process_policy")
    def process(self, input_data: AnalysisInputV2) -> AnalysisOutputV2:
        """Process with full V2 contract enforcement."""
        
        # Validate input contract
        if not isinstance(input_data, AnalysisInputV2):
            raise ContractValidationError(
                "Expected AnalysisInputV2 input",
                field="input_data"
            )
        
        # Process...
        result = self._internal_process(input_data.text)
        
        # Create V2 output
        return AnalysisOutputV2(
            dimension="D1",
            category="category_a",
            confidence=0.85,
            matches=result["matches"],
            output_digest=compute_content_digest(str(result)),
            policy_unit_id=self.policy_unit_id,
            processing_latency_ms=10.5
        )
```

### Strategy 3: Adapter Wrapper

Wrap existing V1 functions without internal changes:

```python
from saaaaaa.utils.contract_adapters import (
    adapt_analysis_input_v1_to_v2,
    v2_to_v1_dict
)

def v1_legacy_function(input_dict: dict) -> dict:
    """Existing V1 function - unchanged."""
    return {"result": "success"}

def v2_wrapped_function(input_v2: AnalysisInputV2) -> AnalysisOutputV2:
    """V2 wrapper around V1 function."""
    
    # Convert V2 to V1 dict
    v1_input = v2_to_v1_dict(input_v2)
    
    # Call V1 function
    v1_result = v1_legacy_function(v1_input)
    
    # Adapt V1 result to V2
    # (custom adaptation logic here)
    return AnalysisOutputV2(...)
```

## Deterministic Execution

### Seed Management

```python
from saaaaaa.utils.deterministic_execution import DeterministicSeedManager

# Initialize with base seed
seed_manager = DeterministicSeedManager(base_seed=42)

# Scoped seed for operation
with seed_manager.scoped_seed("analysis_operation") as seed:
    # All random operations use this seed
    import random
    value = random.random()  # Deterministic!

# Seed automatically restored after context
```

### Deterministic Decorator

```python
from saaaaaa.utils.deterministic_execution import DeterministicExecutor

executor = DeterministicExecutor(base_seed=42)

@executor.deterministic(operation_name="my_analysis")
def analyze_policy(text: str) -> float:
    """Analysis with automatic seed management and logging."""
    import random
    return random.random()  # Deterministic across runs!

# Each call is logged with latency, event_id, etc.
result = analyze_policy("policy text")
```

### UTC-Only Timestamps

```python
from saaaaaa.utils.deterministic_execution import enforce_utc_now
from saaaaaa.utils.enhanced_contracts import utc_now_iso

# Never use datetime.now() - always use UTC
utc_dt = enforce_utc_now()  # datetime with UTC timezone
utc_str = utc_now_iso()     # ISO-8601 string with 'Z' suffix

# Parse and validate UTC timestamps
from saaaaaa.utils.deterministic_execution import parse_utc_timestamp
dt = parse_utc_timestamp("2024-01-01T00:00:00Z")  # Enforces UTC
```

## Structured Logging

### Basic Usage

```python
from saaaaaa.utils.enhanced_contracts import StructuredLogger

logger = StructuredLogger("my_component")

# Log contract validation
logger.log_contract_validation(
    contract_type="AnalysisInputV2",
    correlation_id="550e8400-...",
    success=True,
    latency_ms=5.2,
    payload_size_bytes=1024,
    content_digest="abc123..."
)

# Log execution
logger.log_execution(
    operation="process_policy",
    correlation_id="550e8400-...",
    success=True,
    latency_ms=123.4,
    input_size=1024,
    output_size=2048
)
```

### Output Format

```json
{
  "event": "contract_validation",
  "contract_type": "AnalysisInputV2",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "success": true,
  "latency_ms": 5.2,
  "payload_size_bytes": 1024,
  "content_digest": "abc123...",
  "timestamp_utc": "2024-01-01T00:00:00Z"
}
```

## Error Handling

### Domain-Specific Exceptions

```python
from saaaaaa.utils.enhanced_contracts import (
    ContractValidationError,
    DataIntegrityError,
    FlowCompatibilityError,
    SystemConfigError
)

# Contract violation
try:
    input_data = AnalysisInputV2(text="", ...)  # Empty text
except ValidationError as e:
    raise ContractValidationError(
        "Text field cannot be empty",
        field="text"
    ) from e

# Data integrity error
expected_hash = "abc123..."
actual_hash = compute_content_digest(data)
if expected_hash != actual_hash:
    raise DataIntegrityError(
        "Content hash mismatch",
        expected=expected_hash,
        got=actual_hash
    )

# Flow compatibility error
if required_field not in producer_output:
    raise FlowCompatibilityError(
        f"Missing required field: {required_field}",
        producer="stage_a",
        consumer="stage_b"
    )

# System configuration error
if not config_file.exists():
    raise SystemConfigError(
        "Configuration file not found",
        config_key="questionnaire_path"
    )
```

### Event ID Tracking

All exceptions include reproducible `event_id` for debugging:

```python
try:
    process_data(...)
except ContractValidationError as e:
    print(f"Error ID: {e.event_id}")
    # Log with event_id for correlation
    logger.error(f"[{e.event_id}] Validation failed: {e}")
```

## Flow Compatibility Validation

### Between Pipeline Stages

```python
from saaaaaa.utils.contract_adapters import validate_flow_compatibility

# Stage 1: Preprocessor
preprocessor_output = {
    "text": "normalized text",
    "document_id": "DOC-123",
    "sentences": ["Sentence 1.", "Sentence 2."]
}

# Validate before passing to Stage 2: Analyzer
validate_flow_compatibility(
    producer_output=preprocessor_output,
    consumer_expected_fields=["text", "document_id"],
    producer_name="preprocessor",
    consumer_name="analyzer"
)

# Stage 2: Analyzer (safe to use preprocessor_output)
analyzer_result = analyzer.analyze(**preprocessor_output)
```

### Full Pipeline Validation

```python
from saaaaaa.utils.contract_adapters import validate_pipeline_stage_io

validated_input, validated_output = validate_pipeline_stage_io(
    stage_name="policy_analysis",
    input_contract=AnalysisInputV2,
    output_contract=AnalysisOutputV2,
    actual_input=input_data,
    actual_output=output_data
)
```

## Best Practices

### 1. Always Use Factory Methods

```python
# ✓ Good: Auto-computes digest and payload size
input_data = AnalysisInputV2.create_from_text(
    text="policy text",
    document_id="DOC-123",
    policy_unit_id="PDM-001"
)

# ✗ Bad: Manual digest computation can be error-prone
input_data = AnalysisInputV2(
    text="policy text",
    input_digest="...",  # Easy to get wrong
    payload_size_bytes=len("policy text")
)
```

### 2. Validate Early and Often

```python
def process_stage(input_data: Any) -> AnalysisOutputV2:
    # Validate input contract at entry
    if not isinstance(input_data, AnalysisInputV2):
        raise ContractValidationError("Invalid input type")
    
    # Process...
    result = do_work(input_data)
    
    # Validate output contract before return
    if not isinstance(result, AnalysisOutputV2):
        raise ContractValidationError("Invalid output type")
    
    return result
```

### 3. Use Adapters for Gradual Migration

```python
# Maintain V1 interface while using V2 internally
def v1_compatible_process(v1_input: dict) -> dict:
    v2_input = adapt_analysis_input_v1_to_v2(v1_input, "PDM-001")
    v2_output = internal_v2_process(v2_input)
    return v2_to_v1_dict(v2_output)
```

### 4. Log Structured Events

```python
# ✓ Good: Structured JSON logging
logger.log_execution(
    operation="analyze",
    correlation_id=input_data.correlation_id,
    success=True,
    latency_ms=10.5
)

# ✗ Bad: Ad-hoc print statements
print("Analysis complete")  # No structure, no correlation
```

### 5. Handle Errors with Event IDs

```python
# ✓ Good: Domain-specific exception with event ID
try:
    validate_contract(data)
except ValidationError as e:
    raise ContractValidationError(
        "Validation failed",
        field="data"
    ) from e  # Auto-generates event_id

# ✗ Bad: Generic exception
raise ValueError("Validation failed")  # No event_id for tracking
```

## Testing with V2 Contracts

### Unit Tests

```python
import pytest
from saaaaaa.utils.contracts import AnalysisInputV2

def test_analysis_input_validation():
    """Test V2 contract validation."""
    
    # Valid input
    valid_input = AnalysisInputV2.create_from_text(
        text="test text",
        document_id="DOC-1",
        policy_unit_id="PDM-001"
    )
    assert len(valid_input.input_digest) == 64  # SHA-256
    
    # Invalid input (empty text)
    with pytest.raises(ValidationError):
        AnalysisInputV2.create_from_text(
            text="",  # Empty not allowed
            document_id="DOC-1",
            policy_unit_id="PDM-001"
        )
```

### Integration Tests

```python
def test_pipeline_flow():
    """Test full pipeline with V2 contracts."""
    
    # Stage 1: Preprocessing
    preprocessor = Preprocessor("PDM-001")
    processed = preprocessor.process(raw_text="...")
    assert isinstance(processed, ProcessedTextV2)
    
    # Stage 2: Analysis
    analyzer = Analyzer("PDM-001")
    analysis_input = AnalysisInputV2.create_from_text(
        text=processed.normalized_text,
        document_id="DOC-1",
        policy_unit_id="PDM-001"
    )
    result = analyzer.analyze(analysis_input)
    assert isinstance(result, AnalysisOutputV2)
    
    # Validate flow compatibility
    validate_flow_compatibility(
        processed.model_dump(),
        ["normalized_text"],
        "preprocessor",
        "analyzer"
    )
```

## Migration Checklist

- [ ] Review V1 code and identify all contract usage
- [ ] Install V2 contract modules
- [ ] Add domain-specific exceptions to error handling
- [ ] Replace `print()` with structured logging
- [ ] Add deterministic seed management to stochastic operations
- [ ] Convert timestamps to UTC-only
- [ ] Add `policy_unit_id` to all operations
- [ ] Compute and validate content digests
- [ ] Add flow compatibility validation between stages
- [ ] Update unit tests for V2 contracts
- [ ] Run integration tests
- [ ] Validate with pipeline verification script

## Support and Documentation

- **Enhanced Contracts Module**: `src/saaaaaa/utils/enhanced_contracts.py`
- **Contract Adapters**: `src/saaaaaa/utils/contract_adapters.py`
- **Deterministic Execution**: `src/saaaaaa/utils/deterministic_execution.py`
- **Legacy V1 Contracts**: `src/saaaaaa/utils/contracts.py` (maintained for compatibility)

For questions or issues, refer to the in-script tests in each module for working examples.
