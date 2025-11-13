# Orchestrator Excellence Runbook

This document provides the complete verification runbook for the SAAAAAA orchestrator system, implementing the comprehensive excellence checklist for Python orchestrators.

## Quick Start

To run all verification checks in one command:

```bash
make verify
```

## Complete Verification Pipeline

The verification pipeline runs 10 sequential checks, each building on the previous:

### Step 1: Bytecode Compilation
**Command**: `python -m compileall -q core orchestrator executors`

**Purpose**: Validates Python syntax and detects syntax errors before runtime.

**Success Criteria**: All `.py` files compile without errors.

---

### Step 2: Core Purity Scanner (AST Analysis)
**Command**: `python tools/scan_core_purity.py`

**Purpose**: Static AST analysis ensuring core modules:
- Have no `__main__` blocks (entry points belong in `examples/` or `orchestrator/`)
- Perform no direct I/O operations (no `open()`, `json.load()`, `pandas.read_*`, etc.)
- Remain pure library code with no side effects

**Success Criteria**: Zero violations detected in `core/` modules.

**Violations Detected**:
- `if __name__ == "__main__"` blocks
- Calls to `open()`, `json.load()`, `json.dump()`, `requests.*`, `pandas.read_*`

---

### Step 3: Import Linter (Layer Contracts)
**Command**: `lint-imports --config contracts/importlinter.ini`

**Purpose**: Enforces architectural boundaries through dependency direction rules:
- Core modules cannot import from orchestrator
- Maintains layered architecture: `orchestrator → processors → executors → core`

**Success Criteria**: All layer contracts satisfied.

**Configuration**: See `contracts/importlinter.ini`

---

### Step 4: Ruff Linting
**Command**: `ruff check core orchestrator executors tests tools --quiet`

**Purpose**: Fast Python linting for:
- Code style violations (pycodestyle)
- Logic bugs (bugbear)
- Code simplification opportunities
- Type checking issues
- Unused imports/variables

**Configuration**: See `[tool.ruff]` in `pyproject.toml`

**Key Rules Enabled**:
- `E` - pycodestyle errors
- `F` - pyflakes
- `B` - flake8-bugbear
- `I` - isort (import sorting)
- `ANN` - type annotations
- `UP` - pyupgrade

---

### Step 5: Mypy Type Checking
**Command**: `mypy core orchestrator executors --config-file pyproject.toml`

**Purpose**: Static type checking in strict mode to catch:
- Type inconsistencies
- Missing type annotations
- Invalid type operations
- Interface contract violations

**Configuration**: See `[tool.mypy]` in `pyproject.toml`

**Strict Mode Features**:
- `disallow_untyped_defs = true`
- `disallow_any_unimported = true`
- `disallow_any_generics = true`
- `warn_return_any = true`
- `strict = true`

---

### Step 6: Grep Boundary Checks
**Command**: `python tools/grep_boundary_checks.py`

**Purpose**: Text-pattern-based verification of architectural boundaries:
1. **No orchestrator imports in core/executors**
   - Detects: `import orchestrator` or `from orchestrator import`
   - Ensures: Dependency flows orchestrator → core, never reverse

2. **No provider calls in core/executors**
   - Detects: `get_questionnaire_provider()` calls
   - Ensures: Only orchestrator accesses data providers

3. **No JSON I/O in core**
   - Detects: `open(*.json` patterns
   - Ensures: I/O operations stay in orchestrator layer

**Success Criteria**: Zero boundary violations detected.

---

### Step 7: Pycycle (Circular Dependency Detection)
**Command**: `pycycle --here core orchestrator executors`

**Purpose**: Detects circular import dependencies at the module level.

**Success Criteria**: No circular dependencies found.

**Note**: Circular dependencies cause:
- Import failures
- Initialization order issues
- Difficult-to-debug runtime errors

---

### Step 8: Bulk Import Test
**Command**: `python tools/import_all.py`

**Purpose**: Attempts to import every module in `core.`, `executors.`, and `orchestrator.` packages to surface:
- Hidden import errors
- Missing dependencies (reported separately)
- Module initialization issues
- Circular dependencies (runtime detection)

