"""
Quality gates for SPC (Smart Policy Chunks) validation - Canonical Phase-One.

Validates quality metrics, enforces invariants, and ensures compatibility
with downstream phases in the canonical pipeline flux.
"""

from typing import Any, Dict, List
from pathlib import Path


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
    
    def validate_input(self, document_path: Path) -> Dict[str, Any]:
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
    
    def validate_chunks(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
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
    
    def validate_output_compatibility(self, output: Dict[str, Any]) -> Dict[str, Any]:
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


# Legacy alias for backwards compatibility
class QualityGates(SPCQualityGates):
    """Legacy alias for SPCQualityGates."""
    pass
