# Phase 3: Chunk Routing - Implementation Guide

## Quick Start

Phase 3 routes questions from Phase 2 to their corresponding chunks in the PA×DIM matrix.

```python
from farfan_pipeline.core.phases.phase3_chunk_routing import (
    Phase3ChunkRoutingContract,
    Phase3Input,
)

# Initialize Phase 3
phase3 = Phase3ChunkRoutingContract()

# Prepare input
phase3_input = Phase3Input(
    preprocessed_document=preprocessed_doc,  # From adapter
    questions=phase2_questions               # From Phase 2
)

# Execute routing
phase3_result, metadata = await phase3.run(phase3_input)

# Check results
print(f"Successfully routed: {phase3_result.successful_routes}/{phase3_result.total_questions}")
print(f"Policy area distribution: {phase3_result.policy_area_distribution}")
```

## Overview

Phase 3 implements deterministic chunk routing with:

- **Strict Equality Enforcement:** policy_area_id and dimension_id must match exactly
- **Complete Field Population:** All 7 ChunkRoutingResult fields populated
- **Descriptive Errors:** ValueError with question ID and failure reason
- **Observability:** Match counts and distribution tracking
- **No Task Creep:** Focus solely on routing correctness

## Architecture

### Input Contract

```python
@dataclass
class Phase3Input:
    preprocessed_document: PreprocessedDocument  # 60 chunks
    questions: list[dict[str, Any]]              # Questions from Phase 2
```

**Requirements:**
- Document must have exactly 60 chunks
- Each chunk must have policy_area_id and dimension_id
- Questions must have policy_area_id and dimension_id fields

### Output Contract

```python
@dataclass
class Phase3Result:
    routing_results: list[ChunkRoutingResult]    # Successful routes
    total_questions: int                         # Total processed
    successful_routes: int                       # Successfully routed
    failed_routes: int                           # Failed routes
    policy_area_distribution: dict[str, int]     # PA counts
    dimension_distribution: dict[str, int]       # DIM counts
    routing_errors: list[str]                    # Error messages
```

**Invariants:**
1. `successful_routes + failed_routes == total_questions`
2. `len(routing_results) == successful_routes`
3. `sum(policy_area_distribution.values()) == successful_routes`

### ChunkRoutingResult

The canonical 7-field structure:

```python
@dataclass
class ChunkRoutingResult:
    target_chunk: ChunkData                      # Complete chunk object
    chunk_id: str                                # "PA01-DIM01"
    policy_area_id: str                          # "PA01"
    dimension_id: str                            # "DIM01"
    text_content: str                            # Chunk text
    expected_elements: list[dict[str, Any]]      # Never None
    document_position: tuple[int, int] | None    # (start, end)
```

## Routing Algorithm

### Step 1: Extract Identifiers

```python
policy_area_id = question.get("policy_area_id")
dimension_id = question.get("dimension_id")
```

### Step 2: Normalize Dimension Format

```python
# Convert D1 → DIM01
if dimension_id.startswith("D") and not dimension_id.startswith("DIM"):
    dim_num = int(dimension_id[1:])
    dimension_id = f"DIM{dim_num:02d}"
```

### Step 3: Construct Lookup Key

```python
lookup_key = (policy_area_id, dimension_id)
```

### Step 4: Perform Matrix Lookup

```python
if lookup_key not in chunk_matrix:
    raise ValueError(f"No matching chunk for {policy_area_id}-{dimension_id}")
target_chunk = chunk_matrix[lookup_key]
```

### Step 5: Verify Strict Equality

```python
assert target_chunk.policy_area_id == policy_area_id
assert target_chunk.dimension_id == dimension_id
```

### Step 6: Populate Result

```python
return ChunkRoutingResult(
    target_chunk=target_chunk,
    chunk_id=target_chunk.chunk_id,
    policy_area_id=policy_area_id,
    dimension_id=dimension_id,
    text_content=target_chunk.text,
    expected_elements=target_chunk.expected_elements or [],
    document_position=target_chunk.document_position
)
```

## Error Handling

