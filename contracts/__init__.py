"""
Contracts package - defines API contracts and interfaces.

This package provides backward compatibility by re-exporting
from saaaaaa.utils.contracts.

Version 2.0: Enhanced with Pydantic-based validation, cryptographic
verification, and structured logging.
"""
from __future__ import annotations

from pathlib import Path

# Add src to path for development environments
_SRC_PATH = Path(__file__).resolve().parent.parent / "src"
if _SRC_PATH.exists():  # pragma: no cover - executed at import time
    src_str = str(_SRC_PATH)
# Direct imports from the source modules
from saaaaaa.utils.contracts import (  # noqa: F401, E402
    # V2 Enhanced Contracts (Pydantic-based)
    AnalysisInputV2,
    AnalysisOutputV2,
    BaseContract,
    DocumentMetadataV2,
    ExecutionContextV2,
    ProcessedTextV2,
    ContractValidationError,
    DataIntegrityError,
    FlowCompatibilityError,
    SystemConfigError,
    StructuredLogger,
    compute_content_digest,
    utc_now_iso,
    # V1 Contracts (TypedDict-based) - Backward Compatibility
    MISSING,
    AnalysisInputV1,
    AnalysisInputV1Optional,
    AnalysisOutputV1,
    AnalysisOutputV1Optional,
    AnalyzerProtocol,
    ContractMismatchError,
    DocumentLoaderProtocol,
    DocumentMetadataV1,
    DocumentMetadataV1Optional,
    ExecutionContextV1,
    ExecutionContextV1Optional,
    ProcessedTextV1,
    ProcessedTextV1Optional,
    SentenceCollection,
    TextDocument,
    TextProcessorProtocol,
    ensure_hashable,
    ensure_iterable_not_string,
    validate_contract,
    validate_mapping_keys,
)
from saaaaaa.utils.seed_factory import SeedFactory  # noqa: F401, E402

__all__ = [
    # V2 Enhanced Contracts
    "AnalysisInputV2",
    "AnalysisOutputV2",
    "BaseContract",
    "DocumentMetadataV2",
    "ExecutionContextV2",
    "ProcessedTextV2",
    "ContractValidationError",
    "DataIntegrityError",
    "FlowCompatibilityError",
    "SystemConfigError",
    "StructuredLogger",
    "compute_content_digest",
    "utc_now_iso",
    # V1 Contracts
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
    "SeedFactory",
    "SentenceCollection",
    "TextDocument",
    "TextProcessorProtocol",
    "ensure_hashable",
    "ensure_iterable_not_string",
    "validate_contract",
    "validate_mapping_keys",
]
