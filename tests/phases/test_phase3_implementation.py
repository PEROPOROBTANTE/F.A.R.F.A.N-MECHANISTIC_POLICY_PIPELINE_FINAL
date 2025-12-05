"""
Test Phase 3: Chunk Routing Implementation

This test file verifies the Phase 3 implementation against the specification,
including:
- Routing logic with strict PA-DIM enforcement
- ChunkRoutingResult construction with all 7 canonical fields
- ValueError exceptions with descriptive messages
- Phase specification hierarchical structure compliance
- Observability logging without task creep
"""

import pytest
from dataclasses import replace

from farfan_pipeline.core.phases.phase3_chunk_routing import (
    ChunkRoutingResult,
    Phase3ChunkRoutingContract,
    Phase3Input,
    Phase3Result,
)
from farfan_pipeline.core.types import ChunkData, PreprocessedDocument, Provenance


class TestChunkRoutingResultConstruction:
    """Test ChunkRoutingResult construction with all 7 canonical fields."""
    
    def test_all_seven_fields_present(self):
        """Test that ChunkRoutingResult has exactly 7 canonical fields."""
        chunk = ChunkData(
            id=0,
            text="Test chunk content",
            chunk_type="diagnostic",
            sentences=[0, 1],
            tables=[],
            start_pos=0,
            end_pos=100,
            confidence=0.95,
            chunk_id="PA01-DIM01",
            policy_area_id="PA01",
            dimension_id="DIM01",
            provenance=Provenance(page_number=1),
        )
        
        result = ChunkRoutingResult(
            target_chunk=chunk,
            chunk_id="PA01-DIM01",
            policy_area_id="PA01",
            dimension_id="DIM01",
            text_content="Test chunk content",
            expected_elements=[],
            document_position=(0, 100)
        )
        
        # Verify all 7 fields exist
        assert result.target_chunk is not None
        assert result.chunk_id == "PA01-DIM01"
        assert result.policy_area_id == "PA01"
        assert result.dimension_id == "DIM01"
        assert result.text_content == "Test chunk content"
        assert result.expected_elements == []
        assert result.document_position == (0, 100)
    
    def test_target_chunk_none_raises_error(self):
        """Test that None target_chunk raises ValueError."""
        with pytest.raises(ValueError, match="target_chunk cannot be None"):
            ChunkRoutingResult(
                target_chunk=None,
                chunk_id="PA01-DIM01",
                policy_area_id="PA01",
                dimension_id="DIM01",
                text_content="Test",
                expected_elements=[],
                document_position=None
            )
    
    def test_chunk_id_empty_raises_error(self):
        """Test that empty chunk_id raises ValueError."""
        chunk = ChunkData(
            id=0,
            text="Test",
            chunk_type="diagnostic",
            sentences=[],
            tables=[],
            start_pos=0,
            end_pos=10,
            confidence=0.9,
            policy_area_id="PA01",
            dimension_id="DIM01",
        )
        
        with pytest.raises(ValueError, match="chunk_id cannot be empty"):
            ChunkRoutingResult(
                target_chunk=chunk,
                chunk_id="",
                policy_area_id="PA01",
                dimension_id="DIM01",
                text_content="Test",
                expected_elements=[],
                document_position=None
            )
    
    def test_expected_elements_none_raises_error(self):
        """Test that None expected_elements raises ValueError."""
        chunk = ChunkData(
            id=0,
            text="Test",
            chunk_type="diagnostic",
            sentences=[],
            tables=[],
            start_pos=0,
            end_pos=10,
            confidence=0.9,
            policy_area_id="PA01",
            dimension_id="DIM01",
        )
        
        with pytest.raises(ValueError, match="expected_elements cannot be None"):
            ChunkRoutingResult(
                target_chunk=chunk,
                chunk_id="PA01-DIM01",
                policy_area_id="PA01",
                dimension_id="DIM01",
                text_content="Test",
                expected_elements=None,
                document_position=None
            )
    
    def test_document_position_can_be_none(self):
        """Test that document_position can be None."""
        chunk = ChunkData(
            id=0,
            text="Test",
            chunk_type="diagnostic",
            sentences=[],
            tables=[],
            start_pos=0,
            end_pos=10,
            confidence=0.9,
            policy_area_id="PA01",
            dimension_id="DIM01",
        )
        
        result = ChunkRoutingResult(
            target_chunk=chunk,
            chunk_id="PA01-DIM01",
            policy_area_id="PA01",
            dimension_id="DIM01",
            text_content="Test",
            expected_elements=[],
            document_position=None
        )
        
        assert result.document_position is None


