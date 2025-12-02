# Processing Layer Test Suite

Comprehensive test suite for the FARFAN processing layer with property-based tests using Hypothesis and integration tests.

## Test Files Created

### 1. Property-Based Tests (Hypothesis)

#### `test_semantic_chunking_properties.py`
**Purpose**: Verify semantic chunking determinism

**Test Classes**:
- `TestSemanticChunkingDeterminism`: Core determinism properties
  - `test_chunking_is_deterministic`: Same input → same output
  - `test_chunks_preserve_all_text`: No text loss during chunking
  - `test_chunk_boundaries_are_coherent`: Clean boundaries without fragments
  - `test_chunk_sizes_respect_config`: Size limits respected
  - `test_chunks_have_required_fields`: Schema validation
  - `test_embeddings_are_deterministic`: Embedding stability

- `TestBayesianEvidenceProperties`: Bayesian integration
  - `test_evidence_integration_is_bounded`: Scores in [0,1]
  - `test_high_similarity_increases_confidence`: Monotonicity
  - `test_evidence_integration_is_symmetric`: Order independence

- `TestSemanticChunkingInvariants`: System invariants
  - `test_chunk_positions_are_monotonic`: Position ordering
  - `test_chunk_hashes_are_unique_for_different_content`: Hash uniqueness
  - `test_chunking_is_reproducible_with_seed`: Seed reproducibility

**Key Properties Tested**:
- Determinism: f(x) = f(x) for all x
- Idempotency: f(f(x)) = f(x)
- Completeness: All input preserved in output
- Consistency: Schema compliance across runs

#### `test_spc_ingestion_properties.py`
**Purpose**: Verify SPC ingestion pipeline idempotency

**Test Classes**:
- `TestSPCIngestionIdempotency`: Core idempotency
  - `test_ingestion_is_idempotent`: Multiple runs → same result
  - `test_chunk_hashes_are_stable`: Hash stability
  - `test_metadata_is_consistent`: Metadata preservation
  - `test_pdq_context_inference_is_stable`: PDQ inference stability

- `TestSPCIngestionInvariants`: Pipeline invariants
  - `test_chunks_cover_all_content`: 70%+ content coverage
  - `test_chunks_have_minimum_quality`: Quality thresholds
  - `test_chunk_boundaries_dont_duplicate_content`: <80% overlap

- `TestSPCIngestionCorrectness`: Correctness properties
  - `test_document_id_propagates_to_chunks`: ID preservation
  - `test_multiple_runs_produce_identical_output`: Bit-for-bit identical

**Key Properties Tested**:
- Idempotency: process(process(x)) = process(x)
- Stability: Hashes, metadata, PDQ context remain stable
- Coverage: Minimum 70% content retention
- Correctness: Document ID propagation

#### `test_embedding_policy_properties.py`
**Purpose**: Verify embedding policy consistency

**Test Classes**:
- `TestEmbeddingConsistency`: Embedding consistency
  - `test_embedding_dimensions_are_consistent`: Fixed dimensionality
  - `test_embeddings_are_deterministic`: Seed-based reproducibility
  - `test_embeddings_are_normalized`: Unit vector property
  - `test_similar_texts_have_similar_embeddings`: Similarity preservation

- `TestChunkingConfigurationInvariants`: Config validation
  - `test_config_invariants_hold`: Parameter constraints
  - `test_chunker_respects_config`: Configuration compliance

- `TestBayesianNumericalAnalyzerProperties`: Statistical properties
  - `test_bayesian_evaluation_produces_valid_credible_intervals`: [0,1] bounds
  - `test_bayesian_evaluation_is_bounded`: Output bounds
  - `test_more_data_reduces_uncertainty`: Uncertainty reduction

- `TestPDQContextInference`: PDQ inference
  - `test_pdq_context_structure_is_valid`: Schema validation
  - `test_pdq_inference_is_stable`: Stability across runs

**Key Properties Tested**:
- Consistency: Same dimensionality, normalization
- Determinism: Seed-based reproducibility
- Similarity: Similar inputs → similar embeddings
- Statistical validity: Bayesian credible intervals

### 2. Integration Tests (To Be Created)

#### `test_quality_gates_integration.py` (Planned)
**Purpose**: Integration tests for quality gates

**Planned Tests**:
- Input validation with valid/invalid PDFs
- Chunk validation with quality thresholds
- Output compatibility for downstream phases
- Quality metrics validation (provenance, structural consistency, boundary F1)
- Edge cases: empty documents, malformed chunks

