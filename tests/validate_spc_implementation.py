#!/usr/bin/env python3
"""
Standalone validation script for SPC exploitation features.

This script validates the chunk-aware functionality without requiring pytest.
It can be run directly to verify the implementation.
"""

import sys
from pathlib import Path

# Add src to path
REPO_ROOT = Path(__file__).parent.parent


def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    try:
        from saaaaaa.core.orchestrator.core import ChunkData, PreprocessedDocument
        print("✓ ChunkData and PreprocessedDocument imported")
    except ImportError as e:
        print(f"✗ Failed to import core types: {e}")
        return False
    
    try:
        from saaaaaa.core.orchestrator.chunk_router import ChunkRouter, ChunkRoute
        print("✓ ChunkRouter imported")
    except ImportError as e:
        print(f"✗ Failed to import ChunkRouter: {e}")
        return False
    
    try:
        from saaaaaa.processing.cpp_ingestion.models import CanonPolicyPackage, Chunk
        print("✓ CPP models imported")
    except ImportError as e:
        print(f"✗ Failed to import CPP models: {e}")
        return False
    
    try:
        from saaaaaa.analysis.spc_causal_bridge import SPCCausalBridge
        print("✓ SPCCausalBridge imported")
    except ImportError as e:
        print(f"✗ Failed to import SPCCausalBridge: {e}")
        return False
    
    return True


def test_chunk_data_creation():
    """Test creating ChunkData objects."""
    print("\nTesting ChunkData creation...")
    
    try:
        from saaaaaa.core.orchestrator.core import ChunkData
        
        chunk = ChunkData(
            id=1,
            text="Test chunk",
            chunk_type="diagnostic",
            sentences=[0, 1],
            tables=[],
            start_pos=0,
            end_pos=50,
            confidence=0.9,
            edges_out=[2],
            edges_in=[0],
        )
        
        assert chunk.id == 1
        assert chunk.chunk_type == "diagnostic"
        assert chunk.confidence == 0.9
        print("✓ ChunkData created successfully")
        return True
    except Exception as e:
        print(f"✗ ChunkData creation failed: {e}")
        return False


def test_chunk_router():
    """Test ChunkRouter functionality."""
    print("\nTesting ChunkRouter...")
    
    try:
        from saaaaaa.core.orchestrator.core import ChunkData
        from saaaaaa.core.orchestrator.chunk_router import ChunkRouter
        
        router = ChunkRouter()
        
        # Test all chunk types
        chunk_types = ["diagnostic", "activity", "indicator", "resource", "temporal", "entity"]
        
        for chunk_type in chunk_types:
            chunk = ChunkData(
                id=0,
                text="test",
                chunk_type=chunk_type,
                sentences=[],
                tables=[],
                start_pos=0,
                end_pos=10,
                confidence=0.9,
            )
            
            route = router.route_chunk(chunk)
            
            if route.executor_class == "":
                print(f"✗ No executor for chunk type: {chunk_type}")
                return False
            
            print(f"  ✓ {chunk_type} → {route.executor_class}")
        
        print("✓ ChunkRouter routing successful")
        return True
    except Exception as e:
        print(f"✗ ChunkRouter test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_preprocessed_document():
    """Test PreprocessedDocument with chunks."""
    print("\nTesting PreprocessedDocument...")
    
    try:
        from saaaaaa.core.orchestrator.core import ChunkData, PreprocessedDocument
        
        # Test chunked mode
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
            raw_text="Test text",
            sentences=[],
            tables=[],
            metadata={},
            chunks=chunks,
            chunk_index={},
            chunk_graph={},
            processing_mode="chunked",
        )
        
        assert doc.processing_mode == "chunked"
        assert len(doc.chunks) == 3
        print("✓ PreprocessedDocument in chunked mode works")
        
        # Test flat mode (backward compatibility)
        doc_flat = PreprocessedDocument(
            document_id="test_doc",
            raw_text="Test text",
            sentences=[],
            tables=[],
            metadata={},
        )
        
        assert doc_flat.processing_mode == "flat"
        assert len(doc_flat.chunks) == 0
        print("✓ PreprocessedDocument in flat mode works (backward compatible)")
        
        return True
    except Exception as e:
        print(f"✗ PreprocessedDocument test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_spc_causal_bridge():
    """Test SPCCausalBridge functionality."""
    print("\nTesting SPCCausalBridge...")
    
    try:
        from saaaaaa.analysis.spc_causal_bridge import SPCCausalBridge
        
        bridge = SPCCausalBridge()
        
        # Test causal weight mapping
        assert bridge._compute_causal_weight("dependency") > 0.8
        assert bridge._compute_causal_weight("sequential") < 0.5
        assert bridge._compute_causal_weight("unknown") == 0.0
        print("✓ Causal weight mapping correct")
        
        # Test graph building (if networkx available)
        try:
            import networkx as nx
            
            chunk_graph = {
                "nodes": [
                    {"id": 0, "type": "diagnostic", "text": "Node 0", "confidence": 0.9},
                    {"id": 1, "type": "activity", "text": "Node 1", "confidence": 0.8},
                ],
                "edges": [
                    {"source": 0, "target": 1, "type": "sequential"},
                ],
            }
            
            G = bridge.build_causal_graph_from_spc(chunk_graph)
            
            if G is not None:
                assert G.number_of_nodes() == 2
                assert G.number_of_edges() == 1
                print("✓ Causal graph building successful")
            else:
                print("⚠ NetworkX not available, skipping graph test")
        except ImportError:
            print("⚠ NetworkX not available, skipping graph test")
        
        return True
    except Exception as e:
        print(f"✗ SPCCausalBridge test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all validation tests."""
    print("=" * 80)
    print("SPC EXPLOITATION VALIDATION TESTS")
    print("=" * 80)
    
    tests = [
        ("Imports", test_imports),
        ("ChunkData Creation", test_chunk_data_creation),
        ("ChunkRouter", test_chunk_router),
        ("PreprocessedDocument", test_preprocessed_document),
        ("SPCCausalBridge", test_spc_causal_bridge),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print("=" * 80)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 80)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
