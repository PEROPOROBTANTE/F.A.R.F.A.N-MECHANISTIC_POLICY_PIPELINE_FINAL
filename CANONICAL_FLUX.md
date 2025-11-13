# Canonical Flux: Single Deterministic Pipeline Path

## Overview

This document defines the **single, immutable, deterministic path** from policy document ingestion to final reporting. No parallel fluxes exist except for async operations properly contained within phases.

## Core Principle

```
INPUT (Plan PDF) → spc_ingestion → orchestrator phases → reporting → OUTPUT (Analysis)
```

This is the **only** path through the system. All processing follows this linear flux.

## Phase Architecture

### Phase-One: SPC Ingestion (Smart Policy Chunks)
**Location**: `src/saaaaaa/processing/spc_ingestion/`  
**Entry Point**: `smart_policy_chunks_canonic_phase_one.py` via `CPPIngestionPipeline`  
**Purpose**: Transform raw policy documents into validated smart chunks with comprehensive metadata

**Subphases** (internal to phase-one, not separate paths):
1. Document preprocessing and structural analysis
2. Topic modeling and knowledge graph construction  
3. Causal chain extraction
4. Temporal, argumentative, and discourse analysis
5. Smart chunk creation with inter-chunk relationships
6. Quality validation (via `quality_gates.py`)
7. Strategic ranking and deduplication

**Output Contract**:
```python
{
    'chunks': List[SmartPolicyChunk],  # Validated chunks with embeddings
    'metadata': {
        'document_id': str,
        'title': str,
        'version': str
    },
    'document_path': str
}
```

### Phase-Two through Phase-N: Orchestrator Phases
**Location**: `src/saaaaaa/core/orchestrator/`  
**Coordinator**: `Orchestrator` class in `core.py`  
**Purpose**: Process smart chunks through 11 canonical phases

**Input**: Phase-one output (via cpp_adapter conversion to `PreprocessedDocument`)  
**Phases**:
1. Phase 1: (Already done - ingestion)
2. Phase 2-11: Orchestrator-managed analysis phases

**Wiring**: Orchestrator receives phase-one output via:
```python
PreprocessedDocument.ensure(document, use_spc_ingestion=True)
```

### Final Phase: Reporting
**Location**: TBD (to be documented)  
**Purpose**: Generate final analysis outputs and reports

**Input**: Orchestrator phase results  
**Output**: Final policy analysis deliverables

## Execution Entry Point

**Canonical Runner**: `scripts/run_policy_pipeline_verified.py`

This script:
1. Validates input PDF existence and integrity
2. Runs SPC ingestion (phase-one)
3. Converts to PreprocessedDocument via cpp_adapter
4. Passes to orchestrator for phases 2-11
5. Generates final outputs
6. Creates verification manifest with cryptographic hashes

## Quality Gates

Quality validation occurs at:
- **Phase-One Exit**: `spc_ingestion/quality_gates.py` validates chunk quality
- **Phase Transitions**: Orchestrator validates data contracts between phases
- **Final Output**: Verification manifest confirms end-to-end integrity

## No Parallel Paths Rule

**Forbidden**:
- Multiple ingestion pipelines processing the same document
- Alternative phase sequences
- Bypass routes around orchestrator
- Divergent processing branches

**Allowed**:
- Async operations **within** a single phase (e.g., parallel chunk processing)
- Internal subphases that are deterministically sequenced
- Conditional logic that still follows the main flux

## Configuration

All pipeline behavior is controlled via:
- **Feature Flags**: `WiringFeatureFlags` with `use_spc_ingestion=True`
- **Calibration**: `calibration_registry.py` for canonical parameters
- **Method Registry**: `complete_canonical_catalog.json` for method definitions

## Verification

Pipeline integrity is verified by:
1. Input PDF SHA256 hash
2. Output artifact SHA256 hashes
3. Phase completion counts
4. Verification manifest with `"success": true` only if all invariants hold

**Verification Script**: `scripts/run_policy_pipeline_verified.py`

## Migration Notes

### Old System → New System
- `cpp_ingestion` → `spc_ingestion` (canonical phase-one)
- `use_cpp_ingestion` flag → `use_spc_ingestion` (legacy alias maintained)
- Multiple pipeline paths → Single canonical flux

### Backwards Compatibility
- `CPPIngestionPipeline` wrapper maintained in `spc_ingestion/__init__.py`
- Legacy `use_cpp_ingestion` flag supported (aliases to `use_spc_ingestion`)
- Old contract types preserved for existing code

## Future Extensions

Any new phases must:
1. Integrate into the canonical flux at the appropriate position
2. Define clear input/output contracts
3. Register methods in `complete_canonical_catalog.json`
4. Add calibration parameters to `calibration_registry.py`
5. Not create parallel processing paths

---

**Last Updated**: 2025-11-08  
**Maintained By**: System Architecture Team
