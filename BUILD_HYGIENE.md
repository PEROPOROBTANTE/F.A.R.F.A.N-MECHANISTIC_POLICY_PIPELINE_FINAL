# Build Hygiene and Structure

This document describes the build hygiene practices and structure enforced in this repository.

## Python Version

This project uses **Python 3.12.x** specifically. The version is pinned in:
- `.python-version` - for pyenv and similar tools
- `pyproject.toml` - requires-python = "~=3.12.0"
- All type checkers (mypy, pyright) are configured for Python 3.12

## Dependency Management

All dependencies are **strictly pinned** to exact versions:

- `requirements.txt` - All direct dependencies with exact versions (no `>=`, `~=`, or `*`)
- `constraints.txt` - Locks transitive dependencies to specific versions
- No open ranges or wildcards are allowed

To install dependencies:
```bash
pip install -r requirements.txt -c constraints.txt
```

## Repository Structure

The repository follows a clean, organized structure:

```
SAAAAAA/
├── orchestrator/        # Orchestration layer (reads settings.py)
│   ├── __init__.py
│   └── settings.py      # Centralized configuration
├── core/                # Core business logic (in src/saaaaaa/core/)
├── executors/           # Execution engines
├── tests/               # Test suite
├── tools/               # Utility tools
├── examples/            # Example usage
├── contracts/           # API contracts and interfaces
├── src/
│   └── saaaaaa/         # Main package source
├── .python-version      # Python version pin
├── pyproject.toml       # Project metadata and tool config
├── requirements.txt     # Pinned dependencies
├── constraints.txt      # Transitive dependency locks
├── setup.py             # Package setup
└── .env.example         # Environment template
```

### Package Requirements

All Python packages must have an `__init__.py` file, even if empty.

## PYTHONPATH Configuration

**Do not rely on PYTHONPATH hacks.** Instead:

1. **Development**: Install in editable mode from repository root:
   ```bash
   pip install -e .
   ```

2. **Running modules**: Use `-m` flag from repository root:
   ```bash
   python -m saaaaaa.core.module_name
   ```

3. **Testing**: pytest automatically handles paths when installed with `-e .`

4. **Verification**: `python tools/lint/check_pythonpath_references.py` ensures no new
   `PYTHONPATH` instructions are introduced. The `Path Compliance` GitHub workflow
   runs this lint plus the path audit and fixtures on every push.

## Centralized Configuration

Configuration is centralized in `orchestrator/settings.py`:

- Reads from `.env` file (use `.env.example` as template)
- Loads environment variables
- **Only orchestrator should import settings** - core modules remain config-agnostic
- Core modules receive configuration via dependency injection

### Using Configuration

```python
# In orchestrator code - OK
from orchestrator.settings import settings

# In core code - AVOID
# Do NOT import settings in core modules
# Instead, pass config as parameters
```

## Environment Setup

1. Copy environment template:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your settings (never commit `.env`)

3. Install package:
   ```bash
   pip install -e .
   ```

## Validation

To verify your setup follows these guidelines:

```bash
# Check Python version
python --version  # Should be 3.12.x

# Verify no wildcards in requirements
grep -E '\*|>=|~=' requirements.txt  # Should return nothing

# Verify all packages have __init__.py
find src -type d -exec sh -c 'if [ ! -f "$1/__init__.py" ]; then echo "Missing: $1/__init__.py"; fi' _ {} \;
```
