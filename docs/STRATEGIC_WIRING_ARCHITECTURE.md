# Strategic High-Level Wiring Architecture

## Overview

This document describes the high-level wiring and integration architecture across all strategic self-contained files in the CHESS (Comprehensive Holistic Evaluation Support System) framework.

**Purpose**: AUDIT, ENSURE, FORCE, GUARANTEE, and SUSTAIN high-level wiring across strategic components.

## Strategic Files and Their Roles

### 1. Core Strategic Modules

#### demo_macro_prompts.py
- **Role**: Macro-level analysis demonstrations
- **Purpose**: Demonstrates 5 strategic macro-level analysis prompts
- **Key Components**:
  - Coverage Gap Stressor
  - Contradiction Scanner
  - Bayesian Portfolio Composer
  - Roadmap Optimizer
  - Peer Normalizer
- **Wiring**: Imports from `macro_prompts.py`

#### macro_prompts.py
- **Role**: Macro-level strategic prompt implementations
- **Purpose**: Implements 5 strategic macro-level analysis prompts
- **Key Components**:
  - `CoverageGapStressor`: Evaluates dimensional/cluster coverage
  - `ContradictionScanner`: Detects micro↔meso↔macro contradictions
  - `BayesianPortfolioComposer`: Integrates posteriors into global portfolio
  - `RoadmapOptimizer`: Generates sequenced roadmaps (0-3m / 3-6m / 6-12m)
  - `PeerNormalizer`: Adjusts classification vs peers
  - `MacroPromptsOrchestrator`: Unified orchestrator for all 5 prompts
- **Wiring**: Standalone, imported by `demo_macro_prompts.py`

#### micro_prompts.py
- **Role**: Micro-level analysis prompts
- **Purpose**: Implements 3 critical micro-level analysis prompts
- **Key Components**:
  - Provenance Auditor (QMCM Integrity Check)
  - Bayesian Posterior Justification
  - Anti-Milagro Stress Test
- **Wiring**: Uses `qmcm_hooks.py` for recording

#### meso_cluster_analysis.py
- **Role**: Meso-level cluster analysis utilities
- **Purpose**: Implements 4 independent helper functions for meso-level analytics
- **Key Components**:
  - `analyze_policy_dispersion`: Dispersion analytics with penalty framework
  - `reconcile_cross_metrics`: Validates heterogeneous metric feeds
  - `compose_cluster_posterior`: Aggregates micro posteriors
  - `calibrate_against_peers`: Peer group comparison
- **Wiring**: Standalone, used by orchestrator

### 2. Validation and Quality Assurance

#### validation_engine.py
- **Role**: Centralized rule-based validation engine
- **Purpose**: Provides precondition checking and validation
- **Key Components**:
  - `ValidationEngine`: Core validation engine
  - `ValidationReport`: Structured validation reporting
- **Wiring**: Imports `validation.predicates.ValidationPredicates`

#### validation/predicates.py
- **Role**: Validation predicates for precondition checking
- **Purpose**: Reusable predicates for validating preconditions
- **Key Components**:
  - `ValidationPredicates`: Collection of validation predicates
  - `ValidationResult`: Validation result structure
- **Wiring**: Used by `validation_engine.py`

#### validation/golden_rule.py
- **Role**: Golden Rule enforcement utilities
- **Purpose**: Enforces Golden Rules across orchestrated execution
- **Key Components**:
  - `GoldenRuleValidator`: Enforces immutability and determinism
  - `GoldenRuleViolation`: Exception for rule violations
- **Wiring**: Standalone, used throughout system

#### validation/architecture_validator.py
- **Role**: Architecture validation utilities
- **Purpose**: Validates architecture blueprint references real methods
- **Key Components**:
  - `ArchitectureValidationResult`: Validation result structure
  - Method reference validation
  - Coverage reporting per dimension
- **Wiring**: Validates orchestrator architecture

#### validate_system.py
- **Role**: System validation script
- **Purpose**: Comprehensive QA for entire system
- **Key Components**:
  - Mock/placeholder detection
  - Python syntax checking
  - Import conflict detection
  - Method-level granularity validation
- **Wiring**: Validates all producer files

#### verify_complete_implementation.py
- **Role**: Implementation verification script
- **Purpose**: Verifies complete Bayesian Multi-Level Analysis System
- **Key Components**:
  - Core module verification
  - Test suite validation
  - Documentation checks
  - Module import validation
- **Wiring**: Validates bayesian_multilevel_system.py

#### coverage_gate.py
- **Role**: Coverage enforcement gate
- **Purpose**: Enforces hard-fail at <555 methods threshold
- **Key Components**:
  - Method counting across producers
  - Schema validation
  - Audit report generation
- **Wiring**: Validates all producer classes

### 3. Infrastructure and Support

