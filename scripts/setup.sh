#!/bin/bash
# Quick setup script for SAAAAAA project
# Installs all dependencies and SpaCy models

set -euo pipefail  # Exit on error, undefined variables, and pipeline failures

echo "======================================================================"
echo "SAAAAAA Project Setup"
echo "======================================================================"
echo ""
echo "This script will:"
echo "  1. Install Python dependencies from requirements.txt"
echo "  2. Install SpaCy language models (es_core_news_lg, es_dep_news_trf)"
echo "  3. Verify the installation"
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Found Python $python_version"
echo ""

# Step 1: Install Python dependencies
echo "======================================================================"
echo "Step 1: Installing Python dependencies"
echo "======================================================================"
echo ""

if [ -f "requirements.txt" ]; then
    echo "Installing from requirements.txt..."
    pip install -r requirements.txt
    echo "✓ Python dependencies installed"
else
    echo "✗ ERROR: requirements.txt not found"
    exit 1
fi

echo ""
echo "Installing saaaaaa package in editable mode..."
pip install -e .
echo "✓ Package installed"

echo ""

# Step 2: Install SpaCy models
echo "======================================================================"
echo "Step 2: Installing SpaCy language models"
echo "======================================================================"
echo ""

echo "Installing es_core_news_lg (large Spanish model)..."
python3 -m spacy download es_core_news_lg

echo ""
echo "Installing es_dep_news_trf (transformer Spanish model)..."
python3 -m spacy download es_dep_news_trf

echo "✓ SpaCy models installed"
echo ""

# Step 3: Verify installation
echo "======================================================================"
echo "Step 3: Verifying installation"
echo "======================================================================"
echo ""

if [ -f "scripts/verify_dependencies.py" ]; then
    python3 scripts/verify_dependencies.py
else
    echo "⚠ Warning: verification script not found, skipping verification"
fi

echo ""
echo "======================================================================"
echo "Setup Complete!"
echo "======================================================================"
echo ""
echo "Next steps:"
echo "  - Run tests: pytest tests/"
echo "  - Validate class registry: python scripts/verify_dependencies.py"
echo "  - See DEPENDENCY_SETUP.md for more information"
echo ""
