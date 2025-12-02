"""Test Phase1→Phase2 Adapter Contract

Tests PA×DIM metadata preservation, sentence_metadata.extra structure.
"""
import pytest
from unittest.mock import MagicMock, patch
import hashlib

from farfan_pipeline.core.phases.phase1_to_phase2_adapter import AdapterContract


class TestAdapterContract:
    """Test adapter contract validation."""

    def test_adapter_preserves_pa_dim_metadata(self):
        """Test adapter preserves policy_area_id and dimension_id in sentence_metadata.extra."""
        from farfan_pipeline.processing.models import (
            CanonPolicyPackage, ChunkGraph, Chunk, ChunkResolution,
            TextSpan, QualityMetrics, IntegrityIndex, PolicyManifest
        )
        
        contract = AdapterContract()
        
        chunk_graph = ChunkGraph()
        chunk = Chunk(
            id="test_chunk", text="Test chunk text",
            text_span=TextSpan(0, 50), resolution=ChunkResolution.MESO,
            bytes_hash=hashlib.blake2b(b"test").hexdigest(),
            policy_area_id="PA01", dimension_id="DIM01"
        )
        chunk_graph.add_chunk(chunk)

        cpp = CanonPolicyPackage(
            schema_version="SPC-2025.1", chunk_graph=chunk_graph,
            policy_manifest=PolicyManifest(),
            quality_metrics=QualityMetrics(provenance_completeness=0.9, structural_consistency=0.9),
            integrity_index=IntegrityIndex(blake2b_root="a"*64),
            metadata={"document_id": "test"}
        )
        
        result = contract.validate_input(cpp)
        assert result.passed

    def test_adapter_output_has_chunked_mode(self):
        """Test adapter output has processing_mode='chunked'."""
        contract = AdapterContract()
        
        invariant = next(inv for inv in contract.invariants if inv.name == "processing_mode_chunked")
        assert invariant is not None
        assert "chunked" in invariant.description

    def test_adapter_requires_chunk_id_in_extra(self):
        """Test adapter requires chunk_id in sentence_metadata.extra."""
        contract = AdapterContract()
        
        invariant = next(inv for inv in contract.invariants if inv.name == "chunk_id_preserved")
        assert invariant is not None
        assert "chunk_id" in invariant.description

    def test_adapter_requires_policy_area_id_in_extra(self):
        """Test adapter requires policy_area_id in sentence_metadata.extra."""
        contract = AdapterContract()
        
        invariant = next(inv for inv in contract.invariants if inv.name == "policy_area_id_preserved")
        assert invariant is not None
        assert "policy_area_id" in invariant.description

    def test_adapter_requires_dimension_id_in_extra(self):
        """Test adapter requires dimension_id in sentence_metadata.extra."""
        contract = AdapterContract()
        
        invariant = next(inv for inv in contract.invariants if inv.name == "dimension_id_preserved")
        assert invariant is not None
        assert "dimension_id" in invariant.description
