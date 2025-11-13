# Scoring Module

Implements the 6 scoring modalities (TYPE_A through TYPE_F) for the SAAAAAA policy analysis framework with strict validation and reproducible results.

## Overview

The scoring module provides:
- **Application of 6 scoring modalities** (TYPE_A through TYPE_F)
- **Validation of evidence structure** vs modality requirements
- **Assignment of quality levels** (EXCELENTE, BUENO, ACEPTABLE, INSUFICIENTE)
- **Structured logging** with strict abortability
- **Reproducible ScoredResult** outputs with evidence hashing

## Design Principles

1. **No Fallback**: If evidence validation fails, the entire scoring process aborts with a clear error message. No partial or heuristic scoring.
2. **Strict Validation**: Evidence structure must exactly match modality requirements (required keys, data types, value ranges).
3. **Reproducibility**: Same evidence always produces the same `ScoredResult`. Evidence is hashed for verification.
4. **Structured Logging**: All scoring steps logged at INFO level, errors at ERROR level.
5. **Type Safety**: All inputs and outputs are strongly typed using dataclasses and enums.

## Scoring Modalities

### TYPE_A: Bayesian Numerical Claims

**Purpose**: Score numerical claims, gaps, and risks based on Bayesian confidence.

**Evidence Requirements**:
- `elements` (list): Up to 4 elements
- `confidence` (float): Bayesian confidence score (0-1)

**Scoring**:
- Count elements (max 4)
- Weight by confidence
- Scale to 0-4 range

**Example**:
```python
evidence = {
    "elements": [
        "Baseline gap: 15% unemployment",
        "Risk: inflation at 8%",
        "Target: reduce gap by 30%",
        "Constraint: budget limited to $2M"
    ],
    "confidence": 0.85
}
# Score: ~3.4 / 4.0
```

### TYPE_B: DAG Causal Chains

**Purpose**: Score causal chain completeness via DAG analysis.

**Evidence Requirements**:
- `elements` (list): Up to 3 causal chain elements
- `completeness` (float): DAG completeness score (0-1)

**Scoring**:
- Count causal elements (max 3)
- Each element worth 1 point
- Weight by completeness

**Example**:
```python
evidence = {
    "elements": [
        "Input → Activity",
        "Activity → Output",
        "Output → Outcome"
    ],
    "completeness": 0.92
}
# Score: ~2.76 / 3.0
```

### TYPE_C: Coherence via Inverted Contradictions

**Purpose**: Score coherence by analyzing contradiction absence.

**Evidence Requirements**:
- `elements` (list): Up to 2 coherence elements
- `coherence_score` (float): Inverted contradiction score (0-1, higher is better)

**Scoring**:
- Count coherence elements (max 2)
- Scale by coherence score
- Scale to 0-3 range

**Example**:
```python
evidence = {
    "elements": [
        "Policy states budget of $5M",
        "Annex confirms $5M allocation"
    ],
    "coherence_score": 0.95
}
# Score: ~2.85 / 3.0
```

### TYPE_D: Pattern Matching

**Purpose**: Score baseline data formalization via pattern matching.

**Evidence Requirements**:
- `elements` (list): Up to 3 pattern matches
- `pattern_matches` (int/float): Number of successful pattern matches

**Scoring**:
- Count pattern matches (max 3)
- Scale to 0-3 range

**Example**:
```python
evidence = {
    "elements": [
        "Baseline: unemployment at 12%",
        "Target: reduce to 8% in 3 years",
        "Gap quantified as 4 percentage points"
    ],
    "pattern_matches": 2
}
# Score: 2.0 / 3.0
```

### TYPE_E: Financial Budget Traceability

**Purpose**: Score budget traceability via presence check.

**Evidence Requirements**:
- `elements` (list): Budget elements
- `traceability` (bool or float): Boolean presence or numeric score (0-1)

**Scoring**:
- Boolean presence check (or numeric if provided)
- Scale to 0-3 range
- Returns 0 if no elements present

**Example**:
```python
evidence = {
    "elements": [
        "Budget line item: Training - $1.2M",
        "Budget line item: Equipment - $800K"
    ],
    "traceability": True
}
# Score: 3.0 / 3.0
```

### TYPE_F: Beach Mechanism Inference

**Purpose**: Score mechanism plausibility via Beach tests.

**Evidence Requirements**:
- `elements` (list): Mechanism elements
- `plausibility` (float): Plausibility score (0-1)

**Scoring**:
- Continuous scale based on plausibility
- Weight by element presence
- Scale to 0-3 range

**Example**:
```python
evidence = {
    "elements": [
        "Mechanism: Training increases skills",
        "Mechanism: Skills increase employability"
    ],
    "plausibility": 0.88
}
# Score: ~2.64 / 3.0
```

