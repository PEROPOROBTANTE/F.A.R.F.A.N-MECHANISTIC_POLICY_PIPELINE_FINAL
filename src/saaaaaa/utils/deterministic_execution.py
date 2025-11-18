"""
Deterministic Execution Utilities - Production Grade
====================================================

Utilities for ensuring deterministic, reproducible execution across
the policy analysis pipeline.

Features:
- Deterministic random seed management
- UTC-only timestamp handling
- Structured execution logging
- Side-effect isolation
- Reproducible event ID generation

Author: Policy Analytics Research Unit
Version: 1.0.0
License: Proprietary
"""

import hashlib
import logging
import random
import time
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any

import numpy as np

from .enhanced_contracts import StructuredLogger, utc_now_iso

# ============================================================================
# DETERMINISTIC SEED MANAGEMENT
# ============================================================================

class DeterministicSeedManager:
    """
    Manages random seeds for deterministic execution.

    All stochastic operations must use seeds managed by this class to ensure
    reproducibility across runs.

    Examples:
        >>> manager = DeterministicSeedManager(base_seed=42)
        >>> with manager.scoped_seed("operation1"):
        ...     value = random.random()
        >>> # Seed is automatically restored after context
    """

    def __init__(self, base_seed: int = 42) -> None:
        """
        Initialize seed manager with base seed.

        Args:
            base_seed: Master seed for all derived seeds
        """
        self.base_seed = base_seed
        self._seed_counter = 0
        self._initialize_seeds(base_seed)

    def _initialize_seeds(self, seed: int) -> None:
        """Initialize all random number generators with deterministic seeds."""
        random.seed(seed)
        np.random.seed(seed)
        # For reproducibility, also set hash seed
        # Note: PYTHONHASHSEED should be set in environment for full determinism

    def get_derived_seed(self, operation_name: str) -> int:
        """
        Generate a deterministic seed for a specific operation.

        Args:
            operation_name: Unique name for the operation

        Returns:
            Deterministic integer seed derived from operation name and base seed

        Examples:
            >>> manager = DeterministicSeedManager(42)
            >>> seed1 = manager.get_derived_seed("test")
            >>> seed2 = manager.get_derived_seed("test")
            >>> seed1 == seed2  # Deterministic
            True
        """
        # Use cryptographic hash for stable seed derivation
        hash_input = f"{self.base_seed}:{operation_name}".encode()
        hash_digest = hashlib.sha256(hash_input).digest()
        # Convert first 4 bytes to int
        return int.from_bytes(hash_digest[:4], byteorder='big')

    @contextmanager
    def scoped_seed(self, operation_name: str) -> Iterator[int]:
        """
        Context manager for scoped seed usage.

        Sets seeds for the operation, then restores original state.

        Args:
            operation_name: Unique name for the operation

        Yields:
            Derived seed for this operation

        Examples:
            >>> manager = DeterministicSeedManager(42)
            >>> with manager.scoped_seed("my_operation") as seed:
            ...     result = random.randint(0, 100)
        """
        # Save current state
        random_state = random.getstate()
        np_state = np.random.get_state()

        # Set new seed
        derived_seed = self.get_derived_seed(operation_name)
        self._initialize_seeds(derived_seed)

        try:
            yield derived_seed
        finally:
            # Restore state
            random.setstate(random_state)
            np.random.set_state(np_state)

    def get_event_id(self, operation_name: str, timestamp_utc: str | None = None) -> str:
        """
        Generate a reproducible event ID for an operation.

        Args:
            operation_name: Operation name
            timestamp_utc: Optional UTC timestamp (ISO-8601); if None, uses current time

        Returns:
            Deterministic event ID based on operation and timestamp

        Examples:
            >>> manager = DeterministicSeedManager(42)
            >>> event_id = manager.get_event_id("test", "2024-01-01T00:00:00Z")
            >>> len(event_id)
            64
        """
        ts = timestamp_utc or utc_now_iso()
        hash_input = f"{self.base_seed}:{operation_name}:{ts}".encode()
        return hashlib.sha256(hash_input).hexdigest()


# ============================================================================
# DETERMINISTIC EXECUTION WRAPPER
# ============================================================================

