"""Tests for async timeout handling with PhaseTimeoutError."""

import asyncio
import pytest

# Add src to path for imports
import sys
from pathlib import Path

from saaaaaa.core.orchestrator.core import (
    PhaseTimeoutError,
    execute_phase_with_timeout,
)


@pytest.mark.asyncio
async def test_phase_timeout_raises_custom_error():
    """Test that PhaseTimeoutError is raised on timeout."""
    async def slow_phase():
        await asyncio.sleep(5)
        return "done"

    with pytest.raises(PhaseTimeoutError) as exc_info:
        await execute_phase_with_timeout(
            phase_id=1,
            phase_name="Test Phase",
            coro=slow_phase,
            timeout_s=0.1
        )

    assert exc_info.value.phase_id == 1
    assert exc_info.value.timeout_s == 0.1
    assert "Test Phase" in str(exc_info.value)


@pytest.mark.asyncio
async def test_phase_timeout_error_attributes():
    """Test PhaseTimeoutError has correct attributes."""
    async def slow_phase():
        await asyncio.sleep(1)

    with pytest.raises(PhaseTimeoutError) as exc_info:
        await execute_phase_with_timeout(
            phase_id=5,
            phase_name="Slow Phase",
            coro=slow_phase,
            timeout_s=0.05
        )

    error = exc_info.value
    assert error.phase_id == 5
    assert error.phase_name == "Slow Phase"
    assert error.timeout_s == 0.05


@pytest.mark.asyncio
async def test_phase_completes_within_timeout():
    """Test that phase completes successfully within timeout."""
    async def fast_phase(value: int) -> int:
        await asyncio.sleep(0.01)
        return value * 2

    result = await execute_phase_with_timeout(
        phase_id=2,
        phase_name="Fast Phase",
        coro=fast_phase,
        args=(42,),
        timeout_s=1.0
    )

    assert result == 84


@pytest.mark.asyncio
async def test_phase_cancellation_propagates():
    """Test that cancellation is properly propagated."""
    async def cancellable_phase():
        await asyncio.sleep(10)

    task = asyncio.create_task(
        execute_phase_with_timeout(
            phase_id=1,
            phase_name="Test",
            coro=cancellable_phase,
            timeout_s=100
        )
    )

    await asyncio.sleep(0.01)
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task


@pytest.mark.asyncio
async def test_phase_exception_propagates():
    """Test that exceptions from phase are properly propagated."""
    async def failing_phase():
        await asyncio.sleep(0.01)
        raise ValueError("Test error")

    with pytest.raises(ValueError, match="Test error"):
        await execute_phase_with_timeout(
            phase_id=3,
            phase_name="Failing Phase",
            coro=failing_phase,
            timeout_s=1.0
        )


@pytest.mark.asyncio
async def test_phase_with_kwargs():
    """Test phase execution with keyword arguments."""
    async def phase_with_kwargs(a: int, b: int = 10) -> int:
        await asyncio.sleep(0.01)
        return a + b

    result = await execute_phase_with_timeout(
        phase_id=4,
        phase_name="Kwargs Phase",
        coro=phase_with_kwargs,
        args=(5,),
        b=15,
        timeout_s=1.0
    )

    assert result == 20


@pytest.mark.asyncio
async def test_phase_timeout_default_value():
    """Test that default timeout is used when not specified."""
    async def quick_phase():
        return "success"

    result = await execute_phase_with_timeout(
        phase_id=1,
        phase_name="Quick Phase",
        coro=quick_phase,
        # timeout_s defaults to 300
    )

    assert result == "success"


@pytest.mark.asyncio
async def test_multiple_phases_sequentially():
    """Test multiple phases can be executed sequentially."""
    async def phase1():
        await asyncio.sleep(0.01)
        return "phase1"

    async def phase2():
        await asyncio.sleep(0.01)
        return "phase2"

    result1 = await execute_phase_with_timeout(
        phase_id=1,
        phase_name="Phase 1",
        coro=phase1,
        timeout_s=1.0
    )

    result2 = await execute_phase_with_timeout(
        phase_id=2,
        phase_name="Phase 2",
        coro=phase2,
        timeout_s=1.0
    )

    assert result1 == "phase1"
    assert result2 == "phase2"


@pytest.mark.asyncio
async def test_phase_timeout_with_none_return():
    """Test phase that returns None."""
    async def none_phase():
        await asyncio.sleep(0.01)
        return None

    result = await execute_phase_with_timeout(
        phase_id=1,
        phase_name="None Phase",
        coro=none_phase,
        timeout_s=1.0
    )

    assert result is None
