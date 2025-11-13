"""Tests for enhanced argument resolution with graph-aware intelligence.

This module tests the new enhanced argument resolution features including:
- Graph-aware context initialization
- Sophisticated segments resolution
- Graph object resolution (DiGraph for causal analysis)
- Graph node resolution (origen, destino for causal links)
- Statements resolution
- Graph construction helper
"""

from unittest.mock import Mock
import pytest


# Mark all tests in this module as outdated
pytestmark = pytest.mark.skip(reason="Argument resolution now in ArgRouter extended tests")

from saaaaaa.core.orchestrator.executors import AdvancedDataFlowExecutor, D1Q1_Executor


class MockDoc:
    """Mock document for testing"""
    def __init__(self):
        self.raw_text = "This is a test document. It has multiple sentences."
        self.sentences = ["This is a test document.", "It has multiple sentences."]
        self.tables = []
        self.metadata = {}


class MockExecutor:
    """Mock method executor for testing"""
    def __init__(self):
        self.instances = {}
        
    def execute(self, class_name, method_name, **kwargs):
        return "mock_result"


class TestEnhancedArgumentContext:
    """Test enhanced argument context initialization"""
    
    def test_reset_argument_context_includes_graph_fields(self):
        """Test that reset includes graph-aware fields"""
        mock_method_executor = MockExecutor()
        executor = D1Q1_Executor(mock_method_executor)
        mock_doc = MockDoc()
        
        executor._reset_argument_context(mock_doc)
        
        ctx = executor._argument_context
        
        # Check enhanced graph-aware fields
        assert 'grafo' in ctx
        assert 'graph_nodes' in ctx
        assert 'graph_edges' in ctx
        assert 'statements' in ctx
        
        # Check enhanced segmentation fields
        assert 'segments' in ctx
        assert 'segment_metadata' in ctx
        
        # Check initial values
        assert ctx['grafo'] is None
        assert ctx['graph_nodes'] == []
        assert ctx['graph_edges'] == []
        assert ctx['statements'] == []
        assert ctx['segment_metadata'] == {}


class TestSegmentsResolution:
    """Test sophisticated segments resolution"""
    
    def test_segments_resolution_from_sentences(self):
        """Test that segments are resolved from sentences"""
        mock_method_executor = MockExecutor()
        executor = D1Q1_Executor(mock_method_executor)
        mock_doc = MockDoc()
        
        executor._reset_argument_context(mock_doc)
        
        # Resolve segments
        segments = executor._resolve_argument(
            name='segments',
            class_name='TestClass',
            method_name='test_method',
            doc=mock_doc,
            current_data=None,
            instance=Mock()
        )
        
        assert isinstance(segments, list)
        assert len(segments) > 0
        assert executor._argument_context['segment_metadata']['strategy'] == 'sentence_based'
    
    def test_segments_resolution_from_text(self):
        """Test that segments are created from text when sentences unavailable"""
        mock_method_executor = MockExecutor()
        executor = D1Q1_Executor(mock_method_executor)
        mock_doc = MockDoc()
        mock_doc.sentences = []  # No sentences available
        
        executor._reset_argument_context(mock_doc)
        
        # Resolve segments
        segments = executor._resolve_argument(
            name='segments',
            class_name='TestClass',
            method_name='test_method',
            doc=mock_doc,
            current_data=None,
            instance=Mock()
        )
        
        assert isinstance(segments, list)
        assert len(segments) > 0
        assert executor._argument_context['segment_metadata']['strategy'] == 'semantic_split'


class TestGraphResolution:
    """Test graph object resolution"""
    
    def test_graph_resolution_returns_unset_when_unavailable(self):
        """Test that graph resolution returns _ARG_UNSET when unavailable"""
        from saaaaaa.core.orchestrator.executors import _ARG_UNSET
        
        mock_method_executor = MockExecutor()
        executor = D1Q1_Executor(mock_method_executor)
        mock_doc = MockDoc()
        
        executor._reset_argument_context(mock_doc)
        
        # Create a mock instance without graph attributes
        mock_instance = Mock(spec=['some_method'])  # Spec without grafo/graph attributes
        
        # Resolve graph without any graph available
        grafo = executor._resolve_argument(
            name='grafo',
            class_name='TestClass',
            method_name='test_method',
            doc=mock_doc,
            current_data=None,
            instance=mock_instance
        )
        
        assert grafo is _ARG_UNSET
    
    def test_graph_fallback_creates_empty_digraph(self):
        """Test that graph fallback creates an empty NetworkX DiGraph"""
        mock_method_executor = MockExecutor()
        executor = D1Q1_Executor(mock_method_executor)
        mock_doc = MockDoc()
        
        executor._reset_argument_context(mock_doc)
        
        # Get fallback for graph
        try:
            grafo = executor._fallback_for(
                name='grafo',
                class_name='TestClass',
                method_name='test_method',
                instance=Mock()
            )
            
            # Check if NetworkX is available and graph was created
            if grafo is not None:
                import networkx as nx
                assert isinstance(grafo, nx.DiGraph)
                assert len(grafo.nodes()) == 0
        except ImportError:
            # NetworkX not available, should return None
            assert grafo is None


