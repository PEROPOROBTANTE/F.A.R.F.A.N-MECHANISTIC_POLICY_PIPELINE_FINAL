# Wiring Architecture - Modo Wiring Fino

## Overview

The SAAAAAA wiring system implements **modo wiring fino** (fine-grained wiring mode), providing explicit, contract-validated connections between all system modules. This architecture ensures deterministic initialization, complete observability, and zero tolerance for silent failures.

## Design Principles

### 1. No Graceful Degradation
The system either satisfies declared contract conditions in full or aborts with explicit, diagnosable failure semantics. Partial delivery, fallback heuristics, "best effort" responses, and silent substitutions are **forbidden**.

### 2. No Strategic Simplification
Simplification is **never** employed to pass validation gates or accelerate approval. Complexity is a first-class design asset when it increases fidelity, control, explainability, or strategic leverage.

### 3. State-of-the-Art Baseline
All implementations begin from current research-grade paradigms. Legacy approaches require explicit justification.

### 4. Deterministic Reproducibility
All transformations must be repeatable. Non-determinism is isolated, controlled, or eliminated.

### 5. Explicitness Over Assumption
All transformations declare preconditions, invariants, and postconditions. Implicit coercions and lenient parsing are disallowed.

### 6. Observability as Structure
Tracing, logging, and metrics are built into the wiring, not added as decoration.

## Architecture Components

### Core Modules

#### 1. Ports (`src/saaaaaa/core/ports.py`)
Protocol definitions for all system interfaces:
- `PortCPPIngest`: CPP ingestion interface
- `PortCPPAdapter`: CPP to PreprocessedDocument adapter
- `PortSignalsClient`: Signal fetching interface
- `PortSignalsRegistry`: Signal registry interface
- `PortArgRouter`: Argument routing interface
- `PortExecutor`: Executor interface
- `PortAggregate`: Aggregation interface
- `PortScore`: Scoring interface
- `PortReport`: Reporting interface

#### 2. Contracts (`src/saaaaaa/core/wiring/contracts.py`)
Pydantic models defining deliverables and expectations for each link:
- `CPPDeliverable` → `AdapterExpectation`
- `PreprocessedDocumentDeliverable` → `OrchestratorExpectation`
- `ArgRouterPayloadDeliverable` → `ArgRouterExpectation`
- `SignalPackDeliverable` → `SignalRegistryExpectation`
- And more...

#### 3. Errors (`src/saaaaaa/core/wiring/errors.py`)
Typed error classes with prescriptive fix instructions:
- `WiringContractError`: Contract violation between links
- `MissingDependencyError`: Required dependency unavailable
- `ArgumentValidationError`: Argument routing failure
- `SignalUnavailableError`: Signal service unavailable
- `SignalSchemaError`: Invalid signal pack schema
- `WiringInitializationError`: Bootstrap failure

#### 4. Feature Flags (`src/saaaaaa/core/wiring/feature_flags.py`)
Typed, environment-driven configuration:
- `use_cpp_ingestion: bool` (default: True)
- `enable_http_signals: bool` (default: False)
- `allow_threshold_override: bool` (default: False)
- `wiring_strict_mode: bool` (default: True)
- `enable_observability: bool` (default: True)
- `enable_metrics: bool` (default: True)
- `deterministic_mode: bool` (default: True)

#### 5. Validation (`src/saaaaaa/core/wiring/validation.py`)
Contract validation for all i→i+1 links:
- Link validators with metrics tracking
- Deterministic hashing (BLAKE3)
- Prescriptive error messages
- Success rate monitoring

