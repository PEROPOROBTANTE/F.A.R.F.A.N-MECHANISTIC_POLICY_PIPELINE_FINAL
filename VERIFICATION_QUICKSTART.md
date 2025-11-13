# Verification Quick Start

## One-Command Verification

```bash
make verify
```

This runs all 10 verification steps in sequence. Expected time: ~30 seconds.

## Expected Output

```
=== Step 1: Bytecode Compilation ===
✓ Compilation successful

=== Step 2: Core Purity Scanner (AST anti-I/O and anti-__main__) ===
✓ Core purity verified

=== Step 3: Import Linter (Layer Contracts) ===
✓ Import contracts satisfied

=== Step 4: Ruff Linting ===
✓ Ruff checks passed

=== Step 5: Mypy Type Checking ===
(warnings expected without full package installation)

=== Step 6: Grep Boundary Checks ===
✓ Boundary checks passed

=== Step 7: Pycycle (Circular Dependency Detection) ===
✓ No circular dependencies

=== Step 8: Bulk Import Test ===
✓ Import test passed

=== Step 9: Bandit Security Scan ===
✓ Security scan completed

=== Step 10: Test Suite ===
(requires full package installation)

=== VERIFICATION COMPLETE ===
```

## Individual Checks

### Core Purity (no I/O in core modules)
```bash
python tools/scan_core_purity.py
```
Expected: `Core purity: OK`

### Boundary Violations (architectural rules)
```bash
python tools/grep_boundary_checks.py
```
Expected: `✓ All grep-based boundary checks passed`

### Import Verification (all modules loadable)
```bash
python tools/import_all.py
```
Expected: `Successfully imported X modules cleanly`

### Circular Dependencies
```bash
pycycle --here
```
Expected: `No worries, no cycles here!`

## Common Issues

### "No module named 'dotenv'"
**Cause**: Missing python-dotenv dependency  
**Impact**: Low (only affects orchestrator.settings)  
**Fix**: `pip install python-dotenv` or `pip install -r requirements.txt`

### "Cannot find implementation for saaaaaa"
**Cause**: Package not installed  
**Impact**: Medium (mypy and some tests affected)  
**Fix**: `pip install -e .` (installs package in editable mode)

### Ruff Reports Issues
**Cause**: Code style violations  
**Fix**: `ruff check --fix .` (auto-fix most issues)

### Import-Linter Fails
**Cause**: Architectural boundary violation  
**Impact**: High (breaks dependency rules)  
**Fix**: Refactor code to respect layer boundaries

## Before Committing

Run these three critical checks:

```bash
# 1. Core purity
python tools/scan_core_purity.py

# 2. Boundaries
python tools/grep_boundary_checks.py

# 3. Full verification
make verify
```

If all pass: ✅ Ready to commit!

## Architecture Rules

### ✅ Allowed
- `orchestrator/` imports from `core/`
- `orchestrator/` performs I/O operations
- `examples/` has `__main__` blocks

### ❌ Forbidden
- `core/` imports from `orchestrator/`
- `core/` performs direct I/O
- `core/` has `__main__` blocks
- `executors/` imports from `orchestrator/`

## Tools Required

Install verification tools:
```bash
pip install ruff mypy import-linter pycycle bandit
```

Or with dev dependencies:
```bash
pip install -e ".[dev]"
```

## Documentation

- **Complete Guide**: `ORCHESTRATOR_EXCELLENCE_RUNBOOK.md`
- **Status Report**: `ORCHESTRATOR_EXCELLENCE_SUMMARY.md`
- **This Quick Start**: `VERIFICATION_QUICKSTART.md`

## Help

If verification fails and you're unsure why:

1. Read the error message carefully
2. Check `ORCHESTRATOR_EXCELLENCE_RUNBOOK.md` troubleshooting section
3. Run individual checks to isolate the issue
4. Check if you need to install dependencies

## Success Criteria

All core checks (Steps 1-8) should pass without errors:
- ✅ Compilation
- ✅ Core purity
- ✅ Import contracts
- ✅ Ruff linting
- ✅ Boundary checks
- ✅ No circular dependencies
- ✅ Import test
- ✅ Security scan

Steps 5 and 10 (mypy full, test suite) require full package installation.
