# CI/CD Governance Pipeline

## Overview

This document describes the comprehensive CI/CD governance pipeline that acts as a "muralla" (wall) to ensure code quality and architectural integrity.

## Pipeline Steps

The pipeline executes the following steps **in strict order**, with fail-fast behavior:

### 1. Compile
- **Command**: `python -m compileall src/saaaaaa -f -q`
- **Purpose**: Verify all Python files compile without syntax errors
- **Failure**: Blocks merge if any file has syntax errors

### 2. AST Scanner
- **Purpose**: Enforce core module boundaries
- **Checks**:
  - **anti-__main__**: No `if __name__ == "__main__"` blocks in core modules
  - **anti-I/O**: No direct I/O operations in core modules
- **Tool**: `tools/scan_boundaries.py`
- **Failure**: Blocks merge if core modules violate boundaries

### 3. Import-linter
- **Purpose**: Enforce layer architecture contracts
- **Configuration**: `.importlinter`
- **Contracts**:
  1. Core modules cannot depend on API
  2. Core modules cannot depend on infrastructure
  3. Processing layer depends only on core
  4. Analysis layer depends on processing and core
- **Fallback**: Basic grep-based validation if import-linter not available
- **Failure**: Blocks merge if layer contracts are violated

### 4. Ruff
- **Command**: `ruff check . --config pyproject.toml`
- **Purpose**: Lint and bug detection
- **Configuration**: `pyproject.toml` [tool.ruff] section
- **Failure**: Blocks merge if linting issues found

### 5. Mypy --strict
- **Command**: `mypy --strict --config-file pyproject.toml src/saaaaaa`
- **Purpose**: Strict type checking
- **Configuration**: `pyproject.toml` [tool.mypy] section
- **Failure**: Blocks merge if type errors found

### 6. Pycycle
- **Purpose**: Circular dependency detection
- **Tool**: `pycycle --here src/saaaaaa` (primary)
- **Fallback**: `tools/detect_cycles.py` (custom implementation)
- **Failure**: Blocks merge if circular dependencies detected

### 7. Bulk Import
- **Purpose**: Verify all modules can be imported
- **Method**: Programmatically import all Python modules
- **Failure**: Blocks merge if any module fails to import

### 8. Pytest -q
- **Command**: `pytest -q`
- **Purpose**: Run all unit and integration tests
- **Configuration**: `pyproject.toml` [tool.pytest.ini_options] section
- **Failure**: Blocks merge if any test fails

### 9. Coverage Report
- **Command**: `pytest --cov=src/saaaaaa --cov-report=term-missing --cov-report=html`
- **Purpose**: Ensure adequate test coverage
- **Thresholds**:
  - **Orchestrator modules**: ≥ 80% coverage
  - **Contract modules**: ≥ 80% coverage
- **Artifacts**: HTML coverage report published
- **Failure**: Blocks merge if coverage below threshold

## Fail-Fast Behavior

The pipeline implements **fail on first red**:
- Each step must pass before the next step runs
- Any step failure immediately fails the entire job
- CI blocks merge if any step fails
- No partial successes are allowed

## Artifacts

The pipeline publishes the following artifacts (available for 30 days):

### pipeline-logs
- Core module violation reports (JSON)
- Coverage text report

### coverage-html-report
- Interactive HTML coverage report
- Detailed line-by-line coverage information

## Configuration Files

- **`.github/workflows/governance-pipeline.yml`**: Main workflow definition
- **`.importlinter`**: Layer contract definitions
- **`pyproject.toml`**: Tool configurations (ruff, mypy, pytest, coverage)
- **`tools/scan_boundaries.py`**: AST boundary scanner
- **`tools/detect_cycles.py`**: Circular dependency detector (fallback)

## Triggering the Pipeline

The pipeline runs on:
- **Pull requests**: All PRs to any branch
- **Push**: Commits to `main` or `develop` branches
- **Manual**: Via workflow_dispatch

## Local Testing

To run pipeline steps locally:

```bash
# Step 1: Compile
python -m compileall src/saaaaaa -f -q

# Step 2: AST Scanner
python tools/scan_boundaries.py --root src/saaaaaa/core --fail-on main,io

# Step 3: Import-linter
lint-imports  # or use basic validation

# Step 4: Ruff
ruff check . --config pyproject.toml

# Step 5: Mypy
mypy --strict --config-file pyproject.toml src/saaaaaa

# Step 6: Pycycle
python tools/detect_cycles.py src/saaaaaa

# Step 7: Bulk Import
# See workflow for Python script

# Step 8: Tests
pytest -q

# Step 9: Coverage
pytest --cov=src/saaaaaa --cov-report=term-missing --cov-report=html
```

## Dependencies

Required Python packages:
- mypy
- ruff
- pytest
- pytest-cov
- coverage
- import-linter (optional, has fallback)
- pycycle (optional, has fallback)

## Integration with Branch Protection

To enforce the governance pipeline:

1. Go to repository Settings → Branches
2. Add branch protection rule for `main` and `develop`
3. Enable "Require status checks to pass before merging"
4. Select "CI/CD Governance - All Steps" as required check
5. Enable "Require branches to be up to date before merging"

This ensures no code can be merged without passing all governance checks.
