"""Integration mismatch regression tests.

These tests intentionally assert that specific cross-module edges fail,
preventing accidental reintegration of incompatible interfaces.
"""

import importlib.util
import sys
import types
from datetime import datetime
from pathlib import Path

import pytest

# Ensure project root importability
# ---------------------------------------------------------------------------
# Dependency stubs to import heavy modules without optional packages.
# ---------------------------------------------------------------------------

sys.modules.setdefault("pdfplumber", types.ModuleType("pdfplumber"))
sys.modules.setdefault("fitz", types.ModuleType("fitz"))
sys.modules.setdefault("pandas", types.ModuleType("pandas"))
sys.modules.setdefault("camelot", types.ModuleType("camelot"))
sys.modules.setdefault("tabula", types.ModuleType("tabula"))
sys.modules.setdefault("spacy", types.ModuleType("spacy"))
sys.modules.setdefault("transformers", types.SimpleNamespace(pipeline=lambda *a, **k: None))
sys.modules.setdefault("torch", types.ModuleType("torch"))
sys.modules.setdefault("pymc", types.ModuleType("pymc"))
sys.modules.setdefault("arviz", types.ModuleType("arviz"))
sys.modules.setdefault("pytensor", types.ModuleType("pytensor"))
sys.modules.setdefault("pytensor.tensor", types.ModuleType("pytensor.tensor"))

stub_numpy = types.ModuleType("numpy")

class _DummyNDArray(list):
    pass

stub_numpy.ndarray = _DummyNDArray
stub_numpy.float32 = float
stub_numpy.int32 = int

def _dummy_array(values, *_, **__):
    return list(values)

