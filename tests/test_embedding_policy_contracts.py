"""Contract and property-based tests for PolicyAnalysisEmbedder._filter_by_pdq."""

from __future__ import annotations

import logging
import sys
import types
from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

def _ensure_sentence_transformer_stub() -> None:
    """Provide a lightweight stub so embedding_policy imports without heavy deps."""

    if "sentence_transformers" in sys.modules:
        return

    stub = types.ModuleType("sentence_transformers")

    class _Stub:  # pragma: no cover - defensive stub
        def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401 - simple stub
            raise RuntimeError("SentenceTransformer stub should not be instantiated in tests")

    stub.SentenceTransformer = _Stub
    stub.CrossEncoder = _Stub
    sys.modules["sentence_transformers"] = stub

_ensure_sentence_transformer_stub()

from saaaaaa.processing.embedding_policy import PolicyAnalysisEmbedder  # noqa: E402  - imported after stub

@pytest.fixture()
def embedder_stub() -> PolicyAnalysisEmbedder:
    """Create an embedder instance without running heavy initialisation."""

    instance = PolicyAnalysisEmbedder.__new__(PolicyAnalysisEmbedder)
    instance._logger = logging.getLogger("test.PolicyAnalysisEmbedder")
    return instance

@pytest.fixture()
def pdq_filter() -> dict[str, str]:
    return {"policy": "P1", "dimension": "D1"}

def test_filter_by_pdq_contract_shape(embedder_stub: PolicyAnalysisEmbedder, pdq_filter: dict[str, str]) -> None:
    """Given documented inputs, the output remains a list of semantic chunks."""

    chunk = {
        "content": "evidence",
        "metadata": {"source": "unit-test"},
        "pdq_context": {
            "policy": "P1",
            "dimension": "D1",
            "question_unique_id": "P1-D1-Q1",
            "question": 1,
            "rubric_key": "D1-Q1",
        },
    }

    result = embedder_stub._filter_by_pdq([chunk], pdq_filter)

    assert isinstance(result, list)
    assert result == [chunk]

def test_filter_by_pdq_missing_context_logs_error(
    embedder_stub: PolicyAnalysisEmbedder, pdq_filter: dict[str, str], caplog: pytest.LogCaptureFixture
) -> None:
    """Missing pdq_context results in a standardised contract error code."""

    chunk = {"content": "irrelevant", "metadata": {}, "pdq_context": None}

    with caplog.at_level(logging.ERROR):
        result = embedder_stub._filter_by_pdq([chunk], pdq_filter)

    assert result == []
    assert (
        "ERR_CONTRACT_MISMATCH[fn=_filter_by_pdq, key='pdq_context', needed=True, got=None, index=0]"
        in caplog.text
    )

@st.composite
def chunk_strategy(draw: st.DrawFn) -> Any:
    """Generate chunk payloads covering valid, missing, and malformed contexts."""

    variant = draw(st.sampled_from(["match", "mismatch", "missing", "nondict"]))

    if variant == "nondict":
        return draw(st.one_of(st.none(), st.integers(), st.text(max_size=8)))

    chunk: dict[str, Any] = {
        "content": draw(st.text(max_size=24)),
        "metadata": {"origin": draw(st.text(max_size=8))},
    }

    if variant == "match":
        chunk["pdq_context"] = {
            "policy": "P1",
            "dimension": "D1",
            "question_unique_id": "P1-D1-Q1",
            "question": 1,
            "rubric_key": "D1-Q1",
            "extra_field": draw(st.text(max_size=6)),
        }
        return chunk

    if variant == "mismatch":
        chunk["pdq_context"] = {
            "policy": draw(st.sampled_from(["P2", "P3"])),
            "dimension": draw(st.sampled_from(["D2", "D3"])),
            "question_unique_id": draw(st.text(min_size=1, max_size=6)),
            "question": draw(st.integers(min_value=1, max_value=99)),
            "rubric_key": draw(st.text(min_size=1, max_size=6)),
            "extra": draw(st.text(max_size=4)),
        }
        return chunk

    # missing / malformed pdq_context
    chunk["pdq_context"] = draw(
        st.one_of(
            st.none(),
            st.just({}),
            st.just({"policy": "P1"}),
            st.just({"dimension": "D1"}),
            st.just({"policy": None, "dimension": "D1"}),
            st.just({"policy": "P1", "dimension": None}),
            st.text(max_size=5),
            st.integers(min_value=-1, max_value=3),
        )
    )
    return chunk

@settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[
        HealthCheck.function_scoped_fixture,
        HealthCheck.too_slow,
    ],
)
@given(chunks=st.lists(chunk_strategy(), max_size=6))
def test_filter_by_pdq_property_based(
    embedder_stub: PolicyAnalysisEmbedder, pdq_filter: dict[str, str], chunks: list[Any]
) -> None:
    """Property-based check: the filter never breaks on malformed payloads."""

    result = embedder_stub._filter_by_pdq(chunks, pdq_filter)

    assert isinstance(result, list)
    assert all(chunk in chunks for chunk in result)
    for chunk in result:
        assert isinstance(chunk, dict)
        context = chunk["pdq_context"]
        assert context["policy"] == "P1"
        assert context["dimension"] == "D1"

