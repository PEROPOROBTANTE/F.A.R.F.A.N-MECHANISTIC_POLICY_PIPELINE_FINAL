"""
Test Suite for Phase 1 SPC Ingestion Execution Contract
=======================================================
"""

import unittest
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from saaaaaa.core.phases.phase0_input_validation import CanonicalInput
from saaaaaa.core.phases.phase1_spc_ingestion_full import (
    execute_phase_1_with_full_contract,
    Phase1SPCIngestionFullContract,
    Phase1FatalError,
    PADimGridSpecification
)
from saaaaaa.processing.cpp_ingestion.models import CanonPolicyPackage

class TestPhase1FullContract(unittest.TestCase):

    def setUp(self):
        self.mock_pdf_path = Path("mock.pdf")
        self.mock_canonical_input = CanonicalInput(
            document_id="test_doc",
            run_id="test_run",
            pdf_path=self.mock_pdf_path,
            pdf_sha256="a" * 64,
            pdf_size_bytes=1000,
            pdf_page_count=10,
            questionnaire_path=Path("q.json"),
            questionnaire_sha256="b" * 64,
            created_at=datetime.now(timezone.utc),
            phase0_version="1.0.0",
            validation_passed=True
        )

    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.read_text", return_value="Sample text content.")
    def test_happy_path_execution(self, mock_read, mock_exists):
        """Test full execution with valid input."""
        cpp = execute_phase_1_with_full_contract(self.mock_canonical_input)
        
        # Verify output structure
        self.assertIsInstance(cpp, CanonPolicyPackage)
        self.assertEqual(len(cpp.chunk_graph.chunks), 60)
        self.assertEqual(cpp.schema_version, "SPC-2025.1")
        
        # Verify trace completeness
        trace = cpp.metadata["execution_trace"]
        self.assertEqual(len(trace), 16)
        self.assertEqual(trace[0][0], "SP0")
        self.assertEqual(trace[15][0], "SP15")

    def test_invariant_violation_chunk_count(self):
        """Test failure when chunk count is incorrect."""
        executor = Phase1SPCIngestionFullContract()
        
        # Mock SP4 to return wrong number of chunks
        executor._execute_sp4_segmentation = MagicMock(return_value=[])
        
        with self.assertRaises(Phase1FatalError) as cm:
            executor.run(self.mock_canonical_input)
        
        self.assertIn("Expected 60 chunks", str(cm.exception))

    def test_grid_specification_validation(self):
        """Test PADimGridSpecification validation."""
        # Valid chunk
        valid_chunk = MagicMock()
        valid_chunk.policy_area_id = "PA01"
        valid_chunk.dimension_id = "DIM01"
        valid_chunk.chunk_index = 0
        valid_chunk.causal_graph = {}
        valid_chunk.temporal_markers = {}
        valid_chunk.arguments = {}
        valid_chunk.discourse_mode = "narrative"
        valid_chunk.strategic_rank = 0
        valid_chunk.irrigation_links = []
        valid_chunk.signal_tags = []
        valid_chunk.signal_scores = {}
        valid_chunk.signal_version = "v1"
        
        PADimGridSpecification.validate_chunk(valid_chunk)
        
        # Invalid PA
        invalid_chunk = MagicMock()
        invalid_chunk.policy_area_id = "INVALID"
        invalid_chunk.dimension_id = "DIM01"
        invalid_chunk.chunk_index = 0
        
        with self.assertRaises(AssertionError):
            PADimGridSpecification.validate_chunk(invalid_chunk)

if __name__ == "__main__":
    unittest.main()
