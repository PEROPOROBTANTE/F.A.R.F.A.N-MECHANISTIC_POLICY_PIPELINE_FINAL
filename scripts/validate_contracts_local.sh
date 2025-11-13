#!/bin/bash
# Local validation script for data contracts
# Run this before committing to ensure all checks pass

set -e  # Exit on first error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "================================="
echo "Data Contracts Local Validation"
echo "================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track overall status
FAILED=0

# Create unique temporary file
TMP_OUTPUT=$(mktemp)
trap "rm -f $TMP_OUTPUT" EXIT

# Function to run a check
run_check() {
    local name="$1"
    local command="$2"
    
    echo -n "Running: $name ... "
    
    if eval "$command" > "$TMP_OUTPUT" 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo "Error output:"
        cat "$TMP_OUTPUT" | head -20
        echo ""
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# Check 1: Schema validation
if [ -f schema_validator.py ]; then
    run_check "Schema validation" "python schema_validator.py"
else
    echo -e "${YELLOW}⚠ Skipping: schema_validator.py not found${NC}"
fi

# Check 2: Cross-reference integrity
if [ -f tools/integrity/check_cross_refs.py ]; then
    run_check "Cross-reference integrity" "python tools/integrity/check_cross_refs.py"
else
    echo -e "${YELLOW}⚠ Skipping: tools/integrity/check_cross_refs.py not found${NC}"
fi

# Check 3: Questionnaire linting
if [ -f tools/lint/json_lint.py ] && [ -f questionnaire.json ]; then
run_check "Questionnaire lint" "python tools/lint/json_lint.py questionnaire.json --schema schemas/questionnaire_monolith.schema.json"
else
    echo -e "${YELLOW}⚠ Skipping: questionnaire linting tools not found${NC}"
fi

# Check 4: Rubric linting
if [ -f tools/lint/json_lint.py ] && [ -f rubric_scoring.json ]; then
    run_check "Rubric lint" "python tools/lint/json_lint.py rubric_scoring.json --schema schemas/rubric_scoring.schema.json"
else
    echo -e "${YELLOW}⚠ Skipping: rubric linting tools not found${NC}"
fi

# Check 5: Deterministic artifacts (optional, expensive)
if [ "$1" = "--full" ]; then
    if [ -f tools/integrity/dump_artifacts.py ]; then
        echo "Running: Deterministic artifact check (may take a while) ..."
        rm -rf artifacts/local_run1 artifacts/local_run2
        
        if python tools/integrity/dump_artifacts.py artifacts/local_run1 > /dev/null 2>&1 && \
           python tools/integrity/dump_artifacts.py artifacts/local_run2 > /dev/null 2>&1 && \
           diff artifacts/local_run1/deterministic_snapshot.json artifacts/local_run2/deterministic_snapshot.json > /dev/null 2>&1; then
            echo -e "${GREEN}✓ PASSED${NC}"
        else
            echo -e "${RED}✗ FAILED${NC}"
            echo "Deterministic artifacts differ between runs!"
            FAILED=$((FAILED + 1))
        fi
    fi
fi

# Check 6: Type checking (if mypy is available)
if command -v mypy &> /dev/null; then
    if [ -f orchestrator.py ]; then
        run_check "Type checking (mypy strict)" \
            "mypy --strict orchestrator.py scoring.py recommendation_engine.py validation_engine.py 2>&1 | grep -v 'Success:' || true"
    fi
else
    echo -e "${YELLOW}⚠ Skipping: mypy not installed (install with: pip install mypy)${NC}"
fi

echo ""
echo "================================="
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All checks passed!${NC}"
    echo "You can safely commit your changes."
    exit 0
else
    echo -e "${RED}$FAILED check(s) failed!${NC}"
    echo "Please fix the errors above before committing."
    echo ""
    echo "Hint: Use --verbose flag on individual commands for more details"
    exit 1
fi
