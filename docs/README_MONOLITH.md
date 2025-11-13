# Questionnaire Monolith - Migration Guide

## Overview

The `questionnaire_monolith.json` is a unified, canonical data structure that consolidates:
- Legacy `questionnaire.json` (300 micro questions)
- Legacy `rubric_scoring.json` (scoring matrices and aggregation rules)
- 4 MESO cluster-level questions
- 1 MACRO holistic question

**Total:** 305 questions with complete metadata, patterns, validations, and method references.

## Architecture

### Structure

```
questionnaire_monolith.json
├── version: "1.0.0"
├── generated_at: ISO 8601 timestamp
├── integrity
│   ├── monolith_hash: SHA256 hash for verification
│   └── question_count: {micro: 300, meso: 4, macro: 1, total: 305}
└── blocks
    ├── niveles_abstraccion: Metadata (policy areas, dimensions, clusters)
    ├── micro_questions: 300 micro-level questions
    ├── meso_questions: 4 cluster-level questions
    ├── macro_question: 1 holistic question
    └── scoring: Scoring matrices and quality levels
```

### Base Slot Formula

Each micro question is assigned a `base_slot` using:

```python
base_index = (question_global - 1) % 30
base_slot = f"D{base_index//5+1}-Q{base_index%5+1}"
```

This creates 30 unique base_slots (D1-Q1 through D6-Q5), each appearing exactly 10 times across the 300 micro questions.

### Canonical Clusters

The monolith preserves 4 hermetic clusters:

1. **CL01** (`PA02`, `PA03`, `PA07`) - Seguridad y Paz
2. **CL02** (`PA01`, `PA05`, `PA06`) - Grupos Poblacionales
3. **CL03** (`PA04`, `PA08`) - Territorio-Ambiente
4. **CL04** (`PA09`, `PA10`) - Derechos Sociales & Crisis

## Building the Monolith

### Prerequisites

- Python 3.8+
- Legacy files in repository root:
  - `questionnaire.json`
  - `rubric_scoring.json`
  - `COMPLETE_METHOD_CLASS_MAP.json` (optional)

### Build Command

```bash
python3 build_monolith.py
```

Options:
```bash
python3 build_monolith.py --output /path/to/output.json
```

### Build Phases

The builder executes 11 strict phases:

1. **LoadLegacyPhase**: Load and validate legacy JSON files
2. **StructuralIndexingPhase**: Index 300 micro questions
3. **BaseSlotMappingPhase**: Apply base_slot formula
4. **ExtractionAndNormalizationPhase**: Normalize all text fields
5. **IndicatorsAndEvidencePhase**: Extract patterns and validations
6. **MethodSetSynthesisPhase**: Insert method references per base_slot
7. **RubricTranspositionPhase**: Transfer scoring matrices
8. **MesoMacroEmbeddingPhase**: Add 4 MESO + 1 MACRO questions
9. **IntegritySealingPhase**: Calculate SHA256 hash
10. **ValidationReportPhase**: Verify all invariants
11. **FinalEmissionPhase**: Write monolith + manifest

### Outputs

- `questionnaire_monolith.json`: The monolithic questionnaire (600KB+)
- `forge_manifest.json`: Build metadata and statistics
- `forge.log`: Structured build log

## Validation

### Validate Command

```bash
python3 validate_monolith.py questionnaire_monolith.json
```

### Validations Performed

1. **Structure**: All top-level keys and blocks present
2. **Question Counts**: 300 micro + 4 meso + 1 macro = 305 total
3. **Base Slots**: 30 slots, each with exactly 10 questions
4. **Cluster Hermeticity**: All 4 clusters match canonical definitions
5. **Micro Questions**: Required fields, non-empty text, valid scoring_modality
6. **Meso Questions**: Proper cluster references, type=MESO
7. **Macro Question**: type=MACRO, question_global=305, fallback pattern
8. **Integrity Hash**: Hash present and counts match

### Exit Codes

- `0`: All validations passed
- `1`: One or more validations failed

## Abort Conditions

The builder aborts immediately on any of these conditions:

