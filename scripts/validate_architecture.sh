#!/bin/bash
# ARCHITECTURAL INTEGRITY VALIDATION v2.0
# Enforces canonical architecture via detection (not remediation)
#
# Exit codes:
#   0 = Architecture is valid
#   1 = Forbidden imports detected
#   2 = Compatibility shims detected
#   3 = Deprecated module usage detected

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

EXIT_CODE=0
ERRORS=0
WARNINGS=0

echo "=========================================="
echo "ARCHITECTURAL INTEGRITY VALIDATION"
echo "=========================================="
echo "Repository: $REPO_ROOT"
echo "Canonical Architecture: docs/canonical_architecture.md"
echo ""

# Check 1: Forbidden namespace - orchestration.orchestrator
echo "[1/7] Checking for forbidden orchestration.orchestrator imports..."
ORCHESTRATOR_IMPORTS=$(grep -rn "from orchestration\.orchestrator import\|import orchestration\.orchestrator" \
    --include="*.py" \
    --exclude-dir=".git" \
    --exclude-dir="__pycache__" \
    --exclude-dir="backups" \
    --exclude-dir="artifacts" \
    --exclude-dir="scripts" \
    . 2>/dev/null | grep -v "^[^:]*\.py:[^:]*:#" | grep -v "pattern=r\"" || true)

if [ -n "$ORCHESTRATOR_IMPORTS" ]; then
    echo "$ORCHESTRATOR_IMPORTS"
    echo "❌ ERROR: Found forbidden imports from orchestration.orchestrator"
    echo "   Replace with: from farfan_pipeline.orchestration.core_orchestrator import ..."
    ERRORS=$((ERRORS + 1))
    EXIT_CODE=1
else
    echo "✓ No forbidden orchestration.orchestrator imports"
fi

# Check 2: Forbidden namespace - cross_cutting_infrastructure
echo ""
echo "[2/7] Checking for forbidden cross_cutting_infrastructure imports..."
CROSS_CUTTING_IMPORTS=$(grep -rn "from cross_cutting_infrastructure\|import cross_cutting_infrastructure" \
    --include="*.py" \
    --exclude-dir=".git" \
    --exclude-dir="__pycache__" \
    --exclude-dir="backups" \
    --exclude-dir="artifacts" \
    --exclude-dir="scripts" \
    . 2>/dev/null | grep -v "pattern=r\"" | grep -v "^[^:]*\.py:[^:]*:#" | grep -v "BAD_IMPORT_PATTERNS\|DEPRECATED" || true)

if [ -n "$CROSS_CUTTING_IMPORTS" ]; then
    echo "$CROSS_CUTTING_IMPORTS"
    echo "❌ ERROR: Found forbidden imports from cross_cutting_infrastructure namespace"
    echo "   This namespace has been eliminated. Replace with farfan_pipeline.infrastructure.*"
    ERRORS=$((ERRORS + 1))
    EXIT_CODE=1
else
    echo "✓ No forbidden cross_cutting_infrastructure imports"
fi

# Check 3: Deprecated signal_consumption imports
echo ""
echo "[3/7] Checking for deprecated signal_consumption imports..."
if grep -rn "from.*signal_consumption import\|import.*signal_consumption" \
    --include="*.py" \
    --exclude-dir=".git" \
    --exclude-dir="__pycache__" \
    --exclude-dir="backups" \
    --exclude-dir="artifacts" \
    --exclude-dir="_deprecated" \
    --exclude-dir="scripts" \
    . 2>/dev/null | grep -v "audit/questionnaire_access_audit\|audit/consumption_proof\|SISAS/signal_consumption.py\|backward compatibility"; then
    echo "❌ ERROR: Found imports from deprecated _deprecated/signal_consumption module"
    echo "   These should have been migrated to:"
    echo "   - SISAS.audit.questionnaire_access_audit (AccessLevel, get_access_audit, etc.)"
    echo "   - SISAS.audit.consumption_proof (SignalConsumptionProof, etc.)"
    ERRORS=$((ERRORS + 1))
    if [ "$EXIT_CODE" -eq 0 ]; then
        EXIT_CODE=2
    fi
else
    echo "✓ No deprecated signal_consumption imports (migrated to canonical audit modules)"
fi

# Check 4: Compatibility shims
echo ""
echo "[4/7] Checking for compatibility shim files..."
SHIM_FILES=$(find . -type f \( -name "*_compat.py" -o -name "*_legacy.py" -o -name "*_shim.py" \) \
    -not -path "./.git/*" \
    -not -path "./backups/*" \
    -not -path "./artifacts/*" \
    -not -path "./farfan-env/*" \
    -not -path "./*-env/*" \
    -not -path "./venv/*" \
    -not -path "./.venv/*" \
    -not -path "./tests/*" \
    2>/dev/null || true)

