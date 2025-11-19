"""Tests for cryptographic proof generation."""

import json
import hashlib
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pytest

from saaaaaa.config.paths import SRC_DIR
from saaaaaa.utils.proof_generator import (
    ProofData,
    compute_file_hash,
    compute_dict_hash,
    compute_code_signatures,
    verify_success_conditions,
    generate_proof,
    collect_artifacts_manifest,
    verify_proof,
)


def test_compute_file_hash():
    """Test SHA-256 file hashing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Hello, World!")
        temp_path = Path(f.name)
    
    try:
        hash_val = compute_file_hash(temp_path)
        # SHA-256 of "Hello, World!"
        expected = hashlib.sha256(b"Hello, World!").hexdigest()
        assert hash_val == expected
        assert len(hash_val) == 64
    finally:
        temp_path.unlink()


def test_compute_file_hash_missing_file():
    """Test that missing file raises error."""
    with pytest.raises(FileNotFoundError):
        compute_file_hash(Path("/nonexistent/file.txt"))


def test_compute_dict_hash_deterministic():
    """Test that dict hashing is deterministic."""
    data = {'b': 2, 'a': 1, 'c': 3}
    
    hashes = [compute_dict_hash(data) for _ in range(10)]
    
    # All hashes should be identical
    assert len(set(hashes)) == 1
    assert len(hashes[0]) == 64


def test_compute_dict_hash_key_order_invariant():
    """Test that dict hashing ignores key order."""
    data1 = {'a': 1, 'b': 2, 'c': 3}
    data2 = {'c': 3, 'a': 1, 'b': 2}
    
    hash1 = compute_dict_hash(data1)
    hash2 = compute_dict_hash(data2)
    
    assert hash1 == hash2


def test_compute_code_signatures():
    """Test code signature computation."""
    # Use actual src directory
    src_root = SRC_DIR
    
    if not src_root.exists():
        pytest.skip("Source directory not found")
    
    signatures = compute_code_signatures(src_root)
    
    # Should have signatures for core files
    assert 'core.py' in signatures
    assert 'executors.py' in signatures
    assert 'factory.py' in signatures
    
    # All should be valid SHA-256 hashes
    for name, hash_val in signatures.items():
        assert len(hash_val) == 64
        assert all(c in '0123456789abcdef' for c in hash_val)


def test_verify_success_conditions_all_success():
    """Test success conditions with all phases successful."""
    @dataclass
    class MockPhaseResult:
        success: bool
        error: None = None
    
    phase_results = [MockPhaseResult(success=True) for _ in range(11)]
    
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        
        # Create some artifacts
        (output_dir / "test.json").write_text('{"test": "data"}')
        
        success, errors = verify_success_conditions(
            phase_results=phase_results,
            abort_active=False,
            output_dir=output_dir,
        )
        
        assert success is True
        assert len(errors) == 0


def test_verify_success_conditions_failed_phase():
    """Test success conditions with failed phase."""
    @dataclass
    class MockPhaseResult:
        success: bool
        error: None = None
    
    phase_results = [
        MockPhaseResult(success=True),
        MockPhaseResult(success=False),
        MockPhaseResult(success=True),
    ]
    
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        (output_dir / "test.json").write_text('{"test": "data"}')
        
        success, errors = verify_success_conditions(
            phase_results=phase_results,
            abort_active=False,
            output_dir=output_dir,
        )
        
        assert success is False
        assert any("Phases failed" in err for err in errors)


def test_verify_success_conditions_abort_active():
    """Test success conditions with abort active."""
    @dataclass
    class MockPhaseResult:
        success: bool
        error: None = None
    
    phase_results = [MockPhaseResult(success=True) for _ in range(11)]
    
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        (output_dir / "test.json").write_text('{"test": "data"}')
        
        success, errors = verify_success_conditions(
            phase_results=phase_results,
            abort_active=True,  # Abort is active
            output_dir=output_dir,
        )
        
        assert success is False
        assert any("Abort" in err for err in errors)


def test_verify_success_conditions_no_artifacts():
    """Test success conditions with no artifacts."""
    @dataclass
    class MockPhaseResult:
        success: bool
        error: None = None
    
    phase_results = [MockPhaseResult(success=True) for _ in range(11)]
    
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        # Don't create any artifacts
        
        success, errors = verify_success_conditions(
            phase_results=phase_results,
            abort_active=False,
            output_dir=output_dir,
        )
        
        assert success is False
        assert any("No artifacts" in err for err in errors)


def test_generate_proof_complete():
    """Test complete proof generation."""
    proof_data = ProofData(
        run_id='test-run-123',
        timestamp_utc='2024-01-01T12:00:00Z',
        phases_total=11,
        phases_success=11,
        questions_total=305,
        questions_answered=305,
        evidence_records=150,
        monolith_hash='a' * 64,
        questionnaire_hash='b' * 64,
        catalog_hash='c' * 64,
        method_map_hash='d' * 64,
        code_signature={
            'core.py': 'e' * 64,
            'executors.py': 'f' * 64,
            'factory.py': 'g' * 64,
        },
        input_pdf_hash='h' * 64,
    )
    
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        
        proof_json_path, proof_hash_path = generate_proof(
            proof_data=proof_data,
            output_dir=output_dir,
        )
        
        # Check files exist
        assert proof_json_path.exists()
        assert proof_hash_path.exists()
        
        # Check proof.json content
        with open(proof_json_path, 'r') as f:
            proof_dict = json.load(f)
        
        assert proof_dict['run_id'] == 'test-run-123'
        assert proof_dict['phases_total'] == 11
        assert proof_dict['phases_success'] == 11
        assert proof_dict['questions_total'] == 305
        assert proof_dict['monolith_hash'] == 'a' * 64
        assert 'core.py' in proof_dict['code_signature']
        
        # Check proof.hash content
        with open(proof_hash_path, 'r') as f:
            stored_hash = f.read().strip()
        
        assert len(stored_hash) == 64
        
        # Verify hash matches
        recomputed_hash = compute_dict_hash(proof_dict)
        assert stored_hash == recomputed_hash


def test_generate_proof_missing_required_field():
    """Test that proof generation fails with missing required fields."""
    proof_data = ProofData(
        run_id='',  # Empty required field
        timestamp_utc='2024-01-01T12:00:00Z',
        phases_total=11,
        phases_success=11,
        questions_total=305,
        questions_answered=305,
        evidence_records=150,
        monolith_hash='a' * 64,
        questionnaire_hash='b' * 64,
        catalog_hash='c' * 64,
        method_map_hash='d' * 64,
        code_signature={
            'core.py': 'e' * 64,
        },
    )
    
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        
        with pytest.raises(ValueError, match="run_id"):
            generate_proof(proof_data=proof_data, output_dir=output_dir)


def test_collect_artifacts_manifest():
    """Test artifact manifest collection."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        
        # Create some artifacts
        (output_dir / "test1.json").write_text('{"test": 1}')
        (output_dir / "test2.md").write_text('# Test')
        (output_dir / "subdir").mkdir()
        (output_dir / "subdir" / "test3.json").write_text('{"test": 3}')
        
        manifest = collect_artifacts_manifest(output_dir)
        
        # Should have all artifacts except proof files
        assert len(manifest) == 3
        assert any('test1.json' in key for key in manifest.keys())
        assert any('test2.md' in key for key in manifest.keys())
        assert any('test3.json' in key for key in manifest.keys())
        
        # All values should be SHA-256 hashes
        for hash_val in manifest.values():
            assert len(hash_val) == 64


