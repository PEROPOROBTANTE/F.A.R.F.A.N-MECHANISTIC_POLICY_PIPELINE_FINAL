"""
Property-Based Tests for SPC Ingestion Pipeline Idempotency

Verifies that the SPC ingestion pipeline is idempotent, meaning running
it multiple times on the same input produces identical results.
"""

import hashlib
import json

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from src.farfan_pipeline.processing.spc_ingestion import StrategicChunkingSystem


@st.composite
def minimal_policy_document(draw):
    """Generate minimal valid policy documents for testing."""
    title = draw(st.text(min_size=10, max_size=100))
    content_paragraphs = draw(st.lists(
        st.text(min_size=50, max_size=300),
        min_size=3,
        max_size=10
    ))
    content = "\n\n".join(content_paragraphs)

    return {
        "doc_id": draw(st.text(alphabet=st.characters(whitelist_categories=('L', 'N')),
                              min_size=5, max_size=20)),
        "title": title,
        "content": content
    }


class TestSPCIngestionIdempotency:
    """Property-based tests for SPC ingestion idempotency."""

    @given(doc=minimal_policy_document())
    @settings(max_examples=10, deadline=10000, suppress_health_check=[HealthCheck.too_slow])
    def test_ingestion_is_idempotent(self, doc):
        """Property: Running ingestion twice produces identical results."""
        assume(len(doc["content"]) > 200)

        system = StrategicChunkingSystem()

        result1 = system.process_document(doc["content"], {
            "doc_id": doc["doc_id"],
            "title": doc["title"]
        })

        result2 = system.process_document(doc["content"], {
            "doc_id": doc["doc_id"],
            "title": doc["title"]
        })

        assert len(result1) == len(result2), "Chunk count must be identical"

        for i, (c1, c2) in enumerate(zip(result1, result2, strict=False)):
            c1_text = system.get_chunk_text(c1)
            c2_text = system.get_chunk_text(c2)
            assert c1_text == c2_text, f"Chunk {i} content differs"

    @given(doc=minimal_policy_document())
    @settings(max_examples=10, deadline=10000, suppress_health_check=[HealthCheck.too_slow])
    def test_chunk_hashes_are_stable(self, doc):
        """Property: Chunk hashes remain stable across runs."""
        assume(len(doc["content"]) > 200)

        system = StrategicChunkingSystem()

        result1 = system.process_document(doc["content"], {
            "doc_id": doc["doc_id"],
            "title": doc["title"]
        })

        result2 = system.process_document(doc["content"], {
            "doc_id": doc["doc_id"],
            "title": doc["title"]
        })

        for c1, c2 in zip(result1, result2, strict=False):
            c1_text = system.get_chunk_text(c1)
            c2_text = system.get_chunk_text(c2)

            hash1 = hashlib.sha256(c1_text.encode()).hexdigest()
            hash2 = hashlib.sha256(c2_text.encode()).hexdigest()

            assert hash1 == hash2, "Chunk hashes must be stable"

    @given(doc=minimal_policy_document())
    @settings(max_examples=10, deadline=10000, suppress_health_check=[HealthCheck.too_slow])
    def test_metadata_is_consistent(self, doc):
        """Property: Chunk metadata is consistent across runs."""
        assume(len(doc["content"]) > 200)

        system = StrategicChunkingSystem()

        result1 = system.process_document(doc["content"], {
            "doc_id": doc["doc_id"],
            "title": doc["title"]
        })

        result2 = system.process_document(doc["content"], {
            "doc_id": doc["doc_id"],
            "title": doc["title"]
        })

        for c1, c2 in zip(result1, result2, strict=False):
            meta1 = system.get_chunk_metadata(c1)
            meta2 = system.get_chunk_metadata(c2)

            assert meta1["document_id"] == meta2["document_id"]
            assert meta1["has_table"] == meta2["has_table"]
            assert meta1["has_list"] == meta2["has_list"]
            assert meta1["has_numbers"] == meta2["has_numbers"]

    @given(doc=minimal_policy_document())
    @settings(max_examples=8, deadline=15000, suppress_health_check=[HealthCheck.too_slow])
    def test_pdq_context_inference_is_stable(self, doc):
        """Property: PDQ context inference is stable across runs."""
        assume(len(doc["content"]) > 200)

        system = StrategicChunkingSystem()

        result1 = system.process_document(doc["content"], {
            "doc_id": doc["doc_id"],
            "title": doc["title"]
        })

        result2 = system.process_document(doc["content"], {
            "doc_id": doc["doc_id"],
            "title": doc["title"]
        })

        for c1, c2 in zip(result1, result2, strict=False):
            ctx1 = system.get_chunk_pdq_context(c1)
            ctx2 = system.get_chunk_pdq_context(c2)

            if ctx1 is not None and ctx2 is not None:
                assert ctx1["policy"] == ctx2["policy"]
                assert ctx1["dimension"] == ctx2["dimension"]


