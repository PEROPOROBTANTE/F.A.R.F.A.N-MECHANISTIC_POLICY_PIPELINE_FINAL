# F.A.R.F.A.N Project Structure Documentation

**Framework for Advanced Retrieval of Administrativa Narratives**

This document explains the organization of the F.A.R.F.A.N repository.

## Directory Layout

### Source Code (`src/saaaaaa/`)

**This is where the actual implementation lives.** All new code should be added here.

```
src/saaaaaa/
├── core/
│   ├── orchestrator/      # Main orchestration engine
│   │   ├── core.py        # Core orchestrator logic
│   │   ├── choreographer.py  # Single micro-question execution
│   │   ├── executors.py   # Method executors
│   │   ├── factory.py     # Component factories
│   │   ├── evidence_registry.py  # Evidence tracking
│   │   ├── contract_loader.py   # Contract loading
│   │   └── arg_router.py  # Argument routing
│   ├── contracts.py       # Shared type contracts
│   └── ports.py           # Core ports/interfaces
├── concurrency/
│   └── concurrency.py     # Worker pool and task execution
├── analysis/              # Analysis components
├── processing/            # Processing pipelines
├── infrastructure/        # Infrastructure code
└── utils/                 # Utility functions
```

### Compatibility Shims (Root Level)

**These directories provide backward compatibility** for legacy imports. They are thin wrappers that redirect to the real implementation in `src/saaaaaa/`.

- **`orchestrator/`** - Compatibility shims for orchestrator imports
  - `__init__.py` - Main orchestrator compatibility layer
  - `choreographer_dispatch.py` - Dispatcher component shim
  - `executors.py`, `arg_router.py`, `factory.py` - Component shims
  - `provider.py`, `settings.py` - Configuration shims

- **`concurrency/`** - Compatibility shims for concurrency utilities
  - Redirects to `src/saaaaaa/concurrency/`

- **`core/`** - Compatibility shims for core contracts
  - Redirects to `src/saaaaaa/core/`

- **`executors/`** - Compatibility shims for executors
  - Redirects to `src/saaaaaa/core/orchestrator/executors`

### Root Level Files

- **`orchestrator.py`** - Legacy monolithic orchestrator compatibility shim
- **`*.py`** - Various standalone modules (aggregation, policy_processor, etc.)

### Other Directories

- **`tests/`** - Test suite
- **`examples/`** - Example code and demos
- **`scripts/`** - Utility scripts for validation and maintenance
- **`config/`** - Configuration files and schemas
- **`minipdm/`** - Mini project dependency manager (separate subproject)
- **`data/`** - Data files
- **`docs/`** - Documentation
- **`tools/`** - Development tools

## Why This Structure?

### Separation of Concerns

The `src/saaaaaa/` package contains the **canonical implementation** with proper type safety and architecture. The root-level compatibility shims allow **existing code to continue working** without modification.

### Migration Path

Old code can import from `orchestrator`, `concurrency`, etc. at the root level. New code should import from `saaaaaa.core.orchestrator`, `saaaaaa.concurrency`, etc. from the `src/` directory.

### Example Migration

**Old (still works):**
```python
from orchestrator import Orchestrator
from concurrency import WorkerPool
```

**New (preferred):**
```python
from saaaaaa.core.orchestrator import Orchestrator
from saaaaaa.core.orchestrator.choreographer import Choreographer
from saaaaaa.concurrency import WorkerPool
```

## Orchestration Components

All orchestration-related code is in **one place**: `src/saaaaaa/core/orchestrator/`

The confusing root-level `orchestrator/` directory is just a compatibility layer with multiple shims:
- `choreographer_dispatch.py` - Dispatcher component
- Redirects to the real source: `src/saaaaaa/core/orchestrator/choreographer.py`

## Adding New Features

1. **Always add new code to `src/saaaaaa/`** in the appropriate module
2. If backward compatibility is needed, add a shim at the root level
3. Update tests to use the new `src/saaaaaa/` imports when possible
4. Keep compatibility shims minimal (just imports/re-exports)

## Cleaning Up

To reduce confusion:
1. New code should NOT import from root-level shims
2. Tests should gradually migrate to `src/saaaaaa/` imports
3. The shims will eventually be deprecated once all code migrates