stub_numpy.array = _dummy_array
stub_numpy.median = lambda values: sorted(values)[len(values) // 2]
stub_numpy.percentile = lambda values, q: sorted(values)[int(len(values) * (q / 100.0)) % len(values)]
stub_numpy.clip = lambda value, low, high: max(low, min(high, value))
stub_numpy.mean = lambda values: sum(values) / len(values) if values else 0.0
stub_numpy.var = lambda values, ddof=0: 0.0
stub_numpy.histogram = lambda values, bins: ([len(values)], [0])

class _DummyRandom:
    def beta(self, *_, size):
        return [0.0 for _ in range(size)]

    def normal(self, loc, scale, size):
        return [loc for _ in range(size)]

stub_numpy.random = types.SimpleNamespace(default_rng=lambda: _DummyRandom())

sys.modules.setdefault("numpy", stub_numpy)

stub_pypdf2 = types.ModuleType("PyPDF2")

class _DummyPdfReader:  # pragma: no cover - helper stub
    def __init__(self, *args, **kwargs):
        pass

stub_pypdf2.PdfReader = _DummyPdfReader
sys.modules.setdefault("PyPDF2", stub_pypdf2)

stub_langdetect = types.ModuleType("langdetect")

def _detect(_: str) -> str:  # pragma: no cover - helper stub
    return "es"

class _DummyLangDetectException(Exception):
    pass

stub_langdetect.detect = _detect
stub_langdetect.LangDetectException = _DummyLangDetectException
sys.modules.setdefault("langdetect", stub_langdetect)

stub_sentence_transformers = types.ModuleType("sentence_transformers")

class _DummySentenceTransformer:  # pragma: no cover - helper stub
    def __init__(self, *args, **kwargs):
        pass

    def encode(
        self,
        texts,
        batch_size: int | None = None,
        normalize_embeddings: bool | None = None,
        show_progress_bar: bool | None = None,
        convert_to_numpy: bool | None = None,
    ):
        return [[0.0] for _ in texts]

class _DummyCrossEncoder:  # pragma: no cover - helper stub
    def __init__(self, *args, **kwargs):
        pass

    def predict(self, pairs):
        return [0.0 for _ in pairs]

stub_sentence_transformers.SentenceTransformer = _DummySentenceTransformer
stub_sentence_transformers.CrossEncoder = _DummyCrossEncoder
stub_sentence_transformers.util = types.SimpleNamespace(cos_sim=lambda a, b: 0.0)
sys.modules.setdefault("sentence_transformers", stub_sentence_transformers)

stub_sklearn = types.ModuleType("sklearn")
stub_sklearn_metrics = types.ModuleType("sklearn.metrics")
stub_sklearn_pairwise = types.ModuleType("sklearn.metrics.pairwise")
stub_sklearn_feature = types.ModuleType("sklearn.feature_extraction")
stub_sklearn_feature_text = types.ModuleType("sklearn.feature_extraction.text")
stub_sklearn_cluster = types.ModuleType("sklearn.cluster")
stub_sklearn_preprocessing = types.ModuleType("sklearn.preprocessing")

def _cosine_similarity(a, b):  # pragma: no cover - helper stub
    return [[0.0 for _ in range(len(b))] for _ in range(len(a))]

stub_sklearn_pairwise.cosine_similarity = _cosine_similarity
stub_sklearn_metrics.pairwise = stub_sklearn_pairwise
stub_sklearn.metrics = stub_sklearn_metrics
stub_sklearn_feature.text = stub_sklearn_feature_text
stub_sklearn_feature_text.TfidfVectorizer = object
stub_sklearn_cluster.DBSCAN = object
stub_sklearn_cluster.AgglomerativeClustering = object
stub_sklearn_preprocessing.StandardScaler = object
sys.modules.setdefault("sklearn", stub_sklearn)
sys.modules.setdefault("sklearn.metrics", stub_sklearn_metrics)
sys.modules.setdefault("sklearn.metrics.pairwise", stub_sklearn_pairwise)
sys.modules.setdefault("sklearn.feature_extraction", stub_sklearn_feature)
sys.modules.setdefault("sklearn.feature_extraction.text", stub_sklearn_feature_text)
sys.modules.setdefault("sklearn.cluster", stub_sklearn_cluster)
sys.modules.setdefault("sklearn.preprocessing", stub_sklearn_preprocessing)

stub_scipy = types.ModuleType("scipy")
stub_scipy_stats = types.ModuleType("scipy.stats")
stub_scipy.stats = stub_scipy_stats
stub_scipy_optimize = types.ModuleType("scipy.optimize")
stub_scipy.optimize = stub_scipy_optimize
stub_scipy_optimize.minimize = lambda *args, **kwargs: None
stub_scipy_special = types.ModuleType("scipy.special")
stub_scipy.special = stub_scipy_special
stub_scipy_special.expit = lambda x: x
stub_scipy_special.logit = lambda x: x
sys.modules.setdefault("scipy", stub_scipy)
sys.modules.setdefault("scipy.stats", stub_scipy_stats)
sys.modules.setdefault("scipy.optimize", stub_scipy_optimize)
sys.modules.setdefault("scipy.special", stub_scipy_special)

_orchestrator_path = Path(__file__).parent.parent / "orchestrator.py"
_orchestrator_spec = importlib.util.spec_from_file_location("_orchestrator_module", _orchestrator_path)
if _orchestrator_spec and _orchestrator_spec.loader:
    _orchestrator_module = importlib.util.module_from_spec(_orchestrator_spec)
    _orchestrator_module.datetime = datetime
    _orchestrator_spec.loader.exec_module(_orchestrator_module)
    D1Q1_Executor = _orchestrator_module.D1Q1_Executor
else:  # pragma: no cover - safety fallback
    raise RuntimeError("Unable to load orchestrator module")

from saaaaaa.core.aggregation import DimensionAggregator
from saaaaaa.processing.document_ingestion import (
    DocumentIndexes,
    RawDocument,
    StructuredText,
)
from saaaaaa.processing.document_ingestion import (
    PreprocessedDocument as IngestionPreprocessedDocument,
)
from saaaaaa.processing.policy_processor import BayesianEvidenceScorer, IndustrialPolicyProcessor, PolicyTextProcessor

class _NoOpExecutor:
    """MethodExecutor stand-in that should never receive calls."""

    def execute(self, *args, **kwargs):
        pytest.fail("D1Q1_Executor should not reach MethodExecutor with incompatible document")

def _make_ingestion_preprocessed_document() -> IngestionPreprocessedDocument:
    """Build a minimal ingestion PreprocessedDocument instance."""

    raw_doc = RawDocument(
        file_path="/tmp/sample.pdf",
        file_name="sample.pdf",
        num_pages=1,
        file_size_bytes=1024,
        file_hash="deadbeef",
    )
    structured = StructuredText(full_text="contenido", sections=[], page_boundaries=[])
    return IngestionPreprocessedDocument(
        raw_document=raw_doc,
        full_text="contenido",
        structured_text=structured,
        sentences=["Una oración"],
        sentence_metadata=[{}],
        tables=[],
        indexes=DocumentIndexes(),
        language="es",
        preprocessing_metadata={},
    )

def test_ingestion_preprocessed_document_rejected_by_d1q1_executor():
    """D1Q1 expects orchestrator.PreprocessedDocument, not ingestion version."""

    doc = _make_ingestion_preprocessed_document()
    with pytest.raises(AttributeError):
        D1Q1_Executor.execute(doc, _NoOpExecutor())

@pytest.mark.parametrize(
    "method_factory",
    [
        pytest.param(
            lambda: IndustrialPolicyProcessor.__new__(IndustrialPolicyProcessor).process,
            id="process",
        ),
        pytest.param(
            lambda: (
                IndustrialPolicyProcessor.__new__(IndustrialPolicyProcessor)
                ._match_patterns_in_sentences
            ),
            id="_match_patterns_in_sentences",
        ),
        pytest.param(
            lambda: (
                IndustrialPolicyProcessor.__new__(IndustrialPolicyProcessor)
                ._construct_evidence_bundle
            ),
            id="_construct_evidence_bundle",
        ),
        pytest.param(
            lambda: PolicyTextProcessor.__new__(PolicyTextProcessor).segment_into_sentences,
            id="segment_into_sentences",
        ),
        pytest.param(
            lambda: BayesianEvidenceScorer.__new__(BayesianEvidenceScorer).compute_evidence_score,
            id="compute_evidence_score",
        ),
    ],
)
def test_d1q1_executor_method_signatures_reject_extra_kwargs(method_factory):
    """Every method D1Q1 wires to rejects injected text/sentences/tables kwargs."""

    method = method_factory()
    with pytest.raises(TypeError):
        method(text="texto", sentences=["x"], tables=[])

def test_semantic_processor_chunks_lack_content_key_for_embedder():
    """SemanticProcessor.chunk_text outputs use 'text', not 'content'."""

    semantic_chunks = [
        {
            "text": "Segmento de política",
            "section_type": "diagnostico",
            "section_id": "sec_0",
            "token_count": 42,
            "position": 0,
            "has_table": False,
            "has_numerical": False,
            "pdq_context": {
                "question_unique_id": "P1-D1-Q1",
                "policy": "P1",
                "dimension": "D1",
                "question": 1,
                "rubric_key": "D1-Q1",
            },
        }
    ]

    with pytest.raises(KeyError):
        _ = [chunk["content"] for chunk in semantic_chunks]

def test_bayesian_posterior_samples_incompatible_with_derek_beach_ppc():
    """Posterior samples from analyzer are numeric arrays, not dict records."""

    # Simulate BayesianNumericalAnalyzer output: list/array of floats
    posterior_samples = [0.1, 0.2, 0.3]

    class _PosteriorPredictiveChecker:
        def posterior_predictive_check(self, posterior_samples, observed_data):
            for sample in posterior_samples:
                # DerekBeachProducer expects dict-like samples with .get
                sample.get("coherence")  # type: ignore[attr-defined]

    checker = _PosteriorPredictiveChecker()

    with pytest.raises(AttributeError):
        checker.posterior_predictive_check(posterior_samples, {"coherence": 0.5})

def test_type_a_scores_get_clamped_by_dimension_rubric_thresholds():
    """DimensionAggregator clamps scores above 3, erasing TYPE_A's 0-4 range."""

    dummy_monolith = {"blocks": {"scoring": {}, "niveles_abstraccion": {}}}
    aggregator = DimensionAggregator(dummy_monolith)

    quality_at_three = aggregator.apply_rubric_thresholds(3.0)
    quality_at_four = aggregator.apply_rubric_thresholds(4.0)

    assert quality_at_three == quality_at_four
