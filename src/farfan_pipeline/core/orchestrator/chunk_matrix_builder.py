"""Chunk matrix construction and validation for policy analysis pipeline.

This module provides deterministic construction of the 60-chunk PA×DIM matrix
with comprehensive validation, duplicate detection, and audit logging.

Validation Hierarchy (Leaf Node Pattern):
==========================================
Each validation function is atomic with a single failure mode. This design ensures:
- Precise error messages pinpointing the exact validation failure
- Easy debugging by mapping error message to specific validation function
- No cascading failures from complex validation logic

Validation Stages:
1. Structure Validation (_validate_document_structure)
   - Document has chunks attribute
   - Chunks is a non-empty list
   - Processing mode is 'chunked'

2. Chunk Type Validation (_validate_chunk_structure)
   - Each chunk is a ChunkData instance

3. Required Fields Validation (_validate_chunk_required_fields)
   - text, policy_area_id, dimension_id are present and non-null

4. Field Type Validation (_validate_chunk_field_types)
   - Fields have correct types (strings)
   - Text content is non-empty

5. Format Validation (_validate_chunk_id_format)
   - chunk_id matches PA{01-10}-DIM{01-06} pattern
   - PA value is 01-10
   - DIM value is 01-06

6. Consistency Validation (_validate_chunk_id_consistency)
   - chunk_id matches policy_area_id-dimension_id

7. Uniqueness Validation (_check_duplicate_key, _check_duplicate_chunk_id)
   - No duplicate PA×DIM combinations
   - No duplicate chunk_id values

8. Completeness Validation (_validate_completeness)
   - All 60 PA×DIM combinations present
   - No missing policy areas or dimensions

9. Cardinality Validation (_validate_chunk_count)
   - Exactly 60 chunks in matrix

Phase 1 Contract Guarantees:
=============================
- Exactly 60 chunks (10 PA × 6 DIM)
- All chunks have valid chunk_id (PA{01-10}-DIM{01-06})
- All chunks have non-empty text content
- No duplicate PA×DIM combinations
- Complete coverage of all PA×DIM combinations
- Immutable ChunkData instances (frozen dataclass)
- Efficient O(1) lookup by (PA, DIM) key

Error Message Specificity:
===========================
All error messages follow this pattern:
- Clear identification of what failed
- Location in document (chunk index, PA×DIM combination)
- Expected vs actual values
- Guidance on which Phase 1 subphase to check
- No generic "validation failed" messages

Example Usage:
==============
    from farfan_pipeline.core.orchestrator.chunk_matrix_builder import (
        build_chunk_matrix,
        validate_chunk_matrix_contract,
        generate_validation_summary,
    )
    
    # Build and validate in one call (raises on error)
    matrix, keys = build_chunk_matrix(preprocessed_doc)
    
    # Or validate separately for reporting (no exception)
    report = validate_chunk_matrix_contract(matrix, keys)
    if not report['passed']:
        print(generate_validation_summary(report))
"""

import logging
import re
from functools import lru_cache
from collections.abc import Iterable
from typing import Dict, List, Set, Tuple

from farfan_pipeline.core.types import ChunkData, PreprocessedDocument
from farfan_pipeline.core.orchestrator.questionnaire import load_questionnaire

logger = logging.getLogger(__name__)

CHUNK_ID_PATTERN = re.compile(r"^PA(0[1-9]|10)-DIM(0[1-6])$")
MAX_MISSING_KEYS_TO_DISPLAY = 10


