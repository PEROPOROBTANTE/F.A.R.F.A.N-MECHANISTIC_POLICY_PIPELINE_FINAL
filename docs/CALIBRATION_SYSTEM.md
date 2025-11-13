# Calibration System Documentation

## Overview

The calibration system provides context-aware parameter adjustment for the policy analysis pipeline. It addresses calibration gap #9: "Implementation testing - NO empirical testing on real policy documents."

## Components

### 1. Calibration Registry (`src/saaaaaa/core/orchestrator/calibration_registry.py`)

The calibration registry manages base calibration parameters for orchestrator methods.

**Key Features:**
- Reads calibration data from `config/intrinsic_calibration.json`
- Provides default fallback values for uncalibrated methods
- Supports context-aware resolution

**Main Classes:**

```python
@dataclass(frozen=True)
class MethodCalibration:
    """Calibration parameters for an orchestrator method."""
    score_min: float
    score_max: float
    min_evidence_snippets: int
    max_evidence_snippets: int
    contradiction_tolerance: float  # 0.0-1.0
    uncertainty_penalty: float      # 0.0-1.0
    aggregation_weight: float
    sensitivity: float              # 0.0-1.0
    requires_numeric_support: bool
    requires_temporal_support: bool
    requires_source_provenance: bool
```

**Functions:**

```python
def resolve_calibration(class_name: str, method_name: str) -> MethodCalibration:
    """Get base calibration for a method."""

def resolve_calibration_with_context(
    class_name: str, 
    method_name: str,
    question_id: Optional[str] = None,
    **kwargs
) -> MethodCalibration:
    """Get calibration with context-aware adjustments."""
```

**Usage Example:**

```python
from saaaaaa.core.orchestrator.calibration_registry import (
    resolve_calibration,
    resolve_calibration_with_context
)

# Get base calibration
base = resolve_calibration("SemanticAnalyzer", "extract_entities")
print(f"Evidence range: {base.min_evidence_snippets}-{base.max_evidence_snippets}")

# Get calibration with context
contextual = resolve_calibration_with_context(
    "SemanticAnalyzer", 
    "extract_entities",
    question_id="D1Q1"
)
print(f"Adjusted range: {contextual.min_evidence_snippets}-{contextual.max_evidence_snippets}")
```

### 2. Calibration Context (`src/saaaaaa/core/orchestrator/calibration_context.py`)

The calibration context module provides context-aware modifiers based on question characteristics.

**Key Features:**
- Immutable context updates
- Question ID parsing (D1Q1, D6Q3, etc.)
- Composable modifiers for dimension, policy area, and unit of analysis
- Automatic value clamping to valid ranges

**Main Classes:**

```python
@dataclass(frozen=True)
class CalibrationContext:
    """Context information for calibration adjustment."""
    question_id: str
    dimension: int
    question_num: int
    policy_area: PolicyArea
    unit_of_analysis: UnitOfAnalysis
    method_position: int
    total_methods: int
    
    @classmethod
    def from_question_id(cls, question_id: str) -> CalibrationContext:
        """Parse question ID (e.g., 'D1Q1') into context."""
    
    def with_policy_area(self, policy_area: PolicyArea) -> CalibrationContext:
        """Create copy with updated policy area."""
    
    def with_unit_of_analysis(self, unit: UnitOfAnalysis) -> CalibrationContext:
        """Create copy with updated unit of analysis."""
    
    def with_method_position(self, position: int, total: int) -> CalibrationContext:
        """Create copy with updated method position."""
```

```python
@dataclass(frozen=True)
class CalibrationModifier:
    """Modifier for adjusting calibration parameters."""
    min_evidence_multiplier: float = 1.0
    max_evidence_multiplier: float = 1.0
    contradiction_tolerance_multiplier: float = 1.0
    uncertainty_penalty_multiplier: float = 1.0
    aggregation_weight_multiplier: float = 1.0
    sensitivity_multiplier: float = 1.0
    
    def apply(self, calibration: MethodCalibration) -> MethodCalibration:
        """Apply modifier to calibration."""
```

