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
DEP_OUTPUT=$(python verify_dependencies.py 2>&1)
PASSED=$(echo "$DEP_OUTPUT" | grep -oP 'Passed: \K[0-9]+(?=/6)')
if [ -n "$PASSED" ] && [ "$PASSED" -ge 5 ]; then
    echo -e "${GREEN}✓ All dependencies verified ($PASSED/6)${NC}"
    ((HEALTH_SCORE++))
else
    echo -e "${RED}✗ Some dependencies missing ($PASSED/6)${NC}"
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
