# Dependency Documentation - F.A.R.F.A.N Pipeline

## Critical Dependencies Analysis

This document details the critical dependencies that have caused test failures and require careful installation.

## 1. camelot-py (PDF Table Extraction)

### Package Information
- **PyPI Package**: `camelot-py[cv]==0.11.0`
- **Import Name**: `camelot`
- **Purpose**: Extract tables from PDF documents

### System Dependencies Required

**CRITICAL:** camelot-py WILL NOT WORK without these system packages:

1. **ghostscript** - PDF rendering engine
   - Ubuntu/Debian: `sudo apt-get install ghostscript`
   - macOS: `brew install ghostscript`
   - Fedora/RHEL: `sudo dnf install ghostscript`

2. **tkinter/python3-tk** - GUI toolkit for table detection
   - Ubuntu/Debian: `sudo apt-get install python3-tk`
   - macOS: Usually pre-installed with Python
   - Fedora/RHEL: `sudo dnf install tk`

3. **OpenCV** - Computer vision for table detection (installed via pip)
   - Installed automatically with `camelot-py[cv]`

### Python Dependencies
```
opencv-python==4.10.0.84
opencv-python-headless==4.10.0.84
PyPDF2==3.0.1
pdfplumber==0.11.4
Pillow==11.0.0
```

### Installation Verification
```python
import camelot
tables = camelot.read_pdf('test.pdf')
print(f"Found {len(tables)} tables")
```

### Common Errors

**Error:** `No module named 'camelot'`
- **Cause:** Package not installed
- **Fix:** `pip install camelot-py[cv]==0.11.0`

**Error:** `GhostscriptNotFound`
- **Cause:** ghostscript not installed or not in PATH
- **Fix:** Install ghostscript system package

**Error:** `ImportError: libtk8.6.so`
- **Cause:** tkinter not installed
- **Fix:** `sudo apt-get install python3-tk`

## 2. sentence-transformers (Semantic Embeddings)

### Package Information
- **PyPI Package**: `sentence-transformers==3.3.1`
- **Import Name**: `sentence_transformers`
- **Purpose**: Generate semantic embeddings for policy text analysis

### System Dependencies
- **None required** - Pure Python with C extensions

### Python Dependencies
```
transformers==4.53.0
torch==2.8.0
torchvision==0.19.0
numpy==1.26.4
scipy==1.14.1
scikit-learn==1.6.1
nltk==3.9.1
sentencepiece==0.2.0
huggingface-hub==0.27.1
tokenizers==0.21.0
safetensors==0.5.2
accelerate==1.2.1
```

### Installation Verification
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
embeddings = model.encode(['Test sentence'])
print(f"Embedding shape: {embeddings.shape}")
```

### Common Errors

**Error:** `No module named 'sentence_transformers'`
- **Cause:** Package not installed
- **Fix:** `pip install sentence-transformers==3.3.1`

**Error:** `ImportError: cannot import name 'SentenceTransformer'`
- **Cause:** Version conflict with transformers
- **Fix:**
  ```bash
  pip install --force-reinstall transformers==4.53.0
  pip install --force-reinstall sentence-transformers==3.3.1
  ```

**Error:** CUDA/GPU errors
- **Cause:** PyTorch trying to use GPU but CUDA not configured
- **Fix:** Use CPU-only PyTorch:
  ```bash
  pip install torch==2.8.0 --index-url https://download.pytorch.org/whl/cpu
  ```

## 3. tabula-py (PDF Table Extraction - Alternative Method)

### Package Information
- **PyPI Package**: `tabula-py==2.10.0`
- **Import Name**: `tabula`
- **Purpose**: Java-based PDF table extraction

### System Dependencies Required

**CRITICAL:** tabula-py requires Java Runtime Environment:

1. **Java JRE/JDK** (version 8 or higher)
   - Ubuntu/Debian: `sudo apt-get install default-jre`
   - macOS: `brew install openjdk`
   - Fedora/RHEL: `sudo dnf install java-11-openjdk`

### Installation Verification
```bash
java -version  # Should show Java version
```

```python
import tabula
df = tabula.read_pdf("test.pdf", pages='all')
print(f"Extracted {len(df)} dataframes")
```

### Common Errors

**Error:** `JavaNotFoundError`
- **Cause:** Java not installed or not in PATH
- **Fix:** Install Java JRE and verify with `java -version`

## 4. PyMC/PyTensor Stack (Bayesian Analysis)

### Critical Version Requirements

**IMPORTANT:** These versions are NOT arbitrary - they are carefully pinned for compatibility.

```
numpy==1.26.4        # NumPy 2.0 breaks PyMC binary compatibility
pytensor==2.34.0     # Last version supporting NumPy 1.x
pymc==5.16.2         # Compatible with PyTensor 2.34
arviz==0.20.0        # Visualization for PyMC
```

### Why These Specific Versions?

1. **NumPy 1.26.4**: PyMC and PyTensor compile against NumPy C API. NumPy 2.0 changed the ABI, breaking binary compatibility.

2. **PyTensor 2.34.0**: Last version before NumPy 2.0 requirement. Version 2.35+ requires NumPy 2.0.

3. **PyMC 5.16.2**: Verified to compile and run with PyTensor 2.34 on Python 3.11/3.12.

### System Dependencies for Compilation
```bash
# Ubuntu/Debian
sudo apt-get install build-essential gfortran libopenblas-dev liblapack-dev

# macOS
xcode-select --install
brew install openblas lapack
```

### Installation Verification
```python
import pymc as pm
import pytensor
import numpy as np

print(f"NumPy: {np.__version__}")
print(f"PyTensor: {pytensor.__version__}")
print(f"PyMC: {pm.__version__}")

