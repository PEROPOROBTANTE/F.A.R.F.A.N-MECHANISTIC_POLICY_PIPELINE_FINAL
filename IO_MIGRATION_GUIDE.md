# I/O Boundary Refactoring - Migration Guide

## Overview

The core orchestrator modules have been refactored to eliminate I/O operations, following the **Ports and Adapters** (Hexagonal Architecture) pattern. All file I/O is now centralized in `factory.py`, making core modules pure, testable, and free of external dependencies.

## What Changed

### Before (Old API - Deprecated)
```python
# ❌ Old way - triggers file I/O in constructor
from saaaaaa.core.orchestrator import Orchestrator

orchestrator = Orchestrator(
    catalog_path="rules/METODOS/complete_canonical_catalog.json",
    monolith_path="questionnaire_monolith.json",
    method_map_path="COMPLETE_METHOD_CLASS_MAP.json",
    schema_path="schemas/questionnaire.schema.json"
)
```

### After (New API - Recommended)
```python
# ✅ New way - I/O-free initialization
from saaaaaa.core.orchestrator import Orchestrator
from saaaaaa.core.orchestrator.factory import (
    load_catalog,
    load_questionnaire_monolith,
    load_method_map,
    load_schema,
)

# Step 1: Load data using factory (I/O layer)
catalog = load_catalog()
monolith = load_questionnaire_monolith()
method_map = load_method_map()
schema = load_schema()

# Step 2: Initialize orchestrator with pre-loaded data (pure business logic)
orchestrator = Orchestrator(
    catalog=catalog,
    monolith=monolith,
    method_map=method_map,
    schema=schema,
)
```

## Architecture Changes

### 1. `__init__.py` - QuestionnaireProvider
**Before:** Loaded data from disk
```python
provider = _QuestionnaireProvider()
data = provider.load()  # ❌ Triggers file I/O
```

**After:** Accepts pre-loaded data
```python
from saaaaaa.core.orchestrator import get_questionnaire_provider
from saaaaaa.core.orchestrator.factory import load_questionnaire_monolith

# Load data via factory
monolith = load_questionnaire_monolith()

# Set in provider
get_questionnaire_provider().set_data(monolith)

# Now can get without I/O
data = get_questionnaire_provider().get_data()  # ✅ No I/O
```

### 2. `core.py` - Orchestrator Class
**Changes:**
- Constructor now accepts `catalog`, `monolith`, `method_map`, `schema` data parameters
- All I/O operations removed from `__init__` and `_load_configuration`
- Legacy file path parameters deprecated (will be removed in future version)

**Migration:**
```python
# Before
orchestrator = Orchestrator(catalog_path="...")  # ❌ Deprecated

# After  
catalog = load_catalog(Path("..."))
orchestrator = Orchestrator(catalog=catalog)  # ✅ Recommended
```

### 3. `factory.py` - Centralized I/O
**New Functions:**
- `load_catalog(path)` - Load method catalog JSON
- `load_questionnaire_monolith(path)` - Load questionnaire monolith
- `load_method_map(path)` - Load method-class mapping
- `load_schema(path)` - Load questionnaire schema
- `load_document(path)` - Load and parse documents
- `save_results(results, path)` - Save analysis results

**All file I/O now happens here.**

## Modules Excluded from Boundary Scan

The following modules are designated for I/O operations and excluded from the boundary scan:

1. **`factory.py`** - Designated I/O module for all data loading
2. **`contract_loader.py`** - JSON contract loader utility
3. **`evidence_registry.py`** - Evidence storage with JSONL persistence
4. **`ORCHESTRATOR_MONILITH.py`** - Deprecated monolith (scheduled for removal)

## Benefits

### 1. Testability
```python
# Easy to test with mock data - no file dependencies
mock_catalog = {"method1": {...}, "method2": {...}}
orchestrator = Orchestrator(catalog=mock_catalog)
```

### 2. Performance
```python
# Load data once, create multiple orchestrators
catalog = load_catalog()
monolith = load_questionnaire_monolith()

orch1 = Orchestrator(catalog=catalog, monolith=monolith)
orch2 = Orchestrator(catalog=catalog, monolith=monolith)
# No redundant file I/O!
```

### 3. Flexibility
```python
# Easy to inject different data sources (DB, API, cache, etc.)
catalog = fetch_from_database()  # Or any other source
orchestrator = Orchestrator(catalog=catalog)
```

### 4. Clear Separation
- **I/O Layer:** `factory.py`, `contract_loader.py`, `evidence_registry.py`
- **Business Logic:** `core.py`, `__init__.py`, other orchestrator modules
- No mixing of concerns!

## Verification

Run the boundary scanner to verify no I/O violations:

```bash
python tools/scan_boundaries.py --root src/saaaaaa/core/orchestrator \
                                 --fail-on main,io \
                                 --allow-path factory.py contract_loader.py \
                                              ORCHESTRATOR_MONILITH.py evidence_registry.py
```

Expected output:
```
✅ All files are clean! No boundary violations detected.
Total violations: 0
```

## Examples

See:
- `examples/orchestrator_io_free_example.py` - Demonstrates the new I/O-free initialization pattern

## Breaking Changes

### Removed
- Direct file I/O in `Orchestrator.__init__()` (use factory instead)
- Direct file I/O in `_QuestionnaireProvider.load()` (use factory + set_data instead)

### Deprecated
- File path parameters in `Orchestrator.__init__()` (will be removed in v2.0)

## Timeline

- **v1.x (Current):** New I/O-free API available, legacy paths deprecated
- **v2.0 (Future):** Legacy file path parameters will be removed entirely

## Questions?

For questions or issues, see:
- Architecture documentation: `ARCHITECTURE_REFACTORING.md`
- Factory API: `src/saaaaaa/core/orchestrator/factory.py`
- Examples: `examples/orchestrator_io_free_example.py`
