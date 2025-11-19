# Installation Guide - F.A.R.F.A.N Mechanistic Policy Pipeline

## Quick Start

```bash
# 1. Install system dependencies
./install-system-deps.sh

# 2. Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Upgrade pip and install Python dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# 4. Download spaCy language model
python -m spacy download es_core_news_sm

# 5. Verify installation
pytest tests/ -v
```

## Detailed Installation Instructions

### 1. System Requirements

- **Python**: 3.12+ (tested on 3.12.1)
- **OS**: Ubuntu 20.04+, Debian 11+, Fedora 35+, macOS 12+
- **Memory**: 8GB RAM minimum, 16GB recommended
- **Disk Space**: 10GB for dependencies and models

### 2. System Dependencies

The project requires several system-level packages that must be installed before Python dependencies:

#### Required System Packages

| Package | Purpose | Required By |
|---------|---------|-------------|
| ghostscript | PDF rendering | camelot-py |
| python3-tk | GUI toolkit | camelot-py |
| graphviz | Graph visualization | networkx, pydot |
| Java JRE | PDF processing | tabula-py |
| build-essential | C/C++ compilation | numpy, scipy, pymc |
| python3-dev | Python headers | various C extensions |
| libopenblas-dev | Linear algebra | numpy, scipy |
| gfortran | Fortran compiler | scipy |

#### Installation Commands

**Ubuntu/Debian:**
```bash
sudo apt-get update && sudo apt-get install -y \
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
```

**macOS:**
```bash
brew install ghostscript tcl-tk graphviz openjdk
```

**Fedora/RHEL:**
```bash
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
```

**Automated Installation:**
```bash
./install-system-deps.sh
```

### 3. Python Environment Setup

#### Create Virtual Environment (Recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Upgrade Core Tools

```bash
pip install --upgrade pip setuptools wheel
```

### 4. Python Dependencies Installation

```bash
pip install -r requirements.txt
```

**Note:** This will install ~100 packages. Installation may take 10-30 minutes depending on your system.

#### Critical Dependencies

The following packages have specific version requirements:

- **numpy==1.26.4**: Required for PyMC/PyTensor compatibility. NumPy 2.0 breaks binary compatibility.
- **pytensor==2.34.0**: Last version supporting NumPy 1.x. Version 2.35+ requires NumPy 2.0.
- **pymc==5.16.2**: Verified compatible with PyTensor 2.34 on Python 3.12.
- **camelot-py[cv]==0.11.0**: PDF table extraction with computer vision backend.
- **sentence-transformers==3.3.1**: Semantic embeddings for policy analysis.

### 5. Post-Installation Steps

#### Download spaCy Language Model

```bash
python -m spacy download es_core_news_sm
```

#### Verify Installation

Run the test suite to verify everything is working:

```bash
pytest tests/ -v
```

All tests should pass. If you see import errors for `camelot` or `sentence_transformers`, verify:

1. System dependencies are installed (especially ghostscript and tk)
2. Virtual environment is activated
3. All packages installed successfully: `pip list | grep -E "camelot|sentence"`

### 6. Common Installation Issues

#### Issue: "No module named 'camelot'"

**Cause:** Missing system dependencies or package not installed.

**Solution:**
```bash
# Install system dependencies
sudo apt-get install ghostscript python3-tk

# Reinstall camelot-py
pip install --force-reinstall camelot-py[cv]==0.11.0
```

#### Issue: "No module named 'sentence_transformers'"

**Cause:** Package not installed or version conflict.

**Solution:**
```bash
pip install --force-reinstall sentence-transformers==3.3.1
```

#### Issue: "Java not found" (tabula-py)

**Cause:** Java JRE not installed.

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install default-jre

# macOS
brew install openjdk

# Verify
java -version
```

#### Issue: PyMC/PyTensor compilation errors

**Cause:** Missing compilers or BLAS libraries.

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install build-essential gfortran libopenblas-dev

# Then reinstall
pip install --force-reinstall --no-binary :all: pytensor==2.34.0
pip install --force-reinstall pymc==5.16.2
```

#### Issue: GPU/CUDA errors with PyTorch

**Cause:** CUDA version mismatch or GPU drivers.

**Solution:**
```bash
# For CPU-only installation (recommended for development)
pip install torch==2.8.0 --index-url https://download.pytorch.org/whl/cpu

# For GPU support, check CUDA version first
nvidia-smi
# Then install matching PyTorch version from https://pytorch.org/get-started/locally/
```

### 7. Development Setup

For development work, also install:

```bash
pip install -e .  # Install package in editable mode
```

### 8. Docker Installation (Alternative)

If you prefer Docker:

```bash
docker build -t farfan-pipeline .
docker run -it farfan-pipeline
```

### 9. Environment Variables

Create a `.env` file in the project root:

```bash
# Example .env file
REDIS_HOST=localhost
REDIS_PORT=6379
LOG_LEVEL=INFO
```

### 10. Verification Checklist

- [ ] Python 3.12+ installed
- [ ] System dependencies installed (ghostscript, tk, graphviz, Java)
- [ ] Virtual environment created and activated
- [ ] All Python packages installed from requirements.txt
- [ ] spaCy model downloaded
- [ ] Tests passing
- [ ] No import errors for critical packages (camelot, sentence_transformers, pymc)

## Support

If you encounter issues not covered here:

1. Check the test output for specific error messages
2. Verify all system dependencies are installed
3. Ensure you're using Python 3.12+
4. Check that you're in the virtual environment
5. Review pip installation logs for compilation errors

## Next Steps

After successful installation:

1. Review `README.md` for project overview
2. Check `tests/` for usage examples
3. Run example notebooks in `notebooks/` (if available)
4. Start the application: `python -m saaaaaa.main`
