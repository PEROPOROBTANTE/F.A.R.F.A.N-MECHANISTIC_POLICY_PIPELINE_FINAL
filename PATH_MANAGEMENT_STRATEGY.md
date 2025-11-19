# Path Management Strategy for F.A.R.F.A.N

## Executive Summary

This document defines the **final, efficient, and optimal** path management strategy for the F.A.R.F.A.N project based on Python best practices and PEP standards.

## 1. Python Best Practices for Path Management

### 1.1 The Canonical Import Pattern (PEP 420, PEP 328)

**PRINCIPLE**: All application code MUST reside under `src/<package_name>/` to ensure:
- **Isolation**: Test imports don't accidentally use local files instead of installed package
- **Portability**: Package works identically in development and production
- **Clarity**: Absolute imports are unambiguous
- **Setuptools Compatibility**: `pip install -e .` works correctly

### 1.2 The src-layout Pattern (PyPA Recommended)

```
project_root/
├── src/
│   └── packagename/          # ALL application code here
│       ├── __init__.py
│       ├── module1.py
│       └── subpackage/
│           ├── __init__.py
│           └── module2.py
├── tests/                    # Test code (not in src)
├── scripts/                  # Utility scripts
├── docs/                     # Documentation
├── setup.py                  # Package metadata
└── pyproject.toml           # Build system config
```

**Why src-layout?**
1. **Import Protection**: Cannot accidentally import from working directory
2. **Editable Install Correctness**: `pip install -e .` behaves like production
3. **Namespace Clarity**: Package namespace is explicit
4. **Tool Compatibility**: Works with pytest, mypy, black, etc.

## 2. Current Problems in F.A.R.F.A.N

### 2.1 Root-Level Module Pollution

**CRITICAL VIOLATION**: Multiple root-level directories shadow the canonical `src/saaaaaa/`:

```
❌ WRONG (Current State):
/orchestrator/          # Shadows src/saaaaaa/core/orchestrator/
/calibration/           # Shadows src/saaaaaa/core/calibration/
/validation/            # Shadows src/saaaaaa/utils/validation/
/scoring/               # Shadows src/saaaaaa/scoring/
/contracts/             # Shadows src/saaaaaa/contracts.py
/core/                  # Shadows src/saaaaaa/core/
/concurrency/           # Shadows src/saaaaaa/concurrency/
/executors/             # Shadows src/saaaaaa/core/orchestrator/executors.py
```

**IMPACT**:
- Import ambiguity: `import orchestrator` vs `from saaaaaa.core import orchestrator`
- Path resolution issues: sys.path order determines which module loads
- Testing fragility: Tests may import wrong version
- Deployment confusion: Which files to package?

### 2.2 Mixed Import Styles

**OBSERVED**:
- ✅ Correct: `from saaaaaa.core.orchestrator import core`
- ❌ Wrong: `import orchestrator` (ambiguous - root or src?)
- ❌ Wrong: Relative imports crossing package boundaries

### 2.3 Absolute vs Relative Paths

**CURRENT STATE**:
- Some modules use absolute filesystem paths: `/home/user/...`
- Some use relative paths: `../../data/`
- Some use package-relative: `Path(__file__).parent.parent`

## 3. FINAL PATH MANAGEMENT STRATEGY

### 3.1 RULE 1: Single Source of Truth (src-layout)

```
✅ CORRECT (Target State):
src/saaaaaa/
├── __init__.py
├── core/
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── core.py
│   │   ├── executors.py
│   │   ├── factory.py
│   │   └── ...
│   ├── calibration/
│   │   ├── __init__.py
│   │   └── ...
│   └── wiring/
├── utils/
│   ├── validation/
│   │   ├── __init__.py
│   │   ├── schema_validator.py
│   │   ├── golden_rule.py
│   │   └── predicates.py
│   └── ...
├── analysis/
│   └── scoring/
├── processing/
├── infrastructure/
└── ...
```

**NO ROOT-LEVEL APPLICATION CODE**

### 3.2 RULE 2: Absolute Imports Only (PEP 8)

**ALWAYS**:
```python
from saaaaaa.core.orchestrator import core
from saaaaaa.utils.validation import schema_validator
from saaaaaa.processing.cpp_ingestion import CPPAdapter
```

**NEVER**:
```python
import orchestrator  # Ambiguous!
from ..utils import validation  # Fragile!
import sys; sys.path.append('../..')  # Evil!
```

**EXCEPTION**: Relative imports ONLY within same subpackage:
```python
# In src/saaaaaa/core/orchestrator/factory.py
from .executors import Executor  # OK - same subpackage
from ..calibration import engine  # OK - sibling subpackage
from ...utils import validation  # OK - cousin subpackage
```

### 3.3 RULE 3: Path Resolution via importlib.resources (PEP 420)

