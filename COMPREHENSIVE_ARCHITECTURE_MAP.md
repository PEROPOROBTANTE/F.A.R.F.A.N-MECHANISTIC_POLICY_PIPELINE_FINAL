# FARFAN Mechanistic Policy Pipeline - Comprehensive Architecture Map

## 1. SMART POLICY CHUNKING (SPC) IMPLEMENTATION - Phase 1

### Primary Entry Point
- **File**: `/home/user/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE/scripts/smart_policy_chunks_canonic_phase_one.py` (3,097 lines)
- **Class**: `StrategicChunkingSystem`
- **Function**: `generate_smart_chunks(document_text: str, metadata: dict) -> List[SmartPolicyChunk]`

### SPC Processing Pipeline
The SPC system performs a 15-phase analysis:
1. Document preprocessing and structural analysis
2. Topic modeling and knowledge graph construction
3. Causal chain extraction
4. Temporal, argumentative, and discourse analysis
5. Smart chunk creation with inter-chunk relationships
6. Quality validation and strategic ranking

### SPC Ingestion Module
- **Location**: `/home/user/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE/src/saaaaaa/processing/spc_ingestion/`
- **Files**:
  - `__init__.py` - CPPIngestionPipeline wrapper
  - `converter.py` (21KB) - SmartChunkConverter class
  - `quality_gates.py` (5.5KB) - Quality validation
  - `structural.py` (2.8KB) - Structural analysis

### Key SPC Components

#### SmartChunkConverter Class
- **File**: `/home/user/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE/src/saaaaaa/processing/spc_ingestion/converter.py`
- **Purpose**: Converts SmartPolicyChunk → CanonPolicyPackage format
- **Mapping**: 8 ChunkTypes → ChunkResolution levels:
  - DIAGNOSTICO → MESO
  - ESTRATEGIA → MACRO
  - METRICA, FINANCIERO, OPERATIVO → MICRO
  - NORMATIVO, EVALUACION, MIXTO → MESO
- **Outputs**:
  - ChunkGraph (nodes, edges, relationships)
  - PolicyManifest (axes, programs, projects)
  - QualityMetrics (provenance, coherence, coverage)
  - IntegrityIndex (verification scores)

#### CPPIngestionPipeline Class
- **File**: `/home/user/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE/src/saaaaaa/processing/spc_ingestion/__init__.py`
- **Async Method**: `async process(document_path, document_id, title, max_chunks)`
- **Returns**: CanonPolicyPackage (orchestrator-ready)

### SPC Canonical Producers
Located in `/home/user/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE/src/saaaaaa/processing/`:
- `embedding_policy.py` - EmbeddingPolicyProducer (BGE-M3 2024 SOTA)
- `semantic_chunking_policy.py` - SemanticChunkingProducer
- `policy_processor.py` - create_policy_processor()

### SPC to Orchestrator Bridge
- **File**: `/home/user/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE/src/saaaaaa/utils/spc_adapter.py`
- **Class**: SPCAdapter (alias for CPPAdapter)
- **Function**: `adapt_spc_to_orchestrator(spc_package) -> PreprocessedDocument`
- **Purpose**: Converts SPC CanonPolicyPackage to orchestrator PreprocessedDocument

---

## 2. ORCHESTRATOR IMPLEMENTATION

### Architecture: Two-Layer Imports
The system uses **compatibility shims** for backward compatibility while consolidating the canonical implementation:

#### Real Implementation Location
- **Directory**: `/home/user/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE/src/saaaaaa/core/orchestrator/`
- **Files** (30+ Python modules):
  - `core.py` - Main orchestrator logic & data models
  - `choreographer.py` - Single micro-question execution
  - `executors.py` - Advanced data flow executors (quantum, neuromorphic, causal)
  - `arg_router.py` - Argument routing with 30+ special routes
  - `contract_loader.py` - JSON contract/configuration loader
  - `questionnaire.py` - Questionnaire integrity & loading
  - `signal_loader.py` - Pattern extraction from questionnaire
  - `chunk_router.py` - SPC chunk routing to executors
  - `factory.py` - Component factories
  - `class_registry.py` - Dynamic executor class loading
  - `calibration_registry.py` - Calibration system integration
  - Plus supporting modules for signals, versions, evidence tracking, etc.

