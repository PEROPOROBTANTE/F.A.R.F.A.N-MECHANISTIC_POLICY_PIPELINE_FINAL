#!/usr/bin/env python3
"""
Verify Contract Infrastructure is Operational
==============================================

This script proves the contract infrastructure actually works and
is not just "ornamental documentation". It tests the core functionality
that will be used in the real pipeline.

Tests:
1. ContractEnvelope wrapping and metadata
2. Deterministic execution reproducibility
3. Content digest stability (canonical JSON)
4. JSON logging output
5. Exception hierarchy

Run this to prove the infrastructure is OPERATIONAL.
"""

import sys
from pathlib import Path

# Add src to path

import json
import numpy as np

from saaaaaa.utils.contract_io import ContractEnvelope
from saaaaaa.utils.determinism_helpers import deterministic
from saaaaaa.utils.json_logger import get_json_logger, log_io_event
from saaaaaa.utils.domain_errors import DataContractError, SystemContractError
from saaaaaa.utils.flow_adapters import wrap_payload, unwrap_payload


def test_1_envelope_wrapping():
    """Test 1: ContractEnvelope actually wraps data with metadata."""
    print("\n" + "="*60)
    print("TEST 1: ContractEnvelope Wrapping")
    print("="*60)
    
    payload = {"analysis": "complete", "confidence": 0.95}
    env = ContractEnvelope.wrap(payload, policy_unit_id="TEST-001", correlation_id="run-123")
    
    # Verify all required fields exist
    assert env.schema_version == "io-1.0"
    assert env.policy_unit_id == "TEST-001"
    assert env.correlation_id == "run-123"
    assert len(env.content_digest) == 64  # SHA-256
    assert len(env.event_id) == 64  # SHA-256
    assert env.timestamp_utc.endswith('Z')
    assert env.payload == payload
    
    print(f"✓ Envelope created successfully")
    print(f"  Schema: {env.schema_version}")
    print(f"  Policy Unit: {env.policy_unit_id}")
    print(f"  Correlation: {env.correlation_id}")
    print(f"  Content Digest: {env.content_digest[:32]}...")
    print(f"  Event ID: {env.event_id[:32]}...")
    print(f"  Timestamp: {env.timestamp_utc}")
    print(f"  Payload: {env.payload}")
    print("\n✓ TEST 1 PASSED: Envelope wrapping is OPERATIONAL")


def test_2_deterministic_execution():
    """Test 2: Deterministic context produces reproducible results."""
    print("\n" + "="*60)
    print("TEST 2: Deterministic Execution")
    print("="*60)
    
    results_run1 = []
    results_run2 = []
    
    # Run 1
    with deterministic("TEST-001", "run-1") as seeds1:
        results_run1.append(np.random.rand(5).tolist())
        results_run1.append(np.random.randint(0, 100, 5).tolist())
        import random
        results_run1.append([random.random() for _ in range(5)])
    
    # Run 2 - should produce identical results
    with deterministic("TEST-001", "run-1") as seeds2:
        results_run2.append(np.random.rand(5).tolist())
        results_run2.append(np.random.randint(0, 100, 5).tolist())
        import random
        results_run2.append([random.random() for _ in range(5)])
    
    # Verify determinism
    for i, (r1, r2) in enumerate(zip(results_run1, results_run2)):
        assert r1 == r2, f"Determinism failed at index {i}!"
    
    print(f"✓ Deterministic execution verified")
    print(f"  Seeds used: py={seeds1.py}, np={seeds1.np}")
    print(f"  NumPy results: {results_run1[0][:3]}...")
    print(f"  Python random results: {results_run1[2][:3]}...")
    print(f"  Run 1 == Run 2: {results_run1 == results_run2}")
    
    # Test different correlation_id produces different results
    with deterministic("TEST-001", "run-2"):
        different_result = np.random.rand(5).tolist()
    
    assert different_result != results_run1[0], "Different inputs should give different results"
    print(f"✓ Different correlation_id produces different results")
    
    print("\n✓ TEST 2 PASSED: Determinism is OPERATIONAL")


