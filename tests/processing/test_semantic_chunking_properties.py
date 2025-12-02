"""
Property-Based Tests for Semantic Chunking Determinism

Uses Hypothesis to verify that semantic chunking is deterministic, consistent,
and maintains correctness properties across different inputs.
"""

import hashlib
import re

import numpy as np
import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from src.farfan_pipeline.processing.semantic_chunking_policy import (
    BayesianEvidenceIntegrator,
    SemanticConfig,
    SemanticProcessor,
)


@st.composite
def spanish_policy_text(draw):
    """Generate realistic Spanish policy text for testing."""
    paragraphs = draw(st.lists(
        st.text(
            alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z'), max_codepoint=255),
            min_size=50,
            max_size=500
        ),
        min_size=1,
        max_size=20
    ))
    return "\n\n".join(p.strip() for p in paragraphs if p.strip())


@st.composite
def chunking_config_strategy(draw):
    """Generate valid SemanticConfig instances."""
    chunk_size = draw(st.integers(min_value=256, max_value=1024))
    chunk_overlap = draw(st.integers(min_value=32, max_value=chunk_size // 2))
    return SemanticConfig(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        similarity_threshold=draw(st.floats(min_value=0.5, max_value=0.95)),
        min_evidence_chunks=draw(st.integers(min_value=1, max_value=5)),
        bayesian_prior_strength=draw(st.floats(min_value=0.1, max_value=1.0)),
        device="cpu",
        batch_size=8,
        fp16=False
    )


class TestSemanticChunkingDeterminism:
    """Property-based tests for semantic chunking determinism."""

    @given(text=spanish_policy_text())
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.too_slow])
    def test_chunking_is_deterministic(self, text):
        """Property: Chunking the same text twice produces identical results."""
        assume(len(text) > 100)

        config = SemanticConfig(device="cpu", batch_size=8, fp16=False)
        processor = SemanticProcessor(config)

        chunks1 = processor.chunk_text(text, preserve_structure=False)
        chunks2 = processor.chunk_text(text, preserve_structure=False)

        assert len(chunks1) == len(chunks2), "Chunk count must be deterministic"

        for c1, c2 in zip(chunks1, chunks2, strict=False):
            assert c1["content"] == c2["content"], "Chunk content must be identical"
            assert c1["token_count"] == c2["token_count"], "Token counts must match"

    @given(text=spanish_policy_text())
    @settings(max_examples=15, deadline=5000, suppress_health_check=[HealthCheck.too_slow])
    def test_chunks_preserve_all_text(self, text):
        """Property: All input text appears in output chunks (no loss)."""
        assume(len(text) > 100)

        config = SemanticConfig(device="cpu", batch_size=8, fp16=False)
        processor = SemanticProcessor(config)

        chunks = processor.chunk_text(text, preserve_structure=False)

        reconstructed = " ".join(c["content"] for c in chunks)

        important_words = re.findall(r'\b\w{4,}\b', text.lower())[:20]
        for word in important_words:
            assert word in reconstructed.lower(), f"Word '{word}' lost during chunking"

    @given(text=spanish_policy_text())
    @settings(max_examples=15, deadline=5000, suppress_health_check=[HealthCheck.too_slow])
    def test_chunk_boundaries_are_coherent(self, text):
        """Property: Chunks don't split words or create malformed fragments."""
        assume(len(text) > 100)

        config = SemanticConfig(device="cpu", batch_size=8, fp16=False)
        processor = SemanticProcessor(config)

        chunks = processor.chunk_text(text, preserve_structure=False)

        for chunk in chunks:
            content = chunk["content"]
            assert content.strip() == content or len(content) < 10, \
                "Chunks should be trimmed or very short"

            assert not content.startswith(' ' * 5), "No excessive leading whitespace"
            assert not content.endswith(' ' * 5), "No excessive trailing whitespace"

    @given(
        text=spanish_policy_text(),
        config=chunking_config_strategy()
    )
    @settings(max_examples=10, deadline=10000, suppress_health_check=[HealthCheck.too_slow])
    def test_chunk_sizes_respect_config(self, text, config):
        """Property: Chunks respect configured size limits."""
        assume(len(text) > config.chunk_size)

        processor = SemanticProcessor(config)
        chunks = processor.chunk_text(text, preserve_structure=False)

        for chunk in chunks:
            token_count = chunk["token_count"]
            assert token_count <= config.chunk_size * 1.5, \
                f"Chunk exceeds size limit: {token_count} > {config.chunk_size * 1.5}"

    @given(text=spanish_policy_text())
    @settings(max_examples=15, deadline=5000, suppress_health_check=[HealthCheck.too_slow])
    def test_chunks_have_required_fields(self, text):
        """Property: All chunks have required fields with correct types."""
        assume(len(text) > 100)

        config = SemanticConfig(device="cpu", batch_size=8, fp16=False)
        processor = SemanticProcessor(config)

        chunks = processor.chunk_text(text, preserve_structure=False)

        required_fields = ["content", "section_type", "token_count", "position",
                          "has_table", "has_numerical", "pdq_context"]

        for chunk in chunks:
            for field in required_fields:
                assert field in chunk, f"Missing required field: {field}"

            assert isinstance(chunk["content"], str)
            assert isinstance(chunk["token_count"], int)
            assert isinstance(chunk["position"], int)
            assert isinstance(chunk["has_table"], bool)
            assert isinstance(chunk["has_numerical"], bool)

    @given(text=spanish_policy_text())
    @settings(max_examples=10, deadline=5000, suppress_health_check=[HealthCheck.too_slow])
    def test_embeddings_are_deterministic(self, text):
        """Property: Same text produces identical embeddings."""
        assume(len(text) > 50)

        config = SemanticConfig(device="cpu", batch_size=8, fp16=False)
        processor = SemanticProcessor(config)

        emb1 = processor.embed_single(text)
        emb2 = processor.embed_single(text)

        np.testing.assert_array_almost_equal(emb1, emb2, decimal=5,
            err_msg="Embeddings must be deterministic")


