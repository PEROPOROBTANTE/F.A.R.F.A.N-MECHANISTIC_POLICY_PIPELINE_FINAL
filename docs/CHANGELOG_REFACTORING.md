# Changelog - Core Module Refactoring

All notable changes to the core module architecture are documented in this file.

## [Unreleased] - Foundation Work Complete

### Added

#### Infrastructure & Tooling
- **tools/scan_boundaries.py**: AST-based scanner for detecting I/O operations and `__main__` blocks in core modules
  - Detects file operations (open, read, write)
  - Detects JSON/pickle/YAML I/O
  - Detects `__main__` blocks
  - Provides detailed violation reports with line numbers
  - Exit codes for CI integration

- **.github/workflows/boundary-enforcement.yml**: CI workflow for enforcing architectural boundaries
  - Scans for `__main__` blocks in core modules
  - Runs boundary violation scanner
  - Verifies contract definitions
  - Tests core module syntax
  - Runs boundary enforcement test suite

- **tests/test_boundaries.py**: Comprehensive boundary enforcement test suite
  - Tests for absence of `__main__` blocks
  - Tests for absence of I/O operations (informational for now)
  - Tests safe module imports without side effects
  - Validates boundary scanner tool

- **tests/test_semantic_chunking_bug.py**: Regression tests for semantic_chunking_policy.py
  - Ensures syntax error fix stays fixed
  - Validates no duplicate return statements
  - Checks method structure integrity
  - Prevents regression of duplicate lines bug

#### Contracts & Documentation
- **core_contracts.py**: TypedDict contracts for all 7 core modules
  - SemanticAnalyzerInputContract / OutputContract
  - CDAFFrameworkInputContract / OutputContract
  - PDETAnalyzerInputContract / OutputContract
  - TeoriaCambioInputContract / OutputContract
  - ContradictionDetectorInputContract / OutputContract
  - EmbeddingPolicyInputContract / OutputContract
  - SemanticChunkingInputContract / OutputContract
  - PolicyProcessorInputContract / OutputContract
  - Includes docstrings and usage examples
  - Python 3.9+ support with typing_extensions fallback

- **orchestrator/factory.py**: Factory module for dependency injection (skeleton)
  - I/O operations centralized
  - Contract constructor functions
  - Document loading utilities
  - Results persistence
  - Ready for I/O migration from core modules

- **SURFACE_MAP.md**: Complete API surface documentation
  - Maps exposed classes per module
  - Documents used methods from executors
  - Lists I/O operations to migrate
  - Provides migration strategy
  - Defines deprecation timeline

### Changed

#### Core Modules - Purification
All core modules have been purified of `__main__` blocks to enable safe import without side effects:

- **Analyzer_one.py**: Removed 2 `__main__` blocks (lines 1665, 1887)
- **derek_beach.py**: Removed 1 `__main__` block (line 5818)
- **financiero_viabilidad_tablas.py**: Removed 1 `__main__` block (line 2310)
- **teoria_cambio.py**: Removed 1 `__main__` block (line 1094)
- **contradiction_deteccion.py**: Removed 1 `__main__` block (line 1473)
- **embedding_policy.py**: Removed 1 `__main__` block (line 1891)
- **semantic_chunking_policy.py**: Removed 1 `__main__` block (line 821)

All modules verified with `py_compile` - no syntax errors.

### Fixed

#### Critical Bugs
- **semantic_chunking_policy.py** (lines 555-562): Fixed duplicate code block
  - Removed duplicate list comprehension closing
  - Removed duplicate `return excerpts` statement
  - Added missing `"key_excerpts": key_excerpts` field to return dictionary
  - Added regression tests to prevent reintroduction

### Deprecated

The following patterns are deprecated and will be removed in v2.0:

