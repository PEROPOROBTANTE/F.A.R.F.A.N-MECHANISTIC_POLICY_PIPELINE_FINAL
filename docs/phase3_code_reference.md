# Phase 3 Code Reference

Quick reference guide to Phase 3 implementation code locations.

## Core Implementation

### Main Module

**File:** `src/farfan_pipeline/core/phases/phase3_chunk_routing.py`

#### Classes

**ChunkRoutingResult** (Lines 46-85)
```python
@dataclass
class ChunkRoutingResult:
    """Result of routing a single question to its target chunk."""
    target_chunk: ChunkData
    chunk_id: str
    policy_area_id: str
    dimension_id: str
    text_content: str
    expected_elements: list[dict[str, Any]]
    document_position: tuple[int, int] | None
```

**Phase3Input** (Lines 88-96)
```python
@dataclass
class Phase3Input:
    """Input contract for Phase 3: chunk routing."""
    preprocessed_document: PreprocessedDocument
    questions: list[dict[str, Any]]
```

**Phase3Result** (Lines 99-110)
```python
@dataclass
class Phase3Result:
    """Output contract for Phase 3: chunk routing results."""
    routing_results: list[ChunkRoutingResult]
    total_questions: int
    successful_routes: int
    failed_routes: int
    policy_area_distribution: dict[str, int]
    dimension_distribution: dict[str, int]
    routing_errors: list[str]
```

**Phase3ChunkRoutingContract** (Lines 113-366)
```python
class Phase3ChunkRoutingContract(PhaseContract[Phase3Input, Phase3Result]):
    """Phase 3 Contract: Chunk Routing with Strict PA×DIM Enforcement."""
```

#### Key Methods

**validate_input()** (Lines 133-176)
- Validates Phase3Input structure
- Checks preprocessed document and questions

**validate_output()** (Lines 178-225)
- Validates Phase3Result structure
- Verifies routing results and counts

**execute()** (Lines 227-244)
- Main routing logic execution
- Five-stage execution model:
  1. Input extraction (Lines 188-193)
  2. Validation (Lines 195-198)
  3. Transformation/Routing (Lines 200-224)
  4. Error conditions (Lines 218-224)
  5. Observability (Lines 226-244)

**_build_chunk_matrix()** (Lines 246-278)
- Constructs (PA, DIM) → ChunkData mapping
- Validates matrix completeness

**_route_question_to_chunk()** (Lines 280-366)
- Core routing logic for single question
- Identifier extraction (Lines 271-276)
- Format normalization (Lines 278-288)
- Lookup key construction (Lines 290-292)
- Matrix lookup (Lines 294-303)
- Strict equality verification (Lines 305-322)
- Result population (Lines 324-343)

## Integration Points

### Phase Orchestrator

**File:** `src/farfan_pipeline/core/phases/phase_orchestrator.py`

**Initialization** (Lines 105-107)
```python
# Initialize Phase 3 contract
self.phase3 = Phase3ChunkRoutingContract()
```

**Execution** (Lines 384-418)
```python
# Phase 3: Chunk Routing
phase3_input = Phase3Input(
    preprocessed_document=preprocessed,
    questions=phase2_questions or []
)
phase3_result, phase3_metadata = await self.phase3.run(phase3_input)
```

**Manifest Recording** (Lines 409-416)
```python
self.manifest_builder.record_phase(
    phase_name="phase3_chunk_routing",
    metadata=phase3_metadata,
    input_validation=self.phase3.validate_input(phase3_input),
    output_validation=self.phase3.validate_output(phase3_result),
    invariants_checked=[inv.name for inv in self.phase3.invariants],
    artifacts=[]
)
```

### Module Exports

**File:** `src/farfan_pipeline/core/phases/__init__.py`

**Imports** (Lines 23-28)
```python
from farfan_pipeline.core.phases.phase3_chunk_routing import (
    ChunkRoutingResult,
    Phase3ChunkRoutingContract,
    Phase3Input,
    Phase3Result,
)
```

**Exports** (Lines 50-54)
```python
__all__ = [
    # ...
    "ChunkRoutingResult",
    "Phase3ChunkRoutingContract",
    "Phase3Input",
    "Phase3Result",
    # ...
]
```

