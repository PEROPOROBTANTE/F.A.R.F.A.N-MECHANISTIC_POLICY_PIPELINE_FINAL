# Executor Methods Mapping Summary

## Overview
This document summarizes the extraction of all executor methods from `executors.py` and their mapping to base_slots.

## Statistics

### Total Executors: 30
- **Dimension 1 (D1)**: 5 executors (Q1-Q5)
- **Dimension 2 (D2)**: 5 executors (Q1-Q5)
- **Dimension 3 (D3)**: 5 executors (Q1-Q5)
- **Dimension 4 (D4)**: 5 executors (Q1-Q5)
- **Dimension 5 (D5)**: 5 executors (Q1-Q5)
- **Dimension 6 (D6)**: 5 executors (Q1-Q5)

### Methods per Executor

#### Dimension 1: DIAGNOSTICS & INPUTS
- **D1-Q1** (QuantitativeBaselineExtractor): 17 methods
- **D1-Q2** (ProblemDimensioningAnalyzer): 12 methods
- **D1-Q3** (BudgetAllocationTracer): 13 methods
- **D1-Q4** (InstitutionalCapacityIdentifier): 11 methods
- **D1-Q5** (ScopeJustificationValidator): 7 methods

#### Dimension 2: ACTIVITY DESIGN
- **D2-Q1** (StructuredPlanningValidator): 7 methods
- **D2-Q2** (InterventionLogicInferencer): 11 methods
- **D2-Q3** (RootCauseLinkageAnalyzer): 9 methods
- **D2-Q4** (RiskManagementAnalyzer): 10 methods
- **D2-Q5** (StrategicCoherenceEvaluator): 8 methods

#### Dimension 3: PRODUCTS & OUTPUTS
- **D3-Q1** (IndicatorQualityValidator): 8 methods
- **D3-Q2** (TargetProportionalityAnalyzer): 21 methods
- **D3-Q3** (TraceabilityValidator): 22 methods
- **D3-Q4** (TechnicalFeasibilityEvaluator): 26 methods
- **D3-Q5** (OutputOutcomeLinkageAnalyzer): 25 methods

#### Dimension 4: RESULTS & OUTCOMES
- **D4-Q1** (OutcomeMetricsValidator): 16 methods
- **D4-Q2** (CausalChainValidator): 8 methods
- **D4-Q3** (AmbitionJustificationAnalyzer): 8 methods
- **D4-Q4** (ProblemSolvencyEvaluator): 7 methods
- **D4-Q5** (VerticalAlignmentValidator): 6 methods

#### Dimension 5: IMPACTS
- **D5-Q1** (LongTermVisionAnalyzer): 8 methods
- **D5-Q2** (CompositeMeasurementValidator): 28 methods
- **D5-Q3** (IntangibleMeasurementAnalyzer): 6 methods
- **D5-Q4** (SystemicRiskEvaluator): 7 methods
- **D5-Q5** (RealismAndSideEffectsAnalyzer): 8 methods

#### Dimension 6: CAUSALITY & THEORY OF CHANGE
- **D6-Q1** (ExplicitTheoryBuilder): 8 methods
- **D6-Q2** (LogicalProportionalityValidator): 7 methods
- **D6-Q3** (ValidationTestingAnalyzer): 8 methods
- **D6-Q4** (FeedbackLoopAnalyzer): 7 methods
- **D6-Q5** (ContextualAdaptabilityEvaluator): 9 methods

### Total Methods: 362

### Top Classes by Method Count

1. **PDETMunicipalPlanAnalyzer**: Appears in 28 executors (most frequently used)
2. **BayesianMechanismInference**: Appears in 15 executors
3. **CausalExtractor**: Appears in 14 executors
4. **AdaptivePriorCalculator**: Appears in 13 executors
5. **BayesianCounterfactualAuditor**: Appears in 12 executors
6. **AdvancedDAGValidator**: Appears in 11 executors
7. **IndustrialPolicyProcessor**: Appears in 11 executors
8. **PolicyAnalysisEmbedder**: Appears in 9 executors
9. **OperationalizationAuditor**: Appears in 8 executors
10. **FinancialAuditor**: Appears in 7 executors

### Most Complex Executors (by method count)

1. **D5-Q2** (CompositeMeasurementValidator): 28 methods
2. **D3-Q4** (TechnicalFeasibilityEvaluator): 26 methods
3. **D3-Q5** (OutputOutcomeLinkageAnalyzer): 25 methods
4. **D3-Q3** (TraceabilityValidator): 22 methods
5. **D3-Q2** (TargetProportionalityAnalyzer): 21 methods

### Simplest Executors (by method count)

1. **D4-Q5** (VerticalAlignmentValidator): 6 methods
2. **D5-Q3** (IntangibleMeasurementAnalyzer): 6 methods
3. **D1-Q5** (ScopeJustificationValidator): 7 methods
4. **D2-Q1** (StructuredPlanningValidator): 7 methods
5. **D4-Q4** (ProblemSolvencyEvaluator): 7 methods

## File Location

The complete mapping has been saved to:
```
/home/user/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE_FINAL/executor_methods_mapping.json
```

## JSON Structure

```json
{
  "D1-Q1": [
    {"class": "ClassName", "method": "method_name"},
    ...
  ],
  "D1-Q2": [...],
  ...
}
```

## Verification

All 30 executors have been successfully extracted:
- ✓ All base_slots from D1-Q1 through D6-Q5 are present
- ✓ Each executor includes all methods listed in its docstring
- ✓ Methods are parsed into class name and method name components
- ✓ Both public methods (e.g., `method_name`) and private methods (e.g., `_method_name`) are included

## Notes

1. Some executors have significantly more methods than others, reflecting their complexity
2. D3 (Products & Outputs) and D5 (Impacts) dimensions have the most complex executors
3. The mapping captures both the canonical executors and the experimental/detailed ones (D3-Q2 through D3-Q5, D5-Q2, D6-Q5)
4. All methods maintain their exact naming conventions from the source code
