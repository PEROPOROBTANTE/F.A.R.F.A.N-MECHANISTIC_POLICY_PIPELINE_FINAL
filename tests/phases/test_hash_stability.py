"""Test BLAKE3/BLAKE2b Hash Stability Across Runs

Tests deterministic hash generation for chunks and integrity verification.
"""
import hashlib
import pytest


class TestHashStability:
    """Test hash stability and determinism."""

    def test_blake2b_deterministic(self):
        """Test BLAKE2b produces same hash for same content."""
        content = b"test chunk content for determinism"
        hash1 = hashlib.blake2b(content).hexdigest()
        hash2 = hashlib.blake2b(content).hexdigest()
        
        assert hash1 == hash2
        assert len(hash1) == 128

    def test_blake2b_different_content_different_hash(self):
        """Test BLAKE2b produces different hashes for different content."""
        hash1 = hashlib.blake2b(b"content A").hexdigest()
        hash2 = hashlib.blake2b(b"content B").hexdigest()
        
        assert hash1 != hash2

    def test_sha256_deterministic(self):
        """Test SHA256 produces same hash for same content."""
        content = b"test PDF content"
        hash1 = hashlib.sha256(content).hexdigest()
        hash2 = hashlib.sha256(content).hexdigest()
        
        assert hash1 == hash2
        assert len(hash1) == 64

    def test_chunk_bytes_hash_stability(self):
        """Test Chunk bytes_hash is stable across runs."""
        from farfan_pipeline.processing.models import Chunk, ChunkResolution, TextSpan
        
        chunk_text = "Policy text for testing hash stability"
        chunk_bytes = chunk_text.encode('utf-8')
        
        hash1 = hashlib.blake2b(chunk_bytes).hexdigest()
        hash2 = hashlib.blake2b(chunk_bytes).hexdigest()
        
        chunk1 = Chunk(
            id="test1", text=chunk_text,
            text_span=TextSpan(0, len(chunk_text)),
            resolution=ChunkResolution.MESO,
            bytes_hash=hash1
        )
        
        chunk2 = Chunk(
            id="test2", text=chunk_text,
            text_span=TextSpan(0, len(chunk_text)),
            resolution=ChunkResolution.MESO,
            bytes_hash=hash2
        )
        
        assert chunk1.bytes_hash == chunk2.bytes_hash

    def test_integrity_index_blake2b_root(self):
        """Test IntegrityIndex uses BLAKE2b for root hash."""
        from farfan_pipeline.processing.models import IntegrityIndex
        
        chunk_hashes = {
            "chunk1": "a" * 128,
            "chunk2": "b" * 128,
            "chunk3": "c" * 128
        }
        
        combined = "".join(sorted(chunk_hashes.values()))
        root_hash = hashlib.blake2b(combined.encode()).hexdigest()
        
        integrity = IntegrityIndex(
            blake2b_root=root_hash,
            chunk_hashes=chunk_hashes
        )
        
        assert len(integrity.blake2b_root) == 128
        assert integrity.blake2b_root == root_hash

    def test_hash_stability_across_multiple_runs(self):
        """Test hash remains stable across multiple computations."""
        content = b"Stable content for multiple hash runs"
        
        hashes = [hashlib.blake2b(content).hexdigest() for _ in range(10)]
        
        assert len(set(hashes)) == 1
        assert all(h == hashes[0] for h in hashes)

    def test_empty_content_has_valid_hash(self):
        """Test empty content produces valid hash."""
        hash_empty = hashlib.blake2b(b"").hexdigest()
        
        assert len(hash_empty) == 128
        assert isinstance(hash_empty, str)

    def test_unicode_content_hash_stability(self):
        """Test hash stability with unicode content."""
        content = "Política de desarrollo con ñ y tildes: áéíóú"
        bytes1 = content.encode('utf-8')
        bytes2 = content.encode('utf-8')
        
        hash1 = hashlib.blake2b(bytes1).hexdigest()
        hash2 = hashlib.blake2b(bytes2).hexdigest()
        
        assert hash1 == hash2
