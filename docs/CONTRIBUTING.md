# Contributing to F.A.R.F.A.N

## SIN_CARRETA Compliance

This project enforces **SIN_CARRETA** (Sistema de Importación No-Corrupto, Auditable, Reproducible, Rígido, Exacto, Trazable, Aislado) - a strict doctrine for deterministic, auditable Python imports.

### Core Principles

1. **NO `sys.path` manipulation** - EVER
2. **Only editable installs** - `pip install -e .`
3. **Package imports only** - `from saaaaaa.module import ...`
4. **Canonical structure** - Everything in its proper place

### Setup Requirements

**Non-Negotiable Installation Method:**

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install package in editable mode (REQUIRED)
pip install -e .

# 3. For development with all tools
pip install -e ".[dev]"

# 4. For complete installation with ML/Bayesian features
pip install -e ".[all]"
```

### What is FORBIDDEN

❌ **NEVER** use `sys.path.insert()` or `sys.path.append()`
❌ **NEVER** run scripts without installing the package first
❌ **NEVER** create compatibility wrappers at the root level
❌ **NEVER** import from relative paths like `../../src/`

### Repository Structure

```
SAAAAAA/
├── .github/          # CI/CD workflows
├── config/           # Static configuration
├── data/             # Raw input data
├── docs/             # Documentation
├── scripts/          # Operational scripts (run after pip install -e .)
├── src/
│   └── saaaaaa/      # THE installable Python package
│       ├── __init__.py
│       ├── core/
│       ├── processing/
│       ├── analysis/
│       └── ...
├── tests/            # Test suite
├── pyproject.toml    # Package metadata and dependencies
└── README.md
```

### Running Scripts

All scripts in `scripts/` must be run **after** installing the package:

```bash
# CORRECT
pip install -e .
python scripts/verify_pipeline.py

# WRONG - will fail with ImportError
python scripts/verify_pipeline.py  # without pip install -e .
```

### Running Tests

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=src/saaaaaa --cov-report=html
```

### Import Style

**Always use absolute imports from the installed package:**

```python
# CORRECT
from saaaaaa.core.orchestrator import Orchestrator
from saaaaaa.processing.aggregation import AggregationError
from saaaaaa.utils.contracts import BaseContract

# WRONG - these will not work
import sys
sys.path.insert(0, "../../src")  # FORBIDDEN
from orchestrator import Orchestrator  # No root-level compatibility wrappers
```

### CI Enforcement

The CI pipeline enforces SIN_CARRETA compliance:

- **Fail if `sys.path` manipulation detected** in src/, tests/, scripts/
- **Require `pip install -e .`** in all CI jobs
- **No compatibility wrappers** allowed at repository root

### Adding New Dependencies

1. Add to `pyproject.toml` under `dependencies` or `optional-dependencies`
2. Run `pip install -e .` or `pip install -e ".[dev]"` to install
3. **Never** manually edit `sys.path` as a workaround

### Test Obsolescence Protocol

Tests that rely on pre-normalization structure must be marked obsolete:

```python
import pytest

@pytest.mark.obsolete(reason="Relies on pre-normalization structure")
def test_old_import_pattern():
    # This test will be removed
    pass
```

### Questions?

See:
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [PATH_MANAGEMENT_GUIDE.md](PATH_MANAGEMENT_GUIDE.md) - Import system details
- [README.md](../README.md) - Main documentation

### Enforcement

**Violations of SIN_CARRETA will cause CI to fail.**

This is intentional. Clean, deterministic imports are non-negotiable for:
- **Reproducibility** - Same code, same environment, same results
- **Auditability** - Clear dependency graph, no hidden imports
- **Maintainability** - Standard Python packaging practices
- **Correctness** - No environment-dependent behavior