#### seed_factory.py
- **Role**: Deterministic seed generation
- **Purpose**: Generates reproducible seeds for stochastic operations
- **Key Components**:
  - `SeedFactory`: Factory for deterministic seeds
  - `DeterministicContext`: Context manager for deterministic execution
  - `create_deterministic_seed()`: Convenience function
- **Wiring**: Standalone, used throughout system for reproducibility

#### qmcm_hooks.py
- **Role**: Quality Method Call Monitoring
- **Purpose**: Records method calls for registry tracking
- **Key Components**:
  - `QMCMRecorder`: Records method invocations
  - `get_global_recorder()`: Global recorder accessor
  - `qmcm_record`: Decorator for recording
- **Wiring**: Used by `micro_prompts.py` and orchestrator

#### evidence_registry.py
- **Role**: Append-only evidence registry
- **Purpose**: Maintains immutable evidence chain with cryptographic hashing
- **Key Components**:
  - `EvidenceRegistry`: Append-only ledger
  - `EvidenceRecord`: Immutable evidence entry
- **Wiring**: Standalone, used for audit trail

#### json_contract_loader.py
- **Role**: JSON contract loading and validation
- **Purpose**: Loads and validates JSON contract documents
- **Key Components**:
  - `JSONContractLoader`: Loads JSON contracts
  - `ContractDocument`: Materialized contract with checksum
  - `ContractLoadReport`: Loading result with errors
- **Wiring**: Used for loading configuration and contracts

### 4. Orchestration and Execution

#### orchestrator.py
- **Role**: Orchestrator implementation
- **Purpose**: Orchestrates all 30 base questions with real methods
- **Key Components**:
  - `MethodExecutor`: Executes catalog methods
  - Question executors (D1Q1_Executor, etc.)
  - Evidence aggregation
- **Wiring**: Uses all producer modules, validation engine, QMCM

#### document_ingestion.py
- **Role**: Document ingestion module
- **Purpose**: Loads PDF documents and extracts text
- **Key Components**:
  - `DocumentLoader`: Loads and validates PDFs
  - `TextExtractor`: Extracts text with structure
  - `PreprocessingEngine`: Normalizes and preprocesses
- **Wiring**: Uses policy_processor and financiero_viabilidad_tablas

#### scoring.py
- **Role**: Scoring modalities implementation
- **Purpose**: Applies 6 scoring modalities to question results
- **Key Components**:
  - `MicroQuestionScorer`: Applies scoring modalities
  - 6 scoring types (TYPE_A through TYPE_F)
  - Quality level determination
- **Wiring**: Used by orchestrator for scoring

#### recommendation_engine.py
- **Role**: Rule-based recommendation engine
- **Purpose**: Generates actionable recommendations at all levels
- **Key Components**:
  - `RecommendationEngine`: Core recommendation engine
  - Multi-level recommendations (MICRO, MESO, MACRO)
  - Template rendering with context
- **Wiring**: Uses scoring results and cluster analysis

### 5. Bootstrap and Scripts

#### scripts/bootstrap_validate.py
- **Role**: Bootstrap and validation utility
- **Purpose**: Provisions environment and validates stack
- **Key Components**:
  - Virtual environment creation
  - Dependency installation
  - Dry-run import validation
  - CHESS strategy execution
- **Wiring**: Orchestrates full system validation

## High-Level Wiring Principles

### 1. Determinism and Reproducibility

**Guaranteed by**: `seed_factory.py`

All stochastic operations use deterministic seeds generated from:
- Correlation ID
- File checksums
- Context parameters

**Usage pattern**:
```python
from seed_factory import DeterministicContext

with DeterministicContext(correlation_id="run-001") as seed:
    # All random operations are deterministic
    result = some_stochastic_function()
```

### 2. Immutability and Audit Trail

**Guaranteed by**: `evidence_registry.py`

All evidence is stored in an append-only ledger with cryptographic chaining:
- Each entry links to previous via SHA-256 hash
- Records are frozen (immutable)
- Chain integrity can be verified

**Usage pattern**:
```python
from evidence_registry import EvidenceRegistry

registry = EvidenceRegistry()
record = registry.append(
    method_name="analyze_policy",
    evidence=["finding1", "finding2"],
    metadata={"question_id": "Q1"}
)
```

### 3. Golden Rules Enforcement

**Guaranteed by**: `validation/golden_rule.py`

Enforces architectural constraints:
- Immutable metadata (questionnaire + step catalog)
- Atomic context (copy-on-write semantics)
- Deterministic DAG (no cycles, canonical order)
- Homogeneous treatment (identical predicates)

**Usage pattern**:
```python
from validation.golden_rule import GoldenRuleValidator

validator = GoldenRuleValidator(questionnaire_hash, step_catalog)
validator.assert_immutable_metadata(questionnaire_hash, step_catalog)
validator.assert_deterministic_dag(step_ids)
```

### 4. Validation and Preconditions

**Guaranteed by**: `validation_engine.py` + `validation/predicates.py`