class TestStrictEqualityEnforcement:
    """Test strict policy_area_id and dimension_id equality enforcement."""
    
    @pytest.fixture
    def phase3_contract(self):
        """Create Phase 3 contract instance."""
        return Phase3ChunkRoutingContract()
    
    @pytest.fixture
    def preprocessed_doc_with_chunks(self):
        """Create preprocessed document with 60 chunks."""
        chunks = []
        for pa_num in range(1, 11):
            for dim_num in range(1, 7):
                pa_id = f"PA{pa_num:02d}"
                dim_id = f"DIM{dim_num:02d}"
                chunk = ChunkData(
                    id=len(chunks),
                    text=f"Content for {pa_id} {dim_id}",
                    chunk_type="diagnostic",
                    sentences=[len(chunks)],
                    tables=[],
                    start_pos=len(chunks) * 100,
                    end_pos=(len(chunks) + 1) * 100,
                    confidence=0.95,
                    chunk_id=f"{pa_id}-{dim_id}",
                    policy_area_id=pa_id,
                    dimension_id=dim_id,
                )
                chunks.append(chunk)
        
        return PreprocessedDocument(
            document_id="test_doc",
            raw_text="Test document",
            sentences=[{"text": f"Sentence {i}"} for i in range(60)],
            tables=[],
            metadata={"chunk_count": 60},
            chunks=chunks,
            processing_mode="chunked",
        )
    
    @pytest.mark.asyncio
    async def test_exact_match_succeeds(self, phase3_contract, preprocessed_doc_with_chunks):
        """Test that exact PA and DIM match succeeds."""
        questions = [
            {
                "question_id": "Q001",
                "policy_area_id": "PA01",
                "dimension_id": "DIM01"
            }
        ]
        
        phase3_input = Phase3Input(
            preprocessed_document=preprocessed_doc_with_chunks,
            questions=questions
        )
        
        result = await phase3_contract.execute(phase3_input)
        
        assert result.successful_routes == 1
        assert result.failed_routes == 0
        assert len(result.routing_results) == 1
        
        routing_result = result.routing_results[0]
        assert routing_result.policy_area_id == "PA01"
        assert routing_result.dimension_id == "DIM01"
    
    @pytest.mark.asyncio
    async def test_dimension_format_normalization(self, phase3_contract, preprocessed_doc_with_chunks):
        """Test that D1 format is normalized to DIM01."""
        questions = [
            {
                "question_id": "Q001",
                "policy_area_id": "PA01",
                "dimension_id": "D1"  # Should be normalized to DIM01
            }
        ]
        
        phase3_input = Phase3Input(
            preprocessed_document=preprocessed_doc_with_chunks,
            questions=questions
        )
        
        result = await phase3_contract.execute(phase3_input)
        
        assert result.successful_routes == 1
        routing_result = result.routing_results[0]
        assert routing_result.dimension_id == "DIM01"