#### Compatibility Shim Layer
- **Directory**: `/home/user/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE/orchestrator/`
- **Files**: Thin wrappers redirecting to real implementation in `src/saaaaaa/core/orchestrator/`

### Core Orchestrator Classes

#### Orchestrator (Main)
- **Location**: `/home/user/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE/src/saaaaaa/core/orchestrator/core.py`
- **Data Models**:
  - `PreprocessedDocument` - Input document with chunks and metadata
  - `PhaseResult` - Result from each orchestration phase
  - `Evidence` - Evidence collected during execution
  - `AbortSignal` / `AbortRequested` - Execution control

#### Choreographer (Micro-Question Executor)
- **Location**: `/home/user/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE/src/saaaaaa/core/orchestrator/choreographer.py`
- **Key Classes**:
  - `Choreographer` - Facade exposing micro-question orchestration helpers
  - `FlowController` - Deterministic execution plan construction
  - `DAGNode` - Execution metadata for method groups
  - `ExecutionPlan` - Deterministic orchestration plan
  - `ChoreographerDispatcher` - Method package dispatcher
- **Key Methods**:
  - `_map_question_to_slot()` - Map question ID to execution metadata
  - `build_execution_dag()` - Build ExecutionPlan from method packages
  - `identify_parallel_branches()` - Identify parallelizable methods

#### FlowController
- **Purpose**: Constructs deterministic execution plans for questions
- **Method**: `build_execution_dag(flow_spec, method_packages) -> ExecutionPlan`
- **Method**: `identify_parallel_branches(plan) -> List[List[DAGNode]]`

### Advanced Executors
- **Location**: `/home/user/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE/src/saaaaaa/core/orchestrator/executors.py`
- **Features** (Advanced Paradigms):
  1. Quantum Optimization - Path selection when num_methods >= 3
  2. Neuromorphic Computing - Adaptive data flow processing
  3. Causal Inference - Execution order optimization
  4. Meta-Learning - Adaptive execution strategy selection
  5. Information Theory - Bottleneck detection & entropy optimization
  6. Attention Mechanism - Method prioritization
  7. Topological Data Analysis - Data manifold understanding
  8. Category Theory - Composable execution pipelines
  9. Probabilistic Programming - Uncertainty quantification

### Argument Routing
- **Location**: `/home/user/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE/src/saaaaaa/core/orchestrator/arg_router.py`
- **Class**: `ExtendedArgRouter`
- **Features**:
  - 30+ special route handlers for common methods
  - Strict validation (fail-fast on missing required arguments)
  - **kwargs support for forward compatibility
  - Full observability and metrics

---

## 3. QUESTIONNAIRE STRUCTURE & INTEGRITY

### Questionnaire Integrity Module
- **Location**: `/home/user/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE/src/saaaaaa/core/orchestrator/questionnaire.py`
- **Canonical Loader**: `load_questionnaire() -> CanonicalQuestionnaire`
- **Integrity Rules** (Enforcement Protocol):
  1. **ONE PATH**: questionnaire_monolith.json at `/data/questionnaire_monolith.json`
  2. **ONE HASH**: SHA-256 = `27f7f784583d637158cb70ee236f1a98f77c1a08366612b5ae11f3be24062658`
  3. **ONE STRUCTURE**: Exactly 305 questions (300 micro + 4 meso + 1 macro)
  4. **ONE LOADER**: `load_questionnaire()` is THE ONLY way to load
  5. **ONE TYPE**: `CanonicalQuestionnaire` is the ONLY valid representation

