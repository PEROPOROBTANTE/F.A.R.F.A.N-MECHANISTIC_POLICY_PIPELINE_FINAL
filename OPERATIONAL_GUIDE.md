# OPERATIONAL GUIDE — Installation & First Run (F.A.R.F.A.N)

This guide replaces the legacy `MANUAL_OPERACIONAL.md` and consolidates the only supported ways to install dependencies and run the pipeline. It is focused on operators and analysts who need a repeatable setup.

## 1) Supported Platform & Prerequisites
- OS: Ubuntu/Debian 20.04+ (primary), macOS 13+ (manual path only)
- Python: 3.12.x on `PATH`
- Hardware: 8 GB RAM (16 GB recommended), 5 GB free disk
- Tools: `git`, `bash`, and `sudo` privileges for system packages on Linux

## 2) Primary Install (one command)
Use this unless you are on macOS or cannot use `apt`.
```bash
git clone https://github.com/PEROPOROBTANTE/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE_FINAL.git
cd F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE_FINAL
bash install.sh
source farfan-env/bin/activate
```
What it does:
- Installs system deps (build-essential, openblas, graphviz, ghostscript, JRE, tk)
- Creates `farfan-env/` virtualenv with Python 3.12
- Pins all Python packages (NumPy 1.26.4, scikit-learn 1.6.1, transformers 4.41.2, torch 2.8.0, tensorflow 2.18.0, etc.)
- Attempts SpaCy model downloads (harmless if they fail on restricted networks)

## 3) Manual Install (when `install.sh` is not usable)
**Linux (Ubuntu/Debian)**
```bash
sudo apt-get update && sudo apt-get install -y \
  build-essential python3.12-dev gfortran libopenblas-dev libhdf5-dev \
  ghostscript python3-tk libgraphviz-dev graphviz default-jre

python3.12 -m venv farfan-env
source farfan-env/bin/activate
pip install --upgrade pip setuptools wheel
pip install --no-cache-dir -r requirements.txt
pip install --force-reinstall --no-deps numpy==1.26.4 opencv-python-headless==4.10.0.84
pip install --no-cache-dir -e .
```

**macOS (Homebrew)**
```bash
brew install python@3.12 icu4c pkg-config ghostscript graphviz openjdk
python3.12 -m venv farfan-env
source farfan-env/bin/activate
pip install --upgrade pip setuptools wheel
pip install --no-cache-dir -r requirements.txt
pip install --force-reinstall --no-deps numpy==1.26.4 opencv-python-headless==4.10.0.84
pip install --no-cache-dir -e .
```

Optional (any OS): download SpaCy models after activation
```bash
python -m spacy download es_core_news_lg
python -m spacy download es_dep_news_trf
```

## 4) Verify the Environment
After activation (`source farfan-env/bin/activate`):
```bash
python diagnose_import_error.py           # shows real import failures, not just missing pkgs
python scripts/verify_dependencies.py     # full dependency sanity check
python comprehensive_health_check.sh      # end-to-end readiness probe
```
Expected keys:
- Transformers 4.41.2 + sentence-transformers 3.1.0 + accelerate 1.2.1 import cleanly
- NumPy 1.26.4 with PyMC 5.16.2 / PyTensor <2.26
- OpenCV headless 4.10.0.84 (avoids cv2/NumPy ABI issues)

## 5) Run Your First Analysis
```bash
source farfan-env/bin/activate
python scripts/run_policy_pipeline_verified.py \
  --plan data/plans/Plan_1.pdf \
  --artifacts-dir artifacts/plan1
```
Check `artifacts/plan1/` for generated outputs.

## 6) Maintenance & Tips
- Re-run `bash install.sh` to rebuild a broken env (it recreates `farfan-env/`).
- Keep `requirements.txt` + `install.sh` together in commits; they are version-locked.
- Deprecated scripts: `install_fixed.sh`, `install_dependencies.sh`, and `install-system-deps.sh` are kept only for provenance—prefer `install.sh` or the manual steps above.
- For GPU-enabled boxes, install vendor CUDA/cuDNN packages before running `install.sh`; the pinned torch/tensorflow builds will pick them up automatically.
