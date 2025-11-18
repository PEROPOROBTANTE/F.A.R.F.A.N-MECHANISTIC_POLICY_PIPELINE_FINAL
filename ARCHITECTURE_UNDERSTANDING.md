# F.A.R.F.A.N Pipeline Architecture - Correct Understanding

**Date**: 2025-11-17
**Purpose**: Document correct architectural understanding after review
**Status**: Pre-delete branch summary

---

## Critical Corrections to My Previous Misunderstanding

### What I Got WRONG Before:

1. **❌ WRONG**: I said there are 300 executors
   - **✅ CORRECT**: There are **30 EXECUTORS** that orchestrate methods to answer 300 questions

2. **❌ WRONG**: I mapped ChunkType (DIAGNOSTICO, ESTRATEGIA, etc.) to MICRO/MESO/MACRO execution levels
   - **✅ CORRECT**: ChunkType indicates **CONTENT TYPE** only (what kind of content the chunk contains), NOT execution level

3. **❌ WRONG**: I said MICRO/MESO/MACRO relate to chunk types
   - **✅ CORRECT**:
     - **MICRO** = Execution level for answering the 300 detailed questions
     - **MESO** = Aggregation by 4 clusters of policy areas
     - **MACRO** = Analysis of plan convergence across all 10 policy areas

4. **❌ WRONG**: I created incorrect mappings in CANONICAL_FLUX.md suggesting ChunkType determines which executors run
   - **✅ CORRECT**: Chunks are routed to executors based on Policy Area (PA01-PA10) + Dimension (D1-D6) alignment

---

## Correct Architecture

### 1. The 30 Executors (D1Q1 through D6Q5)

**Structure**: 6 Dimensions × 5 Question Executors = 30 Total Executors

```python
# Dimension 1: INSUMOS (Diagnóstico y Recursos)
D1Q1_Executor, D1Q2_Executor, D1Q3_Executor, D1Q4_Executor, D1Q5_Executor

# Dimension 2: ACTIVIDADES (Diseño de Intervención)
D2Q1_Executor, D2Q2_Executor, D2Q3_Executor, D2Q4_Executor, D2Q5_Executor

# Dimension 3: PRODUCTOS (Productos y Outputs)
D3Q1_Executor, D3Q2_Executor, D3Q3_Executor, D3Q4_Executor, D3Q5_Executor

# Dimension 4: RESULTADOS (Resultados y Outcomes)
D4Q1_Executor, D4Q2_Executor, D4Q3_Executor, D4Q4_Executor, D4Q5_Executor

# Dimension 5: IMPACTOS (Impactos de Largo Plazo)
D5Q1_Executor, D5Q2_Executor, D5Q3_Executor, D5Q4_Executor, D5Q5_Executor

# Dimension 6: CAUSALIDAD (Teoría de Cambio)
D6Q1_Executor, D6Q2_Executor, D6Q3_Executor, D6Q4_Executor, D6Q5_Executor
```

**Key Insight**: Each executor is an **ORCHESTRATION OF MULTIPLE METHODS**, not a single method.

### 2. The 300 Questions

**Structure** (from `questionnaire_monolith.json`):
- **306 total questions** in the questionnaire:
  - **1 MACRO question** (Q305): Holistic vision assessment across all clusters
  - **4 MESO questions** (Q301-Q304): Cluster integration questions
  - **~300 MICRO questions**: Detailed policy assessment questions

**Question Distribution**:
- Each policy area (PA01-PA10) has multiple questions
- Questions span across 6 dimensions (D1-D6)
- Questions are of different **types** (100+ unique pattern types like `analisis_contextual`, `coherencia_recursos`, `meta_cuantitativa`, etc.)

### 3. The 6 Dimensions (Theory of Change)

From `questionnaire_monolith.json` (lines 4-9):

