"""
SPC (Smart Policy Chunks) Ingestion - Canonical Phase-One
==========================================================

This module provides the canonical phase-one ingestion pipeline for processing
development plans into smart policy chunks with comprehensive analysis.

Main exports:
- CPPIngestionPipeline: Primary ingestion pipeline (for compatibility)
- StrategicChunkingSystem: Core chunking system from smart_policy_chunks_canonic_phase_one

The pipeline performs:
1. Document preprocessing and structural analysis
2. Topic modeling and knowledge graph construction
3. Causal chain extraction
4. Temporal, argumentative, and discourse analysis
5. Smart chunk creation with inter-chunk relationships
6. Quality validation and strategic ranking
"""

import importlib.util
import logging
from pathlib import Path

from saaaaaa.config.paths import QUESTIONNAIRE_FILE
from saaaaaa.processing.cpp_ingestion.models import CanonPolicyPackage
from saaaaaa.processing.spc_ingestion.converter import SmartChunkConverter

logger = logging.getLogger(__name__)

# Load smart_policy_chunks_canonic_phase_one without sys.path manipulation
_root = Path(__file__).parent.parent.parent.parent.parent
_module_path = _root / "scripts" / "smart_policy_chunks_canonic_phase_one.py"

spec = importlib.util.spec_from_file_location(
    "smart_policy_chunks_canonic_phase_one",
    _module_path
)
if spec and spec.loader:
    _module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_module)
    StrategicChunkingSystem = _module.StrategicChunkingSystem
else:
    raise ImportError(f"Cannot load smart_policy_chunks_canonic_phase_one from {_module_path}")


class CPPIngestionPipeline:
    """
    SPC ingestion pipeline with orchestrator-compatible output.

    This class provides the canonical phase-one ingestion pipeline:
    1. Processes documents through StrategicChunkingSystem (15-phase analysis)
    2. Converts SmartPolicyChunk output to CanonPolicyPackage format
    3. Returns orchestrator-ready CanonPolicyPackage

    The pipeline ensures 100% alignment between SPC phase-one output and
    what the orchestrator expects to receive.

    Questionnaire Input Contract (SIN_CARRETA compliance):
    -------------------------------------------------------
    - questionnaire_path is an EXPLICIT input (defaults to canonical path)
    - Must be deterministic, auditable, and manifest-tracked
    - No hidden filesystem dependencies
    """

    def __init__(self, questionnaire_path: Path | None = None):
        """
        Initialize the SPC ingestion pipeline with converter.

        Args:
            questionnaire_path: Optional path to questionnaire file.
                               If None, uses canonical path from saaaaaa.config.paths.QUESTIONNAIRE_FILE
        """
        logger.info("Initializing CPPIngestionPipeline with StrategicChunkingSystem")

        # Store questionnaire path for manifest traceability
        if questionnaire_path is None:
            questionnaire_path = QUESTIONNAIRE_FILE

        self.questionnaire_path = questionnaire_path
        logger.info(f"Questionnaire path: {self.questionnaire_path}")

        self.chunking_system = StrategicChunkingSystem()
        self.converter = SmartChunkConverter()
        logger.info("Pipeline initialized successfully")

    async def process(
        self,
        document_path: Path,
        document_id: str = None,
        title: str = None,
        max_chunks: int = 50
    ) -> CanonPolicyPackage:
        """
        Process a document through the complete SPC pipeline.

        Args:
            document_path: Path to input document
            document_id: Optional document identifier
            title: Optional document title
            max_chunks: Maximum number of chunks to generate

        Returns:
            CanonPolicyPackage: Orchestrator-ready policy package with:
                - ChunkGraph with all chunks and relationships
                - PolicyManifest with axes/programs/projects
                - QualityMetrics from SPC analysis
                - IntegrityIndex for verification
                - Rich SPC data preserved in metadata

        Raises:
            ValueError: If document is empty or invalid
            IOError: If document cannot be read
        """
        logger.info(f"Processing document: {document_path}")

        # Read document
        try:
            with open(document_path, encoding='utf-8') as f:
                document_text = f.read()
        except OSError as e:
            logger.error(f"Failed to read document: {e}")
            raise

        if not document_text or not document_text.strip():
            raise ValueError(f"Document is empty or contains only whitespace: {document_path}")

        logger.info(f"Document loaded: {len(document_text)} characters")

        # Prepare metadata
        metadata = {
            'document_id': document_id or str(document_path.stem),
            'title': title or document_path.name,
            'version': 'v3.0',
            'source_path': str(document_path)
        }

        # Process through chunking system (15-phase analysis)
        logger.info("Starting StrategicChunkingSystem.generate_smart_chunks()")
        smart_chunks = self.chunking_system.generate_smart_chunks(document_text, metadata)
        logger.info(f"Generated {len(smart_chunks)} SmartPolicyChunks")

        # Limit chunks if requested
        if max_chunks > 0 and len(smart_chunks) > max_chunks:
            logger.info(f"Limiting to {max_chunks} chunks (from {len(smart_chunks)})")
            smart_chunks = smart_chunks[:max_chunks]

        # Convert to CanonPolicyPackage
        logger.info("Converting SmartPolicyChunks to CanonPolicyPackage")
        canon_package = self.converter.convert_to_canon_package(smart_chunks, metadata)

        # Log quality metrics
        if canon_package.quality_metrics:
            logger.info(
                f"Quality metrics - "
                f"provenance: {canon_package.quality_metrics.provenance_completeness:.2%}, "
                f"coherence: {canon_package.quality_metrics.structural_consistency:.2%}, "
                f"coverage: {canon_package.quality_metrics.chunk_context_coverage:.2%}"
            )

        logger.info(f"Pipeline complete: {len(canon_package.chunk_graph.chunks)} chunks in package")
        return canon_package


__all__ = [
    'CPPIngestionPipeline',
    'StrategicChunkingSystem',
    'SmartChunkConverter',
]
