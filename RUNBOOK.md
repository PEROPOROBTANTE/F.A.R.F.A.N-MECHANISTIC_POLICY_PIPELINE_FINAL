# F.A.R.F.A.N Operational Runbook

**Framework for Advanced Retrieval of Administrative Narratives**

**Version**: 1.0.0
**Date**: 2025-11-18
**Status**: Production Ready

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [System Launch](#system-launch)
3. [Health Checks](#health-checks)
4. [Pipeline Execution](#pipeline-execution)
5. [Monitoring & Diagnostics](#monitoring--diagnostics)
6. [Maintenance Operations](#maintenance-operations)
7. [Troubleshooting](#troubleshooting)
8. [Emergency Procedures](#emergency-procedures)
9. [System Shutdown](#system-shutdown)

---

## Quick Start

### Fastest Path to Running Analysis

```bash
# 1. Activate environment
source farfan-env/bin/activate

# 2. Verify system health
python verify_dependencies.py

# 3. Run analysis
python scripts/run_policy_pipeline_verified.py \
    --plan data/plans/Plan_1.pdf \
    --artifacts-dir artifacts/plan1
```

### Expected Time

- **Environment Activation**: < 1 second
- **Health Check**: 5-10 seconds
- **Pipeline Execution**: 60-180 seconds (depending on plan size)

---

## System Launch

### Pre-Launch Checklist

```bash
# 1. Verify Python version
python3.12 --version
# Expected: Python 3.12.x

# 2. Check virtual environment exists
ls -la farfan-env/
# Expected: Directory exists with bin/, lib/, etc.

# 3. Verify test data available
ls -lh data/plans/Plan_*.pdf
# Expected: At least Plan_1.pdf exists

# 4. Check disk space (need at least 2GB free)
df -h .
# Expected: At least 2GB available
```

### Launch Sequence

#### Step 1: Activate Virtual Environment

```bash
source farfan-env/bin/activate

# Verify activation
echo $VIRTUAL_ENV
# Expected: /path/to/farfan-env

which python
# Expected: /path/to/farfan-env/bin/python
```

#### Step 2: Set Environment Variables (Optional)

```bash
# Enable debug mode (optional)
export PIPELINE_DEBUG=1

# Set custom manifest secret key (production)
export MANIFEST_SECRET_KEY="your-production-secret-key-here"

# Set memory limits (optional)
export PYTHONHASHSEED=42  # For determinism
```

#### Step 3: Run Pre-Flight Checks

```bash
# Quick health check
python3 -c "
from saaaaaa.core.orchestrator.questionnaire import load_questionnaire
q = load_questionnaire()
print(f'✓ System Ready: {q.total_question_count} questions loaded')
print(f'✓ SHA256: {q.sha256[:16]}...')
"
```

**Expected Output**:
```
✓ System Ready: 300 questions loaded
✓ SHA256: [16-char hash]...
```

#### Step 4: Launch Pipeline

```bash
# Standard execution
python scripts/run_policy_pipeline_verified.py \
    --plan data/plans/Plan_1.pdf \
    --artifacts-dir artifacts/plan1

# With specific plan
python scripts/run_policy_pipeline_verified.py \
    --plan data/plans/Plan_2.pdf \
    --artifacts-dir artifacts/plan2

# Or use the simpler demonstration script
python scripts/run_complete_analysis_plan1.py
```

---

## Health Checks

### System Health Check Commands

#### HC-001: Overall System Health

```bash
#!/bin/bash
# Full system health check

echo "========================================="
echo "F.A.R.F.A.N System Health Check"
echo "========================================="
echo ""

# Python version
echo "1. Python Version:"
python3.12 --version || echo "✗ Python 3.12 not found"
echo ""

# Virtual environment
echo "2. Virtual Environment:"
if [ -n "$VIRTUAL_ENV" ]; then
    echo "✓ Activated: $VIRTUAL_ENV"
else
    echo "✗ Not activated - run: source farfan-env/bin/activate"
fi
echo ""

# Dependencies
echo "3. Critical Dependencies:"
python verify_dependencies.py 2>&1 | grep -E "✓|✗|Passed"
echo ""

# Questionnaire
echo "4. Questionnaire Integrity:"
python3 -c "from saaaaaa.core.orchestrator.questionnaire import load_questionnaire; q = load_questionnaire(); print(f'✓ {q.total_question_count} questions loaded')" 2>&1
echo ""

# Test data
echo "5. Test Data Availability:"
for plan in data/plans/Plan_1.pdf data/plans/Plan_2.pdf data/plans/Plan_3.pdf; do
    if [ -f "$plan" ]; then
        size=$(du -h "$plan" | cut -f1)
        echo "✓ $plan ($size)"
    else
        echo "✗ $plan (missing)"
    fi
done
echo ""

# Disk space
echo "6. Disk Space:"
df -h . | tail -1 | awk '{print "Available: " $4 " / " $2 " (" $5 " used)"}'
echo ""

# Memory
echo "7. Memory:"
free -h | grep "Mem:" | awk '{print "Available: " $7 " / " $2}'
echo ""

echo "========================================="
echo "Health Check Complete"
echo "========================================="
```

Save as `health_check.sh`:
```bash
chmod +x health_check.sh
./health_check.sh
```

#### HC-002: Dependency Check

```bash
# Quick dependency verification
python3 << 'EOF'
import sys

deps = {
    'transformers': '4.41.2',
    'sentence_transformers': '3.1.0',
    'accelerate': '1.2.1',
    'pymc': '5.16.2',
    'scikit_learn': '1.6.1',
}

all_ok = True
for module, expected_version in deps.items():
    try:
        mod = __import__(module)
        version = mod.__version__
        status = '✓' if version == expected_version else '⚠'
        print(f"{status} {module}: {version} (expected: {expected_version})")
        if version != expected_version:
            all_ok = False
    except ImportError:
        print(f"✗ {module}: NOT INSTALLED")
        all_ok = False

sys.exit(0 if all_ok else 1)
EOF
```

#### HC-003: Class Registry Check

```bash
# Verify all 22 classes can be imported
python3 << 'EOF'
from saaaaaa.core.orchestrator.class_registry import ClassRegistry

registry = ClassRegistry()
classes = registry.get_all_classes()

print(f"Class Registry: {len(classes)} classes")
print("")

expected = 22
if len(classes) >= expected:
    print(f"✓ All {len(classes)} classes registered")
    for name in sorted(classes.keys()):
        print(f"  ✓ {name}")
    exit(0)
else:
    print(f"✗ Only {len(classes)}/{expected} classes registered")
    exit(1)
EOF
```

#### HC-004: Signal System Check

```bash
# Verify signal system is operational
python3 << 'EOF'
from saaaaaa.core.orchestrator.signals import SignalClient

client = SignalClient(base_url="memory://")

# Test signal registration and retrieval
test_data = {"test": "data", "patterns": ["p1", "p2"]}
client.register_memory_signal("HC_TEST", test_data)

retrieved = client.fetch_signal_pack("HC_TEST")
if retrieved and retrieved.get("test") == "data":
    print("✓ Signal system operational (memory:// transport)")
    exit(0)
else:
    print("✗ Signal system failed")
    exit(1)
EOF
```

#### HC-005: File System Check

```bash
# Verify required directories exist and are writable
for dir in data/plans artifacts data/output; do
    if [ -d "$dir" ]; then
        if [ -w "$dir" ]; then
            echo "✓ $dir (exists, writable)"
        else
            echo "⚠ $dir (exists, NOT writable)"
        fi
    else
        echo "✗ $dir (missing)"
        mkdir -p "$dir" 2>/dev/null && echo "  Created $dir"
    fi
done
```

---

## Pipeline Execution

### Standard Execution Modes

#### Mode 1: Verified Pipeline (Recommended)

**Use Case**: Production analysis with cryptographic proof generation

```bash
python scripts/run_policy_pipeline_verified.py \
    --plan data/plans/Plan_1.pdf \
    --artifacts-dir artifacts/plan1
```

**Outputs**:
- `artifacts/plan1/verification_manifest.json` - Cryptographic manifest with HMAC
- `artifacts/plan1/execution_claims.json` - Structured execution log
- `artifacts/plan1/cpp_metadata.json` - SPC ingestion metadata
- `artifacts/plan1/preprocessed_doc_metadata.json` - Document processing metadata
- `artifacts/plan1/results_summary.json` - Analysis results summary

**Verification**:
```bash
# Check success
grep "PIPELINE_VERIFIED=1" artifacts/plan1/verification_manifest.json

# Verify HMAC integrity
python3 << 'EOF'
import json
from saaaaaa.core.orchestrator.verification_manifest import verify_manifest_integrity

with open('artifacts/plan1/verification_manifest.json') as f:
    manifest = json.load(f)

is_valid, message = verify_manifest_integrity(manifest, "default-dev-key-change-in-production")
print(f"HMAC Verification: {message}")
EOF
```

#### Mode 2: Simple Analysis (Development)

**Use Case**: Quick testing and development

```bash
python scripts/run_complete_analysis_plan1.py
```

**Outputs**:
- Console output with phase-by-phase results
- Optional: Cryptographic proof if all phases succeed
- Artifacts in `data/output/cpp_plan_1/`

#### Mode 3: Custom Pipeline (Advanced)

**Use Case**: Custom analysis with specific parameters

```bash
python3 << 'EOF'
import asyncio
from pathlib import Path
from saaaaaa.processing.spc_ingestion import CPPIngestionPipeline
from saaaaaa.utils.spc_adapter import SPCAdapter
from saaaaaa.core.orchestrator import Orchestrator
from saaaaaa.core.orchestrator.factory import build_processor

async def custom_pipeline():
    # Step 1: SPC Ingestion
    input_path = Path('data/plans/Plan_1.pdf')
    cpp_pipeline = CPPIngestionPipeline(questionnaire_path=None)
    cpp = await cpp_pipeline.process(
        document_path=input_path,
        document_id='Custom_Plan',
        title='Custom Analysis',
        max_chunks=100  # Adjust as needed
    )

    # Step 2: Adaptation
    adapter = SPCAdapter()
    preprocessed = adapter.to_preprocessed_document(cpp, document_id='Custom_Plan')

    # Step 3: Orchestration
    processor = build_processor()
    orchestrator = Orchestrator(
        monolith=processor.questionnaire,
        catalog=processor.factory.catalog
    )

    results = await orchestrator.process_development_plan_async(
        pdf_path=str(input_path),
        preprocessed_document=preprocessed
    )

    # Display results
    successful = sum(1 for r in results if r.success)
    print(f"Completed: {successful}/{len(results)} phases")

    return results

asyncio.run(custom_pipeline())
EOF
```

### Batch Processing

```bash
#!/bin/bash
# Process multiple plans in sequence

PLANS=(
    "data/plans/Plan_1.pdf"
    "data/plans/Plan_2.pdf"
    "data/plans/Plan_3.pdf"
)

for i in "${!PLANS[@]}"; do
    plan="${PLANS[$i]}"
    plan_num=$((i + 1))

    echo "========================================="
    echo "Processing Plan $plan_num: $plan"
    echo "========================================="

    python scripts/run_policy_pipeline_verified.py \
        --plan "$plan" \
        --artifacts-dir "artifacts/batch_run_plan${plan_num}"

    if [ $? -eq 0 ]; then
        echo "✓ Plan $plan_num completed successfully"
    else
        echo "✗ Plan $plan_num failed"
        exit 1
    fi

    echo ""
done

echo "✅ Batch processing completed: ${#PLANS[@]} plans"
```

---

## Monitoring & Diagnostics

### Real-Time Monitoring

#### Monitor Pipeline Execution

```bash
# Run pipeline with output to log file
python scripts/run_policy_pipeline_verified.py \
    --plan data/plans/Plan_1.pdf \
    --artifacts-dir artifacts/plan1 \
    2>&1 | tee pipeline_execution.log

# Monitor in real-time (in another terminal)
tail -f pipeline_execution.log | grep "CLAIM:"
```

#### Monitor System Resources

```bash
#!/bin/bash
# Monitor resource usage during pipeline execution

echo "Timestamp,CPU%,Memory(MB),Disk(MB)" > resource_monitor.csv

while true; do
    timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    cpu=$(ps aux | grep "python.*run_policy" | grep -v grep | awk '{print $3}')
    mem=$(ps aux | grep "python.*run_policy" | grep -v grep | awk '{print $6/1024}')
    disk=$(du -sm artifacts/ | cut -f1)

    echo "$timestamp,$cpu,$mem,$disk" >> resource_monitor.csv
    sleep 5
done
```

### Diagnostic Commands

#### DG-001: Execution Trace Analysis

```bash
# Analyze execution claims from completed run
python3 << 'EOF'
import json
from datetime import datetime

with open('artifacts/plan1/execution_claims.json') as f:
    claims = json.load(f)

print(f"Total claims: {len(claims)}")
print("")

# Group by claim_type
by_type = {}
for claim in claims:
    ct = claim['claim_type']
    by_type[ct] = by_type.get(ct, 0) + 1

print("Claims by type:")
for ct, count in sorted(by_type.items()):
    print(f"  {ct}: {count}")
print("")

# Show timeline
print("Execution timeline:")
for claim in claims[:10]:  # First 10 claims
    ts = claim['timestamp']
    component = claim['component']
    msg = claim['message'][:50]
    print(f"  {ts} | {component:20s} | {msg}")
EOF
```

#### DG-002: Phase Performance Analysis

```bash
# Analyze phase execution times
python3 << 'EOF'
import json

with open('artifacts/plan1/verification_manifest.json') as f:
    manifest = json.load(f)

phases = manifest.get('phases', [])

print(f"Phase Performance Analysis")
print("=" * 60)
print("")

for phase in phases:
    name = phase.get('phase_name', 'Unknown')
    status = phase.get('status', 'Unknown')
    duration = phase.get('duration_seconds', 0)

    status_icon = '✓' if status == 'success' else '✗'
    print(f"{status_icon} {name:40s} {duration:6.2f}s")

print("")
EOF
```

#### DG-003: Artifact Inventory

```bash
# List all artifacts with sizes and hashes
python3 << 'EOF'
import json
from pathlib import Path

manifest_path = Path('artifacts/plan1/verification_manifest.json')
with open(manifest_path) as f:
    manifest = json.load(f)

artifacts = manifest.get('artifacts', {})

print(f"Artifact Inventory ({len(artifacts)} items)")
print("=" * 80)
print("")

for artifact_path, artifact_hash in artifacts.items():
    path = Path(artifact_path)
    if path.exists():
        size = path.stat().st_size / 1024  # KB
        print(f"✓ {path.name:40s} {size:8.1f} KB  {artifact_hash[:16]}...")
    else:
        print(f"✗ {path.name:40s} MISSING")

print("")
EOF
```

#### DG-004: Error Analysis

```bash
# Extract and analyze errors from execution
python3 << 'EOF'
import json

with open('artifacts/plan1/execution_claims.json') as f:
    claims = json.load(f)

errors = [c for c in claims if c['claim_type'] == 'error']

if errors:
    print(f"Found {len(errors)} errors:")
    print("")
    for err in errors:
        print(f"Component: {err['component']}")
        print(f"Message: {err['message']}")
        if 'data' in err and 'traceback' in err['data']:
            print(f"Traceback: {err['data']['traceback'][:200]}...")
        print("-" * 60)
else:
    print("✓ No errors found in execution")
EOF
```

---

## Maintenance Operations

### Regular Maintenance Tasks

#### MT-001: Clear Old Artifacts

```bash
# Remove artifacts older than 7 days
find artifacts/ -type f -mtime +7 -delete
echo "✓ Cleaned artifacts older than 7 days"

# Or clear all artifacts (use with caution)
# rm -rf artifacts/*
# echo "✓ All artifacts cleared"
```

#### MT-002: Update Dependencies

```bash
# Backup current environment
pip freeze > requirements.backup.txt

# Update packages (careful - test afterwards)
pip install --upgrade pip setuptools wheel

# Reinstall with exact versions
bash install.sh

# Verify installation
python verify_dependencies.py
```

#### MT-003: Verify Questionnaire Integrity

```bash
# Check for unauthorized modifications
python3 << 'EOF'
import json
import hashlib

# Load questionnaire
with open('data/questionnaire_monolith.json', 'r') as f:
    data = json.load(f)

# Compute hash
serialized = json.dumps(data, sort_keys=True, ensure_ascii=True, separators=(',', ':'))
computed_hash = hashlib.sha256(serialized.encode()).hexdigest()

# Load expected hash from code
from saaaaaa.core.orchestrator.questionnaire import EXPECTED_HASH

if computed_hash == EXPECTED_HASH:
    print(f"✓ Questionnaire integrity verified")
    print(f"  Hash: {computed_hash[:16]}...")
else:
    print(f"✗ QUESTIONNAIRE MODIFIED!")
    print(f"  Expected: {EXPECTED_HASH[:16]}...")
    print(f"  Computed: {computed_hash[:16]}...")
    print(f"  WARNING: Analysis results may not be reproducible!")
EOF
```

#### MT-004: System Audit

```bash
# Run comprehensive system audit
python scripts/comprehensive_pipeline_audit.py
```

#### MT-005: Test Suite Execution

```bash
# Run automated test suite (see TEST_PLAN.md)
bash test_suite.sh
```

### Performance Optimization

#### Optimize SPC Chunk Generation

```bash
# Reduce chunks for faster processing (less detail)
# Edit scripts to use max_chunks=25

# Or increase for more detail (slower)
# Edit scripts to use max_chunks=100
```

#### Memory Optimization

```bash
# Set Python memory limits
export PYTHONHASHSEED=42
export MALLOC_TRIM_THRESHOLD_=100000

# Run with reduced memory footprint
python -X faulthandler scripts/run_policy_pipeline_verified.py \
    --plan data/plans/Plan_1.pdf \
    --artifacts-dir artifacts/plan1
```

---

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: Virtual Environment Not Activated

**Symptoms**:
```
python: command not found
ModuleNotFoundError: No module named 'saaaaaa'
```

**Solution**:
```bash
source farfan-env/bin/activate
```

#### Issue 2: Import Errors

**Symptoms**:
```
ImportError: cannot import name 'TorchTensorParallelPlugin'
ModuleNotFoundError: No module named 'transformers'
```

**Solution**:
```bash
# Verify correct versions
pip list | grep -E "transformers|accelerate|sentence-transformers"

# Reinstall if needed
bash install.sh
```

#### Issue 3: Out of Memory

**Symptoms**:
```
MemoryError: Unable to allocate array
Killed
```

**Solution**:
```bash
# Reduce chunk count
# Edit pipeline scripts to use max_chunks=25

# Or increase available memory
# Minimum: 8GB RAM
# Recommended: 16GB RAM
```

#### Issue 4: Plan_1.pdf Not Found

**Symptoms**:
```
FileNotFoundError: [Errno 2] No such file or directory: 'data/plans/Plan_1.pdf'
```

**Solution**:
```bash
# Verify you're in the correct directory
pwd
# Should end with: F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE_FINAL

# Check if file exists
ls -lh data/plans/Plan_1.pdf

# If missing, check git status
git status data/plans/
```

#### Issue 5: Pipeline Hangs

**Symptoms**:
- Pipeline runs for > 10 minutes with no output
- CPU usage drops to 0%

**Solution**:
```bash
# Kill pipeline
pkill -f "python.*run_policy"

# Check for deadlocks
python scripts/runtime_audit.py

# Restart with debug mode
export PIPELINE_DEBUG=1
python scripts/run_policy_pipeline_verified.py \
    --plan data/plans/Plan_1.pdf \
    --artifacts-dir artifacts/debug_run
```

### Debug Mode

```bash
# Enable all debug output
export PIPELINE_DEBUG=1
export PYTHONFAULTHANDLER=1

# Run with verbose logging
python -v scripts/run_policy_pipeline_verified.py \
    --plan data/plans/Plan_1.pdf \
    --artifacts-dir artifacts/debug_run 2>&1 | tee debug.log

# Analyze debug log
grep -i "error\|warning\|exception" debug.log
```

---

## Emergency Procedures

### Emergency Stop

```bash
# Stop all running pipelines
pkill -f "python.*run_policy"
pkill -f "python.*run_complete"

# Verify processes stopped
ps aux | grep python | grep -v grep

# Clean up temporary files
rm -rf /tmp/saaaaaa_*

echo "✓ Emergency stop completed"
```

### Recovery from Crash

```bash
# 1. Check for partial artifacts
ls -lh artifacts/

# 2. Remove incomplete runs
rm -rf artifacts/incomplete_run/

# 3. Verify system health
python verify_dependencies.py

# 4. Check questionnaire integrity
python3 -c "from saaaaaa.core.orchestrator.questionnaire import load_questionnaire; load_questionnaire()"

# 5. Restart pipeline
python scripts/run_policy_pipeline_verified.py \
    --plan data/plans/Plan_1.pdf \
    --artifacts-dir artifacts/recovery_run
```

### Data Corruption Recovery

```bash
# 1. Restore from git
git status data/
git checkout data/questionnaire_monolith.json

# 2. Verify integrity
python3 -c "from saaaaaa.core.orchestrator.questionnaire import load_questionnaire; load_questionnaire()"

# 3. Re-run analysis
python scripts/run_policy_pipeline_verified.py \
    --plan data/plans/Plan_1.pdf \
    --artifacts-dir artifacts/recovery_run
```

---

## System Shutdown

### Graceful Shutdown Procedure

```bash
#!/bin/bash
# Graceful system shutdown

echo "========================================="
echo "F.A.R.F.A.N Graceful Shutdown"
echo "========================================="
echo ""

# 1. Stop running pipelines (allow completion)
echo "1. Waiting for active pipelines to complete..."
# (Manual: Let current pipeline finish)

# 2. Verify no processes running
echo "2. Checking for active processes..."
active=$(ps aux | grep "python.*run_policy" | grep -v grep | wc -l)
if [ $active -gt 0 ]; then
    echo "   ⚠ $active pipeline(s) still running"
    echo "   Waiting 60 seconds..."
    sleep 60
fi

# 3. Archive recent artifacts (optional)
echo "3. Archiving recent artifacts..."
if [ -d artifacts/ ]; then
    tar -czf "artifacts_backup_$(date +%Y%m%d_%H%M%S).tar.gz" artifacts/
    echo "   ✓ Artifacts archived"
fi

# 4. Deactivate virtual environment
echo "4. Deactivating virtual environment..."
deactivate 2>/dev/null || echo "   Already deactivated"

# 5. Final status
echo ""
echo "========================================="
echo "✓ Shutdown complete"
echo "========================================="
```

---

## Command Reference

### Quick Command Index

| Command | Purpose | Time |
|---------|---------|------|
| `source farfan-env/bin/activate` | Activate environment | < 1s |
| `python verify_dependencies.py` | Health check | 5-10s |
| `python scripts/run_policy_pipeline_verified.py --plan <PDF>` | Run pipeline | 60-180s |
| `python scripts/run_complete_analysis_plan1.py` | Quick analysis | 60-120s |
| `bash health_check.sh` | Full health check | 10-15s |
| `bash test_suite.sh` | Run test suite | 5-10min |
| `pkill -f "python.*run_policy"` | Emergency stop | < 1s |

### Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `PIPELINE_DEBUG` | Enable debug output | `0` |
| `MANIFEST_SECRET_KEY` | HMAC secret key | `default-dev-key-change-in-production` |
| `PYTHONHASHSEED` | Python hash seed (determinism) | Random |
| `PYTHONFAULTHANDLER` | Enable fault handler | `0` |

### File Locations

| Path | Contents |
|------|----------|
| `data/plans/` | Input PDF files |
| `data/questionnaire_monolith.json` | 300-question evaluation framework |
| `artifacts/` | Pipeline outputs and verification manifests |
| `farfan-env/` | Python virtual environment |
| `scripts/` | Execution scripts |
| `tools/` | Validation and diagnostic tools |
| `tests/` | Automated test suite |

---

## Appendix A: Complete Health Check Script

Save this as `comprehensive_health_check.sh`:

```bash
#!/bin/bash
# Comprehensive F.A.R.F.A.N Health Check
# Version: 1.0.0

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "F.A.R.F.A.N Comprehensive Health Check"
echo "========================================="
echo ""

# Track overall health
HEALTH_SCORE=0
MAX_SCORE=10

# Check 1: Python Version
echo "1. Python Version"
if python3.12 --version > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Python 3.12 installed${NC}"
    ((HEALTH_SCORE++))
else
    echo -e "${RED}✗ Python 3.12 not found${NC}"
fi
echo ""

# Check 2: Virtual Environment
echo "2. Virtual Environment"
if [ -n "$VIRTUAL_ENV" ]; then
    echo -e "${GREEN}✓ Activated: $VIRTUAL_ENV${NC}"
    ((HEALTH_SCORE++))
else
    echo -e "${YELLOW}⚠ Not activated - run: source farfan-env/bin/activate${NC}"
fi
echo ""

# Check 3: Dependencies
echo "3. Critical Dependencies"
DEP_CHECK_OUTPUT="$(python verify_dependencies.py 2>&1)"
DEP_PASSED=$(echo "$DEP_CHECK_OUTPUT" | awk -F'[:/]' '/Passed:/ {gsub(/ /,"",$2); print $2}')
if [ -n "$DEP_PASSED" ] && [ "$DEP_PASSED" -ge 5 ]; then
    echo -e "${GREEN}✓ All dependencies verified${NC}"
    ((HEALTH_SCORE++))
else
    echo -e "${RED}✗ Some dependencies missing${NC}"
fi
echo ""

# Check 4: Questionnaire
echo "4. Questionnaire Integrity"
if python3 -c "from saaaaaa.core.orchestrator.questionnaire import load_questionnaire; load_questionnaire()" 2>/dev/null; then
    echo -e "${GREEN}✓ Questionnaire loaded and verified${NC}"
    ((HEALTH_SCORE++))
else
    echo -e "${RED}✗ Questionnaire integrity check failed${NC}"
fi
echo ""

# Check 5: Class Registry
echo "5. Class Registry"
CLASS_COUNT=$(python3 -c "from saaaaaa.core.orchestrator.class_registry import ClassRegistry; print(len(ClassRegistry().get_all_classes()))" 2>/dev/null || echo "0")
if [ "$CLASS_COUNT" -ge "22" ]; then
    echo -e "${GREEN}✓ All $CLASS_COUNT classes registered${NC}"
    ((HEALTH_SCORE++))
else
    echo -e "${RED}✗ Only $CLASS_COUNT classes registered (expected 22)${NC}"
fi
echo ""

# Check 6: Test Data
echo "6. Test Data Availability"
if [ -f "data/plans/Plan_1.pdf" ]; then
    SIZE=$(du -h data/plans/Plan_1.pdf | cut -f1)
    echo -e "${GREEN}✓ Plan_1.pdf exists ($SIZE)${NC}"
    ((HEALTH_SCORE++))
else
    echo -e "${RED}✗ Plan_1.pdf not found${NC}"
fi
echo ""

# Check 7: Signal System
echo "7. Signal System"
if python3 -c "from saaaaaa.core.orchestrator.signals import SignalClient; c = SignalClient('memory://'); c.register_memory_signal('TEST', {}); c.fetch_signal_pack('TEST')" 2>/dev/null; then
    echo -e "${GREEN}✓ Signal system operational${NC}"
    ((HEALTH_SCORE++))
else
    echo -e "${RED}✗ Signal system check failed${NC}"
fi
echo ""

# Check 8: Disk Space
echo "8. Disk Space"
AVAILABLE=$(df -h . | tail -1 | awk '{print $4}')
AVAILABLE_GB=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
if [ "$AVAILABLE_GB" -gt "2" ]; then
    echo -e "${GREEN}✓ Sufficient space: $AVAILABLE${NC}"
    ((HEALTH_SCORE++))
else
    echo -e "${YELLOW}⚠ Low disk space: $AVAILABLE${NC}"
fi
echo ""

# Check 9: Memory
echo "9. Memory"
if command -v free > /dev/null 2>&1; then
    AVAILABLE_MEM=$(free -g | grep "Mem:" | awk '{print $7}')
    if [ "$AVAILABLE_MEM" -gt "4" ]; then
        echo -e "${GREEN}✓ Sufficient memory: ${AVAILABLE_MEM}GB available${NC}"
        ((HEALTH_SCORE++))
    else
        echo -e "${YELLOW}⚠ Low memory: ${AVAILABLE_MEM}GB available${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Cannot check memory (free command not available)${NC}"
fi
echo ""

# Check 10: Write Permissions
echo "10. Write Permissions"
if [ -w "artifacts/" ] || mkdir -p "artifacts/" 2>/dev/null; then
    echo -e "${GREEN}✓ artifacts/ directory writable${NC}"
    ((HEALTH_SCORE++))
else
    echo -e "${RED}✗ artifacts/ directory not writable${NC}"
fi
echo ""

# Overall Score
echo "========================================="
echo "Health Score: $HEALTH_SCORE/$MAX_SCORE"
if [ "$HEALTH_SCORE" -ge "9" ]; then
    echo -e "${GREEN}✓ System health: EXCELLENT${NC}"
    exit 0
elif [ "$HEALTH_SCORE" -ge "7" ]; then
    echo -e "${YELLOW}⚠ System health: GOOD (some issues)${NC}"
    exit 0
else
    echo -e "${RED}✗ System health: POOR (multiple issues)${NC}"
    exit 1
fi
echo "========================================="
```

Make executable:
```bash
chmod +x comprehensive_health_check.sh
./comprehensive_health_check.sh
```

---

## Appendix B: Automated Test Suite

Save this as `test_suite.sh`:

```bash
#!/bin/bash
# F.A.R.F.A.N Automated Test Suite
# Version: 1.0.0

set -e

echo "========================================="
echo "F.A.R.F.A.N Automated Test Suite"
echo "========================================="
echo ""

FAILED_TESTS=0

# TC-001: Dependencies
echo "Running TC-001: Dependency Verification..."
if python verify_dependencies.py > /tmp/tc001.log 2>&1 && python3 -c "import re; log=open('/tmp/tc001.log').read(); match=re.search(r'Passed: (\d+)/(\d+)', log); exit(0) if match and int(match.group(1)) == int(match.group(2)) else exit(1)" ; then
    echo "✓ TC-001 PASSED"
else
    echo "✗ TC-001 FAILED"
    cat /tmp/tc001.log
    ((FAILED_TESTS++))
fi
echo ""

# TC-002: Questionnaire
echo "Running TC-002: Questionnaire Integrity..."
if python3 -c "from saaaaaa.core.orchestrator.questionnaire import load_questionnaire; load_questionnaire()" 2>&1; then
    echo "✓ TC-002 PASSED"
else
    echo "✗ TC-002 FAILED"
    ((FAILED_TESTS++))
fi
echo ""

# TC-003: Class Registry
echo "Running TC-003: Class Registry..."
CLASS_COUNT=$(python3 -c "from saaaaaa.core.orchestrator.class_registry import ClassRegistry; print(len(ClassRegistry().get_all_classes()))" 2>/dev/null || echo "0")
if [ "$CLASS_COUNT" -ge "22" ]; then
    echo "✓ TC-003 PASSED ($CLASS_COUNT classes)"
else
    echo "✗ TC-003 FAILED (only $CLASS_COUNT classes)"
    ((FAILED_TESTS++))
fi
echo ""

# TC-004: Full Pipeline
echo "Running TC-004: Complete Pipeline (this may take 2-3 minutes)..."
if python scripts/run_policy_pipeline_verified.py \
    --plan data/plans/Plan_1.pdf \
    --artifacts-dir artifacts/test_suite_run > /tmp/tc004.log 2>&1 && \
   grep -q "PIPELINE_VERIFIED=1" /tmp/tc004.log; then
    echo "✓ TC-004 PASSED"
else
    echo "✗ TC-004 FAILED"
    tail -50 /tmp/tc004.log
    ((FAILED_TESTS++))
fi
echo ""

# Summary
echo "========================================="
if [ $FAILED_TESTS -eq 0 ]; then
    echo "✅ ALL TESTS PASSED"
    echo "========================================="
    exit 0
else
    echo "✗ $FAILED_TESTS TEST(S) FAILED"
    echo "========================================="
    exit 1
fi
```

Make executable:
```bash
chmod +x test_suite.sh
./test_suite.sh
```

---

**Document Version**: 1.0.0
**Last Updated**: 2025-11-18
**Maintained By**: F.A.R.F.A.N Development Team
**Contact**: See [README.md](README.md) for support information

---

**Related Documentation**:
- [TEST_PLAN.md](TEST_PLAN.md) - Comprehensive test plan
- [OPERATIONAL_GUIDE.md](OPERATIONAL_GUIDE.md) - User operational guide
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) - Installation instructions
