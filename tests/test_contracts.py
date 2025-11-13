"""
CONTRACT TESTS - API Boundary Validation
=========================================

Tests that verify API contracts are maintained across module boundaries.
Every public function/class gets a test that validates documented input/output shapes.

If a signature or schema drifts, the contract test breaks before production does.

NOTE: This test file is OUTDATED. Use test_contracts_comprehensive.py instead.
"""

from typing import Any

import pytest

# Mark all tests in this module as outdated
pytestmark = pytest.mark.skip(reason="outdated - use test_contracts_comprehensive.py")

from saaaaaa.contracts import (
    MISSING,
    AnalysisInputV1,
    AnalysisOutputV1,
    DocumentMetadataV1,
    ProcessedTextV1,
    SentenceCollection,
    TextDocument,
    ensure_hashable,
    ensure_iterable_not_string,
    validate_contract,
    validate_mapping_keys,
)

class TestContractValidation:
    """Test runtime contract validation helpers."""

    def test_validate_contract_success(self) -> None:
        """Validate contract passes for correct type."""
        validate_contract(
            "hello",
            str,
            parameter="text",
            producer="test",
            consumer="validator",
        )

    def test_validate_contract_failure(self) -> None:
        """Validate contract raises TypeError for wrong type."""
        with pytest.raises(TypeError, match="ERR_CONTRACT_MISMATCH"):
            validate_contract(
                123,
                str,
                parameter="text",
                producer="test",
                consumer="validator",
            )

    def test_validate_mapping_keys_success(self) -> None:
        """Validate mapping with all required keys."""
        mapping: dict[str, Any] = {"key1": "val1", "key2": "val2"}
        validate_mapping_keys(
            mapping,
            ["key1", "key2"],
            producer="test",
            consumer="validator",
        )

    def test_validate_mapping_keys_failure(self) -> None:
        """Validate mapping raises KeyError for missing keys."""
        mapping: dict[str, Any] = {"key1": "val1"}
        with pytest.raises(KeyError, match="ERR_CONTRACT_MISMATCH.*missing_keys"):
            validate_mapping_keys(
                mapping,
                ["key1", "key2"],
                producer="test",
                consumer="validator",
            )

    def test_ensure_iterable_not_string_success(self) -> None:
        """Validate iterable that is not string passes."""
        ensure_iterable_not_string(
            [1, 2, 3],
            parameter="items",
            producer="test",
            consumer="validator",
        )

    def test_ensure_iterable_not_string_rejects_string(self) -> None:
        """Validate iterable check rejects strings."""
        with pytest.raises(TypeError, match="ERR_CONTRACT_MISMATCH.*not str/bytes"):
            ensure_iterable_not_string(
                "string",
                parameter="items",
                producer="test",
                consumer="validator",
            )

    def test_ensure_iterable_not_string_rejects_bool(self) -> None:
        """Validate iterable check rejects non-iterables like bool."""
        with pytest.raises(TypeError, match="ERR_CONTRACT_MISMATCH"):
            ensure_iterable_not_string(
                True,
                parameter="items",
                producer="test",
                consumer="validator",
            )

    def test_ensure_hashable_success(self) -> None:
        """Validate hashable check passes for hashable types."""
        ensure_hashable(
            "string",
            parameter="key",
            producer="test",
            consumer="validator",
        )
        ensure_hashable(
            123,
            parameter="key",
            producer="test",
            consumer="validator",
        )
        ensure_hashable(
            (1, 2, 3),
            parameter="key",
            producer="test",
            consumer="validator",
        )

    def test_ensure_hashable_rejects_dict(self) -> None:
        """Validate hashable check rejects dicts."""
        with pytest.raises(TypeError, match="ERR_CONTRACT_MISMATCH.*unhashable"):
            ensure_hashable(
                {"key": "value"},
                parameter="key",
                producer="test",
                consumer="validator",
            )

    def test_ensure_hashable_rejects_list(self) -> None:
        """Validate hashable check rejects lists."""
        with pytest.raises(TypeError, match="ERR_CONTRACT_MISMATCH.*unhashable"):
            ensure_hashable(
                [1, 2, 3],
                parameter="key",
                producer="test",
                consumer="validator",
            )

