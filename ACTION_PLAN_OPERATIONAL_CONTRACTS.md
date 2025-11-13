# Action Plan: Making Contract Infrastructure Operational

## Current Status: Infrastructure Built, Not Yet Integrated

**Problem:** All the contract infrastructure exists but is not wired into the actual pipeline. It's currently "ornamental" - documentation and examples but no real usage.

## Concrete Benefits This Infrastructure Provides

### 1. **Cryptographic Verification** (Currently: Manual/None)
- **Before:** No verification that phase outputs match inputs between stages
- **After:** SHA-256 digests prove data hasn't been corrupted/modified
- **Real Impact:** Catch pipeline bugs where data gets lost or corrupted

### 2. **Reproducibility** (Currently: Non-deterministic)
- **Before:** Same PDF analyzed twice = different results (random seeds not controlled)
- **After:** Same PDF + same policy_unit_id = identical results every time
- **Real Impact:** Debugging becomes possible; can reproduce issues reliably

### 3. **Traceability** (Currently: Print statements)
- **Before:** Ad-hoc print() statements, no correlation across phases
- **After:** Every operation has correlation_id + event_id, structured JSON logs
- **Real Impact:** Can trace a request through the entire pipeline; find bottlenecks

### 4. **Error Clarity** (Currently: Generic exceptions)
- **Before:** Generic ValueError/TypeError with no context
- **After:** DataContractError vs SystemContractError with event_id for tracking
- **Real Impact:** Know immediately if it's bad data or bad configuration

## Specific Actions Required to Make This Operational

### Phase 1: Wire ContractEnvelope into ONE Phase (Proof of Concept)

**Target:** `saaaaaa/flux/phases.py` - start with the normalize phase

**File to modify:** Find the normalize phase and add envelope wrapping

```python
# In saaaaaa/flux/phases.py
from saaaaaa.utils.contract_io import ContractEnvelope
from saaaaaa.utils.json_logger import get_json_logger, log_io_event
import time

def run_normalize_phase(input_deliverable, *, policy_unit_id: str, correlation_id: str = None):
    logger = get_json_logger("flux.normalize")
    started = time.monotonic()
    
    # Wrap input
    env_in = ContractEnvelope.wrap(
        input_deliverable.model_dump(),
        policy_unit_id=policy_unit_id,
        correlation_id=correlation_id
    )
    
    # ... existing normalization logic ...
    
    # Wrap output
    env_out = ContractEnvelope.wrap(
        output_deliverable.model_dump(),
        policy_unit_id=policy_unit_id,
        correlation_id=correlation_id
    )
    
    # Log structured event
    log_io_event(logger, phase="normalize", envelope_in=env_in, 
                 envelope_out=env_out, started_monotonic=started)
    
    return env_out  # or return both for backward compat
```

**Acceptance Criteria:**
- Phase logs JSON to console with correlation_id and digests
- Same input produces same digest (verify determinism)
- Output includes timestamp_utc and event_id

### Phase 2: Wire Deterministic Seeding into Executors

**Target:** `saaaaaa/core/orchestrator/executors.py` - AdvancedDataFlowExecutor

**File to modify:** Add deterministic context to execute method

```python
# In saaaaaa/core/orchestrator/executors.py
from saaaaaa.utils.determinism_helpers import deterministic, create_deterministic_rng

class AdvancedDataFlowExecutor:
    def execute(self, doc, method_executor, *, policy_unit_id: str, correlation_id: str = None):
        with deterministic(policy_unit_id, correlation_id) as seeds:
            # Replace global np.random calls
            rng = create_deterministic_rng(seeds.np)
            
            # Replace: path = np.random.choice(paths)
            # With: path = rng.choice(paths)
            
            return self._execute_deterministically(doc, method_executor, rng)
```

**Acceptance Criteria:**
- Run same document twice → get identical results
- No more global np.random usage in executor
- Seeds logged in structured logs

### Phase 3: Add policy_unit_id to Pipeline Entrypoint

**Target:** Main pipeline entry point (likely `scripts/run_policy_pipeline_verified.py` or similar)

**File to modify:** Add policy_unit_id parameter derived from PDF filename

```python
# In pipeline entrypoint
def analyze_pdf(pdf_path: Path) -> Dict:
    # Derive policy_unit_id from filename
    policy_unit_id = pdf_path.stem  # e.g., "Plan_1" → "Plan_1"
    correlation_id = str(uuid.uuid4())
    
    # Pass through to all phases
    result = run_pipeline(
        pdf_path=pdf_path,
        policy_unit_id=policy_unit_id,
        correlation_id=correlation_id
    )
    
    return result
```