### CanonicalQuestionnaire Class
- **Immutable**: Uses MappingProxyType and tuples
- **Attributes**:
  - `data`: MappingProxyType[str, Any]
  - `sha256`: str (must match EXPECTED_HASH)
  - `micro_questions`: tuple[MappingProxyType, ...]
  - `meso_questions`: tuple[MappingProxyType, ...]
  - `macro_question`: MappingProxyType | None
  - `micro_question_count`: int (must be 300)
  - `total_question_count`: int (must be 305)
  - `version`: str
  - `schema_version`: str

### Question Structure
Each question contains:
- `question_id`: str
- `question_global`: int (1-305)
- `base_slot`: str (e.g., "D1Q1", "D2Q3")
- `method_sets`: List of method packages to execute
  - Each method package includes:
    - `class`: Executor class name
    - `function`: Method name
    - `method_type`: Type of method
    - `priority`: Priority level (CRITICO=3, IMPORTANTE=2, COMPLEMENTARIO=1)

### Signal Extraction & Loading
- **File**: `/home/user/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE/src/saaaaaa/core/orchestrator/signal_loader.py`
- **Purpose**: Extract ~2200 patterns from 300 micro_questions
- **Grouping**: By policy_area_id (PA01-PA10)
- **Output**: SignalPack objects with fingerprints

### Signal Consumption Tracking
- **File**: `/home/user/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE/src/saaaaaa/core/orchestrator/signal_consumption.py`
- **Class**: `SignalConsumptionProof`
- **Features**:
  - Hash chain tracking of pattern matches
  - Consumption proof generation per executor
  - Merkle tree verification of pattern origin
  - Deterministic proof generation

---

## 4. EXECUTORS & EXECUTOR DISCOVERY

### Class Registry (Dynamic Loader)
- **Location**: `/home/user/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE/src/saaaaaa/core/orchestrator/class_registry.py`
- **Function**: `build_class_registry() -> dict[str, type[object]]`
- **Discovers** 38 executor classes from:
  - `saaaaaa.processing.*` (policy processors, analyzers)
  - `saaaaaa.analysis.*` (semantic, causal, financial analyzers)

### Registered Executor Classes (Sample)
```python
_CLASS_PATHS = {
    # Processing module
    "IndustrialPolicyProcessor": "saaaaaa.processing.policy_processor...",
    "BayesianEvidenceScorer": "saaaaaa.processing.policy_processor...",
    "AdvancedSemanticChunker": "saaaaaa.processing.embedding_policy...",
    
    # Analysis module
    "PolicyContradictionDetector": "saaaaaa.analysis.contradiction_deteccion...",
    "CausalExtractor": "saaaaaa.analysis.dereck_beach...",
    "TeoriaCambio": "saaaaaa.analysis.teoria_cambio...",
    "SemanticAnalyzer": "saaaaaa.analysis.Analyzer_one...",
    # ... 30+ more
}
```

### Executor Configuration
- **File**: `/home/user/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE/src/saaaaaa/core/orchestrator/executor_config.py`
- **Class**: `ExecutorConfig`
- **Default**: `CONSERVATIVE_CONFIG` for safe execution

### Chunk Routing
- **Location**: `/home/user/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE/src/saaaaaa/core/orchestrator/chunk_router.py`
- **Class**: `ChunkRouter`
- **Routing Table** (ChunkType → Executor slots):
  - `diagnostic` → [D1Q1, D1Q2, D1Q5]
  - `activity` → [D2Q1, D2Q2, D2Q3, D2Q4, D2Q5]
  - `indicator` → [D3Q1, D3Q2, D4Q1, D5Q1]
  - `resource` → [D1Q3, D2Q4, D5Q5]
  - `temporal` → [D1Q5, D3Q4, D5Q4]
  - `entity` → [D2Q3, D3Q3]

---

## 5. INTEGRATION POINTS & DATA FLOW