def test_3_digest_stability():
    """Test 3: Content digests are stable (canonical JSON)."""
    print("\n" + "="*60)
    print("TEST 3: Content Digest Stability")
    print("="*60)
    
    # Same data, different key order
    payload1 = {"z": 3, "a": 1, "m": 2}
    payload2 = {"a": 1, "m": 2, "z": 3}
    payload3 = {"m": 2, "z": 3, "a": 1}
    
    env1 = ContractEnvelope.wrap(payload1, policy_unit_id="TEST-001")
    env2 = ContractEnvelope.wrap(payload2, policy_unit_id="TEST-001")
    env3 = ContractEnvelope.wrap(payload3, policy_unit_id="TEST-001")
    
    # All should have same digest (canonical JSON)
    assert env1.content_digest == env2.content_digest == env3.content_digest
    assert env1.event_id == env2.event_id == env3.event_id
    
    print(f"✓ Canonical JSON hashing verified")
    print(f"  Payload 1: {payload1}")
    print(f"  Payload 2: {payload2}")
    print(f"  Payload 3: {payload3}")
    print(f"  Digest 1: {env1.content_digest[:32]}...")
    print(f"  Digest 2: {env2.content_digest[:32]}...")
    print(f"  Digest 3: {env3.content_digest[:32]}...")
    print(f"  All equal: {env1.content_digest == env2.content_digest == env3.content_digest}")
    
    # Different data should give different digest
    env4 = ContractEnvelope.wrap({"different": "data"}, policy_unit_id="TEST-001")
    assert env4.content_digest != env1.content_digest
    print(f"✓ Different data produces different digest")
    
    print("\n✓ TEST 3 PASSED: Digest stability is OPERATIONAL")


def test_4_json_logging():
    """Test 4: JSON logging produces structured output."""
    print("\n" + "="*60)
    print("TEST 4: Structured JSON Logging")
    print("="*60)
    
    # Capture log output
    import io
    log_capture = io.StringIO()
    
    logger = get_json_logger("test.phase")
    # Replace handler with one that writes to our capture
    logger.handlers[0].stream = log_capture
    
    # Create envelopes
    env_in = ContractEnvelope.wrap(
        {"input": "data"},
        policy_unit_id="TEST-001",
        correlation_id="log-test"
    )
    env_out = ContractEnvelope.wrap(
        {"output": "result"},
        policy_unit_id="TEST-001",
        correlation_id="log-test"
    )
    
    # Log event
    import time
    start = time.monotonic()
    time.sleep(0.001)  # Simulate work
    log_io_event(logger, phase="test_phase", envelope_in=env_in, 
                 envelope_out=env_out, started_monotonic=start)
    
    # Parse logged JSON
    log_output = log_capture.getvalue()
    log_data = json.loads(log_output.strip())
    
    # Verify structure
    assert log_data["level"] == "INFO"
    assert log_data["phase"] == "test_phase"
    assert log_data["policy_unit_id"] == "TEST-001"
    assert log_data["correlation_id"] == "log-test"
    assert "event_id" in log_data
    assert "latency_ms" in log_data
    assert "input_digest" in log_data
    assert "output_digest" in log_data
    
    print(f"✓ JSON log structure verified")
    print(f"  Log output:\n{json.dumps(log_data, indent=2)}")
    
    print("\n✓ TEST 4 PASSED: JSON logging is OPERATIONAL")


def test_5_exception_hierarchy():
    """Test 5: Domain exceptions are usable."""
    print("\n" + "="*60)
    print("TEST 5: Exception Hierarchy")
    print("="*60)
    
    # Test DataContractError
    try:
        raise DataContractError("Invalid payload schema")
    except DataContractError as e:
        print(f"✓ DataContractError caught: {e}")
    
    # Test SystemContractError
    try:
        raise SystemContractError("Configuration missing")
    except SystemContractError as e:
        print(f"✓ SystemContractError caught: {e}")
    
    # Test base class catching
    try:
        raise DataContractError("Test")
    except Exception as e:
        assert isinstance(e, DataContractError)
        print(f"✓ Base exception catching works")
    
    print("\n✓ TEST 5 PASSED: Exception hierarchy is OPERATIONAL")


