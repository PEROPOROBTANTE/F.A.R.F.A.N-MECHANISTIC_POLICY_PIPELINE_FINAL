#!/usr/bin/env bash
#
# F.A.R.F.A.N Complete Installation Script
# =========================================
# Installs ALL dependencies with exact versions from requirements.txt
#
# Requirements:
#   - Ubuntu/Debian 20.04+ (or compatible Linux)
#   - Python 3.12.x
#   - sudo access for system dependencies
#
# Usage:
#   bash install.sh
#

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "F.A.R.F.A.N Complete Installation"
echo "=========================================="
echo ""

# 1. Check Python 3.12
echo -e "${YELLOW}[1/8] Checking Python 3.12...${NC}"
if ! command -v python3.12 &> /dev/null; then
    echo -e "${RED}ERROR: Python 3.12 not found${NC}"
    echo "Install with: sudo apt-get install python3.12 python3.12-venv python3.12-dev"
    exit 1
fi

PYTHON_VERSION=$(python3.12 --version | awk '{print $2}')
echo -e "${GREEN}✓ Found Python $PYTHON_VERSION${NC}"

# 2. Install system dependencies
echo ""
echo -e "${YELLOW}[2/8] Installing system dependencies...${NC}"
sudo apt-get update -qq
sudo apt-get install -y --no-install-recommends \
    build-essential \
    python3.12-dev \
    gfortran \
    libopenblas-dev \
    libhdf5-dev \
    ghostscript \
    python3-tk \
    libgraphviz-dev \
    graphviz \
    default-jre \
    2>&1 | grep -E "(Setting up|already)" || true

echo -e "${GREEN}✓ System dependencies installed${NC}"

# 3. Create virtual environment
echo ""
echo -e "${YELLOW}[3/8] Creating virtual environment...${NC}"
if [ -d "farfan-env" ]; then
    echo -e "${YELLOW}WARNING: Removing existing virtual environment...${NC}"
    echo "Press Ctrl+C within 5 seconds to cancel..."
    sleep 5
    rm -rf farfan-env
fi

python3.12 -m venv farfan-env
source farfan-env/bin/activate

echo -e "${GREEN}✓ Virtual environment created${NC}"

# 4. Upgrade pip, setuptools, wheel
echo ""
echo -e "${YELLOW}[4/8] Upgrading pip, setuptools, wheel...${NC}"
pip install --upgrade pip setuptools wheel -q

echo -e "${GREEN}✓ Package tools upgraded${NC}"

# 5. Install base dependencies (without problematic ones)
echo ""
echo -e "${YELLOW}[5/8] Installing core dependencies...${NC}"
echo "This will take several minutes..."

# Install core packages with exact versions
pip install --no-cache-dir \
    numpy==1.26.4 \
    scipy==1.14.1 \
    pandas==2.2.3 \
    polars==1.19.0 \
    pyarrow==19.0.0 \
    scikit-learn==1.6.1 \
    networkx==3.4.2 \
    -q

echo -e "${GREEN}✓ Core dependencies installed${NC}"

# 6. Install ML/DL frameworks
echo ""
echo -e "${YELLOW}[6/8] Installing ML/DL frameworks...${NC}"

# TensorFlow + tf-keras
pip install --no-cache-dir tensorflow==2.18.0 tf-keras -q

# PyTorch + torchvision
pip install --no-cache-dir torch==2.8.0 torchvision==0.23.0 -q

# Bayesian inference
pip install --no-cache-dir "pytensor>=2.25.1,<2.26" pymc==5.16.2 arviz==0.20.0 -q

echo -e "${GREEN}✓ ML/DL frameworks installed${NC}"

# 7. Install NLP stack with EXACT compatible versions
echo ""
echo -e "${YELLOW}[7/8] Installing NLP stack (transformers, sentence-transformers)...${NC}"

pip install --no-cache-dir \
    transformers==4.41.2 \
    sentence-transformers==3.1.0 \
    accelerate==1.2.1 \
    spacy==3.8.3 \
    nltk==3.9.1 \
    sentencepiece==0.2.0 \
    tiktoken==0.8.0 \
    fuzzywuzzy==0.18.0 \
    python-Levenshtein==0.26.1 \
    -q

echo -e "${GREEN}✓ NLP stack installed${NC}"

# 8. Install PDF processing and remaining dependencies
echo ""
echo -e "${YELLOW}[8/8] Installing PDF processing and final dependencies...${NC}"

pip install --no-cache-dir \
    pdfplumber==0.11.4 \
    PyPDF2==3.0.1 \
    PyMuPDF==1.25.2 \
    tabula-py==2.10.0 \
    "camelot-py[cv]==0.11.0" \
    pydot==3.0.4 \
    -q

# Force compatible opencv-python-headless (camelot installs wrong version)
pip install --force-reinstall --no-deps opencv-python-headless==4.10.0.84 -q

# Install package in development mode
pip install --no-cache-dir -e . -q

echo -e "${GREEN}✓ All dependencies installed${NC}"

# 9. Install SpaCy models (optional - may fail due to network)
echo ""
echo -e "${YELLOW}[Optional] Installing SpaCy language models...${NC}"
if python -m spacy download es_core_news_lg 2>&1 | grep -q "Successfully"; then
    echo -e "${GREEN}✓ es_core_news_lg installed${NC}"
else
    echo -e "${YELLOW}⚠ Could not download es_core_news_lg (network restricted)${NC}"
    echo "  Install later with: python -m spacy download es_core_news_lg"
fi

if python -m spacy download es_dep_news_trf 2>&1 | grep -q "Successfully"; then
    echo -e "${GREEN}✓ es_dep_news_trf installed${NC}"
else
    echo -e "${YELLOW}⚠ Could not download es_dep_news_trf (network restricted)${NC}"
    echo "  Install later with: python -m spacy download es_dep_news_trf"
fi

# 10. Final verification
echo ""
echo -e "${YELLOW}[Verification] Running dependency checks...${NC}"
echo ""

# Run diagnostic script
python diagnose_import_error.py 2>&1 | grep -E "(transformers|sentence_transformers|accelerate.*OK|FAILED)" || true

echo ""
echo "=========================================="
echo -e "${GREEN}Installation Complete!${NC}"
echo "=========================================="
echo ""
echo "Installed versions:"
pip list 2>&1 | grep -E "^(numpy|scikit-learn|transformers|sentence-transformers|torch|tensorflow|pymc|pytensor)" | grep -v WARNING || true
echo ""
echo "To activate the environment:"
echo "  source farfan-env/bin/activate"
echo ""
echo "To verify all dependencies:"
echo "  python scripts/verify_dependencies.py"
echo ""
echo "To diagnose import issues:"
echo "  python diagnose_import_error.py"
echo ""