**Enums:**

```python
class PolicyArea(Enum):
    UNKNOWN = "unknown"
    FISCAL = "fiscal"
    SOCIAL = "social"
    INFRASTRUCTURE = "infrastructure"
    ENVIRONMENTAL = "environmental"
    GOVERNANCE = "governance"
    ECONOMIC = "economic"
    HEALTH = "health"
    EDUCATION = "education"
    SECURITY = "security"
    CULTURE = "culture"

class UnitOfAnalysis(Enum):
    UNKNOWN = "unknown"
    BASELINE_GAP = "baseline_gap"
    INTERVENTION = "intervention"
    OUTCOME = "outcome"
    MECHANISM = "mechanism"
    CONTEXT = "context"
    TIMEFRAME = "timeframe"
    STAKEHOLDER = "stakeholder"
    RESOURCE = "resource"
    RISK = "risk"
    ASSUMPTION = "assumption"
```

**Usage Example:**

```python
from saaaaaa.core.orchestrator.calibration_context import (
    CalibrationContext,
    CalibrationModifier,
    PolicyArea,
    resolve_contextual_calibration
)
from saaaaaa.core.orchestrator.calibration_registry import MethodCalibration

# Create context from question ID
context = CalibrationContext.from_question_id("D1Q1")
print(f"Dimension: {context.dimension}, Question: {context.question_num}")

# Add policy area
context = context.with_policy_area(PolicyArea.FISCAL)

# Create base calibration
base = MethodCalibration(
    score_min=0.0,
    score_max=1.0,
    min_evidence_snippets=10,
    max_evidence_snippets=20,
    contradiction_tolerance=0.1,
    uncertainty_penalty=0.3,
    aggregation_weight=1.0,
    sensitivity=0.75,
    requires_numeric_support=False,
    requires_temporal_support=False,
    requires_source_provenance=True,
)

# Apply contextual adjustments
adjusted = resolve_contextual_calibration(base, context)
print(f"Adjusted min_evidence: {base.min_evidence_snippets} -> {adjusted.min_evidence_snippets}")
```

### 3. Empirical Testing Framework (`scripts/test_calibration_empirically.py`)

The empirical testing framework compares base and contextual calibration effectiveness on real policy documents.

**Features:**
- Runs pipeline with base calibration (no context)
- Runs pipeline with contextual calibration
- Computes effectiveness metrics
- Generates comparison report with recommendations
- Outputs JSON results

**Metrics Computed:**

```python
@dataclass
class CalibrationMetrics:
    # Evidence collection
    avg_evidence_snippets: float
    evidence_usage_rate: float
    
    # Confidence
    avg_confidence: float
    confidence_variance: float
    
    # Quality
    contradiction_rate: float
    uncertainty_rate: float
    
    # Performance
    execution_time_s: float
    total_questions: int
    successful_questions: int
    
    # Calibration-specific
    context_adjustments_applied: int
    avg_sensitivity: float
    avg_aggregation_weight: float
```

**Usage:**

```bash
# Test with default plan (data/plans/Plan_1.pdf)
python scripts/test_calibration_empirically.py

# Test with specific plan
python scripts/test_calibration_empirically.py --plan data/plans/Plan_2.pdf

# Specify output file
python scripts/test_calibration_empirically.py --output results.json
```

**Output:**

The script produces:
1. Console output with metrics comparison
2. JSON file with detailed results and recommendations
3. Improvement percentages for each metric

Example recommendations:
- "✓ Context-aware calibration improved confidence by 15.2%"
- "✓ Context-aware calibration reduced contradictions by 23.4%"
- "✓ Applied context adjustments to 87 questions"

## Dimension-Specific Modifiers

| Dimension | Adjustments |
|-----------|-------------|
| D1 | min_evidence × 1.3, sensitivity × 1.1 |
| D2 | max_evidence × 1.2, contradiction_tolerance × 0.8 |
| D3 | min_evidence × 1.2, uncertainty_penalty × 0.9 |
| D4 | sensitivity × 1.2 |
| D5 | min_evidence × 1.1, max_evidence × 1.1 |
| D6 | contradiction_tolerance × 0.9 |
| D7 | uncertainty_penalty × 0.85 |
| D8 | aggregation_weight × 1.15 |
| D9 | sensitivity × 1.15 |
| D10 | min_evidence × 1.4, sensitivity × 1.2 |

