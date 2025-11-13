#!/bin/bash
# Build Rust extension for CPP ingestion system

set -e

echo "Building CPP Ingestion Rust extension..."

# Check if Rust is installed
if ! command -v cargo &> /dev/null; then
    echo "Error: Rust is not installed. Please install Rust from https://rustup.rs/"
    exit 1
fi

# Check if maturin is installed
if ! command -v maturin &> /dev/null; then
    echo "Installing maturin..."
    pip install maturin
fi

# Navigate to cpp_ingestion directory
cd cpp_ingestion

# Build in release mode
echo "Building Rust extension in release mode..."
maturin develop --release

echo "✓ Rust extension built successfully"
echo ""
echo "You can now import: from cpp_ingestion import hash_blake3, normalize_unicode_nfc, ..."
