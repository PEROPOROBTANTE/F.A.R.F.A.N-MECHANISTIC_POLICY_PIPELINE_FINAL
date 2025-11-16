# Migration Guide: Flat to Hierarchical Structure

This guide helps migrate code and references from the old flat structure to the new hierarchical package structure.

## Summary of Changes

The repository has been reorganized from a flat structure into a standard Python package layout following best practices for data pipelines.

## Import Path Changes

All Python modules have moved from the root directory to `src/saaaaaa/` subdirectories. Here's the mapping:

### Core Modules

**Old:** `from orchestrator import ...`  
**New:** `from saaaaaa.core.orchestrator import ...`

**Note:** ORCHESTRATOR_MONILITH.py and executors_COMPLETE_FIXED.py have been removed. Use the modular orchestrator package instead.

### Processing Modules
**Old:** `import document_ingestion`  
**New:** `from saaaaaa.processing import document_ingestion`

**Old:** `import embedding_policy`  
**New:** `from saaaaaa.processing import embedding_policy`

**Old:** `import semantic_chunking_policy`  
**New:** `from saaaaaa.processing import semantic_chunking_policy`

**Old:** `import aggregation`  
**New:** `from saaaaaa.processing import aggregation`

**Old:** `import policy_processor`  
**New:** `from saaaaaa.processing import policy_processor`

### Analysis Modules
**Old:** `import bayesian_multilevel_system`  
**New:** `from saaaaaa.analysis import bayesian_multilevel_system`

**Old:** `import Analyzer_one`  
**New:** `from saaaaaa.analysis import Analyzer_one`

**Old:** `import contradiction_deteccion`  
**New:** `from saaaaaa.analysis import contradiction_deteccion`

**Old:** `import teoria_cambio`  
**New:** `from saaaaaa.analysis import teoria_cambio`

**Old:** `import derek_beach`  
**New:** `from saaaaaa.analysis import derek_beach`

**Old:** `import financiero_viabilidad_tablas`  
**New:** `from saaaaaa.analysis import financiero_viabilidad_tablas`

**Old:** `import meso_cluster_analysis`  
**New:** `from saaaaaa.analysis import meso_cluster_analysis`

**Old:** `import macro_prompts`  
**New:** `from saaaaaa.analysis import macro_prompts`

**Old:** `import micro_prompts`  
**New:** `from saaaaaa.analysis import micro_prompts`

**Old:** `import recommendation_engine`  
**New:** `from saaaaaa.analysis import recommendation_engine`

**Old:** `from scoring import ...`  
**New:** `from saaaaaa.analysis.scoring import ...`

### API Modules
**Old:** `import api_server`  
**New:** `from saaaaaa.api import api_server`

### Utility Modules
**Old:** `import adapters`  
**New:** `from saaaaaa.utils import adapters`

**Old:** `import contracts`  
**New:** `from saaaaaa.utils import contracts`

**Old:** `import core_contracts`  
**New:** `from saaaaaa.utils import core_contracts`

**Old:** `import signature_validator`  
**New:** `from saaaaaa.utils import signature_validator`

**Old:** `import schema_monitor`  
**New:** `from saaaaaa.utils import schema_monitor`

**Old:** `import validation_engine`  
**New:** `from saaaaaa.utils import validation_engine`

**Old:** `import evidence_registry`  
**New:** `from saaaaaa.utils import evidence_registry`

**Old:** `import metadata_loader`  
**New:** `from saaaaaa.utils import metadata_loader`

**Old:** `from validation import ...`  
**New:** `from saaaaaa.utils.validation import ...`

**Old:** `from determinism import ...`  
**New:** `from saaaaaa.utils.determinism import ...`

### Concurrency Modules
**Old:** `from concurrency import ...`  
**New:** `from saaaaaa.concurrency import ...`

## File Path Changes