## Quality Levels

Normalized scores (0-1 range) are mapped to quality levels:

| Level | Threshold | Description |
|-------|-----------|-------------|
| EXCELENTE | ≥ 0.85 | Excellent quality evidence |
| BUENO | ≥ 0.70 | Good quality evidence |
| ACEPTABLE | ≥ 0.55 | Acceptable quality evidence |
| INSUFICIENTE | < 0.55 | Insufficient quality evidence |

## Usage

### Basic Usage

```python
from scoring.scoring import apply_scoring

evidence = {
    "elements": [1, 2, 3, 4],
    "confidence": 0.9
}

result = apply_scoring(
    question_global=1,
    base_slot="PA01-DIM01-Q001",
    policy_area="PA01",
    dimension="DIM01",
    evidence=evidence,
    modality="TYPE_A"
)

print(f"Score: {result.score:.2f}")
print(f"Quality: {result.quality_level}")
```

### Error Handling

The module uses strict validation and will raise exceptions on invalid input:

```python
from scoring.scoring import (
    apply_scoring,
    ModalityValidationError,
    EvidenceStructureError,
)

try:
    result = apply_scoring(...)
except ModalityValidationError as e:
    print(f"Invalid modality or evidence structure: {e}")
except EvidenceStructureError as e:
    print(f"Missing or invalid evidence keys: {e}")
```

### Reproducibility

The `ScoredResult` includes an evidence hash for reproducibility verification:

```python
result1 = apply_scoring(evidence=evidence, ...)
result2 = apply_scoring(evidence=evidence, ...)

assert result1.evidence_hash == result2.evidence_hash
assert result1.score == result2.score
```

## API Reference

### Main Functions

#### `apply_scoring()`

Apply scoring to evidence using specified modality.

**Parameters**:
- `question_global` (int): Global question number (1-300)
- `base_slot` (str): Question slot identifier
- `policy_area` (str): Policy area ID (PA01-PA10)
- `dimension` (str): Dimension ID (DIM01-DIM06)
- `evidence` (dict): Evidence dictionary
- `modality` (str): Scoring modality (TYPE_A through TYPE_F)
- `quality_thresholds` (dict, optional): Custom quality thresholds

**Returns**: `ScoredResult`

**Raises**:
- `ModalityValidationError`: If evidence validation fails
- `ScoringError`: If scoring fails

#### `determine_quality_level()`

Determine quality level from normalized score.

**Parameters**:
- `normalized_score` (float): Score normalized to 0-1 range
- `thresholds` (dict, optional): Custom thresholds

**Returns**: `QualityLevel`

### Classes

#### `ScoredResult`

Reproducible scored result dataclass.

**Attributes**:
- `question_global` (int): Global question number
- `base_slot` (str): Question slot identifier
- `policy_area` (str): Policy area ID
- `dimension` (str): Dimension ID
- `modality` (str): Scoring modality used
- `score` (float): Raw score value
- `normalized_score` (float): Normalized score (0-1)
- `quality_level` (str): Quality level classification
- `evidence_hash` (str): SHA-256 hash of evidence
- `metadata` (dict): Additional scoring metadata
- `timestamp` (str): ISO timestamp of scoring

#### `ScoringValidator`

Validates evidence structure against modality requirements.

**Methods**:
- `validate(evidence, modality)`: Validate evidence structure
- `get_config(modality)`: Get configuration for a modality

### Enums

#### `ScoringModality`

Scoring modality types: `TYPE_A`, `TYPE_B`, `TYPE_C`, `TYPE_D`, `TYPE_E`, `TYPE_F`

#### `QualityLevel`

Quality level classifications: `EXCELENTE`, `BUENO`, `ACEPTABLE`, `INSUFICIENTE`

### Exceptions

#### `ScoringError`

Base exception for scoring errors.

#### `ModalityValidationError`

Raised when evidence structure doesn't match modality requirements.

#### `EvidenceStructureError`

Raised when evidence structure is invalid.

## Testing

Run the test suite:

```bash
python tests/test_scoring.py
```

Run the demo:

```bash
python examples/demo_scoring.py
```

## Implementation Notes

### Preconditions

- Evidence and modality must be declared
- Evidence structure must match modality requirements

### Invariants

- Score range is maintained per modality definition
- Evidence structure is validated before scoring
- Same evidence produces same result (reproducibility)

### Postconditions

- `ScoredResult` is reproducible with same inputs
- No fallback or partial heuristic scoring
- All scoring steps logged

### Abortability

The module implements **strict abortability**:
- Any validation failure aborts with clear error
- No graceful degradation or fallback scoring
- Errors are logged at ERROR level
- Exceptions bubble up to caller

This ensures that scoring results are always complete and trustworthy, or not produced at all.
