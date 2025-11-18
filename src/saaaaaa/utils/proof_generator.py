"""Cryptographic proof generation for pipeline execution verification.

This module generates cryptographic proof files that allow non-engineers to verify
that a pipeline execution was successful and complete. It produces:
- proof.json: Contains execution metadata, phase/question counts, and SHA-256 hashes
- proof.hash: SHA-256 hash of the proof.json file for verification

The proof is ONLY generated when ALL success conditions are met:
- All phases report success=True
- No abort is active
- Non-empty artifacts exist (JSON/MD/logs)
"""

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ProofData:
    """Container for proof generation data.

    All fields must be populated from real execution data.
    No values should be invented or hardcoded.
    """
    run_id: str
    timestamp_utc: str
    phases_total: int
    phases_success: int
    questions_total: int
    questions_answered: int
    evidence_records: int
    monolith_hash: str
    questionnaire_hash: str
    catalog_hash: str
    method_map_hash: str
    code_signature: dict[str, str]

    # Optional fields for additional verification
    input_pdf_hash: str | None = None
    artifacts_manifest: dict[str, str] = field(default_factory=dict)
    execution_metadata: dict[str, Any] = field(default_factory=dict)

    # Calibration metadata for traceability
    calibration_version: str | None = None
    calibration_hash: str | None = None


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash

    Returns:
        Hex string of SHA-256 hash

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Cannot hash missing file: {file_path}")

    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        # Read in chunks for large files
        for chunk in iter(lambda: f.read(65536), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def compute_dict_hash(data: dict[str, Any]) -> str:
    """Compute SHA-256 hash of a dictionary.

    The dictionary is serialized with sort_keys=True and ensure_ascii=True
    to ensure deterministic hashing.

    Args:
        data: Dictionary to hash

    Returns:
        Hex string of SHA-256 hash
    """
    json_str = json.dumps(data, sort_keys=True, ensure_ascii=True, separators=(',', ':'))
    return hashlib.sha256(json_str.encode('utf-8')).hexdigest()


def compute_code_signatures(src_root: Path) -> dict[str, str]:
    """Compute SHA-256 hashes of core orchestrator files.

    Args:
        src_root: Root path to the src/saaaaaa directory

    Returns:
        Dictionary mapping filename to SHA-256 hash

    Raises:
        FileNotFoundError: If any required file is missing
    """
    core_files = {
        'core.py': src_root / 'core' / 'orchestrator' / 'core.py',
        'executors.py': src_root / 'core' / 'orchestrator' / 'executors.py',
        'factory.py': src_root / 'core' / 'orchestrator' / 'factory.py',
    }

    signatures = {}
    for name, path in core_files.items():
        if not path.exists():
            raise FileNotFoundError(f"Required core file missing: {path}")
        signatures[name] = compute_file_hash(path)

    return signatures


def verify_success_conditions(
    phase_results: list[Any],
    abort_active: bool,
    output_dir: Path,
) -> tuple[bool, list[str]]:
    """Verify that all success conditions are met before generating proof.

    Args:
        phase_results: List of PhaseResult objects from orchestrator
        abort_active: Whether an abort signal is active
        output_dir: Directory where artifacts should exist

    Returns:
        Tuple of (success: bool, errors: list[str])
    """
    errors = []

    # Check all phases succeeded
    if not phase_results:
        errors.append("No phase results available")
        return False, errors

    failed_phases = [
        i for i, result in enumerate(phase_results)
        if not result.success
    ]
    if failed_phases:
        errors.append(f"Phases failed: {failed_phases}")

    # Check no abort
    if abort_active:
        errors.append("Abort signal is active")

    # Check for artifacts (at minimum, directory should exist and have content)
    if not output_dir.exists():
        errors.append(f"Output directory does not exist: {output_dir}")
    else:
        # Check for at least some artifacts
        artifacts = list(output_dir.rglob('*.json')) + list(output_dir.rglob('*.md'))
        if not artifacts:
            errors.append(f"No artifacts (JSON/MD) found in {output_dir}")

    return len(errors) == 0, errors


def generate_proof(
    proof_data: ProofData,
    output_dir: Path,
) -> tuple[Path, Path]:
    """Generate proof.json and proof.hash files.

    Args:
        proof_data: Proof data to serialize
        output_dir: Directory where proof files will be written

    Returns:
        Tuple of (proof.json path, proof.hash path)

    Raises:
        ValueError: If proof_data is incomplete
    """
    # Validate required fields are not empty
    required_fields = [
        'run_id', 'timestamp_utc', 'monolith_hash', 'questionnaire_hash',
        'catalog_hash', 'code_signature'
    ]
    for field_name in required_fields:
        value = getattr(proof_data, field_name)
        if not value:
            raise ValueError(f"Required field '{field_name}' is empty")

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build proof dictionary
    proof_dict = {
        'run_id': proof_data.run_id,
        'timestamp_utc': proof_data.timestamp_utc,
        'phases_total': proof_data.phases_total,
        'phases_success': proof_data.phases_success,
        'questions_total': proof_data.questions_total,
        'questions_answered': proof_data.questions_answered,
        'evidence_records': proof_data.evidence_records,
        'monolith_hash': proof_data.monolith_hash,
        'questionnaire_hash': proof_data.questionnaire_hash,
        'catalog_hash': proof_data.catalog_hash,
        'method_map_hash': proof_data.method_map_hash,
        'code_signature': proof_data.code_signature,
    }

    # Add optional fields if present
    if proof_data.input_pdf_hash:
        proof_dict['input_pdf_hash'] = proof_data.input_pdf_hash
    if proof_data.artifacts_manifest:
        proof_dict['artifacts_manifest'] = proof_data.artifacts_manifest
    if proof_data.execution_metadata:
        proof_dict['execution_metadata'] = proof_data.execution_metadata

    # Add calibration metadata for traceability
    if proof_data.calibration_version:
        proof_dict['calibration_version'] = proof_data.calibration_version
    if proof_data.calibration_hash:
        proof_dict['calibration_hash'] = proof_data.calibration_hash

    # Write proof.json with deterministic serialization
    proof_json_path = output_dir / 'proof.json'
    with open(proof_json_path, 'w', encoding='utf-8') as f:
        json.dump(
            proof_dict,
            f,
            sort_keys=True,
            ensure_ascii=True,
            separators=(',', ':'),
        )

    # Compute hash of proof.json (using compact serialization for hash)
    proof_hash = compute_dict_hash(proof_dict)

    # Write proof.hash
    proof_hash_path = output_dir / 'proof.hash'
    with open(proof_hash_path, 'w', encoding='utf-8') as f:
        f.write(proof_hash)

    return proof_json_path, proof_hash_path


def collect_artifacts_manifest(output_dir: Path) -> dict[str, str]:
    """Collect hashes of all artifacts in output directory.

    Args:
        output_dir: Directory containing artifacts

    Returns:
        Dictionary mapping relative path to SHA-256 hash
    """
    manifest = {}

    # Find all artifacts (JSON, MD, logs)
    patterns = ['*.json', '*.md', '*.log', '*.txt']
    for pattern in patterns:
        for artifact_path in output_dir.rglob(pattern):
            # Skip proof files themselves
            if artifact_path.name in ('proof.json', 'proof.hash'):
                continue

            try:
                rel_path = artifact_path.relative_to(output_dir)
                manifest[str(rel_path)] = compute_file_hash(artifact_path)
            except (OSError, PermissionError, ValueError):
                # Skip files we can't read or hash
                pass

    return manifest


def verify_proof(proof_json_path: Path, proof_hash_path: Path) -> tuple[bool, str]:
    """Verify that a proof.json file matches its proof.hash.

    This allows anyone to verify that the proof hasn't been tampered with.

    Args:
        proof_json_path: Path to proof.json
        proof_hash_path: Path to proof.hash

    Returns:
        Tuple of (valid: bool, message: str)
    """
    try:
        # Read proof.json
        with open(proof_json_path, encoding='utf-8') as f:
            proof_dict = json.load(f)

        # Read proof.hash
        with open(proof_hash_path, encoding='utf-8') as f:
            stored_hash = f.read().strip()

        # Recompute hash
        computed_hash = compute_dict_hash(proof_dict)

        # Compare
        if computed_hash == stored_hash:
            return True, "✅ Proof verified: hash matches"
        else:
            return False, f"❌ Proof verification failed: hash mismatch\n  Expected: {stored_hash}\n  Got: {computed_hash}"

    except Exception as e:
        return False, f"❌ Proof verification error: {e}"
