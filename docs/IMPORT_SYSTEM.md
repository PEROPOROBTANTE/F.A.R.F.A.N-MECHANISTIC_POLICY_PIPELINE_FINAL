# F.A.R.F.A.N Import System - Paranoia Constructiva Edition

**Framework for Advanced Retrieval of Administrativa Narratives**

This document describes the deterministic, auditable, and portable import system for the F.A.R.F.A.N project.

## 🎯 Design Principles

1. **No Graceful Degradation**: Imports either succeed completely or fail loudly with actionable errors
2. **No Strategic Simplification**: Complexity is embraced when it increases fidelity and control
3. **State-of-the-Art as Baseline**: Modern patterns from research-grade paradigms
4. **Deterministic Reproducibility**: Same inputs always produce same outputs
5. **Explicitness Over Assumption**: All transformations declare preconditions and postconditions

## 📦 Compat Layer

The `saaaaaa.compat` package provides a compatibility and safety layer for all imports.

### Core Components

#### 1. Safe Imports (`safe_imports.py`)

Provides controlled import behavior with clear failure modes:

```python
from saaaaaa.compat import try_import, lazy_import

# Required import - fails immediately if missing
pyarrow = try_import("pyarrow", required=True, 
                     hint="Install core runtime")

# Optional import - returns None if missing, logs to stderr
httpx = try_import("httpx", required=False,
                   hint="Install extra 'http_signals' or use memory://")
if httpx is None:
    # Use memory:// fallback
    pass

# Alternative package fallback (e.g., Python version compatibility)
toml = try_import("tomllib", alt="tomli", required=True,
                  hint="Python<3.11 needs 'tomli'")

# Lazy loading for heavy modules (defers import until first use)
def process_data(df):
    polars = lazy_import("polars", hint="Install analytics extra")
    return polars.DataFrame(df)
```

**Functions:**
- `try_import(modname, *, required=False, hint="", alt=None)` - Safe import with fallback
- `lazy_import(modname, *, hint="")` - Deferred import with memoization
- `check_import_available(modname)` - Check without importing
- `get_import_version(modname)` - Get version without importing

#### 2. Lazy Dependencies (`lazy_deps.py`)

Pre-configured lazy loaders for heavy dependencies:

```python
from saaaaaa.compat import get_polars, get_torch

def analyze(data):
    pl = get_polars()  # Lazy-loaded on first call
    df = pl.DataFrame(data)
    return df.to_numpy()

def ml_inference(inputs):
    torch = get_torch()  # Lazy-loaded on first call
    tensor = torch.tensor(inputs)
    return model(tensor)
```

**Available lazy loaders:**
- `get_polars()` - Fast DataFrame library
- `get_pyarrow()` - Arrow format support
- `get_torch()` - Deep learning framework
- `get_tensorflow()` - Machine learning framework
- `get_transformers()` - NLP models
- `get_spacy()` - NLP processing
- `get_pandas()` - Data manipulation
- `get_numpy()` - Numerical computing

#### 3. Native Checks (`native_check.py`)

Platform-aware verification for C-extensions and system libraries:

```python
from saaaaaa.compat.native_check import (
    check_system_library,
    verify_native_dependencies,
    print_native_report,
)

# Check system library
result = check_system_library("zstd")
if not result.available:
    print(result.hint)  # Installation instructions

# Verify native dependencies for packages
results = verify_native_dependencies(["pyarrow", "polars"])

# Print comprehensive environment report
print_native_report()
```

#### 4. Version Compatibility

Automatic shimming for Python version differences:

```python
from saaaaaa.compat import tomllib  # tomllib (3.11+) or tomli (<3.11)
from saaaaaa.compat import resources_files  # importlib.resources API

# Load TOML file
with open("config.toml", "rb") as f:
    config = tomllib.load(f)

# Load resource files
data_files = resources_files("saaaaaa.data")
schema = data_files / "schema.json"
```

## 🔧 Optional Dependencies

Dependencies are organized into install extras:

```bash
# Core installation (required dependencies only)
pip install saaaaaa

# With analytics support (polars, pyarrow)
pip install saaaaaa[analytics]

# With ML support (torch, tensorflow)
pip install saaaaaa[ml]

# With NLP support (transformers, spacy)
pip install saaaaaa[nlp]

# With HTTP signals support
pip install saaaaaa[http_signals]

# Complete installation (all optional dependencies)
pip install saaaaaa[all]
```

## 🛠️ Equipment Scripts

Pre-flight checks to verify environment readiness:

