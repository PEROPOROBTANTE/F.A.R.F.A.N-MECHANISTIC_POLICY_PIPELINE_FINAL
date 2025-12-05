# Phase 3: Chunk Routing Specification

## Overview

Phase 3 implements deterministic routing of questions to their corresponding policy area × dimension chunks. This phase ensures that each question is matched to exactly one chunk in the 60-chunk PA×DIM matrix through strict equality enforcement.

## Phase Position in Pipeline

```
Phase 0: Input Validation
    ↓
Phase 1: SPC Ingestion (60 chunks)
    ↓
Adapter: Phase 1 → Phase 2
    ↓
Phase 2: Microquestions (300 questions)
    ↓
**Phase 3: Chunk Routing** ← YOU ARE HERE
    ↓
Phase 4: Pattern Filtering
    ↓
Phase 5: Signal Resolution
    ↓
...
```

## Input Contract

**Type:** `Phase3Input`

```python
@dataclass
class Phase3Input:
    preprocessed_document: PreprocessedDocument  # Contains 60 chunks
    questions: list[dict[str, Any]]              # Questions from Phase 2
```

### Input Requirements

1. **PreprocessedDocument:**
   - Must contain exactly 60 chunks
   - Each chunk must have `policy_area_id` and `dimension_id`
   - Chunks must cover all PA01-PA10 × DIM01-DIM06 combinations
   - Processing mode must be `"chunked"`

2. **Questions:**
   - Non-empty list of question dictionaries
   - Each question must have `policy_area_id` field
   - Each question must have `dimension_id` field
   - Dimension format can be "D1"-"D6" or "DIM01"-"DIM06"

## Output Contract

**Type:** `Phase3Result`

```python
@dataclass
class Phase3Result:
    routing_results: list[ChunkRoutingResult]
    total_questions: int
    successful_routes: int
    failed_routes: int
    policy_area_distribution: dict[str, int]
    dimension_distribution: dict[str, int]
    routing_errors: list[str]
```

### Output Guarantees

1. **Completeness:** `successful_routes + failed_routes == total_questions`
2. **Consistency:** `len(routing_results) == successful_routes`
3. **Distribution:** Policy area counts sum to `successful_routes`

## Hierarchical Phase Structure

Phase 3 follows the established five-stage structure:

### Stage 1: Sequential Dependency Root (Input Extraction)

```
Input Extraction
├── Extract PreprocessedDocument
│   ├── Access chunks list
│   └── Validate chunk count
└── Extract Questions List
    ├── Validate list structure
    └── Count total questions
```

**Purpose:** Isolate all external dependencies at the phase boundary.

**Validation:**
- Verify PreprocessedDocument type
- Verify questions is a list
- Log input sizes

### Stage 2: Validation

```
Validation Stage
├── Chunk Matrix Validation
│   ├── Verify 60 chunks present
│   ├── Check policy_area_id presence
│   ├── Check dimension_id presence
│   └── Detect duplicate PA×DIM keys
└── Question Structure Validation
    ├── Verify policy_area_id field
    ├── Verify dimension_id field
    └── Validate identifier formats
```

**Purpose:** Ensure all inputs meet structural invariants before processing.

**Error Handling:**
- Null policy_area_id → ValueError
- Null dimension_id → ValueError
- Duplicate chunk keys → ValueError
- Invalid chunk count → ValueError

### Stage 3: Transformation

```
Transformation Stage (Routing)
├── Build Chunk Matrix
│   ├── Create (PA, DIM) → ChunkData mapping
│   └── Index by composite key
└── For Each Question:
    ├── Extract Identifiers
    │   ├── Get policy_area_id
    │   └── Get dimension_id
    ├── Normalize Dimension Format
    │   └── D1 → DIM01 conversion
    ├── Construct Lookup Key
    │   └── (policy_area_id, dimension_id)
    ├── Perform Matrix Lookup
    │   └── chunk_matrix[key]
    ├── Verify Strict Equality
    │   ├── chunk.policy_area_id == question.policy_area_id
    │   └── chunk.dimension_id == question.dimension_id
    └── Populate ChunkRoutingResult
        ├── target_chunk: ChunkData
        ├── chunk_id: str
        ├── policy_area_id: str
        ├── dimension_id: str
        ├── text_content: str
        ├── expected_elements: list[dict]
        └── document_position: tuple[int, int] | None
```

