# FARFAN Mechanistic Policy Pipeline - QUICK REFERENCE GUIDE

## One-Sentence Overview
The FARFAN pipeline ingests policy documents through a 15-phase Smart Policy Chunking (SPC) system, converts chunks into a standardized Canon format, adapts them for orchestration, then executes 305 programmatic questions across 38+ dynamic executors with deterministic, auditable results.

---

## Phase 1: Smart Policy Chunking (SPC)

| Item | Location | Details |
|------|----------|---------|
| **Entry Point** | `scripts/smart_policy_chunks_canonic_phase_one.py` | 3,097 lines, 15-phase analysis |
| **Main Class** | `StrategicChunkingSystem` | `generate_smart_chunks()` method |
| **Output** | `SmartPolicyChunk` objects | 8 types, rich metadata |
| **Chunk Types** | 8 types | DIAGNOSTICO, ESTRATEGIA, METRICA, FINANCIERO, NORMATIVO, OPERATIVO, EVALUACION, MIXTO |

### SPC Output Example
```python
SmartPolicyChunk {
  chunk_id: "chunk_001",
  text: "...",
  chunk_type: ChunkType.DIAGNOSTICO,
  semantic_density: 0.85,
  related_chunks: [("chunk_002", 0.92), ...],
  strategic_importance: 0.88
}
```

---

## Phase 2: SPC Conversion & Adaptation

| Step | Class | Location | Transforms To |
|------|-------|----------|----------------|
| 1 | `SmartChunkConverter` | `src/saaaaaa/processing/spc_ingestion/converter.py` | `CanonPolicyPackage` |
| 2 | `SPCAdapter` | `src/saaaaaa/utils/spc_adapter.py` | `PreprocessedDocument` |

### Chunk Type → Resolution Mapping
- DIAGNOSTICO, NORMATIVO, EVALUACION, MIXTO → **MESO**
- METRICA, FINANCIERO, OPERATIVO → **MICRO**
- ESTRATEGIA → **MACRO**

---

## Phase 3-11: Question Execution

| Component | Purpose | Location |
|-----------|---------|----------|
| **Orchestrator** | Main engine | `src/saaaaaa/core/orchestrator/core.py` |
| **Choreographer** | Question executor | `src/saaaaaa/core/orchestrator/choreographer.py` |
| **FlowController** | DAG builder | `src/saaaaaa/core/orchestrator/choreographer.py` |
| **ExtendedArgRouter** | Method invoker | `src/saaaaaa/core/orchestrator/arg_router.py` |

### Execution Flow per Question (305 total)
```
Load Question Metadata
  ↓
Map to Base Slot (e.g., "D1Q1")
  ↓
Build ExecutionPlan (FlowController)
  ↓
Route to Chunks (ChunkRouter) [optional]
  ↓
For each Method:
  - Validate arguments (ExtendedArgRouter)
  - Instantiate executor from registry
  - Execute method
  - Collect evidence
  ↓
Return QuestionResult
```

---

## Questionnaire Integrity (THE CRITICAL FILE)

| Property | Value |
|----------|-------|
| **File** | `/data/questionnaire_monolith.json` |
| **Loader** | `load_questionnaire()` (ONLY way to load) |
| **Questions** | 305 total (300 micro + 4 meso + 1 macro) |
| **SHA-256** | `27f7f784583d637158cb70ee236f1a98f77c1a08366612b5ae11f3be24062658` |
| **Immutable** | Yes (MappingProxyType + tuples) |
| **Type** | `CanonicalQuestionnaire` (ONLY valid type) |

### Question Structure
```python
{
  "question_id": "Q001",
  "question_global": 1,                    # 1-305
  "base_slot": "D1Q1",                     # Execution slot
  "policy_area_id": "PA01",                # PA01-PA10
  "method_sets": [                         # Methods to execute
    {
      "class": "PolicyAnalyzer",
      "function": "analyze",
      "method_type": "analysis",
      "priority": 3                        # CRITICO(3), IMPORTANTE(2), COMPLEMENTARIO(1)
    }
  ]
}
```

---

## Executors (Dynamic Discovery)

