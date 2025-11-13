"""Versioned data transfer objects for preprocessed documents."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping, MutableMapping

__all__ = [
    "StructuredSection",
    "StructuredTextV1",
    "SentenceMetadata",
    "TableAnnotation",
    "DocumentIndexesV1",
    "PreprocessedDocumentV1",
    "PreprocessedDocumentV2",
    "PreprocessedDocument",
    "upgrade_preprocessed_document",
    "downgrade_preprocessed_document",
]

_EMPTY_MAPPING: Mapping[str, Any] = MappingProxyType({})

def _frozen_mapping(data: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not data:
        return _EMPTY_MAPPING
    if isinstance(data, MappingProxyType):
        return data
    return MappingProxyType(dict(data))

@dataclass(frozen=True, slots=True)
class StructuredSection:
    """Section extracted from a document with structural metadata."""

    title: str
    start_char: int
    content: str

@dataclass(frozen=True, slots=True)
class StructuredTextV1:
    """Structured representation of a document's text content."""

    full_text: str
    sections: tuple[StructuredSection, ...] = field(default_factory=tuple)
    page_boundaries: tuple[tuple[int, int], ...] = field(default_factory=tuple)

@dataclass(frozen=True, slots=True)
class SentenceMetadata:
    """Metadata associated with a segmented sentence."""

    index: int
    page_number: int | None = None
    start_char: int | None = None
    end_char: int | None = None
    extra: Mapping[str, Any] = field(default=_EMPTY_MAPPING)

@dataclass(frozen=True, slots=True)
class TableAnnotation:
    """Minimal metadata for a table extracted from a document."""

    table_id: str
    label: str
    attributes: Mapping[str, Any] = field(default=_EMPTY_MAPPING)

@dataclass(frozen=True, slots=True)
class DocumentIndexesV1:
    """Indices built over a document for search and retrieval."""

    term_index: Mapping[str, tuple[int, ...]] = field(default=_EMPTY_MAPPING)
    numeric_index: Mapping[str, tuple[int, ...]] = field(default=_EMPTY_MAPPING)
    temporal_index: Mapping[str, tuple[int, ...]] = field(default=_EMPTY_MAPPING)
    entity_index: Mapping[str, tuple[int, ...]] = field(default=_EMPTY_MAPPING)

@dataclass(frozen=True, slots=True)
class PreprocessedDocumentV1:
    """Initial public DTO for preprocessed documents."""

    document_id: str
    full_text: str
    sentences: tuple[str, ...]
    language: str
    structured_text: StructuredTextV1
    sentence_metadata: tuple[SentenceMetadata, ...]
    tables: tuple[TableAnnotation, ...]
    indexes: DocumentIndexesV1
    metadata: Mapping[str, Any]

    @property
    def raw_text(self) -> str:
        """Backward compatible accessor for legacy consumers."""

        return self.full_text

@dataclass(frozen=True, slots=True)
class PreprocessedDocumentV2:
    """Current DTO for preprocessed documents with explicit versioning."""

    document_id: str
    full_text: str
    sentences: tuple[str, ...]
    language: str
    structured_text: StructuredTextV1
    sentence_metadata: tuple[SentenceMetadata, ...]
    tables: tuple[TableAnnotation, ...]
    indexes: DocumentIndexesV1
    metadata: Mapping[str, Any]
    ingested_at: datetime

    @property
    def raw_text(self) -> str:
        """Backward compatible accessor for legacy consumers."""

        return self.full_text

PreprocessedDocument = PreprocessedDocumentV2

def upgrade_preprocessed_document(doc: PreprocessedDocumentV1 | PreprocessedDocumentV2) -> PreprocessedDocumentV2:
    """Promote a legacy preprocessed document to the latest version."""

    if isinstance(doc, PreprocessedDocumentV2):
        return doc
    metadata = _frozen_mapping(doc.metadata)
    ingested_at_raw: str | None = None
    if "ingested_at" in metadata:
        ingested_at_raw = str(metadata["ingested_at"])
    ingested_at = datetime.fromisoformat(ingested_at_raw) if ingested_at_raw else datetime.utcnow()
    return PreprocessedDocumentV2(
        document_id=doc.document_id,
        full_text=doc.full_text,
        sentences=tuple(doc.sentences),
        language=doc.language,
        structured_text=doc.structured_text,
        sentence_metadata=tuple(doc.sentence_metadata),
        tables=tuple(doc.tables),
        indexes=doc.indexes,
        metadata=metadata,
        ingested_at=ingested_at,
    )

def downgrade_preprocessed_document(doc: PreprocessedDocumentV2) -> PreprocessedDocumentV1:
    """Convert a V2 document to the legacy V1 payload."""

    legacy_metadata: MutableMapping[str, Any] = dict(doc.metadata)
    legacy_metadata.setdefault("ingested_at", doc.ingested_at.isoformat())
    return PreprocessedDocumentV1(
        document_id=doc.document_id,
        full_text=doc.full_text,
        sentences=tuple(doc.sentences),
        language=doc.language,
        structured_text=doc.structured_text,
        sentence_metadata=tuple(doc.sentence_metadata),
        tables=tuple(doc.tables),
        indexes=doc.indexes,
        metadata=MappingProxyType(dict(legacy_metadata)),
    )