**Purpose:** Route each question to its corresponding chunk with full field population.

**Transformation Rules:**
1. Dimension format normalization (D1-D6 → DIM01-DIM06)
2. Composite key construction from identifiers
3. Dictionary lookup for O(1) routing
4. Strict equality verification post-lookup

### Stage 4: Error Conditions (Leaf Nodes)

```
Error Conditions
├── Missing policy_area_id
│   └── ValueError: "Question {id} missing required field 'policy_area_id'"
├── Missing dimension_id
│   └── ValueError: "Question {id} missing required field 'dimension_id'"
├── Invalid dimension format
│   └── ValueError: "Question {id} has invalid dimension_id format: {format}"
├── Chunk Not Found
│   └── ValueError: "Question {id} routing failed: No matching chunk found 
│                     for policy_area_id={pa}, dimension_id={dim}. 
│                     Required chunk {pa}-{dim} is missing from chunk matrix."
├── Policy Area Mismatch
│   └── ValueError: "Question {id} routing verification failed: 
│                     Chunk policy_area_id mismatch. 
│                     Question expects {pa1}, chunk has {pa2}"
└── Dimension Mismatch
    └── ValueError: "Question {id} routing verification failed: 
                      Chunk dimension_id mismatch. 
                      Question expects {dim1}, chunk has {dim2}"
```

**Purpose:** Provide descriptive, actionable error messages for all failure modes.

**Error Message Requirements:**
- Identify the specific question (by ID)
- State the exact reason for failure
- Include relevant identifiers (PA, DIM)
- Distinguish between missing chunks and mismatches

### Stage 5: Observability

```
Observability Logging
├── Routing Outcomes
│   ├── Total questions processed
│   ├── Successful routes count
│   └── Failed routes count
├── Policy Area Distribution
│   └── {PA01: count, PA02: count, ...}
├── Dimension Distribution
│   └── {DIM01: count, DIM02: count, ...}
└── Error Recording
    └── List of all routing errors
```

**Purpose:** Record routing outcomes without introducing task creep.

**Logged Metrics:**
- Match counts (successful vs. failed)
- PA distribution (questions per policy area)
- DIM distribution (questions per dimension)
- Error messages (for failed routes)

**Anti-Pattern (Avoided):**
- Computing chunk quality scores
- Analyzing text content
- Performing NLP operations
- Modifying chunk data

## ChunkRoutingResult Structure

The canonical seven-field structure for routing results:

```python
@dataclass
class ChunkRoutingResult:
    target_chunk: ChunkData              # Complete chunk object
    chunk_id: str                        # PA01-DIM01 format
    policy_area_id: str                  # PA01-PA10
    dimension_id: str                    # DIM01-DIM06
    text_content: str                    # Chunk text (non-empty)
    expected_elements: list[dict]        # Never None (use [])
    document_position: tuple[int, int] | None  # (start, end) or None
```

### Field Validation

All fields validated in `__post_init__`:

1. **target_chunk:** Must not be None
2. **chunk_id:** Must not be empty string
3. **policy_area_id:** Must not be empty string
4. **dimension_id:** Must not be empty string
5. **text_content:** Must not be empty string
6. **expected_elements:** Must not be None (use empty list)
7. **document_position:** Can be None (nullable)

## Routing Algorithm

### Step-by-Step Process

1. **Extract Question Identifiers:**
   ```python
   policy_area_id = question.get("policy_area_id")
   dimension_id = question.get("dimension_id")
   ```

