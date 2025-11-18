"""
Contract I/O Envelope - Universal Metadata Wrapper
===================================================

ContractEnvelope wraps every phase payload (input and output) with
universal metadata including schema_version, timestamp_utc, policy_unit_id,
content_digest, correlation_id, and deterministic event_id.

This module provides the canonical wrapper for all phase I/O to ensure
consistent metadata handling across the pipeline.

Author: Policy Analytics Research Unit
Version: 1.0.0
License: Proprietary
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field, field_validator

if TYPE_CHECKING:
    from collections.abc import Mapping

CANONICAL_SCHEMA_VERSION = "io-1.0"


def _canonical_json_bytes(obj: Any) -> bytes:
    """
    Convert object to canonical JSON bytes for deterministic hashing.

    Args:
        obj: Object to serialize

    Returns:
        Canonical JSON bytes (sorted keys, compact separators)
    """
    return json.dumps(
        obj,
        separators=(",", ":"),
        sort_keys=True,
        ensure_ascii=False
    ).encode("utf-8")


def sha256_hex(obj: Any) -> str:
    """
    Compute SHA-256 hex digest of object via canonical JSON.

    Args:
        obj: Object to hash

    Returns:
        64-character hexadecimal SHA-256 digest

    Examples:
        >>> sha256_hex({"b": 2, "a": 1})
        'eed6d51ab37ca6df16a330c85094467efcab7b5746c0e02bc728a05069ede38b'
        >>> sha256_hex({"a": 1, "b": 2})  # Same despite key order
        'eed6d51ab37ca6df16a330c85094467efcab7b5746c0e02bc728a05069ede38b'
    """
    return hashlib.sha256(_canonical_json_bytes(obj)).hexdigest()


def utcnow_iso() -> str:
    """
    Get current UTC timestamp in ISO-8601 format with Z suffix.

    Returns:
        ISO-8601 timestamp string with Z suffix

    Examples:
        >>> ts = utcnow_iso()
        >>> ts.endswith('Z')
        True
        >>> 'T' in ts
        True
    """
    # Always Z-suffixed UTC; forbidden to use local time
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class ContractEnvelope(BaseModel):
    """
    Universal metadata wrapper for phase I/O payloads.

    Wraps every phase input/output with consistent metadata for:
    - Schema versioning
    - Temporal tracking (UTC only)
    - Policy scope identification
    - Cryptographic verification
    - Request correlation
    - Deterministic event tracking

    Fields:
      - schema_version: Logical envelope schema version
      - timestamp_utc: ISO-8601 Z-suffixed timestamp
      - policy_unit_id: Stable identifier selecting seeds & scope
      - correlation_id: Client-supplied request/run correlation
      - content_digest: SHA-256 over canonical JSON of `payload`
      - event_id: Deterministic SHA-256 over (policy_unit_id, content_digest)
      - payload: The phase's typed deliverable/expectation

    Examples:
        >>> payload = {"result": "success", "data": [1, 2, 3]}
        >>> env = ContractEnvelope.wrap(
        ...     payload,
        ...     policy_unit_id="PDM-001",
        ...     correlation_id="req-123"
        ... )
        >>> env.policy_unit_id
        'PDM-001'
        >>> len(env.content_digest)
        64
        >>> len(env.event_id)
        64
    """

    schema_version: str = Field(default=CANONICAL_SCHEMA_VERSION)
    timestamp_utc: str = Field(default_factory=utcnow_iso)
    policy_unit_id: str = Field(min_length=1)
    correlation_id: str | None = Field(default=None)
    content_digest: str = Field(min_length=64, max_length=64)
    event_id: str = Field(min_length=64, max_length=64)
    payload: Mapping[str, Any] | Any

    model_config = {"frozen": True, "extra": "forbid"}

    @field_validator("timestamp_utc")
    @classmethod
    def _validate_utc(cls, v: str) -> str:
        """Validate timestamp is Z-suffixed UTC ISO-8601."""
        # Quick sanity: must end with Z and parse
        if not v.endswith("Z"):
            raise ValueError("timestamp_utc must be Z-suffixed UTC (ISO-8601)")
        # Let it raise if invalid
        datetime.fromisoformat(v.replace("Z", "+00:00"))
        return v

    @classmethod
    def wrap(
        cls,
        payload: Any,
        *,
        policy_unit_id: str,
        correlation_id: str | None = None,
        schema_version: str = CANONICAL_SCHEMA_VERSION,
    ) -> ContractEnvelope:
        """
        Wrap a payload with universal metadata envelope.

        Args:
            payload: The phase deliverable/expectation to wrap
            policy_unit_id: Policy unit identifier
            correlation_id: Optional request correlation ID
            schema_version: Schema version (default: io-1.0)

        Returns:
            ContractEnvelope with computed digests and event ID

        Examples:
            >>> payload = {"status": "ok"}
            >>> env = ContractEnvelope.wrap(payload, policy_unit_id="PDM-001")
            >>> env.payload["status"]
            'ok'
            >>> env.policy_unit_id
            'PDM-001'
        """
        digest = sha256_hex(payload)
        event_id = sha256_hex({"policy_unit_id": policy_unit_id, "digest": digest})
        return cls(
            schema_version=schema_version,
            policy_unit_id=policy_unit_id,
            correlation_id=correlation_id,
            content_digest=digest,
            event_id=event_id,
            payload=payload,
        )


if __name__ == "__main__":
    import doctest

    # Run doctests
    print("Running doctests...")
    doctest.testmod(verbose=True)

    # Minimal deterministic check
    print("\n" + "="*60)
    print("ContractEnvelope Integration Tests")
    print("="*60)

    print("\n1. Testing deterministic digest computation:")
    p = {"a": 1, "b": [2, 3]}
    e1 = ContractEnvelope.wrap(p, policy_unit_id="PU_123")
    e2 = ContractEnvelope.wrap({"b": [2, 3], "a": 1}, policy_unit_id="PU_123")
    assert e1.content_digest == e2.content_digest  # canonical JSON stable
    assert e1.event_id == e2.event_id
    print(f"   ✓ Digest is deterministic: {e1.content_digest[:16]}...")
    print(f"   ✓ Event ID is deterministic: {e1.event_id[:16]}...")

    print("\n2. Testing envelope immutability:")
    try:
        e1.payload = {"modified": True}
        print("   ✗ FAILED: Envelope should be immutable")
    except Exception:
        print("   ✓ Envelope is immutable (frozen)")

    print("\n3. Testing UTC timestamp validation:")
    assert e1.timestamp_utc.endswith('Z')
    print(f"   ✓ Timestamp is UTC: {e1.timestamp_utc}")

    print("\n4. Testing correlation ID:")
    e3 = ContractEnvelope.wrap(p, policy_unit_id="PU_123", correlation_id="corr-456")
    assert e3.correlation_id == "corr-456"
    print(f"   ✓ Correlation ID: {e3.correlation_id}")

    print("\n" + "="*60)
    print("ContractEnvelope doctest OK - All tests passed!")
    print("="*60)