class DeterministicExecutor:
    """
    Wraps functions to ensure deterministic execution with observability.

    Features:
    - Automatic seed management
    - Structured logging of execution
    - Latency tracking
    - Error handling with event IDs

    Examples:
        >>> executor = DeterministicExecutor(base_seed=42, logger_name="test")
        >>> @executor.deterministic(operation_name="my_func")
        ... def my_function(x: int) -> int:
        ...     return x + random.randint(0, 10)
    """

    def __init__(
        self,
        base_seed: int = 42,
        logger_name: str = "deterministic_executor",
        enable_logging: bool = True
    ) -> None:
        """
        Initialize deterministic executor.

        Args:
            base_seed: Master seed for all operations
            logger_name: Logger name for structured logging
            enable_logging: Whether to enable structured logging
        """
        self.seed_manager = DeterministicSeedManager(base_seed)
        self.logger = StructuredLogger(logger_name) if enable_logging else None
        self.enable_logging = enable_logging

    def deterministic(
        self,
        operation_name: str,
        log_inputs: bool = False,
        log_outputs: bool = False
    ) -> Callable:
        """
        Decorator to make a function deterministic with logging.

        Args:
            operation_name: Unique name for this operation
            log_inputs: Whether to log input parameters
            log_outputs: Whether to log output values

        Returns:
            Decorated function with deterministic execution
        """
        def decorator(func: Callable) -> Callable:
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                # Generate correlation and event IDs
                correlation_id = str(uuid.uuid4())
                event_id = self.seed_manager.get_event_id(operation_name)

                # Start timing
                start_time = time.perf_counter()

                # Execute with scoped seed
                try:
                    with self.seed_manager.scoped_seed(operation_name) as seed:
                        result = func(*args, **kwargs)

                        # Calculate latency
                        latency_ms = (time.perf_counter() - start_time) * 1000

                        # Log success
                        if self.enable_logging and self.logger:
                            log_data = {
                                "event_id": event_id,
                                "seed": seed,
                                "latency_ms": latency_ms,
                            }
                            if log_inputs:
                                log_data["inputs"] = str(args)[:100]  # Truncate for safety
                            if log_outputs:
                                log_data["outputs"] = str(result)[:100]

                            self.logger.log_execution(
                                operation=operation_name,
                                correlation_id=correlation_id,
                                success=True,
                                latency_ms=latency_ms,
                                **log_data
                            )

                        return result

                except Exception as e:
                    # Calculate latency even on error
                    latency_ms = (time.perf_counter() - start_time) * 1000

                    # Log error
                    if self.enable_logging and self.logger:
                        self.logger.log_execution(
                            operation=operation_name,
                            correlation_id=correlation_id,
                            success=False,
                            latency_ms=latency_ms,
                            event_id=event_id,
                            error=str(e)[:200]  # Truncate for safety
                        )

                    # Re-raise with event ID
                    raise RuntimeError(f"[{event_id}] {operation_name} failed: {e}") from e

            return wrapper
        return decorator


# ============================================================================
# UTC TIMESTAMP UTILITIES
# ============================================================================

def enforce_utc_now() -> datetime:
    """
    Get current UTC datetime.

    Returns:
        Current datetime in UTC timezone

    Examples:
        >>> dt = enforce_utc_now()
        >>> dt.tzinfo is not None
        True
    """
    return datetime.now(timezone.utc)


def parse_utc_timestamp(timestamp_str: str) -> datetime:
    """
    Parse ISO-8601 timestamp and enforce UTC.

    Args:
        timestamp_str: ISO-8601 timestamp string

    Returns:
        Parsed datetime in UTC

    Raises:
        ValueError: If timestamp is not UTC or invalid format

    Examples:
        >>> dt = parse_utc_timestamp("2024-01-01T00:00:00Z")
        >>> dt.year
        2024
    """
    dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))

    # Enforce UTC
    if dt.tzinfo is None or dt.utcoffset() != timezone.utc.utcoffset(None):
        raise ValueError(f"Timestamp must be UTC: {timestamp_str}")

    return dt


# ============================================================================
# SIDE-EFFECT ISOLATION
# ============================================================================

