# stdlib
from __future__ import annotations

import os
from typing import Literal

# third-party (pinned in pyproject)
from pydantic import BaseModel, ConfigDict, Field


class IngestConfig(BaseModel):
    """Configuration for ingest phase."""

    model_config = ConfigDict(frozen=True)

    enable_ocr: bool = True
    ocr_threshold: float = 0.85
    max_mb: int = 250

    @classmethod
    def from_env(cls) -> IngestConfig:
        """Create config from environment variables."""
        return cls(
            enable_ocr=os.getenv("FLUX_INGEST_ENABLE_OCR", "true").lower() == "true",
            ocr_threshold=float(os.getenv("FLUX_INGEST_OCR_THRESHOLD", "0.85")),
            max_mb=int(os.getenv("FLUX_INGEST_MAX_MB", "250")),
        )


class NormalizeConfig(BaseModel):
    """Configuration for normalize phase."""

    model_config = ConfigDict(frozen=True)

    unicode_form: Literal["NFC", "NFKC"] = "NFC"
    keep_diacritics: bool = True

    @classmethod
    def from_env(cls) -> NormalizeConfig:
        """Create config from environment variables."""
        return cls(
            unicode_form=os.getenv("FLUX_NORMALIZE_UNICODE_FORM", "NFC"),  # type: ignore[arg-type]
            keep_diacritics=os.getenv("FLUX_NORMALIZE_KEEP_DIACRITICS", "true").lower()
            == "true",
        )


class ChunkConfig(BaseModel):
    """Configuration for chunk phase."""

    model_config = ConfigDict(frozen=True)

    priority_resolution: Literal["MICRO", "MESO", "MACRO"] = "MESO"
    overlap_max: float = 0.15
    max_tokens_micro: int = 400
    max_tokens_meso: int = 1200

    @classmethod
    def from_env(cls) -> ChunkConfig:
        """Create config from environment variables."""
        return cls(
            priority_resolution=os.getenv("FLUX_CHUNK_PRIORITY_RESOLUTION", "MESO"),  # type: ignore[arg-type]
            overlap_max=float(os.getenv("FLUX_CHUNK_OVERLAP_MAX", "0.15")),
            max_tokens_micro=int(os.getenv("FLUX_CHUNK_MAX_TOKENS_MICRO", "400")),
            max_tokens_meso=int(os.getenv("FLUX_CHUNK_MAX_TOKENS_MESO", "1200")),
        )


class SignalsConfig(BaseModel):
    """Configuration for signals phase."""

    model_config = ConfigDict(frozen=True)

    source: Literal["memory", "http"] = "memory"
    http_timeout_s: float = 3.0
    ttl_s: int = 3600
    allow_threshold_override: bool = False

    @classmethod
    def from_env(cls) -> SignalsConfig:
        """Create config from environment variables."""
        return cls(
            source=os.getenv("FLUX_SIGNALS_SOURCE", "memory"),  # type: ignore[arg-type]
            http_timeout_s=float(os.getenv("FLUX_SIGNALS_HTTP_TIMEOUT_S", "3.0")),
            ttl_s=int(os.getenv("FLUX_SIGNALS_TTL_S", "3600")),
            allow_threshold_override=os.getenv(
                "FLUX_SIGNALS_ALLOW_THRESHOLD_OVERRIDE", "false"
            ).lower()
            == "true",
        )


class AggregateConfig(BaseModel):
    """Configuration for aggregate phase."""

    model_config = ConfigDict(frozen=True)

    feature_set: Literal["minimal", "full"] = "full"
    group_by: list[str] = Field(default_factory=lambda: ["policy_area", "year"])

    @classmethod
    def from_env(cls) -> AggregateConfig:
        """Create config from environment variables."""
        group_by_str = os.getenv("FLUX_AGGREGATE_GROUP_BY", "policy_area,year")
        return cls(
            feature_set=os.getenv("FLUX_AGGREGATE_FEATURE_SET", "full"),  # type: ignore[arg-type]
            group_by=[s.strip() for s in group_by_str.split(",") if s.strip()],
        )


class ScoreConfig(BaseModel):
    """Configuration for score phase."""

    model_config = ConfigDict(frozen=True)

    metrics: list[str] = Field(
        default_factory=lambda: ["precision", "coverage", "risk"]
    )
    calibration_mode: Literal["none", "isotonic", "platt"] = "none"

    @classmethod
    def from_env(cls) -> ScoreConfig:
        """Create config from environment variables."""
        metrics_str = os.getenv("FLUX_SCORE_METRICS", "precision,coverage,risk")
        return cls(
            metrics=[s.strip() for s in metrics_str.split(",") if s.strip()],
            calibration_mode=os.getenv("FLUX_SCORE_CALIBRATION_MODE", "none"),  # type: ignore[arg-type]
        )


class ReportConfig(BaseModel):
    """Configuration for report phase."""

    model_config = ConfigDict(frozen=True)

    formats: list[str] = Field(default_factory=lambda: ["json", "md"])
    include_provenance: bool = True

    @classmethod
    def from_env(cls) -> ReportConfig:
        """Create config from environment variables."""
        formats_str = os.getenv("FLUX_REPORT_FORMATS", "json,md")
        return cls(
            formats=[s.strip() for s in formats_str.split(",") if s.strip()],
            include_provenance=os.getenv(
                "FLUX_REPORT_INCLUDE_PROVENANCE", "true"
            ).lower()
            == "true",
        )
