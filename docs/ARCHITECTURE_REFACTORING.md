# Core Module Architecture - Refactoring Guide

## Overview

This repository is undergoing a major architectural refactoring to separate concerns between:
- **Core modules** (pure library code, no I/O)
- **Orchestrator** (I/O, dependency injection, coordination)
- **Executors** (business logic using core modules)

## Goals

1. ✅ **Pure core modules**: No I/O operations, no side effects, fully testable
2. ✅ **Type-safe contracts**: All interfaces defined with TypedDict
3. ✅ **Dependency injection**: Factory pattern for all dependencies
4. ⏳ **Separation of concerns**: I/O in orchestrator, computation in core
5. ⏳ **Easy testing**: Mock contracts instead of mocking I/O

## Current Status

### ✅ Completed (Phase 1-6)
- [x] Fixed critical syntax bug in semantic_chunking_policy.py
- [x] Removed all `__main__` blocks from core modules
- [x] Created contract definitions for all 7 core modules
- [x] Built boundary enforcement tooling (scanner, tests)
- [x] Added CI/CD pipeline for boundary checks
- [x] Documented API surface map

### ⏳ In Progress (Phase 7-10)
- [ ] Migrate ~150 I/O operations to orchestrator/factory.py
- [ ] Update executors to use contract-based APIs
- [ ] Move demo code to examples/ directory
- [ ] Enable strict boundary enforcement in CI

## Architecture

### Before Refactoring
```
Core Module (Analyzer_one.py)
├── Business Logic
├── I/O Operations ❌
├── Demo Code ❌
└── __main__ block ❌

Executor calls methods directly
└── Methods do I/O internally ❌
```

### After Refactoring
```
Core Module (Analyzer_one.py)
└── Pure Business Logic ✓
    └── Accepts InputContract
    └── Returns OutputContract

Orchestrator/Factory
├── Reads questionnaire_monolith.json
├── Loads documents from disk
├── Constructs InputContracts
└── Saves results to disk

Executor uses Factory
├── Factory.load_document()
├── Factory.construct_contract()
├── CoreModule.analyze(contract)
└── Factory.save_results()

Examples/ Directory
└── Demo scripts using Factory + Core
```

## Core Modules

Seven modules are being refactored:

1. **Analyzer_one.py** - Municipal development plan analysis
2. **derek_beach.py** - Causal deconstruction and audit framework (CDAF)
3. **financiero_viabilidad_tablas.py** - Financial viability and table extraction
4. **teoria_cambio.py** - Theory of change analysis
5. **contradiction_deteccion.py** - Policy contradiction detection
6. **embedding_policy.py** - Embedding-based policy analysis
7. **semantic_chunking_policy.py** - Semantic chunking and document analysis

### Rules for Core Modules

**MUST:**
- ✅ Accept typed contracts (InputContract) as parameters
- ✅ Return typed contracts (OutputContract) as results
- ✅ Be pure functions/classes (no I/O, no side effects)
- ✅ Pass all boundary enforcement tests

**MUST NOT:**
- ❌ Contain `if __name__ == "__main__"` blocks
- ❌ Perform I/O operations (open, read, write, json.load, etc.)
- ❌ Read from disk or network
- ❌ Write to disk or network
- ❌ Have side effects on import

## Contract Definitions

All contracts are defined in `core_contracts.py`:

```python
from core_contracts import (
    SemanticAnalyzerInputContract,
    SemanticAnalyzerOutputContract,
    DocumentData,
)

# Example contract
input_contract = SemanticAnalyzerInputContract(
    text="El plan de desarrollo...",
    segments=["Segment 1", "Segment 2"],
    ontology_params={"domain": "municipal"}
)
```

See [core_contracts.py](core_contracts.py) for all contract definitions.

## Factory Pattern

The `orchestrator/factory.py` module centralizes all I/O:

