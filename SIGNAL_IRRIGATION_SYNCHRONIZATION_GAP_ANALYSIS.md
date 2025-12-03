NP# Signal Irrigation Synchronization Gap Analysis

**Date:** 2025-12-03  
**Status:** 🔴 CRITICAL ARCHITECTURAL MISMATCH DETECTED

---

## Executive Summary

**FINDING:** Current signal irrigation implementation operates at **chunk-level granularity** but the contract architecture demands **executor-level synchronization** with **explicit (policy_area_id, dimension_id) routing**.

**RISK:** Signal enrichment floods all chunks indiscriminately without respecting the 1:1 executor-chunk-signal contract specified in the 300 v3 contracts.

---

## Contract Architecture (Ground Truth)

### Canonical Synchronization Model

Each of the **300 executor contracts** defines:

```json
{
  "identity": {
    "question_id": "Q001",
    "dimension_id": "DIM01",      // ← EXPLICIT DIMENSION
    "policy_area_id": "PA01",     // ← EXPLICIT POLICY AREA
    "cluster_id": "CL02"
  },
  "question_context": {
    "patterns": [/* 14 patterns with categories, confidence */],
    "expected_elements": [/* typed requirements */],
    "validations": {/* 5 validation rules */}
  }
}
```

**Contract Invariant:**
> Each executor expects **EXACTLY ONE** chunk with matching `(policy_area_id, dimension_id)` tuple.

---

## Current Implementation (What I Built)

### Signal Enrichment Logic (phases.py:745-850)

```python
for chunk in ch.chunks:
    policy_area_hint = chunk.get("policy_area_hint", "default")  # ❌ ONLY PA
    pack = registry_get(policy_area_hint)                        # ❌ PA-only lookup
    
    # Context filtering
    doc_context = create_document_context(
        section=chunk.get("section"),
        chapter=chunk.get("chapter"),
        policy_area=policy_area_hint,  # ❌ No dimension_id
    )
    
    applicable_patterns, stats = filter_patterns_by_context(patterns, doc_context)
```

**Problem Matrix:**

| Requirement | Current Implementation | Status |
|-------------|------------------------|--------|
| `(policy_area_id, dimension_id)` routing | Only `policy_area_hint` | ❌ FAIL |
| Executor ↔ Chunk JOIN table | No join table | ❌ FAIL |
| Signal type filtering per contract | All patterns from PA pack | ❌ FAIL |
| 1:1 executor-chunk assertion | No uniqueness check | ❌ FAIL |
| Manifest validation | No manifest | ❌ FAIL |
| Redundancy blocking | No duplicate detection | ❌ FAIL |

---

## Architectural Gap Analysis

### Gap 1: Missing Dimension Routing

**Expected:**
```
Chunk_PA01_DIM01 → Q001 (PA01/DIM01) → Only patterns from Q001.patterns[]
Chunk_PA01_DIM02 → Q002 (PA01/DIM02) → Only patterns from Q002.patterns[]
```

**Actual:**
```
All chunks with policy_area=PA01 → ALL patterns from PA01 signal pack
(No dimension discrimination)
```

**Impact:** Dimension D1 chunks receive D2, D3, D4, D5, D6 signals → **massive irrelevant signal pollution**.

---

### Gap 2: Missing JOIN Table

**Expected (from user spec):**

| ExecutorContractID | policy_area_id | dimension_id | expected_signal_types | chunk_id | irrigated_signals |
|--------------------|----------------|--------------|----------------------|----------|-------------------|
| Q001 | PA01 | DIM01 | [patterns from Q001] | chunk_PA01_DIM01 | [sig1, sig2] |
| Q002 | PA01 | DIM02 | [patterns from Q002] | chunk_PA01_DIM02 | [sig3, sig4] |

**Actual:** No table. Chunks are enriched in a loop without executor awareness.

---

### Gap 3: Signal Type Mismatch

**Contract Specification (Q001.v3.json):**
```json
{
  "question_context": {
    "patterns": [
      {"id": "PAT-Q001-000", "category": "TEMPORAL", ...},
      {"id": "PAT-Q001-001", "category": "GENERAL", ...},
      // ... 14 patterns SPECIFIC to Q001
    ],
    "expected_elements": [
      {"type": "fuentes_oficiales", "minimum": 2},
      {"type": "indicadores_cuantitativos", "minimum": 3}
    ]
  }
}
```

**Current Irrigation:**
```python
# Gets ALL patterns from PA01 signal pack (generic policy area patterns)
pack = registry_get("PA01")  # Returns patterns for entire PA01
patterns = pack.get("patterns", [])  # Could be 100+ patterns across all dimensions
```