class ChunkMatrixValidationError(ValueError):
    """Raised when chunk matrix validation fails in Phase 1.
    
    This exception indicates that Phase 1 output does not meet the required
    contract for chunk matrix construction. All errors include specific
    diagnostic information for debugging Phase 1 issues.
    """
    
    def __init__(
        self, 
        message: str, 
        validation_type: str = "unknown", 
        details: Dict = None,
        failed_chunk_indices: List[int] = None,
        phase1_subphase: str = None,
    ):
        """Initialize validation error with diagnostic information.
        
        Args:
            message: Human-readable error message
            validation_type: Category of validation failure
                (e.g., 'structure', 'format', 'completeness')
            details: Additional diagnostic information
            failed_chunk_indices: Indices of chunks that failed validation
            phase1_subphase: Phase 1 subphase where error likely originated
                (SP0-SP15)
        """
        super().__init__(message)
        self.validation_type = validation_type
        self.details = details or {}
        self.failed_chunk_indices = failed_chunk_indices or []
        self.phase1_subphase = phase1_subphase
    
    def get_diagnostic_report(self) -> str:
        """Generate a comprehensive diagnostic report for debugging.
        
        Returns:
            Multi-line string with full diagnostic information
        """
        lines = [
            "=" * 80,
            "PHASE 1 CHUNK MATRIX VALIDATION ERROR",
            "=" * 80,
            f"Validation Type: {self.validation_type}",
            f"Error Message: {self}",
        ]
        
        if self.phase1_subphase:
            lines.append(f"Likely Origin: Phase 1 {self.phase1_subphase}")
        
        if self.failed_chunk_indices:
            lines.append(f"Failed Chunk Indices: {self.failed_chunk_indices[:20]}")
            if len(self.failed_chunk_indices) > 20:
                lines.append(f"  ... and {len(self.failed_chunk_indices) - 20} more")
        
        if self.details:
            lines.append("\nDiagnostic Details:")
            for key, value in self.details.items():
                lines.append(f"  {key}: {value}")
        
        lines.append("=" * 80)
        return "\n".join(lines)


@lru_cache
def _expected_axes_from_monolith() -> tuple[list[str], list[str]]:
    """Load unique policy areas and dimensions from questionnaire monolith."""
    questionnaire = load_questionnaire()
    micro_questions = questionnaire.get_micro_questions()

    policy_areas = sorted(
        {
            q.get("policy_area_id")
            for q in micro_questions
            if q.get("policy_area_id")
        }
    )
    dimensions = sorted(
        {
            q.get("dimension_id")
            for q in micro_questions
            if q.get("dimension_id")
        }
    )

    if not policy_areas or not dimensions:
        raise ValueError(
            "Questionnaire monolith is missing policy_area_id or dimension_id values"
        )

    return policy_areas, dimensions


POLICY_AREAS, DIMENSIONS = _expected_axes_from_monolith()
EXPECTED_CHUNK_COUNT = len(POLICY_AREAS) * len(DIMENSIONS)