class TestValueObjects:
    """Test value objects that prevent type confusion."""

    def test_text_document_creation(self) -> None:
        """TextDocument can be created with valid inputs."""
        doc = TextDocument(
            text="Hello world",
            document_id="doc123",
            metadata={},
        )
        assert doc.text == "Hello world"
        assert doc.document_id == "doc123"

    def test_text_document_rejects_non_string_text(self) -> None:
        """TextDocument rejects non-string text."""
        with pytest.raises(TypeError, match="ERR_CONTRACT_MISMATCH.*text must be str"):
            TextDocument(
                text=123,  # type: ignore[arg-type]
                document_id="doc123",
                metadata={},
            )

    def test_text_document_rejects_empty_text(self) -> None:
        """TextDocument rejects empty text."""
        with pytest.raises(ValueError, match="ERR_CONTRACT_MISMATCH.*cannot be empty"):
            TextDocument(
                text="",
                document_id="doc123",
                metadata={},
            )

    def test_text_document_is_frozen(self) -> None:
        """TextDocument is immutable."""
        doc = TextDocument(text="Hello", document_id="doc123", metadata={})
        with pytest.raises(AttributeError):
            doc.text = "World"  # type: ignore[misc]

    def test_sentence_collection_creation(self) -> None:
        """SentenceCollection can be created with valid sentences."""
        sentences = SentenceCollection(sentences=("Hello", "World"))
        assert len(sentences) == 2
        assert list(sentences) == ["Hello", "World"]

    def test_sentence_collection_rejects_non_strings(self) -> None:
        """SentenceCollection rejects non-string items."""
        with pytest.raises(TypeError, match="ERR_CONTRACT_MISMATCH.*must be strings"):
            SentenceCollection(sentences=(123, 456))  # type: ignore[arg-type]

    def test_sentence_collection_is_hashable(self) -> None:
        """SentenceCollection can be used in sets and as dict keys."""
        s1 = SentenceCollection(sentences=("Hello",))
        s2 = SentenceCollection(sentences=("World",))

        # Can add to set
        sentence_set = {s1, s2}
        assert len(sentence_set) == 2

        # Can use as dict key
        mapping = {s1: "first", s2: "second"}
        assert mapping[s1] == "first"

class TestSentinelValues:
    """Test MISSING sentinel for optional parameters."""

    def test_missing_sentinel_identity(self) -> None:
        """MISSING has identity semantics."""
        from saaaaaa.contracts import MISSING as MISSING2
        assert MISSING is MISSING2

    def test_missing_sentinel_not_none(self) -> None:
        """MISSING is distinguishable from None."""
        assert MISSING is not None
        assert MISSING != None  # noqa: E711

    def test_missing_sentinel_repr(self) -> None:
        """MISSING has readable repr."""
        assert repr(MISSING) == "<MISSING>"

class TestTypedDictContracts:
    """Test TypedDict definitions for data shapes."""

    def test_document_metadata_v1_required_fields(self) -> None:
        """DocumentMetadataV1 requires all fields."""
        metadata: DocumentMetadataV1 = {
            "file_path": "/path/to/file.pdf",
            "file_name": "file.pdf",
            "num_pages": 10,
            "file_size_bytes": 1024,
            "file_hash": "abc123",
        }
        assert metadata["file_path"] == "/path/to/file.pdf"
        assert metadata["num_pages"] == 10

    def test_processed_text_v1_shape(self) -> None:
        """ProcessedTextV1 has correct shape."""
        text: ProcessedTextV1 = {
            "raw_text": "Hello world",
            "normalized_text": "hello world",
            "language": "es",
            "encoding": "utf-8",
        }
        assert text["language"] == "es"

    def test_analysis_input_v1_keyword_only_semantics(self) -> None:
        """AnalysisInputV1 is designed for keyword-only usage."""
        # Should be used with keyword args
        input_data: AnalysisInputV1 = {
            "text": "Sample text",
            "document_id": "doc123",
        }
        assert input_data["text"] == "Sample text"

    def test_analysis_output_v1_shape(self) -> None:
        """AnalysisOutputV1 has correct output shape."""
        output: AnalysisOutputV1 = {
            "dimension": "D1",
            "category": "insumos",
            "confidence": 0.85,
            "matches": ["palabra1", "palabra2"],
        }
        assert output["confidence"] == 0.85
        assert len(output["matches"]) == 2

@pytest.mark.contract
class TestDocumentIngestionContracts:
    """Contract tests for document ingestion module boundaries."""

    def test_document_loader_protocol_signature(self) -> None:
        """DocumentLoader.load_pdf must use keyword-only params."""
        import inspect

        from saaaaaa.contracts import DocumentLoaderProtocol

        # Check protocol signature
        sig = inspect.signature(DocumentLoaderProtocol.load_pdf)
        params = list(sig.parameters.values())

        # First param is self, second should be KEYWORD_ONLY
        assert len(params) >= 2
        # pdf_path should be keyword-only
        pdf_path_param = [p for p in params if p.name == "pdf_path"][0]
        assert pdf_path_param.kind == inspect.Parameter.KEYWORD_ONLY

@pytest.mark.contract
class TestAnalyzerContracts:
    """Contract tests for analyzer module boundaries."""

    def test_analyzer_protocol_keyword_only(self) -> None:
        """Analyzer.analyze must use keyword-only params."""
        import inspect

        from saaaaaa.contracts import AnalyzerProtocol

        sig = inspect.signature(AnalyzerProtocol.analyze)
        params = list(sig.parameters.values())

        # All params except self should be keyword-only
        for param in params[1:]:  # Skip self
            assert param.kind in (
                inspect.Parameter.KEYWORD_ONLY,
                inspect.Parameter.VAR_KEYWORD,
            )

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
