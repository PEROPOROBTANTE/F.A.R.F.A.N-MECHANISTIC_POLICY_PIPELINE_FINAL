"""Test environment-configurable expected counts in core.py."""
import os
import pytest



# Mark all tests in this module as outdated
pytestmark = pytest.mark.skip(reason="Count validation moved to structure_verification")

def test_expected_counts_default():
    """Test that default expected counts are loaded correctly."""
    # Import after setting env vars
    from saaaaaa.core.orchestrator.core import EXPECTED_QUESTION_COUNT, EXPECTED_METHOD_COUNT
    
    # Default values should be loaded
    assert EXPECTED_QUESTION_COUNT == 305
    assert EXPECTED_METHOD_COUNT == 416


def test_expected_counts_custom():
    """Test that custom expected counts can be set via environment."""
    # Set custom env vars
    os.environ["EXPECTED_QUESTION_COUNT"] = "500"
    os.environ["EXPECTED_METHOD_COUNT"] = "600"
    
    try:
        # Re-import to pick up new values
        import importlib
        from saaaaaa.core.orchestrator import core
        importlib.reload(core)
        
        assert core.EXPECTED_QUESTION_COUNT == 500
        assert core.EXPECTED_METHOD_COUNT == 600
    finally:
        # Clean up
        os.environ.pop("EXPECTED_QUESTION_COUNT", None)
        os.environ.pop("EXPECTED_METHOD_COUNT", None)
        
        # Reload again to restore defaults
        importlib.reload(core)


def test_phase_timeout_default():
    """Test that default phase timeout is loaded correctly."""
    from saaaaaa.core.orchestrator.core import PHASE_TIMEOUT_DEFAULT
    
    # Default value should be 300 seconds
    assert PHASE_TIMEOUT_DEFAULT == 300


def test_phase_timeout_custom():
    """Test that custom phase timeout can be set via environment."""
    os.environ["PHASE_TIMEOUT_SECONDS"] = "600"
    
    try:
        import importlib
        from saaaaaa.core.orchestrator import core
        importlib.reload(core)
        
        assert core.PHASE_TIMEOUT_DEFAULT == 600
    finally:
        os.environ.pop("PHASE_TIMEOUT_SECONDS", None)
        importlib.reload(core)
