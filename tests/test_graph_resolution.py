"""Test graph argument resolution in executors.py."""
import pytest


# Mark all tests in this module as outdated
pytestmark = pytest.mark.skip(reason="Graph resolution logic moved to cpp_ingestion ChunkGraph")

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False


@pytest.mark.skipif(not HAS_NETWORKX, reason="NetworkX not installed")
def test_create_empty_graph():
    """Test that _create_empty_graph returns a DiGraph."""
    from saaaaaa.core.orchestrator.executors import AdvancedDataFlowExecutor
    from saaaaaa.core.orchestrator.core import MethodExecutor
    
    executor = MethodExecutor()
    adv_executor = AdvancedDataFlowExecutor(executor)
    
    graph = adv_executor._create_empty_graph()
    
    assert isinstance(graph, nx.DiGraph)
    assert len(graph.nodes()) == 0
    assert len(graph.edges()) == 0


@pytest.mark.skipif(not HAS_NETWORKX, reason="NetworkX not installed")
def test_graph_resolution_when_absent():
    """Test that graph resolution returns empty DiGraph when graph is absent."""
    from saaaaaa.core.orchestrator.executors import AdvancedDataFlowExecutor
    from saaaaaa.core.orchestrator.core import MethodExecutor
    
    executor = MethodExecutor()
    adv_executor = AdvancedDataFlowExecutor(executor)
    
    # Create a mock instance without graph attribute
    class MockInstance:
        pass
    
    instance = MockInstance()
    
    # Resolve graph argument
    result = adv_executor._resolve_argument(
        name="grafo",
        class_name="MockClass",
        method_name="mock_method",
        doc=None,
        current_data=None,
        instance=instance
    )
    
    assert isinstance(result, nx.DiGraph)
    assert len(result.nodes()) == 0


@pytest.mark.skipif(not HAS_NETWORKX, reason="NetworkX not installed")
def test_graph_resolution_when_present():
    """Test that graph resolution returns existing graph when present in context."""
    from saaaaaa.core.orchestrator.executors import AdvancedDataFlowExecutor
    from saaaaaa.core.orchestrator.core import MethodExecutor
    
    executor = MethodExecutor()
    adv_executor = AdvancedDataFlowExecutor(executor)
    
    # Create a graph and add it to context
    existing_graph = nx.DiGraph()
    existing_graph.add_node("test_node")
    adv_executor._argument_context["grafo"] = existing_graph
    
    class MockInstance:
        pass
    
    instance = MockInstance()
    
    # Resolve graph argument
    result = adv_executor._resolve_argument(
        name="grafo",
        class_name="MockClass",
        method_name="mock_method",
        doc=None,
        current_data=None,
        instance=instance
    )
    
    assert result is existing_graph
    assert "test_node" in result.nodes()


def test_create_empty_graph_no_networkx():
    """Test that _create_empty_graph raises ImportError when NetworkX is not available."""
    if HAS_NETWORKX:
        pytest.skip("NetworkX is installed")
    
    from saaaaaa.core.orchestrator.executors import AdvancedDataFlowExecutor
    from saaaaaa.core.orchestrator.core import MethodExecutor
    
    executor = MethodExecutor()
    adv_executor = AdvancedDataFlowExecutor(executor)
    
    with pytest.raises(ImportError, match="NetworkX is required for graph operations"):
        adv_executor._create_empty_graph()
