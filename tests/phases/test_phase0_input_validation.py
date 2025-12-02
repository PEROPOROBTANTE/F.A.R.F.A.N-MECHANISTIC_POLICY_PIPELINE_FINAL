"""Test Phase 0: Input Validation Contract

Tests:
- Input contract validation (Phase0Input)
- Output contract validation (CanonicalInput)
- PDF existence and readability
- SHA256 hash determinism (same file → same hash)
- Questionnaire path resolution
- Metadata extraction (page count, file size)
- Invariant checking
- Error propagation for missing files
"""

import hashlib
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from farfan_pipeline.core.phases.phase0_input_validation import (
    CanonicalInput,
    Phase0Input,
    Phase0ValidationContract,
    PHASE0_VERSION,
)


class TestPhase0InputContract:
    """Test Phase 0 input contract validation."""

    def test_phase0_input_valid(self):
        """Test valid Phase0Input passes validation."""
        contract = Phase0ValidationContract()
        input_data = Phase0Input(
            pdf_path=Path("test.pdf"),
            run_id="test_run_001",
            questionnaire_path=Path("questions.json"),
        )

        result = contract.validate_input(input_data)
        assert result.passed
        assert len(result.errors) == 0

    def test_phase0_input_invalid_type(self):
        """Test invalid input type fails validation."""
        contract = Phase0ValidationContract()
        input_data = {"pdf_path": "test.pdf"}

        result = contract.validate_input(input_data)
        assert not result.passed
        assert len(result.errors) > 0
        assert "Phase0Input" in result.errors[0]

    def test_phase0_input_empty_run_id(self):
        """Test empty run_id fails validation."""
        contract = Phase0ValidationContract()
        input_data = Phase0Input(
            pdf_path=Path("test.pdf"),
            run_id="",
            questionnaire_path=None,
        )

        result = contract.validate_input(input_data)
        assert not result.passed

    def test_phase0_input_invalid_run_id_chars(self):
        """Test run_id with invalid filesystem chars fails validation."""
        contract = Phase0ValidationContract()
        input_data = Phase0Input(
            pdf_path=Path("test.pdf"),
            run_id="test/run:001",
            questionnaire_path=None,
        )

        result = contract.validate_input(input_data)
        assert not result.passed


class TestPhase0OutputContract:
    """Test Phase 0 output contract validation."""

    def test_canonical_input_valid(self, tmp_path):
        """Test valid CanonicalInput passes validation."""
        from datetime import datetime, timezone

        contract = Phase0ValidationContract()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"PDF content")

        output_data = CanonicalInput(
            document_id="test_doc",
            run_id="test_run_001",
            pdf_path=pdf_path,
            pdf_sha256="a" * 64,
            pdf_size_bytes=100,
            pdf_page_count=5,
            questionnaire_path=tmp_path / "questions.json",
            questionnaire_sha256="b" * 64,
            created_at=datetime.now(timezone.utc),
            phase0_version=PHASE0_VERSION,
            validation_passed=True,
            validation_errors=[],
            validation_warnings=[],
        )

        result = contract.validate_output(output_data)
        assert result.passed
        assert len(result.errors) == 0

    def test_canonical_input_validation_failed(self, tmp_path):
        """Test CanonicalInput with validation_passed=False fails."""
        from datetime import datetime, timezone

        contract = Phase0ValidationContract()

        output_data = CanonicalInput(
            document_id="test_doc",
            run_id="test_run_001",
            pdf_path=tmp_path / "test.pdf",
            pdf_sha256="a" * 64,
            pdf_size_bytes=100,
            pdf_page_count=5,
            questionnaire_path=tmp_path / "questions.json",
            questionnaire_sha256="b" * 64,
            created_at=datetime.now(timezone.utc),
            phase0_version=PHASE0_VERSION,
            validation_passed=False,
            validation_errors=["Some error"],
            validation_warnings=[],
        )

        result = contract.validate_output(output_data)
        assert not result.passed
        assert any("validation_passed" in err for err in result.errors)

    def test_canonical_input_invalid_sha256(self, tmp_path):
        """Test CanonicalInput with invalid SHA256 fails."""
        from datetime import datetime, timezone

        contract = Phase0ValidationContract()

        output_data = CanonicalInput(
            document_id="test_doc",
            run_id="test_run_001",
            pdf_path=tmp_path / "test.pdf",
            pdf_sha256="invalid_hash",
            pdf_size_bytes=100,
            pdf_page_count=5,
            questionnaire_path=tmp_path / "questions.json",
            questionnaire_sha256="b" * 64,
            created_at=datetime.now(timezone.utc),
            phase0_version=PHASE0_VERSION,
            validation_passed=True,
            validation_errors=[],
            validation_warnings=[],
        )

        result = contract.validate_output(output_data)
        assert not result.passed

    def test_canonical_input_zero_page_count(self, tmp_path):
        """Test CanonicalInput with zero page_count fails."""
        from datetime import datetime, timezone

        contract = Phase0ValidationContract()

        output_data = CanonicalInput(
            document_id="test_doc",
            run_id="test_run_001",
            pdf_path=tmp_path / "test.pdf",
            pdf_sha256="a" * 64,
            pdf_size_bytes=100,
            pdf_page_count=0,
            questionnaire_path=tmp_path / "questions.json",
            questionnaire_sha256="b" * 64,
            created_at=datetime.now(timezone.utc),
            phase0_version=PHASE0_VERSION,
            validation_passed=True,
            validation_errors=[],
            validation_warnings=[],
        )

        result = contract.validate_output(output_data)
        assert not result.passed


