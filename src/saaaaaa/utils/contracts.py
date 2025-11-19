"""
CONTRACT DEFINITIONS - Frozen Data Shapes
==========================================

TypedDict and Protocol definitions for API contracts across modules.
All data shapes must be versioned and adapters maintained for one release cycle.

Purpose: Replace ad-hoc dicts with typed structures to prevent:
- unexpected keyword argument errors
- missing required positional arguments
- 'str' object has no attribute 'text' errors
- 'bool' object is not iterable
- unhashable type: 'dict' in sets

Version 2.0 Enhancement:
- Pydantic-based contracts with strict validation (enhanced_contracts.py)
- Backward compatibility with V1 TypedDict contracts maintained
- Domain-specific exceptions and structured logging
- Cryptographic content verification and deterministic execution
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    Protocol,
    TypedDict,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence
    from pathlib import Path

# ============================================================================
# V2 ENHANCED CONTRACTS - Pydantic-based with strict validation
# ============================================================================
# Import V2 contracts from enhanced_contracts module
# Use these for new code; V1 contracts maintained for backward compatibility
from .enhanced_contracts import (
    # Pydantic Models
    AnalysisInputV2,
    AnalysisOutputV2,
    BaseContract,
    # Exceptions
    ContractValidationError,
    DataIntegrityError,
    DocumentMetadataV2,
    ExecutionContextV2,
    FlowCompatibilityError,
    ProcessedTextV2,
    # Utilities
    StructuredLogger,
    SystemConfigError,
    compute_content_digest,
    utc_now_iso,
)

# ============================================================================
# DOCUMENT CONTRACTS - V1
# ============================================================================

class DocumentMetadataV1(TypedDict, total=True):
    """Document metadata shape - all fields required."""
    file_path: str
    file_name: str
    num_pages: int
    file_size_bytes: int
    file_hash: str

class DocumentMetadataV1Optional(TypedDict, total=False):
    """Optional document metadata fields."""
    pdf_metadata: dict[str, Any]
    author: str
    title: str
    creation_date: str

class ProcessedTextV1(TypedDict, total=True):
    """Shape for processed text output."""
    raw_text: str
    normalized_text: str
    language: str
    encoding: str

class ProcessedTextV1Optional(TypedDict, total=False):
    """Optional processed text fields."""
    sentences: list[str]
    sections: list[dict[str, Any]]
    tables: Mapping[str, Any]

# ============================================================================
# ANALYSIS CONTRACTS - V1
# ============================================================================

class AnalysisInputV1(TypedDict, total=True):
    """Required fields for analysis input - keyword-only."""
    text: str
    document_id: str

class AnalysisInputV1Optional(TypedDict, total=False):
    """Optional fields for analysis input."""
    metadata: Mapping[str, Any]
    context: Mapping[str, Any]
    sentences: Sequence[str]

class AnalysisOutputV1(TypedDict, total=True):
    """Shape for analysis output."""
    dimension: str
    category: str
    confidence: float
    matches: Sequence[str]

class AnalysisOutputV1Optional(TypedDict, total=False):
    """Optional analysis output fields."""
    positions: Sequence[int]
    evidence: Sequence[str]
    warnings: Sequence[str]

# ============================================================================
# EXECUTION CONTRACTS - V1
# ============================================================================

class ExecutionContextV1(TypedDict, total=True):
    """Execution context for method invocation."""
    class_name: str
    method_name: str
    document_id: str

class ExecutionContextV1Optional(TypedDict, total=False):
    """Optional execution context fields."""
    raw_text: str
    text: str
    metadata: Mapping[str, Any]
    tables: Mapping[str, Any]
    sentences: Sequence[str]

# ============================================================================
# ERROR REPORTING CONTRACTS
# ============================================================================

class ContractMismatchError(TypedDict, total=True):
    """Standard error shape for contract mismatches."""
    error_code: Literal["ERR_CONTRACT_MISMATCH"]
    stage: str
    function: str
    parameter: str
    expected_type: str
    got_type: str
    producer: str
    consumer: str

# ============================================================================
# PROTOCOLS FOR PLUGGABLE BEHAVIOR
# ============================================================================

class TextProcessorProtocol(Protocol):
    """Protocol for text processing components."""

    def normalize_unicode(self, text: str) -> str:
        """Normalize unicode characters in text."""
        ...

    def segment_into_sentences(self, text: str) -> Sequence[str]:
        """Segment text into sentences."""
        ...

class DocumentLoaderProtocol(Protocol):
    """Protocol for document loading components."""

    def load_pdf(self, *, pdf_path: Path) -> DocumentMetadataV1:
        """Load PDF and return metadata - keyword-only params."""
        ...

    def validate_pdf(self, *, pdf_path: Path) -> bool:
        """Validate PDF file - keyword-only params."""
        ...

class AnalyzerProtocol(Protocol):
    """Protocol for analysis components."""

    def analyze(
        self,
        *,
        text: str,
        document_id: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> AnalysisOutputV1:
        """Analyze text and return structured output - keyword-only params."""
        ...

# ============================================================================
# VALUE OBJECTS (prevent .text on strings)
# ============================================================================

@dataclass(frozen=True, slots=True)
class TextDocument:
    """Wrapper to prevent passing plain str where structured text is required."""
    text: str
    document_id: str
    metadata: Mapping[str, Any]

    def __post_init__(self) -> None:
        """Validate that text is non-empty."""
        if not isinstance(self.text, str):
            raise TypeError(
                f"ERR_CONTRACT_MISMATCH: text must be str, got {type(self.text).__name__}"
            )
        if not self.text:
            raise ValueError("ERR_CONTRACT_MISMATCH: text cannot be empty")

@dataclass(frozen=True, slots=True)
class SentenceCollection:
    """Type-safe collection of sentences (prevents iteration bugs)."""
    sentences: tuple[str, ...]  # Immutable and hashable

    def __post_init__(self) -> None:
        """Validate sentences are strings."""
        if not all(isinstance(s, str) for s in self.sentences):
            raise TypeError(
                "ERR_CONTRACT_MISMATCH: All sentences must be strings"
            )

    def __iter__(self) -> Iterable[str]:
        """Make iterable."""
        return iter(self.sentences)

    def __len__(self) -> int:
        """Return count."""
        return len(self.sentences)

# ============================================================================
# SENTINEL VALUES (avoid None ambiguity)
# ============================================================================

class _MissingSentinel:
    """Sentinel type for missing optional parameters."""

    def __repr__(self) -> str:
        return "<MISSING>"

MISSING: _MissingSentinel = _MissingSentinel()

# ============================================================================
# RUNTIME VALIDATION HELPERS
# ============================================================================

def validate_contract(
    value: Any,
    expected_type: type,
    *,
    parameter: str,
    producer: str,
    consumer: str,
) -> None:
    """
    Validate value matches expected contract at runtime.

    Raises TypeError with structured error message on mismatch.
    """
    if not isinstance(value, expected_type):
        error_msg = (
            f"ERR_CONTRACT_MISMATCH["
            f"param='{parameter}', "
            f"expected={expected_type.__name__}, "
            f"got={type(value).__name__}, "
            f"producer={producer}, "
            f"consumer={consumer}"
            f"]"
        )
        raise TypeError(error_msg)

def validate_mapping_keys(
    mapping: Mapping[str, Any],
    required_keys: Sequence[str],
    *,
    producer: str,
    consumer: str,
) -> None:
    """
    Validate mapping contains required keys.

    Raises KeyError with structured message on missing keys.
    """
    missing = [key for key in required_keys if key not in mapping]
    if missing:
        error_msg = (
            f"ERR_CONTRACT_MISMATCH["
            f"missing_keys={missing}, "
            f"producer={producer}, "
            f"consumer={consumer}"
            f"]"
        )
        raise KeyError(error_msg)

def ensure_iterable_not_string(
    value: Any,
    *,
    parameter: str,
    producer: str,
    consumer: str,
) -> None:
    """
    Validate value is iterable but NOT a string or bytes.

    Prevents "'bool' object is not iterable" and "iterate string as tokens" bugs.
    """
    if isinstance(value, (str, bytes)):
        raise TypeError(
            f"ERR_CONTRACT_MISMATCH["
            f"param='{parameter}', "
            f"expected=Iterable (not str/bytes), "
            f"got={type(value).__name__}, "
            f"producer={producer}, "
            f"consumer={consumer}"
            f"]"
        )

    try:
        iter(value)
    except TypeError as e:
        raise TypeError(
            f"ERR_CONTRACT_MISMATCH["
            f"param='{parameter}', "
            f"expected=Iterable, "
            f"got={type(value).__name__}, "
            f"producer={producer}, "
            f"consumer={consumer}"
            f"]"
        ) from e

def ensure_hashable(
    value: Any,
    *,
    parameter: str,
    producer: str,
    consumer: str,
) -> None:
    """
    Validate value is hashable (can be added to set or used as dict key).

    Prevents "unhashable type: 'dict'" errors.
    """
    try:
        hash(value)
    except TypeError as e:
        raise TypeError(
            f"ERR_CONTRACT_MISMATCH["
            f"param='{parameter}', "
            f"expected=Hashable, "
            f"got={type(value).__name__} (unhashable), "
            f"producer={producer}, "
            f"consumer={consumer}"
            f"]"
        ) from e


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    # V2 Enhanced Contracts (Pydantic-based) - RECOMMENDED FOR NEW CODE
    "AnalysisInputV2",
    "AnalysisOutputV2",
    "BaseContract",
    "DocumentMetadataV2",
    "ExecutionContextV2",
    "ProcessedTextV2",
    # V2 Exceptions
    "ContractValidationError",
    "DataIntegrityError",
    "FlowCompatibilityError",
    "SystemConfigError",
    # V2 Utilities
    "StructuredLogger",
    "compute_content_digest",
    "utc_now_iso",
    # V1 Contracts (TypedDict-based) - BACKWARD COMPATIBILITY
    "AnalysisInputV1",
    "AnalysisInputV1Optional",
    "AnalysisOutputV1",
    "AnalysisOutputV1Optional",
    "AnalyzerProtocol",
    "ContractMismatchError",
    "DocumentLoaderProtocol",
    "DocumentMetadataV1",
    "DocumentMetadataV1Optional",
    "ExecutionContextV1",
    "ExecutionContextV1Optional",
    "MISSING",
    "ProcessedTextV1",
    "ProcessedTextV1Optional",
    "SentenceCollection",
    "TextDocument",
    "TextProcessorProtocol",
    "ensure_hashable",
    "ensure_iterable_not_string",
    "validate_contract",
    "validate_mapping_keys",
]
