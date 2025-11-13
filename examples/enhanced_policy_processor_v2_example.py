"""
Example: Policy Processor with V2 Contract Integration
=======================================================

This module demonstrates how to integrate V2 contracts into the
policy_processor while maintaining backward compatibility.

This is a minimal example showing the pattern to follow for migration.

Author: Policy Analytics Research Unit
Version: 1.0.0
License: Proprietary
"""

import sys
from pathlib import Path

# Add src to path

import time
from typing import Any, Dict

from saaaaaa.utils.contracts import (
    # V2 Contracts
    AnalysisInputV2,
    AnalysisOutputV2,
    ProcessedTextV2,
    StructuredLogger,
    compute_content_digest,
    # V2 Exceptions
    ContractValidationError,
)
from saaaaaa.utils.contract_adapters import (
    adapt_analysis_input_v1_to_v2,
    adapt_dict_to_processed_text_v2,
    v2_to_v1_dict,
    validate_flow_compatibility,
)
from saaaaaa.utils.deterministic_execution import (
    DeterministicExecutor,
    DeterministicSeedManager,
)


# ============================================================================
# ENHANCED POLICY PROCESSOR WITH V2 CONTRACTS
# ============================================================================

class EnhancedPolicyProcessorV2:
    """
    Example policy processor with V2 contract enforcement.
    
    Demonstrates:
    - V2 contract usage
    - Deterministic execution
    - Structured logging
    - Error handling with event IDs
    - Flow compatibility validation
    
    Examples:
        >>> processor = EnhancedPolicyProcessorV2(policy_unit_id="PDM-001")
        >>> result = processor.process_policy_text(
        ...     raw_text="Policy document text",
        ...     document_id="DOC-123"
        ... )
        >>> result.dimension
        'D1_INSUMOS'
    """
    
    def __init__(
        self,
        policy_unit_id: str,
        base_seed: int = 42,
        enable_logging: bool = True
    ):
        """
        Initialize enhanced processor with V2 contracts.
        
        Args:
            policy_unit_id: Policy unit identifier (e.g., "PDM-001")
            base_seed: Seed for deterministic execution
            enable_logging: Whether to enable structured logging
        """
        self.policy_unit_id = policy_unit_id
        self.seed_manager = DeterministicSeedManager(base_seed=base_seed)
        self.executor = DeterministicExecutor(
            base_seed=base_seed,
            logger_name=__name__,
            enable_logging=enable_logging
        )
        self.logger = StructuredLogger(__name__) if enable_logging else None
        
        # Processing statistics
        self.stats = {
            "total_processed": 0,
            "total_latency_ms": 0.0,
            "errors": 0
        }
    
    def preprocess_text(
        self,
        raw_text: str,
        normalize: bool = True
    ) -> ProcessedTextV2:
        """
        Preprocess policy text with V2 contract output.
        
        Args:
            raw_text: Raw policy document text
            normalize: Whether to apply normalization
            
        Returns:
            ProcessedTextV2 with input/output digests
            
        Raises:
            ContractValidationError: If input is invalid
            
        Examples:
            >>> processor = EnhancedPolicyProcessorV2("PDM-001")
            >>> result = processor.preprocess_text("Policy text")
            >>> len(result.input_digest)
            64
        """
        start_time = time.perf_counter()
        
        # Validate input
        if not raw_text or len(raw_text) < 10:
            raise ContractValidationError(
                "Raw text too short for processing (minimum 10 characters)",
                field="raw_text"
            )
        
        # Normalize (deterministic operation)
        with self.seed_manager.scoped_seed("preprocess_normalize"):
            if normalize:
                # Simple normalization example
                normalized = raw_text.strip().replace("\n\n", "\n")
            else:
                normalized = raw_text
        
        # Calculate processing latency
        latency_ms = (time.perf_counter() - start_time) * 1000
        
        # Create V2 contract
        result = adapt_dict_to_processed_text_v2(
            raw_text=raw_text,
            normalized_text=normalized,
            policy_unit_id=self.policy_unit_id,
            language="es",  # Spanish for Colombian policy documents
            processing_latency_ms=latency_ms
        )
        
        # Log structured event
        if self.logger:
            self.logger.log_execution(
                operation="preprocess_text",
                correlation_id=result.correlation_id,
                success=True,
                latency_ms=latency_ms,
                input_size=len(raw_text),
                output_size=len(normalized)
            )
        
        return result
    
    def process_policy_text(
        self,
        raw_text: str,
        document_id: str,
        preprocess: bool = True
    ) -> AnalysisOutputV2:
        """
        Process policy text with full V2 contract pipeline.
        
        Args:
            raw_text: Raw policy document text
            document_id: Document identifier
            preprocess: Whether to preprocess text first
            
        Returns:
            AnalysisOutputV2 with validation results
            
        Raises:
            ContractValidationError: If input is invalid
            FlowCompatibilityError: If pipeline stages are incompatible
            
        Examples:
            >>> processor = EnhancedPolicyProcessorV2("PDM-001")
            >>> result = processor.process_policy_text(
            ...     raw_text="Policy text",
            ...     document_id="DOC-123"
            ... )
            >>> 0.0 <= result.confidence <= 1.0
            True
        """
        start_time = time.perf_counter()
        
        try:
            # Stage 1: Preprocessing
            if preprocess:
                preprocessed = self.preprocess_text(raw_text)
                text_to_analyze = preprocessed.normalized_text
                
                # Validate flow compatibility
                validate_flow_compatibility(
                    producer_output=preprocessed.model_dump(),
                    consumer_expected_fields=["normalized_text"],
                    producer_name="preprocess",
                    consumer_name="analyze"
                )
            else:
                text_to_analyze = raw_text
            
            # Stage 2: Create analysis input with V2 contract
            analysis_input = AnalysisInputV2.create_from_text(
                text=text_to_analyze,
                document_id=document_id,
                policy_unit_id=self.policy_unit_id
            )
            
            # Stage 3: Perform analysis (deterministic)
            result = self._analyze_with_v2_contract(analysis_input)
            
            # Update statistics
            self.stats["total_processed"] += 1
            latency_ms = (time.perf_counter() - start_time) * 1000
            self.stats["total_latency_ms"] += latency_ms
            
            # Log success
            if self.logger:
                self.logger.log_execution(
                    operation="process_policy_text",
                    correlation_id=analysis_input.correlation_id,
                    success=True,
                    latency_ms=latency_ms,
                    dimension=result.dimension,
                    confidence=result.confidence
                )
            
            return result
            
        except Exception as e:
            # Update error statistics
            self.stats["errors"] += 1
            
            # Log error with event ID
            if self.logger:
                self.logger.log_execution(
                    operation="process_policy_text",
                    correlation_id="unknown",
                    success=False,
                    latency_ms=(time.perf_counter() - start_time) * 1000,
                    error=str(e)[:200]
                )
            
            raise
    
    def _analyze_with_v2_contract(
        self,
        analysis_input: AnalysisInputV2
    ) -> AnalysisOutputV2:
        """
        Internal analysis with V2 contract enforcement.
        
        This method demonstrates deterministic analysis with automatic
        seed management and structured logging.
        
        Args:
            analysis_input: Validated V2 analysis input
            
        Returns:
            AnalysisOutputV2 with results
        """
        start_time = time.perf_counter()
        
        # Use scoped seed for deterministic processing
        with self.seed_manager.scoped_seed("analyze_policy"):
            # Example: Simple keyword matching for D1_INSUMOS dimension
            # (In real implementation, this would be more sophisticated)
            keywords = ["diagnóstico", "línea base", "presupuesto", "capacidad"]
            matches = [kw for kw in keywords if kw in analysis_input.text.lower()]
            
            # Compute confidence (example: simple keyword coverage)
            confidence = min(len(matches) / len(keywords), 1.0)
        
        # Calculate processing latency
        latency_ms = (time.perf_counter() - start_time) * 1000
        
        # Create output with content digest
        output_data = {
            "dimension": "D1_INSUMOS",
            "category": "diagnostico_cuantitativo",
            "confidence": confidence,
            "matches": matches
        }
        output_digest = compute_content_digest(str(output_data))
        
        return AnalysisOutputV2(
            dimension=output_data["dimension"],
            category=output_data["category"],
            confidence=output_data["confidence"],
            matches=output_data["matches"],
            output_digest=output_digest,
            policy_unit_id=self.policy_unit_id,
            processing_latency_ms=latency_ms,
            evidence=matches if matches else None
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get processing statistics.
        
        Returns:
            Dictionary with processing statistics
            
        Examples:
            >>> processor = EnhancedPolicyProcessorV2("PDM-001")
            >>> stats = processor.get_statistics()
            >>> "total_processed" in stats
            True
        """
        avg_latency = (
            self.stats["total_latency_ms"] / self.stats["total_processed"]
            if self.stats["total_processed"] > 0
            else 0.0
        )
        
        return {
            **self.stats,
            "average_latency_ms": round(avg_latency, 2),
            "error_rate": (
                self.stats["errors"] / self.stats["total_processed"]
                if self.stats["total_processed"] > 0
                else 0.0
            )
        }


# ============================================================================
# BACKWARD COMPATIBLE WRAPPER
# ============================================================================

class PolicyProcessorV1CompatWrapper:
    """
    Wrapper that maintains V1 dict interface while using V2 internally.
    
    Use this for gradual migration of existing code.
    
    Examples:
        >>> wrapper = PolicyProcessorV1CompatWrapper("PDM-001")
        >>> v1_input = {"text": "Policy text", "document_id": "DOC-1"}
        >>> v1_output = wrapper.process_v1_compatible(v1_input)
        >>> "dimension" in v1_output
        True
    """
    
    def __init__(self, policy_unit_id: str):
        """Initialize with V2 processor internally."""
        self.v2_processor = EnhancedPolicyProcessorV2(
            policy_unit_id=policy_unit_id,
            enable_logging=True
        )
    
    def process_v1_compatible(self, v1_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process with V1 dict interface, V2 contracts internally.
        
        Args:
            v1_input: V1-style input dictionary
            
        Returns:
            V1-style output dictionary
        """
        # Adapt V1 input to V2
        v2_input = adapt_analysis_input_v1_to_v2(
            v1_input,
            self.v2_processor.policy_unit_id
        )
        
        # Process with V2
        v2_output = self.v2_processor.process_policy_text(
            raw_text=v2_input.text,
            document_id=v2_input.document_id,
            preprocess=True
        )
        
        # Convert V2 output to V1 dict
        return v2_to_v1_dict(v2_output)


# ============================================================================
# IN-SCRIPT TESTS
# ============================================================================

if __name__ == "__main__":
    import doctest
    
    # Run doctests
    print("Running doctests...")
    doctest.testmod(verbose=True)
    
    # Additional integration tests
    print("\n" + "="*60)
    print("Enhanced Policy Processor Integration Tests")
    print("="*60)
    
    # Test 1: V2 processor with full pipeline
    print("\n1. Testing V2 processor with full pipeline:")
    processor = EnhancedPolicyProcessorV2(
        policy_unit_id="PDM-001",
        base_seed=42,
        enable_logging=False  # Disable for cleaner test output
    )
    
    test_text = """
    Diagnóstico situacional del municipio. La línea base indica que
    el presupuesto asignado es de $1,000,000. Se requiere fortalecer
    la capacidad institucional para implementar el plan.
    """
    
    result = processor.process_policy_text(
        raw_text=test_text,
        document_id="TEST-001",
        preprocess=True
    )
    
    print(f"   ✓ Dimension: {result.dimension}")
    print(f"   ✓ Confidence: {result.confidence:.2f}")
    print(f"   ✓ Matches: {result.matches}")
    print(f"   ✓ Digest: {result.output_digest[:16]}...")
    print(f"   ✓ Latency: {result.processing_latency_ms:.2f}ms")
    
    assert result.dimension == "D1_INSUMOS"
    assert 0.0 <= result.confidence <= 1.0
    assert len(result.output_digest) == 64
    
    # Test 2: V1 compatibility wrapper
    print("\n2. Testing V1 compatibility wrapper:")
    wrapper = PolicyProcessorV1CompatWrapper("PDM-001")
    
    v1_input = {
        "text": test_text,
        "document_id": "TEST-002"
    }
    
    v1_output = wrapper.process_v1_compatible(v1_input)
    
    print(f"   ✓ V1 output keys: {list(v1_output.keys())}")
    print(f"   ✓ Dimension: {v1_output['dimension']}")
    print(f"   ✓ Confidence: {v1_output['confidence']:.2f}")
    
    assert "dimension" in v1_output
    assert "confidence" in v1_output
    assert "matches" in v1_output
    
    # Test 3: Statistics tracking
    print("\n3. Testing statistics tracking:")
    stats = processor.get_statistics()
    print(f"   ✓ Total processed: {stats['total_processed']}")
    print(f"   ✓ Average latency: {stats['average_latency_ms']:.2f}ms")
    print(f"   ✓ Error rate: {stats['error_rate']:.2%}")
    
    assert stats["total_processed"] > 0
    assert stats["error_rate"] == 0.0
    
    # Test 4: Determinism verification
    print("\n4. Testing determinism:")
    processor2 = EnhancedPolicyProcessorV2(
        policy_unit_id="PDM-001",
        base_seed=42,  # Same seed
        enable_logging=False
    )
    
    result2 = processor2.process_policy_text(
        raw_text=test_text,
        document_id="TEST-001",
        preprocess=True
    )
    
    # With same seed, results should be identical
    assert result.confidence == result2.confidence
    assert result.matches == result2.matches
    print("   ✓ Deterministic execution verified")
    
    print("\n" + "="*60)
    print("All integration tests passed!")
    print("="*60)