**Acceptance Criteria:**
- Every phase receives policy_unit_id
- Correlation_id is consistent across all phases
- Logs show the same correlation_id for entire run

### Phase 4: Create Verification Script

**Target:** `scripts/verify_contracts_operational.py` (new file)

**Purpose:** Prove the infrastructure actually works

```python
#!/usr/bin/env python3
"""Verify contract infrastructure is operational."""

import sys
sys.path.insert(0, 'src')

from pathlib import Path
from saaaaaa.utils.contract_io import ContractEnvelope
from saaaaaa.utils.determinism_helpers import deterministic
import numpy as np

def test_envelope_wrapping():
    """Test ContractEnvelope actually wraps data."""
    payload = {"test": "data"}
    env = ContractEnvelope.wrap(payload, policy_unit_id="TEST-001")
    
    assert env.content_digest is not None
    assert env.event_id is not None
    assert env.timestamp_utc.endswith('Z')
    print("✓ Envelope wrapping works")

def test_determinism():
    """Test deterministic execution actually works."""
    results = []
    for _ in range(2):
        with deterministic("TEST-001", "run-1"):
            results.append(np.random.rand(5).tolist())
    
    assert results[0] == results[1], "Determinism failed!"
    print("✓ Deterministic execution works")

def test_digest_stability():
    """Test same data produces same digest."""
    env1 = ContractEnvelope.wrap({"a": 1, "b": 2}, policy_unit_id="TEST-001")
    env2 = ContractEnvelope.wrap({"b": 2, "a": 1}, policy_unit_id="TEST-001")
    
    assert env1.content_digest == env2.content_digest
    print("✓ Content digests are stable (canonical JSON)")

if __name__ == "__main__":
    test_envelope_wrapping()
    test_determinism()
    test_digest_stability()
    print("\n" + "="*60)
    print("All operational tests passed!")
    print("Contract infrastructure is OPERATIONAL, not ornamental.")
    print("="*60)
```

**Acceptance Criteria:**
- Script runs without errors
- All assertions pass
- Clear indication infrastructure is working

## Measurable Outcomes

### Week 1: Basic Integration
- [ ] One FLUX phase uses ContractEnvelope
- [ ] JSON logs visible in console output
- [ ] Verification script passes

### Week 2: Full Integration  
- [ ] All FLUX phases use ContractEnvelope
- [ ] Executors use deterministic() context
- [ ] Pipeline runs end-to-end with correlation_id

### Week 3: Benefits Realized
- [ ] Can reproduce a bug by reusing same policy_unit_id + correlation_id
- [ ] Logs show exact flow of data through pipeline
- [ ] Caught at least one data corruption issue via digest mismatch

## How to Avoid "Pile of Nothingness"

### ❌ What NOT to Do:
- Leave infrastructure unused in the codebase
- Only use in examples but not production code
- Make integration "optional" so nobody uses it
- Add complexity without removing old code

### ✅ What TO Do:
1. **Integration First:** Wire into actual pipeline ASAP
2. **Deprecate Old:** Mark old non-envelope code as deprecated
3. **Measure Impact:** Track how many issues caught by digests/determinism
4. **Enforce in CI:** Require correlation_id in all pipeline runs
5. **Delete Examples:** Once integrated, remove example files (they're now redundant)

## Next Immediate Steps (Priority Order)

1. **TODAY:** Create verification script and prove infrastructure works standalone
2. **THIS WEEK:** Integrate ContractEnvelope into ONE phase (normalize)
3. **NEXT WEEK:** Add deterministic seeding to ONE executor
4. **FOLLOWING:** Expand to all phases and executors
5. **FINALLY:** Remove old non-deterministic code paths

## Concrete Value Metrics

After full integration, you should be able to:

1. **Reproduce any issue:** "Run with `policy_unit_id=PDM-001, correlation_id=abc123`" → identical results
2. **Trace any request:** Grep logs for correlation_id → see entire flow
3. **Verify integrity:** Compare content_digest between stages → catch corruption
4. **Debug faster:** event_id in errors → find exact operation that failed
5. **Measure performance:** latency_ms in logs → identify bottlenecks

## The Bottom Line

**Current State:** Infrastructure exists but unused = "ornamental"

**Required State:** Infrastructure integrated into pipeline = "operational"

**Gap:** 3-4 days of integration work to wire into existing code

**Value:** Reproducibility, traceability, integrity verification - things the pipeline currently lacks

The infrastructure is **not** a pile of nothingness - it's **production-grade tooling waiting to be used**. The question is: **when will we integrate it into the actual pipeline?**