class TestRoutingFailures:
    """Test routing failures raise ValueError with descriptive messages."""
    
    @pytest.fixture
    def phase3_contract(self):
        """Create Phase 3 contract instance."""
        return Phase3ChunkRoutingContract()
    
    @pytest.fixture
    def preprocessed_doc_incomplete(self):
        """Create document with missing chunks."""
        chunks = []
        # Only create 59 chunks (missing PA10-DIM06)
        for pa_num in range(1, 11):
            for dim_num in range(1, 7):
                if pa_num == 10 and dim_num == 6:
                    continue  # Skip PA10-DIM06
                pa_id = f"PA{pa_num:02d}"
                dim_id = f"DIM{dim_num:02d}"
                chunk = ChunkData(
                    id=len(chunks),
                    text=f"Content for {pa_id} {dim_id}",
                    chunk_type="diagnostic",
                    sentences=[],
                    tables=[],
                    start_pos=0,
                    end_pos=100,
                    confidence=0.95,
                    chunk_id=f"{pa_id}-{dim_id}",
                    policy_area_id=pa_id,
                    dimension_id=dim_id,
                )
                chunks.append(chunk)
        
        return PreprocessedDocument(
            document_id="incomplete",
            raw_text="Test",
            sentences=[],
            tables=[],
            metadata={"chunk_count": 59},
            chunks=chunks,
            processing_mode="chunked",
        )
    
    @pytest.mark.asyncio
    async def test_missing_chunk_records_error(self, phase3_contract, preprocessed_doc_incomplete):
        """Test that missing chunk is recorded as routing error."""
        questions = [
            {
                "question_id": "Q300",
                "policy_area_id": "PA10",
                "dimension_id": "DIM06"
            }
        ]
        
        # This should fail during chunk matrix validation
        phase3_input = Phase3Input(
            preprocessed_document=preprocessed_doc_incomplete,
            questions=questions
        )
        
        # The execution should fail during matrix construction
        with pytest.raises(ValueError, match="Expected 60 chunks"):
            await phase3_contract.execute(phase3_input)
    
    @pytest.mark.asyncio
    async def test_missing_policy_area_id_raises_error(self, phase3_contract):
        """Test that missing policy_area_id raises descriptive error."""
        chunks = []
        for pa_num in range(1, 11):
            for dim_num in range(1, 7):
                pa_id = f"PA{pa_num:02d}"
                dim_id = f"DIM{dim_num:02d}"
                chunk = ChunkData(
                    id=len(chunks),
                    text=f"Content for {pa_id} {dim_id}",
                    chunk_type="diagnostic",
                    sentences=[],
                    tables=[],
                    start_pos=0,
                    end_pos=100,
                    confidence=0.95,
                    chunk_id=f"{pa_id}-{dim_id}",
                    policy_area_id=pa_id,
                    dimension_id=dim_id,
                )
                chunks.append(chunk)
        
        doc = PreprocessedDocument(
            document_id="test",
            raw_text="Test",
            sentences=[],
            tables=[],
            metadata={"chunk_count": 60},
            chunks=chunks,
            processing_mode="chunked",
        )
        
        questions = [
            {
                "question_id": "Q001",
                # Missing policy_area_id
                "dimension_id": "DIM01"
            }
        ]
        
        phase3_input = Phase3Input(preprocessed_document=doc, questions=questions)
        result = await phase3_contract.execute(phase3_input)
        
        assert result.failed_routes == 1
        assert len(result.routing_errors) == 1
        assert "missing required field 'policy_area_id'" in result.routing_errors[0]
        assert "Q001" in result.routing_errors[0]


class TestPhaseSpecificationCompliance:
    """Test compliance with phase specification hierarchical structure."""
    
    @pytest.fixture
    def phase3_contract(self):
        """Create Phase 3 contract instance."""
        return Phase3ChunkRoutingContract()
    
    def test_phase_has_correct_name(self, phase3_contract):
        """Test phase has correct canonical name."""
        assert phase3_contract.phase_name == "phase3_chunk_routing"
    
    def test_phase_has_invariants(self, phase3_contract):
        """Test phase defines required invariants."""
        assert len(phase3_contract.invariants) >= 3
        
        invariant_names = [inv.name for inv in phase3_contract.invariants]
        assert "routing_completeness" in invariant_names
        assert "routing_results_match_success" in invariant_names
        assert "policy_area_distribution_sum" in invariant_names
    
    @pytest.mark.asyncio
    async def test_input_validation_stage(self, phase3_contract):
        """Test Stage 1: Input validation catches structural errors."""
        # Invalid input type
        validation = phase3_contract.validate_input("not_a_phase3_input")
        assert not validation.passed
        assert len(validation.errors) > 0
    
    @pytest.mark.asyncio
    async def test_output_validation_stage(self, phase3_contract):
        """Test output validation enforces contract."""
        # Invalid output type
        validation = phase3_contract.validate_output("not_a_phase3_result")
        assert not validation.passed
        assert len(validation.errors) > 0


