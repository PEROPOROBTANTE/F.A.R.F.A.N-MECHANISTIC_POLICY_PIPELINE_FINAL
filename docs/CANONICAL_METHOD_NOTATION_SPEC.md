# Canonical Method Notation Specification

## Overview

This specification defines a rigorous, exhaustive notation system for methods in the SAAAAAA policy analysis framework. The notation must capture:
1. Method identity and classification
2. Calibration requirements and status
3. Execution characteristics
4. Integration layer assignments

## Notation Format

### Primary Notation Structure

```
<MODULE>:<CLASS>.<METHOD>@<LAYER>[<FLAGS>]{<CALIBRATION_STATUS>}
```

### Components

#### 1. MODULE (Required)
Identifies the source module/file:
- `FIN` = financiero_viabilidad_tablas.py
- `ANA` = Analyzer_one.py  
- `CON` = contradiction_deteccion.py
- `EMB` = embedding_policy.py
- `TEO` = teoria_cambio.py
- `SEM` = semantic_chunking_policy.py
- `POL` = policy_processor.py
- `DER` = derek_beach.py
- `AGG` = aggregation.py
- `SCO` = scoring.py
- `REC` = recommendation_engine.py
- `EXE` = executors (various)

#### 2. CLASS (Required)
The Python class containing the method

#### 3. METHOD (Required)
The method name

#### 4. LAYER (Required)
Analysis layer assignment:
- `@Q` = Question layer (micro-question resolution)
- `@D` = Dimension layer (D1-D6 analytical dimension)
- `@P` = Policy Area layer (PA01-PA10)
- `@C` = Congruence layer (executor method ensembles)
- `@M` = Meta layer (aggregation, scoring, reporting)

#### 5. FLAGS (Optional)
Execution characteristics:
- `N` = Requires numeric support
- `T` = Requires temporal support
- `S` = Requires source provenance
- `B` = Bayesian inference
- `A` = Async-capable
- `I` = I/O-intensive
- `C` = Compute-intensive

#### 6. CALIBRATION_STATUS (Required)
Calibration requirement and status:
- `{CAL}` = Calibrated (present in calibration_registry)
- `{REQ}` = Requires calibration (not yet calibrated)
- `{OPT}` = Optional calibration (utility/helper method)
- `{DER}` = Derived (uses other calibrated methods)
- `{INS}` = In-script calibration (hard-coded parameters)

### Extended Notation (for catalog storage)

Full catalog entry format:
```json
{
  "canonical_id": "<MODULE>:<CLASS>.<METHOD>@<LAYER>[<FLAGS>]{<CALIBRATION_STATUS>}",
  "class": "<CLASS>",
  "method_name": "<METHOD>",
  "module": "<MODULE>",
  "file": "<source_file>.py",
  "layer": "<LAYER>",
  "flags": ["<FLAG1>", "<FLAG2>"],
  "calibration_status": "<STATUS>",
  "calibration_ref": "<calibration_registry_key>",
  "signature": "<method_signature>",
  "complexity": "<LOW|MEDIUM|HIGH>",
  "priority": "<LOW|MEDIUM|HIGH|CRITICAL>",
  "dependencies": [],
  "prerequisites": [],
  "execution_requirements": {},
  "calibration_params": {
    "score_min": 0.0,
    "score_max": 1.0,
    "min_evidence_snippets": 1,
    "max_evidence_snippets": 10,
    "contradiction_tolerance": 0.5,
    "uncertainty_penalty": 0.2,
    "aggregation_weight": 1.0,
    "sensitivity": 0.8,
    "requires_numeric_support": false,
    "requires_temporal_support": false,
    "requires_source_provenance": false,
    "layer_weights": {
      "question": 1.0,
      "dimension": 1.0,
      "policy_area": 1.0,
      "congruence": 1.0
    }
  },
  "docstring": "<method documentation>",
  "line_number": 123,
  "aptitude_score": 95.5
}
```

## Examples

### Example 1: Bayesian Method (Calibrated)
```
FIN:BayesianNumericalAnalyzer.analyze_numeric_pattern@Q[NBS]{CAL}
```
- Module: FIN (financiero_viabilidad_tablas.py)
- Class: BayesianNumericalAnalyzer
- Method: analyze_numeric_pattern
- Layer: @Q (Question)
- Flags: N (numeric), B (bayesian), S (source)
- Calibration: {CAL} (calibrated in registry)

### Example 2: Executor Method (Requires Calibration)
```
EXE:CausalExtractor.extract_mechanism@C[NTSA]{REQ}
```
- Module: EXE (executors)
- Class: CausalExtractor
- Method: extract_mechanism
- Layer: @C (Congruence - part of executor ensemble)
- Flags: N, T, S, A (numeric, temporal, source, async)
- Calibration: {REQ} (needs calibration)

### Example 3: Aggregation Method (Derived)
```
AGG:WeightedAggregator.aggregate_scores@M[]{DER}
```
- Module: AGG (aggregation.py)
- Class: WeightedAggregator
- Method: aggregate_scores
- Layer: @M (Meta)
- Flags: None
- Calibration: {DER} (derives from calibrated inputs)

### Example 4: Helper Method (Optional)
```
ANA:TextProcessor._clean_unicode@Q[]{OPT}
```
- Module: ANA (Analyzer_one.py)
- Class: TextProcessor
- Method: _clean_unicode
- Layer: @Q (Question)
- Flags: None
- Calibration: {OPT} (utility method, no calibration needed)