Phase 3 raises descriptive ValueError exceptions for all failure modes:

### Missing Fields

```python
# Missing policy_area_id
raise ValueError(
    f"Question {question_id} missing required field 'policy_area_id'"
)

# Missing dimension_id
raise ValueError(
    f"Question {question_id} missing required field 'dimension_id'"
)
```

### Chunk Not Found

```python
raise ValueError(
    f"Question {question_id} routing failed: "
    f"No matching chunk found for policy_area_id={pa}, dimension_id={dim}. "
    f"Required chunk {pa}-{dim} is missing from the chunk matrix."
)
```

### Verification Failures

```python
# Policy area mismatch
raise ValueError(
    f"Question {question_id} routing verification failed: "
    f"Chunk policy_area_id mismatch. "
    f"Question expects {pa1}, chunk has {pa2}"
)

# Dimension mismatch
raise ValueError(
    f"Question {question_id} routing verification failed: "
    f"Chunk dimension_id mismatch. "
    f"Question expects {dim1}, chunk has {dim2}"
)
```

## Observability

Phase 3 logs routing outcomes without introducing task creep:

### Start Logging

```
======================================================================
PHASE 3: Chunk Routing - Starting Execution
======================================================================
Stage 1: Extracting inputs
Loaded 300 questions
Loaded 60 chunks
Stage 2: Validating chunk matrix
Built chunk matrix with 60 entries
Stage 3: Performing chunk routing
```

### End Logging

```
======================================================================
PHASE 3: Chunk Routing - Execution Complete
Total Questions: 300
Successful Routes: 298
Failed Routes: 2
Policy Area Distribution:
  PA01: 30 questions
  PA02: 30 questions
  ...
Dimension Distribution:
  DIM01: 50 questions
  DIM02: 50 questions
  ...
======================================================================
```

### What Is NOT Logged

Phase 3 avoids task creep by NOT logging:
- Chunk quality scores
- Text content analysis
- NLP metrics
- Chunk modifications
- Signal computations

## Integration

### With Phase Orchestrator

Phase 3 integrates seamlessly after Phase 2:

```python
# In PhaseOrchestrator.run_pipeline()

# Phase 2 completes
phase2_result = ...

# Phase 3 execution
phase3_input = Phase3Input(
    preprocessed_document=preprocessed,
    questions=phase2_result.questions
)

phase3_result, phase3_metadata = await self.phase3.run(phase3_input)

# Record in manifest
self.manifest_builder.record_phase(
    phase_name="phase3_chunk_routing",
    metadata=phase3_metadata,
    input_validation=self.phase3.validate_input(phase3_input),
    output_validation=self.phase3.validate_output(phase3_result),
    invariants_checked=[inv.name for inv in self.phase3.invariants],
    artifacts=[]
)
```

### With Downstream Phases

Phase 4 can access routing results:

```python
# Phase 4 receives Phase 3 output
for routing_result in phase3_result.routing_results:
    chunk = routing_result.target_chunk
    question_id = ...  # From original question
    
    # Apply pattern filtering to chunk
    filtered_result = apply_patterns(chunk, question_id)
```

## Testing

### Unit Tests

Run Phase 3 unit tests:

```bash
pytest tests/phases/test_phase3_chunk_routing.py -v
```

### Implementation Tests

Run implementation verification tests:

```bash
pytest tests/phases/test_phase3_implementation.py -v
```

### Coverage

Phase 3 tests cover:
- Lookup key construction
- Chunk matrix lookup success paths
- KeyError handling and ValueError propagation
- Multi-stage verification (PA, DIM, chunk_id)
- Chunk payload extraction
- Synchronization failure detection
- Contract validation
- Invariant checking

## Performance

### Time Complexity

- **Chunk Matrix Construction:** O(60) = O(1)
- **Per-Question Routing:** O(1) dictionary lookup
- **Total:** O(Q) where Q = number of questions

### Space Complexity

- **Chunk Matrix:** O(60) = O(1)
- **Routing Results:** O(Q)
- **Total:** O(Q)

### Benchmarks

