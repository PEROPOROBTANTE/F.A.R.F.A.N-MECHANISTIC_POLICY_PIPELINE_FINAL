"""
FLUX Pipeline - Fine-grained, deterministic processing pipeline.

Provides explicit contracts, typed configs, deterministic execution,
and comprehensive quality gates.
"""

from __future__ import annotations

from .cli import app as cli_app
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
from .phases import (
    run_aggregate,
    run_chunk,
    # run_ingest removed - use SPC CPPIngestionPipeline as canonical entry point
    run_normalize,
    run_report,
    run_score,
    run_signals,
)

__all__ = [
    # CLI
    "cli_app",
    # Configs
    "IngestConfig",
    "NormalizeConfig",
    "ChunkConfig",
    "SignalsConfig",
    "AggregateConfig",
    "ScoreConfig",
    "ReportConfig",
    # Models
    "DocManifest",
    "PhaseOutcome",
    "IngestDeliverable",
    "NormalizeExpectation",
    "NormalizeDeliverable",
    "ChunkExpectation",
    "ChunkDeliverable",
    "SignalsExpectation",
    "SignalsDeliverable",
    "AggregateExpectation",
    "AggregateDeliverable",
    "ScoreExpectation",
    "ScoreDeliverable",
    "ReportExpectation",
    "ReportDeliverable",
    # Phases (Note: run_ingest removed - use SPC CPPIngestionPipeline)
    "run_normalize",
    "run_chunk",
    "run_signals",
    "run_aggregate",
    "run_score",
    "run_report",
]