def validate_chunk_matrix_contract(
    matrix: Dict[Tuple[str, str], ChunkData],
    sorted_keys: List[Tuple[str, str]],
) -> Dict[str, any]:
    """Validate that chunk matrix satisfies all Phase 1 output contracts.
    
    Performs comprehensive validation to ensure Phase 1 produced a valid
    chunk matrix for use in downstream phases (especially Phase 3 routing).
    
    This function can be called after build_chunk_matrix() to get a detailed
    validation report without raising exceptions.
    
    Args:
        matrix: Chunk matrix to validate
        sorted_keys: Sorted list of matrix keys
        
    Returns:
        Validation report dict with:
            - passed (bool): True if all validations passed
            - errors (list): List of error messages
            - warnings (list): List of warning messages
            - metrics (dict): Quantitative metrics about the matrix
            - recommendations (list): Suggestions for fixing issues
    """
    report = {
        "passed": True,
        "errors": [],
        "warnings": [],
        "recommendations": [],
        "metrics": {
            "chunk_count": len(matrix),
            "expected_count": EXPECTED_CHUNK_COUNT,
            "unique_pa_count": len(set(k[0] for k in sorted_keys)),
            "unique_dim_count": len(set(k[1] for k in sorted_keys)),
            "empty_chunks": 0,
            "chunks_with_provenance": 0,
            "avg_text_length": 0,
        },
    }
    
    text_lengths = []
    
    if len(matrix) != EXPECTED_CHUNK_COUNT:
        report["passed"] = False
        deficit = EXPECTED_CHUNK_COUNT - len(matrix)
        if len(matrix) < EXPECTED_CHUNK_COUNT:
            report["errors"].append(
                f"Chunk count deficit: expected {EXPECTED_CHUNK_COUNT}, "
                f"got {len(matrix)} (missing {deficit})"
            )
            report["recommendations"].append(
                "Check Phase 1 segmentation (SP4) to ensure all PA×DIM combinations are generated"
            )
        else:
            report["errors"].append(
                f"Chunk count surplus: expected {EXPECTED_CHUNK_COUNT}, "
                f"got {len(matrix)} (extra {-deficit})"
            )
            report["recommendations"].append(
                "Check Phase 1 deduplication (SP14) to ensure no duplicate PA×DIM combinations"
            )
    
    for (pa, dim), chunk in matrix.items():
        if chunk.policy_area_id != pa:
            report["passed"] = False
            report["errors"].append(
                f"Chunk ({pa}, {dim}) has inconsistent policy_area_id: {chunk.policy_area_id}"
            )
            report["recommendations"].append(
                f"Verify Phase 1 PA×DIM assignment for chunk at position ({pa}, {dim})"
            )
        
        if chunk.dimension_id != dim:
            report["passed"] = False
            report["errors"].append(
                f"Chunk ({pa}, {dim}) has inconsistent dimension_id: {chunk.dimension_id}"
            )
            report["recommendations"].append(
                f"Verify Phase 1 PA×DIM assignment for chunk at position ({pa}, {dim})"
            )
        
        if not chunk.text or not chunk.text.strip():
            report["passed"] = False
            report["errors"].append(
                f"Chunk ({pa}, {dim}) has empty text content"
            )
            report["metrics"]["empty_chunks"] += 1
            report["recommendations"].append(
                "Check Phase 1 text extraction and chunking logic "
                "to ensure all chunks receive content"
            )
        else:
            text_lengths.append(len(chunk.text))
        
        if chunk.provenance is not None:
            report["metrics"]["chunks_with_provenance"] += 1
        
        expected_chunk_id = f"{pa}-{dim}"
        if chunk.chunk_id and chunk.chunk_id != expected_chunk_id:
            report["warnings"].append(
                f"Chunk ({pa}, {dim}) has unexpected chunk_id: "
                f"{chunk.chunk_id} (expected {expected_chunk_id})"
            )
    
    if text_lengths:
        report["metrics"]["avg_text_length"] = sum(text_lengths) // len(text_lengths)
        report["metrics"]["min_text_length"] = min(text_lengths)
        report["metrics"]["max_text_length"] = max(text_lengths)
    
    expected_keys = {(pa, dim) for pa in POLICY_AREAS for dim in DIMENSIONS}
    actual_keys = set(matrix.keys())
    
    missing_keys = expected_keys - actual_keys
    if missing_keys:
        report["passed"] = False
        report["errors"].append(
            f"Missing PA×DIM combinations ({len(missing_keys)}): {sorted(missing_keys)[:10]}"
        )
        report["recommendations"].append(
            "Review Phase 1 subphase SP4 (segmentation) output "
            "to identify why some PA×DIM cells are missing"
        )
    
    extra_keys = actual_keys - expected_keys
    if extra_keys:
        report["passed"] = False
        report["errors"].append(
            f"Unexpected PA×DIM combinations: {sorted(extra_keys)}"
        )
        report["recommendations"].append(
            "Verify that POLICY_AREAS and DIMENSIONS constants match Phase 1 configuration"
        )
    
    if not report["errors"]:
        report["metrics"]["validation_status"] = "PASSED"
    else:
        report["metrics"]["validation_status"] = "FAILED"
    
    provenance_rate = report["metrics"]["chunks_with_provenance"] / len(matrix) if matrix else 0.0
    report["metrics"]["provenance_completeness"] = round(provenance_rate, 3)
    
    if provenance_rate < 0.8:
        report["warnings"].append(
            f"Low provenance completeness: {provenance_rate:.1%} of chunks have provenance data"
        )
    
    return report


