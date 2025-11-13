# Canonical Notation System

## Overview

The Canonical Notation System is the **single source of truth** for all dimension and policy area references in the SAAAAAA (F.A.R.F.A.N) framework. It is defined in `data/questionnaire_monolith.json` and enforced across all files in the repository.

## Structure

The canonical notation is defined in the `canonical_notation` section of `questionnaire_monolith.json`:

```json
{
  "canonical_notation": {
    "dimensions": {
      "D1": {"code": "DIM01", "name": "INSUMOS", "label": "Diagnóstico y Recursos"},
      "D2": {"code": "DIM02", "name": "ACTIVIDADES", "label": "Diseño de Intervención"},
      "D3": {"code": "DIM03", "name": "PRODUCTOS", "label": "Productos y Outputs"},
      "D4": {"code": "DIM04", "name": "RESULTADOS", "label": "Resultados y Outcomes"},
      "D5": {"code": "DIM05", "name": "IMPACTOS", "label": "Impactos de Largo Plazo"},
      "D6": {"code": "DIM06", "name": "CAUSALIDAD", "label": "Teoría de Cambio"}
    },
    "policy_areas": {
      "PA01": {
        "name": "Derechos de las mujeres e igualdad de género",
        "legacy_id": "P1"
      },
      "PA02": {
        "name": "Prevención de la violencia y protección de la población frente al conflicto armado y la violencia generada por grupos delincuenciales organizados, asociada a economías ilegales",
        "legacy_id": "P2"
      },
      "PA03": {
        "name": "Ambiente sano, cambio climático, prevención y atención a desastres",
        "legacy_id": "P3"
      },
      "PA04": {
        "name": "Derechos económicos, sociales y culturales",
        "legacy_id": "P4"
      },
      "PA05": {
        "name": "Derechos de las víctimas y construcción de paz",
        "legacy_id": "P5"
      },
      "PA06": {
        "name": "Derecho al buen futuro de la niñez, adolescencia, juventud y entornos protectores",
        "legacy_id": "P6"
      },
      "PA07": {
        "name": "Tierras y territorios",
        "legacy_id": "P7"
      },
      "PA08": {
        "name": "Líderes y lideresas, defensores y defensoras de derechos humanos, comunitarios, sociales, ambientales, de la tierra, el territorio y de la naturaleza",
        "legacy_id": "P8"
      },
      "PA09": {
        "name": "Crisis de derechos de personas privadas de la libertad",
        "legacy_id": "P9"
      },
      "PA10": {
        "name": "Migración transfronteriza",
        "legacy_id": "P10"
      }
    }
  }
}
```

## Dimensions (D1-D6)

| Key | Code | Name | Label |
|-----|------|------|-------|
| D1 | DIM01 | INSUMOS | Diagnóstico y Recursos |
| D2 | DIM02 | ACTIVIDADES | Diseño de Intervención |
| D3 | DIM03 | PRODUCTOS | Productos y Outputs |
| D4 | DIM04 | RESULTADOS | Resultados y Outcomes |
| D5 | DIM05 | IMPACTOS | Impactos de Largo Plazo |
| D6 | DIM06 | CAUSALIDAD | Teoría de Cambio |

## Policy Areas (PA01-PA10)

| Code | Legacy ID | Name |
|------|-----------|------|
| PA01 | P1 | Derechos de las mujeres e igualdad de género |
| PA02 | P2 | Prevención de la violencia y protección de la población frente al conflicto armado y la violencia generada por grupos delincuenciales organizados, asociada a economías ilegales |
| PA03 | P3 | Ambiente sano, cambio climático, prevención y atención a desastres |
| PA04 | P4 | Derechos económicos, sociales y culturales |
| PA05 | P5 | Derechos de las víctimas y construcción de paz |
| PA06 | P6 | Derecho al buen futuro de la niñez, adolescencia, juventud y entornos protectores |
| PA07 | P7 | Tierras y territorios |
| PA08 | P8 | Líderes y lideresas, defensores y defensoras de derechos humanos, comunitarios, sociales, ambientales, de la tierra, el territorio y de la naturaleza |
| PA09 | P9 | Crisis de derechos de personas privadas de la libertad |
| PA10 | P10 | Migración transfronteriza |

## Usage in Python Code

### Using the Canonical Notation Module

The recommended way to access canonical notation in Python is via the `saaaaaa.core.canonical_notation` module:

