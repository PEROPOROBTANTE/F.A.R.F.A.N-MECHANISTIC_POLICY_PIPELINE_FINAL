# stdlib
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

# third-party (pinned in pyproject)
from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    import polars as pl
    import pyarrow as pa


class DocManifest(BaseModel):
    """Document manifest with identity and provenance."""

    model_config = ConfigDict(frozen=True)

    document_id: str
    source_uri: str | None = None
    schema_version: str = "FLUX-2025.1"


class PhaseOutcome(BaseModel):
    """Outcome from a pipeline phase execution.

    Authoritative boundary contract between phases and orchestrators.
    All metadata must be preserved across phase boundaries.
    """

    model_config = ConfigDict(frozen=True)

    ok: bool
    phase: Literal[
        "ingest", "normalize", "chunk", "signals", "aggregate", "score", "report"
    ]
    payload: dict[str, Any]  # concrete model cast below
    fingerprint: str
    policy_unit_id: str | None = None
    correlation_id: str | None = None
    envelope_metadata: dict[str, str] = Field(default_factory=dict)
    metrics: dict[str, float] = Field(default_factory=dict)


# Ingest Phase
class IngestDeliverable(BaseModel):
    """Deliverable from ingest phase."""

    model_config = ConfigDict(frozen=True)

    manifest: DocManifest
    raw_text: str
    tables: list[dict[str, Any]] = Field(default_factory=list)
    provenance_ok: bool


# Normalize Phase
class NormalizeExpectation(BaseModel):
    """Expected input for normalize phase."""

    model_config = ConfigDict(frozen=True)

    manifest: DocManifest
    raw_text: str


class NormalizeDeliverable(BaseModel):
    """Deliverable from normalize phase."""

    model_config = ConfigDict(frozen=True)

    sentences: list[str]
    sentence_meta: list[dict[str, Any]]


# Chunk Phase
class ChunkExpectation(BaseModel):
    """Expected input for chunk phase."""

    model_config = ConfigDict(frozen=True)

    sentences: list[str]
    sentence_meta: list[dict[str, Any]]


class ChunkDeliverable(BaseModel):
    """Deliverable from chunk phase."""

    model_config = ConfigDict(frozen=True)

    chunks: list[dict[str, Any]]  # id, text, span, facets
    chunk_index: dict[str, list[str]]  # micro/meso/macro ids


# Signals Phase
class SignalsExpectation(BaseModel):
    """Expected input for signals phase."""

    model_config = ConfigDict(frozen=True)

    chunks: list[dict[str, Any]]


class SignalsDeliverable(BaseModel):
    """Deliverable from signals phase."""

    model_config = ConfigDict(frozen=True)

    enriched_chunks: list[dict[str, Any]]  # adds patterns/entities/thresholds used
    used_signals: dict[str, Any]  # version, policy_area, hash, keys_used


# Aggregate Phase
class AggregateExpectation(BaseModel):
    """Expected input for aggregate phase."""

    model_config = ConfigDict(frozen=True)

    enriched_chunks: list[dict[str, Any]]


class AggregateDeliverable(BaseModel):
    """Deliverable from aggregate phase."""

    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)

    features: pa.Table  # Arrow table of engineered features
    aggregation_meta: dict[str, Any]


# Score Phase
class ScoreExpectation(BaseModel):
    """Expected input for score phase."""

    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)

    features: pa.Table


class ScoreDeliverable(BaseModel):
    """Deliverable from score phase."""

    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)

    scores: pl.DataFrame  # columns: item_id, metric, value
    calibration: dict[str, Any]


# Report Phase
class ReportExpectation(BaseModel):
    """Expected input for report phase."""

    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)

    scores: pl.DataFrame


class ReportDeliverable(BaseModel):
    """Deliverable from report phase."""

    model_config = ConfigDict(frozen=True)

    artifacts: dict[str, str]  # name -> path/URI
    summary: dict[str, Any]