def generate_validation_summary(report: Dict[str, any]) -> str:
    """Generate a human-readable validation summary from a validation report.
    
    Args:
        report: Validation report from validate_chunk_matrix_contract()
        
    Returns:
        Formatted multi-line string suitable for logging or display
    """
    lines = [
        "=" * 80,
        "PHASE 1 CHUNK MATRIX VALIDATION SUMMARY",
        "=" * 80,
        f"Status: {'PASSED ✓' if report['passed'] else 'FAILED ✗'}",
        "",
        "Metrics:",
        f"  Total Chunks: {report['metrics']['chunk_count']} / "
        f"{report['metrics']['expected_count']}",
        f"  Unique Policy Areas: {report['metrics']['unique_pa_count']}",
        f"  Unique Dimensions: {report['metrics']['unique_dim_count']}",
    ]
    
    if "avg_text_length" in report["metrics"] and report["metrics"]["avg_text_length"] > 0:
        lines.extend([
            f"  Avg Text Length: {report['metrics']['avg_text_length']} chars",
            f"  Text Length Range: {report['metrics'].get('min_text_length', 0)} - "
            f"{report['metrics'].get('max_text_length', 0)} chars",
        ])
    
    if "provenance_completeness" in report["metrics"]:
        lines.append(
            f"  Provenance Completeness: {report['metrics']['provenance_completeness']:.1%}"
        )
    
    if report["errors"]:
        lines.extend([
            "",
            f"Errors ({len(report['errors'])}):",
        ])
        for error in report["errors"][:10]:
            lines.append(f"  ✗ {error}")
        if len(report["errors"]) > 10:
            lines.append(f"  ... and {len(report['errors']) - 10} more errors")
    
    if report["warnings"]:
        lines.extend([
            "",
            f"Warnings ({len(report['warnings'])}):",
        ])
        for warning in report["warnings"][:10]:
            lines.append(f"  ⚠ {warning}")
        if len(report["warnings"]) > 10:
            lines.append(f"  ... and {len(report['warnings']) - 10} more warnings")
    
    if report["recommendations"]:
        lines.extend([
            "",
            "Recommendations:",
        ])
        for rec in set(report["recommendations"][:5]):
            lines.append(f"  → {rec}")
    
    lines.append("=" * 80)
    return "\n".join(lines)


def build_chunk_matrix(
    document: PreprocessedDocument,
) -> tuple[dict[tuple[str, str], ChunkData], list[tuple[str, str]]]:
    """Construct validated chunk matrix from preprocessed document.

    Builds a dictionary mapping (PA, DIM) tuples to ChunkData instances,
    performs comprehensive validation, and returns sorted keys for deterministic
    iteration. Guarantees immutability through frozen ChunkData dataclass.

    Args:
        document: PreprocessedDocument containing 60 policy chunks

    Returns:
        Tuple of (chunk_matrix, sorted_keys) where:
        - chunk_matrix: dict mapping (PA, DIM) -> ChunkData (immutable)
        - sorted_keys: list of (PA, DIM) tuples sorted deterministically

    Raises:
        ValueError: If validation fails with specific error message indicating:
            - Missing or malformed chunk data
            - Missing required fields (chunk_id, policy_area_id, dimension_id, text)
            - Invalid chunk_id format (not PA{01-10}-DIM{01-06})
            - Wrong chunk count (not 60)
            - Duplicate PA×DIM combinations
            - Missing PA×DIM combinations
            - Null or empty required fields

    Example:
        >>> doc = PreprocessedDocument(...)
        >>> matrix, keys = build_chunk_matrix(doc)
        >>> chunk = matrix[("PA01", "DIM01")]
        >>> assert len(keys) == 60
        >>> assert keys[0] == ("PA01", "DIM01")
        >>> # Matrix is immutable - ChunkData is frozen
    """
    logger.info(
        f"Phase 1 Chunk Matrix Construction: document={document.document_id}, "
        f"input_chunk_count={len(document.chunks)}"
    )

    _validate_document_structure(document)

    matrix: Dict[Tuple[str, str], ChunkData] = {}
    seen_keys: Set[Tuple[str, str]] = set()
    seen_chunk_ids: Set[str] = set()
    validation_errors: List[str] = []

    for idx, chunk in enumerate(document.chunks):
        try:
            _validate_chunk_structure(chunk, idx)
            _validate_chunk_required_fields(chunk, idx)
            _validate_chunk_field_types(chunk, idx)
            
            chunk_id = chunk.chunk_id or f"{chunk.policy_area_id}-{chunk.dimension_id}"
            _validate_chunk_id_format(chunk_id, idx)
            
            key = (chunk.policy_area_id, chunk.dimension_id)
            _validate_chunk_id_consistency(chunk_id, key, idx)
            
            _check_duplicate_key(key, seen_keys, chunk_id, idx)
            _check_duplicate_chunk_id(chunk_id, seen_chunk_ids, idx)
            
            seen_keys.add(key)
            seen_chunk_ids.add(chunk_id)
            matrix[key] = chunk
            
        except ValueError as e:
            validation_errors.append(str(e))
            logger.error(f"Chunk validation failed at index {idx}: {e}")

    if validation_errors:
        error_summary = "\n  - ".join(validation_errors[:10])
        remaining = len(validation_errors) - 10
        if remaining > 0:
            error_summary += f"\n  ... and {remaining} more errors"
        raise ValueError(
            f"Phase 1 chunk matrix validation failed with "
            f"{len(validation_errors)} error(s):\n  - {error_summary}"
        )

    _validate_completeness(seen_keys, POLICY_AREAS, DIMENSIONS)
    _validate_chunk_count(matrix, EXPECTED_CHUNK_COUNT)

    sorted_keys = _sort_keys_deterministically(matrix.keys())

    logger.info(
        f"Phase 1 chunk matrix constructed successfully: unique_chunks={len(matrix)}, "
        f"expected={EXPECTED_CHUNK_COUNT}, all_validations_passed=True"
    )
    _log_audit_summary(matrix, sorted_keys)

    return matrix, sorted_keys


