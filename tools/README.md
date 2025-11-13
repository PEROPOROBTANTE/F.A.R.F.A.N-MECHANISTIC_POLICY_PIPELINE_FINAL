# Validation and Testing Tools

This directory contains tools for validating data contracts, testing operational feasibility, and ensuring system quality.

## Directory Structure

```
tools/
├── validation/           # Contract validation tools
│   ├── validate_scoring_parity.py
│   └── validate_error_logs.py
└── testing/             # Operational testing tools
    ├── generate_synthetic_traffic.py
    └── boot_check.py
```

## Validation Tools

### Scoring Parity Validation

Validates that scoring normalization is consistent across all modalities.

```bash
# Run parity validation
python tools/validation/validate_scoring_parity.py

# Verbose output
python tools/validation/validate_scoring_parity.py --verbose
```

**What it checks:**
- Normalization formulas are correct for each modality
- Quality thresholds are identical across all modalities
- Boundary conditions produce correct quality levels
- No modality has an unfair advantage

**Exit codes:**
- 0: All parity checks passed
- 1: One or more parity checks failed

### Error Log Validation

Validates contract error logs against the schema.

```bash
# Validate a log file
python tools/validation/validate_error_logs.py --log-file logs/errors.jsonl

# Custom schema path
python tools/validation/validate_error_logs.py \
    --log-file logs/errors.jsonl \
    --schema schemas/contract_error_log.schema.json

# Verbose output
python tools/validation/validate_error_logs.py \
    --log-file logs/errors.jsonl \
    --verbose
```

**Exit codes:**
- 0: All log entries are valid
- 1: One or more validation errors found

## Testing Tools

### Synthetic Traffic Generation

Generates synthetic policy analysis requests for testing runtime validators.

```bash
# Generate 100 synthetic requests
python tools/testing/generate_synthetic_traffic.py --volume 100

# Specific modalities
python tools/testing/generate_synthetic_traffic.py \
    --volume 100 \
    --modalities TYPE_A,TYPE_B,TYPE_C

# Specific policy areas
python tools/testing/generate_synthetic_traffic.py \
    --volume 100 \
    --policy-areas PA01,PA02,PA03

# Save to file (JSONL format)
python tools/testing/generate_synthetic_traffic.py \
    --volume 100 \
    --output traffic.jsonl

# Reproducible generation
python tools/testing/generate_synthetic_traffic.py \
    --volume 100 \
    --seed 42
```

**Output:**
- Statistics on requests by modality and policy area
- Minimum sample size check (10 per modality per policy area)
- Optional JSONL file with all requests

### Boot Check

Validates that all modules load correctly and runtime validators initialize.

```bash
# Run boot check
python tools/testing/boot_check.py

# Verbose output
python tools/testing/boot_check.py --verbose
```

**What it checks:**
- Core modules import successfully
- Optional modules import (non-fatal if missing)
- Orchestrator registry validates without ClassNotFoundError
- Runtime validators initialize successfully

**Exit codes:**
- 0: All boot checks passed
- 1: One or more boot checks failed

## Integration with CI

All validation tools are integrated into the CI pipeline:

### Data Contracts Workflow

```yaml
# .github/workflows/data-contracts.yml
- name: Scoring parity validation
  run: python tools/validation/validate_scoring_parity.py
```

### Pre-commit Hooks

Add to `.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: scoring-parity
      name: Validate scoring parity
      entry: python tools/validation/validate_scoring_parity.py
      language: system
      pass_filenames: false
```

## Local Development Workflow

Before committing:

```bash
# Run all local validation checks
./scripts/validate_contracts_local.sh

# Generate synthetic traffic for testing
python tools/testing/generate_synthetic_traffic.py \
    --volume 100 \
    --output /tmp/test_traffic.jsonl

# Run boot check
python tools/testing/boot_check.py
```

## Testing

All tools have corresponding test suites:

```bash
# Test synthetic traffic generation
python -m pytest tests/operational/test_synthetic_traffic.py -v

# Test boot check functionality
python -m pytest tests/operational/test_boot_checks.py -v

# Run all operational tests
python -m pytest tests/operational/ -v
```

## Requirements

Minimum requirements:
- Python 3.10+
- jsonschema (for error log validation)

Full requirements in `requirements_atroz.txt`.

## Error Handling

All tools follow consistent error handling:

- **Exit code 0**: Success
- **Exit code 1**: Validation/test failure
- **Structured output**: JSON where applicable
- **Clear error messages**: Specific line numbers and remediation steps

## Contributing

When adding new validation or testing tools:

1. Follow the existing naming convention (`validate_*.py` or `*_check.py`)
2. Add command-line interface with `argparse`
3. Provide `--verbose` flag for detailed output
4. Return appropriate exit codes (0 for success, 1 for failure)
5. Add corresponding tests in `tests/operational/`
6. Update this README with usage examples
7. Integrate into CI workflow if appropriate

## Documentation

For detailed information on specific topics:

- **Data Contracts**: See `docs/DATA_CONTRACTS.md`
- **API Exemptions**: See `docs/API_EXEMPTIONS.md`
- **Contract Error Logging**: See `validation/contract_logger.py`
- **Error Log Schema**: See `schemas/contract_error_log.schema.json`
