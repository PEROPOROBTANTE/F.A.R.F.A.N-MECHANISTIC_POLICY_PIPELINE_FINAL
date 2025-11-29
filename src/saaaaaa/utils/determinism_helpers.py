"""
Determinism Helpers - Centralized Seeding and State Management
==============================================================

Provides centralized determinism enforcement for the entire pipeline:
- Stable seed derivation from policy_unit_id and correlation_id
- Context manager for scoped deterministic execution
- Controls random, numpy.random, and other stochastic libraries

Author: Policy Analytics Research Unit
Version: 1.0.0
License: Proprietary
"""

from __future__ import annotations

import json
import os
import random
from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
from typing import TYPE_CHECKING, Any

import numpy as np
from saaaaaa.core.calibration.decorators import calibrated_method

if TYPE_CHECKING:
    from collections.abc import Iterator


def _seed_from(*parts: Any) -> int:
    """
    Derive a 32-bit seed from arbitrary parts via SHA-256.

    Args:
        *parts: Components to hash (will be JSON-serialized)

    Returns:
        32-bit integer seed suitable for random/numpy

    Examples:
        >>> s1 = _seed_from("PU_123", "corr-1")
        >>> s2 = _seed_from("PU_123", "corr-1")
        >>> s1 == s2
        True
        >>> s3 = _seed_from("PU_123", "corr-2")
        >>> s1 != s3
        True
    """
    raw = json.dumps(parts, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    # 32-bit seed for numpy/py random
    return int(sha256(raw.encode("utf-8")).hexdigest()[:8], 16)


@dataclass(frozen=True)
class Seeds:
    """Container for seeds used in deterministic execution."""
    py: int
    np: int


@contextmanager
def deterministic(
    policy_unit_id: str | None = None,
    correlation_id: str | None = None
) -> Iterator[Seeds]:
    """
    Context manager for deterministic execution.

    Sets seeds for Python's random and NumPy's random based on
    policy_unit_id and correlation_id. Seeds are derived deterministically
    via SHA-256 hashing.

    Args:
        policy_unit_id: Policy unit identifier (default: env var or "default")
        correlation_id: Correlation identifier (default: env var or "run")

    Yields:
        Seeds object with py and np seed values

    Examples:
        >>> with deterministic("PU_123", "corr-1") as seeds:
        ...     v1 = random.random()
        ...     a1 = np.random.rand(3)
        >>> with deterministic("PU_123", "corr-1") as seeds:
        ...     v2 = random.random()
        ...     a2 = np.random.rand(3)
        >>> v1 == v2  # Deterministic
        True
        >>> np.array_equal(a1, a2)  # Deterministic
        True
    """
    base = policy_unit_id or os.getenv("POLICY_UNIT_ID", "default")
    salt = correlation_id or os.getenv("CORRELATION_ID", "run")
    s = _seed_from("fixed", base, salt)

    # Set seeds for both random modules
    random.seed(s)
    np.random.seed(s)

    try:
        yield Seeds(py=s, np=s)
    finally:
        # Keep deterministic state; caller may reseed per-phase if needed
        pass


def create_deterministic_rng(seed: int) -> np.random.Generator:
    """
    Create a deterministic NumPy random number generator.

    Use this for local RNG that doesn't affect global state.

    Args:
        seed: Integer seed

    Returns:
        NumPy Generator instance

    Examples:
        >>> rng = create_deterministic_rng(42)
        >>> v1 = rng.random()
        >>> rng = create_deterministic_rng(42)
        >>> v2 = rng.random()
        >>> v1 == v2
        True
    """
    return np.random.default_rng(seed)


if __name__ == "__main__":
    import doctest

    # Run doctests
    print("Running doctests...")
    doctest.testmod(verbose=True)

    # Integration tests
    print("\n" + "="*60)
    print("Determinism Integration Tests")
    print("="*60)

    print("\n1. Testing seed derivation:")
    s1 = _seed_from("PU_123", "corr-1")
    s2 = _seed_from("PU_123", "corr-1")
    s3 = _seed_from("PU_123", "corr-2")
    assert s1 == s2
    assert s1 != s3
    print(f"   ✓ Same inputs → same seed: {s1}")
    print(f"   ✓ Different inputs → different seed: {s3}")

    print("\n2. Testing deterministic context with random:")
    with deterministic("PU_123", "corr-1") as seeds1:
        a = random.random()
        b = random.randint(0, 100)
    with deterministic("PU_123", "corr-1") as seeds2:
        c = random.random()
        d = random.randint(0, 100)
    assert a == c
    assert b == d
    print(f"   ✓ Python random is deterministic: {a:.6f}")
    print(f"   ✓ Python randint is deterministic: {b}")

    print("\n3. Testing deterministic context with numpy:")
    with deterministic("PU_123", "corr-1") as seeds:
        arr1 = np.random.rand(3).tolist()
    with deterministic("PU_123", "corr-1") as seeds:
        arr2 = np.random.rand(3).tolist()
    assert arr1 == arr2
    print(f"   ✓ NumPy random is deterministic: {arr1}")

    print("\n4. Testing local RNG generator:")
    rng1 = create_deterministic_rng(42)
    v1 = rng1.random()
    rng2 = create_deterministic_rng(42)
    v2 = rng2.random()
    assert v1 == v2
    print(f"   ✓ Local RNG is deterministic: {v1:.6f}")

    print("\n5. Testing different correlation IDs produce different results:")
    with deterministic("PU_123", "corr-A"):
        val_a = random.random()
    with deterministic("PU_123", "corr-B"):
        val_b = random.random()
    assert val_a != val_b
    print("   ✓ Different correlation → different values")
    print(f"      corr-A: {val_a:.6f}")
    print(f"      corr-B: {val_b:.6f}")

    print("\n" + "="*60)
    print("Determinism doctest OK - All tests passed!")
    print("="*60)