def _validate_document_structure(document: PreprocessedDocument) -> None:
    """Validate document structure before processing chunks.
    
    Atomic validation: document has chunks list with valid structure.
    
    Args:
        document: PreprocessedDocument to validate
        
    Raises:
        ValueError: If document structure is invalid
    """
    if not hasattr(document, 'chunks'):
        raise ValueError(
            "PreprocessedDocument missing 'chunks' attribute. "
            "Ensure Phase 1 SPC ingestion completed successfully. "
            "Check that Phase 1 execution (all 16 subphases) completed without errors."
        )
    
    if not isinstance(document.chunks, list):
        raise ValueError(
            f"PreprocessedDocument.chunks must be a list, got {type(document.chunks).__name__}. "
            "This indicates corrupted Phase 1 output. "
            "Phase 1 must produce a list of ChunkData instances."
        )
    
    if len(document.chunks) == 0:
        raise ValueError(
            "PreprocessedDocument.chunks is empty. "
            "Phase 1 must produce exactly 60 chunks (10 PA × 6 DIM). "
            "Check Phase 1 segmentation (SP4) and smart chunk generation (SP11)."
        )
    
    if not hasattr(document, 'document_id') or not document.document_id:
        raise ValueError(
            "PreprocessedDocument missing or empty document_id. "
            "Phase 0 input validation must set document_id, and Phase 1 must preserve it."
        )
    
    if not hasattr(document, 'processing_mode'):
        raise ValueError(
            "PreprocessedDocument missing processing_mode attribute. "
            "Phase 1 must set processing_mode to 'chunked'."
        )
    
    if document.processing_mode != 'chunked':
        raise ValueError(
            f"PreprocessedDocument.processing_mode must be 'chunked', got '{document.processing_mode}'. "
            "Phase 1 must set processing_mode to 'chunked' for chunk-aware routing."
        )


def _validate_chunk_structure(chunk: ChunkData, idx: int) -> None:
    """Validate chunk is a ChunkData instance.
    
    Atomic validation: chunk type check.
    
    Args:
        chunk: Object to validate
        idx: Chunk index for error reporting
        
    Raises:
        ValueError: If chunk is not ChunkData instance
    """
    if not isinstance(chunk, ChunkData):
        raise ValueError(
            f"Chunk at index {idx}: expected ChunkData instance, got {type(chunk).__name__}. "
            "Phase 1 output must contain only ChunkData instances."
        )


def _validate_chunk_required_fields(chunk: ChunkData, idx: int) -> None:
    """Validate chunk has all required fields with non-null values.
    
    Atomic validation: presence of required fields.
    
    Args:
        chunk: ChunkData to validate
        idx: Chunk index for error reporting

    Raises:
        ValueError: If any required field is missing or None
    """
    required_fields = {
        'text': 'text_content',
        'policy_area_id': 'policy_area_id (PA01-PA10)',
        'dimension_id': 'dimension_id (DIM01-DIM06)',
    }
    
    missing_fields = []
    null_fields = []
    
    for field, description in required_fields.items():
        if not hasattr(chunk, field):
            missing_fields.append(description)
        elif getattr(chunk, field) is None:
            null_fields.append(description)
    
    if missing_fields:
        raise ValueError(
            f"Chunk at index {idx} (id={chunk.id}): missing required field(s) {', '.join(missing_fields)}. "
            "All chunks must have text, policy_area_id, and dimension_id."
        )
    
    if null_fields:
        raise ValueError(
            f"Chunk at index {idx} (id={chunk.id}): null value in required field(s) {', '.join(null_fields)}. "
            "Phase 1 must populate all required fields with non-null values."
        )