class TestObservabilityLogging:
    """Test observability logging without task creep."""
    
    @pytest.fixture
    def phase3_contract(self):
        """Create Phase 3 contract instance."""
        return Phase3ChunkRoutingContract()
    
    @pytest.fixture
    def complete_document(self):
        """Create complete 60-chunk document."""
        chunks = []
        for pa_num in range(1, 11):
            for dim_num in range(1, 7):
                pa_id = f"PA{pa_num:02d}"
                dim_id = f"DIM{dim_num:02d}"
                chunk = ChunkData(
                    id=len(chunks),
                    text=f"Content for {pa_id} {dim_id}",
                    chunk_type="diagnostic",
                    sentences=[],
                    tables=[],
                    start_pos=0,
                    end_pos=100,
                    confidence=0.95,
                    chunk_id=f"{pa_id}-{dim_id}",
                    policy_area_id=pa_id,
                    dimension_id=dim_id,
                )
                chunks.append(chunk)
        
        return PreprocessedDocument(
            document_id="complete",
            raw_text="Test",
            sentences=[],
            tables=[],
            metadata={"chunk_count": 60},
            chunks=chunks,
            processing_mode="chunked",
        )
    
    @pytest.mark.asyncio
    async def test_routing_outcomes_recorded(self, phase3_contract, complete_document):
        """Test that routing outcomes are recorded."""
        questions = [
            {"question_id": f"Q{i:03d}", "policy_area_id": f"PA{(i % 10) + 1:02d}", 
             "dimension_id": f"DIM{(i % 6) + 1:02d}"}
            for i in range(30)
        ]
        
        phase3_input = Phase3Input(
            preprocessed_document=complete_document,
            questions=questions
        )
        
        result = await phase3_contract.execute(phase3_input)
        
        # Verify outcomes are recorded
        assert result.total_questions == 30
        assert result.successful_routes + result.failed_routes == result.total_questions
    
    @pytest.mark.asyncio
    async def test_policy_area_distribution_recorded(self, phase3_contract, complete_document):
        """Test that policy area distribution is recorded."""
        questions = [
            {"question_id": "Q001", "policy_area_id": "PA01", "dimension_id": "DIM01"},
            {"question_id": "Q002", "policy_area_id": "PA01", "dimension_id": "DIM02"},
            {"question_id": "Q003", "policy_area_id": "PA02", "dimension_id": "DIM01"},
        ]
        
        phase3_input = Phase3Input(
            preprocessed_document=complete_document,
            questions=questions
        )
        
        result = await phase3_contract.execute(phase3_input)
        
        # Verify PA distribution
        assert result.policy_area_distribution["PA01"] == 2
        assert result.policy_area_distribution["PA02"] == 1
    
    @pytest.mark.asyncio
    async def test_dimension_distribution_recorded(self, phase3_contract, complete_document):
        """Test that dimension distribution is recorded."""
        questions = [
            {"question_id": "Q001", "policy_area_id": "PA01", "dimension_id": "DIM01"},
            {"question_id": "Q002", "policy_area_id": "PA02", "dimension_id": "DIM01"},
            {"question_id": "Q003", "policy_area_id": "PA03", "dimension_id": "DIM02"},
        ]
        
        phase3_input = Phase3Input(
            preprocessed_document=complete_document,
            questions=questions
        )
        
        result = await phase3_contract.execute(phase3_input)
        
        # Verify DIM distribution
        assert result.dimension_distribution["DIM01"] == 2
        assert result.dimension_distribution["DIM02"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