### Complete Data Flow Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                     DOCUMENT INPUT                              │
│         (Development Plan / Policy Document)                     │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│            PHASE 1: SMART POLICY CHUNKING (SPC)                 │
│                                                                  │
│  StrategicChunkingSystem.generate_smart_chunks()               │
│  Location: scripts/smart_policy_chunks_canonic_phase_one.py    │
│                                                                  │
│  15-Phase Analysis:                                            │
│  1. Document preprocessing & structural analysis               │
│  2. Topic modeling & knowledge graph construction              │
│  3. Causal chain extraction                                     │
│  4. Temporal & argumentative analysis                           │
│  5. Smart chunk creation with inter-chunk relationships        │
│  6. Quality validation & strategic ranking                     │
│                                                                  │
│  Output: List[SmartPolicyChunk]                                │
│    - chunk_id, content, normalized_text                        │
│    - semantic_density, section_hierarchy                       │
│    - chunk_type (8 types), causal_chain                        │
│    - policy_entities, related_chunks                           │
│    - confidence_metrics, coherence_score                       │
│    - completeness_index, strategic_importance                  │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│     CONVERSION: SmartChunk → CanonPolicyPackage                │
│                                                                  │
│  SmartChunkConverter (src/saaaaaa/processing/spc_ingestion/)   │
│  Method: convert_to_canon_package()                            │
│                                                                  │
│  Transformation:                                               │
│  - Map 8 ChunkTypes → ChunkResolution (MICRO/MESO/MACRO)      │
│  - Extract policy/time/geo facets from SPC data               │
│  - Build ChunkGraph with edges from related_chunks            │
│  - Preserve SPC rich data in metadata                         │
│  - Generate quality metrics & integrity index                 │
│                                                                  │
│  Output: CanonPolicyPackage                                    │
│    - ChunkGraph (chunks + relationships)                       │
│    - PolicyManifest (axes, programs, projects)               │
│    - QualityMetrics (provenance, coherence, coverage)        │
│    - IntegrityIndex (verification scores)                     │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│      ADAPTATION: CanonPolicyPackage → PreprocessedDocument     │
│                                                                  │
│  SPCAdapter / adapt_spc_to_orchestrator()                      │
│  Location: src/saaaaaa/utils/spc_adapter.py                   │
│                                                                  │
│  Transforms for orchestrator consumption:                      │
│  - Orders chunks by text_span.start (deterministic)           │
│  - Computes provenance_completeness metric                    │
│  - Prepares chunk graph for execution                         │
│                                                                  │
│  Output: PreprocessedDocument                                  │
│    - document_id, metadata                                     │
│    - chunks (with resolution levels)                          │
│    - chunk_graph (relationships)                              │
│    - chunk_metadata (policies, entities, etc.)                │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│           PHASE 2: ORCHESTRATOR INITIALIZATION                  │
│                                                                  │
│  Orchestrator.__init__(document: PreprocessedDocument)         │
│  Location: src/saaaaaa/core/orchestrator/core.py              │
│                                                                  │
│  Setup:                                                        │
│  1. Load questionnaire_monolith.json via load_questionnaire() │
│  2. Load signal patterns via signal_loader                     │
│  3. Build class registry via class_registry.py                 │
│  4. Initialize ChunkRouter for chunk-based routing            │
│  5. Prepare execution metadata                                 │
│                                                                  │
│  State:                                                        │
│  - self.document: PreprocessedDocument                        │
│  - self.questionnaire: CanonicalQuestionnaire                │
│  - self.class_registry: dict[str, type[object]]             │
│  - self.chunk_router: ChunkRouter                            │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│       PHASE 3-11: QUESTION EXECUTION BY CHOREOGRAPHER          │
│                                                                  │
│  For each question_global (1-305):                            │
│    Choreographer.execute_question(question_global)            │
│                                                                  │
│  Step 1: Map Question to Slot                                │
│    _map_question_to_slot()                                    │
│    - Find question in monolith                                │
│    - Extract base_slot (e.g., "D1Q1")                        │
│    - Get method_sets for this question                       │
│                                                                  │
│  Step 2: Build Execution DAG                                 │
│    FlowController.build_execution_dag()                      │
│    - Create DAGNode for each method group                     │
│    - Map methods by class/function/priority                   │
│    - Identify parallel branches                              │
│    Output: ExecutionPlan                                      │
│                                                                  │
│  Step 3: Route Chunks (if chunk-based)                      │
│    ChunkRouter.route_chunk(chunk)                            │
│    - Determine executor class for chunk type                  │
│    - Filter methods relevant to chunk                        │
│    Output: ChunkRoute                                        │
│                                                                  │
│  Step 4: Execute Methods with Argument Routing              │
│    For each DAGNode in ExecutionPlan:                        │
│      ExtendedArgRouter.route_arguments()                     │
│      - Match payload to method signature                     │
│      - Apply special routing rules (30+ routes)              │
│      - Validate all required arguments present               │
│      - Call method with proper arguments                     │
│                                                                  │
│  Step 5: Collect Evidence                                   │
│    EvidenceRegistry.record_evidence()                        │
│    - Track method results                                    │
│    - Compute confidence scores                              │
│    - Build evidence DAG                                     │
│                                                                  │
│  Output: QuestionResult                                      │
│    - question_global, base_slot                             │
│    - evidence (dict with all collected results)            │
│    - raw_results, execution_time_ms                        │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│        PHASE 12+: AGGREGATION & REPORTING                      │
│                                                                  │
│  Aggregate results across all 305 questions                   │
│  Generate scoring, analysis, and reports                     │
│  Output: Comprehensive assessment of policy document         │
└─────────────────────────────────────────────────────────────────┘
```

### Key Integration Points

#### 1. SPC → Orchestrator Bridge (spc_adapter.py)
```python
# Import chain:
SmartPolicyChunk 
  → SmartChunkConverter.convert_to_canon_package()
  → CanonPolicyPackage
  → adapt_spc_to_orchestrator()
  → PreprocessedDocument
  → Orchestrator