## Testing

### Main Test Suite

**File:** `tests/phases/test_phase3_chunk_routing.py`

**Test Classes:**
- `TestPhase3LookupKeyConstruction` (Lines 54-87)
- `TestPhase3ChunkMatrixLookup` (Lines 90-195)
- `TestPhase3KeyErrorHandling` (Lines 198-327)
- `TestPhase3MultiStageVerification` (Lines 330-453)
- `TestPhase3ChunkPayloadExtraction` (Lines 456-584)
- `TestPhase3SynchronizationFailures` (Lines 587-741)

### Implementation Tests

**File:** `tests/phases/test_phase3_implementation.py`

**Test Classes:**
- `TestChunkRoutingResultConstruction` (Lines 23-130)
- `TestStrictEqualityEnforcement` (Lines 133-239)
- `TestRoutingFailures` (Lines 242-361)
- `TestPhaseSpecificationCompliance` (Lines 364-403)
- `TestObservabilityLogging` (Lines 406-493)

## Routing Algorithm Flow

### Step-by-Step Execution

```
1. Extract Question Identifiers
   ├── policy_area_id = question.get("policy_area_id")
   └── dimension_id = question.get("dimension_id")
   Location: phase3_chunk_routing.py:271-276

2. Normalize Dimension Format
   ├── if dimension_id.startswith("D") and not .startswith("DIM"):
   │   └── dimension_id = f"DIM{dim_num:02d}"
   Location: phase3_chunk_routing.py:278-288

3. Construct Lookup Key
   └── lookup_key = (policy_area_id, dimension_id)
   Location: phase3_chunk_routing.py:290-292

4. Perform Matrix Lookup
   ├── if lookup_key not in chunk_matrix:
   │   └── raise ValueError("No matching chunk")
   └── target_chunk = chunk_matrix[lookup_key]
   Location: phase3_chunk_routing.py:294-303

5. Verify Strict Equality
   ├── if target_chunk.policy_area_id != policy_area_id:
   │   └── raise ValueError("PA mismatch")
   └── if target_chunk.dimension_id != dimension_id:
       └── raise ValueError("DIM mismatch")
   Location: phase3_chunk_routing.py:305-322

6. Populate Result
   └── return ChunkRoutingResult(...)
   Location: phase3_chunk_routing.py:324-343
```

## Error Handling Locations

### Missing Fields

**Missing policy_area_id** (Lines 278-281)
```python
if policy_area_id is None:
    raise ValueError(
        f"Question {question_id} missing required field 'policy_area_id'"
    )
```

**Missing dimension_id** (Lines 283-286)
```python
if dimension_id is None:
    raise ValueError(
        f"Question {question_id} missing required field 'dimension_id'"
    )
```

### Lookup Failures

**Chunk Not Found** (Lines 294-303)
```python
if lookup_key not in chunk_matrix:
    raise ValueError(
        f"Question {question_id} routing failed: "
        f"No matching chunk found for policy_area_id={policy_area_id}, "
        f"dimension_id={dimension_id}. "
        f"Required chunk {policy_area_id}-{dimension_id} is missing from the chunk matrix."
    )
```

### Verification Failures

**Policy Area Mismatch** (Lines 305-312)
```python
if target_chunk.policy_area_id != policy_area_id:
    raise ValueError(
        f"Question {question_id} routing verification failed: "
        f"Chunk policy_area_id mismatch. "
        f"Question expects {policy_area_id}, chunk has {target_chunk.policy_area_id}"
    )
```

**Dimension Mismatch** (Lines 314-321)
```python
if target_chunk.dimension_id != dimension_id:
    raise ValueError(
        f"Question {question_id} routing verification failed: "
        f"Chunk dimension_id mismatch. "
        f"Question expects {dimension_id}, chunk has {target_chunk.dimension_id}"
    )
```

## Logging Locations

### Start Logging

