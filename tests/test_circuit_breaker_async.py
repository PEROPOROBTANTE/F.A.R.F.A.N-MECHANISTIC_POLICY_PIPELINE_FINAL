"""Test async circuit breaker safety in executors.py."""
import asyncio
import pytest


@pytest.mark.asyncio
async def test_circuit_breaker_increment_failures():
    """Test that circuit breaker increments failures safely."""
    from saaaaaa.core.orchestrator.executors import CircuitBreakerState
    
    cb = CircuitBreakerState()
    
    assert cb.failures == 0
    assert not await cb.is_open()
    
    await cb.increment_failures()
    assert cb.failures == 1
    assert not await cb.is_open()
    
    await cb.increment_failures()
    assert cb.failures == 2
    assert not await cb.is_open()
    
    await cb.increment_failures()
    assert cb.failures == 3
    assert await cb.is_open()


@pytest.mark.asyncio
async def test_circuit_breaker_concurrent_increments():
    """Test that circuit breaker handles concurrent increments correctly."""
    from saaaaaa.core.orchestrator.executors import CircuitBreakerState
    
    cb = CircuitBreakerState()
    
    # Run 10 concurrent increment operations
    tasks = [cb.increment_failures() for _ in range(10)]
    await asyncio.gather(*tasks)
    
    # Should have 10 failures
    assert cb.failures == 10
    assert await cb.is_open()


@pytest.mark.asyncio
async def test_circuit_breaker_reset():
    """Test that circuit breaker reset works correctly."""
    from saaaaaa.core.orchestrator.executors import CircuitBreakerState
    
    cb = CircuitBreakerState()
    
    # Increment to open circuit
    await cb.increment_failures()
    await cb.increment_failures()
    await cb.increment_failures()
    
    assert await cb.is_open()
    
    # Reset
    await cb.reset()
    
    assert cb.failures == 0
    assert not await cb.is_open()


@pytest.mark.asyncio
async def test_circuit_breaker_race_condition():
    """Test that circuit breaker is safe under race conditions."""
    from saaaaaa.core.orchestrator.executors import CircuitBreakerState
    
    cb = CircuitBreakerState()
    
    async def increment_multiple():
        for _ in range(100):
            await cb.increment_failures()
    
    # Run multiple tasks concurrently
    tasks = [increment_multiple() for _ in range(10)]
    await asyncio.gather(*tasks)
    
    # Should have exactly 1000 failures
    assert cb.failures == 1000
    assert await cb.is_open()
