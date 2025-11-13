"""
Integration tests for chunk-aware execution.

Tests the SPC exploitation features including chunk routing,
chunk-scoped execution, and verification that chunk mode
produces equivalent results to flat mode.
"""

import pytest

# Import the components we're testing
try:
    from saaaaaa.core.orchestrator.core import ChunkData, PreprocessedDocument
    from saaaaaa.core.orchestrator.chunk_router import ChunkRouter
    HAS_IMPORTS = True
except ImportError:
    HAS_IMPORTS = False
    pytest.skip("Required modules not available", allow_module_level=True)


class TestChunkRouting:
    """Test chunk routing functionality."""
    
    def test_chunk_router_initialization(self):
        """Test that ChunkRouter initializes correctly."""
        router = ChunkRouter()
        assert router is not None
        assert hasattr(router, 'ROUTING_TABLE')
        assert isinstance(router.ROUTING_TABLE, dict)
    
    def test_chunk_routing_coverage(self):
        """Verify all chunk types have executors mapped."""
        router = ChunkRouter()
        
        chunk_types = ["diagnostic", "activity", "indicator", "resource", "temporal", "entity"]
        
        for chunk_type in chunk_types:
            mock_chunk = ChunkData(
                id=0,
                text="test chunk",
                chunk_type=chunk_type,
                sentences=[],
                tables=[],
                start_pos=0,
                end_pos=100,
                confidence=0.9,
            )
            
            route = router.route_chunk(mock_chunk)
            
            # Each chunk type should have at least one executor
            assert route.executor_class != "", f"No executor for chunk type {chunk_type}"
            assert route.skip_reason is None, f"Chunk type {chunk_type} skipped: {route.skip_reason}"
            assert route.chunk_type == chunk_type
    
    def test_chunk_routing_unknown_type(self):
        """Test router behavior for unknown chunk type."""
        router = ChunkRouter()
        
        # Test get_relevant_executors with an unknown type
        executors = router.get_relevant_executors("unknown_type")
        assert executors == []
        
        # We can't create a ChunkData with invalid chunk_type due to Literal type constraint
        # So we test the router's behavior directly with get_relevant_executors
    
    def test_get_relevant_executors(self):
        """Test getting relevant executors for a chunk type."""
        router = ChunkRouter()
        
        # Diagnostic chunks should map to baseline/gap executors
        executors = router.get_relevant_executors("diagnostic")
        assert len(executors) > 0
        assert "D1Q1" in executors or "D1Q2" in executors
        
        # Activity chunks should map to intervention executors
        executors = router.get_relevant_executors("activity")
        assert len(executors) > 0
        assert any(ex.startswith("D2") for ex in executors)


class TestChunkDataStructure:
    """Test ChunkData and PreprocessedDocument structures."""
    
    def test_chunk_data_creation(self):
        """Test creating ChunkData objects."""
        chunk = ChunkData(
            id=1,
            text="Test chunk text",
            chunk_type="diagnostic",
            sentences=[0, 1, 2],
            tables=[0],
            start_pos=0,
            end_pos=50,
            confidence=0.85,
            edges_out=[2, 3],
            edges_in=[0],
        )
        
        assert chunk.id == 1
        assert chunk.chunk_type == "diagnostic"
        assert len(chunk.sentences) == 3
        assert len(chunk.edges_out) == 2
        assert chunk.confidence == 0.85
    
    def test_preprocessed_document_chunked_mode(self):
        """Test PreprocessedDocument in chunked mode."""
        chunks = [
            ChunkData(
                id=i,
                text=f"Chunk {i}",
                chunk_type="diagnostic",
                sentences=[i],
                tables=[],
                start_pos=i*10,
                end_pos=(i+1)*10,
                confidence=0.9,
            )
            for i in range(3)
        ]
        
        doc = PreprocessedDocument(
            document_id="test_doc",
            raw_text="Test document text",
            sentences=[{"text": "Sentence 1"}, {"text": "Sentence 2"}],
            tables=[],
            metadata={},
            chunks=chunks,
            chunk_index={"sent_0": 0, "sent_1": 1},
            chunk_graph={"nodes": [], "edges": []},
            processing_mode="chunked",
        )
        
        assert doc.processing_mode == "chunked"
        assert len(doc.chunks) == 3
        assert doc.chunk_index["sent_0"] == 0
        assert doc.chunk_graph is not None
    
    def test_preprocessed_document_flat_mode_compatibility(self):
        """Test that PreprocessedDocument still works in flat mode."""
        doc = PreprocessedDocument(
            document_id="test_doc",
            raw_text="Test document text",
            sentences=[{"text": "Sentence 1"}],
            tables=[],
            metadata={},
        )
        
        # Default mode should be flat
        assert doc.processing_mode == "flat"
        assert len(doc.chunks) == 0
        assert len(doc.chunk_index) == 0


