"""Stress tests for circuit breaker under high concurrency."""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock, patch
import pytest

# Add src to path for imports
import sys
from pathlib import Path

from saaaaaa.core.orchestrator.signals import (
    SignalClient,
    SignalPack,
    CircuitBreakerError,
    SignalUnavailableError,
)


def test_circuit_breaker_basic_state_tracking():
    """Test that circuit breaker tracks state changes."""
    client = SignalClient(
        base_url="memory://",
        circuit_breaker_threshold=3,
    )
    
    # Initially no state changes
    assert len(client.get_state_history()) == 0
    assert client.get_metrics()["circuit_open"] is False
    assert client.get_metrics()["failure_count"] == 0
    
    # Simulate failures by calling _record_failure
    client._record_failure()
    assert client.get_metrics()["failure_count"] == 1
    assert client.get_metrics()["circuit_open"] is False
    
    client._record_failure()
    assert client.get_metrics()["failure_count"] == 2
    assert client.get_metrics()["circuit_open"] is False
    
    # Third failure should open circuit
    client._record_failure()
    assert client.get_metrics()["failure_count"] == 3
    assert client.get_metrics()["circuit_open"] is True
    
    # Should have one state change (closed -> open)
    history = client.get_state_history()
    assert len(history) == 1
    assert history[0]["from_open"] is False
    assert history[0]["to_open"] is True
    assert history[0]["failures"] == 3


def test_circuit_breaker_state_history_trimming():
    """Test that state history is trimmed to max_history."""
    client = SignalClient(
        base_url="memory://",
        circuit_breaker_threshold=1,
    )
    
    # Force many state changes by opening/closing circuit
    for i in range(150):
        # Open circuit
        client._record_failure()
        
        # Manually close it to create more state changes
        client._circuit_open = False
        client._failure_count = 0
    
    # Should be trimmed to max_history (100)
    history = client.get_state_history()
    assert len(history) <= 100


def test_circuit_breaker_metrics_after_state_changes():
    """Test that metrics reflect state changes correctly."""
    client = SignalClient(
        base_url="memory://",
        circuit_breaker_threshold=2,
    )
    
    # Record failures
    client._record_failure()
    metrics1 = client.get_metrics()
    assert metrics1["failure_count"] == 1
    assert metrics1["state_change_count"] == 0
    
    client._record_failure()
    metrics2 = client.get_metrics()
    assert metrics2["failure_count"] == 2
    assert metrics2["state_change_count"] == 1  # Circuit opened
    assert metrics2["circuit_open"] is True
    assert metrics2["last_failure_time"] is not None


@pytest.mark.asyncio
async def test_circuit_breaker_high_concurrency():
    """Stress test: Multiple concurrent failure recordings."""
    client = SignalClient(
        base_url="memory://",
        circuit_breaker_threshold=100,
    )
    
    async def record_failures(count: int):
        """Record multiple failures sequentially."""
        for _ in range(count):
            client._record_failure()
            await asyncio.sleep(0.001)  # Simulate work
    
    # Run 10 concurrent tasks, each recording 10 failures
    tasks = [asyncio.create_task(record_failures(10)) for _ in range(10)]
    await asyncio.gather(*tasks)
    
    # Should have exactly 100 failures
    assert client.get_metrics()["failure_count"] == 100
    assert client.get_metrics()["circuit_open"] is True
    
    # Should have one state change (when threshold reached)
    history = client.get_state_history()
    assert len(history) == 1
    assert history[0]["to_open"] is True


@pytest.mark.asyncio
async def test_circuit_breaker_race_condition():
    """Test for race condition when crossing threshold."""
    client = SignalClient(
        base_url="memory://",
        circuit_breaker_threshold=10,
    )
    
    async def increment_failures():
        """Increment failure count."""
        for _ in range(5):
            client._record_failure()
            await asyncio.sleep(0.001)
    
    # Start multiple tasks simultaneously
    tasks = [asyncio.create_task(increment_failures()) for _ in range(3)]
    await asyncio.gather(*tasks)
    
    # Should be exactly 15 failures (3 * 5)
    assert client.get_metrics()["failure_count"] == 15
    assert client.get_metrics()["circuit_open"] is True


def test_circuit_breaker_thread_safety():
    """Test thread safety with ThreadPoolExecutor."""
    client = SignalClient(
        base_url="memory://",
        circuit_breaker_threshold=200,
    )
    
    def record_failure():
        """Record a single failure."""
        client._record_failure()
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(record_failure) for _ in range(100)]
        for future in futures:
            future.result()
    
    # Should have exactly 100 failures
    assert client.get_metrics()["failure_count"] == 100
    assert client.get_metrics()["circuit_open"] is False  # Below threshold


