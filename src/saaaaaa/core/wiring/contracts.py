"""Contract models for wiring validation.

Defines Pydantic models for each link's deliverable and expectation.
Validation ensures type safety and completeness at every boundary.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class CPPDeliverable(BaseModel):
    """Contract for CPP ingestion output (Deliverable).

    Note: CPP (Canon Policy Package) is the legacy name for SPC (Smart Policy Chunks).
    Use SPCDeliverable for new code.
    """

    chunk_graph: dict[str, Any] = Field(
        description="Chunk graph with all chunks"
    )
    policy_manifest: dict[str, Any] = Field(
        description="Policy metadata manifest"
    )
    provenance_completeness: float = Field(
        ge=0.0,
        le=1.0,
        description="Provenance completeness score (must be 1.0)"
    )
    schema_version: str = Field(
        description="CPP schema version"
    )

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }

    @field_validator("provenance_completeness")
    @classmethod
    def validate_completeness(cls, v: float) -> float:
        """Ensure provenance is 100% complete."""
        if v != 1.0:
            raise ValueError(
                f"provenance_completeness must be 1.0, got {v}. "
                "Ensure ingestion pipeline completed successfully."
            )
        return v


class SPCDeliverable(BaseModel):
    """Contract for SPC (Smart Policy Chunks) ingestion output (Deliverable).

    This is the preferred terminology for new code. SPC is the successor to CPP.
    """

    chunk_graph: dict[str, Any] = Field(
        description="Chunk graph with all chunks"
    )
    policy_manifest: dict[str, Any] = Field(
        description="Policy metadata manifest"
    )
    provenance_completeness: float = Field(
        ge=0.0,
        le=1.0,
        description="Provenance completeness score (must be 1.0)"
    )
    schema_version: str = Field(
        description="SPC schema version"
    )

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }

    @field_validator("provenance_completeness")
    @classmethod
    def validate_completeness(cls, v: float) -> float:
        """Ensure provenance is 100% complete."""
        if v != 1.0:
            raise ValueError(
                f"provenance_completeness must be 1.0, got {v}. "
                "Ensure SPC ingestion pipeline completed successfully."
            )
        return v


class AdapterExpectation(BaseModel):
    """Contract for CPPAdapter input (Expectation)."""

    chunk_graph: dict[str, Any] = Field(
        description="Must have chunk_graph with chunks"
    )
    policy_manifest: dict[str, Any] = Field(
        description="Must have policy_manifest"
    )
    provenance_completeness: float = Field(
        ge=1.0,
        le=1.0,
        description="Must be exactly 1.0"
    )

    model_config = {
        "frozen": True,
        "extra": "allow",  # Allow additional fields
    }


class PreprocessedDocumentDeliverable(BaseModel):
    """Contract for CPPAdapter output (Deliverable)."""

    sentence_metadata: list[dict[str, Any]] = Field(
        min_length=1,
        description="Must have at least one sentence"
    )
    resolution_index: dict[str, Any] = Field(
        description="Resolution index must be consistent"
    )
    provenance_completeness: float = Field(
        ge=1.0,
        le=1.0,
        description="Must maintain 1.0 completeness"
    )
    document_id: str = Field(
        min_length=1,
        description="Document ID must be non-empty"
    )

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }


class OrchestratorExpectation(BaseModel):
    """Contract for Orchestrator input (Expectation)."""

    sentence_metadata: list[dict[str, Any]] = Field(
        min_length=1,
        description="Requires sentence_metadata"
    )
    document_id: str = Field(
        min_length=1,
        description="Requires document_id"
    )

    model_config = {
        "frozen": True,
        "extra": "allow",
    }


class ArgRouterPayloadDeliverable(BaseModel):
    """Contract for Orchestrator to ArgRouter (Deliverable)."""

    class_name: str = Field(
        min_length=1,
        description="Target class name"
    )
    method_name: str = Field(
        min_length=1,
        description="Target method name"
    )
    payload: dict[str, Any] = Field(
        description="Method arguments payload"
    )

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }


class ArgRouterExpectation(BaseModel):
    """Contract for ArgRouter input (Expectation)."""

    class_name: str = Field(
        min_length=1,
        description="Class must exist in registry"
    )
    method_name: str = Field(
        min_length=1,
        description="Method must exist on class"
    )
    payload: dict[str, Any] = Field(
        description="Payload with required arguments"
    )

    model_config = {
        "frozen": True,
        "extra": "allow",
    }


class ExecutorInputDeliverable(BaseModel):
    """Contract for ArgRouter to Executor (Deliverable)."""

    args: tuple[Any, ...] = Field(
        description="Positional arguments"
    )
    kwargs: dict[str, Any] = Field(
        description="Keyword arguments"
    )
    method_signature: str = Field(
        description="Target method signature for validation"
    )

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }


class SignalPackDeliverable(BaseModel):
    """Contract for SignalsClient output (Deliverable)."""

    version: str = Field(
        description="Signal pack version (must be present)"
    )
    policy_area: str = Field(
        description="Policy area for signals"
    )
    patterns: list[str] = Field(
        default_factory=list,
        description="Text patterns"
    )
    indicators: list[str] = Field(
        default_factory=list,
        description="KPI indicators"
    )

    model_config = {
        "frozen": True,
        "extra": "allow",  # Allow additional signal fields
    }

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate version format."""
        if not v or v.strip() == "":
            raise ValueError("version must be non-empty")
        return v


