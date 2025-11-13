# Questionnaire Monolith JSON Schema Documentation

## Overview

The `questionnaire_monolith.schema.json` is a comprehensive JSON Schema (Draft-07) that validates the structure, integrity, and quality constraints of the `questionnaire_monolith.json` file. This schema ensures that the canonical source of truth for the 305 questions maintains high quality and consistency.

## Purpose

This schema was designed with the following goals:

1. **Structural Validation**: Ensure all required fields and sections are present with correct types
2. **Data Quality**: Enforce constraints on values, formats, and patterns to maintain data integrity
3. **Referential Integrity**: Validate relationships between different sections of the monolith
4. **Distribution Validation**: Ensure proper distribution of questions across dimensions and clusters
5. **Documentation**: Provide clear descriptions for all schema elements

## Key Features

### 1. Comprehensive Coverage

The schema validates all major sections of the questionnaire monolith:

- **Top-level structure**: version, schema_version, generated_at, integrity, blocks, observability
- **Micro questions**: 300 questions with patterns, validations, method sets, and expected elements
- **Meso questions**: 4 cluster-level questions with aggregation methods
- **Macro question**: 1 holistic question covering all clusters
- **Metadata**: Clusters, dimensions, and policy areas (niveles_abstraccion)
- **Scoring**: Modalities, definitions, and quality levels
- **Semantic layers**: Embedding strategies and disambiguation rules
- **Observability**: Telemetry schema for logging, metrics, and tracing

### 2. Strong Typing and Constraints

Each field has strict type definitions and constraints:

```json
{
  "question_id": {
    "type": "string",
    "pattern": "^Q\\d{3}$",
    "description": "Question ID in format Q001 to Q300"
  },
  "question_global": {
    "type": "integer",
    "minimum": 1,
    "maximum": 300,
    "description": "Global question number (1-300)"
  }
}
```

### 3. Enumerated Values

Critical fields use enums to prevent invalid values:

- **Scoring modalities**: TYPE_A, TYPE_B, TYPE_C, TYPE_D, TYPE_E, TYPE_F
- **Match types**: REGEX, LITERAL
- **Pattern categories**: GENERAL, INDICADOR, TEMPORAL, TERRITORIAL, FUENTE_OFICIAL, UNIDAD_MEDIDA
- **Method types**: extraction, validation, analysis, scoring
- **Quality levels**: EXCELENTE, BUENO, ACEPTABLE, INSUFICIENTE

### 4. Pattern Validation

ID formats are validated with regex patterns:

- Policy Area IDs: `PA01` to `PA10` (pattern: `^PA(0[1-9]|10)$`)
- Cluster IDs: `CL01` to `CL04` (pattern: `^CL0[1-4]$`)
- Dimension IDs: `DIM01` to `DIM06` (pattern: `^DIM0[1-6]$`)
- Base Slots: `D1-Q1` to `D6-Q5` (pattern: `^D[1-6]-Q[1-5]$`)
- Pattern IDs: `PAT-Q###-###` (pattern: `^PAT-Q\\d{3}-\\d{3}$`)

### 5. Integrity Constraints

The schema enforces critical count constraints:

```json
{
  "question_count": {
    "micro": { "const": 300 },
    "meso": { "const": 4 },
    "macro": { "const": 1 },
    "total": { "const": 305 }
  }
}
```

### 6. Hash Validation

SHA256 hashes are validated with a specific pattern:

```json
{
  "monolith_hash": {
    "type": "string",
    "pattern": "^[0-9a-f]{64}$"
  }
}
```

## Structure Overview

### Top Level

```
questionnaire_monolith.json
├── version (semver)
├── schema_version (semver)
├── generated_at (ISO 8601 datetime)
├── canonical_notation (object)
├── integrity
│   ├── monolith_hash (SHA256)
│   ├── ruleset_hash (SHA256)
│   └── question_count (micro: 300, meso: 4, macro: 1, total: 305)
├── observability
│   └── telemetry_schema
│       ├── logs
│       ├── metrics
│       └── tracing
└── blocks
    ├── macro_question
    ├── meso_questions [4]
    ├── micro_questions [300]
    ├── niveles_abstraccion
    │   ├── clusters [4]
    │   ├── dimensions [6]
    │   └── policy_areas [10]
    ├── scoring
    │   ├── micro_levels
    │   ├── modalities
    │   └── modality_definitions
    └── semantic_layers
        ├── embedding_strategy
        └── disambiguation
```

