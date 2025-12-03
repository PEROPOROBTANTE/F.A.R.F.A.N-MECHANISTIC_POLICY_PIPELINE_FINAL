"""
Core type definitions shared across layers.

This module contains types that need to be referenced by both core and analysis
layers without creating circular dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Literal
import re

__all__ = [
    "CategoriaCausal",
    "ChunkData",
    "PreprocessedDocument",
    "Provenance",
]


class CategoriaCausal(Enum):
    """
    Jerarquía axiomática de categorías causales en una teoría de cambio.
    El orden numérico impone la secuencia lógica obligatoria.

    Originally from farfan_core.analysis.teoria_cambio, moved here to break
    architectural dependency (core should not import from analysis).
    """

    INSUMOS = 1
    ACTIVIDADES = 2
    PRODUCTOS = 3
    RESULTADOS = 4
    CAUSALIDAD = 5


@dataclass(frozen=True)
class Provenance:
    """Provenance metadata for a chunk."""

    page_number: int
    section_header: str | None = None
    bbox: tuple[float, float, float, float] | None = None
    span_in_page: tuple[int, int] | None = None
    source_file: str | None = None


@dataclass(frozen=True)
class ChunkData:
    """Single semantic chunk from SPC (Smart Policy Chunks).

    Preserves chunk structure and metadata from the ingestion pipeline,
    enabling chunk-aware executor routing and scoped processing.
    """

    id: int
    chunk_id: str | None = None
    text: str
    chunk_type: Literal[
        "diagnostic", "activity", "indicator", "resource", "temporal", "entity"
    ]
    sentences: list[int]
    tables: list[int]
    start_pos: int
    end_pos: int
    confidence: float
    edges_out: list[int] = field(default_factory=list)
    edges_in: list[int] = field(default_factory=list)
    policy_area_id: str | None = None
    dimension_id: str | None = None
    provenance: Provenance | None = None

    _CHUNK_ID_PATTERN = re.compile(r"^PA(0[1-9]|10)-DIM(0[1-6])$")

    def __post_init__(self) -> None:
        """Validate chunk_id presence and format (PA{01-10}-DIM{01-06})."""
        chunk_id = self.chunk_id
        if chunk_id is None:
            if self.policy_area_id and self.dimension_id:
                chunk_id = f"{self.policy_area_id}-{self.dimension_id}"
                object.__setattr__(self, "chunk_id", chunk_id)
            else:
                raise ValueError(
                    "chunk_id is required and must follow format PA{01-10}-DIM{01-06}. "
                    "Provide chunk_id explicitly or set both policy_area_id and dimension_id "
                    "to derive it."
                )

        if not self._CHUNK_ID_PATTERN.match(chunk_id):
            raise ValueError(
                f"Invalid chunk_id '{chunk_id}'. Expected format PA{{01-10}}-DIM{{01-06}}."
            )

        # Ensure consistency between chunk_id and policy/dimension identifiers if present
        match = self._CHUNK_ID_PATTERN.match(chunk_id)
        if match:
            pa_code = f"PA{match.group(1)}"
            dim_code = f"DIM{match.group(2)}"
            if self.policy_area_id and self.policy_area_id != pa_code:
                raise ValueError(
                    f"chunk_id {chunk_id} mismatches policy_area_id {self.policy_area_id}"
                )
            if self.dimension_id and self.dimension_id != dim_code:
                raise ValueError(
                    f"chunk_id {chunk_id} mismatches dimension_id {self.dimension_id}"
                )


@dataclass
class PreprocessedDocument:
    """Orchestrator representation of a processed document.

    This is the normalized document format used internally by the orchestrator.
    It can be constructed from ingestion payloads or created directly.
    """

    document_id: str
    raw_text: str
    sentences: list[Any]
    tables: list[Any]
    metadata: dict[str, Any]
    source_path: Path | None = None
    sentence_metadata: list[Any] = field(default_factory=list)
    indexes: dict[str, Any] | None = None
    structured_text: dict[str, Any] | None = None
    language: str | None = None
    ingested_at: datetime | None = None
    full_text: str | None = None

    chunks: list[ChunkData] = field(default_factory=list)
    chunk_index: dict[str, int] = field(default_factory=dict)
    chunk_graph: dict[str, Any] = field(default_factory=dict)
    processing_mode: Literal["flat", "chunked"] = "chunked"

    def __post_init__(self) -> None:
        """Validate document fields after initialization.

        Raises:
            ValueError: If raw_text is empty or whitespace-only
        """
        if (not self.raw_text or not self.raw_text.strip()) and self.full_text:
            self.raw_text = self.full_text
        if not self.raw_text or not self.raw_text.strip():
            raise ValueError(
                "PreprocessedDocument cannot have empty raw_text. "
                "Use PreprocessedDocument.ensure() to create from SPC pipeline."
            )
        if self.processing_mode != "chunked":
            raise ValueError(
                f"processing_mode must be 'chunked' for irrigation; got {self.processing_mode!r}"
            )

    @staticmethod
    def _dataclass_to_dict(value: Any) -> Any:
        """Convert a dataclass to a dictionary if applicable."""
        from dataclasses import asdict, is_dataclass

        if is_dataclass(value):
            return asdict(value)
        return value

    @classmethod
    def ensure(
        cls,
        document: Any,
        *,
        document_id: str | None = None,
        use_spc_ingestion: bool = True,
    ) -> PreprocessedDocument:
        """Normalize arbitrary ingestion payloads into orchestrator documents.

        Args:
            document: Document to normalize (PreprocessedDocument or CanonPolicyPackage)
            document_id: Optional document ID override
            use_spc_ingestion: Must be True (SPC is now the only supported ingestion method)

        Returns:
            PreprocessedDocument instance

        Raises:
            ValueError: If use_spc_ingestion is False
            TypeError: If document type is not supported
        """
        import logging

        logger = logging.getLogger(__name__)

        if not use_spc_ingestion:
            raise ValueError(
                "SPC ingestion is now required. Set use_spc_ingestion=True or remove the parameter. "
                "Legacy ingestion methods (document_ingestion module) are no longer supported."
            )

        if isinstance(document, type):
            class_name = getattr(document, "__name__", str(document))
            raise TypeError(
                f"Expected document instance, got class type '{class_name}'. "
                "Pass an instance of the document, not the class itself."
            )

        if isinstance(document, cls):
            return document

        if hasattr(document, "chunk_graph"):
            chunk_graph = getattr(document, "chunk_graph", None)
            if chunk_graph is None:
                raise ValueError(
                    "Document has chunk_graph attribute but it is None. "
                    "Ensure SPC ingestion pipeline completed successfully."
                )

            if not hasattr(chunk_graph, "chunks") or not chunk_graph.chunks:
                raise ValueError(
                    "Document chunk_graph is empty. "
                    "Ensure SPC ingestion pipeline completed successfully and extracted chunks."
                )

            try:
                from farfan_pipeline.utils.spc_adapter import SPCAdapter

                adapter = SPCAdapter()
                preprocessed = adapter.to_preprocessed_document(
                    document, document_id=document_id
                )

                validation_results = []

                if not preprocessed.raw_text or not preprocessed.raw_text.strip():
                    raise ValueError(
                        "SPC ingestion produced empty document. "
                        "Check that the source document contains extractable text."
                    )
                text_length = len(preprocessed.raw_text)
                validation_results.append(f"raw_text: {text_length} chars")

                sentence_count = (
                    len(preprocessed.sentences) if preprocessed.sentences else 0
                )
                if sentence_count == 0:
                    logger.warning(
                        "SPC ingestion produced zero sentences - document may be malformed"
                    )
                validation_results.append(f"sentences: {sentence_count}")

                chunk_count = preprocessed.metadata.get("chunk_count", 0)
                validation_results.append(f"chunks: {chunk_count}")

                logger.info(
                    f"SPC ingestion validation passed: {', '.join(validation_results)}"
                )

                return preprocessed
            except ImportError as e:
                raise ImportError(
                    "SPC ingestion requires spc_adapter module. "
                    "Ensure farfan_core.utils.spc_adapter is available."
                ) from e
            except ValueError:
                raise
            except Exception as e:
                raise TypeError(
                    f"Failed to adapt SPC document: {e}. "
                    "Ensure document is a valid CanonPolicyPackage instance from SPC pipeline."
                ) from e

        raise TypeError(
            "Unsupported preprocessed document payload. "
            f"Expected PreprocessedDocument or CanonPolicyPackage with chunk_graph, got {type(document)!r}. "
            "Documents must be processed through the SPC ingestion pipeline first."
        )
