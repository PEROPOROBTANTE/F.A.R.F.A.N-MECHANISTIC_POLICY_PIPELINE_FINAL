# Dependency Resolution Fix - CI Installation Failure

## Problem

The CI installation was failing with:
```
ResolutionImpossible: pip returned exit code 1
Installing saaaaaa==0.1.0 pulled in packages (e.g., fastapi, pydantic, arviz, scipy, numpy) 
that conflict with other required versions.
pymc requires pytensor in a constrained range but a compatible pytensor distribution was 
not available for the environment.
```

## Root Cause

The issue was in **`setup.py`** (lines 28-37):

```python
# PROBLEMATIC CODE - Reading strict pins from requirements.txt
requirements_file = Path(__file__).parent / "requirements.txt"
install_requires = []
if requirements_file.exists():
    with open(requirements_file, encoding="utf-8") as f:
        install_requires = [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]
```

This code read ALL packages from `requirements.txt` with **exact version pins** (e.g., `numpy==1.26.4`, `pytensor==2.34.0`, `pymc==5.16.2`) and used them as `install_requires` in the package metadata.

When pip tried to install the package:
1. It saw `install_requires` with strict pins like `numpy==1.26.4`
2. But `pyproject.toml` had flexible ranges like `numpy>=1.26.0,<2.0`
3. Other dependencies (fastapi, pydantic, etc.) had their own version requirements
4. The combination of strict pins + flexible ranges created an unsolvable constraint set
5. Result: **ResolutionImpossible**

## Solution

### 1. Fixed `setup.py`

Replaced strict pins from `requirements.txt` with **flexible version ranges**:

```python
# Use flexible dependency ranges instead of strict pins from requirements.txt
# requirements.txt is for development/production pinning, not for package metadata
install_requires = [
    "numpy>=1.26.0,<2.0",
    "pandas>=2.2.0",
    "scipy>=1.14.0",
    "scikit-learn>=1.6.0",
    "networkx>=3.4.0",
    "pydantic>=2.10.0",
    # ... etc (flexible ranges)
]
```

### 2. Made Heavy Dependencies Optional

Moved PyMC, PyTensor, torch, and tensorflow to **optional extras**:

```python
extras_require={
    "bayesian": [
        "pytensor>=2.34.0,<2.35",
        "pymc>=5.16.0",
        "arviz>=0.20.0",
    ],
    "ml": [
        "torch>=2.0.0",
        "tensorflow>=2.16.0",
    ],
    "all": [
        # All optional packages
    ],
}
```

**Why?**
- These packages have complex dependency chains that can cause conflicts
- Not all users need Bayesian analysis or deep learning
- Users can explicitly opt-in: `pip install -e ".[bayesian]"`

### 3. Updated `pyproject.toml`

Synchronized the dependency lists and moved heavy packages to optional extras.

### 4. Fixed Python Version Range

Changed from `>=3.10,<3.13` to `>=3.10,<3.14` to properly support Python 3.12.

## Installation Methods

### For End Users (Recommended)
```bash
# Basic installation (core features only)
pip install -e .

# With Bayesian analysis support
pip install -e ".[bayesian]"

# With ML/DL support
pip install -e ".[ml]"

# Everything
pip install -e ".[all]"
```

### For Development/Production (Exact Pins)
```bash
# Install with exact versions from requirements.txt
pip install -c constraints-complete.txt -r requirements.txt
```

## Key Differences

| Aspect | `pip install -e .` | `requirements.txt` |
|--------|-------------------|-------------------|
| Purpose | Package installation | Development/production pinning |
| Versions | Flexible ranges | Exact pins |
| PyMC/torch | Optional extras | Included by default |
| Use case | Most users, CI | Reproducible environments |
| Conflicts | Rare | Can occur if over-constrained |

## Technical Explanation

**Package metadata vs. requirements files:**

- **Package metadata** (`setup.py`, `pyproject.toml`): Should use flexible version ranges
  - Example: `numpy>=1.26.0,<2.0`
  - Allows pip to find compatible versions
  - Used when installing the package with `pip install`

- **Requirements files** (`requirements.txt`): Can use exact pins
  - Example: `numpy==1.26.4`
  - For reproducible environments
  - Used with `pip install -r requirements.txt`

**The mistake:** Using exact pins from requirements.txt in package metadata creates an over-constrained system that pip cannot resolve.

## Verification

The fix was verified with:
```bash
python3 -m pip install --dry-run -e .
# Successfully resolves all dependencies without conflicts
```

## Impact on CI

The CI workflow should now use:
```yaml
- name: Install package
  run: pip install -e ".[all]"  # Installs with flexible ranges
```

Or for exact reproducibility:
```yaml
- name: Install dependencies
  run: pip install -c constraints-complete.txt -r requirements.txt
```

## Summary

**Problem:** setup.py used strict version pins from requirements.txt, causing dependency conflicts  
**Solution:** Use flexible ranges in setup.py, make heavy packages optional extras  
**Result:** Package installs successfully with pip's dependency resolver  
**Benefit:** Users can choose basic install or opt-in to heavy dependencies

## Additional Fixes

### Keras 3 Compatibility Issue

**Problem:** TensorFlow 2.16+ ships with Keras 3, which is incompatible with transformers.

**Error:**
```
Incompatible ML stack — installed Keras 3 is not supported by transformers.
The logs instruct to install the backwards-compatible tf-keras package.
```

**Solution:** Added `tf-keras>=2.16.0` to the `ml` and `all` extras:
```python
"ml": [
    "torch>=2.0.0",
    "tensorflow>=2.16.0",
    "tf-keras>=2.16.0",  # Required for transformers compatibility
]
```

This ensures that when TensorFlow is installed, the backward-compatible tf-keras is also installed for transformers compatibility.

### Missing NLTK Dependency

**Problem:** NLTK was in `requirements.txt` but not in `requirements-core.txt` or `setup.py`, causing runtime errors.

+**Solution:** Added `nltk>=3.9.0` to:
- `setup.py` install_requires
- `pyproject.toml` dependencies
- `requirements-core.txt`
