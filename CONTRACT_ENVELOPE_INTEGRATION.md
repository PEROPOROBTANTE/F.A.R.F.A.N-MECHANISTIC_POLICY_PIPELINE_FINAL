# ContractEnvelope Integration Guide

## Overview

This guide shows how to integrate the new ContractEnvelope infrastructure with existing FLUX phases and executors.

## Quick Start

```python
from saaaaaa.utils.contract_io import ContractEnvelope
from saaaaaa.utils.determinism_helpers import deterministic
from saaaaaa.utils.json_logger import get_json_logger, log_io_event
from saaaaaa.utils.flow_adapters import wrap_payload, unwrap_payload
from saaaaaa.utils.domain_errors import DataContractError, SystemContractError
```

## Integration Pattern

### 1. FLUX Phase Integration

```python
import time
from saaaaaa.utils.contract_io import ContractEnvelope
from saaaaaa.utils.determinism_helpers import deterministic
from saaaaaa.utils.json_logger import get_json_logger, log_io_event

def run_normalize(cfg, ingest_del, *, policy_unit_id: str, correlation_id: str | None = None):
    """Phase with ContractEnvelope integration."""
    logger = get_json_logger("flux")
    started = time.monotonic()
    
    # Wrap input deliverable
    env_in = ContractEnvelope.wrap(
        ingest_del.model_dump(),
        policy_unit_id=policy_unit_id,
        correlation_id=correlation_id
    )
    
    # Execute with deterministic seeding
    with deterministic(policy_unit_id, correlation_id):
        # ... existing logic that produces norm_del ...
        norm_payload = norm_del.model_dump()
    
    # Wrap output
    env_out = ContractEnvelope.wrap(
        norm_payload,
        policy_unit_id=policy_unit_id,
        correlation_id=correlation_id
    )
    
    # Log I/O event
    log_io_event(
        logger,
        phase="normalize",
        envelope_in=env_in,
        envelope_out=env_out,
        started_monotonic=started
    )
    
    # Return both legacy and envelope for gradual migration
    return env_out  # or keep returning norm_del alongside env_out
```

### 2. Executor Deterministic Seeding

```python
from saaaaaa.utils.determinism_helpers import deterministic, create_deterministic_rng

class AdvancedDataFlowExecutor:
    def execute(self, doc, method_executor, policy_unit_id: str, correlation_id: str | None = None):
        """Execute with deterministic seeding."""
        
        # Enter deterministic context
        with deterministic(policy_unit_id, correlation_id) as seeds:
            # Use local RNG instead of global numpy.random
            rng = create_deterministic_rng(seeds.np)
            
            # Replace: np.random.choice(...) 
            # With: rng.choice(...)
            selected_path = rng.choice(available_paths, p=probabilities)
            
            # Continue with existing logic
            return super().execute(doc, method_executor)
```

### 3. Flow Compatibility Adapters

```python
from saaaaaa.utils.flow_adapters import wrap_payload, unwrap_payload

def consume_from_previous_stage(envelope: ContractEnvelope):
    """Extract payload from previous stage."""
    payload = unwrap_payload(envelope)
    
    # Validate expected fields
    if "normalized_text" not in payload:
        raise DataContractError("Missing 'normalized_text' from previous stage")
    
    return payload["normalized_text"]
```

### 4. Error Handling

```python
from saaaaaa.utils.domain_errors import DataContractError, SystemContractError

try:
    envelope = ContractEnvelope.wrap(payload, policy_unit_id="PDM-001")
except ValueError as e:
    # Contract validation failed
    raise DataContractError(f"Invalid payload: {e}") from e

try:
    config = load_config(path)
except FileNotFoundError as e:
    # System configuration error
    raise SystemConfigError(f"Config not found: {path}") from e
```

## Structured JSON Logging Output

When using `log_io_event()`, you'll see JSON logs like:

```json
{
  "level": "INFO",
  "logger": "flux.normalize",
  "message": "phase_io",
  "timestamp_utc": "2025-11-08T23:13:56.681494Z",
  "event_id": "88dffd408870a36a053852580f650918e4ac90d461dc678b44b1f4e56c7d1807",
  "correlation_id": "example-run-001",
  "policy_unit_id": "PDM-001",
  "phase": "normalize",
  "latency_ms": 7,
  "input_bytes": 165,
  "output_bytes": 185,
  "input_digest": "dcc9867430d0741a798d4c7b17e6e27105a41a5414bfa7cf40acbe6449249f74",
  "output_digest": "ec3e8d8100f86c2454323ca28c255dfb7a95971ccac23cb459621f3107bbbf59"
}
```

## Key Benefits

1. **Universal Metadata**: Every phase I/O carries schema_version, timestamp_utc, policy_unit_id, digests, event_id
2. **Centralized Determinism**: Single `deterministic()` context controls all random operations
3. **Structured Observability**: JSON logs with correlation tracking, no PII
4. **Flow Safety**: Adapters ensure compatibility between phases
5. **Clear Error Separation**: Data vs System errors via exception hierarchy

## Gradual Migration Strategy

### Phase 1: Add Envelope Alongside Existing
```python
def run_phase(...):
    # Existing code continues to work
    result = existing_logic()
    
    # Add envelope wrapping
    envelope = ContractEnvelope.wrap(result, policy_unit_id=..., correlation_id=...)
    
    # Return both for compatibility
    return result  # Old consumers still work
```

### Phase 2: Update Consumers to Use Envelope
```python
def next_phase(envelope: ContractEnvelope):
    # Extract payload
    payload = unwrap_payload(envelope)
    
    # Use metadata
    print(f"Processing {envelope.policy_unit_id} at {envelope.timestamp_utc}")
    
    # Continue processing
    ...
```

### Phase 3: Enforce Envelope-Only APIs
```python
def run_phase(...) -> ContractEnvelope:
    # Only return envelope
    return envelope
```

## Compatibility with Existing V2 Contracts

Both systems can coexist:

```python
# Use V2 Pydantic models for typed payloads
from saaaaaa.utils.contracts import AnalysisInputV2, AnalysisOutputV2

# Wrap in envelope for metadata
input_v2 = AnalysisInputV2.create_from_text(...)
envelope = ContractEnvelope.wrap(
    input_v2.model_dump(),
    policy_unit_id="PDM-001"
)

# Extract and validate
output_data = unwrap_payload(envelope)
output_v2 = AnalysisOutputV2.model_validate(output_data)
```

## Testing

All new modules include in-script tests:

```bash
# Test individual modules
python src/saaaaaa/utils/contract_io.py
python src/saaaaaa/utils/determinism_helpers.py
python src/saaaaaa/utils/json_logger.py
python src/saaaaaa/utils/domain_errors.py
python src/saaaaaa/utils/flow_adapters.py

# Run integration example
python examples/contract_envelope_integration_example.py
```

## Next Steps

1. **Wire into FLUX**: Update `saaaaaa/flux/phases.py` to use ContractEnvelope
2. **Update Executors**: Add `deterministic()` context in `executors.py`
3. **Add policy_unit_id**: Thread through pipeline entrypoints
4. **Replace prints**: Use `get_json_logger()` for all logging
5. **Verify**: Run `scripts/run_policy_pipeline_verified.py` with real PDFs

## Reference Implementation

See `examples/contract_envelope_integration_example.py` for a complete working example showing:
- Phase I/O wrapping
- Deterministic execution
- JSON logging
- Flow compatibility
- Determinism verification