### Micro Question Structure

Each of the 300 micro questions has:

```json
{
  "question_id": "Q001",
  "question_global": 1,
  "base_slot": "D1-Q1",
  "policy_area_id": "PA01",
  "cluster_id": "CL02",
  "dimension_id": "DIM01",
  "text": "...",
  "scoring_modality": "TYPE_A",
  "scoring_definition_ref": "scoring_modalities.TYPE_A",
  "patterns": [
    {
      "id": "PAT-Q001-000",
      "pattern": "...",
      "match_type": "REGEX",
      "confidence_weight": 0.85,
      "category": "TEMPORAL",
      "flags": "i"
    }
  ],
  "expected_elements": [
    {
      "type": "cobertura_territorial_especificada",
      "required": true
    }
  ],
  "method_sets": [
    {
      "module_enum": "DIM01_METHODS",
      "class": "Dimension1Analyzer",
      "function": "analyze_question_1",
      "method_type": "extraction",
      "priority": 1,
      "description": "..."
    }
  ],
  "failure_contract": {
    "abort_if": ["missing_required_element"],
    "emit_code": "ABORT-Q001-REQ"
  },
  "validations": {
    "verificar_fuentes": {
      "patterns": ["fuente:", "según", "datos de"],
      "minimum_required": 2,
      "specificity": "MEDIUM"
    }
  }
}
```

### Meso Question Structure

Each of the 4 meso (cluster-level) questions has:

```json
{
  "question_id": "MESO_1",
  "question_global": 301,
  "type": "MESO",
  "cluster_id": "CLUSTER_1",
  "text": "...",
  "scoring_modality": "MESO_INTEGRATION",
  "aggregation_method": "weighted_average",
  "policy_areas": ["P2", "P3", "P7"],
  "patterns": [
    {
      "type": "cross_reference",
      "description": "..."
    }
  ]
}
```

### Macro Question Structure

The single macro (holistic) question has:

```json
{
  "question_id": "MACRO_1",
  "question_global": 305,
  "type": "MACRO",
  "text": "...",
  "scoring_modality": "MACRO_HOLISTIC",
  "aggregation_method": "holistic_assessment",
  "clusters": ["CLUSTER_1", "CLUSTER_2", "CLUSTER_3", "CLUSTER_4"],
  "patterns": [
    {
      "type": "narrative_coherence",
      "priority": 1,
      "description": "..."
    }
  ],
  "fallback": {
    "condition": "always_true",
    "pattern": "MACRO_AMBIGUO",
    "priority": 999
  }
}
```

## Validation Levels

The schema validation script (`validate_questionnaire_monolith_schema.py`) performs multiple levels of validation:

### Level 1: JSON Schema Validation

Validates against the JSON Schema specification:
- All required fields present
- Correct data types
- Pattern matching for IDs
- Enum value validation
- Array size constraints

### Level 2: Base Slot Distribution

Validates that:
- Exactly 30 unique base slots exist (D1-Q1 through D6-Q5)
- Each base slot appears exactly 10 times across the 300 micro questions

### Level 3: Question ID Uniqueness

Validates that:
- All 305 question IDs are unique
- No duplicates across micro, meso, and macro questions

### Level 4: Cluster Hermeticity

Validates that:
- All 4 clusters have correct policy area assignments
- Cluster definitions match canonical mappings:
  - CL01: PA02, PA03, PA07 (Seguridad y Paz)
  - CL02: PA01, PA05, PA06 (Grupos Poblacionales)
  - CL03: PA04, PA08 (Territorio-Ambiente)
  - CL04: PA09, PA10 (Derechos Sociales & Crisis)

### Level 5: Referential Integrity

Validates that:
- Policy area IDs in questions exist in niveles_abstraccion
- Dimension IDs in questions exist in niveles_abstraccion
- Cluster IDs in questions exist in niveles_abstraccion

## Usage

