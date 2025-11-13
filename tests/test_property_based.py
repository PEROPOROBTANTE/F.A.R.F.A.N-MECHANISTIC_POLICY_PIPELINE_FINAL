"""
PROPERTY-BASED TESTS - Fuzz the Seams
======================================

Uses Hypothesis to generate dicts with missing/extra keys, wrong types,
and empty/None cases for producer→consumer paths.

Shrinking hands us minimal counterexamples that we staple to bug fixes.
"""

from typing import Any

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from saaaaaa.contracts import (
    SentenceCollection,
    TextDocument,
    ensure_hashable,
    ensure_iterable_not_string,
    validate_contract,
    validate_mapping_keys,
)

# ============================================================================
# STRATEGIES - Generate Test Data
# ============================================================================

@st.composite
def valid_text_strategy(draw: Any) -> str:
    """Generate valid non-empty text strings."""
    text = draw(st.text(min_size=1, max_size=1000))
    assume(text.strip())  # Must have non-whitespace content
    return text

@st.composite
def metadata_dict_strategy(draw: Any) -> dict[str, Any]:
    """Generate metadata dictionaries with various shapes."""
    return draw(st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=st.one_of(
            st.text(),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.booleans(),
            st.none(),
        ),
        min_size=0,
        max_size=10,
    ))

@st.composite
def malformed_mapping_strategy(draw: Any) -> dict[str, Any]:
    """Generate mappings that might be missing required keys."""
    base_keys = ["text", "document_id", "metadata"]
    # Randomly drop keys
    available_keys = draw(st.lists(
        st.sampled_from(base_keys),
        min_size=0,
        max_size=len(base_keys),
        unique=True,
    ))

    return {
        key: draw(st.text())
        for key in available_keys
    }

# ============================================================================
# PROPERTY TESTS - TextDocument
# ============================================================================

@pytest.mark.property
class TestTextDocumentProperties:
    """Property-based tests for TextDocument value object."""

    @given(
        text=valid_text_strategy(),
        document_id=st.text(min_size=1, max_size=100),
        metadata=metadata_dict_strategy(),
    )
    def test_text_document_roundtrip(
        self,
        text: str,
        document_id: str,
        metadata: dict[str, Any],
    ) -> None:
        """TextDocument preserves all input data."""
        doc = TextDocument(text=text, document_id=document_id, metadata=metadata)

        assert doc.text == text
        assert doc.document_id == document_id
        # metadata is converted to immutable but content preserved
        assert dict(doc.metadata) == metadata

    @given(
        text=st.one_of(st.integers(), st.lists(st.text()), st.none()),
        document_id=st.text(min_size=1),
        metadata=metadata_dict_strategy(),
    )
    def test_text_document_rejects_invalid_text(
        self,
        text: Any,
        document_id: str,
        metadata: dict[str, Any],
    ) -> None:
        """TextDocument rejects non-string text."""
        with pytest.raises(TypeError):
            TextDocument(text=text, document_id=document_id, metadata=metadata)

    @given(
        document_id=st.text(min_size=1),
        metadata=metadata_dict_strategy(),
    )
    def test_text_document_rejects_empty_text(
        self,
        document_id: str,
        metadata: dict[str, Any],
    ) -> None:
        """TextDocument rejects empty text."""
        with pytest.raises(ValueError):
            TextDocument(text="", document_id=document_id, metadata=metadata)

# ============================================================================
# PROPERTY TESTS - SentenceCollection
# ============================================================================

@pytest.mark.property
class TestSentenceCollectionProperties:
    """Property-based tests for SentenceCollection."""

    @given(
        sentences=st.lists(st.text(min_size=1, max_size=100), min_size=0, max_size=50),
    )
    def test_sentence_collection_iteration(self, sentences: list[str]) -> None:
        """SentenceCollection iteration matches input order."""
        collection = SentenceCollection(sentences=tuple(sentences))

        assert list(collection) == sentences
        assert len(collection) == len(sentences)

    @given(
        sentences1=st.lists(st.text(min_size=1), min_size=1, max_size=10, unique=True),
        sentences2=st.lists(st.text(min_size=1), min_size=1, max_size=10, unique=True),
    )
    def test_sentence_collection_equality(
        self,
        sentences1: list[str],
        sentences2: list[str],
    ) -> None:
        """SentenceCollections with same sentences are equal."""
        c1 = SentenceCollection(sentences=tuple(sentences1))
        c2 = SentenceCollection(sentences=tuple(sentences1))
        c3 = SentenceCollection(sentences=tuple(sentences2))

        assert c1 == c2
        if sentences1 != sentences2:
            assert c1 != c3

    @given(
        sentences=st.lists(
            st.one_of(st.integers(), st.booleans(), st.none()),
            min_size=1,
            max_size=10,
        ),
    )
    def test_sentence_collection_rejects_non_strings(
        self,
        sentences: list[Any],
    ) -> None:
        """SentenceCollection rejects non-string items."""
        with pytest.raises(TypeError):
            SentenceCollection(sentences=tuple(sentences))

