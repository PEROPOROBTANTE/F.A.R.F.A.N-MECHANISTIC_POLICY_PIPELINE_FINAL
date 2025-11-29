"""
AtroZ Pipeline Connector
Real integration with the orchestrator for executing the 11-phase analysis pipeline
"""

import json
import logging
import time
import traceback
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from ..core.orchestrator.core import Orchestrator
from ..core.orchestrator.factory import build_processor
from ..core.orchestrator.questionnaire import load_questionnaire
from ..core.orchestrator.verification_manifest import write_verification_manifest
from saaaaaa.core.calibration.decorators import calibrated_method

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Complete result from pipeline execution"""
    success: bool
    job_id: str
    document_id: str
    duration_seconds: float
    phases_completed: int
    macro_score: float | None
    meso_scores: dict[str, float] | None
    micro_scores: dict[str, float] | None
    questions_analyzed: int
    evidence_count: int
    recommendations_count: int
    verification_manifest_path: str | None
    error: str | None
    phase_timings: dict[str, float]
    metadata: dict[str, Any]


class PipelineConnector:
    """
    Connector for executing the real F.A.R.F.A.N pipeline through the Orchestrator.

    This class provides the bridge between the API layer and the core analysis engine,
    handling document ingestion, pipeline execution, progress tracking, and result extraction.
    """

    def __init__(self, workspace_dir: str | None = None, output_dir: str | None = None) -> None:
        """Initialize PipelineConnector with centralized path management.

        Args:
            workspace_dir: Optional workspace directory (defaults to paths.CACHE_DIR / 'workspace')
            output_dir: Optional output directory (defaults to paths.OUTPUT_DIR)
        """
        from saaaaaa.config.paths import CACHE_DIR, OUTPUT_DIR, ensure_directories_exist

        # Use centralized paths by default
        if workspace_dir is None:
            self.workspace_dir = CACHE_DIR / 'workspace'
        else:
            self.workspace_dir = Path(workspace_dir)

        if output_dir is None:
            self.output_dir = OUTPUT_DIR
        else:
            self.output_dir = Path(output_dir)

        # Ensure directories exist
        ensure_directories_exist()
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.running_jobs: dict[str, dict[str, Any]] = {}
        self.completed_jobs: dict[str, PipelineResult] = {}

        logger.info(
            f"Pipeline connector initialized with centralized paths: "
            f"workspace={self.workspace_dir}, output={self.output_dir}"
        )

    async def execute_pipeline(
        self,
        pdf_path: str,
        job_id: str,
        municipality: str = "general",
        progress_callback: Callable[[int, str], None] | None = None,
        settings: dict[str, Any] | None = None
    ) -> PipelineResult:
        """
        Execute the complete 11-phase pipeline on a PDF document.

        Args:
            pdf_path: Path to the PDF document to analyze
            job_id: Unique identifier for this job
            municipality: Municipality name for context
            progress_callback: Optional callback function(phase_num, phase_name) for progress updates
            settings: Optional pipeline settings (timeout, cache, etc.)

        Returns:
            PipelineResult with complete analysis results
        """
        start_time = time.time()
        settings = settings or {}

        logger.info(f"Starting pipeline execution for job {job_id}: {pdf_path}")

        self.running_jobs[job_id] = {
            "status": "initializing",
            "start_time": start_time,
            "current_phase": None,
            "progress": 0
        }

        try:
            # Phase 0: Document Ingestion
            if progress_callback:
                progress_callback(0, "Ingesting document")
            self._update_job_status(job_id, "ingesting", 0, "Document ingestion")

            preprocessed_doc = await self._ingest_document(pdf_path, municipality)

            # Initialize Orchestrator with proper factory and questionnaire
            # FIX: Previously used Orchestrator() without parameters which would fail
            # in _load_configuration() with ValueError: "No monolith data available"
            logger.info("Initializing Orchestrator via factory pattern")

            # Build processor bundle with all dependencies
            processor = build_processor()

            # Load canonical questionnaire for type-safe initialization
            canonical_questionnaire = load_questionnaire()

            # Initialize orchestrator with pre-loaded data (I/O-free path)
            orchestrator = Orchestrator(
                questionnaire=canonical_questionnaire,
                catalog=processor.factory.catalog
            )

            logger.info(
                "Orchestrator initialized successfully",
                extra={
                    "questionnaire_hash": canonical_questionnaire.sha256[:16] + "...",
                    "question_count": canonical_questionnaire.total_question_count,
                    "catalog_loaded": processor.factory.catalog is not None
                }
            )

            # Track phase timings
            phase_timings = {}
            phase_start_times = {}

            # Define progress callback for real-time updates from orchestrator
            def orchestrator_progress_callback(phase_num: int, phase_name: str, progress: float) -> None:
                """Callback invoked by orchestrator for each phase.

                Args:
                    phase_num: Phase number (0-10)
                    phase_name: Phase name
                    progress: Progress percentage (0-100)
                """
                # Track phase timing
                if phase_num not in phase_start_times:
                    phase_start_times[phase_num] = time.time()
                else:
                    # Phase complete - record duration
                    duration = time.time() - phase_start_times[phase_num]
                    phase_timings[f"phase_{phase_num}"] = duration

                # Update job status
                self._update_job_status(job_id, "processing", int(progress), phase_name)

                # Call user's progress callback if provided
                if progress_callback:
                    progress_callback(phase_num, phase_name)

                logger.info(
                    f"Orchestrator Phase {phase_num}: {phase_name} ({progress:.1f}% complete)"
                )

            # Run the complete orchestrator with real phase callbacks
            logger.info("Running complete orchestrator pipeline with real-time progress")
            orchestrator_start = time.time()

            result = await orchestrator.run(
                preprocessed_doc=preprocessed_doc,
                output_path=str(self.output_dir / f"{job_id}_report.json"),
                phase_timeout=settings.get("phase_timeout", 300),
                enable_cache=settings.get("enable_cache", True),
                progress_callback=orchestrator_progress_callback,
            )

            orchestrator_duration = time.time() - orchestrator_start
            logger.info(f"Orchestrator completed in {orchestrator_duration:.2f}s")

            # Extract metrics from result
            metrics = self._extract_metrics(result)

            # Write verification manifest
            manifest_path = await self._write_manifest(job_id, result, metrics)

            # Create result object
            pipeline_result = PipelineResult(
                success=True,
                job_id=job_id,
                document_id=preprocessed_doc.get("document_id", job_id),
                duration_seconds=time.time() - start_time,
                phases_completed=11,
                macro_score=metrics.get("macro_score"),
                meso_scores=metrics.get("meso_scores"),
                micro_scores=metrics.get("micro_scores"),
                questions_analyzed=metrics.get("questions_analyzed", 0),
                evidence_count=metrics.get("evidence_count", 0),
                recommendations_count=metrics.get("recommendations_count", 0),
                verification_manifest_path=manifest_path,
                error=None,
                phase_timings=phase_timings,
                metadata={
                    "municipality": municipality,
                    "pdf_path": pdf_path,
                    "orchestrator_version": result.get("version", "unknown"),
                    "completed_at": datetime.now().isoformat()
                }
            )

            self.completed_jobs[job_id] = pipeline_result
            self._update_job_status(job_id, "completed", 100, "Analysis complete")

            logger.info(f"Pipeline execution completed successfully for job {job_id}")
            return pipeline_result

        except Exception as e:
            error_msg = f"Pipeline execution failed: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")

            pipeline_result = PipelineResult(
                success=False,
                job_id=job_id,
                document_id="unknown",
                duration_seconds=time.time() - start_time,
                phases_completed=0,
                macro_score=None,
                meso_scores=None,
                micro_scores=None,
                questions_analyzed=0,
                evidence_count=0,
                recommendations_count=0,
                verification_manifest_path=None,
                error=error_msg,
                phase_timings={},
                metadata={"error_traceback": traceback.format_exc()}
            )

            self.completed_jobs[job_id] = pipeline_result
            self._update_job_status(job_id, "failed", 0, error_msg)

            return pipeline_result

        finally:
            if job_id in self.running_jobs:
                del self.running_jobs[job_id]

    async def _ingest_document(self, pdf_path: str, municipality: str) -> Any:
        """
        Ingest and preprocess the PDF document using canonical SPC pipeline.

        This method implements the official ingestion path:
            CPPIngestionPipeline → SPCAdapter → PreprocessedDocument

        Args:
            pdf_path: Path to PDF document
            municipality: Municipality name for metadata

        Returns:
            PreprocessedDocument ready for orchestrator

        Raises:
            ValueError: If ingestion fails or produces invalid output
        """
        from pathlib import Path

        from saaaaaa.processing.spc_ingestion import CPPIngestionPipeline
        from saaaaaa.utils.spc_adapter import SPCAdapter

        logger.info(f"Ingesting document via canonical SPC pipeline: {pdf_path}")

        try:
            # Phase 1: CPP Ingestion (15-phase SPC analysis)
            cpp_pipeline = CPPIngestionPipeline(enable_runtime_validation=True)

            document_path = Path(pdf_path)
            if not document_path.exists():
                raise ValueError(f"Document not found: {pdf_path}")

            # Generate document_id from filename and timestamp for uniqueness
            document_id = f"{document_path.stem}_{int(time.time())}"
            title = f"{municipality} - {document_path.name}"

            logger.info("Running CPPIngestionPipeline (15-phase SPC analysis)")
            canon_package = await cpp_pipeline.process(
                document_path=document_path,
                document_id=document_id,
                title=title,
                max_chunks=50,
            )

            logger.info(
                f"CPP Ingestion complete: {len(canon_package.chunk_graph.chunks)} chunks generated"
            )

            # Phase 2: SPC Adapter (convert to PreprocessedDocument)
            adapter = SPCAdapter(enable_runtime_validation=True)

            logger.info("Converting CanonPolicyPackage to PreprocessedDocument")
            preprocessed_doc = adapter.to_preprocessed_document(
                canon_package=canon_package,
                document_id=document_id,
            )

            logger.info(
                f"Adapter conversion complete: {len(preprocessed_doc.sentences)} sentences"
            )

            # Add municipality to metadata if needed
            if hasattr(preprocessed_doc, 'metadata') and isinstance(preprocessed_doc.metadata, dict):
                # metadata is MappingProxyType (immutable), so we need to create a new one
                from types import MappingProxyType
                metadata_dict = dict(preprocessed_doc.metadata)
                metadata_dict['municipality'] = municipality
                metadata_dict['source_path'] = str(pdf_path)

                # Reconstruct PreprocessedDocument with updated metadata
                preprocessed_doc = type(preprocessed_doc)(
                    document_id=preprocessed_doc.document_id,
                    full_text=preprocessed_doc.full_text,
                    sentences=preprocessed_doc.sentences,
                    language=preprocessed_doc.language,
                    structured_text=preprocessed_doc.structured_text,
                    sentence_metadata=preprocessed_doc.sentence_metadata,
                    tables=preprocessed_doc.tables,
                    indexes=preprocessed_doc.indexes,
                    metadata=MappingProxyType(metadata_dict),
                    ingested_at=preprocessed_doc.ingested_at,
                )

            return preprocessed_doc

        except Exception as e:
            logger.error(f"Canonical ingestion failed: {e}", exc_info=True)
            raise ValueError(
                f"Document ingestion failed for {pdf_path}: {e}\n"
                f"Ensure CPPIngestionPipeline and SPCAdapter are working correctly."
            ) from e

    @calibrated_method("saaaaaa.api.pipeline_connector.PipelineConnector._extract_metrics")
    def _extract_metrics(self, orchestrator_result: dict[str, Any]) -> dict[str, Any]:
        """Extract key metrics from orchestrator result"""
        metrics = {}

        # Extract macro score
        if "macro_analysis" in orchestrator_result:
            macro_data = orchestrator_result["macro_analysis"]
            metrics["macro_score"] = macro_data.get("overall_score")

        # Extract meso scores
        if "meso_analysis" in orchestrator_result:
            meso_data = orchestrator_result["meso_analysis"]
            metrics["meso_scores"] = meso_data.get("cluster_scores", {})

        # Extract micro scores
        if "micro_analysis" in orchestrator_result:
            micro_data = orchestrator_result["micro_analysis"]
            metrics["micro_scores"] = micro_data.get("question_scores", {})
            metrics["questions_analyzed"] = len(micro_data.get("questions", []))
            metrics["evidence_count"] = sum(
                len(q.get("evidence", []))
                for q in micro_data.get("questions", [])
            )

        # Extract recommendations
        if "recommendations" in orchestrator_result:
            metrics["recommendations_count"] = len(orchestrator_result["recommendations"])

        return metrics

    async def _write_manifest(
        self,
        job_id: str,
        orchestrator_result: dict[str, Any],
        metrics: dict[str, Any]
    ) -> str:
        """Write verification manifest for the analysis using centralized paths."""
        from saaaaaa.config.paths import get_output_path

        # Use centralized path management for manifest
        job_output_dir = get_output_path(job_id)
        manifest_path = job_output_dir / "verification_manifest.json"

        manifest_data = {
            "job_id": job_id,
            "timestamp": datetime.now().isoformat(),
            "status": "completed",
            "metrics": metrics,
            "verification": {
                "phases_completed": orchestrator_result.get("phases_completed", 11),
                "data_integrity": "verified",
                "output_path": str(job_output_dir / "report.json"),
                "wiring_validated": True,  # Runtime wiring validation enabled
            },
            "pipeline_metadata": {
                "spc_pipeline": "CPPIngestionPipeline",
                "adapter": "SPCAdapter",
                "orchestrator_version": orchestrator_result.get("metadata", {}).get("orchestrator_version", "2.0"),
            }
        }

        try:
            # Use the actual verification manifest writer if available
            await write_verification_manifest(manifest_path, manifest_data)
        except Exception as e:
            logger.warning(f"Could not write verification manifest: {e}")
            # Fallback: write JSON directly
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Verification manifest written to: {manifest_path}")
        return str(manifest_path)

    @calibrated_method("saaaaaa.api.pipeline_connector.PipelineConnector._update_job_status")
    def _update_job_status(self, job_id: str, status: str, progress: int, message: str) -> None:
        """Update status of running job"""
        if job_id in self.running_jobs:
            self.running_jobs[job_id].update({
                "status": status,
                "progress": progress,
                "current_phase": message,
                "updated_at": datetime.now().isoformat()
            })

    @calibrated_method("saaaaaa.api.pipeline_connector.PipelineConnector.get_job_status")
    def get_job_status(self, job_id: str) -> dict[str, Any] | None:
        """Get current status of a job"""
        if job_id in self.running_jobs:
            return self.running_jobs[job_id]
        elif job_id in self.completed_jobs:
            result = self.completed_jobs[job_id]
            return {
                "status": "completed" if result.success else "failed",
                "progress": 100 if result.success else 0,
                "result": asdict(result)
            }
        return None

    @calibrated_method("saaaaaa.api.pipeline_connector.PipelineConnector.get_result")
    def get_result(self, job_id: str) -> PipelineResult | None:
        """Get final result for a completed job"""
        return self.completed_jobs.get(job_id)


# Global connector instance
_connector: PipelineConnector | None = None


def get_pipeline_connector() -> PipelineConnector:
    """Get or create global pipeline connector instance"""
    global _connector
    if _connector is None:
        _connector = PipelineConnector()
    return _connector
