"""Comprehensive tests for MethodSequenceValidatingMixin."""

import pytest
from hypothesis import given, strategies as st

# Add src to path for imports
import sys
from pathlib import Path

from saaaaaa.core.orchestrator.executors import MethodSequenceValidatingMixin


class MockExecutor:
    """Mock executor for testing."""
    def __init__(self, instances=None):
        self.instances = instances or {}


class TestExecutorValidation(MethodSequenceValidatingMixin):
    """Test executor class."""
    def __init__(self, executor, method_sequence=None):
        self.executor = executor
        self._method_sequence = method_sequence or []
    
    def _get_method_sequence(self):
        return self._method_sequence


def test_validates_existing_methods():
    """Should pass for valid method sequences."""
    test_class = type('TestClass', (), {
        'method1': lambda self: None,
        'method2': lambda self: None,
    })()
    
    executor = MockExecutor(instances={
        'TestClass': test_class
    })
    
    test_executor = TestExecutorValidation(
        executor=executor,
        method_sequence=[
            ('TestClass', 'method1'),
            ('TestClass', 'method2'),
        ]
    )
    
    # Should not raise
    test_executor._validate_method_sequences()


def test_fails_on_missing_class():
    """Should fail if class not in registry."""
    executor = MockExecutor(instances={})
    
    test_executor = TestExecutorValidation(
        executor=executor,
        method_sequence=[('MissingClass', 'method')]
    )
    
    with pytest.raises(ValueError, match="MissingClass not in executor registry"):
        test_executor._validate_method_sequences()


def test_fails_on_missing_method():
    """Should fail if method doesn't exist."""
    test_class = type('TestClass', (), {})()
    
    executor = MockExecutor(instances={
        'TestClass': test_class
    })
    
    test_executor = TestExecutorValidation(
        executor=executor,
        method_sequence=[('TestClass', 'missing_method')]
    )
    
    with pytest.raises(ValueError, match="has no method missing_method"):
        test_executor._validate_method_sequences()


def test_fails_on_non_callable():
    """Should fail if attribute is not callable."""
    test_class = type('TestClass', (), {
        'not_a_method': 'string_value'
    })()
    
    executor = MockExecutor(instances={
        'TestClass': test_class
    })
    
    test_executor = TestExecutorValidation(
        executor=executor,
        method_sequence=[('TestClass', 'not_a_method')]
    )
    
    with pytest.raises(ValueError, match="is not callable"):
        test_executor._validate_method_sequences()


def test_empty_sequence_passes():
    """Should pass with empty method sequence."""
    executor = MockExecutor(instances={})
    
    test_executor = TestExecutorValidation(
        executor=executor,
        method_sequence=[]
    )
    
    # Should not raise
    test_executor._validate_method_sequences()


def test_multiple_classes():
    """Should validate methods across multiple classes."""
    class1 = type('Class1', (), {'method1': lambda self: None})()
    class2 = type('Class2', (), {'method2': lambda self: None})()
    
    executor = MockExecutor(instances={
        'Class1': class1,
        'Class2': class2,
    })
    
    test_executor = TestExecutorValidation(
        executor=executor,
        method_sequence=[
            ('Class1', 'method1'),
            ('Class2', 'method2'),
        ]
    )
    
    # Should not raise
    test_executor._validate_method_sequences()


def test_same_class_multiple_methods():
    """Should validate multiple methods from same class."""
    test_class = type('TestClass', (), {
        'method1': lambda self: None,
        'method2': lambda self: None,
        'method3': lambda self: None,
    })()
    
    executor = MockExecutor(instances={
        'TestClass': test_class
    })
    
    test_executor = TestExecutorValidation(
        executor=executor,
        method_sequence=[
            ('TestClass', 'method1'),
            ('TestClass', 'method2'),
            ('TestClass', 'method3'),
        ]
    )
    
    # Should not raise
    test_executor._validate_method_sequences()


@given(st.lists(
    st.tuples(
        st.text(min_size=1, max_size=20, alphabet=st.characters(
            blacklist_categories=('Cs',), blacklist_characters='\x00'
        )),
        st.text(min_size=1, max_size=20, alphabet=st.characters(
            blacklist_categories=('Cs',), blacklist_characters='\x00'
        )),
    ),
    min_size=0,
    max_size=20
))
def test_validation_handles_arbitrary_sequences(method_sequence):
    """Property test: validation should never crash."""
    executor = MockExecutor(instances={})
    
    test_executor = TestExecutorValidation(
        executor=executor,
        method_sequence=method_sequence
    )
    
    # Should either pass or raise ValueError, never crash
    try:
        test_executor._validate_method_sequences()
    except ValueError:
        pass  # Expected for invalid sequences


def test_validates_real_method():
    """Should validate actual callable methods."""
    class RealClass:
        def real_method(self):
            return "works"
        
        def another_method(self, arg):
            return arg * 2
    
    instance = RealClass()
    
    executor = MockExecutor(instances={
        'RealClass': instance
    })
    
    test_executor = TestExecutorValidation(
        executor=executor,
        method_sequence=[
            ('RealClass', 'real_method'),
            ('RealClass', 'another_method'),
        ]
    )
    
    # Should not raise
    test_executor._validate_method_sequences()


def test_fails_on_property():
    """Should fail if attribute is a property, not a method."""
    class TestClass:
        @property
        def my_property(self):
            return "value"
    
    instance = TestClass()
    
    executor = MockExecutor(instances={
        'TestClass': instance
    })
    
    test_executor = TestExecutorValidation(
        executor=executor,
        method_sequence=[('TestClass', 'my_property')]
    )
    
    # Properties are not callable, so this should fail
    with pytest.raises(ValueError, match="is not callable"):
        test_executor._validate_method_sequences()


def test_validates_inherited_methods():
    """Should validate inherited methods."""
    class BaseClass:
        def base_method(self):
            return "base"
    
    class DerivedClass(BaseClass):
        def derived_method(self):
            return "derived"
    
    instance = DerivedClass()
    
    executor = MockExecutor(instances={
        'DerivedClass': instance
    })
    
    test_executor = TestExecutorValidation(
        executor=executor,
        method_sequence=[
            ('DerivedClass', 'base_method'),
            ('DerivedClass', 'derived_method'),
        ]
    )
    
    # Should not raise
    test_executor._validate_method_sequences()