def _validate_chunk_field_types(chunk: ChunkData, idx: int) -> None:
    """Validate chunk field types and non-empty values.
    
    Atomic validation: field type and content checks.
    
    Args:
        chunk: ChunkData to validate
        idx: Chunk index for error reporting
        
    Raises:
        ValueError: If field types are invalid or values are empty
    """
    if not isinstance(chunk.text, str):
        raise ValueError(
            f"Chunk at index {idx} (id={chunk.id}): text must be string, got {type(chunk.text).__name__}"
        )
    
    if not chunk.text.strip():
        raise ValueError(
            f"Chunk at index {idx} (id={chunk.id}): text_content is empty or whitespace-only. "
            "All chunks must contain non-empty text."
        )
    
    if not isinstance(chunk.policy_area_id, str):
        raise ValueError(
            f"Chunk at index {idx} (id={chunk.id}): policy_area_id must be string, got {type(chunk.policy_area_id).__name__}"
        )
    
    if not isinstance(chunk.dimension_id, str):
        raise ValueError(
            f"Chunk at index {idx} (id={chunk.id}): dimension_id must be string, got {type(chunk.dimension_id).__name__}"
        )


def _validate_chunk_id_format(chunk_id: str, idx: int) -> None:
    """Validate chunk_id matches PA{01-10}-DIM{01-06} pattern.
    
    Atomic validation: chunk_id format compliance.

    Args:
        chunk_id: Chunk identifier to validate
        idx: Chunk index for error reporting

    Raises:
        ValueError: If chunk_id format is invalid with specific pattern expected
    """
    if not isinstance(chunk_id, str):
        raise ValueError(
            f"Chunk at index {idx}: chunk_id must be string, got {type(chunk_id).__name__}"
        )
    
    if not chunk_id.strip():
        raise ValueError(
            f"Chunk at index {idx}: chunk_id is empty or whitespace-only"
        )
    
    if not CHUNK_ID_PATTERN.match(chunk_id):
        match = re.match(r'^(PA\d{2})-(DIM\d{2})$', chunk_id)
        if match:
            pa_part, dim_part = match.groups()
            
            pa_match = re.match(r'^PA(\d{2})$', pa_part)
            if pa_match:
                pa_num = int(pa_match.group(1))
                if pa_num < 1 or pa_num > 10:
                    raise ValueError(
                        f"Chunk at index {idx}: invalid chunk_id '{chunk_id}'. "
                        f"Policy area must be PA01-PA10, got {pa_part} (value {pa_num} out of range)"
                    )
            
            dim_match = re.match(r'^DIM(\d{2})$', dim_part)
            if dim_match:
                dim_num = int(dim_match.group(1))
                if dim_num < 1 or dim_num > 6:
                    raise ValueError(
                        f"Chunk at index {idx}: invalid chunk_id '{chunk_id}'. "
                        f"Dimension must be DIM01-DIM06, got {dim_part} (value {dim_num} out of range)"
                    )
        
        raise ValueError(
            f"Chunk at index {idx}: invalid chunk_id format '{chunk_id}'. "
            "Expected format: PA{{01-10}}-DIM{{01-06}} (e.g., 'PA01-DIM01', 'PA10-DIM06')"
        )


def _validate_chunk_id_consistency(
    chunk_id: str, key: Tuple[str, str], idx: int
) -> None:
    """Validate chunk_id is consistent with policy_area_id and dimension_id.
    
    Atomic validation: chunk_id matches PA×DIM key.
    
    Args:
        chunk_id: Chunk identifier string
        key: Tuple of (policy_area_id, dimension_id)
        idx: Chunk index for error reporting
        
    Raises:
        ValueError: If chunk_id doesn't match the PA-DIM format from key
    """
    expected_chunk_id = f"{key[0]}-{key[1]}"
    if chunk_id != expected_chunk_id:
        raise ValueError(
            f"Chunk at index {idx}: chunk_id inconsistency detected. "
            f"chunk_id='{chunk_id}' does not match policy_area_id='{key[0]}' and dimension_id='{key[1]}' "
            f"(expected '{expected_chunk_id}'). "
            "Phase 1 must ensure chunk_id equals 'policy_area_id-dimension_id'."
        )


