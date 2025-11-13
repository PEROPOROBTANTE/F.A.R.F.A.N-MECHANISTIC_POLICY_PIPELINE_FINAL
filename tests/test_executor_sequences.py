"""Test executor method sequence validation in executors.py."""
import pytest


# Mark all tests in this module as outdated
pytestmark = pytest.mark.skip(reason="Old executor model, replaced by flux phases")

from saaaaaa.core.orchestrator.core import MethodExecutor
from saaaaaa.core.orchestrator.executors import MethodSequenceValidatingMixin


class MockExecutor:
    """Mock executor for testing."""
    
    def __init__(self):
        self.instances = {
            "TestClass": MockInstance()
        }


class MockInstance:
    """Mock instance with test methods."""
    
    def method_a(self):
        return "a"
    
    def method_b(self):
        return "b"
    
    # Not a method, just an attribute
    not_callable = "attribute"


class TestValidatingExecutor(MethodSequenceValidatingMixin):
    """Test executor with validation."""
    
    def __init__(self, method_executor):
        self.executor = method_executor
        self._method_sequence = []
    
    def _get_method_sequence(self):
        return self._method_sequence
    
    def set_sequence(self, sequence):
        self._method_sequence = sequence


def test_validate_valid_sequence():
    """Test that valid sequence passes validation."""
    mock_executor = MockExecutor()
    test_executor = TestValidatingExecutor(mock_executor)
    
    test_executor.set_sequence([
        ("TestClass", "method_a"),
        ("TestClass", "method_b"),
    ])
    
    # Should not raise
    test_executor._validate_method_sequences()


def test_validate_missing_class():
    """Test that validation fails when class is not registered."""
    mock_executor = MockExecutor()
    test_executor = TestValidatingExecutor(mock_executor)
    
    test_executor.set_sequence([
        ("MissingClass", "method_a"),
    ])
    
    with pytest.raises(ValueError, match="Class MissingClass not in executor registry"):
        test_executor._validate_method_sequences()


def test_validate_missing_method():
    """Test that validation fails when method doesn't exist."""
    mock_executor = MockExecutor()
    test_executor = TestValidatingExecutor(mock_executor)
    
    test_executor.set_sequence([
        ("TestClass", "missing_method"),
    ])
    
    with pytest.raises(ValueError, match="TestClass has no method missing_method"):
        test_executor._validate_method_sequences()


def test_validate_not_callable():
    """Test that validation fails when method is not callable."""
    mock_executor = MockExecutor()
    test_executor = TestValidatingExecutor(mock_executor)
    
    test_executor.set_sequence([
        ("TestClass", "not_callable"),
    ])
    
    with pytest.raises(ValueError, match="TestClass.not_callable is not callable"):
        test_executor._validate_method_sequences()


def test_validate_empty_sequence():
    """Test that empty sequence passes validation."""
    mock_executor = MockExecutor()
    test_executor = TestValidatingExecutor(mock_executor)
    
    test_executor.set_sequence([])
    
    # Should not raise
    test_executor._validate_method_sequences()


def test_d1q1_executor_validates_on_init():
    """Test that D1Q1_Executor validates its sequence on initialization."""
    # This test would require mocking all the actual classes
    # For now, we'll just test the mixin behavior
    # In practice, this would catch issues at executor construction time
    pass