| Registry | Location | Count |
|----------|----------|-------|
| **Class Registry** | `src/saaaaaa/core/orchestrator/class_registry.py` | 38+ classes |
| **Configuration** | `src/saaaaaa/core/orchestrator/executor_config.py` | CONSERVATIVE_CONFIG |

### Sample Registered Executors
- `IndustrialPolicyProcessor` - Policy analysis
- `BayesianEvidenceScorer` - Evidence scoring
- `CausalExtractor` - Causal inference
- `TeoriaCambio` - Theory of change analysis
- `SemanticAnalyzer` - Semantic analysis
- `PolicyContradictionDetector` - Contradiction detection
- (30+ more from `saaaaaa.processing` and `saaaaaa.analysis`)

---

## Signals & Pattern Matching

| Property | Details |
|----------|---------|
| **Patterns** | ~2,200 extracted from questions |
| **Grouping** | By policy_area_id (PA01-PA10) |
| **Loader** | `signal_loader.py` |
| **Tracker** | `SignalConsumptionProof` (hash chain) |
| **Verification** | Merkle tree of pattern matches |

---

## Chunk Routing (SPC-Aware Execution)

| Chunk Type | Routed to Executors |
|------------|-------------------|
| `diagnostic` | D1Q1, D1Q2, D1Q5 |
| `activity` | D2Q1-D2Q5 |
| `indicator` | D3Q1, D3Q2, D4Q1, D5Q1 |
| `resource` | D1Q3, D2Q4, D5Q5 |
| `temporal` | D1Q5, D3Q4, D5Q4 |
| `entity` | D2Q3, D3Q3 |

---

## Advanced Execution Paradigms

| Paradigm | Activation | Purpose |
|----------|-----------|---------|
| **Quantum Optimization** | num_methods >= 3 | Path selection |
| **Neuromorphic Computing** | Every data flow | Adaptive processing |
| **Causal Inference** | 2+ questions | Execution order |
| **Meta-Learning** | Every execution | Strategy selection |
| **Information Theory** | Bottleneck detection | Entropy optimization |
| **Attention Mechanism** | Dynamic | Method prioritization |
| **Topological Analysis** | Complex data | Manifold understanding |

---

## Directory Map (Canonical Locations)

```
src/saaaaaa/core/orchestrator/          [30+ modules - THE REAL IMPLEMENTATION]
  ├── core.py                            Main orchestrator
  ├── choreographer.py                   Question execution
  ├── executors.py                       Advanced executors
  ├── arg_router.py                      Argument validation (30+ routes)
  ├── questionnaire.py                   Questionnaire integrity
  ├── signal_loader.py                   Pattern extraction
  ├── chunk_router.py                    SPC chunk routing
  ├── class_registry.py                  Executor discovery
  └── [20+ supporting modules]

src/saaaaaa/processing/spc_ingestion/   [SPC conversion layer]
  ├── __init__.py                        CPPIngestionPipeline
  ├── converter.py                       SmartChunkConverter
  ├── quality_gates.py
  └── structural.py

src/saaaaaa/utils/                       [Adapters & utilities]
  ├── spc_adapter.py                     SPC→PreprocessedDocument
  ├── cpp_adapter.py                     Backward compatibility

orchestrator/                            [COMPATIBILITY SHIMS - Not the real thing!]
  ├── __init__.py
  └── [Thin wrappers to src/saaaaaa/core/orchestrator/]
```

---

## Data Transformation Pipeline (Visual)

```
Policy Document
     ↓
StrategicChunkingSystem (15 phases)
     ↓
SmartPolicyChunk[] (8 types, rich metadata)
     ↓
SmartChunkConverter (type mapping, graph building)
     ↓
CanonPolicyPackage (chunks + manifest + metrics)
     ↓
SPCAdapter (deterministic ordering)
     ↓
PreprocessedDocument (orchestrator-ready)
     ↓
Orchestrator + Choreographer (305 questions)
     ↓
38+ Executors (dynamic dispatch)
     ↓
QuestionResult[] (evidence + metrics)
     ↓
Final Assessment Report
```

---

## Critical Implementation Details