```json
{
  "D1": {"code": "DIM01", "name": "INSUMOS", "label": "Diagnóstico y Recursos"},
  "D2": {"code": "DIM02", "name": "ACTIVIDADES", "label": "Diseño de Intervención"},
  "D3": {"code": "DIM03", "name": "PRODUCTOS", "label": "Productos y Outputs"},
  "D4": {"code": "DIM04", "name": "RESULTADOS", "label": "Resultados y Outcomes"},
  "D5": {"code": "DIM05", "name": "IMPACTOS", "label": "Impactos de Largo Plazo"},
  "D6": {"code": "DIM06", "name": "CAUSALIDAD", "label": "Teoría de Cambio"}
}
```

### 4. The 10 Policy Areas

From `questionnaire_monolith.json` (lines 12-41):

```json
{
  "PA01": "Derechos de las mujeres e igualdad de género",
  "PA02": "Prevención de la violencia y protección...",
  "PA03": "Ambiente sano, cambio climático...",
  "PA04": "Derechos económicos, sociales y culturales",
  "PA05": "Derechos de las víctimas y construcción de paz",
  "PA06": "Derecho al buen futuro de la niñez...",
  "PA07": "Tierras y territorios",
  "PA08": "Líderes y lideresas, defensores de DDHH...",
  "PA09": "Crisis de derechos de personas privadas de libertad",
  "PA10": "Migración transfronteriza"
}
```

### 5. The 4 Clusters (MESO Level)

From `questionnaire_monolith.json`:
- **CLUSTER_1**: Groups specific policy areas for security/peace topics
- **CLUSTER_2**: Groups policy areas for population groups
- **CLUSTER_3**: Groups policy areas for territory-environment
- **CLUSTER_4**: Groups policy areas for social rights & crisis

### 6. The 8 ChunkTypes (Content Classification)

From `scripts/smart_policy_chunks_canonic_phase_one.py` (lines 156-164):

```python
class ChunkType(Enum):
    DIAGNOSTICO = "diagnostico"      # Diagnostic/situation analysis content
    ESTRATEGIA = "estrategia"        # Strategy/objectives content
    METRICA = "metrica"              # Metrics/indicators content
    FINANCIERO = "financiero"        # Budget/financial content
    NORMATIVO = "normativo"          # Legal/normative content
    OPERATIVO = "operativo"          # Operational/implementation content
    EVALUACION = "evaluacion"        # Evaluation/monitoring content
    MIXTO = "mixto"                  # Mixed/hybrid content
```

**Purpose**: Indicates what TYPE OF CONTENT the chunk contains, NOT which executor to use.

**Classification**: Determined by keyword matching in `_classify_chunk_type` method (line 2563).

### 7. Chunk Routing Architecture

**Location**: `src/saaaaaa/core/orchestrator/chunk_router.py`

**Key Insight**: Routing is based on:
1. **Semantic chunk type** (diagnostic, activity, indicator, resource, temporal, entity)
2. **Policy Area** (PA01-PA10)
3. **Dimension** (D1-D6)

**NOT based on ChunkType enum**!

**Routing Table** (lines 36-43):
```python
ROUTING_TABLE: dict[str, list[str]] = {
    "diagnostic": ["D1Q1", "D1Q2", "D1Q5"],  # Baseline/gap analysis executors
    "activity": ["D2Q1", "D2Q2", "D2Q3", "D2Q4", "D2Q5"],  # Intervention executors
    "indicator": ["D3Q1", "D3Q2", "D4Q1", "D5Q1"],  # Metric/indicator executors
    "resource": ["D1Q3", "D2Q4", "D5Q5"],  # Financial/resource executors
    "temporal": ["D1Q5", "D3Q4", "D5Q4"],  # Timeline executors
    "entity": ["D2Q3", "D3Q3"],  # Responsibility/entity executors
}
```

**Result Grouping** (from `core.py` line 2514):
```python
key = (result.dimension, result.policy_area)  # Results keyed by (dimension, policy_area)
```

### 8. Smart Policy Chunks Alignment

