"""
ContractEnvelope Integration Example
====================================

Demonstrates how to use the new envelope-based contract system
in a typical phase execution scenario.

This example shows:
1. Wrapping phase I/O with ContractEnvelope
2. Using deterministic() context for reproducibility
3. Structured JSON logging with log_io_event()
4. Flow adapters for compatibility

Author: Policy Analytics Research Unit
Version: 1.0.0
"""

import sys
from pathlib import Path

# Add src to path

import time
from saaaaaa.utils.contract_io import ContractEnvelope
from saaaaaa.utils.determinism_helpers import deterministic
from saaaaaa.utils.json_logger import get_json_logger, log_io_event
from saaaaaa.utils.flow_adapters import wrap_payload, unwrap_payload
from saaaaaa.utils.domain_errors import DataContractError


def run_normalize_phase(
    raw_text: str,
    *,
    policy_unit_id: str,
    correlation_id: str | None = None
) -> ContractEnvelope:
    """
    Example phase: Normalize text with full envelope workflow.
    
    Args:
        raw_text: Raw input text
        policy_unit_id: Policy unit identifier
        correlation_id: Optional correlation ID
        
    Returns:
        ContractEnvelope with normalized result
    """
    logger = get_json_logger("flux.normalize")
    started = time.monotonic()
    
    # Wrap input
    input_payload = {"raw_text": raw_text, "length": len(raw_text)}
    env_in = wrap_payload(
        input_payload,
        policy_unit_id=policy_unit_id,
        correlation_id=correlation_id
    )
    
    # Execute with deterministic seeding
    with deterministic(policy_unit_id, correlation_id) as seeds:
        # Normalize (deterministic operation)
        normalized = raw_text.strip().replace("\n\n", "\n")
        
        # Build output payload
        output_payload = {
            "normalized_text": normalized,
            "length": len(normalized),
            "seed_used": seeds.py
        }
    
    # Wrap output
    env_out = wrap_payload(
        output_payload,
        policy_unit_id=policy_unit_id,
        correlation_id=correlation_id
    )
    
    # Log I/O event
    log_io_event(
        logger,
        phase="normalize",
        envelope_in=env_in,
        envelope_out=env_out,
        started_monotonic=started
    )
    
    return env_out


def run_analysis_phase(
    normalized_env: ContractEnvelope,
    *,
    policy_unit_id: str,
    correlation_id: str | None = None
) -> ContractEnvelope:
    """
    Example phase: Analyze normalized text.
    
    Args:
        normalized_env: Envelope from previous phase
        policy_unit_id: Policy unit identifier
        correlation_id: Optional correlation ID
        
    Returns:
        ContractEnvelope with analysis results
    """
    logger = get_json_logger("flux.analyze")
    started = time.monotonic()
    
    # Unwrap input from previous phase
    input_payload = unwrap_payload(normalized_env)
    
    # Validate we got expected fields
    if "normalized_text" not in input_payload:
        raise DataContractError(
            "Missing 'normalized_text' field from normalization phase"
        )
    
    text = input_payload["normalized_text"]
    
    # Execute with deterministic seeding
    with deterministic(policy_unit_id, correlation_id):
        # Simple analysis example
        keywords = ["diagnóstico", "estratégico", "financiero"]
        matches = [kw for kw in keywords if kw in text.lower()]
        
        output_payload = {
            "keywords_found": matches,
            "match_count": len(matches),
            "confidence": len(matches) / len(keywords) if keywords else 0.0
        }
    
    # Wrap output
    env_out = wrap_payload(
        output_payload,
        policy_unit_id=policy_unit_id,
        correlation_id=correlation_id
    )
    
    # Log I/O event
    log_io_event(
        logger,
        phase="analyze",
        envelope_in=normalized_env,
        envelope_out=env_out,
        started_monotonic=started
    )
    
    return env_out


if __name__ == "__main__":
    print("="*60)
    print("ContractEnvelope Integration Example")
    print("="*60)
    
    # Example policy text
    test_text = """
    Diagnóstico situacional del municipio.
    Plan estratégico de desarrollo.
    Presupuesto y plan financiero plurianual.
    """
    
    policy_unit_id = "PDM-001"
    correlation_id = "example-run-001"
    
    print(f"\nPolicy Unit ID: {policy_unit_id}")
    print(f"Correlation ID: {correlation_id}")
    print(f"Input text: {len(test_text)} chars")
    
    # Phase 1: Normalize
    print("\n" + "-"*60)
    print("Phase 1: Normalization")
    print("-"*60)
    
    norm_env = run_normalize_phase(
        test_text,
        policy_unit_id=policy_unit_id,
        correlation_id=correlation_id
    )
    
    print(f"✓ Output envelope created")
    print(f"  Schema: {norm_env.schema_version}")
    print(f"  Timestamp: {norm_env.timestamp_utc}")
    print(f"  Content digest: {norm_env.content_digest[:16]}...")
    print(f"  Event ID: {norm_env.event_id[:16]}...")
    
    # Phase 2: Analysis
    print("\n" + "-"*60)
    print("Phase 2: Analysis")
    print("-"*60)
    
    analysis_env = run_analysis_phase(
        norm_env,
        policy_unit_id=policy_unit_id,
        correlation_id=correlation_id
    )
    
    print(f"✓ Analysis envelope created")
    print(f"  Schema: {analysis_env.schema_version}")
    print(f"  Content digest: {analysis_env.content_digest[:16]}...")
    print(f"  Event ID: {analysis_env.event_id[:16]}...")
    
    # Extract and display results
    results = unwrap_payload(analysis_env)
    print(f"\n✓ Results:")
    print(f"  Keywords found: {results['keywords_found']}")
    print(f"  Match count: {results['match_count']}")
    print(f"  Confidence: {results['confidence']:.2f}")
    
    # Verify determinism
    print("\n" + "-"*60)
    print("Verifying Determinism")
    print("-"*60)
    
    norm_env2 = run_normalize_phase(
        test_text,
        policy_unit_id=policy_unit_id,
        correlation_id=correlation_id
    )
    
    # Same input + same IDs = same digest
    if norm_env.content_digest == norm_env2.content_digest:
        print("✓ Determinism verified: identical digests")
        print(f"  Digest 1: {norm_env.content_digest[:32]}...")
        print(f"  Digest 2: {norm_env2.content_digest[:32]}...")
    else:
        print("✗ Determinism check failed!")
    
    print("\n" + "="*60)
    print("Example complete!")
    print("="*60)
    print("\nKey Features Demonstrated:")
    print("  ✓ ContractEnvelope wrapping")
    print("  ✓ Deterministic execution")
    print("  ✓ Structured JSON logging")
    print("  ✓ Flow compatibility (phase chaining)")
    print("  ✓ Domain-specific exceptions")
