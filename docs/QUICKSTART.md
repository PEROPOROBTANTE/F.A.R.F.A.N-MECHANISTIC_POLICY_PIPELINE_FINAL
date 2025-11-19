# F.A.R.F.A.N Quick Start Guide

## Framework for Advanced Retrieval of Administrativa Narratives

### TL;DR - For Developers

F.A.R.F.A.N is a mechanistic policy pipeline for Colombian development plan analysis. This repository follows strict build hygiene practices. Here's what you need to know:

## Setup (First Time)

### Quick Automated Setup (Recommended)

```bash
# Method 1: Using Makefile (simplest - installs dependencies and package)
make install

# Method 2: Using setup script (includes SpaCy models)
bash scripts/setup.sh
```

**Using `make install` will:**
1. Install all Python dependencies from requirements.txt
2. Install the saaaaaa package in editable mode (required for imports to work)

**Using `bash scripts/setup.sh` will:**
1. Install all Python dependencies from requirements.txt
2. Install the saaaaaa package in editable mode (required for imports to work)
3. Download required SpaCy language models (es_core_news_lg, es_dep_news_trf)
4. Verify the installation

### Manual Setup

```bash
# 1. Ensure you have Python 3.12.x
python --version  # Should show 3.12.x

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install SpaCy models
python -m spacy download es_core_news_lg
python -m spacy download es_dep_news_trf

# 4. Copy environment template
cp .env.example .env

# 5. Install the package in editable mode (required)
pip install -e .

# 6. Verify setup
python scripts/verify_dependencies.py
```

**📖 See also:**
- [DEPENDENCY_SETUP.md](DEPENDENCY_SETUP.md) - Complete dependency installation guide
- [IMPORT_RESOLUTION_SUMMARY.md](IMPORT_RESOLUTION_SUMMARY.md) - Import fixes and troubleshooting

## Key Rules

### ✓ Python Version
- **Use Python 3.12.x only** (specified in `.python-version`)
- Don't change the version without team discussion

### ✓ Dependencies
- **Never use wildcards** (`*`) or open ranges (`>=`, `~=`) in requirements.txt
- Always pin to exact versions: `package==1.2.3`
- Update both `requirements.txt` AND `constraints.txt`

### ✓ Running Code
```bash
# Good - use -m flag
python -m saaaaaa.core.module_name

# Good - after pip install -e .
from saaaaaa.core import module_name

# Bad - don't manipulate PYTHONPATH
export PYTHONPATH=/path/to/src  # ❌ NO!
```

### ✓ Configuration
- Configuration lives in `orchestrator/settings.py`
- **Only orchestrator code** should import settings
- Core modules should receive config as parameters

```python
# In orchestrator - OK ✓
from orchestrator.settings import settings

# In core modules - NO ✗
# Don't import settings here, use dependency injection
```

### ✓ Package Structure
- Every directory must have `__init__.py`
- Before creating new packages, ensure they follow the structure

## Directory Layout

```
SAAAAAA/
├── orchestrator/      # Orchestration (reads settings)
├── executors/         # Execution engines  
├── contracts/         # API contracts
├── core/             # (in src/saaaaaa/core/) Core logic
├── tests/            # Tests
├── tools/            # Utilities
└── examples/         # Examples
```

## Common Tasks

### Adding a New Dependency
```bash
# 1. Add to requirements.txt with exact version
echo "new-package==1.2.3" >> requirements.txt

# 2. Add to constraints.txt
echo "new-package==1.2.3" >> constraints.txt

# 3. Install
pip install -r requirements.txt -c constraints.txt

# 4. Validate
python3 tools/validation/validate_build_hygiene.py
```

### Creating a New Package
```bash
# 1. Create directory
mkdir -p new_package

# 2. Add __init__.py
touch new_package/__init__.py

# 3. Validate
python3 tools/validation/validate_build_hygiene.py
```

### Running Tests
```bash
# After pip install -e .
pytest tests/

# Specific test file
pytest tests/test_something.py

# With coverage
pytest --cov=src/saaaaaa tests/
```

## Validation

Check if your setup is correct:
```bash
python3 tools/validation/validate_build_hygiene.py
```

All checks should pass ✓

## Need Help?

- Read `BUILD_HYGIENE.md` for comprehensive guide
- Read `CHECKLIST_SUMMARY.md` for implementation details
- Run validation script to identify issues

## Pre-commit Checklist

Before committing:
- [ ] All dependencies pinned to exact versions
- [ ] New packages have `__init__.py`
- [ ] No PYTHONPATH hacks
- [ ] Config changes only in orchestrator/
- [ ] Validation script passes

## Questions?

**Q: Why Python 3.12 specifically?**
A: For consistency and to use specific language features. All type checkers are configured for 3.12.

**Q: Why pin exact versions?**
A: Reproducibility. Everyone gets the same dependencies, no surprises.

**Q: Can I use `pip install` directly?**
A: Use `pip install -r requirements.txt -c constraints.txt` to ensure constraints are applied.

**Q: Why not use Poetry/Pipenv?**
A: This project uses traditional requirements.txt + constraints.txt for maximum compatibility.