```

#### 2. Questionnaire Loading (questionnaire.py)
```python
# Single canonical entry point:
load_questionnaire() → CanonicalQuestionnaire
  - Verifies SHA-256 hash
  - Validates 305 question structure
  - Returns immutable questionnaire
```

#### 3. Signal Consumption (signal_loader.py + signal_consumption.py)
```python
# Pattern extraction and tracking:
extract_patterns_by_policy_area()
  → SignalPack objects (10 policy areas)
  → SignalConsumptionProof tracking during execution
  → Merkle tree verification
```

#### 4. Chunk-Based Routing (chunk_router.py)
```python
# Route chunks to specific executors:
ChunkRouter.route_chunk(chunk)
  → ChunkRoute (executor class + methods)
  → Filter executors by chunk type
  → Reduce redundant processing
```

#### 5. Argument Validation (arg_router.py)
```python
# Strict method invocation:
ExtendedArgRouter.route_arguments(payload, method_spec)
  → Validate all required arguments
  → Fail-fast on missing/unexpected arguments
  → Apply 30+ special route handlers
  → Call method with correct signature
```

---

## 6. DIRECTORY STRUCTURE & FILE ORGANIZATION

### Root Level Organization
```
/home/user/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE/
├── src/saaaaaa/                          [CANONICAL IMPLEMENTATION]
│   ├── core/
│   │   ├── orchestrator/                 [30+ orchestrator modules]
│   │   │   ├── core.py                   (orchestrator main logic)
│   │   │   ├── choreographer.py          (micro-question execution)
│   │   │   ├── executors.py              (advanced executors)
│   │   │   ├── arg_router.py             (argument routing)
│   │   │   ├── questionnaire.py          (questionnaire integrity)
│   │   │   ├── signal_loader.py          (pattern extraction)
│   │   │   ├── signal_consumption.py     (consumption tracking)
│   │   │   ├── chunk_router.py           (SPC chunk routing)
│   │   │   ├── class_registry.py         (executor discovery)
│   │   │   ├── contract_loader.py        (JSON config loading)
│   │   │   └── [...20+ more modules]
│   │   ├── ports.py                      (abstract interfaces)
│   │   ├── contracts.py                  (type definitions)
│   │   └── [calibration/, wiring/]
│   ├── processing/                       [SPC & document processing]
│   │   ├── spc_ingestion/                [SPC phase-1 conversion]
│   │   │   ├── __init__.py               (CPPIngestionPipeline)
│   │   │   ├── converter.py              (SmartChunkConverter)
│   │   │   ├── quality_gates.py
│   │   │   └── structural.py
│   │   ├── semantic_chunking_policy.py   (semantic chunking)
│   │   ├── embedding_policy.py           (BGE-M3 embeddings)
│   │   ├── policy_processor.py           (policy processing)
│   │   ├── document_ingestion.py
│   │   ├── aggregation.py
│   │   └── [cpp_ingestion/, ...]
│   ├── analysis/                         [Executors & analysis]
│   │   ├── spc_causal_bridge.py          (SPC→causal DAG)
│   │   ├── teoria_cambio.py              (theory of change)
│   │   ├── contradiction_deteccion.py    (contradiction detection)
│   │   ├── dereck_beach.py               (causal analysis)
│   │   ├── financiero_viabilidad_tablas.py
│   │   ├── Analyzer_one.py
│   │   └── [macro_prompts/, meso_cluster_analysis/, ...]
│   ├── utils/                            [Utilities & contracts]
│   │   ├── spc_adapter.py                (SPC→PreprocessedDocument)
│   │   ├── cpp_adapter.py                (backward compat)
│   │   ├── core_contracts.py             (TypedDict definitions)
│   │   ├── contracts_runtime.py          (Pydantic validators)
│   │   ├── evidence_registry.py
│   │   └── [validation/, determinism/, ...]
│   ├── flux/                             [Pipeline phases]
│   │   ├── phases.py                     (11-phase orchestration)
│   │   ├── cli.py
│   │   ├── models.py
│   │   └── configs.py
│   ├── infrastructure/                   [I/O adapters]
│   │   ├── filesystem.py
│   │   ├── environment.py
│   │   ├── clock.py
│   │   └── log_adapters.py
│   └── [api/, compat/, controls/, scoring/]
│
├── orchestrator/                         [COMPATIBILITY SHIMS]
│   ├── __init__.py
│   ├── choreographer_dispatch.py
│   ├── executors.py
│   ├── arg_router.py
│   ├── factory.py
│   ├── provider.py
│   ├── settings.py
│   └── README.md
│
├── scripts/                              [EXECUTABLES & UTILITIES]
│   ├── smart_policy_chunks_canonic_phase_one.py    (SPC phase-1, 3097 lines)
│   └── [other utility scripts]
│
├── config/                               [CONFIGURATION]
│   ├── canonical_ontologies/
│   │   └── policy_areas_and_dimensions.json
│   ├── rules/
│   └── schemas/
│
├── data/                                 [DATA & QUESTIONNAIRE]
│   ├── questionnaire_monolith.json       [CANONICAL QUESTIONNAIRE]
│   ├── bayesian_outputs/
│   └── plans/
│
├── tests/                                [TEST SUITE]
│   ├── integration/
│   ├── unit/
│   ├── calibration/
│   ├── operational/
│   └── [data/, paths/]
│
└── docs/                                 [DOCUMENTATION]
    ├── FINAL_DELIVERABLE_SUMMARY.md
    ├── WIRING_ARCHITECTURE.md
    ├── QUICKSTART.md
    └── [README.inventory.md, system/]