**Phase Start** (Lines 186-193)
```python
logger.info("=" * 70)
logger.info("PHASE 3: Chunk Routing - Starting Execution")
logger.info("=" * 70)
logger.info("Stage 1: Extracting inputs")
logger.info(f"Loaded {len(questions)} questions")
logger.info(f"Loaded {len(preprocessed_doc.chunks)} chunks")
```

### End Logging

**Phase Completion** (Lines 229-244)
```python
logger.info("=" * 70)
logger.info("PHASE 3: Chunk Routing - Execution Complete")
logger.info(f"Total Questions: {total_questions}")
logger.info(f"Successful Routes: {successful_routes}")
logger.info(f"Failed Routes: {failed_routes}")
logger.info("Policy Area Distribution:")
for pa_id in sorted(policy_area_dist.keys()):
    logger.info(f"  {pa_id}: {policy_area_dist[pa_id]} questions")
logger.info("Dimension Distribution:")
for dim_id in sorted(dimension_dist.keys()):
    logger.info(f"  {dim_id}: {dimension_dist[dim_id]} questions")
logger.info("=" * 70)
```

### Error Logging

**Routing Failures** (Lines 221-224)
```python
except ValueError as e:
    error_msg = str(e)
    routing_errors.append(error_msg)
    logger.error(f"Routing failed: {error_msg}")
```

## Invariants

### Defined Invariants

**Location:** phase3_chunk_routing.py:127-148

**1. routing_completeness** (Lines 127-132)
```python
check=lambda result: result.successful_routes + result.failed_routes == result.total_questions
```

**2. routing_results_match_success** (Lines 134-139)
```python
check=lambda result: len(result.routing_results) == result.successful_routes
```

**3. policy_area_distribution_sum** (Lines 141-146)
```python
check=lambda result: sum(result.policy_area_distribution.values()) == result.successful_routes
```

## Usage Examples

### Basic Usage

```python
from farfan_pipeline.core.phases import (
    Phase3ChunkRoutingContract,
    Phase3Input,
)

# Initialize
phase3 = Phase3ChunkRoutingContract()

# Prepare input
input_data = Phase3Input(
    preprocessed_document=doc,
    questions=questions
)

# Execute
result, metadata = await phase3.run(input_data)

# Check results
print(f"Routed: {result.successful_routes}/{result.total_questions}")
```

### With Validation

```python
# Validate input
input_validation = phase3.validate_input(input_data)
if not input_validation.passed:
    print(f"Input validation failed: {input_validation.errors}")
    return

# Execute
result, metadata = await phase3.run(input_data)

# Validate output
output_validation = phase3.validate_output(result)
if not output_validation.passed:
    print(f"Output validation failed: {output_validation.errors}")
    return
```

### Error Handling

```python
result, metadata = await phase3.run(input_data)

if result.failed_routes > 0:
    print(f"Warning: {result.failed_routes} questions failed routing")
    for error in result.routing_errors:
        print(f"  - {error}")
```

## Dependencies

### Internal Dependencies

- `farfan_pipeline.core.phases.phase_protocol.PhaseContract`
- `farfan_pipeline.core.types.ChunkData`
- `farfan_pipeline.core.types.PreprocessedDocument`

### External Dependencies

- `dataclasses` (standard library)
- `logging` (standard library)
- `typing` (standard library)

## Performance Notes

### Critical Paths

**Hot Path:** _route_question_to_chunk() - Lines 280-366
- Called once per question (O(Q) calls)
- Must be O(1) per call

**Optimization Points:**
- Dictionary lookup (Line 294): O(1) ✅
- String operations minimal
- No I/O operations
- No heavy computations

### Memory Usage

**Chunk Matrix:** O(60) = O(1) constant
**Routing Results:** O(Q) where Q = number of questions
**Distributions:** O(PA + DIM) = O(16) constant

## See Also

- [Phase 3 Specification](./phase3_specification.md) - Detailed requirements
- [Phase 3 README](./phase3_README.md) - User guide
- [Phase 3 Audit Report](./PHASE3_AUDIT_REPORT.md) - Verification results
- [Implementation Summary](../PHASE3_IMPLEMENTATION_SUMMARY.md) - Overview

---

**Last Updated:** 2025-01-22  
**Maintained By:** F.A.R.F.A.N Architecture Team
