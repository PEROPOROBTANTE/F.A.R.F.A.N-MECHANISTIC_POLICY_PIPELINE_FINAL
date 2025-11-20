# ORCHESTRATION ARCHITECTURE - Complete Map

## Orchestration Layers (5 niveles)

### Layer 1: PhaseOrchestrator (NEW - Constitutional Entry Point)
**Location**: `src/saaaaaa/core/phases/phase_orchestrator.py`
**Responsibility**: Enforce constitutional phase sequence (0 → 1 → Adapter → Core)

**Phases Coordinated**:
- **Phase 0**: Input Validation (pdf → CanonicalInput)
- **Phase 1**: SPC Ingestion (15 subfases → CanonPolicyPackage)
- **Adapter**: CPP → PreprocessedDocument
- **Delegates to Core Orchestrator** for phases 2-10

**Output**: Hands off `PreprocessedDocument` to Layer 2 (core.Orchestrator)

---

### Layer 2: core.Orchestrator (EXISTING - Pipeline Executor)
**Location**: `src/saaaaaa/core/orchestrator/core.py`
**Responsibility**: Execute 11-phase analysis pipeline

**11 FASES** (defined in `core.Orchestrator.FASES`):
```python
FASE 0:  Validación de Configuración  (_load_configuration)
FASE 1:  Ingestión de Documento       (_ingest_document)          # Uses PreprocessedDocument
FASE 2:  Micro Preguntas              (_execute_micro_questions_async)  # 300 questions
FASE 3:  Scoring Micro                (_score_micro_results_async)
FASE 4:  Agregación Dimensiones       (_aggregate_dimensions_async)    # 60 items
FASE 5:  Agregación Áreas             (_aggregate_policy_areas_async)  # 10 items
FASE 6:  Agregación Clústeres         (_aggregate_clusters)            # 4 clusters
FASE 7:  Evaluación Macro             (_evaluate_macro)
FASE 8:  Recomendaciones              (_generate_recommendations)
FASE 9:  Ensamblado de Reporte        (_assemble_report)
FASE 10: Formateo y Exportación       (_format_and_export)             # Dashboard feed
```

> **Nota:** Los contratos y algoritmos de las FASES 4‑7 se documentan exclusivamente en los dossiers bilingües `docs/phases/phase_4/P04-*.md`, `phase_5/P05-*.md`, `phase_6/P06-*.md` y `phase_7/P07-*.md`. Cualquier ajuste debe reflejarse allí antes de tocar código.

**Context Flow**:
- Phase 0 → `config`
- Phase 1 → `document` (PreprocessedDocument)
- Phase 2 → `micro_results` (MicroQuestionRun[])
- Phase 3 → `scored_results` (ScoredMicroQuestion[])
- Phase 4 → `dimension_scores`
- Phase 5 → `policy_area_scores`
- Phase 6 → `cluster_scores`
- Phase 7 → `macro_result`
- Phase 8 → `recommendations`
- Phase 9 → `report`
- Phase 10 → `export_payload` (to dashboard)

---

### Layer 3: Executors (Dimension × Question Executors)
**Location**: `src/saaaaaa/core/orchestrator/executors.py`
**Responsibility**: Execute specific (Dimension, Question) combinations

**30 Executors** (6 Dimensions × 5 Questions):
```python
{
    "D1-Q1": D1Q1_Executor,  # Dimension 1, Question 1
    "D1-Q2": D1Q2_Executor,
    ...
    "D6-Q5": D6Q5_Executor,  # Dimension 6, Question 5
}
```

**Each Executor**:
- Orchestrates methods from the catalog
- Applies signals and calibration parameters
- Returns Evidence with enriched results

---

### Layer 4: Methods (Canonical Method Catalog)
**Location**: Multiple analysis modules
**Responsibility**: Atomic analysis operations