### Validating the Monolith

```bash
# Run the validation script
python3 scripts/validate_questionnaire_monolith_schema.py

# Expected output on success:
# ✓ ALL VALIDATIONS PASSED
```

### Using the Schema in Code

```python
import json
import jsonschema

# Load schema
with open('config/schemas/questionnaire_monolith.schema.json') as f:
    schema = json.load(f)

# Load monolith
with open('data/questionnaire_monolith.json') as f:
    monolith = json.load(f)

# Validate
try:
    jsonschema.validate(monolith, schema)
    print("Valid!")
except jsonschema.ValidationError as e:
    print(f"Invalid: {e.message}")
```

### Integration with CI/CD

Add to your CI pipeline:

```yaml
- name: Validate Questionnaire Monolith Schema
  run: |
    python3 scripts/validate_questionnaire_monolith_schema.py
```

## Quality Assurance Features

### 1. Prevents Data Corruption

The schema prevents:
- Missing required fields
- Invalid ID formats
- Incorrect data types
- Out-of-range values
- Duplicate question IDs

### 2. Enforces Consistency

The schema ensures:
- Consistent ID patterns across all levels
- Proper cluster and dimension assignments
- Correct scoring modality references
- Valid pattern categories and match types

### 3. Maintains Integrity

The schema validates:
- Question count invariants (300 + 4 + 1 = 305)
- Base slot distribution (30 slots × 10 questions)
- Cluster hermeticity
- Referential integrity between sections

### 4. Supports Evolution

The schema is designed to support evolution:
- Semantic versioning for both data and schema
- Extensible pattern categories
- Flexible validation checks
- Documented descriptions for all fields

## Best Practices

### 1. Always Validate After Changes

```bash
# After any modification to questionnaire_monolith.json
python3 scripts/validate_questionnaire_monolith_schema.py
```

### 2. Version Control

- Keep schema and monolith versions in sync
- Update schema_version when schema changes
- Update version when monolith data changes

### 3. Document Schema Changes

When modifying the schema:
- Add clear descriptions for new fields
- Update this documentation
- Test against actual monolith data
- Consider backward compatibility

### 4. Use Schema for Generation

When generating new monoliths:
- Validate output against schema
- Use schema definitions as specification
- Ensure all constraints are met

## Troubleshooting

### Common Validation Errors

#### 1. Pattern Match Failure

```
Error: 'Q1' does not match '^Q\\d{3}$'
```

**Solution**: Question IDs must be zero-padded (Q001, not Q1)

#### 2. Count Mismatch

```
Error: 300 was expected
```

**Solution**: Ensure exactly 300 micro questions exist

#### 3. Referential Integrity Error

```
Error: Question 1 references invalid policy_area_id: PA11
```

**Solution**: Policy area IDs must be PA01 through PA10

#### 4. Base Slot Distribution Error

```
Error: Base slot D1-Q1 appears 11 times (expected 10)
```

**Solution**: Check base_slot assignments for duplicates

### Schema Validation Fails But Monolith Seems Correct

1. Check if the schema needs updating for new patterns
2. Verify the monolith format hasn't evolved
3. Ensure jsonschema package is up to date
4. Review schema constraints for overly strict rules

## Schema Evolution

### Version History

- **1.0.0** (Current): Initial comprehensive schema
  - Validates 305 questions (300 micro + 4 meso + 1 macro)
  - Enforces integrity constraints
  - Validates observability telemetry
  - Checks referential integrity

### Planned Enhancements

Future versions may include:
- Additional pattern categories
- More granular validation rules
- Cross-question relationship validation
- Temporal consistency checks
- Evidence requirement validation

## Related Documentation

- [README_MONOLITH.md](README_MONOLITH.md) - Monolith architecture and structure
- [questionnaire.schema.json](../config/schemas/questionnaire.schema.json) - Alternative V2 schema
- [OPERATIONAL_GUIDE.md](../OPERATIONAL_GUIDE.md) - System operation guide

## Support

For issues with the schema:
1. Check this documentation
2. Review validation error messages
3. Run validation script with verbose output
4. Examine the schema file directly
5. File an issue in the repository

## License

Same as the parent repository.