2. **Normalize Dimension Format:**
   ```python
   if dimension_id.startswith("D") and not dimension_id.startswith("DIM"):
       dim_num = int(dimension_id[1:])
       dimension_id = f"DIM{dim_num:02d}"
   ```

3. **Construct Lookup Key:**
   ```python
   lookup_key = (policy_area_id, dimension_id)
   ```

4. **Perform Matrix Lookup:**
   ```python
   if lookup_key not in chunk_matrix:
       raise ValueError(f"No matching chunk for {policy_area_id}-{dimension_id}")
   target_chunk = chunk_matrix[lookup_key]
   ```

5. **Verify Strict Equality:**
   ```python
   assert target_chunk.policy_area_id == policy_area_id
   assert target_chunk.dimension_id == dimension_id
   ```

6. **Populate Result:**
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

## Phase Invariants

Phase 3 enforces three critical invariants:

### Invariant 1: Routing Completeness

```python
successful_routes + failed_routes == total_questions
```

**Rationale:** Every question must be either successfully routed or have an error recorded. No questions can be silently dropped.

### Invariant 2: Result Count Consistency

```python
len(routing_results) == successful_routes
```

**Rationale:** The number of ChunkRoutingResult objects must exactly match the count of successful routes.

### Invariant 3: Distribution Sum Consistency

```python
sum(policy_area_distribution.values()) == successful_routes
```

**Rationale:** The sum of questions across all policy areas must equal the total successful routes.

## Error Handling Philosophy

Phase 3 follows these error handling principles:

### 1. Fail Fast on Structural Violations

```python
# Immediate ValueError for missing required fields
if policy_area_id is None:
    raise ValueError("Missing policy_area_id")
```

### 2. Descriptive Error Messages

```python
# Include question ID, field names, and expected values
raise ValueError(
    f"Question {question_id} routing failed: "
    f"No matching chunk found for policy_area_id={pa}, dimension_id={dim}. "
    f"Required chunk {pa}-{dim} is missing from the chunk matrix."
)
```

### 3. Distinguish Error Types

- **Missing Fields:** Question structure invalid
- **Chunk Not Found:** Matrix incomplete or identifiers wrong
- **Mismatch:** Post-lookup verification failed

### 4. Record All Failures

```python
try:
    result = route_question(question)
    routing_results.append(result)
except ValueError as e:
    routing_errors.append(str(e))
```

## Observability and Logging

Phase 3 provides comprehensive logging without task creep:

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
  PA03: 30 questions
  PA04: 30 questions
  PA05: 30 questions
  PA06: 30 questions
  PA07: 30 questions
  PA08: 30 questions
  PA09: 28 questions
  PA10: 30 questions
Dimension Distribution:
  DIM01: 50 questions
  DIM02: 50 questions
  DIM03: 49 questions
  DIM04: 49 questions
  DIM05: 50 questions
  DIM06: 50 questions
======================================================================
```

### Error Logging

```python
logger.error(f"Routing failed: {error_msg}")
```

Each failure is logged immediately with the full error message.

## Integration with Phase Orchestrator

Phase 3 integrates into the orchestrator like other phases:

```python
# In PhaseOrchestrator.run_pipeline()

# ... Phase 2 completion ...

# ================================================================
# PHASE 3: Chunk Routing
# ================================================================
logger.info("=" * 70)
logger.info("PHASE 3: Chunk Routing")
logger.info("=" * 70)

phase3_input = Phase3Input(
    preprocessed_document=preprocessed,
    questions=phase2_result.questions
)

phase3_result, phase3_metadata = await self.phase3.run(phase3_input)

# Record Phase 3 in manifest
self.manifest_builder.record_phase(
    phase_name="phase3_chunk_routing",
    metadata=phase3_metadata,
    input_validation=self.phase3.validate_input(phase3_input),
    output_validation=self.phase3.validate_output(phase3_result),
    invariants_checked=[inv.name for inv in self.phase3.invariants],
    artifacts=[]
)