**From User's Correction**:
> "LOS SMART POLICY CHUNKS ESTAN PENSADOS PARA EL CHUNK QUE LE LLEGUE A CADA EXECUTOR ESTE ALINEADO CON SU POLICY AREA Y SU DIMENSION DE ANALISIS."

**Translation**:
Smart Policy Chunks are designed so that:
- Each chunk that reaches an executor is **aligned with its Policy Area** (PA01-PA10)
- Each chunk is **aligned with its Dimension** (D1-D6)

**Chunk Generation**:
- `PolicyAreaChunkCalibrator` generates **exactly 10 chunks per policy area**
- Total: 100+ chunks across all PA01-PA10
- Each chunk has metadata indicating its policy area and dimension alignment

---

## MICRO/MESO/MACRO Execution Levels (CORRECT)

### MICRO Level
- **Definition**: Execution level for answering the **300 detailed questions**
- **Example**: D3Q2 asks "¿Se especifican indicadores medibles para producto X?"
- **Executors**: The 30 executors (D1Q1-D6Q5) operate at this level

### MESO Level
- **Definition**: **Aggregation by 4 clusters** of policy areas
- **Example**: Cluster 1 aggregates results from PA02, PA03, PA07
- **Questions**: Q301-Q304 (4 MESO questions)

### MACRO Level
- **Definition**: **Analysis of plan convergence** across all 10 policy areas
- **Example**: Q305 asks "¿El plan presenta visión integral que articula todos los clusters?"
- **Questions**: Q305 (1 MACRO question)

---

## Phase 1 Audit Results (CORRECT WORK)

The following audit work was **CORRECT** and should be preserved:

### ✅ H1.5: Comprehensive Validation in SPCAdapter
**File**: `src/saaaaaa/utils/spc_adapter.py`
**Changes**: Added 6-layer validation (V1-V6) in `to_preprocessed_document` method
**Status**: CORRECT - Should be kept

### ✅ H1.4: Robust Budget Extraction
**File**: `src/saaaaaa/processing/spc_ingestion/converter.py`
**Changes**: Enhanced `_extract_budget` method with 4 regex patterns + 4 fallback strategies
**Status**: CORRECT - Should be kept

### ✅ Dependency Addition
**File**: `setup.py`
**Changes**: Added `ftfy>=6.0.0` for encoding repair
**Status**: CORRECT - Should be kept

### ❌ CANONICAL_FLUX.md Updates
**File**: `CANONICAL_FLUX.md`
**Changes**: Added incorrect ChunkType → Executor mappings
**Status**: INCORRECT - Must be deleted/reverted

---

## Summary of Errors in CANONICAL_FLUX.md

Lines 58-69: **WRONG** - Created `CHUNK_TYPE_TO_RESOLUTION` mapping suggesting ChunkType determines MICRO/MESO/MACRO

Lines 147-151: **WRONG** - Suggested ChunkType maps to execution level

Lines 222-277: **WRONG** - Entire "ChunkType → Executor Mapping Verification" section based on incorrect architecture

---

## Next Steps

1. ✅ Delete branch `claude/audit-pipeline-phase-one-014XHA5srrJyNRCt9ZrVYTES`
2. ✅ Create new branch
3. ✅ Cherry-pick ONLY the correct changes (H1.4, H1.5, setup.py)
4. ✅ Do NOT include the incorrect CANONICAL_FLUX.md changes
5. ✅ Commit and push with clear messages

---

## References

- `data/questionnaire_monolith.json`: 306 questions, 30 executor patterns, dimensions, policy areas
- `src/saaaaaa/core/orchestrator/executors.py`: 30 executor class definitions
- `scripts/smart_policy_chunks_canonic_phase_one.py`: Chunk generation, ChunkType classification
- `src/saaaaaa/core/orchestrator/chunk_router.py`: Semantic routing logic
- `src/saaaaaa/core/orchestrator/core.py`: Result grouping by (dimension, policy_area)