class SignalRegistryExpectation(BaseModel):
    """Contract for SignalRegistry input (Expectation)."""

    version: str = Field(
        min_length=1,
        description="Requires version"
    )
    policy_area: str = Field(
        min_length=1,
        description="Requires policy_area"
    )

    model_config = {
        "frozen": True,
        "extra": "allow",
    }


class EnrichedChunkDeliverable(BaseModel):
    """Contract for Executor output (Deliverable)."""

    chunk_id: str = Field(
        min_length=1,
        description="Chunk identifier"
    )
    used_signals: list[str] = Field(
        default_factory=list,
        description="Signals used during execution"
    )
    enrichment: dict[str, Any] = Field(
        description="Enrichment data"
    )

    model_config = {
        "frozen": True,
        "extra": "allow",
    }


class AggregateExpectation(BaseModel):
    """Contract for Aggregate input (Expectation)."""

    enriched_chunks: list[dict[str, Any]] = Field(
        min_length=1,
        description="Must have at least one enriched chunk"
    )

    model_config = {
        "frozen": True,
        "extra": "allow",
    }


class FeatureTableDeliverable(BaseModel):
    """Contract for Aggregate output (Deliverable)."""

    table_type: str = Field(
        description="Must be 'pyarrow.Table'"
    )
    num_rows: int = Field(
        ge=1,
        description="Must have at least one row"
    )
    column_names: list[str] = Field(
        min_length=1,
        description="Must have required columns"
    )

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }


class ScoreExpectation(BaseModel):
    """Contract for Score input (Expectation)."""

    table_type: str = Field(
        description="Must be pa.Table"
    )
    required_columns: list[str] = Field(
        min_length=1,
        description="Required columns for scoring"
    )

    model_config = {
        "frozen": True,
        "extra": "allow",
    }


class ScoresDeliverable(BaseModel):
    """Contract for Score output (Deliverable)."""

    dataframe_type: str = Field(
        description="Must be 'polars.DataFrame'"
    )
    num_rows: int = Field(
        ge=1,
        description="Must have at least one row"
    )
    metrics_computed: list[str] = Field(
        min_length=1,
        description="Metrics that were computed"
    )

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }


class ReportExpectation(BaseModel):
    """Contract for Report input (Expectation)."""

    dataframe_type: str = Field(
        description="Must be pl.DataFrame"
    )
    metrics_present: list[str] = Field(
        min_length=1,
        description="Metrics must be present"
    )
    manifest_present: bool = Field(
        description="Manifest must be provided"
    )

    model_config = {
        "frozen": True,
        "extra": "allow",
    }


class ReportDeliverable(BaseModel):
    """Contract for Report output (Deliverable)."""

    report_uris: dict[str, str] = Field(
        min_length=1,
        description="Mapping of report name to URI"
    )
    all_reports_generated: bool = Field(
        description="All declared reports generated"
    )

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }


__all__ = [
    'CPPDeliverable',
    'SPCDeliverable',
    'AdapterExpectation',
    'PreprocessedDocumentDeliverable',
    'OrchestratorExpectation',
    'ArgRouterPayloadDeliverable',
    'ArgRouterExpectation',
    'ExecutorInputDeliverable',
    'SignalPackDeliverable',
    'SignalRegistryExpectation',
    'EnrichedChunkDeliverable',
    'AggregateExpectation',
    'FeatureTableDeliverable',
    'ScoreExpectation',
    'ScoresDeliverable',
    'ReportExpectation',
    'ReportDeliverable',
]
