# F.A.R.F.A.N Cryptographic Proof Verification

**Framework for Advanced Retrieval of Administrativa Narratives**

## Overview

Every successful F.A.R.F.A.N pipeline execution generates cryptographic proof files that allow anyone (even non-engineers) to verify that the execution was genuine and complete.

## Generated Files

When the pipeline completes successfully, two files are created in the output directory:

1. **`proof.json`** - Contains execution metadata and cryptographic hashes
2. **`proof.hash`** - SHA-256 hash of `proof.json` for tamper detection

## What's in proof.json?

The proof file contains:

### Execution Metadata
- `run_id` - Unique identifier for this execution (UUID)
- `timestamp_utc` - When the execution completed (ISO8601 format)
- `phases_total` - Total number of phases executed
- `phases_success` - Number of phases that succeeded
- `questions_total` - Total micro-questions in questionnaire
- `questions_answered` - Number of questions successfully answered
- `evidence_records` - Number of evidence items collected

### Cryptographic Hashes (SHA-256)
- `monolith_hash` - Hash of the questionnaire monolith
- `questionnaire_hash` - Hash of questionnaire structure
- `catalog_hash` - Hash of the method catalog
- `method_map_hash` - Hash of method mappings
- `input_pdf_hash` - Hash of the input PDF file
- `code_signature` - Hashes of core orchestrator files:
  - `core.py`
  - `executors.py`
  - `factory.py`

### Additional Data
- `artifacts_manifest` - Hashes of generated JSON/MD/log/txt artifacts
- `execution_metadata` - Runtime statistics

## When is Proof Generated?

Proof is **ONLY** generated when **ALL** of these conditions are met:

1. ✅ All phases report `success=True`
2. ✅ No abort signal is active
3. ✅ Non-empty artifacts exist (JSON/MD/logs)

If any condition fails, **no proof is generated**. This prevents false claims of success.

## How to Verify Proof

### Basic Verification (Command Line)

```bash
# 1. View the proof
cat data/output/cpp_plan_1/proof.json

# 2. View the stored hash
cat data/output/cpp_plan_1/proof.hash

# 3. Recompute hash and compare
# On Linux/macOS:
python3 -c "import json, hashlib; \
  data = json.load(open('data/output/cpp_plan_1/proof.json')); \
  print(hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=True, separators=(',', ':')).encode()).hexdigest())"

# Compare with stored hash:
cat data/output/cpp_plan_1/proof.hash
```

### Programmatic Verification

```python
from pathlib import Path
from saaaaaa.utils.proof_generator import verify_proof

proof_dir = Path("data/output/cpp_plan_1")
valid, message = verify_proof(
    proof_dir / "proof.json",
    proof_dir / "proof.hash"
)

if valid:
    print("✅", message)
else:
    print("❌", message)
```

### What to Check

1. **Hash Verification**: Recompute the hash of `proof.json` and verify it matches `proof.hash`
2. **Phase Success**: Verify `phases_success == phases_total`
3. **Question Coverage**: Check `questions_answered` vs `questions_total`
4. **Code Integrity**: Compare `code_signature` hashes with current code files
5. **Input Integrity**: Verify `input_pdf_hash` matches your input PDF

## Security Properties

### Tamper Detection
- Any modification to `proof.json` will cause hash mismatch
- The hash is deterministic (same data = same hash)
- Uses SHA-256 (64 hex characters)

### Deterministic Serialization
- JSON is serialized with `sort_keys=True` and `ensure_ascii=True`
- This ensures the same data always produces the same hash
- Key order doesn't matter

### Non-Repudiation
- The `run_id` uniquely identifies each execution
- The `timestamp_utc` records when it completed
- The `input_pdf_hash` proves which file was processed
- The `code_signature` proves which code was used

## Example Proof File

```json
{
  "run_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "timestamp_utc": "2024-01-15T14:30:00.000000Z",
  "phases_total": 11,
  "phases_success": 11,
  "questions_total": 305,
  "questions_answered": 305,
  "evidence_records": 1250,
  "monolith_hash": "abc123...",
  "questionnaire_hash": "def456...",
  "catalog_hash": "789abc...",
  "method_map_hash": "def012...",
  "input_pdf_hash": "345678...",
  "code_signature": {
    "core.py": "9a8b7c...",
    "executors.py": "6d5e4f...",
    "factory.py": "3c2b1a..."
  },
  "artifacts_manifest": {
    "content_stream.arrow": "hash1...",
    "metadata.json": "hash2..."
  }
}
```

## Troubleshooting

### No proof.json generated?

Check that:
- All 11 phases completed successfully
- No phases were aborted
- Output directory has artifacts

### Hash mismatch?

This means the proof was tampered with or corrupted:
- Do NOT trust this execution
- Re-run the pipeline to generate fresh proof

### Questions mismatch?

If `questions_answered < questions_total`:
- Some questions failed during execution
- Check phase 2 (Micro Questions) logs for errors
- This is still considered a successful run if all phases completed

## Implementation Notes

### FIXME Items

The current implementation has some known limitations:

1. **Method Map Hash**: Currently uses a placeholder derived from the questionnaire since `method_map` is not separately exposed in `ProcessorBundle`. Future versions should expose this separately.

2. **Question Counts**: Extracted from both:
   - Questionnaire monolith (`blocks.micro_questions`)
   - Phase 2 execution results
   
   These should always match, but are verified independently.

3. **Evidence Counts**: Counted across all phase results that contain items with `evidence` attributes. May not capture all evidence types.

## Related Files

- `src/saaaaaa/utils/proof_generator.py` - Core proof generation logic
- `run_complete_analysis_plan1.py` - Runner that generates proofs
- `tests/test_proof_generator.py` - Test suite (14 tests)

## References

- SHA-256: [NIST FIPS 180-4](https://csrc.nist.gov/publications/detail/fips/180/4/final)
- JSON Serialization: [RFC 8259](https://tools.ietf.org/html/rfc8259)
