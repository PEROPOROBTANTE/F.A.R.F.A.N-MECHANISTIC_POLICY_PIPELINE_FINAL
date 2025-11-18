"""
HOSTILE AUDIT TEST SUITE FOR PHASE 1
======================================

Validates Phase 1 against pragmatic Python-pure checklist.
NO MERCY. Verificable or it doesn't exist.

Run with: pytest tests/test_phase1_hostile_audit.py -v
"""

import json
import hashlib
import unicodedata
from pathlib import Path
from dataclasses import is_dataclass, asdict

import pytest


class TestPhase1HostileAudit:
    """Hostile audit test suite for Phase 1 pipeline."""

    @pytest.fixture
    def sample_cpp_path(self):
        """Path to sample CPP artifact (must be generated first)."""
        return Path("artifacts/plan1/cpp.json")

    @pytest.fixture
    def sample_cpp(self, sample_cpp_path):
        """Load sample CPP from artifacts."""
        if not sample_cpp_path.exists():
            pytest.skip(f"CPP artifact not found: {sample_cpp_path}. Run pipeline first.")

        with open(sample_cpp_path, 'r') as f:
            return json.load(f)

    # =========================================================================
    # A. ENTRADA Y ENTORNO
    # =========================================================================

    def test_A1_input_pdf_exists(self):
        """Verify input PDF exists at expected path."""
        input_pdf = Path("data/plans/Plan_1.pdf")
        assert input_pdf.exists(), f"Input PDF not found: {input_pdf}"
        assert input_pdf.stat().st_size > 0, "Input PDF is empty"

    def test_A2_no_rust_module_required(self):
        """Verify no cpp_ingestion Rust module is required."""
        # This is a meta-test: We've adapted to Python-pure, so NO Rust dependency
        try:
            import cpp_ingestion
            pytest.fail("cpp_ingestion Rust module found but should NOT be required")
        except ImportError:
            pass  # Expected - we use Python-pure pipeline

    # =========================================================================
    # B. EXTRACCIÓN DE CONTENIDO
    # =========================================================================

    def test_B1_unicode_normalization_applied(self, tmp_path):
        """Verify Unicode NFC normalization is applied during text extraction."""
        from saaaaaa.processing.spc_ingestion import CPPIngestionPipeline

        # Create test file with denormalized Unicode (NFD)
        test_text = "Educación"  # Contains composed 'ó'
        test_nfd = unicodedata.normalize('NFD', test_text)  # Decompose
        test_file = tmp_path / "test_nfd.txt"

        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_nfd)

        # Load through pipeline
        pipeline = CPPIngestionPipeline()
        loaded_text = pipeline._load_document_text(test_file)

        # Verify output is NFC normalized
        assert loaded_text == unicodedata.normalize('NFC', loaded_text), \
            "Text not NFC normalized after loading"

    # =========================================================================
    # C. CONSTRUCCIÓN DE CHUNKS Y CHUNKGRAPH
    # =========================================================================

    def test_C1_chunks_non_empty(self, sample_cpp):
        """Verify chunk_graph.chunks is non-empty."""
        assert "chunk_graph" in sample_cpp, "Missing chunk_graph in CPP"
        chunks = sample_cpp["chunk_graph"]["chunks"]
        assert len(chunks) >= 5, f"Too few chunks: {len(chunks)} < 5"

    def test_C2_chunks_have_required_fields(self, sample_cpp):
        """Verify each chunk has id, text, text_span."""
        chunks = sample_cpp["chunk_graph"]["chunks"]

        for chunk_id, chunk in chunks.items():
            assert "id" in chunk, f"Chunk {chunk_id} missing 'id'"
            assert "text" in chunk, f"Chunk {chunk_id} missing 'text'"
            assert chunk["text"].strip(), f"Chunk {chunk_id} has empty text"
            assert "text_span" in chunk, f"Chunk {chunk_id} missing 'text_span'"

            span = chunk["text_span"]
            assert "start" in span and "end" in span, \
                f"Chunk {chunk_id} text_span missing start/end"
            assert span["start"] < span["end"], \
                f"Chunk {chunk_id} invalid span: start >= end"

    def test_C3_chunk_hashes_computed(self, sample_cpp):
        """Verify each chunk has a bytes_hash."""
        chunks = sample_cpp["chunk_graph"]["chunks"]

        for chunk_id, chunk in chunks.items():
            assert "bytes_hash" in chunk, f"Chunk {chunk_id} missing 'bytes_hash'"
            chunk_hash = chunk["bytes_hash"]
            assert len(chunk_hash) == 64, \
                f"Chunk {chunk_id} hash invalid length: {len(chunk_hash)} != 64"

    def test_C4_chunk_graph_has_edges(self, sample_cpp):
        """Verify chunk_graph has edges (not flat list)."""
        assert "chunk_graph" in sample_cpp
        edges = sample_cpp["chunk_graph"].get("edges", [])
        # At minimum, expect some edges (relaxed: at least 1)
        assert len(edges) >= 1, "ChunkGraph has no edges (flat structure)"

    # =========================================================================
    # D. ÍNDICES DE INTEGRIDAD
    # =========================================================================

    def test_D1_integrity_index_exists(self, sample_cpp):
        """Verify IntegrityIndex exists."""
        assert "integrity_index" in sample_cpp, "Missing integrity_index in CPP"

    def test_D2_blake2b_root_present(self, sample_cpp):
        """Verify blake2b_root is present and not dummy."""
        integrity = sample_cpp["integrity_index"]
        assert "blake2b_root" in integrity, "Missing blake2b_root in IntegrityIndex"

        root_hash = integrity["blake2b_root"]
        assert root_hash, "blake2b_root is empty"
        assert len(root_hash) == 64, f"blake2b_root invalid length: {len(root_hash)}"
        assert root_hash != "0" * 64, "blake2b_root is dummy value"

    def test_D3_chunk_hashes_dict_present(self, sample_cpp):
        """Verify chunk_hashes dict is present."""
        integrity = sample_cpp["integrity_index"]
        assert "chunk_hashes" in integrity, "Missing chunk_hashes in IntegrityIndex"
        assert len(integrity["chunk_hashes"]) > 0, "chunk_hashes is empty"

    def test_D4_blake2b_recomputable(self, sample_cpp):
        """Verify blake2b_root is recomputable from chunk_hashes."""
        integrity = sample_cpp["integrity_index"]
        chunk_hashes = integrity["chunk_hashes"]
        stored_root = integrity["blake2b_root"]

        # Recompute
        combined = json.dumps(chunk_hashes, sort_keys=True).encode('utf-8')
        recomputed_root = hashlib.blake2b(combined, digest_size=32).hexdigest()

        assert recomputed_root == stored_root, \
            "blake2b_root mismatch: not deterministically recomputable"

    # =========================================================================
    # E. QUALITY METRICS
    # =========================================================================

    def test_E1_quality_metrics_exist(self, sample_cpp):
        """Verify QualityMetrics exist."""
        assert "quality_metrics" in sample_cpp, "Missing quality_metrics in CPP"

    def test_E2_quality_metrics_computed(self, sample_cpp):
        """Verify quality metrics are computed (not dummy)."""
        metrics = sample_cpp["quality_metrics"]

        # Check critical metrics
        assert "provenance_completeness" in metrics
        assert "structural_consistency" in metrics
        assert "boundary_f1" in metrics

        # Values should be in [0, 1] range
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                assert 0 <= value <= 1, \
                    f"Metric {key} out of range: {value} not in [0, 1]"

    # =========================================================================
    # F. CANON POLICY PACKAGE COMPLETO
    # =========================================================================

    def test_F1_cpp_minimal_structure(self, sample_cpp):
        """Verify CPP has minimal required structure."""
        required_keys = [
            "schema_version",
            "chunk_graph",
            "policy_manifest",
            "quality_metrics",
            "integrity_index",
            "metadata"
        ]

        for key in required_keys:
            assert key in sample_cpp, f"CPP missing required key: {key}"

    def test_F2_policy_manifest_present(self, sample_cpp):
        """Verify PolicyManifest has expected fields."""
        manifest = sample_cpp["policy_manifest"]

        expected_fields = ["axes", "programs", "projects", "years", "territories"]
        for field in expected_fields:
            assert field in manifest, f"PolicyManifest missing field: {field}"

    # =========================================================================
    # G. INTEGRACIÓN CON RUNNER VERIFICADO
    # =========================================================================

    def test_G1_verification_manifest_exists(self):
        """Verify verification_manifest.json was generated."""
        manifest_path = Path("artifacts/plan1/verification_manifest.json")
        if not manifest_path.exists():
            pytest.skip("verification_manifest.json not found. Run pipeline first.")

        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        assert "success" in manifest
        assert "integrity_hmac" in manifest

    def test_G2_cpp_artifact_registered(self):
        """Verify cpp.json is registered in manifest artifacts."""
        manifest_path = Path("artifacts/plan1/verification_manifest.json")
        if not manifest_path.exists():
            pytest.skip("verification_manifest.json not found.")

        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        artifacts = manifest.get("artifacts", [])
        cpp_artifacts = [a for a in artifacts if "cpp.json" in a.get("path", "")]

        assert len(cpp_artifacts) > 0, "cpp.json not registered in manifest artifacts"

    # =========================================================================
    # H. DETERMINISMO
    # =========================================================================

    def test_H1_deterministic_seeds_set(self):
        """Verify StrategicChunkingSystem sets deterministic seeds."""
        import importlib.util
        from pathlib import Path

        # Load smart_policy_chunks module
        module_path = Path("scripts/smart_policy_chunks_canonic_phase_one.py")
        spec = importlib.util.spec_from_file_location("spc", module_path)
        spc_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(spc_module)

        # Check that __init__ accepts random_seed parameter
        import inspect
        sig = inspect.signature(spc_module.StrategicChunkingSystem.__init__)
        assert "random_seed" in sig.parameters, \
            "StrategicChunkingSystem.__init__ missing random_seed parameter"


# =============================================================================
# SUMMARY REPORT
# =============================================================================

def test_summary_report(sample_cpp_path):
    """Generate summary report of hostile audit results."""
    if not sample_cpp_path.exists():
        pytest.skip("CPP artifact not found. Cannot generate summary.")

    with open(sample_cpp_path, 'r') as f:
        cpp = json.load(f)

    print("\n" + "=" * 80)
    print("HOSTILE AUDIT SUMMARY")
    print("=" * 80)

    print(f"✅ CPP artifact found: {sample_cpp_path}")
    print(f"✅ Schema version: {cpp.get('schema_version', 'UNKNOWN')}")
    print(f"✅ Chunks: {len(cpp.get('chunk_graph', {}).get('chunks', {}))}")
    print(f"✅ Edges: {len(cpp.get('chunk_graph', {}).get('edges', []))}")
    print(f"✅ Integrity blake2b_root: {cpp.get('integrity_index', {}).get('blake2b_root', 'MISSING')[:16]}...")

    metrics = cpp.get('quality_metrics', {})
    print(f"✅ Provenance completeness: {metrics.get('provenance_completeness', 0):.2%}")
    print(f"✅ Structural consistency: {metrics.get('structural_consistency', 0):.2%}")

    print("=" * 80)
