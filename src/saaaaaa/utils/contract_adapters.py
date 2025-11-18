"""
Contract Migration and Flow Adapters
=====================================

Adapters and utilities to migrate existing code to V2 contracts while
maintaining flow compatibility across pipeline stages.

This module provides:
- V1 to V2 contract adapters
- Flow compatibility validators
- Migration helpers
- Backward compatibility shims

Author: Policy Analytics Research Unit
Version: 1.0.0
License: Proprietary
"""

from __future__ import annotations

import hashlib
import logging
from typing import TYPE_CHECKING, Any

from pydantic import ValidationError

from .enhanced_contracts import (
    AnalysisInputV2,
    ContractValidationError,
    DocumentMetadataV2,
    FlowCompatibilityError,
    ProcessedTextV2,
    compute_content_digest,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger(__name__)


# ============================================================================
# V1 TO V2 ADAPTERS
# ============================================================================

def adapt_document_metadata_v1_to_v2(
    v1_metadata: dict[str, Any],
    policy_unit_id: str,
    file_content: bytes | None = None
) -> DocumentMetadataV2:
    """
    Adapt V1 DocumentMetadata (dict/TypedDict) to V2 Pydantic model.

    Args:
        v1_metadata: V1 metadata dictionary
        policy_unit_id: Policy unit identifier
        file_content: Optional file content for computing digest

    Returns:
        V2 DocumentMetadataV2 instance

    Raises:
        ContractValidationError: If required fields are missing or invalid

    Examples:
        >>> v1_meta = {
        ...     "file_path": "/path/to/doc.pdf",
        ...     "file_name": "doc.pdf",
        ...     "num_pages": 10,
        ...     "file_size_bytes": 1024,
        ...     "file_hash": "abc123"
        ... }
        >>> v2_meta = adapt_document_metadata_v1_to_v2(v1_meta, "PDM-001")
        >>> v2_meta.policy_unit_id
        'PDM-001'
    """
    try:
        # Extract V1 fields
        file_path = v1_metadata.get("file_path", "")
        file_name = v1_metadata.get("file_name", "")
        num_pages = v1_metadata.get("num_pages", 1)
        file_size_bytes = v1_metadata.get("file_size_bytes", 0)

        # V1 uses "file_hash", V2 uses "content_digest" (SHA-256)
        content_digest = v1_metadata.get("file_hash", "")

        # If file_hash is not SHA-256 (64 hex chars), compute it from content if available
        if len(content_digest) != 64 or not all(c in '0123456789abcdef' for c in content_digest.lower()):
            if file_content:
                content_digest = hashlib.sha256(file_content).hexdigest()
            else:
                # Fallback: use a placeholder (should be computed properly in production)
                logger.warning("No valid SHA-256 hash available for document metadata")
                content_digest = "0" * 64  # Placeholder

        # Create V2 instance
        return DocumentMetadataV2(
            file_path=file_path,
            file_name=file_name,
            num_pages=num_pages,
            file_size_bytes=file_size_bytes,
            content_digest=content_digest,
            policy_unit_id=policy_unit_id,
            # Optional fields
            pdf_metadata=v1_metadata.get("pdf_metadata"),
            author=v1_metadata.get("author"),
            title=v1_metadata.get("title"),
            creation_date=v1_metadata.get("creation_date"),
        )

    except ValidationError as e:
        raise ContractValidationError(
            f"Failed to adapt V1 metadata to V2: {e}",
            field="document_metadata"
        ) from e


def adapt_analysis_input_v1_to_v2(
    v1_input: dict[str, Any],
    policy_unit_id: str
) -> AnalysisInputV2:
    """
    Adapt V1 AnalysisInput to V2.

    Args:
        v1_input: V1 analysis input dictionary
        policy_unit_id: Policy unit identifier

    Returns:
        V2 AnalysisInputV2 instance

    Raises:
        ContractValidationError: If required fields are missing

    Examples:
        >>> v1_input = {"text": "Sample text", "document_id": "DOC-1"}
        >>> v2_input = adapt_analysis_input_v1_to_v2(v1_input, "PDM-001")
        >>> v2_input.policy_unit_id
        'PDM-001'
    """
    try:
        text = v1_input.get("text", "")
        document_id = v1_input.get("document_id", "")

        if not text:
            raise ContractValidationError("text field is required", field="text")
        if not document_id:
            raise ContractValidationError("document_id field is required", field="document_id")

        # Use factory method to auto-compute digest
        return AnalysisInputV2.create_from_text(
            text=text,
            document_id=document_id,
            policy_unit_id=policy_unit_id,
            metadata=v1_input.get("metadata"),
            context=v1_input.get("context"),
            sentences=v1_input.get("sentences"),
        )

    except ValidationError as e:
        raise ContractValidationError(
            f"Failed to adapt V1 analysis input to V2: {e}",
            field="analysis_input"
        ) from e


def adapt_dict_to_processed_text_v2(
    raw_text: str,
    normalized_text: str,
    policy_unit_id: str,
    language: str = "es",
    processing_latency_ms: float = 0.0,
    **kwargs: Any
) -> ProcessedTextV2:
    """
    Create ProcessedTextV2 from raw processing results.

    Args:
        raw_text: Original text
        normalized_text: Processed text
        policy_unit_id: Policy unit identifier
        language: Language code (default: "es" for Spanish)
        processing_latency_ms: Processing time in milliseconds
        **kwargs: Additional optional fields

    Returns:
        ProcessedTextV2 instance

    Examples:
        >>> result = adapt_dict_to_processed_text_v2(
        ...     raw_text="Original",
        ...     normalized_text="Normalized",
        ...     policy_unit_id="PDM-001"
        ... )
        >>> result.language
        'es'
    """
    try:
        return ProcessedTextV2(
            raw_text=raw_text,
            normalized_text=normalized_text,
            language=language,
            input_digest=compute_content_digest(raw_text),
            output_digest=compute_content_digest(normalized_text),
            policy_unit_id=policy_unit_id,
            processing_latency_ms=processing_latency_ms,
            sentences=kwargs.get("sentences"),
            sections=kwargs.get("sections"),
            payload_size_bytes=kwargs.get("payload_size_bytes", len(normalized_text.encode('utf-8'))),
        )
    except ValidationError as e:
        raise ContractValidationError(
            f"Failed to create ProcessedTextV2: {e}",
            field="processed_text"
        ) from e


# ============================================================================
# FLOW COMPATIBILITY VALIDATORS
# ============================================================================

def validate_flow_compatibility(
    producer_output: Any,
    consumer_expected_fields: Sequence[str],
    producer_name: str,
    consumer_name: str
) -> None:
    """
    Validate that producer output matches consumer expectations.

    Args:
        producer_output: Output from producer (dict or Pydantic model)
        consumer_expected_fields: List of required field names
        producer_name: Name of producer component
        consumer_name: Name of consumer component

    Raises:
        FlowCompatibilityError: If required fields are missing

    Examples:
        >>> output = {"text": "test", "document_id": "123"}
        >>> validate_flow_compatibility(
        ...     output,
        ...     ["text", "document_id"],
        ...     "processor",
        ...     "analyzer"
        ... )
    """
    # Convert Pydantic model to dict if needed
    if hasattr(producer_output, "model_dump"):
        output_dict = producer_output.model_dump()
    elif isinstance(producer_output, dict):
        output_dict = producer_output
    else:
        raise FlowCompatibilityError(
            f"Unexpected output type from {producer_name}: {type(producer_output).__name__}",
            producer=producer_name,
            consumer=consumer_name
        )

    # Check for required fields
    missing_fields = [field for field in consumer_expected_fields if field not in output_dict]

    if missing_fields:
        raise FlowCompatibilityError(
            f"Flow compatibility error: {producer_name} output missing required fields for {consumer_name}: {missing_fields}",
            producer=producer_name,
            consumer=consumer_name
        )

    logger.debug(
        f"Flow compatibility validated: {producer_name} -> {consumer_name}"
    )


def validate_pipeline_stage_io(
    stage_name: str,
    input_contract: type,
    output_contract: type,
    actual_input: Any,
    actual_output: Any
) -> tuple[Any, Any]:
    """
    Validate input/output contracts for a pipeline stage.

    Args:
        stage_name: Name of the pipeline stage
        input_contract: Expected input contract type
        output_contract: Expected output contract type
        actual_input: Actual input value
        actual_output: Actual output value

    Returns:
        Tuple of (validated_input, validated_output)

    Raises:
        ContractValidationError: If contracts are violated

    Examples:
        >>> # Example with dict inputs/outputs
        >>> validated_in, validated_out = validate_pipeline_stage_io(
        ...     "test_stage",
        ...     dict,
        ...     dict,
        ...     {"key": "value"},
        ...     {"result": "success"}
        ... )
    """
    # Validate input
    if not isinstance(actual_input, input_contract):
        # Try to adapt if it's a dict and we expect a Pydantic model
        if isinstance(actual_input, dict) and hasattr(input_contract, "model_validate"):
            try:
                validated_input = input_contract.model_validate(actual_input)
            except ValidationError as e:
                raise ContractValidationError(
                    f"Stage {stage_name} input contract violation: {e}",
                    field="input"
                ) from e
        else:
            raise ContractValidationError(
                f"Stage {stage_name} expected input type {input_contract.__name__}, got {type(actual_input).__name__}",
                field="input"
            )
    else:
        validated_input = actual_input

    # Validate output
    if not isinstance(actual_output, output_contract):
        if isinstance(actual_output, dict) and hasattr(output_contract, "model_validate"):
            try:
                validated_output = output_contract.model_validate(actual_output)
            except ValidationError as e:
                raise ContractValidationError(
                    f"Stage {stage_name} output contract violation: {e}",
                    field="output"
                ) from e
        else:
            raise ContractValidationError(
                f"Stage {stage_name} expected output type {output_contract.__name__}, got {type(actual_output).__name__}",
                field="output"
            )
    else:
        validated_output = actual_output

    return validated_input, validated_output


# ============================================================================
# BACKWARD COMPATIBILITY HELPERS
# ============================================================================

def v2_to_v1_dict(v2_model: Any) -> dict[str, Any]:
    """
    Convert V2 Pydantic model to V1-compatible dict.

    Removes V2-specific fields (schema_version, timestamp_utc, correlation_id, etc.)
    to maintain backward compatibility with V1 consumers.

    Args:
        v2_model: V2 Pydantic model instance

    Returns:
        V1-compatible dictionary

    Examples:
        >>> from saaaaaa.utils.enhanced_contracts import AnalysisInputV2
        >>> v2_input = AnalysisInputV2.create_from_text(
        ...     text="test",
        ...     document_id="DOC-1",
        ...     policy_unit_id="PDM-001"
        ... )
        >>> v1_dict = v2_to_v1_dict(v2_input)
        >>> "text" in v1_dict and "schema_version" not in v1_dict
        True
    """
    full_dict = v2_model.model_dump() if hasattr(v2_model, "model_dump") else dict(v2_model)

    # Remove V2-specific fields
    v2_specific_fields = {
        "schema_version",
        "timestamp_utc",
        "correlation_id",
        "input_digest",
        "output_digest",
        "content_digest",
        "policy_unit_id",
        "processing_latency_ms",
        "payload_size_bytes",
        "execution_id",
        "parent_correlation_id",
    }

    return {k: v for k, v in full_dict.items() if k not in v2_specific_fields}


# ============================================================================
# MIGRATION HELPERS
# ============================================================================

class ContractMigrationHelper:
    """
    Helper class to assist with V1 to V2 contract migration.

    Provides utilities for gradual migration and compatibility testing.
    """

    @staticmethod
    def wrap_v1_function_with_v2_contracts(
        func: callable,
        policy_unit_id: str,
        adapt_input: bool = True,
        adapt_output: bool = True
    ) -> callable:
        """
        Wrap a V1 function to use V2 contracts.

        Args:
            func: V1 function to wrap
            policy_unit_id: Policy unit identifier
            adapt_input: Whether to adapt input from V2 to V1
            adapt_output: Whether to adapt output from V1 to V2

        Returns:
            Wrapped function with V2 contract support
        """
        def wrapper(*args, **kwargs):
            # TODO: Implement input/output adaptation based on function signature
            # For now, just pass through
            return func(*args, **kwargs)

        return wrapper

    @staticmethod
    def log_migration_status(component_name: str, migrated: bool) -> None:
        """
        Log migration status for tracking.

        Args:
            component_name: Name of component
            migrated: Whether component is migrated to V2
        """
        status = "MIGRATED" if migrated else "V1_LEGACY"
        logger.info(
            f"Component migration status: {component_name} = {status}"
        )


# ============================================================================
# IN-SCRIPT TESTS
# ============================================================================

if __name__ == "__main__":
    import doctest

    # Run doctests
    print("Running doctests...")
    doctest.testmod(verbose=True)

    # Additional tests
    print("\n" + "="*60)
    print("Contract Adapter Tests")
    print("="*60)

    # Test 1: V1 to V2 metadata adaptation
    print("\n1. Testing V1 to V2 metadata adaptation:")
    v1_meta = {
        "file_path": "/path/to/doc.pdf",
        "file_name": "doc.pdf",
        "num_pages": 10,
        "file_size_bytes": 1024,
        "file_hash": "a" * 64,  # Valid SHA-256
    }
    v2_meta = adapt_document_metadata_v1_to_v2(v1_meta, "PDM-001")
    assert v2_meta.policy_unit_id == "PDM-001"
    assert v2_meta.num_pages == 10
    print(f"   ✓ Adapted metadata: policy_unit_id={v2_meta.policy_unit_id}")

    # Test 2: V1 to V2 analysis input adaptation
    print("\n2. Testing V1 to V2 analysis input adaptation:")
    v1_input = {"text": "Sample policy text", "document_id": "DOC-123"}
    v2_input = adapt_analysis_input_v1_to_v2(v1_input, "PDM-001")
    assert v2_input.text == "Sample policy text"
    assert v2_input.policy_unit_id == "PDM-001"
    assert len(v2_input.input_digest) == 64  # SHA-256
    print(f"   ✓ Adapted input: digest={v2_input.input_digest[:16]}...")

    # Test 3: Flow compatibility validation
    print("\n3. Testing flow compatibility validation:")
    output = {"text": "test", "document_id": "123", "extra_field": "value"}
    validate_flow_compatibility(
        output,
        ["text", "document_id"],
        "processor",
        "analyzer"
    )
    print("   ✓ Flow compatibility validated")

    # Test 4: V2 to V1 conversion
    print("\n4. Testing V2 to V1 backward compatibility:")
    v2_model = AnalysisInputV2.create_from_text(
        text="test",
        document_id="DOC-1",
        policy_unit_id="PDM-001"
    )
    v1_dict = v2_to_v1_dict(v2_model)
    assert "text" in v1_dict
    assert "schema_version" not in v1_dict  # V2-specific field removed
    assert "correlation_id" not in v1_dict
    print(f"   ✓ V2 to V1 conversion: {list(v1_dict.keys())}")

    # Test 5: ProcessedText creation
    print("\n5. Testing ProcessedTextV2 creation:")
    processed = adapt_dict_to_processed_text_v2(
        raw_text="Original text",
        normalized_text="Normalized text",
        policy_unit_id="PDM-001",
        language="es"
    )
    assert processed.language == "es"
    assert len(processed.input_digest) == 64
    print(f"   ✓ ProcessedText created: language={processed.language}")

    print("\n" + "="*60)
    print("All adapter tests passed!")
    print("="*60)