if [ -n "$SHIM_FILES" ]; then
    echo "❌ ERROR: Found compatibility shim files (forbidden by Phase 0):"
    echo "$SHIM_FILES"
    ERRORS=$((ERRORS + 1))
    if [ "$EXIT_CODE" -eq 0 ]; then
        EXIT_CODE=2
    fi
else
    echo "✓ No compatibility shim files found"
fi

# Check 5: Imports from _deprecated directories
echo ""
echo "[5/7] Checking for imports from _deprecated directories..."
DEPRECATED_IMPORTS=$(grep -rn "from.*_deprecated.*import\|import.*_deprecated" \
    --include="*.py" \
    --exclude-dir=".git" \
    --exclude-dir="__pycache__" \
    --exclude-dir="backups" \
    --exclude-dir="artifacts" \
    --exclude-dir="_deprecated" \
    --exclude-dir="farfan-env" \
    --exclude-dir="venv" \
    --exclude-dir=".venv" \
    . 2>/dev/null || true)

if [ -n "$DEPRECATED_IMPORTS" ]; then
    echo "⚠️  WARNING: Found imports from _deprecated directories:"
    echo "$DEPRECATED_IMPORTS"
    WARNINGS=$((WARNINGS + 1))
    if [ "$EXIT_CODE" -eq 0 ]; then
        EXIT_CODE=3
    fi
else
    echo "✓ No imports from _deprecated directories"
fi

# Check 6: Placeholder classes (stub implementations)
echo ""
echo "[6/7] Checking for placeholder stub classes..."
PLACEHOLDER_CLASSES=$(grep -rn "^class.*:$" \
    --include="*.py" \
    --exclude-dir=".git" \
    --exclude-dir="__pycache__" \
    --exclude-dir="backups" \
    --exclude-dir="artifacts" \
    --exclude-dir="tests" \
    --exclude-dir="farfan-env" \
    --exclude-dir="venv" \
    --exclude-dir=".venv" \
    . 2>/dev/null | grep -v "Protocol\|Enum\|Exception" || true)

if [ -n "$PLACEHOLDER_CLASSES" ]; then
    # Check if these are actually just empty classes (next line is 'pass' or another class)
    ACTUAL_PLACEHOLDERS=$(echo "$PLACEHOLDER_CLASSES" | while read -r line; do
        FILE=$(echo "$line" | cut -d: -f1)
        LINE_NUM=$(echo "$line" | cut -d: -f2)
        NEXT_LINE=$((LINE_NUM + 1))
        NEXT_CONTENT=$(sed -n "${NEXT_LINE}p" "$FILE" 2>/dev/null | tr -d '[:space:]')
        if [ "$NEXT_CONTENT" = "pass" ]; then
            echo "$line"
        fi
    done)

    if [ -n "$ACTUAL_PLACEHOLDERS" ]; then
        echo "⚠️  WARNING: Found potential placeholder classes (empty with just 'pass'):"
        echo "$ACTUAL_PLACEHOLDERS" | head -10
        WARNINGS=$((WARNINGS + 1))
    else
        echo "✓ No placeholder stub classes found"
    fi
else
    echo "✓ No placeholder stub classes found"
fi

# Check 7: Verify canonical architecture document exists
echo ""
echo "[7/7] Verifying canonical architecture documentation..."
if [ ! -f "docs/canonical_architecture.md" ]; then
    echo "❌ ERROR: Canonical architecture document not found"
    echo "   Expected: docs/canonical_architecture.md"
    ERRORS=$((ERRORS + 1))
    if [ "$EXIT_CODE" -eq 0 ]; then
        EXIT_CODE=1
    fi
else
    echo "✓ Canonical architecture document exists"
fi

# Summary
echo ""
echo "=========================================="
echo "VALIDATION SUMMARY"
echo "=========================================="
echo "Errors:   $ERRORS"
echo "Warnings: $WARNINGS"
echo ""

if [ "$EXIT_CODE" -eq 0 ]; then
    echo "✓ ARCHITECTURAL INTEGRITY VALIDATED"
    echo "  The canonical architecture is enforced."
elif [ "$EXIT_CODE" -eq 1 ]; then
    echo "❌ ARCHITECTURAL VIOLATIONS DETECTED"
    echo "   Critical errors must be fixed before proceeding."
elif [ "$EXIT_CODE" -eq 2 ]; then
    echo "❌ COMPATIBILITY SHIMS DETECTED"
    echo "   Remove all *_compat.py, *_legacy.py, *_shim.py files."
elif [ "$EXIT_CODE" -eq 3 ]; then
    echo "⚠️  DEPRECATION WARNINGS"
    echo "   Deprecated imports should be migrated to canonical paths."
fi

echo ""
echo "For remediation guidance, see: docs/canonical_architecture.md"
echo "For stratification data, see: artifacts/stratification/"
echo ""

exit $EXIT_CODE
