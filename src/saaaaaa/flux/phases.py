# stdlib
from __future__ import annotations

import json
import logging
import os
import re
import time
import unicodedata
from typing import TYPE_CHECKING, Any

# third-party (pinned in pyproject)
import polars as pl
import pyarrow as pa
from blake3 import blake3
from opentelemetry import metrics, trace
from pydantic import BaseModel, ValidationError

# Contract infrastructure - ACTUAL INTEGRATION
from saaaaaa.utils.contract_io import ContractEnvelope
from saaaaaa.utils.json_logger import get_json_logger, log_io_event
from saaaaaa.utils.paths import reports_dir

from .models import (
    AggregateDeliverable,
    AggregateExpectation,
    ChunkDeliverable,
    ChunkExpectation,
    DocManifest,
    IngestDeliverable,
    NormalizeDeliverable,
    NormalizeExpectation,
    PhaseOutcome,
    ReportDeliverable,
    ReportExpectation,
    ScoreDeliverable,
    ScoreExpectation,
    SignalsDeliverable,
    SignalsExpectation,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from .configs import (
        AggregateConfig,
        ChunkConfig,
        NormalizeConfig,
        ReportConfig,
        ScoreConfig,
        SignalsConfig,
    )

logger = logging.getLogger(__name__)
tracer = trace.get_tracer("flux")
meter = metrics.get_meter("flux")

# Metrics
phase_counter = meter.create_counter(
    "flux.phase.ok", description="Successful phase executions"
)
phase_error_counter = meter.create_counter(
    "flux.phase.err", description="Failed phase executions"
)
phase_latency_histogram = meter.create_histogram(
    "flux.phase.latency_ms", description="Phase execution latency in milliseconds"
)


class PreconditionError(Exception):
    """Raised when a phase precondition is violated."""

    def __init__(self, phase: str, condition: str, message: str) -> None:
        self.phase = phase
        self.condition = condition
        super().__init__(f"Precondition failed in {phase}: {condition} - {message}")


class PostconditionError(Exception):
    """Raised when a phase postcondition is violated."""

    def __init__(self, phase: str, condition: str, message: str) -> None:
        self.phase = phase
        self.condition = condition
        super().__init__(f"Postcondition failed in {phase}: {condition} - {message}")


class CompatibilityError(Exception):
    """Raised when phase compatibility validation fails."""

    def __init__(
        self, source: str, target: str, validation_error: ValidationError
    ) -> None:
        self.source = source
        self.target = target
        self.validation_error = validation_error
        super().__init__(
            f"Compatibility error {source} → {target}: {validation_error}"
        )


def _fp(d: BaseModel | dict[str, Any]) -> str:
    """
    Compute deterministic fingerprint.

    requires: d is not None
    ensures: result is 64-char hex string
    """
    if d is None:
        raise PreconditionError("_fp", "d is not None", "Input cannot be None")

    b = (
        d.model_dump_json() if isinstance(d, BaseModel) else json.dumps(d, sort_keys=True)
    ).encode()
    result = blake3(b"FLUX-2025.1" + b).hexdigest()

    if len(result) != 64:
        raise PostconditionError(
            "_fp", "result is 64-char hex", f"Got {len(result)} chars"
        )

    return result


def assert_compat(deliverable: BaseModel, expectation_cls: type[BaseModel]) -> None:
    """
    Validate compatibility between deliverable and expectation.

    requires: deliverable and expectation_cls are not None
    ensures: validation passes or CompatibilityError is raised
    """
    if deliverable is None or expectation_cls is None:
        raise PreconditionError(
            "assert_compat",
            "inputs not None",
            "deliverable and expectation_cls must be provided",
        )

    try:
        expectation_cls.model_validate(deliverable.model_dump())
    except ValidationError as ve:
        raise CompatibilityError(
            deliverable.__class__.__name__, expectation_cls.__name__, ve
        ) from ve


# NOTE: INGEST phase removed - use SPC (Smart Policy Chunks) via CPPIngestionPipeline
# SPC is the ONLY canonical Phase-One entry point (src/saaaaaa/processing/spc_ingestion)
# FLUX phases begin from NORMALIZE, which receives SPC output


# NORMALIZE
def run_normalize(
    cfg: NormalizeConfig,
    ing: IngestDeliverable,
    *,
    policy_unit_id: str | None = None,
    correlation_id: str | None = None,
    envelope_metadata: dict[str, str] | None = None,
) -> PhaseOutcome:
    """
    Execute normalize phase with mandatory metadata propagation.

    requires: compatible input from ingest
    ensures: sentences list is not empty, sentence_meta matches length, metadata propagated
    """
    start_time = time.time()
    start_monotonic = time.monotonic()

    # Derive policy_unit_id from environment or generate default
    if policy_unit_id is None:
        policy_unit_id = os.getenv("POLICY_UNIT_ID", "default-policy")
    if correlation_id is None:
        import uuid
        correlation_id = str(uuid.uuid4())

    # Get contract-aware JSON logger
    contract_logger = get_json_logger("flux.normalize")

    with tracer.start_as_current_span("normalize") as span:
        # Wrap input with ContractEnvelope for traceability
        env_in = ContractEnvelope.wrap(
            ing.model_dump(),
            policy_unit_id=policy_unit_id,
            correlation_id=correlation_id
        )

        # Compatibility check
        assert_compat(ing, NormalizeExpectation)

        if policy_unit_id:
            span.set_attribute("policy_unit_id", policy_unit_id)
        if correlation_id:
            span.set_attribute("correlation_id", correlation_id)

        # PHASE 2: TEXT NORMALIZATION - MAXIMUM STANDARD IMPLEMENTATION
        # =============================================================

        logger.info(
            f"Normalizing text with unicode_form={cfg.unicode_form}, "
            f"keep_diacritics={cfg.keep_diacritics}"
        )

        # Step 1: Unicode Normalization (NFC or NFKC)
        normalized_text = unicodedata.normalize(cfg.unicode_form, ing.raw_text)
        span.set_attribute("unicode_form", cfg.unicode_form)

        # Step 2: Whitespace Normalization (deterministic)
        # Replace multiple spaces with single space
        normalized_text = re.sub(r'[ \t]+', ' ', normalized_text)
        # Replace multiple newlines with single newline
        normalized_text = re.sub(r'\n{3,}', '\n\n', normalized_text)
        # Clean spaces around newlines (but preserve paragraph breaks)
        normalized_text = re.sub(r' *\n *', '\n', normalized_text)
        # Remove trailing/leading whitespace
        normalized_text = normalized_text.strip()

        # Step 3: Diacritic Handling (if configured)
        if not cfg.keep_diacritics:
            logger.info("Removing diacritics per configuration")
            # Decompose to NFD (separates base chars from diacritics)
            nfd_text = unicodedata.normalize('NFD', normalized_text)
            # Filter out combining marks (category Mn)
            no_diacritic_text = ''.join(
                c for c in nfd_text
                if unicodedata.category(c) != 'Mn'
            )
            # Recompose to NFC
            normalized_text = unicodedata.normalize('NFC', no_diacritic_text)
            span.set_attribute("diacritics_removed", True)

        # Step 4: Sentence Segmentation with spaCy (MAXIMUM STANDARD)
        # Try spaCy first (high quality), fallback to regex if unavailable
        sentences: list[str] = []
        sentence_meta: list[dict[str, Any]] = []

        try:
            import spacy
            # Load Spanish model (large for maximum precision)
            try:
                nlp = spacy.load("es_core_news_lg")
            except OSError:
                # Fallback to medium model
                logger.warning("es_core_news_lg not found, using es_core_news_md")
                try:
                    nlp = spacy.load("es_core_news_md")
                except OSError:
                    # Fallback to small model
                    logger.warning("es_core_news_md not found, using es_core_news_sm")
                    nlp = spacy.load("es_core_news_sm")

            # Process with spaCy pipeline
            doc = nlp(normalized_text)

            for i, sent in enumerate(doc.sents):
                sentence_text = sent.text.strip()
                if not sentence_text:
                    continue

                sentences.append(sentence_text)

                # Rich metadata per sentence
                sentence_meta.append({
                    "index": i,
                    "length": len(sentence_text),
                    "char_start": sent.start_char,
                    "char_end": sent.end_char,
                    "token_count": len(sent),
                    "has_verb": any(token.pos_ == "VERB" for token in sent),
                    "num_entities": len(sent.ents),
                    "entity_labels": [ent.label_ for ent in sent.ents] if sent.ents else [],
                    "root_lemma": sent.root.lemma_ if sent.root else None,
                    "root_pos": sent.root.pos_ if sent.root else None,
                })

            logger.info(f"spaCy segmentation: {len(sentences)} sentences extracted")
            span.set_attribute("segmentation_method", "spacy")

        except ImportError:
            logger.warning("spaCy not available, using regex fallback for sentence segmentation")
            span.set_attribute("segmentation_method", "regex_fallback")

            # FALLBACK: Advanced regex-based segmentation
            # Pattern that respects abbreviations, decimals, ellipsis
            # Matches sentence-ending punctuation followed by whitespace and capital letter
            sentence_pattern = r'(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ])'

            # Split by pattern
            raw_sentences = re.split(sentence_pattern, normalized_text)

            char_pos = 0
            for i, sent_text in enumerate(raw_sentences):
                sent_text = sent_text.strip()
                if not sent_text:
                    continue

                sentences.append(sent_text)

                sentence_meta.append({
                    "index": i,
                    "length": len(sent_text),
                    "char_start": char_pos,
                    "char_end": char_pos + len(sent_text),
                    "token_count": len(sent_text.split()),
                    "has_verb": None,  # Not available without spaCy
                    "num_entities": None,
                    "entity_labels": [],
                    "root_lemma": None,
                    "root_pos": None,
                })

                char_pos += len(sent_text) + 1  # +1 for space/newline

            logger.info(f"Regex segmentation: {len(sentences)} sentences extracted")

        # Final validation
        if not sentences:
            logger.error("Normalization produced zero sentences - attempting line-based fallback")
            # Last resort: split by newlines (but still normalize each)
            for i, line in enumerate(normalized_text.split('\n')):
                line = line.strip()
                if line:
                    sentences.append(line)
                    sentence_meta.append({
                        "index": i,
                        "length": len(line),
                        "char_start": 0,
                        "char_end": len(line),
                        "token_count": len(line.split()),
                        "has_verb": None,
                        "num_entities": None,
                        "entity_labels": [],
                        "root_lemma": None,
                        "root_pos": None,
                    })

        out = NormalizeDeliverable(sentences=sentences, sentence_meta=sentence_meta)

        # Postconditions
        if not out.sentences:
            raise PostconditionError(
                "run_normalize", "non-empty sentences", "Must produce at least one sentence"
            )

        if len(out.sentences) != len(out.sentence_meta):
            raise PostconditionError(
                "run_normalize",
                "meta length match",
                f"sentences={len(out.sentences)}, meta={len(out.sentence_meta)}",
            )

        # Wrap output with ContractEnvelope
        env_out = ContractEnvelope.wrap(
            out.model_dump(),
            policy_unit_id=policy_unit_id,
            correlation_id=correlation_id
        )

        fp = _fp(out)
        span.set_attribute("fingerprint", fp)
        span.set_attribute("sentence_count", len(out.sentences))
        span.set_attribute("correlation_id", correlation_id)
        span.set_attribute("content_digest", env_out.content_digest)

        duration_ms = (time.time() - start_time) * 1000
        phase_latency_histogram.record(duration_ms, {"phase": "normalize"})
        phase_counter.add(1, {"phase": "normalize"})

        # Structured JSON logging with envelope metadata
        log_io_event(
            contract_logger,
            phase="normalize",
            envelope_in=env_in,
            envelope_out=env_out,
            started_monotonic=start_monotonic
        )

        logger.info(
            "phase_complete: phase=%s ok=%s fingerprint=%s duration_ms=%.2f sentence_count=%d",
            "normalize",
            True,
            fp,
            duration_ms,
            len(out.sentences),
        )

        return PhaseOutcome(
            ok=True,
            phase="normalize",
            payload=out.model_dump(),
            fingerprint=fp,
            policy_unit_id=policy_unit_id,
            correlation_id=correlation_id,
            envelope_metadata={
                "event_id": env_out.event_id,
                "content_digest": env_out.content_digest,
                "schema_version": env_out.schema_version,
            },
            metrics={"duration_ms": duration_ms, "sentence_count": len(out.sentences)},
        )


# CHUNK
def run_chunk(
    cfg: ChunkConfig,
    norm: NormalizeDeliverable,
    *,
    policy_unit_id: str | None = None,
    correlation_id: str | None = None,
    envelope_metadata: dict[str, str] | None = None,
) -> PhaseOutcome:
    """
    Execute chunk phase with mandatory metadata propagation.

    requires: compatible input from normalize
    ensures: chunks not empty, chunk_index has valid resolutions, metadata propagated
    """
    start_time = time.time()
    start_monotonic = time.monotonic()

    # Derive policy_unit_id from environment or generate default
    if policy_unit_id is None:
        policy_unit_id = os.getenv("POLICY_UNIT_ID", "default-policy")
    if correlation_id is None:
        import uuid
        correlation_id = str(uuid.uuid4())

    # Get contract-aware JSON logger
    contract_logger = get_json_logger("flux.chunk")

    with tracer.start_as_current_span("chunk") as span:
        # Wrap input with ContractEnvelope
        env_in = ContractEnvelope.wrap(
            norm.model_dump(),
            policy_unit_id=policy_unit_id,
            correlation_id=correlation_id
        )

        # Compatibility check
        assert_compat(norm, ChunkExpectation)

        if policy_unit_id:
            span.set_attribute("policy_unit_id", policy_unit_id)
        if correlation_id:
            span.set_attribute("correlation_id", correlation_id)

        # TODO: Implement actual chunking with token limits and overlap
        chunks: list[dict[str, Any]] = [
            {
                "id": f"c{i}",
                "text": s,
                "resolution": cfg.priority_resolution,
                "span": {"start": i, "end": i + 1},
            }
            for i, s in enumerate(norm.sentences)
        ]

        idx: dict[str, list[str]] = {
            "micro": [],
            "meso": [c["id"] for c in chunks if c["resolution"] == "MESO"],
            "macro": [],
        }

        out = ChunkDeliverable(chunks=chunks, chunk_index=idx)

        # Postconditions
        if not out.chunks:
            raise PostconditionError(
                "run_chunk", "non-empty chunks", "Must produce at least one chunk"
            )

        valid_resolutions = {"micro", "meso", "macro"}
        if not all(k in valid_resolutions for k in out.chunk_index):
            raise PostconditionError(
                "run_chunk",
                "valid chunk_index keys",
                f"Keys must be {valid_resolutions}",
            )

        # Wrap output with ContractEnvelope
        env_out = ContractEnvelope.wrap(
            out.model_dump(),
            policy_unit_id=policy_unit_id,
            correlation_id=correlation_id
        )

        fp = _fp(out)
        span.set_attribute("fingerprint", fp)
        span.set_attribute("chunk_count", len(out.chunks))
        span.set_attribute("correlation_id", correlation_id)
        span.set_attribute("content_digest", env_out.content_digest)

        duration_ms = (time.time() - start_time) * 1000
        phase_latency_histogram.record(duration_ms, {"phase": "chunk"})
        phase_counter.add(1, {"phase": "chunk"})

        # Structured JSON logging with envelope metadata
        log_io_event(
            contract_logger,
            phase="chunk",
            envelope_in=env_in,
            envelope_out=env_out,
            started_monotonic=start_monotonic
        )

        logger.info(
            "phase_complete: phase=%s ok=%s fingerprint=%s duration_ms=%.2f chunk_count=%d",
            "chunk",
            True,
            fp,
            duration_ms,
            len(out.chunks),
        )

        return PhaseOutcome(
            ok=True,
            phase="chunk",
            payload=out.model_dump(),
            fingerprint=fp,
            policy_unit_id=policy_unit_id,
            correlation_id=correlation_id,
            envelope_metadata={
                "event_id": env_out.event_id,
                "content_digest": env_out.content_digest,
                "schema_version": env_out.schema_version,
            },
            metrics={"duration_ms": duration_ms, "chunk_count": len(out.chunks)},
        )


# SIGNALS
def run_signals(
    cfg: SignalsConfig,
    ch: ChunkDeliverable,
    *,
    registry_get: Callable[[str], dict[str, Any] | None],
    policy_unit_id: str | None = None,
    correlation_id: str | None = None,
    envelope_metadata: dict[str, str] | None = None,
) -> PhaseOutcome:
    """
    Execute signals phase (cross-cut) with mandatory metadata propagation.

    requires: compatible input from chunk, registry_get callable
    ensures: enriched_chunks not empty, used_signals recorded, metadata propagated
    """
    get_json_logger("flux.signals")
    time.monotonic()
    start_time = time.time()

    with tracer.start_as_current_span("signals") as span:
        # Thread correlation tracking
        if correlation_id:
            span.set_attribute("correlation_id", correlation_id)
        if policy_unit_id:
            span.set_attribute("policy_unit_id", policy_unit_id)

        # Compatibility check
        assert_compat(ch, SignalsExpectation)

        # Wrap input with ContractEnvelope
        env_in = ContractEnvelope.wrap(
            ch.model_dump(),
            policy_unit_id=policy_unit_id or "default",
            correlation_id=correlation_id
        )
        span.set_attribute("input_digest", env_in.content_digest)

        # Preconditions
        if registry_get is None:
            raise PreconditionError(
                "run_signals",
                "registry_get not None",
                "registry_get must be provided",
            )

        if policy_unit_id:
            span.set_attribute("policy_unit_id", policy_unit_id)
        if correlation_id:
            span.set_attribute("correlation_id", correlation_id)

        # TODO: Implement actual signal enrichment
        pack = registry_get("default")

        if pack is None:
            enriched = ch.chunks
            used_signals: dict[str, Any] = {"present": False}
        else:
            enriched = [
                {**c, "patterns_used": len(pack.get("patterns", []))}
                for c in ch.chunks
            ]
            used_signals = {
                "present": True,
                "version": pack.get("version", "unknown"),
                "policy_area": "default",
            }

        out = SignalsDeliverable(enriched_chunks=enriched, used_signals=used_signals)

        # Postconditions
        if not out.enriched_chunks:
            raise PostconditionError(
                "run_signals", "non-empty enriched_chunks", "Must have at least one chunk"
            )

        if "present" not in out.used_signals:
            raise PostconditionError(
                "run_signals",
                "used_signals.present exists",
                "used_signals must indicate presence",
            )

        fp = _fp(out)
        span.set_attribute("fingerprint", fp)
        span.set_attribute("signals_present", used_signals["present"])

        # Wrap output with ContractEnvelope
        env_out = ContractEnvelope.wrap(
            out.model_dump(),
            policy_unit_id=policy_unit_id or "default",
            correlation_id=correlation_id
        )
        span.set_attribute("content_digest", env_out.content_digest)
        span.set_attribute("event_id", env_out.event_id)

        duration_ms = (time.time() - start_time) * 1000
        phase_latency_histogram.record(duration_ms, {"phase": "signals"})
        phase_counter.add(1, {"phase": "signals"})

        logger.info(
            "phase_complete: phase=%s ok=%s fingerprint=%s duration_ms=%.2f signals_present=%s policy_unit_id=%s",
            "signals",
            True,
            fp,
            duration_ms,
            used_signals["present"],
            policy_unit_id,
        )

        return PhaseOutcome(
            ok=True,
            phase="signals",
            payload=out.model_dump(),
            fingerprint=fp,
            policy_unit_id=policy_unit_id,
            correlation_id=correlation_id,
            envelope_metadata={
                "event_id": env_out.event_id,
                "content_digest": env_out.content_digest,
                "schema_version": env_out.schema_version,
            },
            metrics={"duration_ms": duration_ms},
        )


# AGGREGATE
def run_aggregate(
    cfg: AggregateConfig,
    sig: SignalsDeliverable,
    *,
    policy_unit_id: str | None = None,
    correlation_id: str | None = None,
    envelope_metadata: dict[str, str] | None = None,
) -> PhaseOutcome:
    """
    Execute aggregate phase with mandatory metadata propagation.

    requires: compatible input from signals, group_by not empty
    ensures: features table has required columns, aggregation_meta recorded, metadata propagated
    """
    get_json_logger("flux.aggregate")
    time.monotonic()
    start_time = time.time()

    with tracer.start_as_current_span("aggregate") as span:
        # Thread correlation tracking
        if correlation_id:
            span.set_attribute("correlation_id", correlation_id)
        if policy_unit_id:
            span.set_attribute("policy_unit_id", policy_unit_id)

        # Compatibility check
        assert_compat(sig, AggregateExpectation)

        # Wrap input with ContractEnvelope
        env_in = ContractEnvelope.wrap(
            sig.model_dump(),
            policy_unit_id=policy_unit_id or "default",
            correlation_id=correlation_id
        )
        span.set_attribute("input_digest", env_in.content_digest)

        # Preconditions
        if not cfg.group_by:
            raise PreconditionError(
                "run_aggregate",
                "group_by not empty",
                "group_by must contain at least one field",
            )

        if policy_unit_id:
            span.set_attribute("policy_unit_id", policy_unit_id)
        if correlation_id:
            span.set_attribute("correlation_id", correlation_id)

        # TODO: Implement actual feature engineering
        item_ids = [c.get("id", f"c{i}") for i, c in enumerate(sig.enriched_chunks)]
        patterns = [c.get("patterns_used", 0) for c in sig.enriched_chunks]

        tbl = pa.table({"item_id": item_ids, "patterns_used": patterns})

        aggregation_meta: dict[str, Any] = {
            "rows": tbl.num_rows,
            "group_by": cfg.group_by,
            "feature_set": cfg.feature_set,
        }

        out = AggregateDeliverable(features=tbl, aggregation_meta=aggregation_meta)

        # Postconditions
        if out.features.num_rows == 0:
            raise PostconditionError(
                "run_aggregate", "non-empty features", "Features table must have rows"
            )

        required_columns = {"item_id"}
        actual_columns = set(out.features.column_names)
        if not required_columns.issubset(actual_columns):
            missing = required_columns - actual_columns
            raise PostconditionError(
                "run_aggregate",
                "required columns present",
                f"Missing columns: {missing}",
            )

        fp = _fp(aggregation_meta)
        span.set_attribute("fingerprint", fp)
        span.set_attribute("feature_count", tbl.num_rows)

        # Wrap output with ContractEnvelope
        payload_dict = {"rows": tbl.num_rows, "meta": aggregation_meta}
        env_out = ContractEnvelope.wrap(
            payload_dict,
            policy_unit_id=policy_unit_id or "default",
            correlation_id=correlation_id
        )
        span.set_attribute("content_digest", env_out.content_digest)
        span.set_attribute("event_id", env_out.event_id)

        duration_ms = (time.time() - start_time) * 1000
        phase_latency_histogram.record(duration_ms, {"phase": "aggregate"})
        phase_counter.add(1, {"phase": "aggregate"})

        logger.info(
            "phase_complete: phase=%s ok=%s fingerprint=%s duration_ms=%.2f feature_count=%d",
            "aggregate",
            True,
            fp,
            duration_ms,
            tbl.num_rows,
        )

        return PhaseOutcome(
            ok=True,
            phase="aggregate",
            payload=payload_dict,
            fingerprint=fp,
            policy_unit_id=policy_unit_id,
            correlation_id=correlation_id,
            envelope_metadata=envelope_metadata or {},
            metrics={"duration_ms": duration_ms, "feature_count": tbl.num_rows},
        )


# SCORE
def run_score(
    cfg: ScoreConfig,
    agg: AggregateDeliverable,
    *,
    policy_unit_id: str | None = None,
    correlation_id: str | None = None,
    envelope_metadata: dict[str, str] | None = None,
) -> PhaseOutcome:
    """
    Execute score phase with mandatory metadata propagation.

    requires: compatible input from aggregate, metrics not empty
    ensures: scores dataframe not empty, has required columns, metadata propagated
    """
    get_json_logger("flux.score")
    time.monotonic()
    start_time = time.time()

    with tracer.start_as_current_span("score") as span:
        # Thread correlation tracking
        if correlation_id:
            span.set_attribute("correlation_id", correlation_id)
        if policy_unit_id:
            span.set_attribute("policy_unit_id", policy_unit_id)

        # Compatibility check
        assert_compat(agg, ScoreExpectation)

        # Wrap input with ContractEnvelope
        input_payload = {"rows": agg.features.num_rows, "meta": agg.aggregation_meta}
        env_in = ContractEnvelope.wrap(
            input_payload,
            policy_unit_id=policy_unit_id or "default",
            correlation_id=correlation_id
        )
        span.set_attribute("input_digest", env_in.content_digest)

        # Preconditions
        if not cfg.metrics:
            raise PreconditionError(
                "run_score", "metrics not empty", "metrics list must not be empty"
            )

        if policy_unit_id:
            span.set_attribute("policy_unit_id", policy_unit_id)
        if correlation_id:
            span.set_attribute("correlation_id", correlation_id)

        # TODO: Implement actual scoring logic
        item_ids = agg.features.column("item_id").to_pylist()

        # Create scores for each metric
        data: dict[str, list[Any]] = {
            "item_id": item_ids * len(cfg.metrics),
            "metric": [m for m in cfg.metrics for _ in item_ids],
            "value": [1.0] * (len(item_ids) * len(cfg.metrics)),
        }

        df = pl.DataFrame(data)

        calibration: dict[str, Any] = {"mode": cfg.calibration_mode}

        out = ScoreDeliverable(scores=df, calibration=calibration)

        # Postconditions
        if out.scores.height == 0:
            raise PostconditionError(
                "run_score", "non-empty scores", "Scores dataframe must have rows"
            )

        required_cols = {"item_id", "metric", "value"}
        actual_cols = set(out.scores.columns)
        if not required_cols.issubset(actual_cols):
            missing = required_cols - actual_cols
            raise PostconditionError(
                "run_score", "required columns present", f"Missing columns: {missing}"
            )

        fp = _fp({"n": df.height, "calibration": calibration})
        span.set_attribute("fingerprint", fp)
        span.set_attribute("score_count", df.height)

        # Wrap output with ContractEnvelope
        payload_dict = {"n": df.height}
        env_out = ContractEnvelope.wrap(
            payload_dict,
            policy_unit_id=policy_unit_id or "default",
            correlation_id=correlation_id
        )
        span.set_attribute("content_digest", env_out.content_digest)
        span.set_attribute("event_id", env_out.event_id)

        duration_ms = (time.time() - start_time) * 1000
        phase_latency_histogram.record(duration_ms, {"phase": "score"})
        phase_counter.add(1, {"phase": "score"})

        logger.info(
            "phase_complete: phase=%s ok=%s fingerprint=%s duration_ms=%.2f score_count=%d",
            "score",
            True,
            fp,
            duration_ms,
            df.height,
        )

        return PhaseOutcome(
            ok=True,
            phase="score",
            payload=payload_dict,
            fingerprint=fp,
            policy_unit_id=policy_unit_id,
            correlation_id=correlation_id,
            envelope_metadata=envelope_metadata or {},
            metrics={"duration_ms": duration_ms, "score_count": df.height},
        )


# REPORT
def run_report(
    cfg: ReportConfig,
    sc: ScoreDeliverable,
    manifest: DocManifest,
    *,
    policy_unit_id: str | None = None,
    correlation_id: str | None = None,
    envelope_metadata: dict[str, str] | None = None,
) -> PhaseOutcome:
    """
    Execute report phase with mandatory metadata propagation.

    requires: compatible input from score, manifest not None
    ensures: artifacts not empty, summary contains required fields, metadata propagated
    """
    get_json_logger("flux.report")
    time.monotonic()
    start_time = time.time()

    with tracer.start_as_current_span("report") as span:
        # Thread correlation tracking
        if correlation_id:
            span.set_attribute("correlation_id", correlation_id)
        if policy_unit_id:
            span.set_attribute("policy_unit_id", policy_unit_id)

        # Compatibility check
        assert_compat(sc, ReportExpectation)

        # Wrap input with ContractEnvelope
        input_payload = {"n": sc.scores.height}
        env_in = ContractEnvelope.wrap(
            input_payload,
            policy_unit_id=policy_unit_id or "default",
            correlation_id=correlation_id
        )
        span.set_attribute("input_digest", env_in.content_digest)

        # Preconditions
        if manifest is None:
            raise PreconditionError(
                "run_report", "manifest not None", "manifest must be provided"
            )

        if policy_unit_id:
            span.set_attribute("policy_unit_id", policy_unit_id)
        if correlation_id:
            span.set_attribute("correlation_id", correlation_id)

        # TODO: Implement actual report generation
        artifacts: dict[str, str] = {}

        # Use reports directory instead of /tmp
        report_base = reports_dir() / "flux_summaries"
        report_base.mkdir(parents=True, exist_ok=True)

        for fmt in cfg.formats:
            artifact_path = str(report_base / f"{manifest.document_id}.summary.{fmt}")
            artifacts[f"summary.{fmt}"] = artifact_path

        summary: dict[str, Any] = {
            "items": sc.scores.height,
            "document_id": manifest.document_id,
            "include_provenance": cfg.include_provenance,
        }

        out = ReportDeliverable(artifacts=artifacts, summary=summary)

        # Postconditions
        if not out.artifacts:
            raise PostconditionError(
                "run_report", "non-empty artifacts", "Must produce at least one artifact"
            )

        if "items" not in out.summary:
            raise PostconditionError(
                "run_report", "summary.items present", "Summary must contain items count"
            )

        fp = _fp(out)
        span.set_attribute("fingerprint", fp)
        span.set_attribute("artifact_count", len(out.artifacts))

        # Wrap output with ContractEnvelope (final phase)
        env_out = ContractEnvelope.wrap(
            out.model_dump(),
            policy_unit_id=policy_unit_id or "default",
            correlation_id=correlation_id
        )
        span.set_attribute("content_digest", env_out.content_digest)
        span.set_attribute("event_id", env_out.event_id)

        duration_ms = (time.time() - start_time) * 1000
        phase_latency_histogram.record(duration_ms, {"phase": "report"})
        phase_counter.add(1, {"phase": "report"})

        logger.info(
            "phase_complete: phase=%s ok=%s fingerprint=%s duration_ms=%.2f artifact_count=%d policy_unit_id=%s",
            "report",
            True,
            fp,
            duration_ms,
            len(out.artifacts),
            policy_unit_id,
        )

        return PhaseOutcome(
            ok=True,
            phase="report",
            payload=out.model_dump(),
            fingerprint=fp,
            policy_unit_id=policy_unit_id,
            correlation_id=correlation_id,
            envelope_metadata={
                "event_id": env_out.event_id,
                "content_digest": env_out.content_digest,
                "schema_version": env_out.schema_version,
            },
            metrics={"duration_ms": duration_ms, "artifact_count": len(out.artifacts)},
        )
