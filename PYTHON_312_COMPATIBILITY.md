# Python 3.12 Compatibility Guide

## Critical Information

This repository is configured for **Python 3.12** compatibility. However, Python 3.12 introduces significant challenges due to **NumPy 2.0 binary incompatibility** with the PyMC/PyTensor stack.

## The NumPy 2.0 Problem

**NumPy 2.0** introduced breaking changes to the C-API that affect packages compiled against NumPy 1.x:

- **Old API**: `numpy._core._multiarray_umath`, `numpy.core.multiarray`
- **New API**: Different internal module structure, removed `_ARRAY_API` symbols

### Why We Use NumPy 1.26.4 (NOT a Downgrade)

**This is a COMPATIBILITY REQUIREMENT, not a downgrade:**

1. **PyTensor 2.35+** requires NumPy 2.0+
2. **PyTensor 2.34.0** supports NumPy 1.x and has Python 3.12 wheels
3. **PyMC 5.16.2** works with PyTensor 2.34.0
4. **PyMC has NO pre-built wheels for Python 3.12** - must build from source

**The constraint chain:**
```
Python 3.12 → PyTensor 2.34.0 (max) → NumPy <2.0 (requirement) → NumPy 1.26.4 (latest 1.x)
```

## Dependency Version Matrix

### Core Scientific Stack

| Package | Version | Reason |
|---------|---------|--------|
| `numpy` | 1.26.4 | Last 1.x with Python 3.12 support, required for PyMC/PyTensor |
| `scipy` | 1.14.1 | Compatible with NumPy 1.26.4 and Python 3.12 |
| `pandas` | 2.2.3 | Works with NumPy 1.26.4 |
| `scikit-learn` | 1.6.1 | Python 3.12 compatible |

### Bayesian/Causal Stack

| Package | Version | Reason |
|---------|---------|--------|
| `pytensor` | 2.34.0 | Last version supporting NumPy 1.x with Python 3.12 |
| `pymc` | 5.16.2 | Compatible with PyTensor 2.34.0, builds from source on 3.12 |
| `arviz` | 0.20.0 | Compatible with above |
| `dowhy` | 0.12 | Python 3.12 compatible |
| `econml` | 0.15.1 | Python 3.12 compatible |

### ML/DL Stack

| Package | Version | Reason |
|---------|---------|--------|
| `tensorflow` | 2.18.0 | Requires >=2.16 for Python 3.12 |
| `torch` | 2.8.0 | Python 3.12 compatible |
| `transformers` | 4.48.3 | Requires huggingface-hub >= 0.27 |
| `sentence-transformers` | 3.3.1 | Python 3.12 compatible |
| `spacy` | 3.8.3 | Python 3.12 compatible |

### Hugging Face Ecosystem

| Package | Version | Reason |
|---------|---------|--------|
| `huggingface-hub` | 0.27.1 | **CRITICAL**: transformers requires >= 0.27 for full initialization |
| `safetensors` | 0.5.2 | Latest stable |
| `tokenizers` | 0.21.0 | Compatible with transformers 4.48+ |

## Known Issues

### 1. PyMC Installation from Source

PyMC 5.16.2 must be built from source on Python 3.12. This requires:

```bash
# Install build dependencies
pip install Cython setuptools wheel

# Install PyMC (will build from source)
pip install pymc==5.16.2
```

**Build requirements:**
- C compiler (gcc/clang)
- Cython
- NumPy (for build)

### 2. System Dependencies for Native Packages

Several packages require system libraries:

```bash
# Ubuntu/Debian
sudo apt-get install -y \
    ghostscript \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1

# macOS
brew install ghostscript
```

**Packages requiring system libs:**
- `camelot-py` → ghostscript
- `opencv-python` → libGL, libglib2.0
- `torch` → libgomp1
- `spacy` models → system fonts

### 3. Transformers Degradation Warning

If `huggingface-hub < 0.27`, transformers will show:

```
WARNING: huggingface_hub version is too old. Some features may not work.
Falling back to lightweight contradiction components.
```

**Impact:**
- Full pipeline initialization fails
- Degrades to basic components
- Missing advanced features

**Solution:** Ensure `huggingface-hub==0.27.1` is installed.

### 4. Chained Native Dependencies

The following packages have complex native dependency chains:

