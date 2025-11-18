# F.A.R.F.A.N Installation Guide

## Quick Start (Automated)

```bash
bash install.sh
```

**This single command installs everything:**
- ✅ System dependencies (build-essential, gfortran, ghostscript, etc.)
- ✅ Python 3.12 virtual environment
- ✅ ALL Python packages with exact compatible versions
- ✅ Verifies installation with diagnostic script

**Expected time:** 10-15 minutes (depending on network speed)

---

## What Gets Installed

### Core Stack (with exact versions)
```
Python: 3.12.3
numpy: 1.26.4
scikit-learn: 1.6.1
scipy: 1.14.1
pandas: 2.2.3
```

### ML/DL Frameworks
```
tensorflow: 2.18.0
tf-keras: 2.18.0       # Fixes Keras 3 incompatibility
torch: 2.8.0
torchvision: 0.23.0
```

### NLP Stack (CRITICAL VERSIONS)
```
transformers: 4.41.2              # ✓ Compatible with accelerate 1.2.1
sentence-transformers: 3.1.0      # ✓ No TorchTensorParallelPlugin error
accelerate: 1.2.1                 # ✓ Stable version
spacy: 3.8.3
```

### Bayesian Inference
```
pytensor: 2.25.5 (range: >=2.25.1,<2.26)
pymc: 5.16.2
arviz: 0.20.0
```

### PDF Processing
```
PyMuPDF: 1.25.2
pdfplumber: 0.11.4
tabula-py: 2.10.0
camelot-py: 0.11.0
opencv-python-headless: 4.10.0.84  # Forced compatible version
```

---

## Requirements

### System Requirements
- **OS:** Ubuntu 20.04+ / Debian 11+ (or compatible Linux)
- **Python:** 3.12.x (must be installed)
- **RAM:** 8GB minimum, 16GB recommended
- **Disk:** 5GB free space
- **sudo access:** Required for system dependencies

### Install Python 3.12 (if not present)
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3.12 python3.12-venv python3.12-dev
```

---

## Installation Steps

### 1. Clone and Navigate
```bash
git clone https://github.com/PEROPOROBTANTE/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE_FINAL.git
cd F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE_FINAL
```

### 2. Pull Latest Fixes
```bash
git checkout claude/fix-deployment-issues-01TqDr4epcBunhuqtuXmmn2o
git pull origin claude/fix-deployment-issues-01TqDr4epcBunhuqtuXmmn2o
```

### 3. Run Install Script
```bash
bash install.sh
```

The script will:
1. ✓ Check Python 3.12
2. ✓ Install system dependencies (needs sudo)
3. ✓ Create `farfan-env/` virtual environment
4. ✓ Upgrade pip, setuptools, wheel
5. ✓ Install core dependencies (numpy, scipy, pandas, scikit-learn)
6. ✓ Install ML/DL frameworks (tensorflow, torch, pymc)
7. ✓ Install NLP stack **with exact compatible versions**
8. ✓ Install PDF processing tools
9. ⚠ Attempt SpaCy model downloads (may fail due to network)
10. ✓ Run verification diagnostics

### 4. Activate Environment
```bash
source farfan-env/bin/activate
```

### 5. Verify Installation
```bash
# Quick diagnostic (shows actual import errors, not just "NOT INSTALLED")
python diagnose_import_error.py

# Full dependency check
python scripts/verify_dependencies.py
```

**Expected output:**
```
transformers           ✓ OK
sentence_transformers  ✓ OK
accelerate            ✓ OK

✓ Successfully loaded 22 classes
Passed: 5/6 checks
```

---

## Troubleshooting

### Issue: "sentence_transformers: Semantic embeddings - NOT INSTALLED"

**Diagnosis:**
```bash
python diagnose_import_error.py
```

**If you see:**
```
✓ Installed: Version: 3.3.1
✗ ImportError: cannot import name 'TorchTensorParallelPlugin'
```

**Solution:** You have the WRONG transformers version (4.42+). Fix:
```bash
source farfan-env/bin/activate
pip install --no-cache-dir transformers==4.41.2 sentence-transformers==3.1.0 accelerate==1.2.1
```

### Issue: "scikit-learn version conflict"

**Check versions:**
```bash
pip show scikit-learn
```

**Should be:** 1.6.1

**Fix:**
```bash
pip install --force-reinstall scikit-learn==1.6.1
```

### Issue: "SpaCy models not downloading"

**This is normal** in restricted network environments (403 Forbidden from GitHub releases).

**Manual fix:**
```bash
# After installation completes, download models directly:
python -m spacy download es_core_news_lg
python -m spacy download es_dep_news_trf
```

**Note:** The system works without SpaCy models, but some processors (CDAF, Financial) will have limited functionality.

### Issue: "numpy version conflict with opencv-python-headless"

**Fix:** (Already handled by install.sh)
```bash
pip install --force-reinstall --no-deps numpy==1.26.4
pip install --no-deps opencv-python-headless==4.10.0.84
```

---

## Manual Installation (Advanced)

If `install.sh` fails, install manually:

```bash
# 1. System dependencies
sudo apt-get install -y build-essential python3.12-dev gfortran \
  libopenblas-dev libhdf5-dev ghostscript python3-tk \
  libgraphviz-dev graphviz default-jre

