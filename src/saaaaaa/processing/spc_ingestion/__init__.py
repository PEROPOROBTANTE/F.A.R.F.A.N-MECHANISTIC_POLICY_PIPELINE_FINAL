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

from pathlib import Path
import importlib.util
import logging
import unicodedata  # For NFC normalization

from saaaaaa.config.paths import QUESTIONNAIRE_FILE
from saaaaaa.processing.cpp_ingestion.models import CanonPolicyPackage
from saaaaaa.processing.spc_ingestion.converter import SmartChunkConverter
from saaaaaa.processing.spc_ingestion.quality_gates import SPCQualityGates

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
        self.quality_gates = SPCQualityGates()
        logger.info("Pipeline initialized successfully")

    def _load_document_text(self, document_path: Path) -> str:
        """
        Load document text from PDF, TXT, or MD files.

        Args:
            document_path: Path to document file

        Returns:
            Extracted text content

        Raises:
            ValueError: If file type is unsupported
            IOError: If file cannot be read
        """
        suffix = document_path.suffix.lower()

        if suffix == '.pdf':
            # Use PyMuPDF (fitz) for PDF extraction
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(document_path)
                text_parts = []
                for page in doc:
                    text_parts.append(page.get_text())
                doc.close()
                text = '\n'.join(text_parts)

                # Normalize to NFC for deterministic hashing and span calculation
                text = unicodedata.normalize('NFC', text)

                logger.info(f"Extracted {len(text)} characters from PDF ({len(text_parts)} pages)")
                return text
            except ImportError:
                logger.error("PyMuPDF (fitz) not available for PDF extraction")
                raise IOError(
                    "PDF extraction requires PyMuPDF (install with: pip install PyMuPDF). "
                    "Alternatively, convert PDF to text manually."
                )
            except Exception as e:
                logger.error(f"Failed to extract PDF: {e}")
                raise IOError(f"PDF extraction failed: {e}")

        elif suffix in ['.txt', '.md']:
            # Plain text or markdown
            try:
                with open(document_path, 'r', encoding='utf-8') as f:
                    text = f.read()

                # Normalize to NFC for deterministic hashing and span calculation
                text = unicodedata.normalize('NFC', text)

                logger.info(f"Loaded {len(text)} characters from {suffix} file")
                return text
            except IOError as e:
                logger.error(f"Failed to read text file: {e}")
                raise

        else:
            raise ValueError(
                f"Unsupported file type: {suffix}. "
                f"Supported types: .pdf, .txt, .md"
            )

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

        # Quality gate: Validate input file
        validation_input = self.quality_gates.validate_input(document_path)
        if not validation_input["passed"]:
            raise ValueError(
                f"SPC input validation failed: {validation_input['failures']}"
            )
        logger.info(f"Input validation passed (file size: {validation_input['file_size_bytes']} bytes)")

        # Load document text (supports PDF, TXT, MD)
        try:
            document_text = self._load_document_text(document_path)
        except (IOError, ValueError) as e:
            logger.error(f"Failed to load document: {e}")
            raise

        if not document_text or not document_text.strip():
            raise ValueError(f"Document text is empty after extraction: {document_path}")

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

        # Quality gate: Validate chunks
        chunk_dicts = [
            {
                "text": c.text,
                "chunk_id": c.chunk_id,
                "strategic_importance": c.strategic_importance,
                "quality_score": c.confidence_metrics.get("overall_confidence", 0.0),
            }
            for c in smart_chunks
        ]
        validation_chunks = self.quality_gates.validate_chunks(chunk_dicts)
        if not validation_chunks["passed"]:
            raise ValueError(
                f"SPC chunk validation failed: {validation_chunks['failures']}"
            )
        if validation_chunks.get("warnings"):
            logger.warning(f"Chunk validation warnings: {validation_chunks['warnings'][:3]}")
        logger.info(f"Chunk validation passed ({validation_chunks['chunk_count']} chunks)")

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