### Configuration Files
- `inventory.json` → `config/inventory.json`
- `execution_mapping.yaml` → `config/execution_mapping.yaml`
- `method_counts.json` → `config/method_counts.json`
- `forge_manifest.json` → `config/forge_manifest.json`
- `schemas/` → `config/schemas/`
- `rules/` → `config/rules/`

### Data Files
- `questionnaire_monolith.json` → `data/questionnaire_monolith.json`
- `interaction_matrix.csv` → `data/interaction_matrix.csv`
- `provenance.csv` → `data/provenance.csv`

### Documentation Files
- All `.md` files (except README.md) → `docs/`
- Example: `ARCHITECTURE_DIAGRAM.md` → `docs/ARCHITECTURE_DIAGRAM.md`

### Scripts
- Demo scripts → `examples/`
- Build/validation scripts → `scripts/`

## Configuration Updates

### pyproject.toml
Updated to reflect the new package structure:
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pyright]
include = ["src/saaaaaa/"]
exclude = ["**/__pycache__", "**/.venv", "**/node_modules", "tests/", "examples/", ".git", "minipdm/"]

[tool.coverage.run]
source = ["src/saaaaaa"]
omit = ["tests/*", "examples/*", ".venv/*", "minipdm/*"]
```

## Installation

After the reorganization, install the package in development mode:

```bash
pip install -e .
```

This will:
1. Make the `saaaaaa` package importable
2. Allow changes to be immediately available without reinstallation
3. Support all the new import paths

## Testing Import Changes

To test if imports are working correctly:

```python
# Test core orchestrator imports
from saaaaaa.core.orchestrator import Orchestrator
from saaaaaa.core.orchestrator.executors import MethodExecutor

# Test processing imports
from saaaaaa.processing import document_ingestion
from saaaaaa.processing import embedding_policy

# Test analysis imports
from saaaaaa.analysis import bayesian_multilevel_system
from saaaaaa.analysis.scoring import scoring

# Test utility imports
from saaaaaa.utils import contracts
from saaaaaa.utils.validation import schema_validator

# Test concurrency imports
from saaaaaa.concurrency import concurrency
```

## Common Issues and Solutions

### Issue: ModuleNotFoundError
**Symptom:** `ModuleNotFoundError: No module named 'old_module_name'`  
**Solution:** Update the import to use the new package path (see mappings above)

### Issue: Cannot find config/data files
**Symptom:** `FileNotFoundError` when loading config or data files  
**Solution:** Update file paths to use new locations:
- `config/inventory.json` instead of `inventory.json`
- `data/questionnaire_monolith.json` instead of `questionnaire_monolith.json`

### Issue: Package not installed
**Symptom:** `ModuleNotFoundError: No module named 'saaaaaa'`  
**Solution:** Run `pip install -e .` from the repository root

### Issue: Relative imports broken
**Symptom:** `ImportError: attempted relative import beyond top-level package`  
**Solution:** Use absolute imports starting with `saaaaaa.` instead of relative imports

## Scripts and Tools

### Running Scripts
Scripts in `scripts/` directory may need updating to use new import paths. Update them following the import mapping above.

### Running Examples
Examples in `examples/` directory are excluded from type checking but may need import updates for functionality.

### Running Tests
Tests should continue to work as-is since they import from the package. If tests use file paths, update to new locations:
```python
# Old
with open('inventory.json') as f:
    ...

# New
with open('config/inventory.json') as f:
    ...
```

## Benefits of New Structure

1. **Clear Organization:** Related modules are grouped together
2. **Standard Layout:** Follows PEP 420 and src-layout best practices
3. **Better Tooling:** IDEs and linters understand the structure better
4. **Easy Navigation:** Logical hierarchy makes finding code easier
5. **Scalability:** Easy to add new modules in appropriate locations
6. **Professional:** Matches industry standards for Python projects

## Rollback (Not Recommended)

If needed, the reorganization can be reverted using git:
```bash
git revert <commit-hash>
```

However, moving forward with the new structure is strongly recommended for long-term maintainability.

## Questions?

See `docs/REPOSITORY_STRUCTURE.md` for detailed documentation on the new structure.