```

### Rust Components
```
spc_ingestion/                            [Rust SPC support]
├── src/
│   └── lib.rs                            (BLAKE3 hashing, unicode normalization)
├── Cargo.toml
└── [performance-critical operations]
```

---

## 7. KEY DATA STRUCTURES

### SPC Output: SmartPolicyChunk
```python
@dataclass
class SmartPolicyChunk:
    chunk_id: str
    document_id: str
    content_hash: str
    text: str
    normalized_text: str
    semantic_density: float
    section_hierarchy: List[str]
    document_position: tuple[int, int]
    chunk_type: ChunkType  # 8 types
    causal_chain: List[Any]
    policy_entities: List[Any]
    related_chunks: List[tuple[str, float]]  # (chunk_id, confidence)
    confidence_metrics: Dict[str, float]
    coherence_score: float
    completeness_index: float
    strategic_importance: float
```

### Orchestrator Input: PreprocessedDocument
```python
@dataclass
class PreprocessedDocument:
    document_id: str
    metadata: dict
    chunks: List[Chunk]
    chunk_graph: ChunkGraph
    chunk_metadata: dict
    title: str | None = None
    version: str | None = None
```

### Question Metadata from Questionnaire
```python
{
    "question_id": "Q001",
    "question_global": 1,
    "base_slot": "D1Q1",
    "policy_area_id": "PA01",
    "method_sets": [
        {
            "class": "IndustrialPolicyProcessor",
            "function": "analyze_diagnostico",
            "method_type": "analysis",
            "priority": 3  # CRITICO
        },
        # ... more methods
    ],
    "patterns": [
        # ~2200 patterns extracted across all questions
    ]
}
```

### Execution Results: QuestionResult
```python
@dataclass
class QuestionResult:
    question_global: int
    base_slot: str
    evidence: dict[str, Any]       # Collected from all methods
    raw_results: dict[str, Any]    # Raw method outputs
    execution_time_ms: float = 0.0
    error: Any | None = None
