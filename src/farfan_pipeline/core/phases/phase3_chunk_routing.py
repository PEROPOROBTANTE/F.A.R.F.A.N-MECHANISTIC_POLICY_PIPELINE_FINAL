"""
Phase 3: Chunk Routing
======================

This module implements Phase 3 of the F.A.R.F.A.N pipeline, which routes
questions to their corresponding policy area and dimension chunks.

Phase Structure:
----------------
Phase 3 follows the established hierarchical structure:

1. Sequential Dependency Root (Input Extraction):
   - Extract questions from Phase 2 result
   - Extract chunk matrix from PreprocessedDocument
   - Validate input contracts

2. Validation Stage:
   - Verify question structure (policy_area_id, dimension_id presence)
   - Verify chunk matrix completeness (60 chunks, PA×DIM coverage)
   - Validate lookup key formats

3. Transformation Stage:
   - Convert question dimension to DIM_ID format (D1 → DIM01)
   - Construct lookup keys (policy_area_id, dimension_id)
   - Perform chunk routing via matrix lookup

4. Error Conditions (Leaf Nodes):
   - Missing policy_area_id or dimension_id in question → ValueError
   - Chunk not found for (PA, DIM) key → ValueError with descriptive message
   - Chunk metadata mismatch → ValueError

5. Observability:
   - Log routing outcomes (match counts)
   - Log policy area distribution
   - Record routing failures

Design Principles:
------------------
- **Strict Equality Enforcement**: policy_area_id and dimension_id must match exactly
- **Complete Field Population**: All 7 canonical ChunkRoutingResult fields populated
- **Descriptive Errors**: ValueError exceptions identify question and failure reason
- **No Task Creep**: Focus solely on core routing correctness
- **Deterministic**: Same inputs produce same routing outcomes

Author: F.A.R.F.A.N Architecture Team
Date: 2025-01-22
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from farfan_pipeline.core.phases.phase_protocol import (
    ContractValidationResult,
    PhaseContract,
)
from farfan_pipeline.core.types import ChunkData, PreprocessedDocument

logger = logging.getLogger(__name__)


@dataclass
class ChunkRoutingResult:
    """Result of routing a single question to its target chunk.
    
    This dataclass contains all seven canonical fields required for
    Phase 3 chunk routing verification.
    """
    
    target_chunk: ChunkData
    chunk_id: str
    policy_area_id: str
    dimension_id: str
    text_content: str
    expected_elements: list[dict[str, Any]]
    document_position: tuple[int, int] | None
    
    def __post_init__(self) -> None:
        """Validate that all required fields are properly populated."""
        if self.target_chunk is None:
            raise ValueError("target_chunk cannot be None")
        if not self.chunk_id:
            raise ValueError("chunk_id cannot be empty")
        if not self.policy_area_id:
            raise ValueError("policy_area_id cannot be empty")
        if not self.dimension_id:
            raise ValueError("dimension_id cannot be empty")
        if not self.text_content:
            raise ValueError("text_content cannot be empty")
        if self.expected_elements is None:
            raise ValueError("expected_elements cannot be None (use empty list [])")


@dataclass
class Phase3Input:
    """Input contract for Phase 3: chunk routing.
    
    Contains the preprocessed document with chunk matrix and
    the questions from Phase 2 that need routing.
    """
    
    preprocessed_document: PreprocessedDocument
    questions: list[dict[str, Any]]


@dataclass
class Phase3Result:
    """Output contract for Phase 3: chunk routing results.
    
    Contains routing results for all questions and observability metrics.
    """
    
    routing_results: list[ChunkRoutingResult]
    total_questions: int
    successful_routes: int
    failed_routes: int
    policy_area_distribution: dict[str, int] = field(default_factory=dict)
    dimension_distribution: dict[str, int] = field(default_factory=dict)
    routing_errors: list[str] = field(default_factory=list)


class Phase3ChunkRoutingContract(PhaseContract[Phase3Input, Phase3Result]):
    """
    Phase 3 Contract: Chunk Routing with Strict PA×DIM Enforcement.
    
    This phase routes each question to its corresponding chunk in the
    60-chunk PA×DIM matrix, enforcing strict equality between question
    and chunk identifiers.
    """
    
    def __init__(self):
        """Initialize Phase 3 contract with validation invariants."""
        super().__init__("phase3_chunk_routing")
        
        # Add invariants for Phase 3
        self.add_invariant(
            name="routing_completeness",
            description="All questions must be either successfully routed or have an error recorded",
            check=lambda result: result.successful_routes + result.failed_routes == result.total_questions,
            error_message="Routing count mismatch: some questions were neither routed nor recorded as failures"
        )
        
        self.add_invariant(
            name="routing_results_match_success",
            description="Number of routing results must match successful routes",
            check=lambda result: len(result.routing_results) == result.successful_routes,
            error_message="Routing results count does not match successful_routes count"
        )
        
        self.add_invariant(
            name="policy_area_distribution_sum",
            description="Policy area distribution must sum to successful routes",
            check=lambda result: sum(result.policy_area_distribution.values()) == result.successful_routes,
            error_message="Policy area distribution counts do not sum to successful_routes"
        )
    
    def validate_input(self, input_data: Any) -> ContractValidationResult:
        """Validate Phase 3 input contract.
        
        Args:
            input_data: Input to validate (should be Phase3Input)
            
        Returns:
            ContractValidationResult with validation status
        """
        errors = []
        warnings = []
        
        if not isinstance(input_data, Phase3Input):
            errors.append(f"Input must be Phase3Input, got {type(input_data).__name__}")
            return ContractValidationResult(
                passed=False,
                contract_type="input",
                phase_name=self.phase_name,
                errors=errors
            )
        
        # Validate preprocessed document
        if not isinstance(input_data.preprocessed_document, PreprocessedDocument):
            errors.append("preprocessed_document must be PreprocessedDocument instance")
        
        if not input_data.preprocessed_document.chunks:
            errors.append("preprocessed_document.chunks cannot be empty")
        
        chunk_count = len(input_data.preprocessed_document.chunks)
        if chunk_count != 60:
            warnings.append(f"Expected 60 chunks, found {chunk_count}")
        
        # Validate questions list
        if not isinstance(input_data.questions, list):
            errors.append("questions must be a list")
        
        if not input_data.questions:
            errors.append("questions list cannot be empty")
        
        # Validate question structure
        for idx, question in enumerate(input_data.questions[:5]):  # Sample first 5
            if not isinstance(question, dict):
                errors.append(f"Question {idx} must be a dict")
                continue
            
            if "policy_area_id" not in question:
                errors.append(f"Question {idx} missing policy_area_id")
            
            if "dimension_id" not in question:
                errors.append(f"Question {idx} missing dimension_id")
        
        passed = len(errors) == 0
        
        return ContractValidationResult(
            passed=passed,
            contract_type="input",
            phase_name=self.phase_name,
            errors=errors,
            warnings=warnings
        )
    
    def validate_output(self, output_data: Any) -> ContractValidationResult:
        """Validate Phase 3 output contract.
        
        Args:
            output_data: Output to validate (should be Phase3Result)
            
        Returns:
            ContractValidationResult with validation status
        """
        errors = []
        warnings = []
        
        if not isinstance(output_data, Phase3Result):
            errors.append(f"Output must be Phase3Result, got {type(output_data).__name__}")
            return ContractValidationResult(
                passed=False,
                contract_type="output",
                phase_name=self.phase_name,
                errors=errors
            )
        
        # Validate routing results structure
        if not isinstance(output_data.routing_results, list):
            errors.append("routing_results must be a list")
        
        # Validate counts
        if output_data.total_questions < 0:
            errors.append("total_questions cannot be negative")
        
        if output_data.successful_routes < 0:
            errors.append("successful_routes cannot be negative")
        
        if output_data.failed_routes < 0:
            errors.append("failed_routes cannot be negative")
        
        # Validate routing result objects
        for idx, result in enumerate(output_data.routing_results[:5]):  # Sample first 5
            if not isinstance(result, ChunkRoutingResult):
                errors.append(f"routing_results[{idx}] must be ChunkRoutingResult")
                continue
            
            if not result.chunk_id:
                errors.append(f"routing_results[{idx}] has empty chunk_id")
            
            if not result.policy_area_id:
                errors.append(f"routing_results[{idx}] has empty policy_area_id")
            
            if not result.dimension_id:
                errors.append(f"routing_results[{idx}] has empty dimension_id")
        
        # Check for failures
        if output_data.failed_routes > 0:
            warnings.append(f"{output_data.failed_routes} questions failed routing")
        
        passed = len(errors) == 0
        
        return ContractValidationResult(
            passed=passed,
            contract_type="output",
            phase_name=self.phase_name,
            errors=errors,
            warnings=warnings
        )
    
    async def execute(self, input_data: Phase3Input) -> Phase3Result:
        """Execute Phase 3: chunk routing logic.
        
        Routes each question to its corresponding chunk by matching
        policy_area_id and dimension_id between the question and the
        chunk matrix.
        
        Args:
            input_data: Phase3Input with preprocessed document and questions
            
        Returns:
            Phase3Result with routing outcomes and observability metrics
            
        Raises:
            ValueError: If routing logic encounters invalid data
        """
        logger.info("=" * 70)
        logger.info("PHASE 3: Chunk Routing - Starting Execution")
        logger.info("=" * 70)
        
        # Stage 1: Input Extraction (Sequential Dependency Root)
        logger.info("Stage 1: Extracting inputs")
        preprocessed_doc = input_data.preprocessed_document
        questions = input_data.questions
        
        logger.info(f"Loaded {len(questions)} questions")
        logger.info(f"Loaded {len(preprocessed_doc.chunks)} chunks")
        
        # Stage 2: Validation
        logger.info("Stage 2: Validating chunk matrix")
        chunk_matrix = self._build_chunk_matrix(preprocessed_doc)
        logger.info(f"Built chunk matrix with {len(chunk_matrix)} entries")
        
        # Stage 3: Transformation (Routing)
        logger.info("Stage 3: Performing chunk routing")
        routing_results: list[ChunkRoutingResult] = []
        routing_errors: list[str] = []
        policy_area_dist: dict[str, int] = {}
        dimension_dist: dict[str, int] = {}
        
        for question in questions:
            try:
                routing_result = self._route_question_to_chunk(
                    question=question,
                    chunk_matrix=chunk_matrix
                )
                routing_results.append(routing_result)
                
                # Update distributions
                pa_id = routing_result.policy_area_id
                dim_id = routing_result.dimension_id
                policy_area_dist[pa_id] = policy_area_dist.get(pa_id, 0) + 1
                dimension_dist[dim_id] = dimension_dist.get(dim_id, 0) + 1
                
            except ValueError as e:
                # Stage 4: Error Conditions (Leaf Nodes)
                error_msg = str(e)
                routing_errors.append(error_msg)
                logger.error(f"Routing failed: {error_msg}")
        
        # Stage 5: Observability
        successful_routes = len(routing_results)
        failed_routes = len(routing_errors)
        total_questions = len(questions)
        
        logger.info("=" * 70)
        logger.info("PHASE 3: Chunk Routing - Execution Complete")
        logger.info(f"Total Questions: {total_questions}")
        logger.info(f"Successful Routes: {successful_routes}")
        logger.info(f"Failed Routes: {failed_routes}")
        logger.info("Policy Area Distribution:")
        for pa_id in sorted(policy_area_dist.keys()):
            logger.info(f"  {pa_id}: {policy_area_dist[pa_id]} questions")
        logger.info("Dimension Distribution:")
        for dim_id in sorted(dimension_dist.keys()):
            logger.info(f"  {dim_id}: {dimension_dist[dim_id]} questions")
        logger.info("=" * 70)
        
        return Phase3Result(
            routing_results=routing_results,
            total_questions=total_questions,
            successful_routes=successful_routes,
            failed_routes=failed_routes,
            policy_area_distribution=policy_area_dist,
            dimension_distribution=dimension_dist,
            routing_errors=routing_errors
        )
    
    def _build_chunk_matrix(
        self, 
        preprocessed_doc: PreprocessedDocument
    ) -> dict[tuple[str, str], ChunkData]:
        """Build chunk matrix keyed by (policy_area_id, dimension_id).
        
        Args:
            preprocessed_doc: PreprocessedDocument with chunks
            
        Returns:
            Dictionary mapping (PA, DIM) tuples to ChunkData
            
        Raises:
            ValueError: If chunk matrix is invalid
        """
        chunk_matrix: dict[tuple[str, str], ChunkData] = {}
        
        for chunk in preprocessed_doc.chunks:
            if chunk.policy_area_id is None:
                raise ValueError(
                    f"Chunk {chunk.id} has null policy_area_id"
                )
            
            if chunk.dimension_id is None:
                raise ValueError(
                    f"Chunk {chunk.id} has null dimension_id"
                )
            
            key = (chunk.policy_area_id, chunk.dimension_id)
            
            if key in chunk_matrix:
                raise ValueError(
                    f"Duplicate chunk for {chunk.policy_area_id}-{chunk.dimension_id}"
                )
            
            chunk_matrix[key] = chunk
        
        # Validate we have 60 chunks (10 PA × 6 DIM)
        if len(chunk_matrix) != 60:
            raise ValueError(
                f"Expected 60 chunks in matrix, found {len(chunk_matrix)}"
            )
        
        return chunk_matrix
    
    def _route_question_to_chunk(
        self,
        question: dict[str, Any],
        chunk_matrix: dict[tuple[str, str], ChunkData]
    ) -> ChunkRoutingResult:
        """Route a single question to its corresponding chunk.
        
        This method implements the core routing logic with strict
        policy_area_id and dimension_id equality enforcement.
        
        Args:
            question: Question dictionary with policy_area_id and dimension_id
            chunk_matrix: Matrix of chunks keyed by (PA, DIM)
            
        Returns:
            ChunkRoutingResult with all seven canonical fields populated
            
        Raises:
            ValueError: If question is missing required fields or no matching chunk found
        """
        # Extract question identifiers
        question_id = question.get("question_id", "UNKNOWN")
        policy_area_id = question.get("policy_area_id")
        dimension_id = question.get("dimension_id")
        
        # Validate question has required fields
        if policy_area_id is None:
            raise ValueError(
                f"Question {question_id} missing required field 'policy_area_id'"
            )
        
        if dimension_id is None:
            raise ValueError(
                f"Question {question_id} missing required field 'dimension_id'"
            )
        
        # Convert dimension format if needed (D1 → DIM01)
        if isinstance(dimension_id, str) and dimension_id.startswith("D") and not dimension_id.startswith("DIM"):
            # Extract number from D1, D2, etc.
            try:
                dim_num = int(dimension_id[1:])
                dimension_id = f"DIM{dim_num:02d}"
            except (ValueError, IndexError):
                raise ValueError(
                    f"Question {question_id} has invalid dimension_id format: {dimension_id}"
                )
        
        # Construct lookup key
        lookup_key = (policy_area_id, dimension_id)
        
        # Perform chunk lookup
        if lookup_key not in chunk_matrix:
            raise ValueError(
                f"Question {question_id} routing failed: "
                f"No matching chunk found for policy_area_id={policy_area_id}, "
                f"dimension_id={dimension_id}. "
                f"Required chunk {policy_area_id}-{dimension_id} is missing from the chunk matrix."
            )
        
        target_chunk = chunk_matrix[lookup_key]
        
        # Verify strict equality between question and chunk identifiers
        if target_chunk.policy_area_id != policy_area_id:
            raise ValueError(
                f"Question {question_id} routing verification failed: "
                f"Chunk policy_area_id mismatch. "
                f"Question expects {policy_area_id}, chunk has {target_chunk.policy_area_id}"
            )
        
        if target_chunk.dimension_id != dimension_id:
            raise ValueError(
                f"Question {question_id} routing verification failed: "
                f"Chunk dimension_id mismatch. "
                f"Question expects {dimension_id}, chunk has {target_chunk.dimension_id}"
            )
        
        # Extract chunk_id (guaranteed to be present after validation)
        chunk_id = target_chunk.chunk_id or f"{policy_area_id}-{dimension_id}"
        
        # Extract text content
        text_content = target_chunk.text
        
        # Extract expected_elements (ensure it's never None)
        expected_elements = target_chunk.expected_elements or []
        
        # Extract document_position (can be None)
        document_position = target_chunk.document_position
        
        # Construct and return ChunkRoutingResult with all 7 canonical fields
        return ChunkRoutingResult(
            target_chunk=target_chunk,
            chunk_id=chunk_id,
            policy_area_id=policy_area_id,
            dimension_id=dimension_id,
            text_content=text_content,
            expected_elements=expected_elements,
            document_position=document_position
        )


__all__ = [
    "ChunkRoutingResult",
    "Phase3Input",
    "Phase3Result",
    "Phase3ChunkRoutingContract",
]