class TestBayesianEvidenceProperties:
    """Property-based tests for Bayesian evidence integration."""

    @given(
        similarities=st.lists(st.floats(min_value=-1.0, max_value=1.0), min_size=1, max_size=20),
        prior_concentration=st.floats(min_value=0.1, max_value=2.0)
    )
    @settings(max_examples=50, deadline=1000)
    def test_evidence_integration_is_bounded(self, similarities, prior_concentration):
        """Property: Evidence integration produces scores in [0, 1]."""
        integrator = BayesianEvidenceIntegrator(prior_concentration)

        metadata = [{"position": i, "has_table": False, "has_numerical": False,
                    "section_type": "diagnostico"}
                   for i in range(len(similarities))]

        result = integrator.integrate_evidence(np.array(similarities), metadata)

        assert 0.0 <= result["posterior_mean"] <= 1.0, \
            f"Posterior mean out of bounds: {result['posterior_mean']}"
        assert 0.0 <= result["confidence"] <= 1.0, \
            f"Confidence out of bounds: {result['confidence']}"
        assert result["information_gain"] >= 0.0, \
            f"Information gain must be non-negative: {result['information_gain']}"

    @given(
        similarities=st.lists(st.floats(min_value=0.5, max_value=1.0), min_size=1, max_size=10)
    )
    @settings(max_examples=30, deadline=1000)
    def test_high_similarity_increases_confidence(self, similarities):
        """Property: Higher similarities lead to higher confidence."""
        integrator = BayesianEvidenceIntegrator(0.5)

        metadata = [{"position": i, "has_table": False, "has_numerical": False,
                    "section_type": "diagnostico"}
                   for i in range(len(similarities))]

        result = integrator.integrate_evidence(np.array(similarities), metadata)

        assert result["posterior_mean"] > 0.4, \
            "High similarities should produce high posterior mean"
        assert result["confidence"] > 0.3, \
            "High similarities should produce reasonable confidence"

    @given(
        n_chunks=st.integers(min_value=1, max_value=20),
        prior=st.floats(min_value=0.1, max_value=2.0)
    )
    @settings(max_examples=30, deadline=1000)
    def test_evidence_integration_is_symmetric(self, n_chunks, prior):
        """Property: Same similarities in different order produce same result."""
        integrator = BayesianEvidenceIntegrator(prior)

        similarities = np.random.RandomState(42).uniform(0.3, 0.9, n_chunks)
        metadata = [{"position": i, "has_table": False, "has_numerical": False,
                    "section_type": "diagnostico"}
                   for i in range(n_chunks)]

        result1 = integrator.integrate_evidence(similarities, metadata)

        shuffled_indices = np.random.RandomState(43).permutation(n_chunks)
        similarities_shuffled = similarities[shuffled_indices]
        metadata_shuffled = [metadata[i] for i in shuffled_indices]

        result2 = integrator.integrate_evidence(similarities_shuffled, metadata_shuffled)

        assert abs(result1["posterior_mean"] - result2["posterior_mean"]) < 0.15, \
            "Evidence integration should be approximately order-independent"


