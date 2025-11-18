"""
Flow Adapters - Thin Compatibility Layer
=========================================

Provides thin adapters for wrapping and unwrapping payloads with
ContractEnvelope to maintain flow compatibility across pipeline stages.

Functions:
    - wrap_payload: Wrap a payload in ContractEnvelope
    - unwrap_payload: Extract payload from ContractEnvelope with optional validation

Author: Policy Analytics Research Unit
Version: 1.0.0
License: Proprietary
"""

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel

from .contract_io import ContractEnvelope

T = TypeVar("T", bound=BaseModel)


def wrap_payload(
    payload: Any,
    *,
    policy_unit_id: str,
    correlation_id: str | None = None
) -> ContractEnvelope:
    """
    Wrap a payload with ContractEnvelope metadata.

    Args:
        payload: The payload to wrap
        policy_unit_id: Policy unit identifier
        correlation_id: Optional correlation ID

    Returns:
        ContractEnvelope containing the payload

    Examples:
        >>> env = wrap_payload(
        ...     {"status": "ok"},
        ...     policy_unit_id="PU_1",
        ...     correlation_id="req-123"
        ... )
        >>> env.policy_unit_id
        'PU_1'
        >>> env.correlation_id
        'req-123'
        >>> env.payload["status"]
        'ok'
    """
    return ContractEnvelope.wrap(
        payload,
        policy_unit_id=policy_unit_id,
        correlation_id=correlation_id
    )


def unwrap_payload(
    envelope: ContractEnvelope,
    expected_model: type[T] | None = None
) -> Any:
    """
    Extract payload from ContractEnvelope with optional validation.

    Args:
        envelope: The envelope to unwrap
        expected_model: Optional Pydantic model to validate against

    Returns:
        The unwrapped payload, optionally validated

    Examples:
        >>> env = wrap_payload({"a": 1}, policy_unit_id="PU_1")
        >>> unwrap_payload(env)
        {'a': 1}
        >>> unwrap_payload(env) == {"a": 1}
        True
    """
    raw = envelope.payload
    return expected_model.model_validate(raw) if expected_model is not None else raw


def get_envelope_metadata(envelope: ContractEnvelope) -> dict[str, Any]:
    """
    Extract metadata from ContractEnvelope.

    Args:
        envelope: The envelope

    Returns:
        Dictionary with metadata fields

    Examples:
        >>> env = wrap_payload({"data": 1}, policy_unit_id="PU_1")
        >>> meta = get_envelope_metadata(env)
        >>> meta["policy_unit_id"]
        'PU_1'
        >>> "content_digest" in meta
        True
        >>> "event_id" in meta
        True
    """
    return {
        "schema_version": envelope.schema_version,
        "timestamp_utc": envelope.timestamp_utc,
        "policy_unit_id": envelope.policy_unit_id,
        "correlation_id": envelope.correlation_id,
        "content_digest": envelope.content_digest,
        "event_id": envelope.event_id,
    }


if __name__ == "__main__":
    import doctest

    # Run doctests
    print("Running doctests...")
    doctest.testmod(verbose=True)

    # Integration tests
    print("\n" + "="*60)
    print("Flow Adapters Integration Tests")
    print("="*60)

    print("\n1. Testing wrap_payload:")
    env = wrap_payload({"a": 1}, policy_unit_id="PU_1")
    assert env.payload == {"a": 1}
    assert env.policy_unit_id == "PU_1"
    assert len(env.content_digest) == 64
    print("   ✓ Payload wrapped successfully")
    print(f"      Policy Unit: {env.policy_unit_id}")
    print(f"      Digest: {env.content_digest[:16]}...")

    print("\n2. Testing unwrap_payload without validation:")
    payload = unwrap_payload(env)
    assert payload == {"a": 1}
    print("   ✓ Payload unwrapped successfully")
    print(f"      Payload: {payload}")

    print("\n3. Testing unwrap_payload with Pydantic validation:")

    class TestModel(BaseModel):
        a: int

    env2 = wrap_payload({"a": 42}, policy_unit_id="PU_2")
    validated = unwrap_payload(env2, TestModel)
    assert isinstance(validated, TestModel)
    assert validated.a == 42
    print("   ✓ Payload validated with Pydantic model")
    print(f"      Validated value: {validated.a}")

    print("\n4. Testing get_envelope_metadata:")
    env3 = wrap_payload(
        {"data": "test"},
        policy_unit_id="PU_3",
        correlation_id="corr-789"
    )
    meta = get_envelope_metadata(env3)
    assert meta["policy_unit_id"] == "PU_3"
    assert meta["correlation_id"] == "corr-789"
    assert "content_digest" in meta
    assert "event_id" in meta
    assert "timestamp_utc" in meta
    print("   ✓ Metadata extracted successfully")
    print(f"      Keys: {list(meta.keys())}")

    print("\n5. Testing round-trip wrap/unwrap:")
    original = {"key": "value", "number": 123}
    wrapped = wrap_payload(original, policy_unit_id="PU_4")
    unwrapped = unwrap_payload(wrapped)
    assert unwrapped == original
    print("   ✓ Round-trip wrap/unwrap preserves data")

    print("\n6. Testing correlation ID propagation:")
    env_with_corr = wrap_payload(
        {"test": True},
        policy_unit_id="PU_5",
        correlation_id="my-correlation-id"
    )
    assert env_with_corr.correlation_id == "my-correlation-id"
    meta_with_corr = get_envelope_metadata(env_with_corr)
    assert meta_with_corr["correlation_id"] == "my-correlation-id"
    print("   ✓ Correlation ID propagated correctly")

    print("\n" + "="*60)
    print("Adapters doctest OK - All tests passed!")
    print("="*60)