# 2. Virtual environment
python3.12 -m venv farfan-env
source farfan-env/bin/activate

# 3. Upgrade tools
pip install --upgrade pip setuptools wheel

# 4. Install from requirements.txt (contains all fixed versions)
pip install --no-cache-dir -r requirements.txt

# 5. Force compatible versions
pip install --force-reinstall --no-deps numpy==1.26.4
pip install --no-deps opencv-python-headless==4.10.0.84

# 6. Install package
pip install --no-cache-dir -e .

# 7. Verify
python diagnose_import_error.py
```

---

## Verification Commands

### Check All Installed Versions
```bash
source farfan-env/bin/activate
pip list | grep -E "transformers|sentence-transformers|torch|tensorflow|pymc|pytensor|scikit-learn|numpy"
```

### Expected Output:
```
accelerate                1.2.1
arviz                     0.20.0
numpy                     1.26.4
pymc                      5.16.2
pytensor                  2.25.5
scikit-learn              1.6.1
sentence-transformers     3.1.0
tensorflow                2.18.0
torch                     2.8.0
transformers              4.41.2
```

### Test Critical Imports
```bash
python -c "
from saaaaaa.processing.policy_processor import IndustrialPolicyProcessor
from saaaaaa.analysis.contradiction_detection import PolicyContradictionDetector
from saaaaaa.processing.embedding_policy import PolicyAnalysisEmbedder
print('✓ All critical classes import successfully')
"
```

---

## Files Modified (For Reference)

This installation fixes the following dependency issues:

| File | Change | Reason |
|------|--------|--------|
| `setup.py` | pytensor: 2.34→2.25.1-2.26 | pymc 5.16.2 compatibility |
| | pymc: >=5.16.0→==5.16.2 | Fix version conflict |
| | transformers: >=4.48.0→>=4.41.0,<4.42.0 | Avoid TorchTensorParallelPlugin bug |
| | sentence-transformers: >=3.0.0→>=3.1.0,<3.2.0 | Compatibility |
| `requirements.txt` | transformers: 4.53.0→4.41.2 | Fix TorchTensorParallelPlugin |
| | sentence-transformers: 3.3.1→3.1.0 | Compatibility |
| | scikit-learn: 1.5.2→1.6.1 | Remove econml constraint |
| | Removed: dowhy, econml | Not used in codebase |
| `.gitignore` | Added: farfan-env/ | Exclude venv from git |

---

## Common Issues Explained

### 1. TorchTensorParallelPlugin Error
**What happened:** transformers 4.42+ tries to import `TorchTensorParallelPlugin` from accelerate, but this class was removed in accelerate 1.0+.

**Solution:** Use transformers 4.41.2 (last version before the problematic import).

### 2. econml vs scikit-learn Conflict
**What happened:** econml 0.15.1 requires `scikit-learn<1.6`, but saaaaaa needs `scikit-learn>=1.6`.

**Solution:** Removed econml (not used in codebase).

### 3. Keras 3 Incompatibility
**What happened:** tensorflow 2.18+ uses Keras 3, but transformers doesn't support it yet.

**Solution:** Install `tf-keras` (Keras 2.x compatibility wrapper).

---

## Support

**If installation still fails:**

1. Check Python version: `python3.12 --version` (must be 3.12.x)
2. Run diagnostic: `python diagnose_import_error.py`
3. Check logs: Installation output shows specific errors
4. Verify git branch: `git branch` (should show `claude/fix-deployment-issues-*`)

**Get help:**
- GitHub Issues: https://github.com/PEROPOROBTANTE/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE_FINAL/issues
- Include output of: `python diagnose_import_error.py`
