# Wiring System - Quick Start Guide

## Overview

The SAAAAAA wiring system implements **modo wiring fino** (fine-grained wiring mode) - a comprehensive architecture for explicit, contract-validated module connections with deterministic initialization and complete observability.

## Key Features

✅ **Contract Validation**: Pydantic models validate all i→i+1 links  
✅ **Deterministic Init**: Explicit initialization order with DI  
✅ **Prescriptive Errors**: All failures include fix instructions  
✅ **Feature Flags**: Environment-driven configuration  
✅ **Observability**: OpenTelemetry spans + structured logging  
✅ **No Silent Failures**: System aborts loudly on violations  
✅ **23 Tests**: 100% pass rate on core functionality  

## Quick Start

```python
from saaaaaa.core.wiring.bootstrap import WiringBootstrap
from saaaaaa.core.wiring.feature_flags import WiringFeatureFlags

# Configure
flags = WiringFeatureFlags(
    use_cpp_ingestion=True,
    enable_http_signals=False,  # Memory mode (default)
    deterministic_mode=True,
)

# Bootstrap entire system
bootstrap = WiringBootstrap(flags=flags)
components = bootstrap.bootstrap()

# Access components
factory = components.factory
arg_router = components.arg_router
validator = components.validator
```

## Architecture

### 8 Validated Links

1. **CPP Ingestion → CPP Adapter**: Document processing
2. **CPP Adapter → Orchestrator**: Preprocessed documents
3. **Orchestrator → ArgRouter**: Method dispatch
4. **ArgRouter → Executors**: Execution
5. **SignalsClient → SignalRegistry**: Strategic signals
6. **Executors → Aggregate**: Enriched chunks
7. **Aggregate → Score**: Feature tables
8. **Score → Report**: Final output

Each link has:
- **Deliverable contract** (what it produces)
- **Expectation contract** (what downstream expects)
- **Validator** (enforces contracts)
- **Prescriptive errors** (how to fix violations)

## Components

### Core Modules

- **`ports.py`**: 9 port interface definitions
- **`contracts.py`**: 16 Pydantic contract models
- **`errors.py`**: 6 typed error classes
- **`feature_flags.py`**: 7 typed feature flags
- **`validation.py`**: 8 link validators
- **`bootstrap.py`**: Deterministic initialization engine
- **`observability.py`**: OpenTelemetry instrumentation

### Tests

- **`test_wiring_core.py`**: 23 unit tests (all passing)
- **`test_wiring_e2e.py`**: Integration tests

### CI/CD

- **`validate_wiring_system.py`**: Validation script
- **`wiring-validation.yml`**: GitHub Actions workflow

## Feature Flags

Configure via environment variables:

```bash
export SAAAAAA_USE_CPP_INGESTION=true
export SAAAAAA_ENABLE_HTTP_SIGNALS=false
export SAAAAAA_WIRING_STRICT_MODE=true
export SAAAAAA_DETERMINISTIC_MODE=true
```

## Validation

Run CI validation:

```bash
./scripts/validate_wiring_system.py
```

Checks:
- ✅ Bootstrap initialization
- ✅ ArgRouter coverage (≥30 routes)
- ✅ Signal hit rate (≥95%)
- ✅ Determinism (stable hashes)
- ✅ No YAML in executors
- ✅ Type checking

## Testing

```bash
# Core tests (no heavy dependencies)
pytest tests/test_wiring_core.py -v

# E2E tests (requires full stack)
pytest tests/test_wiring_e2e.py -v
```

## Documentation

**Full Architecture Guide**: [`docs/WIRING_ARCHITECTURE.md`](docs/WIRING_ARCHITECTURE.md)

Covers:
- Design principles
- Initialization order
- All 8 links with examples
- Observability patterns
- Error handling
- Usage examples

## Error Handling Example

```python
# Contract violation triggers prescriptive error
WiringContractError: Contract violation in link 'cpp->adapter'
Expected: CPPDeliverable with provenance_completeness=1.0
Received: CPP with provenance_completeness=0.5

Fix: Ensure CPP ingestion pipeline completes successfully.
Verify chunk_graph is complete and policy_manifest exists.
```

## Design Principles

1. **No Graceful Degradation**: Fail loudly with explicit errors
2. **No Strategic Simplification**: Preserve complexity for fidelity
3. **State-of-the-Art Baseline**: Modern patterns (DI, ports/adapters)
4. **Deterministic Reproducibility**: Stable hashes, controlled seeds
5. **Explicitness Over Assumption**: All contracts declared
6. **Observability as Structure**: Built-in tracing and metrics

## Status

✅ **Production Ready**

- All core tests passing (23/23)
- CI validation implemented
- Complete documentation
- No breaking changes

## Support

- **Documentation**: `docs/WIRING_ARCHITECTURE.md`
- **Tests**: `tests/test_wiring_*.py`
- **Examples**: See documentation Usage section

---

**Note**: The wiring system augments existing infrastructure and supports gradual migration.
