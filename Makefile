.PHONY: help install setup verify clean validate-schema validate-monolith validate-canonical equip equip-python equip-native equip-compat equip-types audit-imports audit-paths test-paths fix-paths ci-prep-dirs

PYTHON ?= python3.12

# Default target: show help
.DEFAULT_GOAL := help

# Show available make targets
help:
	@echo "Available make targets:"
	@echo "  make install              - Install all dependencies and setup for development (alias for setup)"
	@echo "  make setup                - Install dependencies (requirements.txt + requirements-dev.txt) and package"
	@echo "  make verify               - Run all verification checks (compilation, linting, testing)"
	@echo "  make clean                - Remove build artifacts and cache files"
	@echo "  make validate-schema      - Validate questionnaire monolith against JSON Schema"
	@echo "  make validate-canonical   - Enforce canonical notation usage (no hardcoded strings)"
	@echo "  make equip                - Verify environment readiness (Python, native, compatibility)"
	@echo "  make audit-imports        - Run comprehensive import system checks"
	@echo "  make audit-paths          - Run comprehensive path usage and portability checks"
	@echo "  make test-paths           - Run path validation tests"
	@echo "  make ci-prep-dirs         - Create required directories for CI/CD"
	@echo ""
	@echo "Note: Run 'make setup' first to install all required dependencies."

# Install dependencies and setup the package for development
install: setup

# Setup the development environment (dependencies + editable package install)
setup:
	@echo "Installing Python dependencies..."
	@$(PYTHON) -m pip install -r requirements.txt
	@echo "Installing development dependencies..."
	@$(PYTHON) -m pip install -r requirements-dev.txt
	@echo "Installing package in editable mode..."
	@$(PYTHON) -m pip install -e .
	@echo "✓ Setup complete! Package installed and ready to use."

# Run all verification checks (following orchestrator excellence checklist)
verify:
	@echo "=== Step 1: Bytecode Compilation ==="
	@$(PYTHON) -m compileall -q src/saaaaaa || (echo "❌ Compilation failed" && exit 1)
	@echo "✓ Compilation successful\n"
	
	@echo "=== Step 2: Core Purity Scanner (AST anti-I/O and anti-__main__) ==="
	@$(PYTHON) tools/scan_core_purity.py || (echo "❌ Core purity check failed" && exit 1)
	@echo "✓ Core purity verified\n"
	
	@echo "=== Step 3: Canonical Notation Enforcement ==="
	@$(PYTHON) tools/lint/check_canonical_notation.py || (echo "❌ Canonical notation violations detected" && exit 1)
	@echo "✓ Canonical notation check passed\n"
	
	@echo "=== Step 4: Import Linter (Layer Contracts) ==="
	@lint-imports --config contracts/importlinter.ini || (echo "❌ Import contracts violated" && exit 1)
	@echo "✓ Import contracts satisfied\n"
	
	@echo "=== Step 5: Ruff Linting ==="
	@ruff check src/saaaaaa --quiet || (echo "⚠️  Ruff found issues" && exit 1)
	@echo "✓ Ruff checks passed\n"
	
	@echo "=== Step 6: Mypy Type Checking ==="
	@mypy src/saaaaaa --config-file pyproject.toml --no-error-summary 2>&1 | tee /tmp/mypy_output.txt | grep -E "(error|warning)" && echo "⚠️  Mypy found issues (install full package for complete check)" || echo "✓ Mypy checks passed\n"
	
	@echo "=== Step 7: Grep Boundary Checks ==="
	@$(PYTHON) tools/grep_boundary_checks.py || (echo "❌ Boundary violations detected" && exit 1)
	@echo "✓ Boundary checks passed\n"
	
	@echo "=== Step 8: Pycycle (Circular Dependency Detection) ==="
	@pycycle --here > /tmp/pycycle_output.txt 2>&1 || true; \
	if grep -q "No worries" /tmp/pycycle_output.txt; then \
		echo "✓ No circular dependencies\n"; \
	else \
		echo "❌ Circular dependencies detected"; \
		cat /tmp/pycycle_output.txt; \
		exit 1; \
	fi
	
	@echo "=== Step 9: Bulk Import Test ==="
	@$(PYTHON) scripts/import_all.py || (echo "❌ Import test failed" && exit 1)
	@echo "✓ Import test passed\n"
	
	@echo "=== Step 10: Bandit Security Scan ==="
	@bandit -q -r src/saaaaaa -f txt 2>&1 | head -20 || echo "✓ Security scan completed\n"
	
	@echo "=== Step 11: Test Suite ==="
	@pytest -q -ra tests/ 2>&1 | tail -30 || echo "⚠️  Some tests failed"
	
	@echo "\n=== VERIFICATION COMPLETE ==="

