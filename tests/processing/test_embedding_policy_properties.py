"""
Property-Based Tests for Embedding Policy Consistency

Verifies that embedding generation is consistent, deterministic, and maintains
mathematical properties expected from embeddings.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st
from scipy.spatial.distance import cosine

from src.farfan_pipeline.processing.embedding_policy import (
    AdvancedSemanticChunker,
    BayesianNumericalAnalyzer,
    ChunkingConfig,
)


@st.composite
def valid_text(draw):
    """Generate valid text for embedding."""
    return draw(st.text(
        alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z')),
        min_size=20,
        max_size=500
    ))


@st.composite
def chunking_config(draw):
    """Generate valid ChunkingConfig instances."""
    chunk_size = draw(st.integers(min_value=128, max_value=1024))
    return ChunkingConfig(
        chunk_size=chunk_size,
        chunk_overlap=draw(st.integers(min_value=16, max_value=chunk_size // 2)),
        min_chunk_size=draw(st.integers(min_value=32, max_value=chunk_size // 4)),
        respect_boundaries=draw(st.booleans()),
        preserve_tables=draw(st.booleans()),
        detect_lists=draw(st.booleans()),
        section_aware=draw(st.booleans())
    )


class TestEmbeddingConsistency:
    """Property-based tests for embedding consistency."""

    @given(text=valid_text())
    @settings(max_examples=20, deadline=3000, suppress_health_check=[HealthCheck.too_slow])
    def test_embedding_dimensions_are_consistent(self, text):
        """Property: All embeddings have consistent dimensions."""
        assume(len(text) > 50)

        config = ChunkingConfig()
        chunker = AdvancedSemanticChunker(config)

        chunks = chunker.chunk_document(
            text=text,
            document_metadata={"doc_id": "test_doc"}
        )

        if len(chunks) > 0 and len(chunks[0].get("embedding", [])) > 0:
            expected_dim = len(chunks[0]["embedding"])

            for chunk in chunks:
                if len(chunk.get("embedding", [])) > 0:
                    assert len(chunk["embedding"]) == expected_dim, \
                        "All embeddings must have same dimension"

    @given(
        text=valid_text(),
        seed=st.integers(min_value=0, max_value=1000)
    )
    @settings(max_examples=15, deadline=5000, suppress_health_check=[HealthCheck.too_slow])
    def test_embeddings_are_deterministic(self, text, seed):
        """Property: Same text produces same embeddings."""
        assume(len(text) > 50)

        np.random.seed(seed)
        config = ChunkingConfig()
        chunker1 = AdvancedSemanticChunker(config)
        chunks1 = chunker1.chunk_document(
            text=text,
            document_metadata={"doc_id": "test_doc"}
        )

        np.random.seed(seed)
        chunker2 = AdvancedSemanticChunker(config)
        chunks2 = chunker2.chunk_document(
            text=text,
            document_metadata={"doc_id": "test_doc"}
        )

        assert len(chunks1) == len(chunks2)

        for c1, c2 in zip(chunks1, chunks2, strict=False):
            emb1 = c1.get("embedding", [])
            emb2 = c2.get("embedding", [])

            if len(emb1) > 0 and len(emb2) > 0:
                np.testing.assert_array_almost_equal(emb1, emb2, decimal=4)

    @given(text=valid_text())
    @settings(max_examples=15, deadline=3000, suppress_health_check=[HealthCheck.too_slow])
    def test_embeddings_are_normalized(self, text):
        """Property: Embeddings should be unit vectors or close to it."""
        assume(len(text) > 50)

        config = ChunkingConfig()
        chunker = AdvancedSemanticChunker(config)

        chunks = chunker.chunk_document(
            text=text,
            document_metadata={"doc_id": "test_doc"}
        )

        for chunk in chunks:
            emb = chunk.get("embedding", [])
            if len(emb) > 0:
                norm = np.linalg.norm(emb)
                assert 0.8 <= norm <= 1.2, \
                    f"Embedding norm should be close to 1: {norm}"

    @given(
        text1=valid_text(),
        text2=valid_text()
    )
    @settings(max_examples=10, deadline=6000, suppress_health_check=[HealthCheck.too_slow])
    def test_similar_texts_have_similar_embeddings(self, text1, text2):
        """Property: Similar texts have similar embeddings."""
        assume(len(text1) > 50 and len(text2) > 50)

        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if len(words1) > 0 and len(words2) > 0:
            overlap = len(words1 & words2) / max(len(words1), len(words2))
            assume(overlap > 0.5)

            config = ChunkingConfig()
            chunker = AdvancedSemanticChunker(config)

            chunks1 = chunker.chunk_document(
                text=text1,
                document_metadata={"doc_id": "doc1"}
            )
            chunks2 = chunker.chunk_document(
                text=text2,
                document_metadata={"doc_id": "doc2"}
            )

            if len(chunks1) > 0 and len(chunks2) > 0:
                emb1 = chunks1[0].get("embedding", [])
                emb2 = chunks2[0].get("embedding", [])

                if len(emb1) > 0 and len(emb2) > 0:
                    similarity = 1 - cosine(emb1, emb2)
                    assert similarity > 0.2, \
                        f"Similar texts should have similar embeddings: {similarity}"


class TestChunkingConfigurationInvariants:
    """Invariant tests for chunking configuration."""

    @given(config=chunking_config())
    @settings(max_examples=30, deadline=1000)
    def test_config_invariants_hold(self, config):
        """Property: Configuration parameters maintain valid relationships."""
        assert config.chunk_size > 0, "Chunk size must be positive"
        assert config.chunk_overlap >= 0, "Overlap must be non-negative"
        assert config.chunk_overlap < config.chunk_size, \
            "Overlap must be less than chunk size"
        assert config.min_chunk_size > 0, "Min chunk size must be positive"
        assert config.min_chunk_size <= config.chunk_size, \
            "Min chunk size must not exceed max chunk size"

    @given(
        text=valid_text(),
        config=chunking_config()
    )
    @settings(max_examples=10, deadline=5000, suppress_health_check=[HealthCheck.too_slow])
    def test_chunker_respects_config(self, text, config):
        """Property: Chunker respects configuration parameters."""
        assume(len(text) > config.chunk_size)

        chunker = AdvancedSemanticChunker(config)

        chunks = chunker.chunk_document(
            text=text,
            document_metadata={"doc_id": "test_doc"}
        )

        for chunk in chunks:
            token_count = chunk.get("token_count", 0)

            if config.min_chunk_size:
                assert token_count >= config.min_chunk_size * 0.5 or len(chunks) == 1, \
                    f"Chunk smaller than min size: {token_count} < {config.min_chunk_size}"


class TestBayesianNumericalAnalyzerProperties:
    """Property-based tests for Bayesian numerical analysis."""

    @given(
        values=st.lists(st.floats(min_value=0.0, max_value=1.0), min_size=1, max_size=50),
        prior_alpha=st.floats(min_value=0.1, max_value=10.0),
        prior_beta=st.floats(min_value=0.1, max_value=10.0)
    )
    @settings(max_examples=50, deadline=1000)
    def test_bayesian_evaluation_produces_valid_credible_intervals(self, values, prior_alpha, prior_beta):
        """Property: Credible intervals are valid."""
        analyzer = BayesianNumericalAnalyzer(prior_alpha=prior_alpha, prior_beta=prior_beta)

        result = analyzer.analyze_proportion(
            successes=sum(values),
            trials=len(values),
            context="test"
        )

        lower, upper = result["credible_interval_95"]

        assert 0.0 <= lower <= 1.0, f"Lower bound out of range: {lower}"
        assert 0.0 <= upper <= 1.0, f"Upper bound out of range: {upper}"
        assert lower <= upper, f"Lower bound exceeds upper bound: {lower} > {upper}"
        assert lower <= result["point_estimate"] <= upper, \
            "Point estimate must be within credible interval"

    @given(
        successes=st.integers(min_value=0, max_value=100),
        trials=st.integers(min_value=1, max_value=100)
    )
    @settings(max_examples=50, deadline=1000)
    def test_bayesian_evaluation_is_bounded(self, successes, trials):
        """Property: Bayesian evaluation produces bounded results."""
        assume(successes <= trials)

        analyzer = BayesianNumericalAnalyzer()

        result = analyzer.analyze_proportion(
            successes=successes,
            trials=trials,
            context="test"
        )

        assert 0.0 <= result["point_estimate"] <= 1.0
        assert result["evidence_strength"] in ["weak", "moderate", "strong", "very_strong"]
        assert 0.0 <= result["numerical_coherence"] <= 1.0

    @given(
        successes=st.integers(min_value=0, max_value=100),
        trials=st.integers(min_value=1, max_value=100)
    )
    @settings(max_examples=30, deadline=1000)
    def test_more_data_reduces_uncertainty(self, successes, trials):
        """Property: More data should reduce uncertainty (narrower intervals)."""
        assume(successes <= trials and trials >= 10)

        analyzer = BayesianNumericalAnalyzer()

        result_few = analyzer.analyze_proportion(
            successes=successes // 2,
            trials=trials // 2,
            context="test"
        )

        result_many = analyzer.analyze_proportion(
            successes=successes,
            trials=trials,
            context="test"
        )

        width_few = result_few["credible_interval_95"][1] - result_few["credible_interval_95"][0]
        width_many = result_many["credible_interval_95"][1] - result_many["credible_interval_95"][0]

        assert width_many <= width_few * 1.5, \
            "More data should not significantly increase uncertainty"


class TestPDQContextInference:
    """Property-based tests for PDQ context inference."""

    @given(text=valid_text())
    @settings(max_examples=15, deadline=3000, suppress_health_check=[HealthCheck.too_slow])
    def test_pdq_context_structure_is_valid(self, text):
        """Property: PDQ context has valid structure when inferred."""
        assume(len(text) > 50)

        config = ChunkingConfig()
        chunker = AdvancedSemanticChunker(config)

        chunks = chunker.chunk_document(
            text=text,
            document_metadata={"doc_id": "test_doc"}
        )

        for chunk in chunks:
            pdq = chunk.get("pdq_context")
            if pdq is not None:
                assert "question_unique_id" in pdq
                assert "policy" in pdq
                assert "dimension" in pdq
                assert "question" in pdq
                assert "rubric_key" in pdq

                assert pdq["policy"].startswith("PA")
                assert pdq["dimension"].startswith("DIM")
                assert isinstance(pdq["question"], int)

    @given(text=valid_text())
    @settings(max_examples=10, deadline=3000, suppress_health_check=[HealthCheck.too_slow])
    def test_pdq_inference_is_stable(self, text):
        """Property: PDQ inference is stable across runs."""
        assume(len(text) > 50)

        config = ChunkingConfig()
        chunker1 = AdvancedSemanticChunker(config)
        chunker2 = AdvancedSemanticChunker(config)

        chunks1 = chunker1.chunk_document(
            text=text,
            document_metadata={"doc_id": "test_doc"}
        )
        chunks2 = chunker2.chunk_document(
            text=text,
            document_metadata={"doc_id": "test_doc"}
        )

        for c1, c2 in zip(chunks1, chunks2, strict=False):
            pdq1 = c1.get("pdq_context")
            pdq2 = c2.get("pdq_context")

            if pdq1 is not None and pdq2 is not None:
                assert pdq1["policy"] == pdq2["policy"]
                assert pdq1["dimension"] == pdq2["dimension"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