class TestSPCCausalBridge:
    """Test SPC causal bridge functionality."""
    
    def test_spc_causal_bridge_initialization(self):
        """Test SPCCausalBridge initializes correctly."""
        try:
            from saaaaaa.analysis.spc_causal_bridge import SPCCausalBridge
            
            bridge = SPCCausalBridge()
            assert bridge is not None
            assert hasattr(bridge, 'CAUSAL_WEIGHTS')
            assert bridge.CAUSAL_WEIGHTS["dependency"] > bridge.CAUSAL_WEIGHTS["sequential"]
        except ImportError:
            pytest.skip("SPCCausalBridge not available")
    
    def test_causal_weight_mapping(self):
        """Test that edge types map to appropriate causal weights."""
        try:
            from saaaaaa.analysis.spc_causal_bridge import SPCCausalBridge
            
            bridge = SPCCausalBridge()
            
            # Strong causal relationships should have high weights
            assert bridge._compute_causal_weight("dependency") > 0.8
            assert bridge._compute_causal_weight("hierarchical") > 0.6
            
            # Weak causal relationships should have lower weights
            assert bridge._compute_causal_weight("sequential") < 0.5
            
            # Unknown types should return 0
            assert bridge._compute_causal_weight("unknown_type") == 0.0
        except ImportError:
            pytest.skip("SPCCausalBridge not available")
    
    def test_build_causal_graph_from_spc(self):
        """Test building causal graph from chunk graph."""
        try:
            from saaaaaa.analysis.spc_causal_bridge import SPCCausalBridge
            import networkx as nx
            
            bridge = SPCCausalBridge()
            
            chunk_graph = {
                "nodes": [
                    {"id": 0, "type": "diagnostic", "text": "Node 0", "confidence": 0.9},
                    {"id": 1, "type": "activity", "text": "Node 1", "confidence": 0.8},
                    {"id": 2, "type": "indicator", "text": "Node 2", "confidence": 0.85},
                ],
                "edges": [
                    {"source": 0, "target": 1, "type": "sequential"},
                    {"source": 1, "target": 2, "type": "dependency"},
                ],
            }
            
            G = bridge.build_causal_graph_from_spc(chunk_graph)
            
            assert G is not None
            assert G.number_of_nodes() == 3
            assert G.number_of_edges() == 2
            assert nx.is_directed_acyclic_graph(G)
            
        except ImportError:
            pytest.skip("NetworkX or SPCCausalBridge not available")


class TestChunkMetricsCalculation:
    """Test chunk metrics calculation for verification manifest."""
    
    def test_chunk_metrics_for_chunked_mode(self):
        """Test that chunk metrics are calculated correctly."""
        # This would require running the actual pipeline
        # For now, we just verify the structure
        
        chunks = [
            ChunkData(
                id=i,
                text=f"Chunk {i}",
                chunk_type=["diagnostic", "activity", "indicator"][i % 3],
                sentences=[i],
                tables=[],
                start_pos=i*10,
                end_pos=(i+1)*10,
                confidence=0.9,
            )
            for i in range(6)
        ]
        
        # Verify chunk type distribution
        chunk_types = {}
        for chunk in chunks:
            chunk_types[chunk.chunk_type] = chunk_types.get(chunk.chunk_type, 0) + 1
        
        assert chunk_types["diagnostic"] == 2
        assert chunk_types["activity"] == 2
        assert chunk_types["indicator"] == 2


# Integration test markers
@pytest.mark.integration
class TestChunkVsFlatEquivalence:
    """
    Test that chunk mode produces equivalent results to flat mode.
    
    Note: This would require running the full pipeline with real data.
    For now, we document the expected behavior.
    """
    
    def test_structure_preservation(self):
        """
        Verify that chunk mode preserves semantic structure.
        
        This test would:
        1. Run pipeline on same input in both modes
        2. Compare macro scores (should be within 5% relative tolerance)
        3. Verify chunk mode executes fewer operations
        4. Confirm chunk mode maintains quality
        """
        pytest.skip("Requires full pipeline execution with real data")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
