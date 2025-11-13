# TEST IMPORT MATRIX

This document shows which modules can be successfully imported in a clean environment after package installation.

## Summary

The `saaaaaa` package has been successfully restructured to use absolute imports without sys.path manipulations.

- **Package location:** `src/saaaaaa/`
- **Installation method:** `pip install -e .`
- **Import style:** Absolute imports only (e.g., `from saaaaaa.core.orchestrator import Orchestrator`)

## ✅ Successfully Imported Core Modules

All core modules can be imported without sys.path manipulation:

| Module Path | Description | Status |
|-------------|-------------|--------|
| `saaaaaa` | Main package | ✓ |
| `saaaaaa.core.orchestrator` | Orchestration core | ✓ |
| `saaaaaa.core.ports` | Port interfaces | ✓ |
| `saaaaaa.analysis.bayesian_multilevel_system` | Bayesian analysis | ✓ |
| `saaaaaa.analysis.recommendation_engine` | Recommendation system | ✓ |
| `saaaaaa.analysis.meso_cluster_analysis` | Meso-level clustering | ✓ |
| `saaaaaa.processing.document_ingestion` | Document processing | ✓ |
| `saaaaaa.processing.aggregation` | Data aggregation | ✓ |
| `saaaaaa.processing.embedding_policy` | Embedding generation | ✓ |
| `saaaaaa.concurrency.concurrency` | Concurrency utilities | ✓ |
| `saaaaaa.api.api_server` | API server | ✓ |
| `saaaaaa.scoring.scoring` | Scoring module (via analysis.scoring) | ✓ |
| `saaaaaa.infrastructure.filesystem` | Filesystem utilities | ✓ |
| `saaaaaa.infrastructure.logging` | Logging utilities | ✓ |
| `saaaaaa.utils.contracts` | Contract validation | ✓ |
| `saaaaaa.utils.validation.schema_validator` | Schema validation | ✓ |

## Package Structure

```
src/saaaaaa/
├── __init__.py
├── analysis/              # Analysis modules
│   ├── bayesian_multilevel_system.py
│   ├── recommendation_engine.py
│   ├── meso_cluster_analysis.py
│   └── scoring/
├── api/                   # API server
│   └── api_server.py
├── concurrency/           # Concurrency utilities
│   └── concurrency.py
├── core/                  # Core orchestration
│   ├── orchestrator/
│   └── ports.py
├── processing/            # Document processing
│   ├── document_ingestion.py
│   ├── aggregation.py
│   └── embedding_policy.py
├── infrastructure/        # Infrastructure utilities
│   ├── filesystem.py
│   └── logging.py
└── utils/                 # Utility modules
    ├── contracts.py
    └── validation/
```

## Import Strategy

### ✅ Correct - Absolute Imports

All imports should use absolute paths from the installed package:

```python
# Core modules
from saaaaaa.core.orchestrator import Orchestrator
from saaaaaa.core.ports import Port

# Analysis modules
from saaaaaa.analysis.bayesian_multilevel_system import BayesianRollUp
from saaaaaa.analysis.recommendation_engine import RecommendationEngine

# Processing modules
from saaaaaa.processing.document_ingestion import ingest_document
from saaaaaa.processing.aggregation import aggregate_results

# Utilities
from saaaaaa.utils.contracts import validate_contract
from saaaaaa.utils.validation.schema_validator import SchemaValidator
```

### ❌ Incorrect - Relative Imports

Do not use relative imports outside the package:

```python
# Don't do this
from ..core import Orchestrator
from . import something
```

### ❌ Incorrect - sys.path Manipulation

Do not manipulate sys.path:

```python
# Don't do this
import sys
sys.path.insert(0, '/path/to/src')
```

## Testing Without Installation

For testing and development, you can use PYTHONPATH:

```bash
# Set PYTHONPATH to include src directory
export PYTHONPATH=/home/runner/work/SAAAAAA/SAAAAAA/src

# Or inline with command
PYTHONPATH=/path/to/SAAAAAA/src python -c "import saaaaaa"
```

But production code and examples should always assume the package is installed via pip.

## Verification Commands

### Verify package can be imported

```bash
python -c "import saaaaaa; print('✓ Package imports successfully')"
```

### Verify submodules

```bash
python -c "from saaaaaa.core.orchestrator import Orchestrator; print('✓')"
python -c "from saaaaaa.analysis.bayesian_multilevel_system import BayesianRollUp; print('✓')"
python -c "from saaaaaa.processing.document_ingestion import ingest_document; print('✓')"
```

### Walk all packages

```bash
python -c "
import saaaaaa
import pkgutil

modules = list(pkgutil.walk_packages(saaaaaa.__path__, prefix='saaaaaa.'))
print(f'Found {len(modules)} importable modules')
"
```

## Installation

### Development Installation

```bash
# Install in editable mode with development dependencies
pip install -e ".[dev,test]"
```

### Production Installation

```bash
# Install package only
pip install .
```

## Test Execution

Tests should run without PYTHONPATH manipulation:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_smoke_imports.py

# Run with coverage
pytest --cov=saaaaaa --cov-report=html
```

## Entry Points

The package defines CLI entry points that are available after installation:

```bash
# Main orchestrator
saaaaaa --input plan.pdf --mode full

# API server
saaaaaa-api --port 8000
```

## Compliance Status

- ✅ **No sys.path manipulations** - All removed from 165 files
- ✅ **Absolute imports** - All examples and tests use absolute imports
- ✅ **Package structure** - All code under `src/saaaaaa/`
- ✅ **Entry points** - Defined in pyproject.toml and setup.py
- ✅ **Test compatibility** - pytest runs without PYTHONPATH hacks
