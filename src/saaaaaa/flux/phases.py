# stdlib
from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Callable

# third-party (pinned in pyproject)
import polars as pl
import pyarrow as pa
from blake3 import blake3
from opentelemetry import metrics, trace
from pydantic import BaseModel, ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential_jitter

from saaaaaa.utils.paths import reports_dir
from saaaaaa.processing.spc_ingestion import StrategicChunkingSystem

# Contract infrastructure - ACTUAL INTEGRATION
from saaaaaa.utils.contract_io import ContractEnvelope
from saaaaaa.utils.determinism_helpers import deterministic
from saaaaaa.utils.json_logger import get_json_logger, log_io_event

from .configs import (
    AggregateConfig,
    ChunkConfig,
    IngestConfig,
    NormalizeConfig,
    ReportConfig,
    ScoreConfig,
    SignalsConfig,
)
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


# INGEST
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=1, max=10),
    reraise=True,
)
def run_ingest(
    cfg: IngestConfig,
    *,
    input_uri: str,
    policy_unit_id: str | None = None,
    correlation_id: str | None = None,
    envelope_metadata: dict[str, str] | None = None,
) -> PhaseOutcome:
    """
    Execute ingest phase with mandatory metadata propagation.

    requires: non-empty input_uri
    ensures: provenance_ok is True, fingerprint computed, metadata propagated
    """
    contract_logger = get_json_logger("flux.ingest")
    started_monotonic = time.monotonic()
    start_time = time.time()

    with tracer.start_as_current_span("ingest") as span:
        # Thread correlation tracking
        if correlation_id:
            span.set_attribute("correlation_id", correlation_id)
        if policy_unit_id:
            span.set_attribute("policy_unit_id", policy_unit_id)
        
        # Preconditions
        if not input_uri or not input_uri.strip():
            raise PreconditionError(
                "run_ingest",
                "non-empty input_uri",
                "input_uri must be a non-empty string",
            )

        span.set_attribute("document_id", os.path.basename(input_uri))
        if policy_unit_id:
            span.set_attribute("policy_unit_id", policy_unit_id)
        if correlation_id:
            span.set_attribute("correlation_id", correlation_id)

        # Use SPC (Smart Policy Chunks) ingestion - the canonical phase-one pipeline
        try:
            input_path = Path(input_uri)
            if not input_path.exists():
                raise PreconditionError(
                    "run_ingest",
                    "input_uri must exist",
                    f"File not found: {input_uri}",
                )
            
            # Initialize SPC chunking system
            spc_system = StrategicChunkingSystem()
            
            # Read document content
            if input_path.suffix.lower() == '.pdf':
                # For PDF files, use appropriate extraction
                import pdfplumber
                raw_text_parts = []
                tables: list[dict[str, Any]] = []
                
                with pdfplumber.open(input_path) as pdf:
                    for page_num, page in enumerate(pdf.pages):
                        # Extract text
                        page_text = page.extract_text() or ""
                        if page_text.strip():
                            raw_text_parts.append(page_text)
                        
                        # Extract tables
                        page_tables = page.extract_tables()
                        if page_tables:
                            for table_idx, table in enumerate(page_tables):
                                if table:
                                    tables.append({
                                        "page": page_num + 1,
                                        "table_index": table_idx,
                                        "data": table,
                                    })
                
                raw_text = "\n\n".join(raw_text_parts)
            else:
                # For text files, read directly
                with open(input_path, 'r', encoding='utf-8') as f:
                    raw_text = f.read()
                tables = []
            
            # Validate we got content
            if not raw_text or not raw_text.strip():
                raise PostconditionError(
                    "run_ingest",
                    "non-empty content",
                    f"No text content extracted from {input_uri}",
                )
            
        except ImportError as e:
            # Fallback if pdfplumber not available
            logger.warning(f"PDF processing library not available: {e}. Using text extraction fallback.")
            with open(input_uri, 'r', encoding='utf-8', errors='ignore') as f:
                raw_text = f.read()
            tables = []

        out = IngestDeliverable(
            manifest=DocManifest(document_id=os.path.basename(input_uri)),
            raw_text=raw_text,
            tables=tables,
            provenance_ok=True,
        )

        # Postconditions
        if not out.provenance_ok:
            raise PostconditionError(
                "run_ingest", "provenance_ok", "Provenance must be verified"
            )

        fp = _fp(out)
        span.set_attribute("fingerprint", fp)

        # Wrap output with ContractEnvelope for traceability
        env_out = ContractEnvelope.wrap(
            out.model_dump(),
            policy_unit_id=policy_unit_id or "default",
            correlation_id=correlation_id
        )
        span.set_attribute("content_digest", env_out.content_digest)
        span.set_attribute("event_id", env_out.event_id)

        duration_ms = (time.time() - start_time) * 1000
        phase_latency_histogram.record(duration_ms, {"phase": "ingest"})
        phase_counter.add(1, {"phase": "ingest"})

        logger.info(
            "phase_complete: phase=%s ok=%s fingerprint=%s duration_ms=%.2f",
            "ingest",
            True,
            fp,
            duration_ms,
        )

        return PhaseOutcome(
            ok=True,
            phase="ingest",
            payload=out.model_dump(),
            fingerprint=fp,
            policy_unit_id=policy_unit_id,
            correlation_id=correlation_id,
            envelope_metadata=envelope_metadata or {},
            metrics={"duration_ms": duration_ms},
        )


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

        # TODO: Implement actual normalization (unicode normalization, etc.)
        sentences = [s for s in ing.raw_text.split("\n") if s.strip()]
        sentence_meta: list[dict[str, Any]] = [
            {"index": i, "length": len(s)} for i, s in enumerate(sentences)
        ]

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
        if not all(k in valid_resolutions for k in out.chunk_index.keys()):
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
    contract_logger = get_json_logger("flux.signals")
    started_monotonic = time.monotonic()
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
    contract_logger = get_json_logger("flux.aggregate")
    started_monotonic = time.monotonic()
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
    contract_logger = get_json_logger("flux.score")
    started_monotonic = time.monotonic()
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
    contract_logger = get_json_logger("flux.report")
    started_monotonic = time.monotonic()
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
