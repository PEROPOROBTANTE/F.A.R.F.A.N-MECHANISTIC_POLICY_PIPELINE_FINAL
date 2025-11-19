#!/bin/bash
# ============================================================================
# SAAAAAA Installation Script - Python 3.12 Compatible
# ============================================================================
# This script installs ALL dependencies with proper error handling
# and verification for Python 3.12 environments
#
# Usage:
#   ./install_fixed.sh [--skip-pymc] [--test-only]
#
# Options:
#   --skip-pymc: Skip PyMC installation (avoids building from source)
#   --test-only: Only run verification tests
# ============================================================================

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SKIP_PYMC=false
TEST_ONLY=false
MAX_RETRIES=3
TIMEOUT=600

# Parse arguments
for arg in "$@"; do
    case $arg in
        --skip-pymc)
            SKIP_PYMC=true
            shift
            ;;
        --test-only)
            TEST_ONLY=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $arg${NC}"
            exit 1
            ;;
    esac
done

# Print header
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}SAAAAAA Installation Script - Python 3.12 Required${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "${BLUE}Python version: ${PYTHON_VERSION}${NC}"

if [[ "$PYTHON_VERSION" != "3.12" ]]; then
    echo -e "${RED}ERROR: Python 3.12 required${NC}"
    exit 1
fi

if [[ "$TEST_ONLY" == true ]]; then
    echo -e "${YELLOW}Running verification tests only...${NC}"
    python3 << 'EOF'
import sys

packages_to_test = [
    ('numpy', 'NumPy - Core array library'),
    ('scipy', 'SciPy - Scientific computing'),
    ('pandas', 'Pandas - Data manipulation'),
    ('sklearn', 'Scikit-learn - Machine learning'),
    ('networkx', 'NetworkX - Graph analysis'),
    ('pydantic', 'Pydantic - Data validation'),
    ('flask', 'Flask - Web framework'),
    ('fastapi', 'FastAPI - Web framework'),
    ('transformers', 'Transformers - NLP'),
    ('huggingface_hub', 'Hugging Face Hub'),
]

print("Testing package imports...")
print("="*70)

failed = []
for package, description in packages_to_test:
    try:
        mod = __import__(package)
        version = getattr(mod, '__version__', 'unknown')
        print(f'✅ {package:20s} v{version:10s} - {description}')
    except ImportError as e:
        print(f'❌ {package:20s} {"MISSING":10s} - {description}')
        failed.append(package)

print("="*70)

if failed:
    print(f'\n❌ FAILED: Missing packages: {", ".join(failed)}')
    sys.exit(1)
else:
    print(f'\n✅ SUCCESS: All packages imported successfully!')
    
# Check NumPy version specifically
import numpy
if numpy.__version__.startswith('2.'):
    print(f'\n⚠️  WARNING: NumPy 2.x detected ({numpy.__version__})')
    print('   This may cause issues with PyMC/PyTensor.')
    print('   Recommended: numpy==1.26.4')
elif numpy.__version__ == '1.26.4':
    print(f'\n✅ NumPy version correct: {numpy.__version__}')
else:
    print(f'\nℹ️  NumPy version: {numpy.__version__}')

sys.exit(0)
EOF
    exit $?
fi

echo ""
echo -e "${YELLOW}Step 1: Checking system dependencies${NC}"
echo "----------------------------------------------------------------------"

# Check for system dependencies
MISSING_DEPS=()

if ! command -v gcc &> /dev/null; then
    MISSING_DEPS+=("gcc (C compiler)")
fi

if ! command -v gs &> /dev/null; then
    MISSING_DEPS+=("ghostscript")
fi

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Missing system dependencies:${NC}"
    for dep in "${MISSING_DEPS[@]}"; do
        echo "   - $dep"
    done
    echo ""
    echo "Install with:"
    echo "  Ubuntu/Debian: sudo apt-get install -y gcc ghostscript libgl1-mesa-glx libglib2.0-0"
    echo "  macOS:         brew install gcc ghostscript"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✅ All system dependencies found${NC}"
fi

echo ""
echo -e "${YELLOW}Step 2: Upgrading pip and build tools${NC}"
echo "----------------------------------------------------------------------"
pip install --upgrade pip setuptools wheel || {
    echo -e "${RED}Failed to upgrade pip/setuptools/wheel${NC}"
    exit 1
}

echo ""
echo -e "${YELLOW}Step 3: Installing core dependencies${NC}"
echo "----------------------------------------------------------------------"
echo "This will install NumPy 1.26.4 (required for PyMC/PyTensor compatibility)"

pip install --timeout=${TIMEOUT} --retries=${MAX_RETRIES} \
    -c constraints.txt \
    numpy==1.26.4 \
    scipy==1.14.1 \
    pandas==2.2.3 \
    scikit-learn==1.6.1 \
    networkx==3.4.2 \
    pydantic==2.10.6 \
    || {
    echo -e "${RED}Failed to install core dependencies${NC}"
    exit 1
}

echo -e "${GREEN}✅ Core dependencies installed${NC}"

echo ""
echo -e "${YELLOW}Step 4: Installing web frameworks${NC}"
echo "----------------------------------------------------------------------"

pip install --timeout=${TIMEOUT} --retries=${MAX_RETRIES} \
    -c constraints.txt \
    flask==3.0.3 \
    fastapi==0.115.6 \
    httpx==0.28.1 \
    || {
    echo -e "${RED}Failed to install web frameworks${NC}"
    exit 1
}

echo -e "${GREEN}✅ Web frameworks installed${NC}"

echo ""
echo -e "${YELLOW}Step 5: Installing NLP/ML packages${NC}"
echo "----------------------------------------------------------------------"

pip install --timeout=${TIMEOUT} --retries=${MAX_RETRIES} \
    -c constraints.txt \
    huggingface-hub==0.27.1 \
    transformers==4.48.3 \
    tokenizers==0.21.0 \
    safetensors==0.5.2 \
    || {
    echo -e "${RED}Failed to install NLP packages${NC}"
    exit 1
}

echo -e "${GREEN}✅ NLP/ML packages installed${NC}"

if [[ "$SKIP_PYMC" == false ]]; then
    echo ""
    echo -e "${YELLOW}Step 6: Installing PyMC stack (may build from source)${NC}"
    echo "----------------------------------------------------------------------"
    echo "This may take several minutes..."
    
    # Install Cython first
    pip install Cython || {
        echo -e "${YELLOW}⚠️  Warning: Cython installation failed${NC}"
    }
    
    # Install PyTensor
    pip install --timeout=${TIMEOUT} --retries=${MAX_RETRIES} \
        pytensor==2.34.0 || {
        echo -e "${RED}Failed to install PyTensor${NC}"
        exit 1
    }
    
    # Install PyMC (may build from source)
    pip install --timeout=${TIMEOUT} --retries=${MAX_RETRIES} --no-binary pymc \
        pymc==5.16.2 || {
        echo -e "${YELLOW}⚠️  Warning: PyMC installation failed (building from source may have failed)${NC}"
        echo "   You can continue without PyMC or install manually later"
        read -p "Continue without PyMC? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    }
    
    echo -e "${GREEN}✅ PyMC stack installed${NC}"
else
    echo ""
    echo -e "${YELLOW}Step 6: Skipping PyMC installation (--skip-pymc flag)${NC}"
fi

echo ""
echo -e "${YELLOW}Step 7: Installing remaining dependencies${NC}"
echo "----------------------------------------------------------------------"

pip install --timeout=${TIMEOUT} --retries=${MAX_RETRIES} \
    -c constraints.txt \
    -r requirements-core.txt \
    || {
    echo -e "${YELLOW}⚠️  Warning: Some optional dependencies may have failed${NC}"
}

echo ""
echo -e "${YELLOW}Step 8: Verification${NC}"
echo "----------------------------------------------------------------------"

python3 << 'EOF'
import sys

print("Verifying critical packages...")
print("="*70)

packages_to_test = [
    'numpy',
    'scipy', 
    'pandas',
    'sklearn',
    'networkx',
    'pydantic',
    'flask',
    'fastapi',
    'transformers',
    'huggingface_hub',
]

failed = []
for package in packages_to_test:
    try:
        mod = __import__(package)
        version = getattr(mod, '__version__', 'unknown')
        print(f'✅ {package:20s} v{version}')
    except ImportError:
        print(f'❌ {package:20s} MISSING')
        failed.append(package)

print("="*70)

if failed:
    print(f'\n⚠️  Missing packages: {", ".join(failed)}')
    sys.exit(1)

# Check NumPy version
import numpy
print(f'\nNumPy version: {numpy.__version__}')
if numpy.__version__ != '1.26.4':
    print('⚠️  WARNING: Expected NumPy 1.26.4 for PyMC compatibility')

sys.exit(0)
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}============================================================================${NC}"
    echo -e "${GREEN}✅ INSTALLATION SUCCESSFUL!${NC}"
    echo -e "${GREEN}============================================================================${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Verify installation: python scripts/verify_importability.py"
    echo "  2. Run tests: pytest tests/"
    echo "  3. See PYTHON_312_COMPATIBILITY.md for detailed information"
    echo ""
else
    echo ""
    echo -e "${RED}============================================================================${NC}"
    echo -e "${RED}❌ INSTALLATION COMPLETED WITH WARNINGS${NC}"
    echo -e "${RED}============================================================================${NC}"
    echo ""
    echo "Some packages may be missing. Check the output above."
    echo "See PYTHON_312_COMPATIBILITY.md for troubleshooting."
    echo ""
    exit 1
fi