1. **PyMC** → PyTensor → NumPy → BLAS/LAPACK
2. **Camelot** → opencv-python → libGL → X11 libs
3. **spaCy** → Cython models → system fonts
4. **sentence-transformers** → torch → CUDA (optional)

Each layer can introduce platform-specific failures.

## Installation Strategies

### Strategy 1: Full Install (Recommended)

```bash
# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Upgrade pip and install build tools
pip install --upgrade pip setuptools wheel Cython

# Install core dependencies with constraints
pip install -c constraints.txt -r requirements-core.txt

# Install optional dependencies
pip install -c constraints.txt -r requirements-optional.txt

# Install PyMC (will build from source)
pip install -c constraints.txt pymc==5.16.2 pytensor==2.34.0 arviz==0.20.0

# Verify installation
python scripts/verify_importability.py
```

### Strategy 2: Minimal Install (Skip PyMC)

If PyMC build fails or isn't needed:

```bash
# Install everything except PyMC stack
pip install -c constraints.txt -r requirements-core.txt

# Comment out in code:
# import pymc
# import pytensor
# import arviz
```

### Strategy 3: Docker (Most Reliable)

```dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc g++ make \
    ghostscript \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt constraints.txt ./
RUN pip install --no-cache-dir -c constraints.txt -r requirements.txt

WORKDIR /app
```

## Verification Steps

After installation, verify everything works:

```bash
# 1. Check NumPy version
python -c "import numpy; print(f'NumPy: {numpy.__version__}')"
# Expected: 1.26.4

# 2. Check PyTensor compatibility
python -c "import pytensor; print(f'PyTensor: {pytensor.__version__}')"
# Expected: 2.34.0

# 3. Test PyMC (if installed)
python -c "import pymc; print(f'PyMC: {pymc.__version__}')"
# Expected: 5.16.2 or build from source

# 4. Test Transformers
python -c "import transformers; print(f'Transformers: {transformers.__version__}')"
# Should NOT show huggingface_hub warning

# 5. Run full import audit
python scripts/verify_importability.py
```

## Why Not Downgrade to Python 3.11?

Python 3.11 previously solved some of these headaches (pre-built PyMC wheels, broader package matrix, fewer bleeding-edge issues). **Despite that, the platform now mandates Python 3.12.x** for determinism audits and feature parity with upstream dependencies. Downgrading is prohibited because it fragments the environment and breaks cryptographic proof guarantees.

Therefore, staying on Python 3.12 requires:
- Pinning NumPy 1.26.4 for PyTensor/PyMC compatibility
- Building PyMC from source (or using pre-built artifacts produced internally)
- Installing the system dependencies described above

## Troubleshooting

### Error: `ModuleNotFoundError: No module named 'numpy._core._multiarray_umath'`

**Cause:** Trying to use NumPy 2.0 with PyMC/PyTensor compiled for NumPy 1.x

**Solution:**
```bash
pip install numpy==1.26.4
```

### Error: `ImportError: cannot import name '_ARRAY_API'`

**Cause:** Same as above - NumPy 2.0 API incompatibility

**Solution:** Downgrade to NumPy 1.26.4

### Error: PyMC build fails with "No C compiler found"

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install build-essential

# macOS
xcode-select --install

# Then retry
pip install pymc==5.16.2
```

### Warning: "huggingface_hub version too old"

**Solution:**
```bash
pip install --upgrade huggingface-hub==0.27.1
```

### Error: Camelot fails with "ghostscript not found"

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install ghostscript

# macOS
brew install ghostscript
```

## Alternative: Use NumPy 2.0 Without PyMC

If you don't need Bayesian analysis:

1. Remove PyMC, PyTensor, arviz from requirements
2. Use NumPy 2.0+
3. Update constraints.txt:
   ```
   numpy==2.0.2
   pytensor  # REMOVE
   pymc      # REMOVE
   arviz     # REMOVE
   ```

## Summary

**This is NOT a downgrade issue. This is a binary compatibility requirement.**

- Python 3.12 + PyMC → REQUIRES NumPy 1.26.4
- PyTensor 2.35+ requires NumPy 2.0, but breaks PyMC
- PyTensor 2.34.0 is the bridge version
- All other packages work fine with NumPy 1.26.4

**The versions in requirements.txt are the ONLY working combination for Python 3.12 with the full stack.**
