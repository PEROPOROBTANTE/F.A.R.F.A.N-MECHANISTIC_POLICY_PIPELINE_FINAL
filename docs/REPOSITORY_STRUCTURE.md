# Repository Structure

This document describes the new hierarchical organization of the SAAAAAA repository, following Python best practices for data pipelines.

## Overview

The repository has been reorganized from a flat structure into a proper Python package hierarchy with clear separation of concerns.

## Directory Structure

```
saaaaaa/
├── src/saaaaaa/              # Main Python package
│   ├── core/                 # Core orchestration and execution
│   ├── processing/           # Data processing modules
│   ├── analysis/             # Analysis and ML modules
│   ├── api/                  # API server and web interface
│   ├── utils/                # Utility modules
│   └── concurrency/          # Concurrency utilities
├── tests/                    # Test suite
├── docs/                     # Documentation
├── examples/                 # Example scripts and demos
├── scripts/                  # Utility and validation scripts
├── config/                   # Configuration files
├── data/                     # Data files
├── tools/                    # Development and build tools
└── minipdm/                  # Mini PDM sub-project

```

## Package Descriptions

### `src/saaaaaa/` - Main Package

The main Python package containing all production code.

#### `src/saaaaaa/core/`
Core orchestration and execution components:
- `orchestrator/` - Modular orchestrator package with core, executors, evidence registry, and other components
- `ports.py` - Port definitions for the orchestrator
- `contracts.py` - Core contracts and interfaces

#### `src/saaaaaa/processing/`
Data processing pipeline components:
- `document_ingestion.py` - Document processing
- `embedding_policy.py` - Embedding generation
- `semantic_chunking_policy.py` - Semantic chunking
- `aggregation.py` - Data aggregation
- `policy_processor.py` - Policy processing

#### `src/saaaaaa/analysis/`
Analysis and machine learning modules:
- `bayesian_multilevel_system.py` - Bayesian analysis
- `Analyzer_one.py` - Primary analyzer
- `contradiction_deteccion.py` - Contradiction detection
- `teoria_cambio.py` - Theory of change
- `derek_beach.py` - Beach testing
- `financiero_viabilidad_tablas.py` - Financial viability
- `meso_cluster_analysis.py` - Cluster analysis
- `macro_prompts.py` - Macro-level prompts
- `micro_prompts.py` - Micro-level prompts
- `recommendation_engine.py` - Recommendation system
- `enhance_recommendation_rules.py` - Rule enhancement
- `scoring/` - Scoring sub-package

#### `src/saaaaaa/api/`
API and web interface:
- `api_server.py` - Flask API server
- `static/` - Static web assets

#### `src/saaaaaa/utils/`
Utility modules:
- `adapters.py` - Adapter patterns
- `contracts.py` - Contract definitions
- `core_contracts.py` - Core contracts
- `signature_validator.py` - Signature validation
- `schema_monitor.py` - Schema monitoring
- `validation_engine.py` - Validation engine
- `runtime_error_fixes.py` - Runtime error handling
- `evidence_registry.py` - Evidence registry
- `metadata_loader.py` - Metadata loading
- `json_contract_loader.py` - JSON contract loading
- `seed_factory.py` - Seed generation
- `qmcm_hooks.py` - QMCM hooks
- `coverage_gate.py` - Coverage gate
- `validation/` - Validation sub-package
- `determinism/` - Determinism utilities

#### `src/saaaaaa/concurrency/`
Concurrency management utilities

#### `src/saaaaaa/controls/`
Control and monitoring components

### `tests/` - Test Suite

Comprehensive test suite covering all modules. Tests are organized to mirror the package structure.

### `docs/` - Documentation

All documentation files including:
- Architecture documentation
- Implementation summaries
- API documentation
- User guides
- Development notes

### `examples/` - Example Scripts

Demonstration scripts and integration examples:
- `demo_aguja_i.py`
- `demo_bayesian_multilevel.py`
- `demo_macro_prompts.py`
- `demo_tres_agujas.py`
- `integration_guide_bayesian.py`

### `scripts/` - Utility Scripts

Command-line tools and validation scripts:
- `build_monolith.py` - Build script
- `validate_*.py` - Validation scripts
- `recommendation_cli.py` - CLI interface

### `config/` - Configuration

Configuration files and schemas:
- `execution_mapping.yaml` - Execution configuration
- `inventory.json` - Component inventory
- `method_counts.json` - Method statistics
- `schemas/` - JSON schemas
- `rules/` - Rule definitions

### `data/` - Data Files

Data files and datasets:
- `questionnaire_monolith.json` - Questionnaire data
- `interaction_matrix.csv` - Interaction matrix
- `provenance.csv` - Data provenance

### `tools/` - Development Tools

Build, testing, and validation tools

### `minipdm/` - Mini PDM

Separate mini-PDM sub-project

## Benefits of New Structure

1. **Clear Separation of Concerns**: Each directory has a specific purpose
2. **Python Package Standards**: Follows PEP 420 and standard package layouts
3. **Easier Navigation**: Logical grouping of related modules
4. **Better IDE Support**: Modern IDEs can better understand the structure
5. **Scalability**: Easy to add new modules in appropriate locations
6. **Testing**: Clear mapping between code and tests
7. **Documentation**: Centralized documentation location
8. **Deployment**: Standard src-layout enables better packaging

## Migration Notes

- All imports now use the `saaaaaa` package prefix (e.g., `from saaaaaa.core import ...`)
- Configuration paths updated in `pyproject.toml`
- Test discovery and coverage configured for new structure
- Legacy flat imports are not supported

## Development Workflow

1. **Adding new code**: Place in appropriate `src/saaaaaa/` subdirectory
2. **Adding tests**: Place in `tests/` with matching structure
3. **Adding docs**: Place in `docs/`
4. **Adding examples**: Place in `examples/`
5. **Configuration**: Update files in `config/`

## Installation

For development:
```bash
pip install -e .
```

This installs the package in editable mode from the `src/` directory.