Expected performance for 300 questions:
- Matrix construction: < 10ms
- Routing 300 questions: < 50ms
- Total Phase 3 execution: < 100ms

## Common Issues

### Issue 1: Dimension Format Mismatch

**Problem:** Questions use "D1" but chunks use "DIM01"

**Solution:** Phase 3 automatically normalizes D1 → DIM01

### Issue 2: None expected_elements

**Problem:** Chunk has None expected_elements, validation fails

**Solution:** Always use fallback:
```python
expected_elements=target_chunk.expected_elements or []
```

### Issue 3: Missing Chunks

**Problem:** Chunk matrix has < 60 chunks

**Solution:** Fix upstream (Phase 1 ingestion or adapter)
```
ValueError: Expected 60 chunks in matrix, found 59
```

### Issue 4: Silently Dropped Questions

**Problem:** Question not routed but not in errors

**Solution:** Phase 3 guarantees completeness invariant:
```python
successful_routes + failed_routes == total_questions
```

## Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Phase 3 will log detailed routing steps
```

### Inspect Routing Errors

```python
result = await phase3.run(phase3_input)

if result.failed_routes > 0:
    print("Routing Errors:")
    for error in result.routing_errors:
        print(f"  - {error}")
```

### Verify Distributions

```python
# Check if questions are evenly distributed
pa_dist = result.policy_area_distribution
dim_dist = result.dimension_distribution

print(f"PA distribution: {pa_dist}")
print(f"DIM distribution: {dim_dist}")

# Expected: roughly 30 questions per PA, 50 per DIM (for 300 questions)
```

## Best Practices

### 1. Always Check Invariants

```python
result = await phase3.run(input_data)
assert result.successful_routes + result.failed_routes == result.total_questions
```

### 2. Handle Routing Failures Gracefully

```python
if result.failed_routes > 0:
    logger.warning(f"{result.failed_routes} questions failed routing")
    # Decide whether to continue or abort pipeline
```

### 3. Log Distributions for Monitoring

```python
logger.info(f"PA distribution: {result.policy_area_distribution}")
logger.info(f"DIM distribution: {result.dimension_distribution}")
```

### 4. Use Contract Validation

```python
# Validate input before execution
input_validation = phase3.validate_input(phase3_input)
if not input_validation.passed:
    raise ValueError(f"Invalid input: {input_validation.errors}")
```

### 5. Record in Manifest

```python
manifest_builder.record_phase(
    phase_name="phase3_chunk_routing",
    metadata=metadata,
    input_validation=input_validation,
    output_validation=output_validation,
    invariants_checked=invariant_names,
    artifacts=[]
)
```

## FAQ

### Q: What if a question has an invalid dimension format?

**A:** Phase 3 raises a descriptive ValueError:
```
Question Q123 has invalid dimension_id format: DX
```

### Q: Can Phase 3 modify chunks?

**A:** No. Phase 3 is read-only. Chunks are never modified.

### Q: What if the chunk matrix is incomplete?

**A:** Phase 3 validates the matrix and raises ValueError if != 60 chunks.

### Q: Does Phase 3 analyze chunk content?

**A:** No. Phase 3 only performs routing. Content analysis is for downstream phases.

### Q: How are routing errors handled?

**A:** Each routing failure is caught, logged, and recorded in `routing_errors`. The phase continues processing remaining questions.

### Q: What's the difference between failed_routes and routing_errors?

**A:** `failed_routes` is a count, `routing_errors` is a list of error messages.

## See Also

- [Phase 3 Specification](./phase3_specification.md) - Detailed spec
- [Phase 2 Documentation](./phase2_README.md) - Upstream phase
- [Phase 4 Documentation](./phase4_README.md) - Downstream phase
- [Phase Protocol](../src/farfan_pipeline/core/phases/phase_protocol.py) - Contract system

## Support

For issues with Phase 3 implementation:
1. Check test suite: `pytest tests/phases/test_phase3_*.py -v`
2. Review logs for routing errors
3. Verify chunk matrix completeness
4. Ensure question structure compliance