```bash
# Run all equipment checks
make equip

# Individual checks
make equip-python    # Python version, packages, bytecode
make equip-native    # System libraries, C-extensions
make equip-compat    # Compat layer functionality
make equip-types     # Type stubs and py.typed marker
```

## 🔍 Import Auditing

Automated tools to detect import issues:

```bash
# Run all import audits
make audit-imports

# Individual audits
python scripts/audit_import_shadowing.py    # Local files shadowing stdlib
python scripts/audit_circular_imports.py    # Import cycles
python scripts/audit_import_budget.py       # Import-time performance
```

### Audit Gates (CI Integration)

These checks should block CI if they fail:

1. **Shadowing Gate**: No local files shadow stdlib or third-party packages
2. **Circular Import Gate**: No import cycles in any layer
3. **Import Budget Gate**: Critical modules import in ≤300ms
4. **Optional Integrity Gate**: Each optional import has tests with/without package

## 📝 Best Practices

### For Library Developers

1. **Always use absolute imports:**
   ```python
   # Good
   from saaaaaa.core.orchestrator import Orchestrator
   
   # Bad - avoid deep relative imports
   from ...core.orchestrator import Orchestrator
   ```

2. **Use future annotations:**
   ```python
   from __future__ import annotations
   
   def process(data: list[dict[str, Any]]) -> DataFrame:
       ...
   ```

3. **Lazy-load heavy dependencies:**
   ```python
   def heavy_operation():
       # Import inside function, not at module level
       torch = lazy_import("torch")
       return torch.tensor([1, 2, 3])
   ```

4. **Handle optional dependencies explicitly:**
   ```python
   from saaaaaa.compat import try_import
   
   httpx = try_import("httpx", required=False,
                      hint="Install extra 'http_signals'")
   
   def fetch_data(url):
       if httpx is None:
           # Fallback to memory:// or local cache
           return load_from_cache(url)
       return httpx.get(url)
   ```

5. **No import-time side effects:**
   ```python
   # Bad - runs at import time
   data = expensive_computation()
   
   # Good - deferred to explicit init
   data = None
   
   def init():
       global data
       data = expensive_computation()
   ```

### For Application Developers

1. **Install appropriate extras:**
   ```bash
   # Minimal installation for testing
   pip install saaaaaa
   
   # Full installation for production
   pip install saaaaaa[all]
   ```

2. **Run equipment checks before deployment:**
   ```bash
   make equip
   ```

3. **Monitor import-time budget:**
   ```bash
   python scripts/audit_import_budget.py
   ```

## 🚨 Error Messages

The import system provides actionable error messages:

### Missing Optional Dependency
```
[IMPORT] Failed 'httpx' (optional). Install extra 'http_signals' or set source=memory://
```

### Circular Import
```
Circular import detected: core.X <- utils.Y. Move import inside function or refactor dependency.
```

### Native Library Missing
```
pyarrow failed to import: missing libzstd. Install system package 'zstd' or use manylinux wheel >= X.Y
```

### Shadowing Detected
```
Local file 'json.py' shadows stdlib 'json'. Rename file to avoid import hijacking.
```

### Import-Time Network Access
```
Network access during import detected in module Z. Move IO to runtime (init function).
```

## 📊 Import Budget

Critical modules must import within 300ms budget:

| Module | Budget | Typical Time |
|--------|--------|--------------|
| `saaaaaa` | 300ms | ~50ms |
| `saaaaaa.core` | 300ms | ~80ms |
| `saaaaaa.processing` | 300ms | ~120ms |

Heavy dependencies are lazy-loaded:

| Package | Import Time | Lazy Loaded |
|---------|-------------|-------------|
| `polars` | 50-200ms | ✅ |
| `pyarrow` | 50-150ms | ✅ |
| `torch` | 500-1500ms | ✅ |
| `tensorflow` | 1000-3000ms | ✅ |
| `transformers` | 200-500ms | ✅ |

## 🔗 Platform Compatibility

The import system ensures compatibility across:

- **Linux**: manylinux2014, musllinux (Alpine)
- **macOS**: arm64 (Apple Silicon), x86_64 (Intel)
- **Windows**: win-amd64

Platform-specific considerations:
- System library paths (LD_LIBRARY_PATH, DYLD_*, PATH)
- CPU features (AVX, NEON)
- FIPS mode for cryptography
- Wheel compatibility tags

## 📚 References

- **PEP 420**: Implicit Namespace Packages
- **PEP 561**: Distributing and Packaging Type Information
- **PEP 517/518**: Build System Requirements
- [Import System Problem Statement](../IMPORT_AUDIT.md)
- [Equipment Scripts Documentation](../Makefile)
