# Path Management & Portability Guide

## Overview

This document describes the path management system in SAAAAAA, designed to ensure cross-platform compatibility (Linux, macOS, Windows), security, and deterministic behavior.

## Core Principles

1. **No Absolute Paths**: All paths are relative to the project root
2. **No sys.path Manipulation**: Use proper package imports
3. **Use pathlib.Path**: Never use `os.path` functions
4. **Validate All Paths**: Use validation utilities before I/O operations
5. **Controlled Write Locations**: Write only to designated directories
6. **Security First**: Prevent path traversal attacks

## Path Utilities Module

All path operations should use utilities from `saaaaaa.utils.paths`:

```python
from saaaaaa.utils.paths import (
    proj_root,      # Project root directory
    src_dir,        # Source code directory
    data_dir,       # Data directory
    tmp_dir,        # Temporary files
    build_dir,      # Build artifacts
    cache_dir,      # Cache files
    reports_dir,    # Generated reports
    safe_join,      # Safe path joining with traversal protection
    is_within,      # Check path containment
    validate_read_path,   # Validate before reading
    validate_write_path,  # Validate before writing
)
```

## Usage Examples

### Reading Files

```python
from saaaaaa.utils.paths import proj_root, validate_read_path

# Good: Relative to project root
config_path = proj_root() / "config" / "settings.yaml"
validate_read_path(config_path)
with open(config_path) as f:
    config = yaml.safe_load(f)

# Bad: Absolute path
config_path = Path("/home/user/project/config/settings.yaml")  # ❌
```

### Writing Files

```python
from saaaaaa.utils.paths import build_dir, validate_write_path

# Good: Write to build directory
output_path = build_dir() / "results" / "output.json"
output_path.parent.mkdir(parents=True, exist_ok=True)
validate_write_path(output_path)
with open(output_path, "w") as f:
    json.dump(data, f)

# Bad: Write to source tree
output_path = src_dir() / "generated.py"  # ❌ Raises error
validate_write_path(output_path)  # Raises ValueError
```

### Temporary Files

```python
from saaaaaa.utils.paths import tmp_dir
from pathlib import Path

# Good: Use project tmp directory
tmp = tmp_dir()
temp_file = tmp / "processing_12345.tmp"

# Better: Use tempfile module with tmp_dir as base
import tempfile
with tempfile.TemporaryDirectory(dir=tmp_dir()) as tmpdir:
    temp_file = Path(tmpdir) / "data.tmp"
    # Automatic cleanup when context exits
```

### User-Provided Paths (Security)

```python
from saaaaaa.utils.paths import tmp_dir, safe_join, PathTraversalError

# Good: Protect against traversal
base_dir = tmp_dir() / "uploads"
user_filename = request.get("filename")  # From user input

try:
    safe_path = safe_join(base_dir, user_filename)
    # safe_path is guaranteed to be within base_dir
except PathTraversalError:
    # User tried "../../../etc/passwd" or similar
    raise ValueError("Invalid filename")

# Bad: Direct concatenation
unsafe_path = base_dir / user_filename  # ❌ No traversal protection
```

### Package Resources

```python
from saaaaaa.utils.paths import resources, PathNotFoundError

# Good: Access packaged resources
try:
    config_path = resources("saaaaaa.core", "config", "defaults.yaml")
    with open(config_path) as f:
        defaults = yaml.safe_load(f)
except PathNotFoundError:
    # Resource not found or not properly packaged
    raise
```

## Directory Structure

```
project_root/
├── src/              # Source code (read-only in production)
│   └── saaaaaa/
├── data/             # Data files (may be read-write)
├── tests/            # Test files
├── scripts/          # Utility scripts
├── tmp/              # Temporary files (gitignored)
├── build/            # Build artifacts (gitignored)
│   ├── cache/        # Cache files
│   └── reports/      # Generated reports
└── pyproject.toml    # Project marker file
```

## Environment Variables

The system supports environment variables for customization:

- `FLUX_WORKDIR`: Override project root (default: auto-detected)
- `FLUX_TMPDIR`: Override temp directory (default: `{project}/tmp`)
- `FLUX_REPORTS`: Override reports directory (default: `{project}/build/reports`)

```python
from saaaaaa.utils.paths import get_workdir, get_tmpdir, get_reports_dir

# These respect environment variables
workdir = get_workdir()
tmpdir = get_tmpdir()
reports = get_reports_dir()
```

## Security Features

### Path Traversal Protection

The `safe_join()` function prevents directory traversal attacks:

```python
from saaaaaa.utils.paths import safe_join, PathTraversalError

base = proj_root() / "data"

# These are safe
safe_join(base, "subfolder", "file.txt")  # ✅
safe_join(base, "sub", "..", "file.txt")  # ✅ Resolves to base/file.txt

# These raise PathTraversalError
safe_join(base, "..", "..", "etc", "passwd")  # ❌
safe_join(base, "/absolute/path")  # ❌
```

### Write Protection

By default, writing to the source tree is prohibited:

```python
from saaaaaa.utils.paths import src_dir, validate_write_path

src_file = src_dir() / "saaaaaa" / "core" / "generated.py"

# This raises ValueError
validate_write_path(src_file)

# Allow only when explicitly needed (e.g., code generation)
validate_write_path(src_file, allow_source_tree=True)
```