def _check_duplicate_key(
    key: Tuple[str, str],
    seen_keys: Set[Tuple[str, str]],
    chunk_id: str,
    idx: int,
) -> None:
    """Check for duplicate (PA, DIM) keys.
    
    Atomic validation: uniqueness of PA×DIM combination.

    Args:
        key: (policy_area_id, dimension_id) tuple
        seen_keys: Set of previously seen keys
        chunk_id: Chunk identifier for error reporting
        idx: Chunk index for error reporting

    Raises:
        ValueError: If key already exists in seen_keys with specific guidance
    """
    if key in seen_keys:
        raise ValueError(
            f"Chunk at index {idx}: duplicate (PA, DIM) combination detected for '{chunk_id}'. "
            f"The combination ({key[0]}, {key[1]}) already exists in the matrix. "
            "Each PA×DIM combination must appear exactly once. "
            "Phase 1 must produce unique chunks for all 60 combinations (10 PA × 6 DIM)."
        )


def _check_duplicate_chunk_id(
    chunk_id: str,
    seen_chunk_ids: Set[str],
    idx: int,
) -> None:
    """Check for duplicate chunk_id strings.
    
    Atomic validation: uniqueness of chunk_id.

    Args:
        chunk_id: Chunk identifier to check
        seen_chunk_ids: Set of previously seen chunk IDs
        idx: Chunk index for error reporting

    Raises:
        ValueError: If chunk_id already exists with guidance on cause
    """
    if chunk_id in seen_chunk_ids:
        raise ValueError(
            f"Chunk at index {idx}: duplicate chunk_id '{chunk_id}'. "
            f"Each chunk must have a unique identifier. "
            "This error typically indicates Phase 1 produced multiple chunks with the same PA×DIM values, "
            "or chunk_id was manually set to a duplicate value."
        )


def _validate_chunk_count(
    matrix: Dict[Tuple[str, str], ChunkData],
    expected_count: int,
) -> None:
    """Validate chunk matrix has exactly the expected number of chunks.
    
    Atomic validation: chunk count equals 60.

    Args:
        matrix: Chunk matrix keyed by (PA, DIM)
        expected_count: Expected number of chunks (60)

    Raises:
        ValueError: If chunk count doesn't match with diagnostic information
    """
    actual_count = len(matrix)
    if actual_count != expected_count:
        deficit = expected_count - actual_count
        surplus = actual_count - expected_count
        
        if actual_count < expected_count:
            raise ValueError(
                f"Phase 1 chunk matrix cardinality violation: expected {expected_count} unique chunks (10 PA × 6 DIM), "
                f"but found {actual_count} (deficit of {deficit}). "
                "This indicates Phase 1 failed to produce all required PA×DIM combinations. "
                "Check Phase 1 output for missing policy areas or dimensions."
            )
        else:
            raise ValueError(
                f"Phase 1 chunk matrix cardinality violation: expected {expected_count} unique chunks (10 PA × 6 DIM), "
                f"but found {actual_count} (surplus of {surplus}). "
                "This indicates Phase 1 produced duplicate PA×DIM combinations that were not caught. "
                "Verify Phase 1 deduplication logic (SP14)."
            )