#### Example/Demo Code (to be moved to examples/)
- `Analyzer_one.example_usage()` → Move to `examples/analyzer_one_demo.py`
- `Analyzer_one.main()` → Move to `examples/analyzer_one_cli.py`
- `derek_beach.main()` → Move to `examples/cdaf_demo.py`
- `financiero_viabilidad_tablas.main_example()` → Move to `examples/pdet_demo.py`
- `teoria_cambio.main()` → Move to `examples/teoria_cambio_demo.py`
- `contradiction_deteccion` example code → Move to `examples/contradiction_demo.py`
- `embedding_policy.example_pdm_analysis()` → Move to `examples/embedding_demo.py`
- `semantic_chunking_policy.main()` → Move to `examples/semantic_chunking_demo.py`

#### Utility Classes (to be moved to orchestrator/)
- `Analyzer_one.ResultsExporter` → Move to `orchestrator/exporters.py`
- `Analyzer_one.ConfigurationManager` → Move to `orchestrator/config.py`
- `Analyzer_one.BatchProcessor` → Move to `orchestrator/batch.py`

### Migration Guide

#### For Module Users
**Old pattern (deprecated):**
```python
from Analyzer_one import SemanticAnalyzer, MunicipalOntology

ontology = MunicipalOntology()
analyzer = SemanticAnalyzer(ontology)
results = analyzer.analyze_document("plan.txt")  # Has I/O!
```

**New pattern (after I/O migration):**
```python
from orchestrator.factory import CoreModuleFactory
from Analyzer_one import SemanticAnalyzer, MunicipalOntology

# Factory handles I/O
factory = CoreModuleFactory()
document = factory.load_document("plan.txt")

# Construct contract
input_contract = factory.construct_semantic_analyzer_input(document)

# Pure computation, no I/O
ontology = MunicipalOntology()
analyzer = SemanticAnalyzer(ontology)
results = analyzer.analyze(input_contract)  # No I/O!
```

#### For Core Module Developers
**Rules:**
1. **No I/O operations** in core modules (no open, read, write, json.load, etc.)
2. **No `__main__` blocks** in core modules
3. **Accept contracts** as input (TypedDict from core_contracts.py)
4. **Return contracts** as output
5. **No side effects** on import

**Testing:**
```bash
# Check for violations
python tools/scan_boundaries.py .

# Run boundary tests
pytest tests/test_boundaries.py -v
```

### Remaining Work

#### Phase 7: I/O Migration (Large effort)
Migrate ~150 I/O operations from core modules to orchestrator/factory.py:
- Analyzer_one.py: 72 I/O operations
- derek_beach.py: 40 I/O operations
- financiero_viabilidad_tablas.py: Multiple operations
- teoria_cambio.py: Some operations

#### Phase 8: Executor Integration (Complex refactoring)
- Update executors_COMPLETE_FIXED.py (8,781 lines) to use contracts
- Test all execution paths
- Ensure no behavior changes

#### Phase 9: Examples Migration (Straightforward)
- Extract example code to examples/ directory
- Create demo scripts for each module

#### Phase 10: CI/CD Integration (Straightforward)
- Enforce boundary scanner in CI (currently informational)
- Add mypy --strict checks
- Configure import-linter

## Deprecation Timeline

- **v1.0** (Current): Introduce contracts alongside existing APIs
- **v1.1** (Next): Mark old APIs as deprecated, emit warnings
- **v2.0** (Future): Remove old APIs, contracts only

## Statistics

- **Files changed**: 7 core modules + 8 new files
- **Lines removed**: 116 (\_\_main\_\_ blocks)
- **Lines added**: ~2,000 (contracts, tests, docs, tooling)
- **I/O operations remaining**: ~150 (to be migrated)
- **Test coverage**: Boundary tests added
- **CI/CD**: Boundary enforcement workflow added

## References

- [SURFACE_MAP.md](SURFACE_MAP.md) - Detailed API surface documentation
- [core_contracts.py](core_contracts.py) - Contract definitions
- [tools/scan_boundaries.py](tools/scan_boundaries.py) - Boundary scanner
- [orchestrator/factory.py](orchestrator/factory.py) - Factory pattern implementation