## Testing

### Run Path Tests

```bash
# Run all path tests
make test-paths

# Or with pytest directly
pytest tests/paths/ -v
```

### Multi-Platform Testing

Tests run on Linux, macOS, and Windows in CI to verify:

- Path separator handling (/ vs \\)
- Unicode normalization (NFC vs NFD)
- Long path support (Windows ~260 char limit)
- Case sensitivity differences

## Path Audit

### Run the Audit

```bash
# Generate audit report
make audit-paths

# View results
cat PATHS_AUDIT.md
```

The audit scans all Python files and reports:

- **Critical**: sys.path manipulation in production code
- **High**: Absolute paths, hardcoded temp directories
- **Medium**: `Path.cwd()` usage, `os.path` functions
- **Low**: Informational warnings

### Quality Gates

CI enforces these rules:

- ✅ Zero critical path issues
- ✅ No sys.path manipulation outside scripts/tests/examples
- ✅ Path tests pass on Linux, macOS, and Windows
- ✅ No hardcoded absolute paths in production code

## Migration Guide

### From os.path to pathlib

```python
# Before
import os
path = os.path.join(base, "subdir", "file.txt")
dirname = os.path.dirname(path)
exists = os.path.exists(path)

# After
from pathlib import Path
path = Path(base) / "subdir" / "file.txt"
dirname = path.parent
exists = path.exists()
```

### From __file__ to proj_root()

```python
# Before
from pathlib import Path
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent
config_file = project_root / "config" / "settings.yaml"

# After
from saaaaaa.utils.paths import proj_root
config_file = proj_root() / "config" / "settings.yaml"
```

### From Path.cwd() to proj_root()

```python
# Before
from pathlib import Path
config = Path.cwd() / "config.yaml"

# After
from saaaaaa.utils.paths import proj_root
config = proj_root() / "config.yaml"
```

## Common Patterns

### Script Initialization

```python
#!/usr/bin/env python3
"""Script description."""

from saaaaaa.utils.paths import proj_root, tmp_dir, reports_dir

def main():
    # All paths relative to project root
    input_file = proj_root() / "data" / "input.csv"
    output_dir = reports_dir() / "analysis"
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process...
```

### Test Setup

```python
import pytest
from saaaaaa.utils.paths import tmp_dir

@pytest.fixture
def temp_workspace(tmp_path):
    """Provide a temporary workspace for testing."""
    # Use pytest's tmp_path or our tmp_dir()
    workspace = tmp_dir() / "test_workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    yield workspace
    # Cleanup (if not using pytest's tmp_path)
    shutil.rmtree(workspace)
```

### Data Pipeline

```python
from saaaaaa.utils.paths import data_dir, cache_dir, reports_dir, validate_read_path, validate_write_path

def process_data():
    # Input from data directory
    input_path = data_dir() / "raw" / "dataset.csv"
    validate_read_path(input_path)
    
    # Cache intermediate results
    cache_path = cache_dir() / "processed_data.pkl"
    validate_write_path(cache_path)
    
    # Final output to reports
    output_path = reports_dir() / "final_report.pdf"
    validate_write_path(output_path)
```

## Troubleshooting

### "PathNotFoundError: Resource not found"

Resources must be declared in `pyproject.toml`:

```toml
[tool.setuptools.package-data]
saaaaaa = ["config/*.yaml", "data/*.json"]
```

Or use `MANIFEST.in` for additional files:

```
include src/saaaaaa/config/*.yaml
include src/saaaaaa/data/*.json
```

### "PathTraversalError: Path traversal detected"

This is a security feature. If you need to access paths outside the workspace:

1. Verify the use case is legitimate
2. Use absolute paths explicitly (not recommended)
3. Or adjust the base directory for `safe_join()`

### "Cannot write to source tree"

This is intentional. Write outputs to:

- `build_dir()` for build artifacts
- `cache_dir()` for cache files
- `reports_dir()` for reports
- `tmp_dir()` for temporary files

If you must write to source (e.g., code generation):

```python
validate_write_path(path, allow_source_tree=True)
```

## Best Practices

1. ✅ Always use `pathlib.Path` instead of string paths
2. ✅ Use path utilities from `saaaaaa.utils.paths`
3. ✅ Validate paths before I/O operations
4. ✅ Use `safe_join()` for user-provided path components
5. ✅ Write to designated directories (build, cache, reports, tmp)
6. ✅ Use `resources()` for packaged data files
7. ✅ Test on multiple platforms (Linux, macOS, Windows)
8. ❌ Never use absolute paths
9. ❌ Never use `sys.path.append()` or `.insert()`
10. ❌ Never use `os.path` functions
11. ❌ Never use `Path.cwd()` for project-relative paths
12. ❌ Never write to the source tree without explicit permission

## References

- [Python pathlib documentation](https://docs.python.org/3/library/pathlib.html)
- [importlib.resources documentation](https://docs.python.org/3/library/importlib.resources.html)
- Path audit report: `PATHS_AUDIT.md`
- Test suite: `tests/paths/`
- Utilities: `src/saaaaaa/utils/paths.py`