def test_circuit_breaker_cooldown_and_reset():
    """Test circuit breaker cooldown and reset behavior."""
    client = SignalClient(
        base_url="memory://",
        circuit_breaker_threshold=2,
        circuit_breaker_cooldown_s=0.1,  # Short cooldown for testing
    )
    
    # Open circuit
    client._record_failure()
    client._record_failure()
    assert client.get_metrics()["circuit_open"] is True
    
    initial_changes = len(client.get_state_history())
    
    # Wait for cooldown
    time.sleep(0.15)
    
    # Simulate successful request by resetting
    old_open = client._circuit_open
    client._circuit_open = False
    client._failure_count = 0
    
    # Manually record state change (simulating what _fetch_from_http does)
    client._state_changes.append({
        'timestamp': time.time(),
        'from_open': old_open,
        'to_open': False,
        'failures': 0,
    })
    
    # Should have one more state change
    assert len(client.get_state_history()) == initial_changes + 1
    assert client.get_metrics()["circuit_open"] is False
    assert client.get_metrics()["failure_count"] == 0


@pytest.mark.asyncio
async def test_circuit_breaker_under_sustained_load():
    """Test circuit breaker behavior under sustained concurrent load."""
    client = SignalClient(
        base_url="memory://",
        circuit_breaker_threshold=50,
    )
    
    async def sustained_failures(duration_s: float):
        """Record failures for a duration."""
        end_time = time.time() + duration_s
        count = 0
        while time.time() < end_time:
            client._record_failure()
            count += 1
            await asyncio.sleep(0.01)
        return count
    
    # Run for 0.5 seconds with 5 concurrent workers
    tasks = [asyncio.create_task(sustained_failures(0.5)) for _ in range(5)]
    results = await asyncio.gather(*tasks)
    
    total_failures = sum(results)
    assert client.get_metrics()["failure_count"] == total_failures
    assert client.get_metrics()["circuit_open"] is True  # Should exceed threshold


def test_circuit_breaker_state_history_timestamps():
    """Test that state history includes proper timestamps."""
    client = SignalClient(
        base_url="memory://",
        circuit_breaker_threshold=2,
    )
    
    start_time = time.time()
    
    client._record_failure()
    client._record_failure()  # Opens circuit
    
    history = client.get_state_history()
    assert len(history) == 1
    
    change = history[0]
    assert "timestamp" in change
    assert "from_open" in change
    assert "to_open" in change
    assert "failures" in change
    
    # Timestamp should be recent
    assert change["timestamp"] >= start_time
    assert change["timestamp"] <= time.time()
    assert change["failures"] == 2


@pytest.mark.asyncio
async def test_circuit_breaker_many_state_changes():
    """Test multiple open/close cycles."""
    client = SignalClient(
        base_url="memory://",
        circuit_breaker_threshold=2,
        circuit_breaker_cooldown_s=0.05,
    )
    
    for cycle in range(5):
        # Open circuit
        client._record_failure()
        client._record_failure()
        assert client.get_metrics()["circuit_open"] is True
        
        # Wait for cooldown
        await asyncio.sleep(0.06)
        
        # Manually close (simulating successful request after cooldown)
        old_open = client._circuit_open
        client._circuit_open = False
        client._failure_count = 0
        client._state_changes.append({
            'timestamp': time.time(),
            'from_open': old_open,
            'to_open': False,
            'failures': 0,
        })
    
    # Should have 10 state changes (5 opens + 5 closes)
    history = client.get_state_history()
    assert len(history) == 10
    
    # Verify alternating pattern
    for i, change in enumerate(history):
        if i % 2 == 0:
            # Even indices should be open transitions
            assert change["from_open"] is False
            assert change["to_open"] is True
        else:
            # Odd indices should be close transitions
            assert change["from_open"] is True
            assert change["to_open"] is False


def test_circuit_breaker_state_after_many_failures():
    """Test circuit breaker state after many failures beyond threshold."""
    client = SignalClient(
        base_url="memory://",
        circuit_breaker_threshold=5,
    )
    
    # Record way more failures than threshold
    for _ in range(50):
        client._record_failure()
    
    # Should still only have one state change (when threshold was crossed)
    history = client.get_state_history()
    assert len(history) == 1
    assert history[0]["failures"] == 5  # Recorded when threshold was reached
    
    # But failure count should be 50
    assert client.get_metrics()["failure_count"] == 50
    assert client.get_metrics()["circuit_open"] is True