**Success Criteria**: All modules import without errors (missing external dependencies are noted but don't fail the check).

**Key Features**:
- Distinguishes between architecture errors and missing dependencies
- Adds `src/` to path for development environments
- Provides detailed traceback for import failures

---

### Step 9: Bandit Security Scan
**Command**: `bandit -q -r core orchestrator executors -f txt`

**Purpose**: Static security analysis detecting:
- Hardcoded passwords/secrets
- Use of insecure functions
- SQL injection vulnerabilities
- Command injection risks
- Insecure cryptography

**Success Criteria**: No high or medium severity issues in critical paths.

**Note**: Some warnings may be acceptable with justification.

---

### Step 10: Test Suite
**Command**: `pytest -q -ra tests/`

**Purpose**: Runs the complete test suite including:
- Unit tests
- Integration tests
- Contract tests (`test_boundaries.py`, `test_contract_snapshots.py`)
- Golden path tests (`test_orchestrator_golden.py`)
- Regression tests

**Key Test Files**:
- `tests/test_boundaries.py` - Architectural guardrails
- `tests/test_orchestrator_golden.py` - Contract verification
- `tests/test_contract_snapshots.py` - Schema stability
- `tests/test_regression_semantic_chunking.py` - Bug prevention

---

## Manual Verification Commands

Run individual checks as needed:

```bash
# 1. Compile bytecode
python -m compileall -q core orchestrator executors

# 2. Core purity check
python tools/scan_core_purity.py

# 3. Import linter
lint-imports --config contracts/importlinter.ini

# 4. Ruff linting
ruff check core orchestrator executors tests tools

# 5. Mypy type checking
mypy core orchestrator executors --config-file pyproject.toml

# 6. Grep boundary checks
python tools/grep_boundary_checks.py

# 7. Circular dependency detection
pycycle --here core orchestrator executors

# 8. Bulk import test
python tools/import_all.py

# 9. Security scan
bandit -r core orchestrator executors

# 10. Test suite
pytest -q -ra tests/

# 11. Coverage report (optional)
coverage run -m pytest && coverage report -m
```

## Architectural Guarantees

When all checks pass, the system guarantees:

### ✅ Compilation Guarantee
- No syntax errors
- All Python files compile to valid bytecode

### ✅ Import Guarantee
- No circular dependencies
- No missing imports (within the package)
- Clean module initialization

### ✅ Architectural Guarantee
- Dependency direction enforced (orchestrator → core)
- No I/O in core modules (pure library code)
- No `__main__` blocks in library code
- Runtime boundary enforcement via provider guards

### ✅ Type Guarantee
- Consistent type signatures
- No `Any` in public APIs (where enforced)
- Contract stability verified

### ✅ Security Baseline
- No obvious security vulnerabilities
- No hardcoded secrets
- Safe function usage

### ✅ Test Coverage
- Core orchestration paths tested
- Contract schemas locked
- Regression prevention in place

## CI/CD Integration

Add to your CI pipeline (e.g., `.github/workflows/verify.yml`):

```yaml
name: Verify

on: [push, pull_request]

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install ruff mypy import-linter pycycle bandit pytest pytest-cov
      - name: Run verification
        run: make verify
```

## Development Workflow

### Before Committing
```bash
# Quick check
make verify
```

### Before Creating PR
```bash
# Full verification with coverage
make verify
coverage run -m pytest
coverage report -m
```

### After Making Changes to Core
```bash
# Verify purity and boundaries
python tools/scan_core_purity.py
python tools/grep_boundary_checks.py
pytest tests/test_boundaries.py
```

### After Changing Contracts
```bash
# Verify contract stability
pytest tests/test_contract_snapshots.py
pytest tests/test_orchestrator_golden.py
```

## Troubleshooting

### Import Errors
**Issue**: `import_all.py` reports import errors

**Solutions**:
1. Check for circular imports with `pycycle`
2. Verify `__init__.py` files exist in all packages
3. Check `sys.path` includes repository root and `src/`
4. Install missing dependencies: `pip install -r requirements.txt`

### Boundary Violations
**Issue**: `grep_boundary_checks.py` or `scan_core_purity.py` report violations

**Solutions**:
1. Move I/O operations from `core/` to `orchestrator/`
2. Inject data from orchestrator instead of reading in core
3. Remove `__main__` blocks from library code
4. Move demos to `examples/` directory

### Type Errors
**Issue**: `mypy` reports type inconsistencies

**Solutions**:
1. Add explicit type annotations to function signatures
2. Use `TypedDict` for structured dictionaries
3. Import types under `if TYPE_CHECKING:` to avoid circular imports
4. Use `# type: ignore[specific-code]` only when necessary with justification

### Layer Violations
**Issue**: `import-linter` reports forbidden imports

**Solutions**:
1. Refactor code to respect dependency direction
2. Extract shared types to `core/contracts.py`
3. Use dependency injection instead of direct imports
4. Consider creating an adapter layer

## File Inventory

### Verification Tools
- `tools/scan_core_purity.py` - AST scanner for I/O and __main__
- `tools/import_all.py` - Bulk import verification
- `tools/grep_boundary_checks.py` - Pattern-based boundary checks
- `contracts/importlinter.ini` - Layer contract configuration

### Test Files
- `tests/test_boundaries.py` - Architectural guardrail tests
- `tests/test_orchestrator_golden.py` - Golden path contract tests
- `tests/test_contract_snapshots.py` - Schema stability tests
- `tests/test_regression_semantic_chunking.py` - Regression prevention

### Configuration
- `pyproject.toml` - Python version, mypy, ruff, pytest config
- `.python-version` - Python version lock (3.11.9)
- `requirements.txt` - Pinned dependencies
- `constraints.txt` - Transitive dependency locks
- `Makefile` - Verification commands

## References

- **Orchestrator Excellence Checklist**: See problem statement
- **Python Type Checking**: https://mypy.readthedocs.io/
- **Import Linter**: https://import-linter.readthedocs.io/
- **Ruff Linter**: https://docs.astral.sh/ruff/
- **Bandit Security**: https://bandit.readthedocs.io/