def test_verify_proof_valid():
    """Test proof verification with valid proof."""
    proof_data = ProofData(
        run_id='test-run-verify',
        timestamp_utc='2024-01-01T12:00:00Z',
        phases_total=11,
        phases_success=11,
        questions_total=305,
        questions_answered=305,
        evidence_records=150,
        monolith_hash='a' * 64,
        questionnaire_hash='b' * 64,
        catalog_hash='c' * 64,
        method_map_hash='d' * 64,
        code_signature={'core.py': 'e' * 64},
    )
    
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        
        proof_json_path, proof_hash_path = generate_proof(
            proof_data=proof_data,
            output_dir=output_dir,
        )
        
        # Verify the proof
        valid, message = verify_proof(proof_json_path, proof_hash_path)
        
        assert valid is True
        assert "verified" in message.lower()


def test_verify_proof_tampered():
    """Test proof verification with tampered proof."""
    proof_data = ProofData(
        run_id='test-run-tamper',
        timestamp_utc='2024-01-01T12:00:00Z',
        phases_total=11,
        phases_success=11,
        questions_total=305,
        questions_answered=305,
        evidence_records=150,
        monolith_hash='a' * 64,
        questionnaire_hash='b' * 64,
        catalog_hash='c' * 64,
        method_map_hash='d' * 64,
        code_signature={'core.py': 'e' * 64},
    )
    
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        
        proof_json_path, proof_hash_path = generate_proof(
            proof_data=proof_data,
            output_dir=output_dir,
        )
        
        # Tamper with the proof
        with open(proof_json_path, 'r') as f:
            proof_dict = json.load(f)
        
        proof_dict['phases_total'] = 999  # Tamper
        
        with open(proof_json_path, 'w') as f:
            json.dump(proof_dict, f)
        
        # Verify should fail
        valid, message = verify_proof(proof_json_path, proof_hash_path)
        
        assert valid is False
        assert "failed" in message.lower() or "mismatch" in message.lower()


def test_proof_data_with_calibration_metadata():
    """Test ProofData includes calibration metadata."""
    proof_data = ProofData(
        run_id='test-run-123',
        timestamp_utc='2024-01-01T12:00:00Z',
        phases_total=11,
        phases_success=11,
        questions_total=305,
        questions_answered=305,
        evidence_records=150,
        monolith_hash='a' * 64,
        questionnaire_hash='b' * 64,
        catalog_hash='c' * 64,
        method_map_hash='d' * 64,
        code_signature={'core.py': 'e' * 64},
        calibration_version='1.0.0',
        calibration_hash='calib' * 16,  # 64 chars
    )
    
    assert proof_data.calibration_version == '1.0.0'
    assert proof_data.calibration_hash == 'calib' * 16
    
    # Test proof generation includes calibration metadata
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        
        proof_json_path, _ = generate_proof(
            proof_data=proof_data,
            output_dir=output_dir,
        )
        
        with open(proof_json_path, 'r') as f:
            proof_dict = json.load(f)
        
        assert proof_dict['calibration_version'] == '1.0.0'
        assert proof_dict['calibration_hash'] == 'calib' * 16
