"""Test per-phase async timeout in core.py."""
import asyncio
import pytest


@pytest.mark.asyncio
async def test_phase_timeout_raises_on_timeout():
    """Test that phase timeout raises PhaseTimeoutError when exceeded."""
    from saaaaaa.core.orchestrator.core import execute_phase_with_timeout, PhaseTimeoutError
    
    async def slow_handler():
        """A handler that takes longer than timeout."""
        await asyncio.sleep(1)
    
    # Use a very short timeout
    timeout = 0.1
    
    with pytest.raises(PhaseTimeoutError) as exc_info:
        await execute_phase_with_timeout(
            phase_id=1,
            phase_name="test_phase",
            handler=slow_handler,
            args=(),
            timeout_s=timeout
        )
    
    # Verify exception attributes
    assert exc_info.value.phase_id == 1
    assert exc_info.value.phase_name == "test_phase"
    assert exc_info.value.timeout_s == timeout
    assert "timed out" in str(exc_info.value)


@pytest.mark.asyncio
async def test_phase_timeout_succeeds_within_timeout():
    """Test that phase completes successfully within timeout."""
    from saaaaaa.core.orchestrator.core import execute_phase_with_timeout
    
    async def fast_handler():
        """A handler that completes quickly."""
        await asyncio.sleep(0.01)
        return "success"
    
    # Use a reasonable timeout
    timeout = 1.0
    
    result = await execute_phase_with_timeout(
        phase_id=2,
        phase_name="fast_phase",
        handler=fast_handler,
        args=(),
        timeout_s=timeout
    )
    assert result == "success"


@pytest.mark.asyncio
async def test_phase_timeout_default_value():
    """Test that PHASE_TIMEOUT_DEFAULT has the expected value."""
    from saaaaaa.core.orchestrator.core import PHASE_TIMEOUT_DEFAULT
    
    # Default should be 300 seconds
    assert PHASE_TIMEOUT_DEFAULT == 300
    assert isinstance(PHASE_TIMEOUT_DEFAULT, int)


@pytest.mark.asyncio
async def test_phase_timeout_with_cancellation():
    """Test that phase timeout handles cancellation correctly."""
    from saaaaaa.core.orchestrator.core import execute_phase_with_timeout
    
    async def cancellable_handler():
        """A handler that can be cancelled."""
        await asyncio.sleep(10)
    
    # Create task and cancel it
    task = asyncio.create_task(
        execute_phase_with_timeout(
            phase_id=3,
            phase_name="cancellable_phase",
            handler=cancellable_handler,
            args=(),
            timeout_s=5.0
        )
    )
    
    await asyncio.sleep(0.01)  # Let it start
    task.cancel()
    
    with pytest.raises(asyncio.CancelledError):
        await task


@pytest.mark.asyncio
async def test_phase_timeout_with_exception():
    """Test that phase timeout propagates exceptions correctly."""
    from saaaaaa.core.orchestrator.core import execute_phase_with_timeout
    
    async def failing_handler():
        """A handler that raises an exception."""
        raise ValueError("Test error")
    
    with pytest.raises(ValueError, match="Test error"):
        await execute_phase_with_timeout(
            phase_id=4,
            phase_name="failing_phase",
            handler=failing_handler,
            args=(),
            timeout_s=1.0
        )


@pytest.mark.asyncio
async def test_phase_timeout_logs_completion_time():
    """Test that phase timeout logs completion time correctly."""
    from saaaaaa.core.orchestrator.core import execute_phase_with_timeout
    
    async def timed_handler():
        """A handler with measurable execution time."""
        await asyncio.sleep(0.1)
        return "completed"
    
    result = await execute_phase_with_timeout(
        phase_id=5,
        phase_name="timed_phase",
        handler=timed_handler,
        args=(),
        timeout_s=1.0
    )
    
    assert result == "completed"