```python
from saaaaaa.core.canonical_notation import (
    get_dimension_info,
    get_policy_area_info,
    get_all_dimensions,
    get_all_policy_areas,
    CanonicalDimension,
    CanonicalPolicyArea
)

# Get dimension information
d1_info = get_dimension_info('D1')
print(f"Code: {d1_info.code}")  # DIM01
print(f"Name: {d1_info.name}")  # INSUMOS
print(f"Label: {d1_info.label}")  # Diagnóstico y Recursos

# Get policy area information
pa01_info = get_policy_area_info('PA01')
print(f"Code: {pa01_info.code}")  # PA01
print(f"Name: {pa01_info.name}")  # Derechos de las mujeres e igualdad de género
print(f"Legacy: {pa01_info.legacy_id}")  # P1

# Get all dimensions
all_dims = get_all_dimensions()
for key, info in all_dims.items():
    print(f"{key}: {info.code} - {info.label}")

# Get all policy areas
all_areas = get_all_policy_areas()
for code, info in all_areas.items():
    print(f"{code}: {info.name}")

# Using enums
dim = CanonicalDimension.D1
print(dim.code)  # DIM01
print(dim.label)  # Diagnóstico y Recursos

area = CanonicalPolicyArea.PA01
print(area.value)  # PA01
print(area.name_long)  # Derechos de las mujeres e igualdad de género
print(area.legacy_id)  # P1
```

### Legacy Enums (embedding_policy.py)

For backward compatibility, the `embedding_policy.py` module provides enums that map legacy IDs to canonical codes:

```python
from saaaaaa.processing.embedding_policy import PolicyDomain, AnalyticalDimension

# PolicyDomain maps P1-P10 to PA01-PA10
policy = PolicyDomain.P1
print(policy.value)  # PA01

# AnalyticalDimension maps D1-D6 to DIM01-DIM06
dim = AnalyticalDimension.D1
print(dim.value)  # DIM01
```

## Usage in JSON Schemas

JSON schemas should reference the canonical codes in descriptions:

```json
{
  "properties": {
    "dimension": {
      "type": "string",
      "enum": ["DIM01", "DIM02", "DIM03", "DIM04", "DIM05", "DIM06"],
      "description": "Dimension code per canonical notation"
    },
    "policy_area": {
      "type": "string",
      "enum": ["PA01", "PA02", "PA03", "PA04", "PA05", "PA06", "PA07", "PA08", "PA09", "PA10"],
      "description": "Policy area code per canonical notation"
    }
  }
}
```

For backward compatibility with D1-D6 and P1-P10 keys, reference the canonical codes in descriptions:

```json
{
  "D1": {
    "type": "number",
    "description": "DIM01: INSUMOS - Diagnóstico y Recursos"
  },
  "P1": {
    "type": "number",
    "description": "PA01: Derechos de las mujeres e igualdad de género"
  }
}
```

## Migration Guide

### From Hardcoded Strings

**Before:**
```python
DIMENSION_LABELS = {
    "D1": "Diagnóstico y Recursos",
    "D2": "Diseño de Intervención",
    # ...
}
```

**After:**
```python
from saaaaaa.core.canonical_notation import get_all_dimensions

dimension_labels = {
    key: info.label 
    for key, info in get_all_dimensions().items()
}
```

### From Enum with Hardcoded Values

**Before:**
```python
class Dimension(Enum):
    D1 = "Diagnóstico y Recursos"
    D2 = "Diseño de Intervención"
```

**After:**
```python
from saaaaaa.core.canonical_notation import CanonicalDimension

# Use CanonicalDimension.D1.label to get "Diagnóstico y Recursos"
# Use CanonicalDimension.D1.code to get "DIM01"
```

## Validation

To validate that the canonical notation is correctly loaded:

```bash
# Validate questionnaire monolith schema
python3 scripts/validate_questionnaire_monolith_schema.py

# Test canonical notation module
python3 -c "
from saaaaaa.core.canonical_notation import get_all_dimensions, get_all_policy_areas
print(f'Dimensions: {len(get_all_dimensions())}')
print(f'Policy Areas: {len(get_all_policy_areas())}')
"
```

## Architecture Principles

1. **Single Source of Truth**: All dimension and policy area definitions MUST come from `questionnaire_monolith.json`
2. **No Hardcoded Values**: Never hardcode dimension or policy area names/labels in code
3. **Lazy Loading**: The canonical notation module uses `@lru_cache` to load data once and cache it
4. **Type Safety**: Use dataclasses (`DimensionInfo`, `PolicyAreaInfo`) for type-safe access
5. **Backward Compatibility**: Legacy IDs (P1-P10, D1-D6) are preserved for compatibility

## Files Updated

The following files have been updated to use the canonical notation:

1. **Data Files**:
   - `data/questionnaire_monolith.json` - Added `canonical_notation` section

2. **Python Modules**:
   - `src/saaaaaa/core/canonical_notation.py` - New module for canonical notation access
   - `src/saaaaaa/processing/embedding_policy.py` - Updated enums to reference canonical codes

3. **JSON Schemas**:
   - `config/schemas/embedding_policy/semantic_chunk.schema.json` - Updated to use PA01-PA10 and DIM01-DIM06
   - `config/schemas/report_assembly/macro_convergence.schema.json` - Updated descriptions to reference canonical codes

4. **Examples**:
   - `examples/demo_bayesian_multilevel.py` - Updated comments to reference canonical codes

## Future Work

- Update all remaining files to use the canonical notation module
- Add validation to ensure no hardcoded dimension/policy area strings exist
- Create migration scripts for legacy code
- Add CI/CD checks to enforce canonical notation usage
