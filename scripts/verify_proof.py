#!/usr/bin/env python3
"""F.A.R.F.A.N Standalone Proof Verification Script.

Framework for Advanced Retrieval of Administrativa Narratives

This script can be run by anyone to verify a proof.json file from the 
F.A.R.F.A.N pipeline without needing to understand the codebase or have 
the full environment set up.

Usage:
    python verify_proof.py <output_directory>
    
Example:
    python verify_proof.py data/output/cpp_plan_1
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path


def compute_hash(data: dict) -> str:
    """Compute SHA-256 hash of dictionary with deterministic serialization."""
    json_str = json.dumps(data, sort_keys=True, ensure_ascii=True, separators=(',', ':'))
    return hashlib.sha256(json_str.encode('utf-8')).hexdigest()


def verify_proof(output_dir: Path) -> int:
    """Verify proof files in output directory.
    
    Returns:
        0 if verification passes, 1 otherwise
    """
    print("=" * 80)
    print("F.A.R.F.A.N CRYPTOGRAPHIC PROOF VERIFICATION")
    print("=" * 80)
    print()
    
    # Check files exist
    proof_json = output_dir / "proof.json"
    proof_hash = output_dir / "proof.hash"
    
    if not proof_json.exists():
        print(f"❌ proof.json not found in {output_dir}")
        return 1
    
    if not proof_hash.exists():
        print(f"❌ proof.hash not found in {output_dir}")
        return 1
    
    print(f"📁 Output directory: {output_dir}")
    print(f"📄 Found proof.json: {proof_json}")
    print(f"🔐 Found proof.hash: {proof_hash}")
    print()
    
    # Read proof.json
    try:
        with open(proof_json, 'r', encoding='utf-8') as f:
            proof_data = json.load(f)
    except Exception as e:
        print(f"❌ Failed to read proof.json: {e}")
        return 1
    
    # Read proof.hash
    try:
        with open(proof_hash, 'r', encoding='utf-8') as f:
            stored_hash = f.read().strip()
    except Exception as e:
        print(f"❌ Failed to read proof.hash: {e}")
        return 1
    
    # Verify hash format
    if len(stored_hash) != 64:
        print(f"❌ Invalid hash length: {len(stored_hash)} (expected 64)")
        return 1
    
    if not all(c in '0123456789abcdef' for c in stored_hash):
        print(f"❌ Invalid hash format (not hex)")
        return 1
    
    # Recompute hash
    computed_hash = compute_hash(proof_data)
    
    print("🔍 HASH VERIFICATION")
    print("-" * 80)
    print(f"Stored hash:   {stored_hash}")
    print(f"Computed hash: {computed_hash}")
    print()
    
    if computed_hash != stored_hash:
        print("❌ VERIFICATION FAILED: Hash mismatch!")
        print("   The proof.json file has been tampered with or corrupted.")
        return 1
    
    print("✅ Hash verification PASSED")
    print()
    
    # Display proof contents
    print("📊 PROOF CONTENTS")
    print("-" * 80)
    # Validate mandatory fields before displaying contents
    required_fields = [
        'run_id', 'timestamp_utc',
        'phases_total', 'phases_success',
        'questions_total', 'questions_answered',
        'evidence_records',
        'monolith_hash', 'catalog_hash'
    ]
    # Optional-but-expected fields that must be present if produced by generator
    expected_fields = ['questionnaire_hash', 'input_pdf_hash', 'artifacts_manifest', 'code_signature']

    missing = [k for k in required_fields if k not in proof_data]
    if missing:
        print(f"❌ Missing required field(s) in proof.json: {', '.join(missing)}")
        return 1

    # Basic structural/type validations
    hash_keys = [k for k in ['monolith_hash', 'catalog_hash', 'questionnaire_hash', 'input_pdf_hash'] if k in proof_data]
    for k in hash_keys:
        v = proof_data.get(k, '')
        if not (isinstance(v, str) and len(v) == 64 and all(c in '0123456789abcdef' for c in v)):
            print(f"❌ Invalid hash for {k}: expected 64-char lowercase hex")
            return 1

    if not isinstance(proof_data.get('phases_total'), int) or not isinstance(proof_data.get('phases_success'), int):
        print("❌ phases_total and phases_success must be integers")
        return 1
    if not isinstance(proof_data.get('questions_total'), int) or not isinstance(proof_data.get('questions_answered'), int):
        print("❌ questions_total and questions_answered must be integers")
        return 1
    if not isinstance(proof_data.get('evidence_records'), int):
        print("❌ evidence_records must be an integer")
        return 1

    # Validate maps presence and non-empty
    for k in ['code_signature', 'artifacts_manifest']:
        if k not in proof_data or not isinstance(proof_data[k], dict) or len(proof_data[k]) == 0:
            print(f"❌ {k} must be present and non-empty")
            return 1

    # Display proof contents
    print("📊 PROOF CONTENTS")
    print("-" * 80)
    print(f"Run ID:              {proof_data.get('run_id', 'N/A')}")
    print(f"Timestamp (UTC):     {proof_data.get('timestamp_utc', 'N/A')}")
    print(f"Phases Total:        {proof_data.get('phases_total', 'N/A')}")
    print(f"Phases Success:      {proof_data.get('phases_success', 'N/A')}")
    print(f"Questions Total:     {proof_data.get('questions_total', 'N/A')}")
    print(f"Questions Answered:  {proof_data.get('questions_answered', 'N/A')}")
    print(f"Evidence Records:    {proof_data.get('evidence_records', 'N/A')}")
    print()
    
    # Verify all phases succeeded
    phases_total = proof_data.get('phases_total', 0)
    phases_success = proof_data.get('phases_success', 0)
    
    if phases_total == phases_success and phases_total > 0:
        print(f"✅ All {phases_total} phases completed successfully")
    else:
        print(f"⚠️  Only {phases_success}/{phases_total} phases succeeded")
    
    # Check question coverage
    questions_total = proof_data.get('questions_total', 0)
    questions_answered = proof_data.get('questions_answered', 0)
    
    if questions_total > 0:
        coverage = (questions_answered / questions_total) * 100
        print(f"📝 Question coverage: {questions_answered}/{questions_total} ({coverage:.1f}%)")
    
    print()
    
    # Display code signatures
    code_sig = proof_data.get('code_signature', {})
    if code_sig:
        print("🔐 CODE SIGNATURES")
        print("-" * 80)
        for filename, file_hash in sorted(code_sig.items()):
            print(f"{filename:20s} {file_hash[:16]}...{file_hash[-8:]}")
        print()
    
    # Display data hashes
    print("🔐 DATA HASHES")
    print("-" * 80)
    for key in ['monolith_hash', 'questionnaire_hash', 'catalog_hash', 'input_pdf_hash']:
        if key in proof_data:
            hash_val = proof_data[key]
            if len(hash_val) == 64:
                print(f"{key:20s} {hash_val[:16]}...{hash_val[-8:]}")
            else:
                print(f"{key:20s} {hash_val}")
    print()
    
    # Display artifacts
    artifacts = proof_data.get('artifacts_manifest', {})
    if artifacts:
        print(f"📦 ARTIFACTS ({len(artifacts)} files)")
        print("-" * 80)
        for artifact_name in sorted(artifacts.keys())[:10]:  # Show first 10
            print(f"  - {artifact_name}")
        if len(artifacts) > 10:
            print(f"  ... and {len(artifacts) - 10} more")
        print()
    
    # Final verdict
    print("=" * 80)
    if phases_total == phases_success and phases_total > 0:
        print("=" * 80)
        print("✅ PROOF VERIFICATION SUCCESSFUL")
        print("=" * 80)
        print()
        print("This execution proof is valid and has not been tampered with.")
        print("The pipeline completed successfully with verified results.")
        print()
        return 0
    else:
        print("=" * 80)
        print("❌ PROOF VERIFICATION FAILED")
        print("=" * 80)
        print()
        print("The proof indicates not all phases succeeded or phase counts are invalid.")
        print("Verification fails to prevent accepting incomplete or tampered executions.")
        print()
        return 1
    print("=" * 80)
    print()
    print("This execution proof is valid and has not been tampered with.")
    print("The pipeline completed successfully with verified results.")
    print()
    
    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Verify cryptographic proof of pipeline execution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python verify_proof.py data/output/cpp_plan_1
  python verify_proof.py /path/to/output/dir

This script verifies:
1. proof.json and proof.hash files exist
2. The hash in proof.hash matches the computed hash of proof.json
3. The proof contains all required fields
4. All phases completed successfully
        """
    )
    parser.add_argument(
        'output_dir',
        type=Path,
        help='Directory containing proof.json and proof.hash'
    )
    
    args = parser.parse_args()
    
    if not args.output_dir.exists():
        print(f"❌ Directory not found: {args.output_dir}")
        return 1
    
    if not args.output_dir.is_dir():
        print(f"❌ Not a directory: {args.output_dir}")
        return 1
    
    return verify_proof(args.output_dir)


if __name__ == "__main__":
    sys.exit(main())