```

---

## 8. KEY ALGORITHMS & PARADIGMS

### 1. Deterministic Execution (Quantum-Inspired)
- **Purpose**: Reproducible results for same (policy_unit_id, correlation_id)
- **Implementation**: DeterministicSeeds with numpy + Python random seeding
- **Location**: src/saaaaaa/core/orchestrator/executors.py (QuantumState class)

### 2. Circuit Breaker Pattern
- **Purpose**: Fault isolation in concurrent execution
- **State**: open/closed based on failure count
- **Implementation**: CircuitBreakerState (async-safe)

### 3. Execution Metrics
- **Tracking**: Total/successful/failed executions, timing, method performance
- **Thread-Safe**: Uses threading.RLock() for global metrics
- **Purpose**: Performance monitoring and optimization

### 4. Evidence Registry
- **Purpose**: Track all collected evidence from methods
- **Feature**: Hash chain and Merkle tree verification
- **Location**: src/saaaaaa/core/orchestrator/evidence_registry.py

### 5. Signal Pattern Matching
- **Type**: ~2200 regex patterns from questionnaire
- **Consumption Proof**: Cryptographic hash chain of matches
- **Policy Areas**: 10 areas (PA01-PA10) with patterns
- **Verification**: Merkle tree for provenance

---

## 9. DOCUMENTATION FILES

### Architecture & Design
- `/home/user/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE/PROJECT_STRUCTURE.md` - Repository structure
- `/home/user/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE/ARCHITECTURE_REFACTORING.md` - Hexagonal architecture
- `/home/user/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE/orchestrator/README.md` - Orchestrator compatibility layer

### Analysis & Reports
- `/home/user/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE/docs/FINAL_DELIVERABLE_SUMMARY.md`
- `/home/user/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE/docs/WIRING_ARCHITECTURE.md`
- `/home/user/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE/docs/QUICKSTART.md`

---

## 10. INTEGRATION WIRING SUMMARY

### Import Dependencies
```
                    CLI / Document Input
                            │
                            ▼
        ┌─────────────────────────────────────┐
        │  StrategicChunkingSystem (SPC)      │
        │  smart_chunks_canonic_phase_one.py  │
        └────────────┬────────────────────────┘
                     │ SmartPolicyChunk[]
                     ▼
        ┌─────────────────────────────────────┐
        │  SmartChunkConverter                │
        │  spc_ingestion/converter.py         │
        └────────────┬────────────────────────┘
                     │ CanonPolicyPackage
                     ▼
        ┌─────────────────────────────────────┐
        │  SPCAdapter                         │
        │  spc_adapter.py                     │
        └────────────┬────────────────────────┘
                     │ PreprocessedDocument
                     ▼
        ┌─────────────────────────────────────┐
        │  Orchestrator.__init__()            │
        │  core/orchestrator/core.py          │
        └────────────┬────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
    Load Questionnaire      Build Class Registry
    (questionnaire.py)      (class_registry.py)
        │                         │
        └────────────┬────────────┘
                     │
                     ▼
    For each question (1-305):
        Choreographer.execute_question()
            │
            ├─ Load Signals (signal_loader.py)
            ├─ Map Question (questionnaire.py)
            ├─ Build DAG (choreographer.py)
            ├─ Route Chunks (chunk_router.py)
            ├─ Route Arguments (arg_router.py)
            ├─ Execute Methods (class_registry instantiates)
            ├─ Consume Signals (signal_consumption.py)
            └─ Collect Evidence (evidence_registry.py)