def _validate_completeness(
    seen_keys: Set[Tuple[str, str]],
    policy_areas: List[str],
    dimensions: List[str],
) -> None:
    """Validate all required PA×DIM combinations are present.
    
    Atomic validation: completeness of PA×DIM coverage.

    Args:
        seen_keys: Set of (PA, DIM) keys found in document
        policy_areas: List of expected policy areas (PA01-PA10)
        dimensions: List of expected dimensions (DIM01-DIM06)

    Raises:
        ValueError: If any required combinations are missing with detailed diagnostic
    """
    expected_keys = {(pa, dim) for pa in policy_areas for dim in dimensions}
    missing_keys = expected_keys - seen_keys

    if missing_keys:
        missing_sorted = sorted(missing_keys)
        missing_count = len(missing_keys)
        
        missing_by_pa: Dict[str, List[str]] = {}
        missing_by_dim: Dict[str, List[str]] = {}
        
        for pa, dim in missing_sorted:
            missing_by_pa.setdefault(pa, []).append(dim)
            missing_by_dim.setdefault(dim, []).append(pa)
        
        display_limit = 15
        missing_display = [f"{pa}-{dim}" for pa, dim in missing_sorted[:display_limit]]
        
        error_parts = [
            f"Phase 1 chunk matrix completeness violation: missing {missing_count} PA×DIM combination(s).",
            f"Missing combinations: [{', '.join(missing_display)}",
        ]
        
        if missing_count > display_limit:
            error_parts.append(f", ... and {missing_count - display_limit} more")
        
        error_parts.append("]")
        
        if len(missing_by_pa) <= 3:
            pa_summary = "; ".join(
                f"{pa}: missing {len(dims)} dimension(s) ({', '.join(dims)})"
                for pa, dims in sorted(missing_by_pa.items())
            )
            error_parts.append(f"\nBy policy area: {pa_summary}")
        
        if len(missing_by_dim) <= 3:
            dim_summary = "; ".join(
                f"{dim}: missing {len(pas)} policy area(s) ({', '.join(pas)})"
                for dim, pas in sorted(missing_by_dim.items())
            )
            error_parts.append(f"\nBy dimension: {dim_summary}")
        
        error_parts.append(
            "\nPhase 1 must produce exactly 60 chunks covering all combinations. "
            "Check Phase 1 segmentation logic (SP4) and ensure all PA×DIM cells are populated."
        )
        
        raise ValueError("".join(error_parts))


def _sort_keys_deterministically(
    keys: Iterable[Tuple[str, str]],
) -> List[Tuple[str, str]]:
    """Sort matrix keys deterministically by PA then DIM.
    
    Ensures O(1) lookup operations benefit from predictable iteration order.

    Args:
        keys: Iterable of (PA, DIM) tuple keys

    Returns:
        Sorted list of keys for deterministic iteration (PA01-DIM01, PA01-DIM02, ..., PA10-DIM06)
    """
    return sorted(keys, key=lambda k: (k[0], k[1]))


def _log_audit_summary(
    matrix: Dict[Tuple[str, str], ChunkData],
    sorted_keys: List[Tuple[str, str]],
) -> None:
    """Log comprehensive audit summary of constructed chunk matrix.
    
    Provides diagnostic information for Phase 1 output quality assessment.

    Args:
        matrix: Constructed chunk matrix (immutable ChunkData instances)
        sorted_keys: Sorted list of matrix keys
    """
    pa_counts: Dict[str, int] = {pa: 0 for pa in POLICY_AREAS}
    dim_counts: Dict[str, int] = {dim: 0 for dim in DIMENSIONS}
    
    text_lengths: List[int] = []
    chunks_with_provenance = 0

    for pa, dim in sorted_keys:
        pa_counts[pa] = pa_counts.get(pa, 0) + 1
        dim_counts[dim] = dim_counts.get(dim, 0) + 1
        
        chunk = matrix[(pa, dim)]
        text_lengths.append(len(chunk.text))
        
        if chunk.provenance is not None:
            chunks_with_provenance += 1

    total_text_length = sum(text_lengths)
    avg_text_length = total_text_length // len(matrix) if matrix else 0
    min_text_length = min(text_lengths) if text_lengths else 0
    max_text_length = max(text_lengths) if text_lengths else 0
    
    provenance_completeness = chunks_with_provenance / len(matrix) if matrix else 0.0

    logger.info(
        "phase1_chunk_matrix_audit_summary",
        extra={
            "total_chunks": len(matrix),
            "expected_chunks": EXPECTED_CHUNK_COUNT,
            "validation_passed": True,
            "chunks_per_policy_area": pa_counts,
            "chunks_per_dimension": dim_counts,
            "text_statistics": {
                "total_chars": total_text_length,
                "avg_length": avg_text_length,
                "min_length": min_text_length,
                "max_length": max_text_length,
            },
            "provenance_completeness": round(provenance_completeness, 3),
            "chunks_with_provenance": chunks_with_provenance,
            "immutability_guaranteed": True,
        },
    )


__all__ = [
    "build_chunk_matrix",
    "validate_chunk_matrix_contract",
    "generate_validation_summary",
    "ChunkMatrixValidationError",
    "POLICY_AREAS",
    "DIMENSIONS",
    "EXPECTED_CHUNK_COUNT",
    "CHUNK_ID_PATTERN",
]