# Should print:
# NumPy: 1.26.4
# PyTensor: 2.34.0
# PyMC: 5.16.2
```

## 5. Complete Dependency Graph

### Core Scientific Stack
```
numpy==1.26.4
  └── scipy==1.14.1
      └── scikit-learn==1.6.1
      └── pandas==2.2.3
      └── pytensor==2.34.0
          └── pymc==5.16.2
              └── arviz==0.20.0
```

### Deep Learning Stack
```
torch==2.8.0
  └── torchvision==0.19.0
  └── transformers==4.53.0
      └── sentence-transformers==3.3.1
      └── huggingface-hub==0.27.1
      └── tokenizers==0.21.0
      └── accelerate==1.2.1
```

### PDF Processing Stack
```
opencv-python==4.10.0.84
  └── camelot-py[cv]==0.11.0
      └── ghostscript (system)
      └── tkinter (system)

PyPDF2==3.0.1
pdfplumber==0.11.4
tabula-py==2.10.0
  └── Java JRE (system)
```

### Web Framework Stack
```
fastapi==0.115.6
  └── uvicorn[standard]==0.34.0
  └── pydantic==2.10.6
      └── pydantic-settings==2.7.0

flask==3.0.3
  └── flask-cors==6.0.0
  └── flask-socketio==5.4.1
  └── werkzeug==3.0.6
```

## 6. Installation Order (Critical)

To avoid dependency conflicts, install in this order:

```bash
# 1. System dependencies FIRST
./install-system-deps.sh

# 2. Upgrade pip/setuptools
pip install --upgrade pip setuptools wheel

# 3. Core scientific stack
pip install numpy==1.26.4
pip install scipy==1.14.1
pip install pandas==2.2.3

# 4. PyMC stack (may take time to compile)
pip install pytensor==2.34.0
pip install pymc==5.16.2

# 5. Deep learning (large downloads)
pip install torch==2.8.0 torchvision==0.19.0

# 6. All remaining packages
pip install -r requirements.txt

# 7. Post-installation
python -m spacy download es_core_news_sm
```

**OR** simply:
```bash
pip install -r requirements.txt
```
(requirements.txt already has correct ordering)

## 7. Troubleshooting Matrix

| Error Message | Missing Dependency | Solution |
|---------------|-------------------|----------|
| `No module named 'camelot'` | camelot-py | `pip install camelot-py[cv]==0.11.0` |
| `No module named 'sentence_transformers'` | sentence-transformers | `pip install sentence-transformers==3.3.1` |
| `GhostscriptNotFound` | ghostscript (system) | `sudo apt-get install ghostscript` |
| `ImportError: libtk8.6.so` | python3-tk (system) | `sudo apt-get install python3-tk` |
| `JavaNotFoundError` | Java JRE (system) | `sudo apt-get install default-jre` |
| PyMC compilation errors | build tools | `sudo apt-get install build-essential gfortran` |
| NumPy version conflicts | Wrong numpy version | `pip install --force-reinstall numpy==1.26.4` |

## 8. Verification Script

Run this script to verify all critical dependencies:

```python
#!/usr/bin/env python3
"""Verify all critical dependencies are installed correctly."""

import sys

def check_import(module_name, package_name=None):
    """Try to import a module and report status."""
    try:
        __import__(module_name)
        print(f"✓ {module_name}")
        return True
    except ImportError as e:
        pkg = package_name or module_name
        print(f"✗ {module_name} - Install with: pip install {pkg}")
        print(f"  Error: {e}")
        return False

def main():
    print("Checking critical dependencies...\n")

    checks = [
        ('camelot', 'camelot-py[cv]==0.11.0'),
        ('sentence_transformers', 'sentence-transformers==3.3.1'),
        ('tabula', 'tabula-py==2.10.0'),
        ('pymc', 'pymc==5.16.2'),
        ('pytensor', 'pytensor==2.34.0'),
        ('transformers', 'transformers==4.53.0'),
        ('torch', 'torch==2.8.0'),
        ('cv2', 'opencv-python==4.10.0.84'),
        ('spacy', 'spacy==3.8.3'),
        ('networkx', 'networkx==3.4.2'),
        ('fastapi', 'fastapi==0.115.6'),
        ('flask', 'flask==3.0.3'),
    ]

    results = [check_import(mod, pkg) for mod, pkg in checks]

    print(f"\n{sum(results)}/{len(results)} dependencies OK")

    if not all(results):
        print("\nSome dependencies are missing. Run:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    else:
        print("\n✓ All critical dependencies installed!")

        # Version checks
        import numpy, pytensor, pymc
        print(f"\nVersion verification:")
        print(f"  NumPy: {numpy.__version__} (expected 1.26.4)")
        print(f"  PyTensor: {pytensor.__version__} (expected 2.34.0)")
        print(f"  PyMC: {pymc.__version__} (expected 5.16.2)")

if __name__ == '__main__':
    main()
```

Save as `verify_dependencies.py` and run:
```bash
python verify_dependencies.py
```

## 9. Docker Alternative

If system dependency installation is problematic, use Docker:

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ghostscript \
    python3-tk \
    graphviz \
    default-jre \
    build-essential \
    gfortran \
    libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download es_core_news_sm
```

## Summary

The test failures you experienced were due to missing **system dependencies**, not missing Python packages. The key issues:

1. **camelot-py** requires **ghostscript** and **python3-tk** (system packages)
2. **tabula-py** requires **Java JRE** (system package)
3. These cannot be installed via pip alone

**Solution:** Run `./install-system-deps.sh` before `pip install -r requirements.txt`
