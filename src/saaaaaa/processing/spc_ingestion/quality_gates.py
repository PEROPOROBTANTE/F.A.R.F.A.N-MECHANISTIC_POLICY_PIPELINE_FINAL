"""
Quality gates for SPC (Smart Policy Chunks) validation - Canonical Phase-One.

Validates quality metrics, enforces invariants, and ensures compatibility
with downstream phases in the canonical pipeline flux.

MAXIMUM STANDARD: No tolerance for data quality degradation.
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SPCQualityGates:
    """Quality validation gates for Smart Policy Chunks ingestion."""

    # Phase-one output quality thresholds
    MIN_CHUNKS = 5
    MAX_CHUNKS = 200
    MIN_CHUNK_LENGTH = 50  # characters
    MAX_CHUNK_LENGTH = 5000
    MIN_STRATEGIC_SCORE = 0.3
    MIN_QUALITY_SCORE = 0.5
    REQUIRED_CHUNK_FIELDS = ['text', 'chunk_id', 'strategic_importance', 'quality_score']

    # Compatibility thresholds for downstream phases
    MIN_EMBEDDING_DIM = 384  # For semantic analysis
    REQUIRED_METADATA_FIELDS = ['document_id', 'title', 'version']

    # CRITICAL quality metrics (per README specifications)
    MIN_PROVENANCE_COMPLETENESS = 1.0  # 100% REQUIRED (no partial coverage tolerated)
    MIN_STRUCTURAL_CONSISTENCY = 1.0   # 100% REQUIRED (perfect structure)
    MIN_BOUNDARY_F1 = 0.85             # Chunk boundary quality
    MIN_BUDGET_CONSISTENCY = 0.95      # Budget data consistency
    MIN_TEMPORAL_ROBUSTNESS = 0.80     # Temporal data quality

    def validate_input(self, document_path: Path) -> dict[str, Any]:
        """
        Validate input document before processing.

        Args:
            document_path: Path to input document

        Returns:
            Dictionary with validation results
        """
        failures = []

        # Check file exists
        if not document_path.exists():
            failures.append(f"Input document not found: {document_path}")
            return {"passed": False, "failures": failures}

        # Check file size (not empty, not too large)
        file_size = document_path.stat().st_size
        if file_size == 0:
            failures.append("Input document is empty")
        elif file_size > 50 * 1024 * 1024:  # 50MB limit
            failures.append(f"Input document too large: {file_size / 1024 / 1024:.1f}MB")

        # Check file extension
        if document_path.suffix.lower() not in ['.txt', '.pdf', '.json']:
            failures.append(f"Unsupported file type: {document_path.suffix}")

        return {
            "passed": len(failures) == 0,
            "failures": failures,
            "file_size_bytes": file_size,
        }

    def validate_chunks(self, chunks: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Validate processed chunks from phase-one.

        Args:
            chunks: List of smart policy chunks

        Returns:
            Dictionary with validation results
        """
        failures = []
        warnings = []

        # Check chunk count
        if len(chunks) < self.MIN_CHUNKS:
            failures.append(f"Too few chunks: {len(chunks)} < {self.MIN_CHUNKS}")
        elif len(chunks) > self.MAX_CHUNKS:
            warnings.append(f"High chunk count: {len(chunks)} > {self.MAX_CHUNKS}")

        # Validate each chunk
        for idx, chunk in enumerate(chunks):
            chunk_id = chunk.get('chunk_id', f'chunk_{idx}')

            # Check required fields
            for field in self.REQUIRED_CHUNK_FIELDS:
                if field not in chunk:
                    failures.append(f"{chunk_id}: Missing required field '{field}'")

            # Check chunk text length
            text = chunk.get('text', '')
            if len(text) < self.MIN_CHUNK_LENGTH:
                failures.append(f"{chunk_id}: Text too short: {len(text)} < {self.MIN_CHUNK_LENGTH}")
            elif len(text) > self.MAX_CHUNK_LENGTH:
                warnings.append(f"{chunk_id}: Text very long: {len(text)} > {self.MAX_CHUNK_LENGTH}")

            # Check quality scores
            strategic_score = chunk.get('strategic_importance', 0)
            if strategic_score < self.MIN_STRATEGIC_SCORE:
                warnings.append(f"{chunk_id}: Low strategic importance: {strategic_score}")

            quality_score = chunk.get('quality_score', 0)
            if quality_score < self.MIN_QUALITY_SCORE:
                warnings.append(f"{chunk_id}: Low quality score: {quality_score}")

        return {
            "passed": len(failures) == 0,
            "failures": failures,
            "warnings": warnings,
            "chunk_count": len(chunks),
        }

    def validate_output_compatibility(self, output: dict[str, Any]) -> dict[str, Any]:
        """
        Validate output structure for compatibility with downstream phases.

        Ensures the phase-one output can be consumed by next phases in the flux.

        Args:
            output: Phase-one output dictionary

        Returns:
            Dictionary with validation results
        """
        failures = []

        # Check required top-level keys
        if 'chunks' not in output:
            failures.append("Missing 'chunks' in output")

        if 'metadata' not in output:
            failures.append("Missing 'metadata' in output")
        else:
            # Validate metadata fields
            metadata = output['metadata']
            for field in self.REQUIRED_METADATA_FIELDS:
                if field not in metadata:
                    failures.append(f"Missing required metadata field: '{field}'")

        # Check chunks structure
        if 'chunks' in output:
            chunks_result = self.validate_chunks(output['chunks'])
            if not chunks_result['passed']:
                failures.extend(chunks_result['failures'])

        return {
            "passed": len(failures) == 0,
            "failures": failures,
        }

    def validate_quality_metrics(self, quality_metrics: Any) -> dict[str, Any]:
        """
        Validate quality metrics from CanonPolicyPackage against MAXIMUM STANDARDS.

        Enforces strict thresholds per README specifications. No degradation tolerated.

        Args:
            quality_metrics: QualityMetrics instance from CanonPolicyPackage

        Returns:
            Dictionary with validation results:
            {
                "passed": bool,
                "failures": List[str],  # CRITICAL failures that MUST be fixed
                "warnings": List[str],  # Non-critical warnings
                "metrics": Dict[str, float]  # Actual metric values
            }
        """
        failures = []
        warnings = []
        metrics_dict = {}

        # Extract metrics (handle both object and dict)
        if hasattr(quality_metrics, '__dict__'):
            # It's an object
            provenance_completeness = getattr(quality_metrics, 'provenance_completeness', 0.0)
            structural_consistency = getattr(quality_metrics, 'structural_consistency', 0.0)
            boundary_f1 = getattr(quality_metrics, 'boundary_f1', 0.0)
            budget_consistency = getattr(quality_metrics, 'budget_consistency_score', 0.0)
            temporal_robustness = getattr(quality_metrics, 'temporal_robustness', 0.0)
            chunk_context_coverage = getattr(quality_metrics, 'chunk_context_coverage', 0.0)
        else:
            # It's a dict
            provenance_completeness = quality_metrics.get('provenance_completeness', 0.0)
            structural_consistency = quality_metrics.get('structural_consistency', 0.0)
            boundary_f1 = quality_metrics.get('boundary_f1', 0.0)
            budget_consistency = quality_metrics.get('budget_consistency_score', 0.0)
            temporal_robustness = quality_metrics.get('temporal_robustness', 0.0)
            chunk_context_coverage = quality_metrics.get('chunk_context_coverage', 0.0)

        # Store actual values
        metrics_dict = {
            'provenance_completeness': provenance_completeness,
            'structural_consistency': structural_consistency,
            'boundary_f1': boundary_f1,
            'budget_consistency_score': budget_consistency,
            'temporal_robustness': temporal_robustness,
            'chunk_context_coverage': chunk_context_coverage,
        }

        # CRITICAL: Provenance completeness MUST be 100%
        if provenance_completeness < self.MIN_PROVENANCE_COMPLETENESS:
            failures.append(
                f"🔴 CRITICAL: Provenance completeness below threshold: "
                f"{provenance_completeness:.2%} < {self.MIN_PROVENANCE_COMPLETENESS:.0%}. "
                f"Every token must be traceable to source (README requirement)."
            )
            logger.error(
                f"Provenance completeness FAILED: {provenance_completeness:.2%} "
                f"(required: {self.MIN_PROVENANCE_COMPLETENESS:.0%})"
            )

        # CRITICAL: Structural consistency MUST be perfect
        if structural_consistency < self.MIN_STRUCTURAL_CONSISTENCY:
            failures.append(
                f"🔴 CRITICAL: Structural consistency below threshold: "
                f"{structural_consistency:.2%} < {self.MIN_STRUCTURAL_CONSISTENCY:.0%}. "
                f"Policy structure must be perfectly parsed (FASE 3 gate)."
            )
            logger.error(
                f"Structural consistency FAILED: {structural_consistency:.2%} "
                f"(required: {self.MIN_STRUCTURAL_CONSISTENCY:.0%})"
            )

        # HIGH: Boundary F1 for chunk quality
        if boundary_f1 < self.MIN_BOUNDARY_F1:
            failures.append(
                f"🔴 HIGH: Boundary F1 below threshold: "
                f"{boundary_f1:.2f} < {self.MIN_BOUNDARY_F1}. "
                f"Chunk boundaries are not accurate enough (FASE 8 gate)."
            )
            logger.error(
                f"Boundary F1 FAILED: {boundary_f1:.2f} "
                f"(required: {self.MIN_BOUNDARY_F1})"
            )

        # HIGH: Budget consistency for financial data
        if budget_consistency < self.MIN_BUDGET_CONSISTENCY:
            warnings.append(
                f"🟡 Budget consistency below threshold: "
                f"{budget_consistency:.2%} < {self.MIN_BUDGET_CONSISTENCY:.0%}. "
                f"Budget data may have inconsistencies (FASE 6 gate)."
            )
            logger.warning(
                f"Budget consistency WARNING: {budget_consistency:.2%} "
                f"(recommended: {self.MIN_BUDGET_CONSISTENCY:.0%})"
            )

        # MEDIUM: Temporal robustness
        if temporal_robustness < self.MIN_TEMPORAL_ROBUSTNESS:
            warnings.append(
                f"🟡 Temporal robustness below threshold: "
                f"{temporal_robustness:.2%} < {self.MIN_TEMPORAL_ROBUSTNESS:.0%}. "
                f"Temporal data may be incomplete."
            )

        # INFO: Chunk context coverage
        if chunk_context_coverage < 0.5:
            warnings.append(
                f"ℹ️ Low chunk context coverage: {chunk_context_coverage:.2%}. "
                f"Few inter-chunk relationships detected."
            )

        # Summary logging
        if failures:
            logger.error(f"Quality metrics validation FAILED with {len(failures)} critical issues")
        elif warnings:
            logger.warning(f"Quality metrics validation PASSED with {len(warnings)} warnings")
        else:
            logger.info("Quality metrics validation PASSED - All thresholds met")

        return {
            "passed": len(failures) == 0,
            "failures": failures,
            "warnings": warnings,
            "metrics": metrics_dict,
        }


# Legacy alias for backwards compatibility
class QualityGates(SPCQualityGates):
    """Legacy alias for SPCQualityGates."""
    pass
