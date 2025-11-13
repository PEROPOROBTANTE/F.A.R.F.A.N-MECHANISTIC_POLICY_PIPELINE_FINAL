#!/usr/bin/env python3
"""
Equipment script for CPP subsystem.

Runs smoke tests for SPCAdapter and CPPIngestionPipeline.
"""

import sys
import traceback
from pathlib import Path
from typing import Dict, Any


def test_cpp_adapter_import() -> Dict[str, Any]:
    """Test SPCAdapter can be imported."""
    try:
        from saaaaaa.utils.spc_adapter import SPCAdapter, adapt_spc_to_orchestrator
        return {
            "success": True,
            "message": "SPCAdapter importable"
        }
    except ImportError as e:
        return {
            "success": False,
            "message": f"Import failed: {e}"
        }


def test_cpp_ingestion_pipeline() -> Dict[str, Any]:
    """Test CPPIngestionPipeline initialization."""
    try:
        from saaaaaa.processing.cpp_ingestion import CPPIngestionPipeline
        
        pipeline = CPPIngestionPipeline(
            enable_ocr=False,
            ocr_confidence_threshold=0.85,
            chunk_overlap_threshold=0.15
        )
        
        return {
            "success": True,
            "schema_version": pipeline.SCHEMA_VERSION,
            "message": f"CPPIngestionPipeline initialized (schema={pipeline.SCHEMA_VERSION})"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Initialization failed: {e}"
        }


def test_cpp_adapter_conversion() -> Dict[str, Any]:
    """Test SPCAdapter conversion with minimal CPP document."""
    try:
        from saaaaaa.utils.spc_adapter import SPCAdapter
        from saaaaaa.processing.cpp_ingestion.models import (
            CanonPolicyPackage,
            ChunkGraph,
            Chunk,
            ChunkResolution,
            TextSpan,
            PolicyManifest,
            ProvenanceMap,
            QualityMetrics,
            IntegrityIndex,
        )
        
        # Create minimal test CPP
        chunk = Chunk(
            id="test_chunk_001",
            bytes_hash="test_hash",
            text_span=TextSpan(start=0, end=100),
            resolution=ChunkResolution.MICRO,
            text="Test policy document text.",
            policy_facets=None,
            time_facets=None,
            geo_facets=None,
        )
        
        chunk_graph = ChunkGraph()
        chunk_graph.add_chunk(chunk)
        
        policy_manifest = PolicyManifest(
            axes=["test_axis"],
            programs=["test_program"],
            years=[2024],
            territories=["test_territory"]
        )
        
        provenance_map = ProvenanceMap(
            source_document="test_doc.pdf",
            ingestion_timestamp="2025-11-06T00:00:00Z",
            pipeline_version="1.0.0"
        )
        
        quality_metrics = QualityMetrics(
            boundary_f1=0.95,
            kpi_linkage_rate=0.90,
            budget_consistency_score=0.85,
            provenance_completeness=1.0
        )
        
        integrity_index = IntegrityIndex(
            chunk_count=1,
            total_bytes=100,
            global_hash="test_global_hash"
        )
        
        cpp = CanonPolicyPackage(
            chunk_graph=chunk_graph,
            policy_manifest=policy_manifest,
            provenance_map=provenance_map,
            quality_metrics=quality_metrics,
            integrity_index=integrity_index,
            schema_version="1.0.0"
        )
        
        # Test conversion
        adapter = SPCAdapter()
        preprocessed = adapter.adapt(cpp)
        
        return {
            "success": True,
            "provenance_completeness": cpp.quality_metrics.provenance_completeness,
            "chunk_count": len(preprocessed.sentences),
            "message": f"Conversion successful (provenance={cpp.quality_metrics.provenance_completeness})"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Conversion failed: {e}",
            "traceback": traceback.format_exc()
        }


def test_cpp_ensure() -> Dict[str, Any]:
    """Test SPCAdapter.ensure() method."""
    try:
        from saaaaaa.utils.spc_adapter import SPCAdapter
        from saaaaaa.processing.cpp_ingestion.models import CanonPolicyPackage
        
        # Create adapter
        adapter = SPCAdapter()
        
        # Test with None (should raise)
        try:
            adapter.ensure(None)
            return {
                "success": False,
                "message": "ensure(None) should raise SPCAdapterError"
            }
        except Exception:
            pass  # Expected
        
        return {
            "success": True,
            "message": "ensure() validation working"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"ensure() test failed: {e}"
        }


def main():
    """Run CPP equipment smoke tests."""
    print("=" * 70)
    print("EQUIP:CPP - CPP Adapter & Ingestion")
    print("=" * 70)
    print()
    
    tests = [
        ("SPCAdapter import", test_cpp_adapter_import),
        ("CPPIngestionPipeline init", test_cpp_ingestion_pipeline),
        ("SPCAdapter conversion", test_cpp_adapter_conversion),
        ("SPCAdapter ensure()", test_cpp_ensure),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"Testing: {name}...")
        result = test_func()
        results.append(result['success'])
        
        if result['success']:
            print(f"✓ {result['message']}")
        else:
            print(f"✗ {result['message']}")
            if 'traceback' in result:
                print(f"  Traceback:\n{result['traceback']}")
        print()
    
    print("=" * 70)
    if all(results):
        print(f"✓ CPP EQUIPMENT COMPLETE: {len(results)}/{len(results)} tests passed")
    else:
        failed = sum(1 for r in results if not r)
        print(f"✗ CPP EQUIPMENT FAILED: {failed}/{len(results)} tests failed")
    print("=" * 70)
    
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