## Policy Area Modifiers

| Policy Area | Adjustments |
|-------------|-------------|
| FISCAL | min_evidence × 1.3, sensitivity × 1.1 |
| SOCIAL | max_evidence × 1.2, uncertainty_penalty × 0.9 |
| INFRASTRUCTURE | contradiction_tolerance × 0.8, sensitivity × 1.1 |
| ENVIRONMENTAL | min_evidence × 1.2, uncertainty_penalty × 0.85 |

## Unit of Analysis Modifiers

| Unit | Adjustments |
|------|-------------|
| BASELINE_GAP | min_evidence × 1.4, sensitivity × 1.2 |
| INTERVENTION | contradiction_tolerance × 0.9, sensitivity × 1.1 |
| OUTCOME | min_evidence × 1.3, uncertainty_penalty × 0.8 |
| MECHANISM | max_evidence × 1.2, sensitivity × 1.15 |

## Validation

Run validation tests:

```bash
python scripts/validate_calibration_modules.py
```

This validates:
- MethodCalibration creation and validation
- Question ID parsing (D1Q1, d2q5, D10Q25)
- Context immutability
- CalibrationModifier application
- Contextual resolution
- Integration between modules

## Integration with Orchestrator

The calibration system is designed to integrate with the orchestrator's method execution:

```python
from saaaaaa.core.orchestrator import Orchestrator
from saaaaaa.core.orchestrator.factory import build_processor
from saaaaaa.core.orchestrator.calibration_registry import resolve_calibration_with_context

# Build processor
processor = build_processor()

# Create orchestrator
orchestrator = Orchestrator(monolith=processor.questionnaire)

# In your method executor, use calibration:
calibration = resolve_calibration_with_context(
    class_name="YourClass",
    method_name="your_method",
    question_id="D1Q1"
)

# Use calibration parameters
min_evidence = calibration.min_evidence_snippets
max_evidence = calibration.max_evidence_snippets
# ... etc
```

## Testing

Existing tests in `tests/test_calibration_context.py` cover:
- CalibrationContext creation from question IDs
- Immutable context updates
- CalibrationModifier identity and application
- Value clamping
- Contextual calibration resolution
- Integration between registry and context modules

## Design Principles

1. **Immutability**: All context updates create new instances
2. **Composability**: Modifiers apply sequentially
3. **Determinism**: Same inputs always produce same outputs
4. **Graceful Degradation**: Missing calibration data uses defaults
5. **Type Safety**: Extensive use of dataclasses and enums
6. **Traceability**: All adjustments are logged and reversible

## Files

```
src/saaaaaa/core/orchestrator/
  ├── calibration_registry.py    (226 lines) - Base calibration resolution
  └── calibration_context.py     (339 lines) - Context-aware modifiers

scripts/
  ├── test_calibration_empirically.py   (452 lines) - Empirical testing framework
  └── validate_calibration_modules.py   (166 lines) - Validation tests

config/
  └── intrinsic_calibration.json - Calibration data (read by registry)

tests/
  └── test_calibration_context.py - Unit tests (existing)

docs/
  └── CALIBRATION_SYSTEM.md - This documentation
```

## Future Enhancements

Potential improvements:
1. Machine learning-based calibration adjustment
2. A/B testing framework for calibration strategies
3. Real-time calibration adaptation based on results
4. Calibration effectiveness tracking over time
5. Policy area inference from document content
6. Automated calibration tuning based on gold standard results

## References

- Problem Statement: Calibration Gap #9
- Three-Pillar Calibration System: `canonic_calibration_methods.md`
- Intrinsic Calibration Rubric: `config/intrinsic_calibration_rubric.json`
- Method Catalog: Built by `scripts/build_canonical_method_catalog.py`