**Mismatch:** Q001 needs 14 specific patterns, but receives 100+ generic PA patterns.

---

### Gap 4: No Redundancy Blocking

**Requirement:**
> If chunk or signal appears in multiple contracts—but contracts require exclusivity—manifest error and abort. No silent double irrigation.

**Current:**
- No tracking of which chunks receive which signals
- No detection if multiple executors claim same chunk
- No manifest of chunk → contract assignments

---

## Root Cause Analysis

### Why This Happened

1. **Signal Registry Design:** Built around `policy_area_id` only (no dimension awareness)
2. **Chunk Schema:** Has `policy_area_hint` but dimension is implied, not explicit
3. **My Implementation:** Followed existing registry API without questioning the (PA, DIM) requirement
4. **Missing Spec:** The synchronization requirement wasn't visible until user provided executor contracts

### Evidence from Codebase

```python
# signal_registry.py (hypothetical - need to verify)
def get_signal_pack(policy_area_id: str) -> SignalPack:
    # ❌ Only takes policy_area_id, not (policy_area_id, dimension_id)
    ...
```

```python
# Chunk structure (from tests)
chunk = {
    "id": "chunk_123",
    "text": "...",
    "policy_area_hint": "PA01",  # ✓ Has PA
    "section": "budget",
    # ❌ No explicit dimension_id field
}
```

---

## Correct Synchronization Architecture

### Step 1: Canonical JOIN Table Builder

**Location:** New module `src/farfan_pipeline/core/orchestrator/executor_chunk_synchronizer.py`

```python
@dataclass
class ExecutorChunkBinding:
    executor_contract_id: str  # Q001
    policy_area_id: str        # PA01
    dimension_id: str          # DIM01
    expected_patterns: list[dict]  # From contract.question_context.patterns
    chunk_id: str | None       # Resolved chunk ID (or None if missing)
    irrigated_signals: list[dict]  # Actual signals delivered
    status: Literal["matched", "missing_chunk", "duplicate_chunk", "mismatch"]

def build_join_table(
    contracts: list[ExecutorContract],
    chunks: list[Chunk]
) -> list[ExecutorChunkBinding]:
    """
    For each contract:
    1. Assert exactly one chunk exists with (PA, DIM) match
    2. If 0 or 2+ chunks → ABORT with manifest error
    3. Resolve contract.patterns to actual signal instances
    4. Return binding table for irrigation phase
    """
    ...
```

### Step 2: Contract-Driven Irrigation

**Modify:** `src/farfan_pipeline/flux/phases.py::run_signals()`

```python
def run_signals(ch: ChunksDeliverable, ...):
    # STEP 1: Load all 300 contracts
    contracts = load_all_executor_contracts()
    
    # STEP 2: Build JOIN table (BLOCKING - aborts on mismatch)
    bindings = build_join_table(contracts, ch.chunks)
    
    # STEP 3: Validate 1:1 invariant
    validate_uniqueness(bindings)  # Aborts if chunk mapped to 2+ contracts
    
    # STEP 4: Irrigate ONLY per binding
    for binding in bindings:
        chunk = find_chunk_by_id(ch.chunks, binding.chunk_id)
        
        # Get patterns FROM CONTRACT, not from generic PA pack
        applicable_patterns = filter_patterns_by_context(
            binding.expected_patterns,  # ← From Q001.question_context.patterns
            create_document_context(chunk)
        )
        
        # Enrich chunk with contract-specific signals
        chunk["applicable_patterns"] = applicable_patterns
        chunk["bound_to_executor"] = binding.executor_contract_id
        chunk["dimension_id"] = binding.dimension_id  # Make explicit
        
        # Track for manifest
        binding.irrigated_signals = applicable_patterns
    
    # STEP 5: Generate verification manifest
    manifest = generate_verification_manifest(bindings)
    return SignalsDeliverable(enriched_chunks=..., manifest=manifest)
```

### Step 3: Verification Manifest

**Output:** `verification_manifest.json`

```json
{
  "success": true,
  "timestamp": "2025-12-03T...",
  "total_contracts": 300,
  "total_chunks": 300,
  "bindings": [
    {
      "executor_contract_id": "Q001",
      "chunk_id": "chunk_PA01_DIM01_001",
      "policy_area_id": "PA01",
      "dimension_id": "DIM01",
      "patterns_delivered": 14,
      "pattern_ids": ["PAT-Q001-000", "PAT-Q001-001", ...],
      "status": "matched",
      "provenance": {
        "contract_file": "config/executor_contracts/specialized/Q001.v3.json",
        "contract_hash": "abc123...",
        "chunk_source": "phase1_output"
      }
    },
    // ... 299 more
  ],
  "errors": [],
  "warnings": [],
  "invariants_validated": {
    "one_to_one_mapping": true,
    "all_contracts_have_chunks": true,
    "all_chunks_assigned": true,
    "no_duplicate_irrigation": true
  }
}
```