class TestPhase0Execution:
    """Test Phase 0 execution logic."""

    @pytest.mark.asyncio
    async def test_execute_missing_pdf(self, tmp_path):
        """Test execution fails for missing PDF."""
        contract = Phase0ValidationContract()
        input_data = Phase0Input(
            pdf_path=tmp_path / "nonexistent.pdf",
            run_id="test_run_001",
            questionnaire_path=tmp_path / "questions.json",
        )

        with pytest.raises(FileNotFoundError) as exc_info:
            await contract.execute(input_data)

        assert "PDF not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_missing_questionnaire(self, tmp_path):
        """Test execution fails for missing questionnaire."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n")

        contract = Phase0ValidationContract()
        input_data = Phase0Input(
            pdf_path=pdf_path,
            run_id="test_run_001",
            questionnaire_path=tmp_path / "nonexistent.json",
        )

        with pytest.raises(FileNotFoundError) as exc_info:
            await contract.execute(input_data)

        assert "Questionnaire not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_success(self, tmp_path):
        """Test successful execution produces valid CanonicalInput."""
        pdf_path = tmp_path / "test.pdf"
        pdf_content = b"%PDF-1.4\n%Test PDF content"
        pdf_path.write_bytes(pdf_content)

        questionnaire_path = tmp_path / "questions.json"
        questionnaire_path.write_text('{"questions": []}')

        contract = Phase0ValidationContract()

        with patch.object(contract, "_get_pdf_page_count", return_value=5):
            input_data = Phase0Input(
                pdf_path=pdf_path,
                run_id="test_run_001",
                questionnaire_path=questionnaire_path,
            )

            canonical_input = await contract.execute(input_data)

            assert canonical_input.document_id == "test"
            assert canonical_input.run_id == "test_run_001"
            assert canonical_input.pdf_path == pdf_path
            assert len(canonical_input.pdf_sha256) == 64
            assert canonical_input.pdf_size_bytes == len(pdf_content)
            assert canonical_input.pdf_page_count == 5
            assert canonical_input.validation_passed is True
            assert len(canonical_input.validation_errors) == 0


class TestPhase0SHA256Determinism:
    """Test SHA256 hash stability across runs."""

    def test_sha256_same_file_same_hash(self, tmp_path):
        """Test same file produces same SHA256 hash."""
        pdf_path = tmp_path / "test.pdf"
        pdf_content = b"%PDF-1.4\nTest content for determinism"
        pdf_path.write_bytes(pdf_content)

        contract = Phase0ValidationContract()

        hash1 = contract._compute_sha256(pdf_path)
        hash2 = contract._compute_sha256(pdf_path)

        assert hash1 == hash2
        assert len(hash1) == 64
        assert all(c in "0123456789abcdef" for c in hash1)

    def test_sha256_different_content_different_hash(self, tmp_path):
        """Test different content produces different SHA256 hash."""
        pdf1 = tmp_path / "test1.pdf"
        pdf2 = tmp_path / "test2.pdf"
        pdf1.write_bytes(b"%PDF-1.4\nContent A")
        pdf2.write_bytes(b"%PDF-1.4\nContent B")

        contract = Phase0ValidationContract()

        hash1 = contract._compute_sha256(pdf1)
        hash2 = contract._compute_sha256(pdf2)

        assert hash1 != hash2

    def test_sha256_matches_expected(self, tmp_path):
        """Test SHA256 matches expected value for known content."""
        pdf_path = tmp_path / "test.pdf"
        pdf_content = b"test"
        pdf_path.write_bytes(pdf_content)

        contract = Phase0ValidationContract()
        computed_hash = contract._compute_sha256(pdf_path)

        expected_hash = hashlib.sha256(pdf_content).hexdigest()
        assert computed_hash == expected_hash


class TestPhase0Invariants:
    """Test Phase 0 invariants."""

    def test_all_invariants_registered(self):
        """Test all required invariants are registered."""
        contract = Phase0ValidationContract()

        invariant_names = [inv.name for inv in contract.invariants]

        assert "validation_passed" in invariant_names
        assert "pdf_page_count_positive" in invariant_names
        assert "pdf_size_positive" in invariant_names
        assert "sha256_format" in invariant_names
        assert "no_validation_errors" in invariant_names

    def test_invariants_pass_for_valid_output(self, tmp_path):
        """Test invariants pass for valid output."""
        from datetime import datetime, timezone

        contract = Phase0ValidationContract()

        output_data = CanonicalInput(
            document_id="test_doc",
            run_id="test_run_001",
            pdf_path=tmp_path / "test.pdf",
            pdf_sha256="a" * 64,
            pdf_size_bytes=100,
            pdf_page_count=5,
            questionnaire_path=tmp_path / "questions.json",
            questionnaire_sha256="b" * 64,
            created_at=datetime.now(timezone.utc),
            phase0_version=PHASE0_VERSION,
            validation_passed=True,
            validation_errors=[],
            validation_warnings=[],
        )

        passed, failed = contract.check_invariants(output_data)
        assert passed
        assert len(failed) == 0

    def test_invariants_fail_for_invalid_output(self, tmp_path):
        """Test invariants fail for invalid output."""
        from datetime import datetime, timezone

        contract = Phase0ValidationContract()

        output_data = CanonicalInput(
            document_id="test_doc",
            run_id="test_run_001",
            pdf_path=tmp_path / "test.pdf",
            pdf_sha256="invalid",
            pdf_size_bytes=0,
            pdf_page_count=0,
            questionnaire_path=tmp_path / "questions.json",
            questionnaire_sha256="b" * 64,
            created_at=datetime.now(timezone.utc),
            phase0_version=PHASE0_VERSION,
            validation_passed=False,
            validation_errors=["error"],
            validation_warnings=[],
        )

        passed, failed = contract.check_invariants(output_data)
        assert not passed
        assert len(failed) > 0


class TestPhase0Run:
    """Test Phase 0 run() integration."""

    @pytest.mark.asyncio
    async def test_run_validates_input(self, tmp_path):
        """Test run() validates input contract."""
        contract = Phase0ValidationContract()
        invalid_input = "not a Phase0Input"

        with pytest.raises(ValueError) as exc_info:
            await contract.run(invalid_input)

        assert "Input contract validation failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_run_returns_metadata(self, tmp_path):
        """Test run() returns phase metadata."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n")
        questionnaire_path = tmp_path / "questions.json"
        questionnaire_path.write_text('{}')

        contract = Phase0ValidationContract()

        with patch.object(contract, "_get_pdf_page_count", return_value=3):
            input_data = Phase0Input(
                pdf_path=pdf_path,
                run_id="test_run",
                questionnaire_path=questionnaire_path,
            )

            output, metadata = await contract.run(input_data)

            assert metadata.phase_name == "phase0_input_validation"
            assert metadata.success is True
            assert metadata.error is None
            assert metadata.duration_ms is not None
            assert metadata.duration_ms >= 0