For data files, configs, etc.:

```python
# ✅ CORRECT: Package-relative resource access
from importlib.resources import files

def load_config():
    config_file = files('saaaaaa').joinpath('data/config.yaml')
    with config_file.open('r') as f:
        return yaml.safe_load(f)

# ✅ CORRECT: Runtime path construction
from pathlib import Path

def get_data_dir() -> Path:
    """Get project data directory (works in dev and production)."""
    # Option 1: Relative to package
    package_root = Path(__file__).parents[2]  # src/saaaaaa/utils/paths.py -> project_root
    return package_root / "data"

    # Option 2: Environment variable
    return Path(os.getenv('SAAAAAA_DATA_DIR', './data'))
```

**NEVER**:
```python
# ❌ WRONG: Hardcoded absolute path
data_dir = Path('/home/user/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE_/data')

# ❌ WRONG: Assumes CWD
data_dir = Path('data')  # Breaks if run from different directory
```

### 3.4 RULE 4: Configuration Over Convention

**Centralized path configuration**:

```python
# src/saaaaaa/config/paths.py
from pathlib import Path
from typing import Final
import os

# Project root (for development)
PROJECT_ROOT: Final[Path] = Path(__file__).parents[3]  # src/saaaaaa/config/paths.py -> root

# Data directories (configurable)
DATA_DIR: Final[Path] = Path(os.getenv('SAAAAAA_DATA_DIR', PROJECT_ROOT / 'data'))
OUTPUT_DIR: Final[Path] = Path(os.getenv('SAAAAAA_OUTPUT_DIR', PROJECT_ROOT / 'output'))
CACHE_DIR: Final[Path] = Path(os.getenv('SAAAAAA_CACHE_DIR', PROJECT_ROOT / '.cache'))

# Ensure directories exist
for dir_path in [DATA_DIR, OUTPUT_DIR, CACHE_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)
```

**Usage**:
```python
from saaaaaa.config.paths import DATA_DIR, OUTPUT_DIR

questionnaire_path = DATA_DIR / 'questionnaire_monolith.json'
report_path = OUTPUT_DIR / 'report.json'
```

## 4. OPTIMAL FOLDER ORGANIZATION

### 4.1 Principles of Optimal Python Package Structure

**REASON 1: Cohesion**
Files with related functionality must be grouped together. Reduces cognitive load and improves maintainability.

**REASON 2: Separation of Concerns**
Clear boundaries between layers (core logic, infrastructure, API, utils). Prevents circular dependencies.

**REASON 3: Discoverability**
Intuitive hierarchy allows developers to locate modules quickly. Follows principle of least surprise.

**REASON 4: Testability**
Structure enables easy mocking and testing. Tests mirror src structure.

**REASON 5: Scalability**
Supports growth without reorganization. New features fit into existing structure.

**REASON 6: Dependency Management**
Clear import paths reveal dependencies. Prevents tangled coupling.

### 4.2 Current Organization Assessment

| Principle | Current Grade | Issue |
|-----------|---------------|-------|
| Cohesion | ❌ F | Duplicates scatter related code |
| Separation of Concerns | ⚠️ D | Root modules violate boundaries |
| Discoverability | ⚠️ C | Ambiguous locations (3 scoring dirs!) |
| Testability | ✅ B | Tests are separate, but imports are fragile |
| Scalability | ❌ F | Adding features unclear where to put them |
| Dependency Management | ❌ F | Root modules create circular risks |

**OVERALL**: Requires immediate refactoring

### 4.3 Target Organization Structure