class TestNodeResolution:
    """Test graph node resolution (origen, destino)"""
    
    def test_origen_resolution_from_dict(self):
        """Test origen resolution from dictionary"""
        mock_method_executor = MockExecutor()
        executor = D1Q1_Executor(mock_method_executor)
        mock_doc = MockDoc()
        
        executor._reset_argument_context(mock_doc)
        
        current_data = {'origen': 'node_a', 'destino': 'node_b'}
        
        origen = executor._resolve_argument(
            name='origen',
            class_name='TestClass',
            method_name='test_method',
            doc=mock_doc,
            current_data=current_data,
            instance=Mock()
        )
        
        assert origen == 'node_a'
    
    def test_destino_resolution_from_tuple(self):
        """Test destino resolution from tuple"""
        mock_method_executor = MockExecutor()
        executor = D1Q1_Executor(mock_method_executor)
        mock_doc = MockDoc()
        
        executor._reset_argument_context(mock_doc)
        
        current_data = ('node_a', 'node_b')
        
        destino = executor._resolve_argument(
            name='destino',
            class_name='TestClass',
            method_name='test_method',
            doc=mock_doc,
            current_data=current_data,
            instance=Mock()
        )
        
        assert destino == 'node_b'
    
    def test_node_fallbacks(self):
        """Test node fallbacks return default node identifiers"""
        mock_method_executor = MockExecutor()
        executor = D1Q1_Executor(mock_method_executor)
        mock_doc = MockDoc()
        
        executor._reset_argument_context(mock_doc)
        
        origen = executor._fallback_for(
            name='origen',
            class_name='TestClass',
            method_name='test_method',
            instance=Mock()
        )
        
        destino = executor._fallback_for(
            name='destino',
            class_name='TestClass',
            method_name='test_method',
            instance=Mock()
        )
        
        assert origen == "node_0"
        assert destino == "node_1"


class TestStatementsResolution:
    """Test statements resolution"""
    
    def test_statements_resolution_from_list(self):
        """Test statements resolution from list data"""
        mock_method_executor = MockExecutor()
        executor = D1Q1_Executor(mock_method_executor)
        mock_doc = MockDoc()
        
        executor._reset_argument_context(mock_doc)
        
        current_data = ["Statement 1", "Statement 2", "Statement 3"]
        
        statements = executor._resolve_argument(
            name='statements',
            class_name='TestClass',
            method_name='test_method',
            doc=mock_doc,
            current_data=current_data,
            instance=Mock()
        )
        
        assert statements == current_data
        assert executor._argument_context['statements'] == current_data


class TestUpdateArgumentContext:
    """Test enhanced context update with graph-aware tracking"""
    
    def test_update_tracks_graph_from_teoria_cambio(self):
        """Test that DiGraph from TeoriaCambio is tracked"""
        mock_method_executor = MockExecutor()
        executor = D1Q1_Executor(mock_method_executor)
        mock_doc = MockDoc()
        
        executor._reset_argument_context(mock_doc)
        
        # Create a mock graph result
        try:
            import networkx as nx
            mock_graph = nx.DiGraph()
            mock_graph.add_edge('A', 'B')
            mock_graph.add_edge('B', 'C')
            
            executor._update_argument_context(
                method_key='TeoriaCambio.construir_grafo_causal',
                result=mock_graph,
                class_name='TeoriaCambio',
                method_name='construir_grafo_causal'
            )
            
            ctx = executor._argument_context
            assert ctx['grafo'] is mock_graph
            assert len(ctx['graph_nodes']) == 3
            assert len(ctx['graph_edges']) == 2
        except ImportError:
            pytest.skip("NetworkX not available")
    
    def test_update_tracks_segments(self):
        """Test that segments from segmentation methods are tracked"""
        mock_method_executor = MockExecutor()
        executor = D1Q1_Executor(mock_method_executor)
        mock_doc = MockDoc()
        
        executor._reset_argument_context(mock_doc)
        
        segments = ["Segment 1", "Segment 2", "Segment 3"]
        
        executor._update_argument_context(
            method_key='PolicyTextProcessor.segment_into_sentences',
            result=segments,
            class_name='PolicyTextProcessor',
            method_name='segment_into_sentences'
        )
        
        ctx = executor._argument_context
        assert ctx['segments'] == segments
        assert ctx['segment_metadata']['strategy'] == 'method_result'
        assert ctx['segment_metadata']['count'] == 3


class TestConstructCausalGraph:
    """Test graph construction helper"""
    
    def test_construct_causal_graph_creates_graph(self):
        """Test that construct_causal_graph creates a NetworkX DiGraph"""
        mock_method_executor = MockExecutor()
        executor = D1Q1_Executor(mock_method_executor)
        mock_doc = MockDoc()
        
        executor._reset_argument_context(mock_doc)
        
        statements = [
            "A causes B",
            "B results in C",
            "C because of D"
        ]
        
        try:
            graph = executor._construct_causal_graph(statements, Mock())
            
            if graph is not None:
                import networkx as nx
                assert isinstance(graph, nx.DiGraph)
                # Should have some nodes from causal extraction
                assert len(graph.nodes()) > 0
        except ImportError:
            pytest.skip("NetworkX not available")
    
    def test_construct_causal_graph_handles_non_causal_statements(self):
        """Test that non-causal statements are handled gracefully"""
        mock_method_executor = MockExecutor()
        executor = D1Q1_Executor(mock_method_executor)
        mock_doc = MockDoc()
        
        executor._reset_argument_context(mock_doc)
        
        statements = [
            "This is a statement",
            "Another statement",
            "Yet another one"
        ]
        
        try:
            graph = executor._construct_causal_graph(statements, Mock())
            
            if graph is not None:
                import networkx as nx
                assert isinstance(graph, nx.DiGraph)
                # May have isolated nodes but no edges
                assert len(graph.nodes()) >= 0
        except ImportError:
            pytest.skip("NetworkX not available")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
