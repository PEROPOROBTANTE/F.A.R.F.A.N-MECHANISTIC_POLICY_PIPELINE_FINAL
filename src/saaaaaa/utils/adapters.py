"""
ADAPTER LAYER - Centralized Shims for API Evolution
====================================================

One adapter function per boundary. Never "fix" at random call sites.
Adapters maintained for one release cycle when schemas change.

Purpose: Bridge old dict-based APIs to new typed contracts cleanly.
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Any

from contracts import (
    AnalysisInputV1,
    AnalysisOutputV1,
    DocumentMetadataV1,
    TextDocument,
    validate_mapping_keys,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

# ============================================================================
# DEPRECATION HELPERS
# ============================================================================

def _deprecation_warning(
    old_name: str,
    new_name: str,
    removal_version: str,
    additional_msg: str = "",
) -> None:
    """Emit a loud deprecation warning with removal date."""
    msg = (
        f"Parameter '{old_name}' is deprecated and will be removed in {removal_version}. "
        f"Use '{new_name}' instead."
    )
    if additional_msg:
        msg += f" {additional_msg}"

    warnings.warn(msg, DeprecationWarning, stacklevel=3)

# ============================================================================
# DOCUMENT ADAPTERS
# ============================================================================

def adapt_document_metadata_to_v1(
    raw_dict: Mapping[str, Any],
    *,
    strict: bool = False,
) -> DocumentMetadataV1:
    """
    Adapt raw dict to DocumentMetadataV1 contract.

    Args:
        raw_dict: Raw dictionary from legacy code
        strict: If True, raise on missing keys; if False, provide defaults

    Returns:
        Validated DocumentMetadataV1

    Raises:
        KeyError: If strict=True and required keys missing
        TypeError: If values have wrong types
    """
    required_keys = ["file_path", "file_name", "num_pages", "file_size_bytes", "file_hash"]

    if strict:
        validate_mapping_keys(
            raw_dict,
            required_keys,
            producer="legacy_code",
            consumer="adapt_document_metadata_to_v1",
        )

    # Extract with defaults for non-strict mode
    metadata: DocumentMetadataV1 = {
        "file_path": str(raw_dict.get("file_path", "")),
        "file_name": str(raw_dict.get("file_name", "")),
        "num_pages": int(raw_dict.get("num_pages", 0)),
        "file_size_bytes": int(raw_dict.get("file_size_bytes", 0)),
        "file_hash": str(raw_dict.get("file_hash", "")),
    }

    return metadata

def adapt_text_to_document(
    text: str | TextDocument,
    *,
    document_id: str,
    metadata: Mapping[str, Any] | None = None,
) -> TextDocument:
    """
    Adapt plain string or TextDocument to TextDocument contract.

    Handles case where legacy code passes plain str instead of TextDocument.

    Args:
        text: Plain string or TextDocument
        document_id: Document identifier
        metadata: Optional metadata dict

    Returns:
        TextDocument value object
    """
    if isinstance(text, TextDocument):
        return text

    if not isinstance(text, str):
        raise TypeError(
            f"ERR_CONTRACT_MISMATCH: text must be str or TextDocument, "
            f"got {type(text).__name__}"
        )

    return TextDocument(
        text=text,
        document_id=document_id,
        metadata=metadata or {},
    )

# ============================================================================
# ANALYSIS ADAPTERS
# ============================================================================

def adapt_analysis_input_kwargs(
    kwargs: dict[str, Any],
) -> AnalysisInputV1:
    """
    Adapt **kwargs from legacy calls to AnalysisInputV1 contract.

    Handles parameter name aliases:
    - 'raw_text' -> 'text'
    - 'doc_id' -> 'document_id'

    Args:
        kwargs: Raw kwargs dict from legacy code

    Returns:
        Validated AnalysisInputV1

    Raises:
        KeyError: If required keys missing after alias resolution
    """
    # Handle parameter aliases with deprecation warnings
    if "raw_text" in kwargs and "text" not in kwargs:
        _deprecation_warning(
            "raw_text",
            "text",
            "v2.0.0",
            "The API now uses 'text' consistently across all functions.",
        )
        kwargs["text"] = kwargs["raw_text"]

    if "doc_id" in kwargs and "document_id" not in kwargs:
        _deprecation_warning("doc_id", "document_id", "v2.0.0")
        kwargs["document_id"] = kwargs["doc_id"]

    # Validate required fields
    required = ["text", "document_id"]
    validate_mapping_keys(
        kwargs,
        required,
        producer="legacy_call_site",
        consumer="adapt_analysis_input_kwargs",
    )

    # Build typed result
    result: AnalysisInputV1 = {
        "text": str(kwargs["text"]),
        "document_id": str(kwargs["document_id"]),
    }

    return result

def adapt_analysis_output_to_dict(
    output: AnalysisOutputV1,
) -> dict[str, Any]:
    """
    Adapt AnalysisOutputV1 to plain dict for legacy consumers.

    Temporary adapter during migration period.
    Will be removed in v2.0.0.

    Args:
        output: Typed analysis output

    Returns:
        Plain dict for legacy code
    """
    return dict(output)

# ============================================================================
# PARAMETER NAME MIGRATION ADAPTERS
# ============================================================================

def handle_renamed_param(
    kwargs: dict[str, Any],
    old_name: str,
    new_name: str,
    *,
    removal_version: str = "v2.0.0",
) -> None:
    """
    Handle renamed parameter with deprecation warning.

    If old_name present but not new_name, copy value and emit warning.
    Modifies kwargs dict in place.

    Args:
        kwargs: Kwargs dict to modify
        old_name: Old parameter name
        new_name: New parameter name
        removal_version: Version where old name will be removed
    """
    if old_name in kwargs and new_name not in kwargs:
        _deprecation_warning(old_name, new_name, removal_version)
        kwargs[new_name] = kwargs[old_name]

def migrate_pdf_path_param(kwargs: dict[str, Any]) -> None:
    """
    Migrate 'pdf_path' to keyword-only 'pdf_path' with Path type.

    Common error: unexpected keyword argument 'pdf_path'
    Fix: Ensure it's passed as keyword-only and converted to Path.
    """
    if "pdf_path" in kwargs:
        value = kwargs["pdf_path"]
        if isinstance(value, str):
            kwargs["pdf_path"] = Path(value)
        elif not isinstance(value, Path):
            raise TypeError(
                f"ERR_CONTRACT_MISMATCH: pdf_path must be str or Path, "
                f"got {type(value).__name__}"
            )

def migrate_tables_param(kwargs: dict[str, Any]) -> None:
    """
    Migrate 'tables' parameter to Mapping type.

    Common error: producer sent list, consumer expected Mapping
    Fix: Detect and convert to proper structure.
    """
    if "tables" in kwargs:
        tables = kwargs["tables"]

        # If it's a list, convert to mapping
        if isinstance(tables, list):
            warnings.warn(
                "ERR_CONTRACT_MISMATCH: 'tables' should be Mapping[str, Any], "
                "got list. Converting to dict. "
                "Producer should be updated to send Mapping.",
                DeprecationWarning,
                stacklevel=2,
            )
            # Convert list of tables to mapping
            kwargs["tables"] = {
                f"table_{i}": table
                for i, table in enumerate(tables)
            }

# ============================================================================
# METADATA MIGRATION ADAPTERS
# ============================================================================

def handle_metadata_to_tables_migration(kwargs: dict[str, Any]) -> None:
    """
    Handle parameter rename: metadata -> tables.

    Common migration pattern when refactoring table extraction.
    Maintains backwards compatibility for one release cycle.
    """
    handle_renamed_param(
        kwargs,
        "metadata",
        "tables",
        removal_version="v2.0.0",
    )

# ============================================================================
# TEXT ATTRIBUTE ADAPTERS
# ============================================================================

def ensure_text_attribute(obj: Any) -> str:
    """
    Safely extract text from object that might be str or have .text attribute.

    Common error: 'str' object has no attribute 'text'
    Fix: Handle both plain strings and objects with .text attribute.

    Args:
        obj: Object that is either str or has .text attribute

    Returns:
        Extracted text string

    Raises:
        TypeError: If obj is neither str nor has .text attribute
    """
    if isinstance(obj, str):
        return obj

    if hasattr(obj, "text") and isinstance(obj.text, str):
        return obj.text

    raise TypeError(
        f"ERR_CONTRACT_MISMATCH: expected str or object with .text attribute, "
        f"got {type(obj).__name__}"
    )

# ============================================================================
# COLLECTION ADAPTERS
# ============================================================================

def adapt_to_sequence(
    value: Any,
    *,
    parameter: str,
    allow_strings: bool = False,
) -> Sequence[Any]:
    """
    Adapt value to Sequence, handling common iteration errors.

    Common errors:
    - 'bool' object is not iterable
    - Iterating string as tokens when expecting collection

    Args:
        value: Value to adapt
        parameter: Parameter name for error messages
        allow_strings: If False, reject strings even though they're iterable

    Returns:
        Sequence-like object

    Raises:
        TypeError: If value is not iterable or is string when disallowed
    """
    # Reject booleans (common source of "not iterable" errors)
    if isinstance(value, bool):
        raise TypeError(
            f"ERR_CONTRACT_MISMATCH: param='{parameter}', "
            f"expected=Sequence, got=bool (not iterable)"
        )

    # Reject strings if not allowed
    if not allow_strings and isinstance(value, (str, bytes)):
        raise TypeError(
            f"ERR_CONTRACT_MISMATCH: param='{parameter}', "
            f"expected=Sequence (not str), got={type(value).__name__}"
        )

    # Check if iterable
    try:
        iter(value)
        return value  # type: ignore[return-value]
    except TypeError as e:
        raise TypeError(
            f"ERR_CONTRACT_MISMATCH: param='{parameter}', "
            f"expected=Sequence, got={type(value).__name__} (not iterable)"
        ) from e

def adapt_for_set_membership(value: Any, *, parameter: str) -> Any:
    """
    Adapt value for use in sets or as dict keys (must be hashable).

    Common error: unhashable type: 'dict'
    Fix: Convert unhashable types to hashable equivalents.

    Args:
        value: Value to adapt
        parameter: Parameter name for error messages

    Returns:
        Hashable version of value

    Raises:
        TypeError: If value cannot be made hashable
    """
    # Already hashable
    try:
        hash(value)
        return value
    except TypeError:
        pass

    # Convert dict to frozenset of items
    if isinstance(value, dict):
        try:
            return frozenset(value.items())
        except TypeError:
            # Nested dicts - convert to tuple of tuples
            items = []
            for k, v in value.items():
                hashable_k = adapt_for_set_membership(k, parameter=f"{parameter}.key")
                hashable_v = adapt_for_set_membership(v, parameter=f"{parameter}.value")
                items.append((hashable_k, hashable_v))
            return tuple(sorted(items))

    # Convert list to tuple
    if isinstance(value, list):
        return tuple(
            adapt_for_set_membership(item, parameter=f"{parameter}.item")
            for item in value
        )

    # Convert set to frozenset
    if isinstance(value, set):
        return frozenset(value)

    raise TypeError(
        f"ERR_CONTRACT_MISMATCH: param='{parameter}', "
        f"cannot make {type(value).__name__} hashable"
    )

# ============================================================================
# VALIDATION SUMMARY
# ============================================================================

def validate_adapted_kwargs(
    kwargs: dict[str, Any],
    *,
    producer: str,
    consumer: str,
    required_keys: Sequence[str],
) -> None:
    """
    Final validation after all adaptations applied.

    Ensures all required parameters present and types correct.

    Args:
        kwargs: Adapted kwargs dict
        producer: Name of producing module/function
        consumer: Name of consuming module/function
        required_keys: List of required parameter names

    Raises:
        KeyError: If required keys missing
    """
    validate_mapping_keys(
        kwargs,
        required_keys,
        producer=producer,
        consumer=consumer,
    )