## Layer Assignment Rules

### @Q (Question Layer)
Methods that directly contribute to answering micro-questions:
- Evidence extraction
- Pattern matching
- Text analysis for specific questions
- Base slot resolution

### @D (Dimension Layer)
Methods that operate across dimension (D1-D6):
- Dimension-level aggregation
- Cross-question synthesis within dimension
- Dimensional coherence checks

### @P (Policy Area Layer)
Methods that operate across policy areas (PA01-PA10):
- Cross-area integration
- Policy coherence analysis
- Inter-area relationship detection

### @C (Congruence Layer)
Methods that participate in executor ensembles:
- Multiple methods working together
- Sequential or parallel execution
- Method output chaining
- Requires congruence calibration

### @M (Meta Layer)
System-level operations:
- Aggregation across layers
- Scoring and weighting
- Report generation
- Recommendation synthesis

## Calibration Requirements by Layer

### Question Layer (@Q)
**Parameters:**
- `question_weight`: Contribution to question answer (0.0-1.0)
- `evidence_threshold`: Minimum evidence quality (0.0-1.0)
- `base_slot_sensitivity`: Response to base slot context

**Formula:**
```
Q_score = (evidence_score × question_weight) / (1 + uncertainty_penalty)
```

### Dimension Layer (@D)
**Parameters:**
- `dimension_weight`: Contribution to dimension score
- `cross_question_coherence`: Inter-question consistency requirement
- `dimensional_sensitivity`: Response to D1-D6 context

**Formula:**
```
D_score = ∑(Q_scores × dimension_weight) / num_questions
```

### Policy Area Layer (@P)
**Parameters:**
- `policy_area_weight`: Contribution to policy area score
- `cross_policy_coherence`: Inter-area consistency requirement
- `area_sensitivity`: Response to PA01-PA10 context

**Formula:**
```
P_score = ∑(D_scores × policy_area_weight) / num_dimensions
```

### Congruence Layer (@C)
**Parameters:**
- `ensemble_weight`: Method's weight in executor ensemble
- `sequence_position`: Position in execution sequence
- `congruence_factor`: Adjustment for ensemble harmony
- `predecessor_influence`: Impact of previous methods
- `successor_sensitivity`: Preparation for next methods

**Formula (Complex):**
```
C_score = (method_score × ensemble_weight × congruence_factor) + 
          (predecessor_scores × predecessor_influence) - 
          (disruption_penalty × (1 - congruence_factor))
```

### Meta Layer (@M)
**Parameters:**
- `aggregation_function`: SUM, AVG, WEIGHTED_AVG, MAX, MIN
- `layer_weights`: Weights for Q, D, P, C layers
- `normalization_strategy`: How to normalize across layers

**Formula:**
```
M_score = aggregation_function(
    Q_scores × layer_weights['question'],
    D_scores × layer_weights['dimension'],
    P_scores × layer_weights['policy_area'],
    C_scores × layer_weights['congruence']
)
```

## Integration with calibration_registry.py

The calibration registry must be extended to support:

```python
@dataclass(frozen=True)
class CanonicalMethodCalibration:
    """Extended calibration with canonical notation support."""
    
    # Canonical identification
    canonical_id: str  # Full notation
    module: str
    class_name: str
    method_name: str
    layer: str  # Q, D, P, C, M
    flags: tuple[str, ...]
    calibration_status: str
    
    # Base calibration (from MethodCalibration)
    score_min: float
    score_max: float
    min_evidence_snippets: int
    max_evidence_snippets: int
    contradiction_tolerance: float
    uncertainty_penalty: float
    aggregation_weight: float
    sensitivity: float
    requires_numeric_support: bool
    requires_temporal_support: bool
    requires_source_provenance: bool
    
    # Layer-specific calibration
    layer_weights: dict[str, float]  # Q, D, P, C weights
    question_weight: float = 1.0  # @Q layer
    dimension_weight: float = 1.0  # @D layer
    policy_area_weight: float = 1.0  # @P layer
    ensemble_weight: float = 1.0  # @C layer
    congruence_factor: float = 1.0  # @C layer
    
    # Meta-layer configuration
    aggregation_function: str = "WEIGHTED_AVG"
    normalization_strategy: str = "MINMAX"
```

## Alignment Requirements

### 1. complete_canonical_catalog.json
Must include:
- `canonical_id` field using this notation
- `layer` assignment
- `flags` array
- `calibration_status`
- `calibration_params` object

### 2. calibration_registry.py
Must support:
- Loading methods from canonical catalog
- Mapping canonical_id to calibration
- Layer-specific parameter access
- Congruence calculation for @C layer

### 3. calibration_context.py
Must provide:
- Context resolution from canonical_id
- Layer-aware calibration lookup
- Dynamic parameter adjustment based on context

### 4. analysis/factory.py
Must support:
- Loading calibrations by canonical_id
- Merging YAML and Python calibrations
- Path resolution for calibration files

## Implementation Priority

1. **Phase 1** (Completed): Rename catalog to canonical name
2. **Phase 2** (Current): Define canonical notation spec
3. **Phase 3**: Update catalog with canonical_id fields
4. **Phase 4**: Extend calibration_registry with layer support
5. **Phase 5**: Implement congruence calculations
6. **Phase 6**: Comprehensive method audit and updates