#### 6. Bootstrap (`src/saaaaaa/core/wiring/bootstrap.py`)
Deterministic initialization engine:
- Sequential initialization phases
- Dependency injection via constructors
- Signal system setup (memory:// or HTTP)
- CoreModuleFactory creation
- ArgRouter initialization
- Hash computation for drift detection

#### 7. Observability (`src/saaaaaa/core/wiring/observability.py`)
OpenTelemetry instrumentation:
- Span creation for each link operation
- Structured logging with structlog
- Latency tracking
- Error attribution
- Dynamic attribute support

## Initialization Order

The bootstrap sequence follows a strict deterministic order:

### Phase 1: Load Resources
```python
provider = QuestionnaireResourceProvider(data)
```
- Loads questionnaire monolith JSON
- Extracts patterns, validations, indicators
- No IO at import time

### Phase 2: Build Signal System
```python
signal_client = SignalClient(base_url="memory://")
signal_registry = SignalRegistry(max_size=100, ttl_s=3600)
```
- Creates in-memory signal source (default)
- Optional HTTP client with circuit breaker
- LRU cache with TTL management
- Seeds initial signals

### Phase 3: Create Executor Config
```python
executor_config = ExecutorConfig(
    temperature=0.0,  # Deterministic
    seed=0,
)
```
- Typed configuration with defaults
- No YAML files
- Environment variable support

### Phase 4: Create Factory with DI
```python
factory = CoreModuleFactory(
    questionnaire_data=data,
    signal_registry=registry,
)
```
- Dependency injection for all 19 module classes
- Constructor-based injection
- No singleton pattern

### Phase 5: Build Class Registry
```python
class_registry = build_class_registry()
```
- Maps class names to types
- Used by ArgRouter for method dispatch

### Phase 6: Initialize ArgRouter
```python
arg_router = ExtendedArgRouter(class_registry)
```
- ≥30 special routes
- Strict validation (no silent drops)
- **kwargs awareness

### Phase 7: Create Validator
```python
validator = WiringValidator()
```
- Validates all i→i+1 contracts
- Computes deterministic hashes
- Tracks validation metrics

### Phase 8: Seed Signals (Memory Mode)
```python
for area in ["fiscal", "salud", "ambiente", ...]:
    pack = SignalPack(version="1.0.0", policy_area=area, ...)
    memory_source.register(area, pack)
    registry.put(area, pack)
```
- Seeds initial signals for policy areas
- Ensures immediate availability

### Phase 9: Compute Hashes
```python
init_hashes = {
    "provider": blake3(provider_keys),
    "registry": blake3(registry_metrics),
    "router": blake3(router_data),
}
```
- Deterministic hashes for drift detection
- Used for validating reproducibility

## Wiring Links and Contracts

### Link 1: CPP Ingestion → CPP Adapter

**Deliverable Contract (CPPDeliverable):**
- `chunk_graph`: Complete chunk graph
- `policy_manifest`: Policy metadata
- `provenance_completeness`: Must be 1.0
- `schema_version`: CPP schema version

**Expectation Contract (AdapterExpectation):**
- Requires valid chunk_graph
- Requires policy_manifest
- Enforces provenance_completeness == 1.0

**Validation:**
```python
validator.validate_cpp_to_adapter(cpp_data)
```

**Failure Mode:**
```
WiringContractError: Contract violation in link 'cpp->adapter'
Expected: CPPDeliverable with provenance_completeness=1.0
Received: CPP with provenance_completeness=0.5
Fix: Ensure ingestion pipeline completes successfully
```

### Link 2: CPP Adapter → Orchestrator

**Deliverable Contract (PreprocessedDocumentDeliverable):**
- `sentence_metadata`: Non-empty list of sentences
- `resolution_index`: Chunk resolution index
- `provenance_completeness`: 1.0
- `document_id`: Non-empty string

**Expectation Contract (OrchestratorExpectation):**
- Requires sentence_metadata with ≥1 entry
- Requires non-empty document_id

**Validation:**
```python
validator.validate_adapter_to_orchestrator(doc_data)
```

### Link 3: Orchestrator → ArgRouter

**Deliverable Contract (ArgRouterPayloadDeliverable):**
- `class_name`: Target class name
- `method_name`: Target method name
- `payload`: Method arguments

**Expectation Contract (ArgRouterExpectation):**
- Class must exist in registry
- Method must exist on class
- Payload must contain required args

**Validation:**
```python
validator.validate_orchestrator_to_argrouter(payload_data)
```

### Link 4: ArgRouter → Executors

**Deliverable Contract (ExecutorInputDeliverable):**
- `args`: Tuple of positional arguments
- `kwargs`: Dict of keyword arguments
- `method_signature`: For validation

**Validation:**
```python
validator.validate_argrouter_to_executors(input_data)
```

**ArgRouter Behavior:**
- ≥30 special routes with known signatures
- Strict validation: No silent parameter drops
- **kwargs support for forward compatibility
- Metrics: `silent_drop_count` must be 0

### Link 5: SignalsClient → SignalRegistry

**Deliverable Contract (SignalPackDeliverable):**
- `version`: Non-empty semantic version
- `policy_area`: Policy domain
- `patterns`: Text patterns (optional)
- `indicators`: KPIs (optional)

**Expectation Contract (SignalRegistryExpectation):**
- Requires version field
- Requires policy_area field

**Validation:**
```python
validator.validate_signals_to_registry(signal_data)
```

**Signal Semantics:**
- `None` return = 304 Not Modified OR circuit breaker open
- Registry uses LRU eviction + TTL
- Memory mode: `memory://` (default)
- HTTP mode: Optional, with circuit breaker

### Link 6: Executors → Aggregate

**Deliverable Contract (EnrichedChunkDeliverable):**
- `chunk_id`: Chunk identifier
- `used_signals`: Signals used during execution
- `enrichment`: Enrichment data

**Expectation Contract (AggregateExpectation):**
- `enriched_chunks`: ≥1 enriched chunk

**Validation:**
```python
validator.validate_executors_to_aggregate(chunks_data)
```

### Link 7: Aggregate → Score

**Deliverable Contract (FeatureTableDeliverable):**
- `table_type`: "pyarrow.Table"
- `num_rows`: ≥1
- `column_names`: Required columns

**Expectation Contract (ScoreExpectation):**
- Must be pa.Table type
- Must have required columns

**Validation:**
```python
validator.validate_aggregate_to_score(table_data)
```

### Link 8: Score → Report

**Deliverable Contract (ScoresDeliverable):**
- `dataframe_type`: "polars.DataFrame"
- `num_rows`: ≥1
- `metrics_computed`: List of computed metrics

**Expectation Contract (ReportExpectation):**
- Must be pl.DataFrame type
- Metrics must be present
- Manifest must be provided

**Validation:**
```python
validator.validate_score_to_report(scores_data)
```

## Observability

### OpenTelemetry Spans

Every wiring operation creates a span:

```python
with trace_wiring_link("cpp->adapter", document_id=doc_id) as attrs:
    result = adapter.convert(cpp)
    attrs["chunk_count"] = len(result.chunks)
```

**Span Attributes:**
- `link`: Link name
- `document_id`: Document identifier
- `latency_ms`: Operation latency
- `ok`: Success/failure boolean
- `fingerprint`: Data fingerprint
- `error_type`: Error type (if failed)
- `error_message`: Error message (if failed)

### Structured Logging

All operations log with structlog:

```python
logger.info(
    "wiring_link_complete",
    link="cpp->adapter",
    latency_ms=123.45,
    ok=True,
    document_id="doc123",
)
```

### Metrics

Validators track metrics:
- `validation_count`: Total validations
- `failure_count`: Failed validations
- `success_rate`: Success rate [0.0, 1.0]

Registry tracks metrics:
- `hit_rate`: Cache hit rate
- `size`: Current cache size
- `hits`: Total hits
- `misses`: Total misses
- `evictions`: Total evictions

## Feature Flags

### Environment Variables

```bash
export SAAAAAA_USE_CPP_INGESTION=true
export SAAAAAA_ENABLE_HTTP_SIGNALS=false
export SAAAAAA_ALLOW_THRESHOLD_OVERRIDE=false
export SAAAAAA_WIRING_STRICT_MODE=true
export SAAAAAA_ENABLE_OBSERVABILITY=true
export SAAAAAA_ENABLE_METRICS=true
export SAAAAAA_DETERMINISTIC_MODE=true
```

### Flag Validation

Flags are validated for conflicts:

```python
flags = WiringFeatureFlags.from_env()
warnings = flags.validate()
# Returns warnings for incompatible combinations
```

**Warning Examples:**
- HTTP + deterministic mode: May cause non-determinism
- Strict mode disabled: Not recommended for production
- No observability/metrics: Debugging will be difficult

## CI Validation

### Validation Script

Run comprehensive validation:

```bash
./scripts/validate_wiring_system.py
```

**Checks:**
1. Bootstrap initialization
2. ArgRouter coverage (≥30 routes)
3. Signal hit rate (≥0.95 in memory mode)
4. Determinism (stable hashes)
5. No YAML in executors
6. Type checking (pyright/mypy)

### CI Gates

These validations must pass before merge:
- `wiring_contracts_ok == True`
- `argrouter_coverage >= 30`
- `signals.hit_rate > 0.95` (memory mode)
- `determinism_check == PASS`
- `no_yaml_in_executors == True`
- `type_check_strict == PASS`

### Wiring Checklist

Generated at `WIRING_CHECKLIST.json`:

```json
{
  "factory_instances": 19,
  "argrouter_routes": 30,
  "signals_mode": "memory",
  "used_signals_present": true,
  "contracts": {
    "cpp->adapter": "ok",
    "adapter->orchestrator": "ok",
    "orchestrator->argrouter": "ok",
    "argrouter->executors": "ok",
    "signals": "ok",
    "executors->aggregate": "ok",
    "aggregate->score": "ok",
    "score->report": "ok"
  },
  "hashes": {
    "provider": "abc123...",
    "registry": "def456...",
    "router": "ghi789..."
  }
}
```

## Error Handling

### Policy: Fail Loud

On contract violation:
1. **Stop execution immediately**
2. **Emit WiringContractError** with:
   - Link name
   - Expected schema
   - Received schema
   - Failed field
   - **Prescriptive fix**
3. **Do not continue downstream**

### Error Examples

```python
WiringContractError: Contract violation in link 'cpp->adapter'
Expected: CPPDeliverable
Received: dict
Field: provenance_completeness
Fix: Ensure CPP ingestion pipeline completes successfully.
```

```python
MissingDependencyError: Missing dependency 'questionnaire.json' required by 'WiringBootstrap'
Fix: Ensure questionnaire file exists at /path/to/questionnaire.json
```

## Testing

### Core Tests (`tests/test_wiring_core.py`)

23 tests covering:
- Contract model validation
- Error class behavior
- Feature flag configuration
- Link validation
- Deterministic hashing
- Observability instrumentation

### E2E Tests (`tests/test_wiring_e2e.py`)

Integration tests covering:
- Full bootstrap initialization
- Memory mode signal flow
- Contract validation across all links
- Determinism guarantees
- Error handling with prescriptive messages

### Running Tests

```bash
# Core tests (no heavy dependencies)
pytest tests/test_wiring_core.py -v

# E2E tests (requires full stack)
pytest tests/test_wiring_e2e.py -v

# All wiring tests
pytest tests/test_wiring*.py -v
```

## Usage

### Basic Bootstrap

```python
from saaaaaa.core.wiring.bootstrap import WiringBootstrap
from saaaaaa.core.wiring.feature_flags import WiringFeatureFlags

# Configure flags
flags = WiringFeatureFlags(
    use_cpp_ingestion=True,
    enable_http_signals=False,  # Memory mode
    deterministic_mode=True,
)

# Bootstrap system
bootstrap = WiringBootstrap(
    questionnaire_path="data/questionnaire.json",
    flags=flags,
)

components = bootstrap.bootstrap()

# Access components
provider = components.provider
signal_registry = components.signal_registry
factory = components.factory
arg_router = components.arg_router
validator = components.validator
```

### Contract Validation

```python
from saaaaaa.core.wiring.validation import WiringValidator

validator = WiringValidator()

# Validate CPP → Adapter
cpp_data = {
    "chunk_graph": {"chunks": {}},
    "policy_manifest": {},
    "provenance_completeness": 1.0,
    "schema_version": "2.0",
}
validator.validate_cpp_to_adapter(cpp_data)

# Get metrics
metrics = validator.get_all_metrics()
summary = validator.get_summary()
```

### Observability

```python
from saaaaaa.core.wiring.observability import trace_wiring_link

with trace_wiring_link("custom->link", document_id="doc123") as attrs:
    result = perform_operation()
    attrs["result_size"] = len(result)
```

## Future Enhancements

1. **Dynamic Route Discovery**: Auto-detect methods for ArgRouter
2. **Contract Versioning**: Support multiple contract versions
3. **Distributed Tracing**: Full OpenTelemetry export
4. **Performance Budgets**: Per-link latency budgets
5. **Hot Reload**: Dynamic signal updates without restart
6. **Contract Evolution**: Backward-compatible contract changes

## References

- Problem Statement: See root `PROBLEM_STATEMENT_VERIFICATION.md`
- Port Interfaces: `src/saaaaaa/core/ports.py`
- Contract Models: `src/saaaaaa/core/wiring/contracts.py`
- Bootstrap Engine: `src/saaaaaa/core/wiring/bootstrap.py`
- Tests: `tests/test_wiring_*.py`
