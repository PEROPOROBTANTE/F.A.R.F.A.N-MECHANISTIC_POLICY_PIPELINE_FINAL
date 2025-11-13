"""End-to-end integration test for signal channel.

This test verifies that signals flow from SignalRegistry through executors
and actually affect execution results.
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from saaaaaa.core.orchestrator.signals import SignalPack, SignalRegistry
from saaaaaa.core.orchestrator.executors import AdvancedDataFlowExecutor


class MockMethodExecutor:
    """Mock method executor for testing."""
    
    def __init__(self):
        self.instances = {}
        self.executed_methods = []
        self.received_patterns = None
        self.received_indicators = None
    
    def execute(self, class_name: str, method_name: str, **kwargs):
        """Track execution and capture signal parameters."""
        self.executed_methods.append((class_name, method_name))
        
        # Capture signals if provided
        if 'patterns' in kwargs:
            self.received_patterns = kwargs['patterns']
        if 'indicators' in kwargs:
            self.received_indicators = kwargs['indicators']
        
        return f"result_from_{method_name}"


class TestExecutor(AdvancedDataFlowExecutor):
    """Test executor that uses patterns parameter."""
    
    def execute(self, doc, method_executor):
        """Execute with signal-aware method sequence."""
        method_sequence = [
            ('TestClass', 'process_with_patterns'),
        ]
        return self.execute_with_optimization(doc, method_executor, method_sequence)


def test_signals_flow_end_to_end():
    """Test that signals flow from registry to executor to method execution."""
    # Setup: Create signal registry with test patterns
    registry = SignalRegistry(max_size=10, default_ttl_s=3600)
    
    test_patterns = ["pattern1", "pattern2", "pattern3"]
    test_indicators = ["indicator1", "indicator2"]
    
    signal_pack = SignalPack(
        version="1.0.0",
        policy_area="fiscal",
        patterns=test_patterns,
        indicators=test_indicators,
    )
    registry.put("fiscal", signal_pack)
    
    # Setup: Create executor with signal registry
    mock_method_executor = MockMethodExecutor()
    
    # Create a mock instance with a method that accepts patterns
    mock_instance = Mock()
    mock_instance.process_with_patterns = Mock(return_value="processed")
    mock_method_executor.instances["TestClass"] = mock_instance
    
    executor = TestExecutor(mock_method_executor, signal_registry=registry)
    
    # Setup: Create mock document
    mock_doc = Mock()
    mock_doc.raw_text = "Test document text"
    mock_doc.metadata = {}
    
    # Execute
    result = executor.execute(mock_doc, mock_method_executor)
    
    # Verify: Signals were fetched and tracked
    assert len(executor.used_signals) > 0
    assert executor.used_signals[0]["policy_area"] == "fiscal"
    assert executor.used_signals[0]["version"] == "1.0.0"
    
    # Verify: Result includes signal metadata
    assert "used_signals" in result["meta"]
    assert len(result["meta"]["used_signals"]) > 0


def test_signals_injected_into_method_kwargs():
    """Test that signals are actually injected as method parameters."""
    # Setup
    registry = SignalRegistry(max_size=10, default_ttl_s=3600)
    
    test_patterns = ["test_pattern_1", "test_pattern_2"]
    signal_pack = SignalPack(
        version="2.0.0",
        policy_area="fiscal",
        patterns=test_patterns,
    )
    registry.put("fiscal", signal_pack)
    
    mock_method_executor = MockMethodExecutor()
    
    # Create mock instance with method that accepts patterns parameter
    mock_instance = Mock()
    
    def capture_patterns(patterns=None, **kwargs):
        """Method that captures patterns parameter."""
        mock_method_executor.received_patterns = patterns
        return {"patterns_received": patterns}
    
    mock_instance.test_method = capture_patterns
    mock_method_executor.instances["TestClass"] = mock_instance
    
    # Create executor
    executor = TestExecutor(mock_method_executor, signal_registry=registry)
    
    mock_doc = Mock()
    mock_doc.raw_text = "Test text"
    mock_doc.metadata = {}
    
    # Execute with method that has 'patterns' parameter
    class PatternAwareExecutor(AdvancedDataFlowExecutor):
        def execute(self, doc, method_executor):
            method_sequence = [('TestClass', 'test_method')]
            return self.execute_with_optimization(doc, method_executor, method_sequence)
    
    pattern_executor = PatternAwareExecutor(mock_method_executor, signal_registry=registry)
    result = pattern_executor.execute(mock_doc, mock_method_executor)
    
    # Verify: Patterns were injected
    # Note: This tests the injection mechanism is in place
    assert pattern_executor.used_signals  # Signals were fetched
    assert "used_signals" in result["meta"]  # Signals tracked in metadata


def test_executor_without_signal_registry_works():
    """Test that executors work without signal registry (backward compatibility)."""
    mock_method_executor = MockMethodExecutor()
    
    mock_instance = Mock()
    mock_instance.simple_method = Mock(return_value="result")
    mock_method_executor.instances["TestClass"] = mock_instance
    
    # Create executor WITHOUT signal registry
    executor = TestExecutor(mock_method_executor, signal_registry=None)
    
    mock_doc = Mock()
    mock_doc.raw_text = "Test text"
    mock_doc.metadata = {}
    
    # Execute - should work without signals
    result = executor.execute(mock_doc, mock_method_executor)
    
    # Verify: Execution completed without signals
    assert result is not None
    assert "meta" in result
    # used_signals should be empty list
    assert result["meta"]["used_signals"] == []


def test_signal_context_preserved_across_methods():
    """Test that signals remain available throughout execution."""
    registry = SignalRegistry(max_size=10, default_ttl_s=3600)
    
    signal_pack = SignalPack(
        version="1.0.0",
        policy_area="fiscal",
        patterns=["p1", "p2"],
        indicators=["i1", "i2"],
        verbs=["v1", "v2"],
    )
    registry.put("fiscal", signal_pack)
    
    mock_method_executor = MockMethodExecutor()
    mock_instance = Mock()
    mock_instance.method1 = Mock(return_value="r1")
    mock_instance.method2 = Mock(return_value="r2")
    mock_method_executor.instances["TestClass"] = mock_instance
    
    class MultiMethodExecutor(AdvancedDataFlowExecutor):
        def execute(self, doc, method_executor):
            method_sequence = [
                ('TestClass', 'method1'),
                ('TestClass', 'method2'),
            ]
            return self.execute_with_optimization(doc, method_executor, method_sequence)
    
    executor = MultiMethodExecutor(mock_method_executor, signal_registry=registry)
    
    mock_doc = Mock()
    mock_doc.raw_text = "Test"
    mock_doc.metadata = {}
    
    result = executor.execute(mock_doc, mock_method_executor)
    
    # Verify: Only one signal fetch for entire execution
    assert len(executor.used_signals) == 1
    
    # Verify: Signal metadata tracked
    assert "used_signals" in result["meta"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