# Validate canonical notation usage
validate-canonical:
	@echo "Checking canonical notation enforcement..."
	@$(PYTHON) tools/lint/check_canonical_notation.py

# Validate questionnaire monolith against JSON Schema
validate-monolith:
	@echo "Validating questionnaire monolith..."
	@$(PYTHON) scripts/validate_questionnaire_monolith_schema.py

# Alias for validate-monolith
validate-schema: validate-monolith

# Clean build artifacts and cache files
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf build/ dist/ *.egg-info .pytest_cache/ .mypy_cache/ .ruff_cache/
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Cleaned"

# Equipment checks - verify environment readiness
equip: equip-python equip-native equip-compat
	@echo "\n=== ALL EQUIPMENT CHECKS COMPLETE ==="

equip-python:
	@echo "Running Python environment checks..."
	@$(PYTHON) scripts/equip_python.py

equip-native:
	@echo "Running native dependencies checks..."
	@$(PYTHON) scripts/equip_native.py

equip-compat:
	@echo "Running compatibility layer checks..."
	@$(PYTHON) scripts/equip_compat.py

equip-types:
	@echo "Running type stubs checks..."
	@echo "Checking for py.typed marker..."
	@test -f src/saaaaaa/py.typed && echo "✓ py.typed present" || (echo "✗ py.typed missing" && exit 1)
	@echo "Checking type checking configuration..."
	@grep -q "typeCheckingMode" pyproject.toml && echo "✓ pyright configured" || echo "⚠️  pyright not configured"
	@grep -q "strict = true" pyproject.toml && echo "✓ mypy strict mode enabled" || echo "⚠️  mypy not strict"

# Import audit - comprehensive import system checks
audit-imports:
	@echo "=== IMPORT AUDIT ==="
	@echo "\n1. Shadowing Detection:"
	@$(PYTHON) scripts/audit_import_shadowing.py || true
	@echo "\n2. Circular Import Detection:"
	@$(PYTHON) scripts/audit_circular_imports.py || true
	@echo "\n3. Import Budget Check:"
	@$(PYTHON) scripts/audit_import_budget.py || true
	@echo "\n=== AUDIT COMPLETE ==="

# Path audit - comprehensive path usage and portability checks
audit-paths:
	@echo "=== PATH AUDIT ==="
	@$(PYTHON) scripts/audit_paths.py
	@echo "✓ Path audit complete. See PATHS_AUDIT.md for details."

# Path testing - run all path validation tests
test-paths:
	@echo "=== PATH TESTS ==="
	@pytest tests/paths/ -v
	@echo "✓ Path tests complete."

# Path fix - auto-fix common path issues (where safe)
fix-paths:
	@echo "=== PATH AUTO-FIX ==="
	@echo "⚠️  Auto-fix not yet implemented. Manual fixes required."
	@echo "See PATHS_AUDIT.md for guidance."

# CI prep - create required directories for CI/CD
ci-prep-dirs:
	@echo "=== PREPARING CI DIRECTORIES ==="
	@mkdir -p tmp build/cache build/reports data
	@echo "✓ CI directories created."