# ... Continue to Phase 4 ...
```

## Testing Strategy

Phase 3 testing covers all hierarchical stages:

### Unit Tests (per test file structure)

1. **Lookup Key Construction:**
   - Dimension format conversion (D1 → DIM01)
   - Policy area format validation (PA01-PA10)
   - Tuple construction

2. **Chunk Matrix Lookup:**
   - Valid key success path
   - All policy areas accessible
   - All dimensions accessible
   - Returns correct ChunkData type

3. **KeyError Handling:**
   - Invalid policy area
   - Invalid dimension
   - Nonexistent PA-DIM combination
   - ValueError propagation from KeyError

4. **Multi-Stage Verification:**
   - policy_area_id equality check
   - dimension_id equality check
   - chunk_id consistency with PA-DIM

5. **Chunk Payload Extraction:**
   - text_content non-empty
   - expected_elements extraction (sentences, tables)
   - document_position tuple format
   - Provenance metadata handling

6. **Synchronization Failures:**
   - Missing chunks error format
   - Duplicate chunk detection
   - Invalid format errors

### Integration Tests

1. **Full 300-Question Routing:**
   - All questions route successfully
   - Distribution matches expectations
   - No errors recorded

2. **Partial Chunk Matrix:**
   - Some questions fail routing
   - Errors correctly identify missing chunks
   - Successful routes still populate correctly

3. **Contract Validation:**
   - Input validation catches structural errors
   - Output validation enforces invariants
   - Manifest records phase execution

## Performance Characteristics

- **Time Complexity:** O(Q) where Q is number of questions
  - Chunk matrix construction: O(C) where C = 60 (constant)
  - Per-question routing: O(1) dictionary lookup
  - Total: O(60 + Q) = O(Q)

- **Space Complexity:** O(Q + C)
  - Chunk matrix: O(60) = O(1) constant
  - Routing results: O(Q)
  - Total: O(Q)

- **Determinism:** 
  - Same input always produces same routing
  - No randomness or non-deterministic operations
  - Dictionary iteration order preserved (Python 3.7+)

## Common Pitfalls and Solutions

### Pitfall 1: Dimension Format Inconsistency

**Problem:** Questions use "D1" but chunks use "DIM01"

**Solution:** Normalize in routing logic:
```python
if dimension_id.startswith("D") and not dimension_id.startswith("DIM"):
    dim_num = int(dimension_id[1:])
    dimension_id = f"DIM{dim_num:02d}"
```

### Pitfall 2: None vs. Empty List for expected_elements

**Problem:** expected_elements can be None, but ChunkRoutingResult validation fails

**Solution:** Always use empty list as fallback:
```python
expected_elements=target_chunk.expected_elements or []
```

### Pitfall 3: Silently Dropped Questions

**Problem:** Exception caught but question not counted as failure

**Solution:** Always record in routing_errors:
```python
except ValueError as e:
    routing_errors.append(str(e))
```

### Pitfall 4: Task Creep (Analyzing Chunk Quality)

**Problem:** Temptation to add chunk scoring or quality metrics

**Solution:** Phase 3 is ONLY routing. Scoring belongs in Phase 4+.

## Conclusion

Phase 3 implements a focused, deterministic chunk routing mechanism that:

1. ✅ Enforces strict policy_area_id and dimension_id equality
2. ✅ Populates all seven canonical ChunkRoutingResult fields
3. ✅ Raises descriptive ValueError exceptions on failures
4. ✅ Follows established hierarchical phase structure
5. ✅ Provides observability without task creep
6. ✅ Maintains O(Q) performance with O(1) per-question routing

The implementation serves as a clean boundary between Phase 2 (question generation) and Phase 4 (pattern filtering), ensuring that all questions are deterministically mapped to their corresponding chunks before further analysis.