**Examples**:
- `saaaaaa.analysis.micro_prompts` - CDAF extraction
- `saaaaaa.analysis.bayesian_multilevel_system` - Probabilistic models
- `saaaaaa.analysis.contradiction_deteccion` - Contradiction detection
- `saaaaaa.analysis.derek_beach` - Process tracing
- `saaaaaa.analysis.teoria_cambio` - Theory of change
- `saaaaaa.analysis.spc_causal_bridge` - Causal bridging

**Routing**:
- `MethodExecutor` uses `ArgRouter` to dispatch to methods
- `class_registry` provides method lookup
- `ExecutorConfig` provides method-specific configuration

---

### Layer 5: Calibration Orchestrator
**Location**: `src/saaaaaa/core/orchestrator/calibration_context.py`
**Responsibility**: Manage calibration parameters across all layers

**Coordinates**:
- Parameter injection into executors
- Signal calibration gates
- Method-specific hyperparameters
- Quality thresholds

---

## CRITICAL WIRING POINTS

### Wiring Point 1: PhaseOrchestrator → core.Orchestrator
**Interface**: `PreprocessedDocument`

**Contract**:
```python
# PhaseOrchestrator produces:
preprocessed_document = {
    "document_id": str,
    "raw_text": str,
    "sentences": list[str],
    "chunk_graph": dict,  # From CanonPolicyPackage
    "processing_mode": "chunked",
    "metadata": dict
}

# core.Orchestrator expects (in _ingest_document):
document = PreprocessedDocument.ensure(preprocessed_document)
```

**Failure Modes**:
1. ❌ `processing_mode != "chunked"` → Orchestrator rejects
2. ❌ `chunk_graph` missing → Adapter validation fails
3. ❌ `raw_text` empty → PreprocessedDocument.__post_init__ raises ValueError
4. ❌ `document_id` mismatch → Traceability broken

**Solution**: PhaseOrchestrator MUST validate Adapter output before handing to core.Orchestrator

---

### Wiring Point 2: core.Orchestrator → Executors
**Interface**: Evidence selection via `chunk_graph`

**Contract**:
- Executors receive `PreprocessedDocument.chunks`
- Executors filter chunks by `policy_area_id` and `dimension_id`
- Evidence MUST reference valid `chunk_ids`

**Failure Modes**:
1. ❌ Chunks missing `policy_area_id` → Executor cannot route
2. ❌ Chunks missing `dimension_id` → Executor cannot filter
3. ❌ Chunk references invalid → Evidence traceability breaks

**Solution**: Phase 1 invariants MUST enforce PA×DIM on all chunks

---

### Wiring Point 3: Executors → Methods
**Interface**: `ArgRouter` + `MethodExecutor`

**Contract**:
- Executors specify method name + kwargs
- `ArgRouter` validates method signature
- `class_registry` provides method instance

**Failure Modes**:
1. ❌ Method not in registry → `ClassRegistryError`
2. ❌ Invalid kwargs → `ArgumentValidationError`
3. ❌ Method execution fails → Executor catches, returns error Evidence

**Solution**: ExecutorConfig validation + degraded mode handling

---

### Wiring Point 4: core.Orchestrator → Calibration
**Interface**: `CalibrationOrchestrator`

**Contract**:
- Orchestrator queries calibration for parameters
- Executors receive calibrated hyperparameters
- Methods use calibrated thresholds

**Failure Modes**:
1. ❌ Calibration orchestrator None → Use defaults
2. ❌ Parameter missing → Fallback to hardcoded values
3. ❌ Parameter out of range → Validation error

**Solution**: Graceful degradation with warnings

---

## INTEGRATION STRATEGY

### How PhaseOrchestrator Integrates:

```python
# In run_policy_pipeline_verified.py (EXISTING):

# BEFORE (current):
pipeline = CPPIngestionPipeline()
cpp = await pipeline.process(pdf_path)
adapter = SPCAdapter()
preprocessed = adapter.to_preprocessed_document(cpp)
orchestrator = Orchestrator(...)
results = await orchestrator.process_development_plan_async(pdf_path, preprocessed)

# AFTER (with PhaseOrchestrator):
phase_orchestrator = PhaseOrchestrator()
pipeline_result = await phase_orchestrator.run_pipeline(
    pdf_path=pdf_path,
    run_id=run_id,
    questionnaire_path=questionnaire_path,
    artifacts_dir=artifacts_dir
)

if pipeline_result.success:
    # PhaseOrchestrator internally:
    # 1. Ran Phase 0 (validation)
    # 2. Ran Phase 1 (SPC ingestion)
    # 3. Ran Adapter
    # 4. Created core.Orchestrator
    # 5. Ran core.Orchestrator.process_development_plan_async()
    # 6. Returned complete results

    # Access results:
    preprocessed = pipeline_result.preprocessed_document
    phase2_result = pipeline_result.phase2_result  # From core.Orchestrator
```

---

## FAILURE MODE ANALYSIS

### Scenario 1: Phase 0 Fails
**Cause**: PDF not found
**Effect**:
- PhaseOrchestrator.run_pipeline() catches error
- Sets `PipelineResult.success = False`
- Records error in manifest
- Returns early (no Phase 1 executed)

**Wiring Impact**: None (pipeline never starts)

---

### Scenario 2: Phase 1 Fails
**Cause**: SPC ingestion produces < 60 chunks
**Effect**:
- Phase1Contract.check_invariants() fails
- PhaseOrchestrator catches error
- Sets `PipelineResult.success = False`
- Returns early (Adapter not executed)

**Wiring Impact**: core.Orchestrator never receives input

---

### Scenario 3: Adapter Fails
**Cause**: CanonPolicyPackage has empty chunk_graph
**Effect**:
- Adapter validation fails
- `PreprocessedDocument.ensure()` raises ValueError
- PhaseOrchestrator catches error
- Returns early

**Wiring Impact**: core.Orchestrator never receives input

---

### Scenario 4: core.Orchestrator Phase 2 Fails
**Cause**: Question execution timeout
**Effect**:
- core.Orchestrator._execute_micro_questions_async() catches PhaseTimeoutError
- Sets phase_result.success = False
- Triggers abort signal
- Stops at Phase 2

**Wiring Impact**: Phases 3-10 not executed, dashboard not updated

---

### Scenario 5: Executor Degraded Mode
**Cause**: Method class not in registry
**Effect**:
- MethodExecutor enters degraded_mode
- Executor returns placeholder Evidence
- Phase 2 completes with warnings
- Quality metrics show degradation

**Wiring Impact**: Partial results, flagged in manifest

---

## VALIDATION CHECKLIST

Before merging PhaseOrchestrator:

- [ ] Test Phase 0 failure → verify pipeline stops cleanly
- [ ] Test Phase 1 failure → verify no Adapter call
- [ ] Test Adapter failure → verify no core.Orchestrator call
- [ ] Test core.Orchestrator receives valid PreprocessedDocument
- [ ] Test Executors receive chunks with PA×DIM
- [ ] Test Methods receive valid Evidence
- [ ] Test Calibration parameters flow to Executors
- [ ] Test manifest records all phase boundaries
- [ ] Test verification_manifest.json merges with phase_manifest.json
- [ ] Test runner can still run without PhaseOrchestrator (backward compat)

---

## RECOMMENDATION

**DO NOT** replace core.Orchestrator.

**DO** wrap it with PhaseOrchestrator as the new entry point:

```
run_policy_pipeline_verified.py
    ↓
PhaseOrchestrator.run_pipeline()
    ↓ Phase 0, 1, Adapter
    ↓ (produces PreprocessedDocument)
    ↓
core.Orchestrator.process_development_plan_async()
    ↓ Phases 0-10 (uses PreprocessedDocument from PhaseOrchestrator)
    ↓ Executors → Methods → Calibration
    ↓
dashboard update (Phase 10 export)
```

This preserves ALL existing functionality while adding constitutional constraints.
