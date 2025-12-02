# Phase 0-11 Test Suite

Comprehensive test suite for the canonical phase pipeline contracts and orchestration.

## Test Files

### Core Phase Tests

1. **test_phase0_input_validation.py** (405 lines)
   - Input contract validation (Phase0Input)
   - Output contract validation (CanonicalInput)
   - PDF existence and readability
   - SHA256 hash determinism
   - Questionnaire path resolution
   - Metadata extraction (page count, file size)
   - All 5 invariants
   - Error propagation for missing files
   - Phase metadata tracking

2. **test_phase1_spc_ingestion.py** (114 lines)
   - Input contract validation (CanonicalInput from Phase 0)
   - Output contract validation (CanonPolicyPackage)
   - 60 chunks generation (10 PA × 6 DIM)
   - PA×DIM tagging completeness
   - Quality metrics thresholds (provenance >= 0.8, structural >= 0.85)
   - BLAKE2b hash stability for chunks

3. **test_adapter.py** (74 lines)
   - Phase1→Phase2 adapter contract
   - PA×DIM metadata preservation
   - sentence_metadata.extra structure
   - chunk_id, policy_area_id, dimension_id preservation
   - processing_mode='chunked' enforcement

4. **test_phase2_microquestions.py** (51 lines)
   - Phase 2 result structure validation
   - Questions list validation
   - Required fields checking (base_slot, question_id, evidence, validation)

### Contract & Boundary Tests

5. **test_phase_boundaries.py** (69 lines)
   - Phase N output becomes Phase N+1 input
   - Contract type checking at boundaries
   - Sequential execution enforcement
   - PhaseContract.run() validation

6. **test_manifest_builder.py** (187 lines)
   - Manifest initialization
   - Phase recording (success/failure)
   - Invariant tracking
   - Artifact tracking
   - Manifest completeness (all 4 phases: 0, 1, adapter, 2)
   - Manifest serialization and saving

7. **test_failure_propagation.py** (170 lines)
   - Input validation failure → ABORT
   - Output validation failure → ABORT
   - Invariant failure → ABORT
   - Phase N failure prevents Phase N+1
   - Error capture in metadata
   - Pipeline abort behavior

### Quality & Integrity Tests

8. **test_provenance_completeness.py** (176 lines)
   - provenance_completeness >= 0.8 threshold
   - Chunk provenance field validation
   - ProvenanceMap structure (source_page, source_section)
   - All 60 chunks have provenance
   - Phase 1 provenance invariant
   - Quality metrics tracking

9. **test_hash_stability.py** (109 lines)
   - BLAKE2b deterministic hashing
   - SHA256 deterministic hashing
   - Same content → same hash across runs
   - Different content → different hash
   - Chunk bytes_hash stability
   - IntegrityIndex blake2b_root validation
   - Unicode content hash stability

### Integration Tests

10. **test_orchestrator_integration.py** (169 lines)
    - Orchestrator has all phase contracts
    - Manifest builder initialization
    - PipelineResult structure
    - Invalid PDF error handling
    - Manifest generation (always, even on failure)
    - Manifest saving to artifacts_dir
    - Single entry point enforcement (run_pipeline)
    - Phase sequence enforcement

## Test Coverage

### Phase Contracts
- ✅ Phase 0: Input Validation (CanonicalInput)
- ✅ Phase 1: SPC Ingestion (CanonPolicyPackage, 60 chunks)
- ✅ Adapter: Phase1→Phase2 (PreprocessedDocument)
- ✅ Phase 2: Microquestions (Phase2Result)

### Contract Boundaries
- ✅ Input/output contract validation at each boundary
- ✅ Type checking and invariant enforcement
- ✅ No phase can be skipped
- ✅ Sequential execution guaranteed

### Hash Stability
- ✅ BLAKE2b for chunk hashes (128-char hex)
- ✅ SHA256 for file hashes (64-char hex)
- ✅ Deterministic across runs
- ✅ IntegrityIndex root hash

### Manifest Completeness
- ✅ All phases recorded
- ✅ Input/output validation tracked
- ✅ Invariants checked and recorded
- ✅ Timing information (started_at, finished_at, duration_ms)
- ✅ Success/failure status
- ✅ Error messages captured

### Failure Propagation
- ✅ Input validation failure → ABORT
- ✅ Output validation failure → ABORT
- ✅ Invariant failure → ABORT
- ✅ Phase N failure prevents Phase N+1 from executing
- ✅ Errors captured in manifest

### Provenance Completeness
- ✅ provenance_completeness >= 0.8 enforced
- ✅ All chunks have provenance field
- ✅ ProvenanceMap structure validated
- ✅ Source page and section tracking
- ✅ Phase 1 invariant checks provenance threshold

## Running Tests

```bash
# Run all phase tests
pytest tests/phases/ -v

# Run specific test file
pytest tests/phases/test_phase0_input_validation.py -v

# Run with coverage
pytest tests/phases/ -v --cov=farfan_pipeline.core.phases --cov-report=term-missing

# Run only contract tests
pytest tests/phases/test_phase0_input_validation.py tests/phases/test_phase1_spc_ingestion.py tests/phases/test_adapter.py -v

# Run only integration tests
pytest tests/phases/test_orchestrator_integration.py tests/phases/test_failure_propagation.py -v
```

## Test Statistics

- **Total test files**: 10
- **Total lines of code**: 1,529
- **Phase contract tests**: 4 files
- **Boundary tests**: 3 files
- **Quality tests**: 2 files
- **Integration tests**: 1 file

## Key Invariants Tested

### Phase 0
1. validation_passed == True
2. pdf_page_count > 0
3. pdf_size_bytes > 0
4. SHA256 format (64-char hex)
5. No validation errors

### Phase 1
1. chunk_count == 60
2. All chunks have policy_area_id (PA01-PA10)
3. All chunks have dimension_id (DIM01-DIM06)
4. provenance_completeness >= 0.8
5. structural_consistency >= 0.85

### Adapter
1. All chunks preserved as sentences
2. processing_mode == 'chunked'
3. chunk_id in sentence_metadata.extra
4. policy_area_id in sentence_metadata.extra
5. dimension_id in sentence_metadata.extra

### Phase 2
1. questions list present
2. questions list non-empty
3. Required fields in each question

## Architecture Guarantees

The test suite enforces these constitutional guarantees:

1. **Single Entry Point**: Only `PhaseOrchestrator.run_pipeline()` executes phases
2. **Sequential Execution**: Phase 0 → Phase 1 → Adapter → Phase 2
3. **No Bypass**: Impossible to skip phases or validation
4. **Contract Enforcement**: All inputs/outputs validated
5. **Invariant Checking**: All invariants verified
6. **Full Traceability**: Complete manifest with all boundaries
7. **Deterministic**: Same input → same output (modulo controlled randomness)
8. **Failure Propagation**: Any phase failure aborts pipeline
9. **Provenance Tracking**: All chunks traceable to source
10. **Hash Stability**: Deterministic hashing for integrity verification
