#!/bin/bash
# ============================================================================
# F.A.R.F.A.N MECHANISTIC POLICY PIPELINE - SYSTEM DEPENDENCIES INSTALLER
# ============================================================================
# This script installs all required system-level dependencies for the project
# Run this BEFORE installing Python packages with pip
# ============================================================================

set -e  # Exit on error

echo "============================================================================"
echo "F.A.R.F.A.N System Dependencies Installer"
echo "============================================================================"

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VERSION=$VERSION_ID
else
    echo "Error: Cannot detect operating system"
    exit 1
fi

echo "Detected OS: $OS"
echo ""

case $OS in
    ubuntu|debian)
        echo "Installing dependencies for Ubuntu/Debian..."
        sudo apt-get update
        sudo apt-get install -y \
            ghostscript \
            python3-tk \
            libgraphviz-dev \
            graphviz \
            default-jre \
            build-essential \
            python3-dev \
            libopenblas-dev \
            liblapack-dev \
            gfortran \
            pkg-config
        echo "✓ Ubuntu/Debian dependencies installed successfully"
        ;;

    fedora|rhel|centos)
        echo "Installing dependencies for Fedora/RHEL/CentOS..."
        sudo dnf install -y \
            ghostscript \
            tk \
            graphviz \
            graphviz-devel \
            java-11-openjdk \
            gcc \
            gcc-c++ \
            python3-devel \
            openblas-devel \
            lapack-devel \
            gcc-gfortran \
            pkg-config
        echo "✓ Fedora/RHEL dependencies installed successfully"
        ;;

    arch|manjaro)
        echo "Installing dependencies for Arch Linux..."
        sudo pacman -Syu --noconfirm \
            ghostscript \
            tk \
            graphviz \
            jre-openjdk \
            base-devel \
            python \
            openblas \
            lapack \
            gcc-fortran \
            pkg-config
        echo "✓ Arch Linux dependencies installed successfully"
        ;;

    *)
        echo "Warning: Unsupported OS: $OS"
        echo "Please manually install the following dependencies:"
        echo "  - ghostscript (for PDF processing with camelot)"
        echo "  - tk/tkinter (for GUI components)"
        echo "  - graphviz (for graph visualization)"
        echo "  - Java JRE (for tabula-py PDF table extraction)"
        echo "  - Build tools (gcc, g++, make)"
        echo "  - Python development headers"
        echo "  - BLAS/LAPACK libraries (for scientific computing)"
        echo "  - Fortran compiler (for scipy/numpy)"
        exit 1
        ;;
esac

echo ""
echo "============================================================================"
echo "System dependencies installation complete!"
echo "============================================================================"
echo ""
echo "Next steps:"
echo "1. Upgrade pip: pip install --upgrade pip setuptools wheel"
echo "2. Install Python packages: pip install -r requirements.txt"
echo "3. Download spaCy model: python -m spacy download es_core_news_sm"
echo ""
echo "============================================================================"
