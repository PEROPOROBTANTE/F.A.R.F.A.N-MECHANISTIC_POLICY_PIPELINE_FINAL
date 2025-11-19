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
if python verify_dependencies.py > /tmp/tc001.log 2>&1; then
    PASSED=$(grep -oP 'Passed: \K\d+(?=/6)' /tmp/tc001.log || echo "0")
    if [ "$PASSED" -ge "5" ]; then
        echo "✓ TC-001 PASSED"
    else
        echo "✗ TC-001 FAILED (only $PASSED/6 passed)"
        ((FAILED_TESTS++))
    fi
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