---

## Impact Assessment

### What Breaks Without This Fix

1. **D1 chunks receive D2-D6 signals** → 500% signal bloat → Performance degradation
2. **Executor receives wrong signals** → Evidence extraction fails → Scores = 0
3. **No audit trail** → Cannot prove which signals went to which executor → Violates provenance contract
4. **CI cannot validate** → No blocking test for synchronization → Silent failures in production

### What Works Now (Lucky)

- Context filtering reduces false positives **within a policy area**
- Lineage tracking captures pattern provenance (but doesn't prevent wrong pattern delivery)

---

## Implementation Priority

### BLOCKING (Must Do Before Production)

1. **Chunk Schema Update:** Add explicit `dimension_id` field to all chunks
2. **JOIN Table Builder:** Implement `build_join_table` with 1:1 assertion
3. **Contract-Driven Irrigation:** Replace PA-only lookup with (PA, DIM) routing
4. **Verification Manifest:** Generate and validate after each run

### HIGH (Must Do Before Next Release)

5. **Redundancy Blocker:** Detect and abort on duplicate chunk assignments
6. **Integration Tests:** CI test that validates manifest.success = true for all 300 contracts
7. **Signal Registry Refactor:** Support `get_signal_pack(policy_area_id, dimension_id)`

### MEDIUM (Technical Debt)

8. **Manifest Consumer:** Dashboard endpoint to visualize synchronization status
9. **Performance Optimization:** Cache contract patterns, avoid re-loading 300 JSON files per run

---

## Questions for User

### Q1: Chunk-Dimension Binding

**Where is `dimension_id` assigned to chunks?**
- Phase 1 SPC ingestion?
- Chunk router?
- Implicit from contract lookup?

**Evidence Needed:**
```bash
grep -r "dimension_id.*chunk" src/farfan_pipeline/
```

### Q2: Signal Registry Structure

**Does the signal registry already support (PA, DIM) lookups?**
- If YES: Just fix the call site
- If NO: Must refactor registry

**Need to check:**
```python
# src/farfan_pipeline/core/orchestrator/signal_registry.py
def get(policy_area_id: str, dimension_id: str) -> SignalPack:  # ← Does this exist?
```

### Q3: Contract Pattern Source

**Should patterns come from:**
- A) `contract.question_context.patterns` (14 patterns per contract = 4,200 total patterns)
- B) `signal_registry.get(PA, DIM).patterns` (centralized registry)
- C) Intersection of A ∩ B (contract declares, registry validates)

---

## Recommendation

**DO NOT PROCEED** with current implementation in production.

**IMMEDIATE ACTION:**
1. **STOP:** Current implementation violates contract architecture
2. **AUDIT:** Run diagnostic to check if chunks have `dimension_id`
3. **DESIGN:** Decide on JOIN table location (orchestrator vs. phase)
4. **IMPLEMENT:** Canonical synchronization with manifest
5. **TEST:** CI validates manifest.success = true for all 300 contracts
6. **DEPLOY:** Only after manifest passes

---

## Files Requiring Changes

| File | Change Type | Reason |
|------|-------------|--------|
| `src/farfan_pipeline/flux/phases.py` | **REWRITE** | Replace PA-only irrigation with (PA, DIM) routing |
| `src/farfan_pipeline/core/orchestrator/executor_chunk_synchronizer.py` | **CREATE** | NEW: JOIN table builder + validator |
| `src/farfan_pipeline/core/types.py` | **MODIFY** | Add `dimension_id` to Chunk schema |
| `src/farfan_pipeline/core/orchestrator/signal_registry.py` | **AUDIT** | Check if (PA, DIM) lookup exists |
| `config/executor_contracts/specialized/*.v3.json` | **CONSUME** | Read `question_context.patterns` per contract |
| `tests/integration/test_signal_synchronization.py` | **CREATE** | NEW: Validate manifest for all 300 contracts |

---

## Conclusion

**Current Status:** ⚠️ **PROTOTYPE** (works for single policy area, breaks on multi-dimension)

**Required Status:** ✅ **PRODUCTION** (explicit (PA, DIM) routing with manifest validation)

**Effort Estimate:** 2-3 days for full synchronization implementation

**Risk if Skipped:** Pipeline produces invalid results that pass syntax checks but fail semantic contracts.