All execution steps validate preconditions:
- Question specifications
- Execution results
- Producer availability
- Context parameters

**Usage pattern**:
```python
from validation_engine import ValidationEngine

engine = ValidationEngine(cuestionario_data)
result = engine.validate_scoring_preconditions(
    question_spec, execution_results, plan_text
)
if not result.is_valid:
    raise ValidationError(result.message)
```

### 5. Quality Method Call Monitoring

**Guaranteed by**: `qmcm_hooks.py`

All method calls are recorded for quality monitoring:
- Method invocations
- Input/output types
- Execution status
- Timing

**Usage pattern**:
```python
from qmcm_hooks import qmcm_record

@qmcm_record
def my_analysis_method(arg1: str, arg2: int) -> dict:
    return {"result": "data"}
```

## Integration Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATOR                                 │
│  (orchestrator.py)                                                   │
│  - Coordinates all 30 base questions                                 │
│  - Uses MethodExecutor for catalog methods                           │
└────┬───────────────────────────┬─────────────────────┬──────────────┘
     │                           │                     │
     ▼                           ▼                     ▼
┌─────────────┐          ┌─────────────┐      ┌─────────────┐
│  VALIDATION │          │   SCORING   │      │ RECOMMENDA- │
│   ENGINE    │          │             │      │    TION     │
│             │          │             │      │   ENGINE    │
└─────┬───────┘          └─────┬───────┘      └─────┬───────┘
      │                        │                    │
      │                        │                    │
      ▼                        ▼                    ▼
┌─────────────────────────────────────────────────────────┐
│              INFRASTRUCTURE LAYER                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ SEED FACTORY │  │ QMCM HOOKS   │  │  EVIDENCE    │  │
│  │              │  │              │  │  REGISTRY    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
      │                        │                    │
      ▼                        ▼                    ▼
┌─────────────────────────────────────────────────────────┐
│            STRATEGIC ANALYSIS LAYER                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   MICRO      │  │     MESO     │  │    MACRO     │  │
│  │  PROMPTS     │  │   CLUSTER    │  │   PROMPTS    │  │
│  │              │  │   ANALYSIS   │  │              │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Provenance Tracking

All strategic files are tracked in `provenance.csv` with:
- File path
- Commit hash
- Author
- Timestamp

This ensures full traceability of all strategic components.

## Testing Strategy

### Unit Tests
- `tests/test_strategic_wiring.py`: Comprehensive wiring validation
  - File existence and syntax
  - Import validation
  - Interface validation
  - Determinism tests
  - Immutability tests
  - Golden Rules tests

### Integration Tests
- `validate_strategic_wiring.py`: Full system wiring validation
  - Cross-file dependencies
  - Module interfaces
  - Determinism guarantees
  - Immutability guarantees
  - Golden Rules compliance

### Quality Gates
- `coverage_gate.py`: Enforces method coverage threshold (555 methods)
- `validate_system.py`: Comprehensive QA for entire system

## Continuous Integration

The strategic wiring validation is designed to be integrated into CI/CD:

```yaml
# Example GitHub Actions workflow
- name: Validate Strategic Wiring
  run: |
    python3 validate_strategic_wiring.py
    python3 -m unittest tests.test_strategic_wiring
    python3 coverage_gate.py
```

## Maintenance Guidelines

### Adding New Strategic Files

1. Add file to repository
2. Update `provenance.csv` with file information
3. Add tests to `tests/test_strategic_wiring.py`
4. Update wiring specs in `validate_strategic_wiring.py`
5. Document in this file

### Modifying Existing Wiring

1. Ensure backward compatibility
2. Update tests to reflect changes
3. Run full validation suite
4. Update documentation

### Removing Strategic Files

1. Check all dependencies first
2. Update `provenance.csv`
3. Remove related tests
4. Update validation scripts
5. Update documentation

## Compliance Checklist

- [x] All strategic files exist and are syntactically correct
- [x] Provenance tracking includes all strategic files
- [x] Cross-file wiring is properly configured
- [x] Module interfaces are properly exposed
- [x] Determinism is guaranteed via SeedFactory
- [x] Immutability is guaranteed via EvidenceRegistry
- [x] Golden Rules are enforced via GoldenRuleValidator
- [x] Validation engine provides precondition checking
- [x] QMCM hooks record all method calls
- [x] Comprehensive test coverage exists
- [x] Integration validation passes
- [x] Documentation is complete and up-to-date

## Conclusion

The strategic high-level wiring architecture ensures:

1. **AUDIT**: Full traceability via provenance tracking and evidence registry
2. **ENSURE**: Comprehensive validation at all levels
3. **FORCE**: Hard-fail on quality gates (coverage, syntax, imports)
4. **GUARANTEE**: Determinism via seed factory, immutability via evidence registry
5. **SUSTAIN**: Golden Rules enforcement and continuous validation

All strategic files are properly wired, validated, and sustained for production use.