```python
from orchestrator.factory import CoreModuleFactory

# Factory handles all I/O
factory = CoreModuleFactory()

# Load document (I/O happens here)
document = factory.load_document(Path("plan.txt"))

# Construct contract (no I/O)
input_contract = factory.construct_semantic_analyzer_input(document)

# Use core module (pure computation, no I/O)
from Analyzer_one import SemanticAnalyzer, MunicipalOntology
ontology = MunicipalOntology()
analyzer = SemanticAnalyzer(ontology)
result = analyzer.analyze(input_contract)  # Pure!

# Save results (I/O happens here)
factory.save_results(result, Path("results.json"))
```

## Testing

### Boundary Enforcement

Test that core modules remain pure:

```bash
# Scan for violations
python tools/scan_boundaries.py .

# Run boundary tests
pytest tests/test_boundaries.py -v

# Run semantic chunking regression tests
pytest tests/test_semantic_chunking_bug.py -v
```

### CI/CD

The `.github/workflows/boundary-enforcement.yml` workflow runs on every PR:
- Scans for `__main__` blocks
- Runs boundary violation scanner
- Verifies contract definitions
- Tests core module syntax

## Development Workflow

### Adding a New Feature to a Core Module

1. **Define contracts** in `core_contracts.py`
   ```python
   class MyFeatureInputContract(TypedDict):
       text: str
       config: NotRequired[Dict[str, Any]]
   ```

2. **Implement in core module** (no I/O!)
   ```python
   def my_feature(input: MyFeatureInputContract) -> MyFeatureOutputContract:
       # Pure computation only
       return {...}
   ```

3. **Add factory method** in `orchestrator/factory.py`
   ```python
   def construct_my_feature_input(document: DocumentData) -> MyFeatureInputContract:
       return MyFeatureInputContract(
           text=document['raw_text'],
           config={}
       )
   ```

4. **Write tests** in `tests/test_my_feature.py`
   ```python
   def test_my_feature():
       input_contract = MyFeatureInputContract(text="test")
       result = my_feature(input_contract)
       assert result['some_field'] == expected
   ```

5. **Verify boundaries**
   ```bash
   python tools/scan_boundaries.py .
   pytest tests/test_boundaries.py -v
   ```

### Migrating I/O from Core Module

1. **Identify I/O operation** to migrate
   ```bash
   python tools/scan_boundaries.py . | grep module_name.py
   ```

2. **Move to factory.py**
   ```python
   # Before (in core module):
   with open('file.json') as f:
       data = json.load(f)
   
   # After (in factory.py):
   def load_my_data(path: Path) -> Dict[str, Any]:
       with open(path) as f:
           return json.load(f)
   ```

3. **Update core module** to accept data via contract
   ```python
   # Before:
   def process(file_path: str):
       with open(file_path) as f:  # I/O!
           data = json.load(f)
       return analyze(data)
   
   # After:
   def process(input: MyInputContract) -> MyOutputContract:
       return analyze(input['data'])  # No I/O!
   ```

4. **Update tests** and verify boundaries

## Documentation

- **[SURFACE_MAP.md](SURFACE_MAP.md)** - Detailed API surface documentation
- **[CHANGELOG_REFACTORING.md](CHANGELOG_REFACTORING.md)** - All refactoring changes
- **[core_contracts.py](core_contracts.py)** - Contract definitions with examples
- **[orchestrator/factory.py](orchestrator/factory.py)** - Factory implementation

## Migration Timeline

| Phase | Status | Description |
|-------|--------|-------------|
| 1-6 | ✅ Complete | Foundation work, contracts, tooling |
| 7 | ⏳ Next | I/O migration (~150 operations) |
| 8 | 📋 Planned | Executor integration |
| 9 | 📋 Planned | Examples migration |
| 10 | 📋 Planned | Strict CI enforcement |

## Contributing

When contributing to core modules:

1. **Never add I/O operations** to core modules
2. **Always use contracts** for inputs/outputs
3. **Run boundary scanner** before committing
4. **Add tests** for new functionality
5. **Update contracts** if changing APIs

## Questions?

See:
- [SURFACE_MAP.md](SURFACE_MAP.md) for API details
- [core_contracts.py](core_contracts.py) for contract definitions
- [CHANGELOG_REFACTORING.md](CHANGELOG_REFACTORING.md) for what changed

## License

[Same as main project]