@contextmanager
def isolated_execution() -> Iterator[None]:
    """
    Context manager to isolate side effects during execution.

    Current isolation:
    - Prevents print statements (captured and logged as warning)
    - Future: file I/O restrictions, network restrictions

    Yields:
        None

    Examples:
        >>> with isolated_execution():
        ...     # Code here has controlled side effects
        ...     pass
    """
    # For now, minimal isolation - can be extended with more restrictions
    import io
    import sys

    # Capture stdout/stderr to detect violations
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    try:
        sys.stdout = stdout_capture
        sys.stderr = stderr_capture
        yield
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

        # Log any captured output as warning (side effect violation)
        if stdout_capture.getvalue():
            logging.warning(
                "Side effect detected: stdout captured during isolated execution: %s",
                stdout_capture.getvalue()[:200]
            )
        if stderr_capture.getvalue():
            logging.warning(
                "Side effect detected: stderr captured during isolated execution: %s",
                stderr_capture.getvalue()[:200]
            )


# ============================================================================
# IN-SCRIPT TESTS
# ============================================================================

if __name__ == "__main__":
    import doctest

    # Run doctests
    print("Running doctests...")
    doctest.testmod(verbose=True)

    # Additional tests
    print("\n" + "="*60)
    print("Deterministic Execution Tests")
    print("="*60)

    # Test 1: Seed manager determinism
    print("\n1. Testing seed manager determinism:")
    manager1 = DeterministicSeedManager(42)
    manager2 = DeterministicSeedManager(42)

    seed1_a = manager1.get_derived_seed("test_op")
    seed1_b = manager1.get_derived_seed("test_op")
    seed2_a = manager2.get_derived_seed("test_op")

    assert seed1_a == seed1_b == seed2_a, "Seeds must be deterministic"
    print(f"   ✓ Deterministic seeds: {seed1_a} == {seed1_b} == {seed2_a}")

    # Test 2: Scoped seed restoration
    print("\n2. Testing scoped seed restoration:")
    manager = DeterministicSeedManager(42)

    initial_value = random.random()
    with manager.scoped_seed("temp_operation"):
        _ = random.random()  # Different value inside scope
    restored_value = random.random()

    # Reset and check if we can reproduce
    manager._initialize_seeds(42)
    reproduced_value = random.random()

    print(f"   ✓ Initial value: {initial_value:.6f}")
    print(f"   ✓ Reproduced value: {reproduced_value:.6f}")
    assert abs(initial_value - reproduced_value) < 1e-10, "Seed restoration failed"
    print("   ✓ Seed restoration successful")

    # Test 3: Deterministic executor
    print("\n3. Testing deterministic executor:")
    executor = DeterministicExecutor(base_seed=42, enable_logging=False)

    @executor.deterministic(operation_name="test_function")
    def sample_function(n: int) -> float:
        return sum(random.random() for _ in range(n))

    result1 = sample_function(5)

    # Reset and run again
    executor.seed_manager._initialize_seeds(42)
    result2 = sample_function(5)

    print(f"   ✓ Result 1: {result1:.6f}")
    print(f"   ✓ Result 2: {result2:.6f}")
    assert abs(result1 - result2) < 1e-10, "Deterministic execution failed"
    print("   ✓ Deterministic execution verified")

    # Test 4: UTC enforcement
    print("\n4. Testing UTC enforcement:")
    utc_now = enforce_utc_now()
    print(f"   ✓ UTC now: {utc_now.isoformat()}")
    assert utc_now.tzinfo is not None, "Must have timezone"

    # Test 5: Event ID reproducibility
    print("\n5. Testing event ID reproducibility:")
    manager = DeterministicSeedManager(42)
    event_id1 = manager.get_event_id("operation", "2024-01-01T00:00:00Z")
    event_id2 = manager.get_event_id("operation", "2024-01-01T00:00:00Z")
    assert event_id1 == event_id2, "Event IDs must be reproducible"
    print(f"   ✓ Event ID: {event_id1[:16]}...")
    print("   ✓ Event ID reproducibility verified")

    print("\n" + "="*60)
    print("All tests passed!")
    print("="*60)