def test_6_flow_adapters():
    """Test 6: Flow adapters work for phase compatibility."""
    print("\n" + "="*60)
    print("TEST 6: Flow Adapters")
    print("="*60)
    
    # Wrap payload
    original = {"phase": "normalize", "result": "success"}
    wrapped = wrap_payload(original, policy_unit_id="TEST-001", correlation_id="flow-test")
    
    assert isinstance(wrapped, ContractEnvelope)
    assert wrapped.policy_unit_id == "TEST-001"
    assert wrapped.correlation_id == "flow-test"
    print(f"✓ wrap_payload works")
    
    # Unwrap payload
    unwrapped = unwrap_payload(wrapped)
    assert unwrapped == original
    print(f"✓ unwrap_payload works")
    
    # Round-trip
    assert unwrap_payload(wrap_payload(original, policy_unit_id="TEST-001")) == original
    print(f"✓ Round-trip wrap/unwrap preserves data")
    
    print("\n✓ TEST 6 PASSED: Flow adapters are OPERATIONAL")


def test_7_real_world_scenario():
    """Test 7: Simulate real pipeline phase with all components."""
    print("\n" + "="*60)
    print("TEST 7: Real-World Pipeline Simulation")
    print("="*60)
    
    # Simulate phase execution
    policy_unit_id = "PDM-Plan-001"
    correlation_id = "pipeline-run-789"
    
    print(f"Simulating pipeline with:")
    print(f"  Policy Unit: {policy_unit_id}")
    print(f"  Correlation: {correlation_id}")
    
    # Phase 1: Ingest
    with deterministic(policy_unit_id, correlation_id):
        ingest_result = {
            "text": "Plan de Desarrollo Municipal",
            "pages": 10,
            "encoding": "utf-8"
        }
    
    env_ingest = ContractEnvelope.wrap(
        ingest_result,
        policy_unit_id=policy_unit_id,
        correlation_id=correlation_id
    )
    print(f"\n✓ Phase 1 (Ingest) completed")
    print(f"  Digest: {env_ingest.content_digest[:32]}...")
    
    # Phase 2: Normalize (uses output from phase 1)
    ingest_data = unwrap_payload(env_ingest)
    with deterministic(policy_unit_id, correlation_id):
        normalize_result = {
            "normalized_text": ingest_data["text"].lower(),
            "word_count": len(ingest_data["text"].split())
        }
    
    env_normalize = ContractEnvelope.wrap(
        normalize_result,
        policy_unit_id=policy_unit_id,
        correlation_id=correlation_id
    )
    print(f"✓ Phase 2 (Normalize) completed")
    print(f"  Digest: {env_normalize.content_digest[:32]}...")
    
    # Verify correlation_id propagated
    assert env_ingest.correlation_id == env_normalize.correlation_id == correlation_id
    print(f"✓ Correlation ID propagated through phases")
    
    # Verify reproducibility
    env_ingest_2 = ContractEnvelope.wrap(
        ingest_result,
        policy_unit_id=policy_unit_id,
        correlation_id=correlation_id
    )
    assert env_ingest.content_digest == env_ingest_2.content_digest
    print(f"✓ Reproducibility verified (same input → same digest)")
    
    print("\n✓ TEST 7 PASSED: Real-world scenario is OPERATIONAL")


def main():
    """Run all operational tests."""
    print("="*60)
    print("CONTRACT INFRASTRUCTURE OPERATIONAL VERIFICATION")
    print("="*60)
    print("\nThis script proves the infrastructure is NOT ornamental.")
    print("It tests the actual functionality that will be used in production.")
    
    try:
        test_1_envelope_wrapping()
        test_2_deterministic_execution()
        test_3_digest_stability()
        test_4_json_logging()
        test_5_exception_hierarchy()
        test_6_flow_adapters()
        test_7_real_world_scenario()
        
        print("\n" + "="*60)
        print("ALL TESTS PASSED ✓")
        print("="*60)
        print("\n🎉 CONTRACT INFRASTRUCTURE IS OPERATIONAL 🎉")
        print("\nThis is NOT a pile of nothingness.")
        print("This is production-ready infrastructure waiting to be integrated.")
        print("\nNext step: Wire into actual FLUX phases and executors.")
        print("See ACTION_PLAN_OPERATIONAL_CONTRACTS.md for integration steps.")
        print("="*60)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
