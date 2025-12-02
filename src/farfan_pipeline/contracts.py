"""Contracts module re-exports from utils.contracts package.

This module provides backward compatibility for code that imports
contracts from farfan_core.contracts instead of farfan_core.utils.contracts.
"""

from farfan_pipeline.utils.contracts import (
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

__all__ = [
    "MISSING",
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