class TestSPCIngestionInvariants:
    """Invariant tests for SPC ingestion pipeline."""

    @given(doc=minimal_policy_document())
    @settings(max_examples=10, deadline=10000, suppress_health_check=[HealthCheck.too_slow])
    def test_chunks_cover_all_content(self, doc):
        """Property: Chunks collectively cover all important content."""
        assume(len(doc["content"]) > 200)

        system = StrategicChunkingSystem()

        chunks = system.process_document(doc["content"], {
            "doc_id": doc["doc_id"],
            "title": doc["title"]
        })

        all_chunk_text = " ".join(system.get_chunk_text(c) for c in chunks)

        important_words = set()
        for word in doc["content"].split():
            if len(word) > 5:
                important_words.add(word.lower())

        coverage = sum(1 for word in important_words
                      if word in all_chunk_text.lower())

        coverage_ratio = coverage / max(len(important_words), 1)
        assert coverage_ratio > 0.7, \
            f"Chunks must cover at least 70% of important words: {coverage_ratio:.2%}"

    @given(doc=minimal_policy_document())
    @settings(max_examples=10, deadline=10000, suppress_health_check=[HealthCheck.too_slow])
    def test_chunks_have_minimum_quality(self, doc):
        """Property: All chunks meet minimum quality thresholds."""
        assume(len(doc["content"]) > 200)

        system = StrategicChunkingSystem()

        chunks = system.process_document(doc["content"], {
            "doc_id": doc["doc_id"],
            "title": doc["title"]
        })

        for chunk in chunks:
            text = system.get_chunk_text(chunk)

            assert len(text) >= 20, f"Chunk too short: {len(text)} chars"

            assert text.strip(), "Chunk must not be empty"

            words = text.split()
            assert len(words) >= 5, f"Chunk has too few words: {len(words)}"

    @given(doc=minimal_policy_document())
    @settings(max_examples=10, deadline=10000, suppress_health_check=[HealthCheck.too_slow])
    def test_chunk_boundaries_dont_duplicate_content(self, doc):
        """Property: Chunks don't have excessive duplication."""
        assume(len(doc["content"]) > 200)

        system = StrategicChunkingSystem()

        chunks = system.process_document(doc["content"], {
            "doc_id": doc["doc_id"],
            "title": doc["title"]
        })

        if len(chunks) >= 2:
            for i in range(len(chunks) - 1):
                text1 = system.get_chunk_text(chunks[i])
                text2 = system.get_chunk_text(chunks[i + 1])

                words1 = set(text1.lower().split())
                words2 = set(text2.lower().split())

                if words1 and words2:
                    overlap = len(words1 & words2) / max(len(words1), len(words2))
                    assert overlap < 0.8, \
                        f"Excessive overlap between chunks {i} and {i+1}: {overlap:.2%}"


class TestSPCIngestionCorrectness:
    """Correctness properties for SPC ingestion."""

    @given(doc=minimal_policy_document())
    @settings(max_examples=10, deadline=10000, suppress_health_check=[HealthCheck.too_slow])
    def test_document_id_propagates_to_chunks(self, doc):
        """Property: Document ID is preserved in all chunks."""
        assume(len(doc["content"]) > 200)

        system = StrategicChunkingSystem()

        chunks = system.process_document(doc["content"], {
            "doc_id": doc["doc_id"],
            "title": doc["title"]
        })

        for chunk in chunks:
            meta = system.get_chunk_metadata(chunk)
            assert meta["document_id"] == doc["doc_id"], \
                "Document ID must propagate to all chunks"

    @given(
        doc=minimal_policy_document(),
        run_count=st.integers(min_value=2, max_value=4)
    )
    @settings(max_examples=5, deadline=20000, suppress_health_check=[HealthCheck.too_slow])
    def test_multiple_runs_produce_identical_output(self, doc, run_count):
        """Property: Multiple runs produce bit-for-bit identical output."""
        assume(len(doc["content"]) > 200)

        system = StrategicChunkingSystem()

        results = []
        for _ in range(run_count):
            chunks = system.process_document(doc["content"], {
                "doc_id": doc["doc_id"],
                "title": doc["title"]
            })

            serialized = json.dumps([
                {
                    "text": system.get_chunk_text(c),
                    "metadata": system.get_chunk_metadata(c)
                }
                for c in chunks
            ], sort_keys=True)

            results.append(hashlib.sha256(serialized.encode()).hexdigest())

        assert len(set(results)) == 1, \
            f"Multiple runs produced different outputs: {results}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