# ============================================================================
# PROPERTY TESTS - Contract Validation
# ============================================================================

@pytest.mark.property
class TestContractValidationProperties:
    """Property-based tests for runtime contract validation."""

    @given(
        value=st.text(),
    )
    def test_validate_contract_accepts_matching_type(self, value: str) -> None:
        """validate_contract accepts values of expected type."""
        validate_contract(
            value,
            str,
            parameter="test",
            producer="hypothesis",
            consumer="validator",
        )

    @given(
        value=st.one_of(st.integers(), st.lists(st.text()), st.booleans()),
    )
    def test_validate_contract_rejects_wrong_type(self, value: Any) -> None:
        """validate_contract rejects values of wrong type."""
        with pytest.raises(TypeError, match="ERR_CONTRACT_MISMATCH"):
            validate_contract(
                value,
                str,
                parameter="test",
                producer="hypothesis",
                consumer="validator",
            )

    @given(
        mapping=malformed_mapping_strategy(),
    )
    def test_validate_mapping_keys_finds_missing(
        self,
        mapping: dict[str, Any],
    ) -> None:
        """validate_mapping_keys detects missing required keys."""
        required = ["text", "document_id", "metadata"]

        if all(key in mapping for key in required):
            # Should pass
            validate_mapping_keys(
                mapping,
                required,
                producer="hypothesis",
                consumer="validator",
            )
        else:
            # Should fail
            with pytest.raises(KeyError, match="ERR_CONTRACT_MISMATCH"):
                validate_mapping_keys(
                    mapping,
                    required,
                    producer="hypothesis",
                    consumer="validator",
                )

    @given(
        value=st.lists(st.integers(), min_size=0, max_size=100),
    )
    def test_ensure_iterable_accepts_lists(self, value: list[int]) -> None:
        """ensure_iterable_not_string accepts list iterables."""
        ensure_iterable_not_string(
            value,
            parameter="items",
            producer="hypothesis",
            consumer="validator",
        )

    @given(
        value=st.text(min_size=0, max_size=100),
    )
    def test_ensure_iterable_rejects_strings(self, value: str) -> None:
        """ensure_iterable_not_string rejects string iterables."""
        with pytest.raises(TypeError, match="ERR_CONTRACT_MISMATCH.*not str"):
            ensure_iterable_not_string(
                value,
                parameter="items",
                producer="hypothesis",
                consumer="validator",
            )

    @given(
        value=st.one_of(st.booleans(), st.integers(), st.floats()),
    )
    def test_ensure_iterable_rejects_non_iterables(self, value: Any) -> None:
        """ensure_iterable_not_string rejects non-iterables."""
        with pytest.raises(TypeError, match="ERR_CONTRACT_MISMATCH"):
            ensure_iterable_not_string(
                value,
                parameter="items",
                producer="hypothesis",
                consumer="validator",
            )

    @given(
        value=st.one_of(
            st.text(),
            st.integers(),
            st.booleans(),
            st.tuples(st.integers(), st.integers()),
        ),
    )
    def test_ensure_hashable_accepts_hashables(self, value: Any) -> None:
        """ensure_hashable accepts hashable values."""
        ensure_hashable(
            value,
            parameter="key",
            producer="hypothesis",
            consumer="validator",
        )

    @given(
        value=st.one_of(
            st.lists(st.integers()),
            st.dictionaries(st.text(), st.integers()),
        ),
    )
    def test_ensure_hashable_rejects_unhashables(self, value: Any) -> None:
        """ensure_hashable rejects unhashable values."""
        with pytest.raises(TypeError, match="ERR_CONTRACT_MISMATCH.*unhashable"):
            ensure_hashable(
                value,
                parameter="key",
                producer="hypothesis",
                consumer="validator",
            )

# ============================================================================
# PROPERTY TESTS - Edge Cases
# ============================================================================

@pytest.mark.property
class TestEdgeCases:
    """Property-based tests for edge cases and boundary conditions."""

    @given(
        mapping=st.dictionaries(
            keys=st.text(),
            values=st.one_of(st.none(), st.text(), st.integers()),
            min_size=0,
            max_size=100,
        ),
    )
    def test_empty_and_large_mappings(self, mapping: dict[str, Any]) -> None:
        """Contract validation works with empty and large mappings."""
        # Should not crash
        keys = list(mapping.keys())[:3]  # Take up to 3 keys

        if all(k in mapping for k in keys):
            validate_mapping_keys(
                mapping,
                keys,
                producer="hypothesis",
                consumer="test",
            )

    @given(
        sentences=st.lists(
            st.text(min_size=0, max_size=1000),
            min_size=0,
            max_size=100,
        ),
    )
    def test_empty_and_large_sentence_collections(
        self,
        sentences: list[str],
    ) -> None:
        """SentenceCollection handles empty and large inputs."""
        # Filter to valid strings only
        valid_sentences = [s for s in sentences if isinstance(s, str)]
        collection = SentenceCollection(sentences=tuple(valid_sentences))

        assert len(collection) == len(valid_sentences)
        assert list(collection) == valid_sentences

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