### 1. Questionnaire Loading
```python
from saaaaaa.core.orchestrator.questionnaire import load_questionnaire

q = load_questionnaire()  # ONLY way to load
# Returns CanonicalQuestionnaire with:
#   - sha256 verified
#   - 305 questions guaranteed
#   - Immutable data structures
```

### 2. Executing a Question
```python
from saaaaaa.core.orchestrator.choreographer import Choreographer

choreographer = Choreographer()
result = choreographer.execute_question(
    question_global=1,
    monolith=questionnaire.data,
    method_catalog=catalog
)
# Returns QuestionResult with evidence dict
```

### 3. Routing Arguments to Method
```python
from saaaaaa.core.orchestrator.arg_router import ExtendedArgRouter

router = ExtendedArgRouter()
router.route_arguments(
    payload={"text": "...", "context": {...}},
    method_spec=method_signature
)
# Validates, applies special routes (30+), calls method
```

### 4. Routing Chunks to Executors
```python
from saaaaaa.core.orchestrator.chunk_router import ChunkRouter

router = ChunkRouter()
route = router.route_chunk(chunk)
# Returns ChunkRoute with executor_class + methods
```

---

## Key Files to Understand the Pipeline

### Must-Read (In Order)
1. `PROJECT_STRUCTURE.md` - Repository organization
2. `ARCHITECTURE_REFACTORING.md` - Hexagonal architecture principles
3. `src/saaaaaa/core/orchestrator/questionnaire.py` - Questionnaire integrity
4. `src/saaaaaa/core/orchestrator/choreographer.py` - Question execution
5. `src/saaaaaa/processing/spc_ingestion/converter.py` - SPC→Canon conversion
6. `src/saaaaaa/utils/spc_adapter.py` - Canon→Orchestrator adaptation

### Advanced Topics
- `src/saaaaaa/core/orchestrator/executors.py` - Advanced paradigms
- `src/saaaaaa/core/orchestrator/arg_router.py` - Argument routing (30+ routes)
- `src/saaaaaa/analysis/spc_causal_bridge.py` - SPC causal analysis
- `src/saaaaaa/core/orchestrator/class_registry.py` - Executor discovery

---

## Testing the Pipeline

```python
# Minimal test
from saaaaaa.processing.spc_ingestion import StrategicChunkingSystem
from saaaaaa.utils.spc_adapter import adapt_spc_to_orchestrator
from saaaaaa.core.orchestrator import Orchestrator

# Phase 1: Chunk
scs = StrategicChunkingSystem()
smart_chunks = scs.generate_smart_chunks(document_text, metadata)

# Phase 2: Convert
# (SmartChunkConverter internally)
canon_package = converter.convert_to_canon_package(smart_chunks, metadata)

# Phase 3: Adapt
doc = adapt_spc_to_orchestrator(canon_package)

# Phase 4: Execute
orch = Orchestrator(doc)
# ... execution happens across 305 questions
```

---

## Performance Notes

| Operation | Time | Memory |
|-----------|------|--------|
| SPC Phase-1 (15 phases) | Minutes | 100-200MB |
| Orchestrator initialization | Seconds | 50-100MB |
| Single question execution | 50-200ms | Per question |
| Batch (5 questions) | 300-1000ms | - |
| Batch (30 questions) | 2-5 seconds | - |
| Full 305 questions | Minutes | 200-300MB total |

---

## Conclusion

The FARFAN pipeline is a sophisticated, multi-phase system that:

1. **Intelligently chunks** policy documents (15-phase SPC)
2. **Transforms** chunks through standardized formats (Canon → PreprocessedDocument)
3. **Dynamically discovers** 38+ executor classes
4. **Deterministically executes** 305 programmatic questions
5. **Validates arguments** strictly (ExtendedArgRouter)
6. **Routes chunks** intelligently (ChunkRouter)
7. **Consumes signals** with cryptographic proof
8. **Collects evidence** in hash chains and Merkle trees
9. **Reports results** with comprehensive metrics

**The code follows Hexagonal Architecture principles**: pure business logic in core, I/O at boundaries, and dependency injection throughout.

