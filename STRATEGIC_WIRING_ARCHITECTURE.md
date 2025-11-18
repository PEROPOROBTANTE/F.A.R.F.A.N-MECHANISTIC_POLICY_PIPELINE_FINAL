# Strategic Wiring Architecture

This document describes the high-level architecture and wiring of the SAAAAAA strategic files.

## Overview

The SAAAAAA system is built on a modular architecture with strategic high-level wiring files that provide compatibility layers and integration points between the core package (`src/saaaaaa`) and external interfaces.

## Strategic Files

### Core Strategic Files

1. **demo_macro_prompts.py** - Demo version of macro-level prompt builders
2. **verify_complete_implementation.py** - Verification script for complete implementation
3. **validation_engine.py** - Validation engine for scoring preconditions
4. **validate_system.py** - System-wide validation script
5. **seed_factory.py** - Deterministic seed generation factory
6. **qmcm_hooks.py** - QMCM (Quality Method Call Monitor) recorder hooks
7. **meso_cluster_analysis.py** - Meso-level cluster analysis functions
8. **macro_prompts.py** - Macro-level prompt builders and orchestrators
9. **json_contract_loader.py** - JSON contract document loader
10. **evidence_registry.py** - Immutable evidence registry with blockchain-like tracking
11. **document_ingestion.py** - Document ingestion pipeline
12. **scoring.py** - Scoring modalities for question results
13. **recommendation_engine.py** - Policy recommendation engine
14. **orchestrator.py** - Main orchestrator for SAAAAAA system
15. **micro_prompts.py** - Micro-level prompt builders
16. **coverage_gate.py** - Coverage enforcement gate for method counts

### Validation Strategic Files

17. **scripts/bootstrap_validate.py** - Bootstrap validation script for CI/CD
18. **validation/predicates.py** - Validation predicates for system checks
19. **validation/golden_rule.py** - Golden rule validator for immutability enforcement
20. **validation/architecture_validator.py** - Architecture validation for system structure

## Architecture Patterns

### Compatibility Wrapper Pattern

Most strategic files serve as compatibility wrappers that re-export functionality from the core `saaaaaa` package located in `src/saaaaaa`. This pattern provides:

- **Backward Compatibility**: External code can import from the root directory
- **Clean Separation**: Core implementation stays in `src/saaaaaa`
- **Easy Migration**: Gradual transition to package-based imports

Example:
```python
# validation_engine.py (wrapper)
from saaaaaa.utils.validation_engine import (
    ValidationEngine,
    ValidationReport,
)
```

### Package Structure

```
SAAAAAA/
├── src/saaaaaa/           # Core package
│   ├── core/             # Core orchestration logic
│   ├── analysis/         # Analysis modules
│   ├── processing/       # Processing pipelines
│   ├── utils/            # Utility modules
│   ├── concurrency/      # Concurrency support
│   └── controls/         # Control mechanisms
├── [strategic files]     # Compatibility wrappers
├── validation/           # Validation wrappers
└── scripts/              # Utility scripts
```

## Import Resolution

All consumers must install the project in editable mode:

```bash
pip install -e .
```

Once installed, invoke tools with `python -m ...` so the interpreter
resolves imports through the package metadata rather than via `PYTHONPATH`
hacks. This guarantees the same module graph locally and in CI.

## Provenance Tracking

All strategic files are tracked in `provenance.csv` with metadata including:
- Filename
- Purpose
- Creation date
- Last modified date
- Status

This ensures audit trail and traceability for all strategic components.

## Testing

Strategic wiring is validated through:
1. **Unit Tests**: `tests/test_strategic_wiring.py`
2. **Syntax Validation**: `tools/validate_strategic_files.py syntax`
3. **Provenance Validation**: `tools/validate_strategic_files.py provenance`
4. **Integration Validation**: `validate_strategic_wiring.py`

## Guarantees

The strategic wiring architecture provides:
- **AUDIT**: Full traceability via provenance tracking
- **ENSURE**: Comprehensive validation at all levels
- **FORCE**: Hard-fail on quality gates
- **GUARANTEE**: Determinism and immutability enforced
- **SUSTAIN**: Golden Rules compliance validated
