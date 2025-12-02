# Analysis Layer Test Suite

Comprehensive test coverage for the 7-producer analysis layer of the F.A.R.F.A.N mechanistic policy pipeline.

## Test Coverage Summary

- **Total Test Files**: 8
- **Total Test Cases**: 161
- **Total Lines of Code**: ~2,653
- **Coverage**: All 7 producers + integration tests

## Test Files

### 1. `test_semantic_analyzer.py` (301 lines, 22 tests)
Tests for semantic cube extraction and policy domain classification.

**Coverage:**
- SemanticAnalyzer initialization and configuration
- Semantic cube extraction with empty/valid segments
- Value chain link classification
- Policy domain classification  
- Cross-cutting theme detection
- TF-IDF vectorization
- Segment processing and complexity calculation
- Similarity threshold filtering
- Municipal ontology structure validation
- Integration tests with realistic segments

### 2. `test_contradiction_detector.py` (349 lines, 29 tests)
Tests for multi-dimensional contradiction detection.

**Coverage:**
- BayesianConfidenceCalculator with domain-informed priors
- Posterior probability calculation with evidence strength
- Domain weight effects on posterior
- TemporalLogicVerifier initialization and pattern matching
- Temporal consistency verification
- Temporal marker parsing (years, quarters, Spanish markers)
- Resource extraction and mutual exclusivity
- PolicyContradictionDetector with mocked transformers
- Numerical, temporal, semantic contradiction detection
- Coherence metrics calculation
- Resolution recommendation generation

### 3. `test_derek_beach_causal.py` (384 lines, 28 tests)
Tests for Derek Beach mechanistic evidence evaluation.

**Coverage:**
- BeachEvidentialTest taxonomy (hoop, smoking gun, doubly decisive, straw-in-wind)
- Test classification by necessity and sufficiency
- Bayesian test logic application with knock-out rules
- MetaNode data structure and entity-activity associations
- Audit flags mechanism
- EntityActivity tuples with confidence bounds
- CausalLink structure with Bayesian fields
- ConfigLoader with YAML validation
- Pydantic schema validation
- CDAFException structured error handling
- Integration tests for causal DAG construction

### 4. `test_teoria_cambio.py` (307 lines, 21 tests)
Tests for theory of change validation and DAG analysis.

**Coverage:**
- TeoriaCambio initialization and caching
- Canonical causal graph construction
- Connection validity checking between categories
- Complete validation with valid/invalid graphs
- Category extraction and order validation
- Complete path finding (INSUMOS → CAUSALIDAD)
- Suggestion generation for violations
- AdvancedGraphNode with metadata normalization
- Role validation and serialization
- Deterministic seed generation (SHA-512)
- Monte Carlo simulation structure
- AdvancedDAGValidator integration

### 5. `test_recommendation_engine.py` (407 lines, 27 tests)
Tests for multi-level rule-based recommendation generation.

**Coverage:**
- RecommendationEngine initialization with JSON schema validation
- MICRO-level recommendations (PA-DIM scores)
- MESO-level recommendations (cluster performance)
- MACRO-level recommendations (plan-level metrics)
- Template rendering with variable substitution
- Condition evaluation (score bands, variance levels)
- Recommendation and RecommendationSet data structures
- Metadata tracking and serialization
- Enhanced v2.0 fields (execution, budget)
- Hot-reloading of rules
- Integration tests for full pipeline

### 6. `test_bayesian_multilevel.py` (279 lines, 18 tests)
Tests for Bayesian multilevel analysis system.

**Coverage:**
- ReconciliationValidator with range/unit/period/entity validators
- Validation penalty calculation
- BayesianUpdater with probative test taxonomy
- Sequential Bayesian updating
- Likelihood ratio calculation for all test types
- Evidence weight calculation (KL divergence)
- CSV export for posterior tables
- DispersionEngine (CV, max gap, Gini coefficient)
- MicroLevelAnalysis pipeline integration
- Posterior sampling validation

### 7. `test_graph_metrics_fallback.py` (262 lines, 19 tests)
Tests for graph metrics computation with graceful degradation.

**Coverage:**
- NetworkX availability checking
- Graph metrics computation with edge list format
- Graph metrics computation with adjacency dict format
- Fallback handling when NetworkX unavailable
- Basic stats computation without NetworkX
- GraphMetricsInfo structure validation
- Observability integration (logging, metrics)
- Runtime config default handling
- Invalid/empty graph handling
- Integration tests for full pipeline with degradation

### 8. `test_financial_viability.py` (353 lines, 17 tests)
Tests for PDET municipal plan analysis and financial extraction.

**Coverage:**
- ColombianMunicipalContext (official systems, territorial categories)
- DNP dimensions and PDET pillars validation
- PDET theory of change structure
- PDETMunicipalPlanAnalyzer initialization
- DataFrame cleaning and header detection
- Table deduplication with semantic similarity
- ExtractedTable data structure (fragmentation support)
- FinancialIndicator with Decimal precision
- ResponsibleEntity with specificity scoring
- QualityScore with multi-dimensional metrics
- Integration tests for extraction pipeline

## Running Tests

```bash
# All analysis tests
python -m pytest tests/analysis/ -v

# Specific producer
python -m pytest tests/analysis/test_semantic_analyzer.py -v

# With coverage
python -m pytest tests/analysis/ -v --cov=farfan_pipeline.analysis --cov-report=term-missing

# Specific test
python -m pytest tests/analysis/test_bayesian_multilevel.py::TestBayesianUpdater::test_sequential_update -v
```

## Test Architecture

### Unit Tests
- Mock external dependencies (transformers, spaCy, NetworkX)
- Test individual functions and methods in isolation
- Validate data structures and contracts
- Assert pre/postconditions

### Integration Tests
- Test full pipelines end-to-end
- Validate inter-component interactions
- Test graceful degradation scenarios
- Verify observability integration

### Fixtures
- `pytest.fixture` for reusable test data
- Mock objects for expensive dependencies
- Temporary paths for file I/O tests
- Sample DataFrames and graphs

## Test Quality Standards

- ✅ Type hints on all test functions
- ✅ Docstrings explaining test purpose
- ✅ Descriptive assertion messages
- ✅ Edge case coverage (empty, invalid, boundary)
- ✅ Mock external I/O operations
- ✅ Deterministic test execution
- ✅ No test interdependencies

## Coverage Targets

- **Unit Test Coverage**: >80% per module
- **Integration Test Coverage**: >60% end-to-end scenarios
- **Edge Case Coverage**: 100% for critical paths

## Test Maintenance

- Update tests when producer interfaces change
- Add tests for new features/bugs
- Keep mocks synchronized with actual APIs
- Review test coverage quarterly