| Code | Phase | Condition |
|------|-------|-----------|
| A001 | LoadLegacy | Missing or invalid legacy file |
| A010 | StructuralIndexing | Discontinuous global numbering |
| A020 | BaseSlotMapping | Base slot coverage mismatch |
| A030 | ExtractionAndNormalization | Invalid scoring modality |
| A040 | IndicatorsAndEvidence | Missing expected elements |
| A050 | MethodSetSynthesis | Method metadata incomplete |
| A060 | RubricTransposition | Rubric thresholds out of order |
| A070 | MesoMacroEmbedding | Cluster hermeticity violation |
| A080 | IntegritySealing | Monolith hash mismatch |
| A090 | ValidationReport | Atom loss detected |
| A100 | FinalEmission | Empty monolith emission |

## Integration

### Orchestrator Integration

The monolith is the **ONLY** source of truth for questionnaire data. The orchestrator should:

1. Load `questionnaire_monolith.json` on startup
2. Cache blocks in memory for efficient access
3. Never modify the monolith directly
4. Verify integrity hash on load

Example:

```python
import json
import hashlib

def load_monolith(path):
    with open(path) as f:
        monolith = json.load(f)
    
    # Verify integrity
    stored_hash = monolith['integrity']['monolith_hash']
    # ... verify hash ...
    
    return monolith

# Access blocks
monolith = load_monolith('questionnaire_monolith.json')
micro_questions = monolith['blocks']['micro_questions']
meso_questions = monolith['blocks']['meso_questions']
macro_question = monolith['blocks']['macro_question']
```

### Choreographer Integration

The choreographer should obtain data **only through the orchestrator**:

```python
# ❌ WRONG - Direct access
with open('questionnaire_monolith.json') as f:
    data = json.load(f)

# ✅ CORRECT - Via orchestrator
questions = orchestrator.get_questions_for_dimension('DIM01')
```

## Migration from Legacy

### Before Migration

```
questionnaire.json        -> 300 questions
rubric_scoring.json       -> Scoring rules
```

### After Migration

```
questionnaire_monolith.json  -> 305 questions + scoring + metadata
```

### Deprecation

Once the monolith is in use:

1. **DO NOT** modify `questionnaire.json` or `rubric_scoring.json`
2. **DO NOT** load legacy files in production code
3. **DO** rebuild monolith if legacy files are updated (development only)
4. **DO** use the monolith as the single source of truth

## Quality Levels

### Micro Questions

| Level | Min Score | Color |
|-------|-----------|-------|
| EXCELENTE | 0.85 | green |
| BUENO | 0.70 | blue |
| ACEPTABLE | 0.55 | yellow |
| INSUFICIENTE | 0.0 | red |

### Scoring Modalities

- **TYPE_A**: Count 4 elements, scale to 0-3
- **TYPE_B**: Count up to 3 elements, each worth 1 point
- **TYPE_C**: Count 2 elements, scale to 0-3
- **TYPE_D**: Count 3 elements, weighted
- **TYPE_E**: Boolean presence check
- **TYPE_F**: Continuous scale

## Troubleshooting

### Build Failures

**Symptom**: Build aborts with error code

**Solution**: Check `forge.log` for the exact phase and error message. Fix the underlying issue in legacy files and rebuild.

### Validation Failures

**Symptom**: Validator reports errors

**Solution**: The monolith is corrupted or manually modified. Rebuild from legacy sources.

### Hash Mismatch

**Symptom**: Integrity hash doesn't match

**Solution**: File was modified after generation. Rebuild to get a clean hash.

## FAQ

### Q: Can I edit the monolith manually?

**A:** No. Always rebuild from legacy sources to maintain integrity.

### Q: How often should I rebuild?

**A:** Only when legacy files are updated (development). In production, the monolith is immutable.

### Q: What if I need to add a question?

**A:** Update the legacy `questionnaire.json`, then rebuild the monolith.

### Q: Can I use the monolith with older code?

**A:** No. Code must be updated to use the monolith structure. The orchestrator provides the abstraction layer.

### Q: Is the hash required?

**A:** Yes. The hash ensures the monolith hasn't been tampered with or corrupted.

## Performance

- **File Size**: ~600KB (610,000 bytes)
- **Load Time**: <100ms (Python)
- **Memory**: ~2MB in-memory (uncompressed JSON)
- **Recommended**: Load once, cache in memory

## Versioning

Current version: **1.0.0**

Version format: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes to structure
- **MINOR**: New blocks or backward-compatible additions
- **PATCH**: Bug fixes, no structure changes

## License

Same as the parent repository.

## Support

For issues or questions, see the project repository.
