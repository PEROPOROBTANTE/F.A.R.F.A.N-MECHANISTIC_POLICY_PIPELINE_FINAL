# Scripts Directory - Equipment and Validation Tools

This directory contains scripts for equipment, validation, and operational management of the SIN_CARRETA system.

## Equipment Scripts

### `equip_signals.py`
**Purpose:** Equipment routine for signals subsystem  
**Usage:**
```bash
python3 scripts/equip_signals.py --warmup-cache --preload-patterns --verify-registry
```

**Options:**
- `--source {memory,http}`: Signal source (default: memory)
- `--preload-patterns`: Pre-compile regex patterns
- `--warmup-cache`: Warm up signal cache with test data
- `--verify-registry`: Verify signal registry initialization
- `--hit-rate-threshold FLOAT`: Minimum hit rate threshold (default: 0.95)

**What it does:**
- Initializes SignalRegistry with proper configuration
- Pre-compiles common regex patterns for performance
- Warms up memory:// cache with test signals
- Verifies signal hit rate meets threshold (≥95%)

---

### `equip_cpp_smoke.py`
**Purpose:** Smoke tests for CPP adapter and ingestion pipeline  
**Usage:**
```bash
python3 scripts/equip_cpp_smoke.py --run-tests
```

**What it does:**
- Tests CPPAdapter can be imported
- Initializes CPPIngestionPipeline and verifies schema version
- Tests conversion from Canon Policy Package to PreprocessedDocument
- Validates CPPAdapter.ensure() method
- Verifies provenance completeness = 1.0

---

### `preflight_check.py`
**Purpose:** Pre-execution validation checklist  
**Usage:**
```bash
python3 scripts/preflight_check.py --verbose
```

**What it validates:**
1. Python version ≥ 3.10
2. No YAML files in executors/ (code-only config)
3. ArgRouter has ≥ 30 routes
4. Memory signals (memory://) available
5. Critical imports work (orchestrator, flux, cpp_ingestion)
6. Pinned dependencies installed with correct versions

**Exit codes:**
- 0: All checks passed
- 1: One or more checks failed

---

### `mark_outdated_tests.py`
**Purpose:** Automatically mark outdated tests with @pytest.mark.skip  
**Usage:**
```bash
python3 scripts/mark_outdated_tests.py
```

**What it does:**
- Reads `tests/UPDATED_TESTS_MANIFEST.json`
- Adds `pytestmark = pytest.mark.skip(reason="...")` to outdated test files
- Ensures tests marked as outdated won't run in CI/CD

---

## Other Utility Scripts

### `scan_no_yaml_in_executors.py`
**Purpose:** Verify no YAML files exist in executors/ directory  
**Usage:**
```bash
python3 scripts/scan_no_yaml_in_executors.py
```

**Policy:** Executors must use code-only configuration (frozen dataclasses), no YAML.

---

### `verify_system_equipment.py` (if exists)
**Purpose:** Comprehensive system verification  
**Usage:**
```bash
python3 scripts/verify_system_equipment.py --check-all
```

---

## Makefile Integration

All equipment scripts are integrated into the Makefile for easy execution:

```bash
# Individual equipment phases
make equip-system     # OS checks, ulimits, ICU
make equip-python     # Dependencies, C-exts, imports
make equip-signals    # Signal registry, cache warmup
make equip-cpp        # CPP adapter smoke tests

# All equipment phases
make equip-all

# Preflight checklist
make preflight
```

---

## Test Execution

See `tests/UPDATED_TESTS_MANIFEST.json` for complete test organization.

```bash
# Run only updated tests
pytest -m "updated and not outdated" -v

# Run critical tests
pytest tests/test_contracts_comprehensive.py tests/test_flux_integration.py -v

# Run by category
pytest tests/test_signal_*.py -v  # All signal tests
```

---

## Directory Structure

```
scripts/
├── equip_signals.py              # Signal subsystem equipment
├── equip_cpp_smoke.py           # CPP subsystem smoke tests
├── preflight_check.py           # Pre-execution validation
├── mark_outdated_tests.py       # Auto-mark outdated tests
├── scan_no_yaml_in_executors.py # YAML prohibition check
├── setup.sh                     # System setup script
├── README.md                    # This file
└── ... (other utility scripts)
```

---

## Development Workflow

### Before Starting Work
```bash
make equip-all          # Ensure system is equipped
make preflight          # Run preflight checks
```

### During Development
```bash
pytest -m updated -v    # Run updated tests only
make verify             # Full verification pipeline
```

### Before Committing
```bash
make clean              # Clean artifacts
pytest -m updated -v    # Final test run
make preflight          # Final validation
```

---

## Quality Gates

All equipment scripts enforce quality gates:

| Gate | Threshold | Script |
|------|-----------|--------|
| Signal hit rate | ≥ 95% | equip_signals.py |
| Provenance completeness | = 1.0 | equip_cpp_smoke.py |
| ArgRouter routes | ≥ 30 | preflight_check.py |
| Python version | ≥ 3.10 | preflight_check.py |
| YAML in executors | = 0 | scan_no_yaml_in_executors.py |

---

## Troubleshooting

### Import Errors
```bash
# Reinstall package
pip install -e .

# Verify imports
python3 -c "from saaaaaa.core.orchestrator import Orchestrator; print('OK')"
```

### Failed Preflight
```bash
# Check specific failure
python3 scripts/preflight_check.py --verbose

# Re-equip system
make equip-all
```

### Test Failures
```bash
# Run with full output
pytest tests/test_failing.py -vv --tb=long

# Check test classification
grep "pytestmark" tests/test_failing.py
```

---

For complete operational instructions, see:
- **[OPERATIONAL_GUIDE.md](../OPERATIONAL_GUIDE.md)** - Current operational/install guide
- **[tests/UPDATED_TESTS_MANIFEST.json](../tests/UPDATED_TESTS_MANIFEST.json)** - Test classification
