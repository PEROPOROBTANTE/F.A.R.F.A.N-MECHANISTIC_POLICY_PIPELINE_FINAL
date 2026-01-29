# F.A.R.F.A.N Canonical Architecture

## Overview

The F.A.R.F.A.N (Framework for Advanced Retrieval and Forensic Analysis of Administrative Narratives) pipeline follows a strict architectural pattern to ensure determinism, maintainability, and scalability.

## Directory Structure

```
src/farfan_pipeline/
├── orchestration/          # Pipeline orchestration
│   ├── core_orchestrator.py
│   ├── gates/             # Gate validation
│   └── verification_manifest.py
├── phases/                # Pipeline phases P00-P09
│   ├── Phase_00/         # Initialization & Validation
│   ├── Phase_01/         # Document Processing
│   ├── Phase_02/         # Contract Generation
│   ├── Phase_03/         # Scoring
│   ├── Phase_04/         # Dimension Aggregation
│   ├── Phase_05/         # Policy Area Scoring
│   ├── Phase_06/         # Clustering
│   ├── Phase_07/         # Exit Validation
│   ├── Phase_08/         # Versioning
│   └── Phase_09/         # Completion
├── infrastructure/        # Core infrastructure
│   ├── contractual/      # Contract enforcement (Dura Lex)
│   ├── irrigation_using_signals/  # SISAS system
│   └── verification/     # Verification utilities
└── dashboard_atroz_/     # Dashboard integration
```

## Forbidden Namespaces

The following namespaces have been deprecated and must NOT be used:

1. `orchestration.orchestrator` - Use `farfan_pipeline.orchestration.core_orchestrator`
2. `cross_cutting_infrastructure` - Use `farfan_pipeline.infrastructure.*`
3. `_deprecated/signal_consumption` - Use `SISAS.audit.*` modules

## Compatibility Shims

Compatibility shim files (*_compat.py, *_legacy.py, *_shim.py) are forbidden in production code.
They may only exist in test directories for backward compatibility testing.

## Phase Invariants

Each phase has specific invariants that must be maintained:

- **P01**: chunk_count=60, policy_areas=10, dimensions=6
- **P02**: contract_count=300, executors=30
- **P03**: score_range=(0,3), scores_count=300
- **P04**: dimension_scores=60, method=Choquet
- **P05**: policy_area_scores=10
- **P06**: cluster_count=4
- **P07**: components=CCCA,SGD,SAS
- **P08**: version=3.0.0
- **P09**: status=complete

## Gate Validation

Phase 0 defines seven gates (GATE_1 through GATE_7) that must be passed before pipeline execution can proceed.

## Determinism

The pipeline enforces determinism through:
- PYTHONHASHSEED=42
- torch.manual_seed(42)
- numpy.random.seed(42)
- random.seed(42)

## Contract Validation (CQVR)

All contracts must pass CQVR (Contract Quality Validation and Remediation) with a minimum threshold score.