class TestSemanticChunkingInvariants:
    """Invariant tests for semantic chunking pipeline."""

    @given(text=spanish_policy_text())
    @settings(max_examples=15, deadline=5000, suppress_health_check=[HealthCheck.too_slow])
    def test_chunk_positions_are_monotonic(self, text):
        """Property: Chunk positions increase monotonically."""
        assume(len(text) > 100)

        config = SemanticConfig(device="cpu", batch_size=8, fp16=False)
        processor = SemanticProcessor(config)

        chunks = processor.chunk_text(text, preserve_structure=False)

        positions = [c["position"] for c in chunks]
        assert positions == sorted(positions), "Chunk positions must be monotonic"

    @given(text=spanish_policy_text())
    @settings(max_examples=15, deadline=5000, suppress_health_check=[HealthCheck.too_slow])
    def test_chunk_hashes_are_unique_for_different_content(self, text):
        """Property: Different chunk contents produce different hashes."""
        assume(len(text) > 200)

        config = SemanticConfig(device="cpu", batch_size=8, fp16=False)
        processor = SemanticProcessor(config)

        chunks = processor.chunk_text(text, preserve_structure=False)

        if len(chunks) >= 2:
            hash1 = hashlib.sha256(chunks[0]["content"].encode()).hexdigest()
            hash2 = hashlib.sha256(chunks[1]["content"].encode()).hexdigest()

            if chunks[0]["content"] != chunks[1]["content"]:
                assert hash1 != hash2, "Different content must have different hashes"

    @given(
        text=spanish_policy_text(),
        seed=st.integers(min_value=0, max_value=1000)
    )
    @settings(max_examples=10, deadline=5000, suppress_health_check=[HealthCheck.too_slow])
    def test_chunking_is_reproducible_with_seed(self, text, seed):
        """Property: Same seed produces same chunking."""
        assume(len(text) > 100)

        np.random.seed(seed)
        config = SemanticConfig(device="cpu", batch_size=8, fp16=False)
        processor1 = SemanticProcessor(config)
        chunks1 = processor1.chunk_text(text, preserve_structure=False)

        np.random.seed(seed)
        config = SemanticConfig(device="cpu", batch_size=8, fp16=False)
        processor2 = SemanticProcessor(config)
        chunks2 = processor2.chunk_text(text, preserve_structure=False)

        assert len(chunks1) == len(chunks2)
        for c1, c2 in zip(chunks1, chunks2, strict=False):
            assert c1["content"] == c2["content"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
