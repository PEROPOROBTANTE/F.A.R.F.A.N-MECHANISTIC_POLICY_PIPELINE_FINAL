# F.A.R.F.A.N Test Plan (Plan de Prueba)

**Framework for Advanced Retrieval of Administrative Narratives**

## Document Information

- **Version**: 1.0.0
- **Date**: 2025-11-18
- **Status**: Active
- **Purpose**: Comprehensive end-to-end testing plan for F.A.R.F.A.N pipeline validation

---

## Table of Contents

1. [Test Objectives](#test-objectives)
2. [Test Environment](#test-environment)
3. [Test Data](#test-data)
4. [Test Cases](#test-cases)
5. [Verification Commands](#verification-commands)
6. [Success Criteria](#success-criteria)
7. [Troubleshooting](#troubleshooting)

---

## Test Objectives

### Primary Objectives

1. **Verify Complete Pipeline Execution**: Ensure all 11 phases of the orchestrator execute successfully
2. **Validate Cryptographic Integrity**: Confirm proof generation and verification mechanisms work correctly
3. **Test Dependency Resolution**: Verify all dependencies are correctly installed and functional
4. **Validate Determinism**: Ensure reproducible results across multiple runs
5. **Verify Data Quality**: Confirm provenance completeness, chunk quality, and structural consistency

### Secondary Objectives

1. Test individual producer modules independently
2. Validate signal system operation (memory:// transport)
3. Verify artifact generation and integrity hashing
4. Test error handling and graceful degradation
5. Validate questionnaire integrity protocol

---

## Test Environment

### Prerequisites

```bash
# 1. Python version
python3.12 --version
# Expected: Python 3.12.x

# 2. Virtual environment activated
which python
# Expected: /path/to/farfan-env/bin/python

# 3. Dependencies installed
pip list | grep -E "transformers|sentence-transformers|pymc|scikit-learn"
# Expected: All packages with correct versions
```

### Environment Setup

```bash
# Activate virtual environment
source farfan-env/bin/activate

# Verify installation
python verify_dependencies.py

# Expected output:
# ✓ All dependencies verified
# ✓ 22/22 classes loaded successfully
```

---

## Test Data

### Available Test Plans

| Plan ID | File Path | Size | Pages | Description |
|---------|-----------|------|-------|-------------|
| Plan_1 | data/plans/Plan_1.pdf | ~500KB | ~50 | Primary test plan |
| Plan_2 | data/plans/Plan_2.pdf | ~300KB | ~30 | Secondary test plan |
| Plan_3 | data/plans/Plan_3.pdf | ~400KB | ~40 | Tertiary test plan |

### Test Plan Selection

For initial testing, use **Plan_1.pdf** as it provides comprehensive coverage of policy structures.

```bash
# Verify test data exists
ls -lh data/plans/Plan_1.pdf

# Expected output:
# -rw-r--r-- 1 user user 500K Nov 17 10:00 data/plans/Plan_1.pdf
```

---

## Test Cases

### TC-001: Dependency Verification

**Objective**: Verify all dependencies are correctly installed

**Command**:
```bash
python verify_dependencies.py
```

**Expected Output**:
```
======================================================================
1. Checking Python Version
======================================================================
✓ Python 3.12.x

======================================================================
2. Checking Core NLP Dependencies
======================================================================
✓ transformers: NLP transformers - 4.41.2
✓ sentence_transformers: Semantic embeddings - 3.1.0
✓ spacy: NLP framework - 3.8.3

======================================================================
3. Checking PDF Processing Dependencies
======================================================================
✓ PyMuPDF: PDF document processing
✓ tabula-py: Table extraction from PDFs
✓ camelot-py: Complex table extraction
✓ pdfplumber: PDF text and layout

======================================================================
4. Checking NLP Dependencies
======================================================================
✓ sentencepiece: Tokenization for transformers
✓ tiktoken: OpenAI tokenizer
✓ fuzzywuzzy: Fuzzy string matching

======================================================================
6. Loading Class Registry
======================================================================
✓ Successfully loaded 22 classes

Passed: 5/6 checks
```

**Pass Criteria**:
- At least 5/6 checks passing
- All 22 classes loaded successfully
- No critical import errors

---

### TC-002: Questionnaire Integrity Verification

**Objective**: Verify questionnaire monolith integrity and hash validation

**Command**:
```bash
python3 -c "
from saaaaaa.core.orchestrator.questionnaire import load_questionnaire
q = load_questionnaire()
print(f'✓ Questionnaire loaded successfully')
print(f'  Micro questions: {q.micro_question_count}')
print(f'  Total questions: {q.total_question_count}')
print(f'  SHA256: {q.sha256[:16]}...')
print(f'✓ Hash validation passed')
"
```

**Expected Output**:
```
✓ Questionnaire loaded successfully
  Micro questions: 300
  Total questions: 300
  SHA256: [16-char hash]...
✓ Hash validation passed
```

**Pass Criteria**:
- No hash mismatch errors
- 300 micro questions loaded
- SHA256 verification successful

---

### TC-003: SPC Ingestion Pipeline (Phase 1)

**Objective**: Test Smart Policy Chunks ingestion pipeline

**Command**:
```bash
python3 << 'EOF'
import asyncio
from pathlib import Path
from saaaaaa.processing.spc_ingestion import CPPIngestionPipeline

async def test_spc():
    input_path = Path('data/plans/Plan_1.pdf')
    pipeline = CPPIngestionPipeline(questionnaire_path=None)

    print('🔄 Starting SPC ingestion...')
    cpp = await pipeline.process(
        document_path=input_path,
        document_id='TEST_Plan_1',
        title='Test Plan 1',
        max_chunks=50
    )

    if cpp:
        chunks = len(cpp.chunk_graph.chunks) if cpp.chunk_graph else 0
        print(f'✓ SPC ingestion completed')
        print(f'  Chunks generated: {chunks}')
        print(f'  Schema version: {cpp.schema_version}')

        if cpp.quality_metrics:
            print(f'  Provenance: {cpp.quality_metrics.provenance_completeness:.2%}')
            print(f'  Structural consistency: {cpp.quality_metrics.structural_consistency:.2%}')

        print('\n✅ TEST PASSED: SPC Ingestion')
        return True
    else:
        print('❌ TEST FAILED: SPC ingestion returned None')
        return False

asyncio.run(test_spc())
EOF
```

**Expected Output**:
```
🔄 Starting SPC ingestion...
✓ SPC ingestion completed
  Chunks generated: 45-50
  Schema version: v3.0
  Provenance: 100.00%
  Structural consistency: 100.00%

✅ TEST PASSED: SPC Ingestion
```

**Pass Criteria**:
- SPC ingestion completes without errors
- At least 40 chunks generated
- Provenance completeness = 100%
- Schema version = v3.0

---

### TC-004: Complete Pipeline Execution (End-to-End)

**Objective**: Execute complete F.A.R.F.A.N pipeline from PDF to results with cryptographic proof

**Command**:
```bash
python scripts/run_policy_pipeline_verified.py \
    --plan data/plans/Plan_1.pdf \
    --artifacts-dir artifacts/test_plan1
```

**Expected Output** (abbreviated):
```
================================================================================
F.A.R.F.A.N VERIFIED POLICY PIPELINE RUNNER
Framework for Advanced Retrieval of Administrativa Narratives
================================================================================
Plan: /path/to/data/plans/Plan_1.pdf
Artifacts: /path/to/artifacts/test_plan1
================================================================================

CLAIM: {"timestamp":"...","claim_type":"start","component":"pipeline",...}
CLAIM: {"timestamp":"...","claim_type":"hash","component":"input_verification",...}
CLAIM: {"timestamp":"...","claim_type":"complete","component":"spc_ingestion",...}
CLAIM: {"timestamp":"...","claim_type":"complete","component":"spc_adapter",...}
CLAIM: {"timestamp":"...","claim_type":"complete","component":"orchestrator",...}

================================================================================
PIPELINE_VERIFIED=1
Manifest: artifacts/test_plan1/verification_manifest.json
HMAC: [16-char hash]...
Phases: 11 completed, 0 failed
Artifacts: 4
================================================================================

================================================================================
PIPELINE_VERIFIED=1
Status: SUCCESS
================================================================================
```

**Verification Steps**:

```bash
# 1. Check verification manifest exists
test -f artifacts/test_plan1/verification_manifest.json && echo "✓ Manifest exists"

# 2. Verify HMAC integrity
python3 << 'EOF'
import json
from saaaaaa.core.orchestrator.verification_manifest import verify_manifest_integrity

with open('artifacts/test_plan1/verification_manifest.json') as f:
    manifest = json.load(f)

is_valid, message = verify_manifest_integrity(manifest, "default-dev-key-change-in-production")
print(f"{'✓' if is_valid else '✗'} HMAC Integrity: {message}")
EOF

# 3. Check artifacts generated
ls -lh artifacts/test_plan1/
# Expected: verification_manifest.json, execution_claims.json, cpp_metadata.json, etc.

# 4. Verify execution claims
jq '.[] | select(.claim_type=="complete") | .component' artifacts/test_plan1/execution_claims.json
# Expected: Multiple "complete" claims for each phase
```

**Pass Criteria**:
- Pipeline exits with code 0 (success)
- PIPELINE_VERIFIED=1 in output
- 11 phases completed, 0 failed
- verification_manifest.json generated with valid HMAC
- At least 4 artifacts generated

---

### TC-005: Determinism Verification

**Objective**: Verify pipeline produces identical results across multiple runs

**Command**:
```bash
# Run 1
python scripts/run_policy_pipeline_verified.py \
    --plan data/plans/Plan_1.pdf \
    --artifacts-dir artifacts/determinism_run1

# Run 2
python scripts/run_policy_pipeline_verified.py \
    --plan data/plans/Plan_1.pdf \
    --artifacts-dir artifacts/determinism_run2

# Compare hashes
python3 << 'EOF'
import json

with open('artifacts/determinism_run1/verification_manifest.json') as f:
    manifest1 = json.load(f)

with open('artifacts/determinism_run2/verification_manifest.json') as f:
    manifest2 = json.load(f)

hash1 = manifest1.get('pipeline_hash', '')
hash2 = manifest2.get('pipeline_hash', '')

if hash1 == hash2:
    print(f'✓ Determinism verified: Hashes match')
    print(f'  Hash: {hash1[:16]}...')
else:
    print(f'✗ Determinism failed: Hashes differ')
    print(f'  Run 1: {hash1[:16]}...')
    print(f'  Run 2: {hash2[:16]}...')
EOF
```

**Pass Criteria**:
- Both runs complete successfully
- Pipeline hashes match between runs
- Input PDF hashes match
- Number of phases completed matches

---

### TC-006: Signal System Verification

**Objective**: Verify cross-cut signals system operates correctly

**Command**:
```bash
python3 << 'EOF'
from saaaaaa.core.orchestrator.signals import SignalClient

# Initialize signal client
client = SignalClient(base_url="memory://")

# Register test signal
test_signal = {
    "patterns": ["test_pattern_1", "test_pattern_2"],
    "indicators": ["indicator_1"],
    "thresholds": {"min_score": 0.85}
}

client.register_memory_signal("TEST_PA01", test_signal)
print("✓ Signal registered: TEST_PA01")

# Fetch signal
fetched = client.fetch_signal_pack("TEST_PA01")
if fetched:
    print("✓ Signal fetched successfully")
    print(f"  Patterns: {len(fetched.get('patterns', []))}")
    print(f"  Indicators: {len(fetched.get('indicators', []))}")
else:
    print("✗ Signal fetch failed")

print("\n✅ TEST PASSED: Signal System")
EOF
```

**Expected Output**:
```
✓ Signal registered: TEST_PA01
✓ Signal fetched successfully
  Patterns: 2
  Indicators: 1

✅ TEST PASSED: Signal System
```

**Pass Criteria**:
- Signal registration succeeds
- Signal retrieval returns expected data
- No transport errors

---

### TC-007: Individual Producer Testing

**Objective**: Test individual producer modules independently

**Command**:
```bash
# Run all producers
bash scripts/run_all_producers.sh

# Or test individual producers
python3 << 'EOF'
from saaaaaa.core.orchestrator.factory import build_processor

processor = build_processor()
print(f"✓ Processor bundle created")
print(f"  Method executor: {type(processor.method_executor).__name__}")
print(f"  Questionnaire: {len(processor.questionnaire)} keys")
print(f"  Catalog: {len(processor.factory.catalog)} keys")
print("\n✅ TEST PASSED: Producer Initialization")
EOF
```

**Pass Criteria**:
- Processor bundle created successfully
- All expected keys present in questionnaire and catalog
- No import errors

---

### TC-008: Contract Validation

**Objective**: Verify contract enforcement and boundary validation

**Command**:
```bash
# Run contract validation
bash scripts/validate_contracts_local.sh

# Or use Python directly
python3 << 'EOF'
import sys
sys.path.insert(0, 'src')

from saaaaaa.core.orchestrator.provider import ContractProvider

provider = ContractProvider()
print("✓ ContractProvider initialized")
print("✓ Boundary enforcement active")
print("\n✅ TEST PASSED: Contract System")
EOF
```

**Pass Criteria**:
- No architectural violations detected
- Boundary checks pass
- Contract enforcement active

---

### TC-009: Artifact Integrity Verification

**Objective**: Verify all generated artifacts have valid SHA256 hashes

**Command**:
```bash
# After running TC-004, verify artifact hashes
python3 << 'EOF'
import json
import hashlib
from pathlib import Path

manifest_path = Path('artifacts/test_plan1/verification_manifest.json')
with open(manifest_path) as f:
    manifest = json.load(f)

artifacts = manifest.get('artifacts', {})
print(f"Verifying {len(artifacts)} artifacts...\n")

all_valid = True
for artifact_path, expected_hash in artifacts.items():
    if Path(artifact_path).exists():
        # Recompute hash
        sha256 = hashlib.sha256()
        with open(artifact_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        actual_hash = sha256.hexdigest()

        if actual_hash == expected_hash:
            print(f"✓ {Path(artifact_path).name}: Hash verified")
        else:
            print(f"✗ {Path(artifact_path).name}: Hash mismatch!")
            all_valid = False
    else:
        print(f"✗ {Path(artifact_path).name}: File not found!")
        all_valid = False

if all_valid:
    print("\n✅ TEST PASSED: All artifact hashes verified")
else:
    print("\n✗ TEST FAILED: Some artifacts failed verification")
EOF
```

**Pass Criteria**:
- All artifact files exist
- All SHA256 hashes match expected values
- No missing or corrupted artifacts

---

### TC-010: Stress Test (Multiple Plans)

**Objective**: Test system stability across multiple plan analyses

**Command**:
```bash
# Process all three test plans sequentially
for plan_id in 1 2 3; do
    echo "========================================="
    echo "Processing Plan_${plan_id}.pdf"
    echo "========================================="

    python scripts/run_policy_pipeline_verified.py \
        --plan data/plans/Plan_${plan_id}.pdf \
        --artifacts-dir artifacts/stress_test_plan${plan_id}

    if [ $? -eq 0 ]; then
        echo "✓ Plan_${plan_id} completed successfully"
    else
        echo "✗ Plan_${plan_id} failed"
        exit 1
    fi

    echo ""
done

echo "✅ ALL PLANS PROCESSED SUCCESSFULLY"
```

**Pass Criteria**:
- All 3 plans process without errors
- Each generates valid verification manifest
- No memory leaks or resource exhaustion
- Consistent performance across runs

---

## Verification Commands

### Quick Health Check

```bash
# One-liner to verify system is operational
python3 -c "from saaaaaa.core.orchestrator.questionnaire import load_questionnaire; q = load_questionnaire(); print(f'✓ System operational: {q.total_question_count} questions loaded')"
```

### Dependency Check

```bash
# Verify critical dependencies
python3 -c "
import transformers
import sentence_transformers
import pymc
import scikit_learn as sklearn

print('✓ transformers:', transformers.__version__)
print('✓ sentence_transformers:', sentence_transformers.__version__)
print('✓ pymc:', pymc.__version__)
print('✓ scikit-learn:', sklearn.__version__)
"
```

### Class Registry Check

```bash
# Verify all 22 classes can be imported
python3 -c "
from saaaaaa.core.orchestrator.class_registry import ClassRegistry

registry = ClassRegistry()
classes = registry.get_all_classes()
print(f'✓ {len(classes)} classes registered')

for name, cls in classes.items():
    print(f'  ✓ {name}')
"
```

---

## Success Criteria

### Minimum Passing Criteria

For a test run to be considered successful, the following must be true:

| Criterion | Requirement | Verification |
|-----------|-------------|--------------|
| **Dependencies** | All critical dependencies installed | TC-001 passes |
| **Questionnaire** | Hash validation successful | TC-002 passes |
| **SPC Ingestion** | Provenance completeness = 100% | TC-003 passes |
| **Pipeline Execution** | PIPELINE_VERIFIED=1 | TC-004 passes |
| **Phases** | 11/11 phases completed | TC-004 passes |
| **Artifacts** | All artifacts generated with valid hashes | TC-009 passes |
| **Integrity** | HMAC verification passes | TC-004 verification |

### Optional Criteria

| Criterion | Requirement | Verification |
|-----------|-------------|--------------|
| **Determinism** | Identical hashes across runs | TC-005 passes |
| **Signals** | Signal system operational | TC-006 passes |
| **Stress** | Multiple plans process successfully | TC-010 passes |

---

## Troubleshooting

### Common Issues

#### Issue 1: Import Errors

**Symptom**:
```
ModuleNotFoundError: No module named 'transformers'
```

**Solution**:
```bash
# Ensure virtual environment is activated
source farfan-env/bin/activate

# Reinstall dependencies
bash install.sh
```

#### Issue 2: TorchTensorParallelPlugin Error

**Symptom**:
```
ImportError: cannot import name 'TorchTensorParallelPlugin' from 'accelerate'
```

**Solution**:
```bash
# Verify correct versions are installed
pip list | grep -E "transformers|accelerate"

# Should show:
# transformers==4.41.2
# accelerate==1.2.1

# If incorrect, reinstall
pip install --force-reinstall transformers==4.41.2 sentence-transformers==3.1.0
```

#### Issue 3: Questionnaire Hash Mismatch

**Symptom**:
```
HashValidationError: Questionnaire hash mismatch
```

**Solution**:
```bash
# Check if questionnaire file was modified
git status data/questionnaire_monolith.json

# If modified, revert to canonical version
git checkout data/questionnaire_monolith.json
```

#### Issue 4: Plan_1.pdf Not Found

**Symptom**:
```
FileNotFoundError: [Errno 2] No such file or directory: 'data/plans/Plan_1.pdf'
```

**Solution**:
```bash
# Verify file exists
ls -lh data/plans/Plan_1.pdf

# If missing, check git repository
git status data/plans/

# Ensure you're in the correct directory
pwd
# Should end with: F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE_FINAL
```

#### Issue 5: Low Memory During Execution

**Symptom**:
```
MemoryError: Unable to allocate array
```

**Solution**:
```bash
# Reduce max_chunks parameter
# Edit script to use max_chunks=25 instead of 50

# Or increase available memory (Docker/VM)
# Recommended: 16GB RAM minimum
```

---

## Test Execution Log Template

Use this template to record test results:

```markdown
### Test Execution Report

**Date**: YYYY-MM-DD
**Tester**: [Your Name]
**Environment**: [OS, Python version]
**Branch**: [git branch name]

| Test Case | Status | Duration | Notes |
|-----------|--------|----------|-------|
| TC-001 | ✓ PASS | 5s | All dependencies verified |
| TC-002 | ✓ PASS | 2s | Hash validation successful |
| TC-003 | ✓ PASS | 45s | 48 chunks generated |
| TC-004 | ✓ PASS | 120s | 11/11 phases completed |
| TC-005 | ✓ PASS | 240s | Hashes match |
| TC-006 | ✓ PASS | 3s | Signal system operational |
| TC-007 | ✓ PASS | 10s | All producers initialized |
| TC-008 | ✓ PASS | 5s | No violations detected |
| TC-009 | ✓ PASS | 8s | All artifacts verified |
| TC-010 | ✗ SKIP | - | Optional stress test |

**Overall Result**: PASS (9/9 required tests passed)

**Artifacts Generated**:
- verification_manifest.json (SHA256: abc123...)
- execution_claims.json (SHA256: def456...)
- cpp_metadata.json (SHA256: ghi789...)

**Issues Encountered**: None

**Recommendations**: All systems operational, ready for production use.
```

---

## Automated Test Suite

### Run All Required Tests

Create a test runner script:

```bash
#!/bin/bash
# test_suite.sh - Run all required test cases

set -e

echo "========================================="
echo "F.A.R.F.A.N Automated Test Suite"
echo "========================================="
echo ""

# TC-001: Dependencies
echo "Running TC-001: Dependency Verification..."
python verify_dependencies.py > /tmp/tc001.log 2>&1
if grep -q "Passed: [56]/6" /tmp/tc001.log; then
    echo "✓ TC-001 PASSED"
else
    echo "✗ TC-001 FAILED"
    cat /tmp/tc001.log
    exit 1
fi

# TC-002: Questionnaire
echo "Running TC-002: Questionnaire Integrity..."
python3 -c "from saaaaaa.core.orchestrator.questionnaire import load_questionnaire; q = load_questionnaire()" 2>&1
if [ $? -eq 0 ]; then
    echo "✓ TC-002 PASSED"
else
    echo "✗ TC-002 FAILED"
    exit 1
fi

# TC-004: Full Pipeline
echo "Running TC-004: Complete Pipeline..."
python scripts/run_policy_pipeline_verified.py \
    --plan data/plans/Plan_1.pdf \
    --artifacts-dir artifacts/test_suite_run > /tmp/tc004.log 2>&1

if grep -q "PIPELINE_VERIFIED=1" /tmp/tc004.log; then
    echo "✓ TC-004 PASSED"
else
    echo "✗ TC-004 FAILED"
    cat /tmp/tc004.log
    exit 1
fi

echo ""
echo "========================================="
echo "✅ ALL REQUIRED TESTS PASSED"
echo "========================================="
```

Make executable and run:

```bash
chmod +x test_suite.sh
./test_suite.sh
```

---

## References

- [OPERATIONAL_GUIDE.md](OPERATIONAL_GUIDE.md) - Complete operational documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture details
- [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) - Installation instructions
- [README.md](README.md) - Project overview

---

**Last Updated**: 2025-11-18
**Document Version**: 1.0.0
**Maintained By**: F.A.R.F.A.N Development Team
