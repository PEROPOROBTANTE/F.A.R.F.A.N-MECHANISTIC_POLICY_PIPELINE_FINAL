# Integration Tests TODO

The following integration test files need to be created to complete the test suite.

## 1. test_quality_gates_integration.py

**Purpose**: Integration tests for SPCQualityGates validation

**Required Test Cases**:

```python
class TestQualityGatesInputValidation:
    def test_validate_valid_pdf_document()
    def test_validate_empty_document_fails()
    def test_validate_oversized_document_fails()
    def test_validate_unsupported_file_type_fails()

class TestQualityGatesChunkValidation:
    def test_validate_chunks_with_sufficient_count()
    def test_validate_chunks_with_insufficient_count_fails()
    def test_validate_chunks_with_low_quality_warnings()
    def test_validate_chunks_with_missing_fields_fails()
    def test_validate_chunk_text_length_boundaries()

class TestQualityGatesOutputCompatibility:
    def test_validate_compatible_output_structure()
    def test_validate_missing_metadata_fails()
    def test_validate_missing_chunks_fails()

class TestQualityGatesMetrics:
    def test_validate_metrics_all_pass()
    def test_validate_metrics_provenance_failure()
    def test_validate_metrics_structural_consistency_failure()
    def test_validate_metrics_boundary_f1_failure()
    def test_validate_metrics_budget_consistency_warning()
```

**Critical Assertions**:
- Provenance completeness = 1.0 (100% required)
- Structural consistency = 1.0 (100% required)
- Boundary F1 >= 0.85
- Budget consistency >= 0.95
- Temporal robustness >= 0.80

## 2. test_policy_processor_integration.py

**Purpose**: End-to-end policy processor tests with realistic documents

**Required Test Cases**:

```python
class TestPolicyProcessorEndToEnd:
    def test_process_small_document_50_pages()
    def test_process_medium_document_100_pages()
    def test_process_large_document_150_pages()
    def test_processing_time_under_5_minutes_for_150_pages()
    def test_memory_usage_under_2gb_for_150_pages()

class TestCausalChainExtraction:
    def test_extract_causal_chains_from_diagnostic_section()
    def test_extract_causal_chains_from_strategy_section()
    def test_extract_multi_hop_causal_reasoning()
    def test_causal_chain_confidence_scores()

class TestPolicyEntityRecognition:
    def test_recognize_government_entities()
    def test_recognize_beneficiary_groups()
    def test_recognize_funding_sources()
    def test_recognize_geographic_entities()

class TestBudgetAndKPIExtraction:
    def test_extract_budget_from_tables()
    def test_extract_budget_from_narrative_text()
    def test_extract_kpis_with_targets()
    def test_extract_temporal_information()

class TestComplexLayouts:
    def test_process_multi_column_layout()
    def test_process_document_with_charts()
    def test_process_document_with_complex_tables()
    def test_process_document_with_footnotes()
```

**Test Data Requirements**:
- Create synthetic 50/100/150-page PDM documents using fpdf2 or reportlab
- Include realistic Colombian PDM structure (Ley 152/1994)
- Include tables, budgets, KPIs, causal statements
- Add edge cases: rotated pages, multi-column, embedded images

**Performance Benchmarks**:
- 50 pages: <2 minutes
- 100 pages: <3.5 minutes
- 150 pages: <5 minutes
- Memory: <2GB peak

## 3. test_aggregation_integration.py

**Purpose**: Aggregation pipeline correctness with mock data

**Required Test Cases**:

```python
class TestDimensionAggregation:
    def test_aggregate_5_questions_to_dimension()
    def test_dimension_aggregation_with_weights()
    def test_dimension_aggregation_rejects_insufficient_questions()
    def test_dimension_aggregation_validates_weights_sum_to_one()
    def test_dimension_aggregation_applies_quality_thresholds()

class TestAreaAggregation:
    def test_aggregate_6_dimensions_to_area()
    def test_area_aggregation_with_custom_weights()
    def test_area_aggregation_rejects_missing_dimensions()
    def test_area_aggregation_handles_zero_weight_dimensions()

class TestClusterAggregation:
    def test_aggregate_multiple_areas_to_cluster()
    def test_cluster_coherence_calculation()
    def test_cluster_variance_calculation()
    def test_cluster_identifies_weakest_area()

class TestMacroAggregation:
    def test_aggregate_all_clusters_to_macro_score()
    def test_macro_cross_cutting_coherence()
    def test_macro_identifies_systemic_gaps()
    def test_macro_strategic_alignment_score()

class TestAggregationInvariants:
    def test_aggregation_is_deterministic()
    def test_aggregation_respects_weight_constraints()
    def test_aggregation_scores_in_valid_range()
    def test_aggregation_preserves_quality_levels()

class TestAggregationEdgeCases:
    def test_handle_all_zero_scores()
    def test_handle_all_perfect_scores()
    def test_handle_missing_optional_dimensions()
    def test_handle_conflicting_quality_levels()
```

**Mock Data Strategy**:

```python
def generate_mock_scored_results(
    n_areas: int = 10,
    n_dimensions: int = 6,
    n_questions: int = 5,
    score_distribution: str = "mixed"  # "low", "medium", "high", "mixed"
) -> list[ScoredResult]:
    """Generate realistic mock ScoredResult instances."""
    # Total: 10 areas × 6 dimensions × 5 questions = 300 results
    # Vary scores based on distribution:
    # - low: 0-0.4
    # - medium: 0.4-0.7
    # - high: 0.7-1.0
    # - mixed: random from all ranges
```

**Validation Points**:
- All scores in [0, 1]
- Quality levels match score thresholds
- Weights sum to 1.0 at each level
- Coverage requirements met
- Hermeticity maintained

## Implementation Priority

1. **High Priority**: test_aggregation_integration.py
   - Critical for phase 4-7 validation
   - Can use pure mock data (no external dependencies)
   - Fast to run

2. **Medium Priority**: test_quality_gates_integration.py
   - Important for phase 1 validation
   - Requires sample PDFs but can use small ones
   - Moderate runtime

3. **Low Priority**: test_policy_processor_integration.py
   - Most complex to implement
   - Requires large test PDFs (150 pages)
   - Slow to run (benchmarking)
   - Consider marking as @pytest.mark.slow

## Estimated Effort

- test_aggregation_integration.py: 4-6 hours
  - Mock data generator: 1 hour
  - Test cases: 3-4 hours
  - Edge cases: 1 hour

- test_quality_gates_integration.py: 3-4 hours
  - Sample PDF creation: 1 hour
  - Test cases: 2-3 hours

- test_policy_processor_integration.py: 8-12 hours
  - Large PDF generation: 3-4 hours
  - Test infrastructure: 2-3 hours
  - Test cases: 3-5 hours

**Total**: 15-22 hours

## Running Instructions (Future)

```bash
# Run only integration tests
pytest tests/processing/test_*_integration.py -v

# Run without slow tests
pytest tests/processing/ -v -m "not slow"

# Run with coverage
pytest tests/processing/ -v --cov=src.farfan_pipeline.processing --cov-report=html

# Run with performance profiling
pytest tests/processing/test_policy_processor_integration.py -v --profile
```