```

### Data Transformation Chain
```
Raw Document
    ↓
StrategicChunkingSystem (15 phases)
    ↓
SmartPolicyChunk objects
    ↓
SmartChunkConverter
    ↓
CanonPolicyPackage
    ↓
SPCAdapter
    ↓
PreprocessedDocument
    ↓
Orchestrator (305 questions × multiple executors)
    ↓
QuestionResult × 305
    ↓
Final Assessment Report
```

---

## 11. CRITICAL ASSUMPTIONS & REQUIREMENTS

1. **Questionnaire Integrity**: questionnaire_monolith.json must:
   - Contain exactly 305 questions
   - Match SHA-256 hash: `27f7f784583d637158cb70ee236f1a98f77c1a08366612b5ae11f3be24062658`
   - Be loaded ONLY via `load_questionnaire()` function

2. **Data Ordering**: Chunks are deterministically ordered by text_span.start

3. **Method Resolution**: All executor methods must be registered in `class_registry.py`

4. **Signal Patterns**: ~2200 patterns grouped by policy_area_id (PA01-PA10)

5. **Hexagonal Architecture**: 
   - Core modules (no I/O)
   - Ports (abstract interfaces)
   - Infrastructure (I/O adapters)
   - Orchestrator (composition root)

---

## 12. TESTING STRUCTURE

```
tests/
├── integration/        - End-to-end pipeline tests
├── unit/              - Individual component tests
├── calibration/       - Calibration system tests
├── operational/       - Operational scenario tests
├── data/              - Test data and fixtures
└── paths/             - Path resolution tests
```

---

## QUICK REFERENCE: Key Files to Know

1. **SPC Entry**: `scripts/smart_policy_chunks_canonic_phase_one.py`
2. **SPC Conversion**: `src/saaaaaa/processing/spc_ingestion/converter.py`
3. **SPC→Orchestrator**: `src/saaaaaa/utils/spc_adapter.py`
4. **Orchestrator Core**: `src/saaaaaa/core/orchestrator/core.py`
5. **Question Executor**: `src/saaaaaa/core/orchestrator/choreographer.py`
6. **Questionnaire**: `src/saaaaaa/core/orchestrator/questionnaire.py`
7. **Executor Registry**: `src/saaaaaa/core/orchestrator/class_registry.py`
8. **Argument Router**: `src/saaaaaa/core/orchestrator/arg_router.py`
9. **Chunk Router**: `src/saaaaaa/core/orchestrator/chunk_router.py`
10. **Causal Bridge**: `src/saaaaaa/analysis/spc_causal_bridge.py`