**Critical Thresholds**:
- MIN_PROVENANCE_COMPLETENESS = 1.0 (100% required)
- MIN_STRUCTURAL_CONSISTENCY = 1.0 (100% required)
- MIN_BOUNDARY_F1 = 0.85
- MIN_BUDGET_CONSISTENCY = 0.95
- MIN_TEMPORAL_ROBUSTNESS = 0.80

#### `test_policy_processor_integration.py` (Planned)
**Purpose**: End-to-end policy processor tests with 150-page PDFs

**Planned Tests**:
- Large document processing (150+ pages)
- Memory efficiency validation
- Causal chain extraction accuracy
- Policy entity recognition
- Budget and KPI extraction
- Temporal dynamics parsing
- Performance benchmarks (<5min for 150-page PDF)

**Test Data Requirements**:
- Synthetic 150-page Colombian PDM documents
- Real-world anonymized PDM samples
- Edge cases: tables, charts, multi-column layouts

#### `test_aggregation_integration.py` (Planned)
**Purpose**: Aggregation pipeline correctness with mock scored results

**Planned Tests**:
- Dimension aggregation (5 questions → 1 dimension score)
- Policy area aggregation (6 dimensions → 1 area score)
- Cluster aggregation (multiple areas → 1 cluster score)
- Macro evaluation (all clusters → 1 holistic score)
- Weight validation and normalization
- Threshold enforcement
- Hermeticity validation
- Coverage error handling

**Mock Data Strategy**:
- Generate 300 mock ScoredResult instances (60 dimensions × 5 questions)
- Vary scores: low (0-0.4), medium (0.4-0.7), high (0.7-1.0)
- Test edge cases: missing dimensions, zero weights, threshold violations

## Running the Tests

### Property-Based Tests
```bash
# Run all property-based tests
pytest tests/processing/test_*_properties.py -v

# Run with coverage
pytest tests/processing/test_*_properties.py -v --cov=src.farfan_pipeline.processing --cov-report=term-missing

# Run specific test class
pytest tests/processing/test_semantic_chunking_properties.py::TestSemanticChunkingDeterminism -v

# Adjust Hypothesis examples for faster/slower runs
pytest tests/processing/ -v --hypothesis-seed=42
```

### Integration Tests
```bash
# Run all integration tests (when created)
pytest tests/processing/test_*_integration.py -v

# Run with specific markers
pytest tests/processing/ -v -m "integration"
pytest tests/processing/ -v -m "slow"
```

### Full Suite
```bash
# Run everything
pytest tests/processing/ -v --tb=short

# With coverage and report
pytest tests/processing/ -v --cov=src.farfan_pipeline.processing --cov-report=html
```

## Test Configuration

### Hypothesis Settings
- `max_examples`: 10-50 depending on test complexity
- `deadline`: 1000-15000ms depending on operation
- `suppress_health_check`: [HealthCheck.too_slow] for model-heavy tests

### Coverage Targets
- **Line coverage**: >85% for processing layer
- **Branch coverage**: >75% for complex logic
- **Critical paths**: 100% coverage (quality gates, aggregation)

## Key Testing Principles

1. **Determinism**: All processing must be deterministic with fixed seeds
2. **Idempotency**: Re-running operations produces identical results
3. **Invariants**: System properties hold under all inputs
4. **Correctness**: Output matches specification
5. **Performance**: Large documents (<5min for 150 pages)
6. **Quality**: Minimum thresholds enforced

## Dependencies

```python
# Testing framework
pytest==8.3.4
pytest-cov==6.0.0

# Property-based testing
hypothesis==6.122.3

# Already in requirements.txt:
# - numpy, pandas, scipy (data processing)
# - transformers, sentence-transformers (embeddings)
# - PyMuPDF (PDF processing)
```

## Maintenance

- **Add new tests**: When adding features to processing layer
- **Update properties**: When modifying core algorithms
- **Benchmark regularly**: Monitor performance regressions
- **Review coverage**: Ensure critical paths tested

## Known Limitations

1. **Disk space**: Large test data may require cleanup
2. **Model loading**: Transformers can be slow, use caching
3. **Hypothesis examples**: Trade-off between coverage and speed
4. **Integration tests**: Require realistic test data (PDFs)

## Future Enhancements

- [ ] Create remaining integration test files
- [ ] Add performance benchmarks with pytest-benchmark
- [ ] Generate synthetic 150-page PDM test documents
- [ ] Add mutation testing with mutmut
- [ ] Implement test data generators for realistic PDMs
- [ ] Add visual regression tests for PDF parsing
