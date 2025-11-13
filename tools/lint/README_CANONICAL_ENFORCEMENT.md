# Canonical Notation Enforcement

This directory contains enforcement mechanisms to ensure canonical notation is used throughout the codebase.

## Pre-commit Hook

The `check_canonical_notation.py` script is configured as a pre-commit hook to automatically check for hardcoded dimension and policy area strings before commits.

### Installation

Pre-commit hooks are configured in `.pre-commit-config.yaml`:

```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run canonical-notation-check --all-files
```

### Usage

The hook runs automatically on `git commit` and will:
- ✅ Pass if no hardcoded strings are found
- ❌ Fail if hardcoded dimension/policy area strings are detected
- Display the file, line number, and violating string for each issue

### Manual Execution

```bash
# Check all files
python tools/lint/check_canonical_notation.py

# Check specific files
python tools/lint/check_canonical_notation.py src/saaaaaa/analysis/*.py

# Via Makefile
make validate-canonical
```

## Forbidden Strings

The checker blocks these hardcoded strings:

**Dimensions:**
- "Diagnóstico y Recursos"
- "Diseño de Intervención"
- "Productos y Outputs"
- "Resultados y Outcomes"
- "Impactos de Largo Plazo"
- "Teoría de Cambio"

**Policy Areas:**
- "Derechos de las mujeres e igualdad de género"
- "Prevención de la violencia y protección"
- "Ambiente sano, cambio climático"
- "Derechos económicos, sociales y culturales"
- "Derechos de las víctimas y construcción de paz"
- "Derecho al buen futuro de la niñez"
- "Tierras y territorios"
- "Líderes y defensores de derechos humanos"
- "Crisis de derechos de personas privadas"
- "Migración transfronteriza"

## Exempt Files

These files are exempt from checking:
- `canonical_notation.py` - Defines the canonical notation system
- `check_canonical_notation.py` - The checker itself
- `questionnaire_monolith.json` - Source of truth for canonical data
- `embedding_policy.py` - Contains enum definitions with inline documentation
- `factory.py` - Contains example docstrings

## How to Fix Violations

Instead of hardcoded strings, use:

```python
# Option 1: Use canonical_notation module
from saaaaaa.core.canonical_notation import get_dimension_info, get_policy_area_info

dim_info = get_dimension_info('D1')
print(dim_info.label)  # "Diagnóstico y Recursos"

area_info = get_policy_area_info('PA01')
print(area_info.name)  # "Derechos de las mujeres e igualdad de género"

# Option 2: Use factory
from saaaaaa.core.orchestrator.factory import get_canonical_dimensions

dims = get_canonical_dimensions()
print(dims['D1']['label'])  # "Diagnóstico y Recursos"
```

## CI/CD Integration

The canonical notation check is integrated into:
1. **Pre-commit hooks** - Runs before each commit
2. **Makefile verify** - Step 3 of verification pipeline
3. **Makefile validate-canonical** - Standalone validation target

## Exit Codes

- `0` - All checks passed
- `1` - Violations found

## Notes

- Docstrings and comments are automatically skipped
- The checker uses regex to identify code vs. documentation
- False positives can be reported as issues for investigation