```
project_root/
├── src/
│   └── saaaaaa/
│       ├── __init__.py                      # Package root
│       │
│       ├── core/                            # Core business logic (no I/O)
│       │   ├── orchestrator/                # Main pipeline orchestration
│       │   │   ├── core.py                  # Main orchestrator
│       │   │   ├── executors.py             # Executor implementations
│       │   │   ├── factory.py               # Factory patterns
│       │   │   ├── questionnaire.py         # Questionnaire loader
│       │   │   └── signals.py               # Signal management
│       │   ├── calibration/                 # Calibration system
│       │   │   ├── orchestrator.py
│       │   │   ├── intrinsic_loader.py
│       │   │   └── layer_requirements.py
│       │   ├── wiring/                      # Dependency injection
│       │   │   └── bootstrap.py
│       │   └── contracts.py                 # Core contracts
│       │
│       ├── analysis/                        # Analysis algorithms
│       │   ├── scoring/                     # Scoring methods
│       │   │   └── scoring.py
│       │   ├── financiero_viabilidad_tablas.py
│       │   ├── contradiction_deteccion.py
│       │   └── recommendation_engine.py
│       │
│       ├── processing/                      # Data processing
│       │   ├── cpp_ingestion/               # CPP ingestion pipeline
│       │   │   ├── models.py
│       │   │   └── ...
│       │   ├── spc_ingestion/               # SPC ingestion
│       │   │   ├── converter.py
│       │   │   └── ...
│       │   ├── policy_processor.py
│       │   └── semantic_chunking_policy.py
│       │
│       ├── utils/                           # Utilities (reusable)
│       │   ├── validation/                  # Validation utilities
│       │   │   ├── schema_validator.py
│       │   │   ├── predicates.py
│       │   │   └── golden_rule.py
│       │   ├── determinism/                 # Determinism helpers
│       │   ├── cpp_adapter.py
│       │   ├── spc_adapter.py
│       │   └── paths.py                     # Path management
│       │
│       ├── infrastructure/                  # Infrastructure concerns
│       │   ├── logging.py
│       │   ├── caching.py
│       │   └── monitoring.py
│       │
│       ├── api/                             # External interfaces
│       │   ├── api_server.py                # REST API
│       │   ├── signals_service.py           # Signal service
│       │   └── static/                      # Static assets
│       │
│       ├── config/                          # Configuration
│       │   ├── paths.py                     # Centralized paths
│       │   └── settings.py                  # Global settings
│       │
│       ├── flux/                            # Flux management
│       ├── patterns/                        # Pattern matching
│       ├── audit/                           # Audit utilities
│       ├── controls/                        # Control systems
│       ├── concurrency/                     # Concurrency primitives
│       ├── optimization/                    # Optimization algorithms
│       └── observability/                   # Observability
│
├── tests/                                   # All tests (mirrors src structure)
│   ├── unit/                                # Unit tests
│   ├── integration/                         # Integration tests
│   ├── calibration/                         # Calibration tests
│   └── ...
│
├── scripts/                                 # Utility scripts (not part of package)
│   ├── canonical_flux_analyzer.py
│   └── ...
│
├── tools/                                   # Development tools
├── docs/                                    # Documentation
├── data/                                    # Data files (not in package)
├── examples/                                # Example usage
├── setup.py                                 # Package metadata
└── pyproject.toml                          # Build config
```

**KEY PRINCIPLES**:
1. **No root-level modules** (except setup.py, pyproject.toml, etc.)
2. **All code in src/saaaaaa/**
3. **Layered architecture**: core → analysis/processing → utils → infrastructure → api
4. **No circular dependencies**: Lower layers don't import from higher layers

## 5. Implementation Roadmap

### Phase 1: Consolidation (IMMEDIATE)

1. **Identify canonical versions** of duplicated modules
2. **Move root-level modules** into `src/saaaaaa/` at appropriate locations
3. **Update all imports** to use absolute `saaaaaa.*` imports
4. **Remove empty directories** after migration

### Phase 2: Path Standardization

1. **Create `src/saaaaaa/config/paths.py`** with centralized path configuration
2. **Replace all hardcoded paths** with references to paths.py
3. **Add environment variable support** for deployment flexibility
4. **Update all data/output access** to use Path objects

### Phase 3: Validation

1. **Run all tests** to ensure imports work
2. **Run import audits** (detect circular imports, missing __init__.py)
3. **Verify editable install**: `pip install -e .`
4. **Check production install**: `pip install dist/saaaaaa-*.whl`

### Phase 4: Enforcement

1. **Add import linter** rules to CI/CD
2. **Create pre-commit hooks** to prevent root-level code
3. **Add path validation** tests
4. **Update documentation** with import guidelines

## 6. Migration Script Strategy

The migration script will:

1. **Analyze** current structure (already done via canonical_flux_analyzer.py)
2. **Map** root-level modules to canonical locations in src/
3. **Backup** current state (git commit + tag)
4. **Move** files to canonical locations
5. **Update** imports in all files (AST-based rewriting)
6. **Update** tests to use new imports
7. **Verify** all tests pass
8. **Deprecate** old root-level directories (add deprecation warnings)
9. **Remove** after grace period

## 7. Success Criteria

- ✅ Zero root-level application modules
- ✅ All imports use `from saaaaaa.` pattern
- ✅ All tests pass with new structure
- ✅ `pip install -e .` works correctly
- ✅ No circular import errors
- ✅ All paths use centralized configuration
- ✅ CI/CD enforces path/import rules

## 8. References

- [PEP 8](https://peps.python.org/pep-0008/) - Style Guide for Python Code
- [PEP 328](https://peps.python.org/pep-0328/) - Imports: Multi-Line and Absolute/Relative
- [PEP 420](https://peps.python.org/pep-0420/) - Implicit Namespace Packages
- [PyPA Packaging Guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
- [Testing Your Python Package](https://blog.ionelmc.ro/2014/05/25/python-packaging/)
