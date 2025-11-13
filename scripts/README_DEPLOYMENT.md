# Deployment Package Generation

This directory contains the script to generate a production-ready deployment package for the SAAAAAA system.

## Overview

The `create_deployment_zip.py` script creates a deployment ZIP file that includes **only the essential files** required to run the system at maximum performance in production, excluding:

- ❌ Deprecated files (e.g., `ORCHESTRATOR_MONILITH.py`)
- ❌ Documentation files (except `README.md` and `QUICKSTART.md`)
- ❌ Development files (tests, examples, IDE configs)
- ❌ Build artifacts and cache files
- ❌ Development tools and scripts

## Usage

### Generate Deployment Package

```bash
# From the repository root
python3 scripts/create_deployment_zip.py
```

This will create:
- `saaaaaa-deployment.zip` - The deployment package (approx. 11 MB)
- `saaaaaa-deployment.txt` - Manifest file listing all included files

### What's Included

The deployment package includes:

✅ **Source Code**
- `src/saaaaaa/` - Main Python package with all runtime code
- All analysis, processing, and infrastructure modules

✅ **Compatibility Shims**
- `orchestrator/`, `concurrency/`, `core/`, `executors/` - Backward compatibility layers
- Root-level compatibility modules (for legacy imports)

✅ **Configuration**
- `config/` - All configuration files, schemas, and rules
- `data/` - Data files including questionnaire and inventories

✅ **Package Files**
- `setup.py`, `pyproject.toml` - Package configuration
- `requirements.txt`, `requirements_atroz.txt` - Dependencies
- `constraints.txt` - Version constraints

✅ **Essential Documentation**
- `README.md` - Project overview
- `QUICKSTART.md` - Quick start guide

### What's Excluded

The deployment package excludes:

🚫 **Deprecated Files**
- `src/saaaaaa/core/orchestrator/ORCHESTRATOR_MONILITH.py` - Deprecated monolithic orchestrator
- `docs/README_MONOLITH.md` - Deprecated documentation

🚫 **Development Files**
- All `.md` files except `README.md` and `QUICKSTART.md`
- `tests/` - Test suite
- `examples/` - Example scripts
- `tools/` - Development tools
- `.github/`, `.augment/` - CI/CD and development configs

🚫 **IDE and Dev Tools**
- `.vscode/`, `.idea/` - IDE configurations
- `.DS_Store`, `.gitignore` - Development files
- `.pre-commit-config.yaml`, `.importlinter` - Development tools

🚫 **Build Artifacts**
- `__pycache__/`, `*.pyc`, `*.pyo` - Python cache
- `.pytest_cache/`, `.mypy_cache/` - Testing cache
- Build and distribution directories

## Deployment

### Extract and Install

```bash
# Extract the deployment package
unzip saaaaaa-deployment.zip -d /path/to/deployment

# Navigate to deployment directory
cd /path/to/deployment

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .

# Verify installation
python -c "from saaaaaa.core.orchestrator import Orchestrator; print('✅ Installation successful')"
```

### Production Considerations

1. **Performance**: The deployment package is optimized for maximum performance by excluding unnecessary files
2. **Size**: Approximately 11 MB (vs 33 MB for full repository)
3. **Security**: No development files or credentials are included
4. **Dependencies**: All runtime dependencies are specified in `requirements.txt`

## Verification

The script automatically generates a manifest file (`saaaaaa-deployment.txt`) that lists all included files. Review this file to verify the package contents.

### Check Package Contents

```bash
# View manifest
cat saaaaaa-deployment.txt

# List files in ZIP
unzip -l saaaaaa-deployment.zip

# Verify no deprecated files
unzip -l saaaaaa-deployment.zip | grep -i monolith | grep -v questionnaire
```

## Performance Optimization

The deployment package is optimized for production performance:

1. **No deprecated code**: Ensures no deprecated modules are loaded
2. **Minimal file size**: Reduces deployment time and storage
3. **Clean imports**: Only necessary compatibility shims included
4. **No test overhead**: Test files excluded to reduce package size

## Maintenance

When adding new files to the repository, update the `create_deployment_zip.py` script:

- Add essential runtime files to `INCLUDE_PATTERNS`
- Add development/deprecated files to `EXCLUDE_PATTERNS`

## Support

For issues or questions about deployment:
1. Review the manifest file to verify package contents
2. Check the script output for excluded file counts
3. Consult `README.md` and `QUICKSTART.md` in the deployment package
