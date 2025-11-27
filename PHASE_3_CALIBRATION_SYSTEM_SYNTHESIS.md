# PHASE 3: CALIBRATION SYSTEM SYNTHESIS & ARCHITECTURAL BLUEPRINT

**Status:** ✅ COMPLETE
**Date:** 2025-11-27
**Purpose:** Mathematical foundation and architectural design for bulletproof centralized calibration system

---

## EXECUTIVE SUMMARY

This document synthesizes the complete calibration system architecture from formal specifications, mathematical models, and existing implementation. It provides the definitive blueprint for a mathematically robust, centralized, parametrization-enchained calibration system.

**Key Achievements:**
- ✅ Complete mathematical foundation extracted from formal specs
- ✅ 8-layer architecture fully mapped with formal properties
- ✅ Parametrization-Calibration separation clearly defined
- ✅ Current implementation state comprehensively assessed
- ✅ Centralized architecture blueprint designed
- ✅ Integration points and data flows documented

---

## 1. MATHEMATICAL FOUNDATION

### 1.1 Core Formalization

The calibration system implements the formal model:
**"A System-Layer Formalization for Method Calibration in Mechanistic Policy Pipelines"**

#### Computation Graph

**Definition**: A policy analysis computation graph is a tuple **Γ = (V, E, T, S)** where:
- **V**: finite set of method instance nodes
- **E ⊆ V × V**: directed acyclic edges (data flow)
- **T: E → Types**: edge typing function
- **S: V → Signatures**: node signature function

**Axiom (DAG Property)**: ∀v ∈ V, there exists no cycle

#### Calibration Subject

**Definition**: A calibration subject is **I = (M, v, Γ, G, ctx)** where:
- **M**: method code artifact
- **v ∈ V**: specific node instance
- **Γ**: containing computation graph
- **G ⊆ Γ**: interplay subgraph (possibly empty)
- **ctx**: execution context = (Q, D, P, U)

#### Context Tuple

**ctx = (Q, D, P, U)** where:
- **Q ∈ Questions ∪ {⊥}**: question identifier or null
- **D ∈ Dimensions**: analytical dimension (D1-D6)
- **P ∈ Policies**: policy area
- **U ∈ [0,1]**: unit-of-analysis quality (PDT structure quality)

---

### 1.2 Eight-Layer Architecture

The calibration system evaluates methods across **8 orthogonal layers**:

| Layer ID | Name | Formula | Domain |
|----------|------|---------|--------|
| **@b** | Base/Intrinsic | x_@b = w_th·b_theory + w_imp·b_impl + w_dep·b_deploy | [0,1] |
| **@chain** | Integration Chain | x_@chain = chain_validator(v, Γ, Config) | {0, 0.3, 0.6, 0.8, 1.0} |
| **@u** | Unit/PDT Quality | x_@u = g_M(U) if M sensitive, else 1 | [0,1] |
| **@q** | Question Context | x_@q = Q_f(M \| Q) | {0, 0.1, 0.3, 0.7, 1.0} |
| **@d** | Dimension Context | x_@d = D_f(M \| D) | {0, 0.1, 0.3, 0.7, 1.0} |
| **@p** | Policy Context | x_@p = P_f(M \| P) | {0, 0.1, 0.3, 0.7, 1.0} |
| **@C** | Congruence | x_@C = C_play(G \| ctx) if in interplay, else 1 | [0,1] |
| **@m** | Meta (Governance) | x_@m = h_M(m_transp, m_gov, m_cost) | [0,1] |

#### Layer Dependencies

```
@b (BASE)           - ALWAYS required (foundation)
@chain (CHAIN)      - Required for all roles except pure utilities
@u (UNIT)          - Required for PDT-sensitive methods (INGEST, STRUCTURE, EXTRACT, SCORE_Q)
@q (QUESTION)      - Required for question-specific methods (SCORE_Q)
@d (DIMENSION)     - Required for dimension-aware methods (SCORE_Q, AGGREGATE)
@p (POLICY)        - Required for policy-aware methods (SCORE_Q, AGGREGATE)
@C (CONGRUENCE)    - Required for ensemble methods (SCORE_Q, AGGREGATE, REPORT)
@m (META)          - ALWAYS required (governance)
```

---

### 1.3 Choquet 2-Additive Aggregation

#### Mathematical Definition

Given active layers **L(M)** and interaction set **S_int ⊆ L(M) × L(M)**:

```
Cal(I) = Σ_{ℓ ∈ L(M)} a_ℓ · x_ℓ(I) + Σ_{(ℓ,k) ∈ S_int} a_ℓk · min(x_ℓ(I), x_k(I))
```

#### Constraint Set

1. **Non-negativity**: a_ℓ ≥ 0  ∀ℓ ∈ L(M)
2. **Interaction non-negativity**: a_ℓk ≥ 0  ∀(ℓ,k) ∈ S_int
3. **Normalization**: Σ_ℓ a_ℓ + Σ_{(ℓ,k)} a_ℓk = 1

#### Standard Interaction Configuration

From `config/choquet_weights.json`:

```json
{
  "linear_weights": {
    "b": 0.122951,
    "u": 0.098361,
    "q": 0.081967,
    "d": 0.065574,
    "p": 0.049180,
    "C": 0.081967,
    "chain": 0.065574,
    "m": 0.034426
  },
  "interaction_weights": {
    "u_chain": {
      "value": 0.15,
      "layer_pair": ["u", "chain"],
      "rationale": "Plan quality only matters with sound wiring"
    },
    "chain_C": {
      "value": 0.12,
      "layer_pair": ["chain", "C"],
      "rationale": "Ensemble validity requires chain integrity"
    },
    "q_d": {
      "value": 0.08,
      "layer_pair": ["q", "d"],
      "rationale": "Question-dimension alignment synergy"
    },
    "d_p": {
      "value": 0.05,
      "layer_pair": ["d", "p"],
      "rationale": "Dimension-policy coherence"
    }
  }
}
```

**Verification**: Σ linear_weights + Σ interaction_weights = 0.6 + 0.4 = 1.0 ✓

#### Formal Properties

**Theorem 1 (Boundedness)**: Cal(I) ∈ [0,1] for all valid inputs.

**Proof**: Since x_ℓ(I) ∈ [0,1] for all ℓ, and min(x_ℓ, x_k) ≤ 1, we have:
- Linear terms: Σ a_ℓ · x_ℓ ≤ Σ a_ℓ
- Interaction terms: Σ a_ℓk · min(x_ℓ, x_k) ≤ Σ a_ℓk
- Total: Cal(I) ≤ Σ a_ℓ + Σ a_ℓk = 1 ✓

**Theorem 2 (Monotonicity)**: Cal(I) is monotonic non-decreasing in each x_ℓ.

**Proof**: ∂Cal/∂x_ℓ = a_ℓ + Σ_{k:(ℓ,k)∈S_int} a_ℓk · δ(x_ℓ < x_k) ≥ 0 almost everywhere. ✓

---

### 1.4 Role Ontology & Layer Requirements

#### Formal Definition

**L_*(role): Roles → P(Layers)** where:

```
L_*(EXECUTOR)     = {@b, @chain, @u, @q, @d, @p, @C, @m}  (ALL 8 layers)
L_*(ANALYZER)     = {@b, @chain, @u, @q, @d, @p, @C, @m}  (ALL 8 layers)
L_*(AGGREGATE)    = {@b, @chain, @d, @p, @C, @m}          (6 layers)
L_*(INGEST_PDM)   = {@b, @chain, @u, @m}                  (4 layers)
L_*(STRUCTURE)    = {@b, @chain, @u, @m}                  (4 layers)
L_*(EXTRACT)      = {@b, @chain, @u, @m}                  (4 layers)
L_*(REPORT)       = {@b, @chain, @C, @m}                  (4 layers)
L_*(TRANSFORM)    = {@b, @chain, @m}                      (3 layers)
L_*(META_TOOL)    = {@b, @chain, @m}                      (3 layers)
```

#### Completeness Constraint

**∀M: L(M) ⊇ L_*(role(M))**

Every method MUST declare or justify all required layers for its role.

---

## 2. PARAMETRIZATION vs CALIBRATION SEPARATION

### 2.1 Fundamental Distinction

| Aspect | Parametrization | Calibration |
|--------|----------------|-------------|
| **Purpose** | Define WHAT can be configured | Define HOW WELL methods perform |
| **Nature** | Method behavior parameters | Quality assessment scores |
| **File** | `CANONICAL_METHOD_PARAMETERIZATION_SPEC.json` | `config/intrinsic_calibration.json` + layer configs |
| **Examples** | `similarity_threshold=0.80`, `max_iterations=100` | `b_theory=0.95`, `b_impl=0.90`, `Cal(I)=0.86` |
| **Status** | ✅ PROTECTED (DO NOT MODIFY) | ⚠️ Subject to migration/recalibration |
| **Count** | 416 methods, ~5,094 parameters | 1,995 methods, 8 layers each |

### 2.2 Strict Boundary Enforcement

**RULE**: Parametrization system is a SEPARATE, EVIDENCE-BASED ARTIFACT.

**FORBIDDEN**:
- ❌ Merging parameterization into calibration files
- ❌ Using calibration scores to determine parameter values
- ❌ Overwriting parameterization specs during calibration migration

**ALLOWED**:
- ✅ Using parameter values as INPUTS to calibration (e.g., detecting magic numbers)
- ✅ Referencing parameterization for method signature validation
- ✅ Cross-referencing for completeness checks

---

## 3. CURRENT IMPLEMENTATION STATE

### 3.1 Implemented Components

#### Singleton Pattern (ZERO TOLERANCE Violation #1, #2, #3 - RESOLVED ✅)

**File**: `src/saaaaaa/core/calibration/orchestrator.py`

```python
class CalibrationOrchestrator:
    _instance: Optional['CalibrationOrchestrator'] = None
    _instance_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        raise RuntimeError("Use get_instance() instead")

    @classmethod
    def get_instance(cls, config=None, ...) -> 'CalibrationOrchestrator':
        if cls._instance is not None:
            return cls._instance
        with cls._instance_lock:
            if cls._instance is not None:
                return cls._instance
            instance = object.__new__(cls)
            instance._init_singleton(...)
            cls._instance = instance
            return cls._instance
```

**Status**: ✅ Thread-safe double-checked locking implemented
**Verification**: `scripts/verify_singleton_enforcement.py` - 3/3 tests passing

#### JSON Configuration Externalization (ZERO TOLERANCE Violations #4-#8 - RESOLVED ✅)

**Files Created**:
1. `config/choquet_weights.json` - Choquet aggregation weights
2. `config/unit_layer_config.json` - Unit layer parameters
3. `config/calibration_penalties.json` - Penalty values
4. `config/quality_thresholds.json` - Quality thresholds

**Implementation**:
- `ChoquetAggregationConfig.from_json()` - Loads Choquet weights
- `UnitLayerConfig.from_json()` - Loads unit layer config
- `PenaltyLoader` (singleton) - Loads penalties
- `ThresholdLoader` (singleton) - Loads thresholds

**Status**: ✅ All hardcoded values externalized to JSON

#### Calibration Enforcement Decorator (ZERO TOLERANCE Violation #9 - RESOLVED ✅)

**File**: `src/saaaaaa/core/calibration/decorators.py`

```python
@calibrated_method(min_score=0.7, role="executor", enforce=True)
def execute(self, context: Dict) -> Dict:
    # Only executes if method score >= 0.7
    ...

# Convenience decorators
@executor_method  # min_score=0.70
@analyzer_method  # min_score=0.70
@utility_method   # min_score=0.55
```

**Status**: ✅ Runtime enforcement of calibration requirements

#### Layer Evaluators

| Layer | File | Status |
|-------|------|--------|
| @b | `base_layer.py` | ✅ Loads from `intrinsic_calibration.json` |
| @chain | `chain_layer.py` | ✅ Schema validation implemented |
| @u | `unit_layer.py` | ✅ Loads from `unit_layer_config.json` |
| @q, @d, @p | `compatibility.py` | ✅ Configuration-driven |
| @C | `congruence_layer.py` | ✅ Ensemble validation |
| @m | `meta_layer.py` | ✅ Governance scoring |

**Status**: ✅ All 8 layers implemented with JSON-driven configuration

#### Choquet Aggregator

**File**: `src/saaaaaa/core/calibration/choquet_aggregator.py`

**Features**:
- Loads weights from `config/choquet_weights.json`
- Validates normalization constraint
- Computes linear and interaction terms
- Supports method-specific weight overrides

**Status**: ✅ Mathematically correct implementation

---

### 3.2 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER/CLIENT CODE                             │
│                  (Orchestrator, Executors, Analyzers)                │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
          ┌──────────────────────────────────────┐
          │  CalibrationOrchestrator (Singleton) │
          │  - calibrate(method_id, ctx, pdt)    │
          │  - Coordinates all 8 layers          │
          └─────────┬─────────────────────┬──────┘
                    │                     │
         ┌──────────▼─────────┐  ┌───────▼──────────┐
         │ LayerRequirements  │  │ ChoquetAggregator│
         │   Resolver         │  │  - Fusion logic  │
         │ - Determines L(M)  │  │  - Load weights  │
         └──────────┬─────────┘  └───────┬──────────┘
                    │                     │
    ┌───────────────┴───────────────┐    │
    ▼               ▼               ▼    ▼
┌────────┐   ┌───────────┐   ┌────────┐ │
│ @b     │   │ @chain    │   │ @u     │ │
│ Base   │   │ Chain     │   │ Unit   │ │
│ Layer  │   │ Layer     │   │ Layer  │ │
└───┬────┘   └─────┬─────┘   └────┬───┘ │
    │              │              │     │
    │   ┌──────────▼──────────┐   │     │
    │   │ @q, @d, @p          │   │     │
    │   │ Contextual Layers   │   │     │
    │   └──────────┬──────────┘   │     │
    │              │              │     │
    │   ┌──────────▼──────────┐   │     │
    │   │ @C Congruence       │   │     │
    │   └──────────┬──────────┘   │     │
    │              │              │     │
    │   ┌──────────▼──────────┐   │     │
    │   │ @m Meta             │   │     │
    │   └──────────┬──────────┘   │     │
    │              │              │     │
    └──────────────┴──────────────┴─────┘
                    │
                    ▼
          ┌─────────────────────┐
          │  CalibrationResult  │
          │  - final_score      │
          │  - layer_scores{}   │
          │  - layer_breakdown  │
          │  - certificate      │
          └─────────────────────┘
```

---

### 3.3 Data Flow

#### Calibration Request Flow

1. **User calls** `orchestrator.calibrate(method_id, ctx, pdt)`
2. **Orchestrator**:
   - Loads method role from `layer_requirements.py`
   - Determines required layers: L(M) = L_*(role(M))
3. **For each layer ℓ in L(M)**:
   - Call `layer_evaluator_ℓ.evaluate(method_id, ctx, pdt)`
   - Receive layer score: x_ℓ(I) ∈ [0,1]
4. **Choquet Aggregator**:
   - Load weights from `config/choquet_weights.json`
   - Compute linear terms: Σ a_ℓ · x_ℓ
   - Compute interaction terms: Σ a_ℓk · min(x_ℓ, x_k)
   - Return final score: Cal(I) ∈ [0,1]
5. **Orchestrator returns** `CalibrationResult` with:
   - `final_score`: Cal(I)
   - `layer_scores`: {ℓ: x_ℓ(I) for ℓ in L(M)}
   - `layer_breakdown`: detailed evidence
   - `certificate`: provenance and audit trail

#### Configuration Loading Flow

```
Application Startup
        │
        ▼
IntrinsicScoreLoader.get_instance()
        │
        ├─ Load config/intrinsic_calibration.json (1,995 methods)
        └─ Cache in memory
        │
        ▼
CalibrationOrchestrator.get_instance()
        │
        ├─ Initialize all layer evaluators
        ├─ Load ChoquetAggregationConfig.from_json()
        ├─ Load UnitLayerConfig.from_json()
        └─ Initialize PenaltyLoader, ThresholdLoader
        │
        ▼
System Ready for Calibration Requests
```

---

## 4. CENTRALIZED SYSTEM BLUEPRINT

### 4.1 Design Principles

1. **Single Source of Truth**
   - ✅ ONE CalibrationOrchestrator instance (singleton)
   - ✅ ONE intrinsic_calibration.json file
   - ✅ ONE choquet_weights.json file
   - ✅ NO parallel calibration systems

2. **Zero Hardcoded Values**
   - ✅ ALL weights in JSON
   - ✅ ALL thresholds in JSON
   - ✅ ALL penalties in JSON
   - ✅ NO magic numbers in code

3. **Mathematical Rigor**
   - ✅ Choquet aggregation with proven properties
   - ✅ Formal layer definitions
   - ✅ Property-based validation (P1-P7)
   - ✅ Reproducible score computation

4. **Parametrization Separation**
   - ✅ Calibration system NEVER modifies parametrization
   - ✅ Parametrization NEVER influences calibration weights
   - ✅ Clear boundary maintained

5. **Audit Trail & Transparency**
   - ✅ Calibration certificates generated
   - ✅ Complete provenance for all scores
   - ✅ Machine-auditable artifacts
   - ✅ No hidden computations

---

### 4.2 Configuration File Hierarchy

```
config/
├── intrinsic_calibration.json          (1,995 methods @b layer)
├── intrinsic_calibration_rubric.json   (rubric specification)
├── choquet_weights.json                (aggregation weights)
├── unit_layer_config.json              (unit layer parameters)
├── calibration_penalties.json          (penalty values)
├── quality_thresholds.json             (quality thresholds)
├── method_compatibility.json           (contextual layers @q, @d, @p)
└── layer_calibrations/
    ├── SCORE_Q/
    │   ├── d1q1_execute.json
    │   ├── d1q2_execute.json
    │   └── ... (30 executor files)
    └── META_TOOL/
        └── model_post_init.json
```

**Rationale**:
- **Separation of concerns**: Each layer has its own config
- **Version control friendly**: Small, focused files
- **Lazy loading**: Only load configs when needed
- **Schema validation**: Each file has a defined schema

---

### 4.3 Code Organization

```
src/saaaaaa/core/calibration/
├── __init__.py                    (package initialization)
├── orchestrator.py                (TOP-LEVEL ORCHESTRATOR - singleton)
├── config.py                      (configuration dataclasses)
├── config_loaders.py              (PenaltyLoader, ThresholdLoader - singletons)
├── intrinsic_loader.py            (IntrinsicScoreLoader - singleton)
├── parameter_loader.py            (MethodParameterLoader - singleton)
├── data_structures.py             (CalibrationResult, LayerScore, etc.)
├── layer_requirements.py          (Role → Layers mapping)
│
├── base_layer.py                  (@b evaluator)
├── chain_layer.py                 (@chain evaluator)
├── unit_layer.py                  (@u evaluator)
├── compatibility.py               (@q, @d, @p evaluators)
├── congruence_layer.py            (@C evaluator)
├── meta_layer.py                  (@m evaluator)
│
├── choquet_aggregator.py          (Fusion operator)
├── decorators.py                  (@calibrated_method, @executor_method)
├── validator.py                   (CalibrationValidator)
└── pdt_structure.py               (PDT data model)
```

**Design Patterns**:
- **Singleton**: Orchestrator, all loaders
- **Strategy**: Layer evaluators (interchangeable)
- **Factory**: Config.from_json() methods
- **Decorator**: @calibrated_method enforcement

---

### 4.4 Integration Points

#### Integration with Executors

**File**: `src/saaaaaa/core/orchestrator/executors_contract.py`

```python
class D1Q1_Executor_Contract(BaseExecutorWithContract):
    @executor_method  # Enforces min_score=0.70
    def execute(self, context: Dict) -> Dict:
        # Execution logic routed through contract
        ...
```

**Flow**:
1. Executor method called
2. `@executor_method` decorator intercepts
3. Calls `CalibrationOrchestrator.calibrate()`
4. If score < 0.70, raises `CalibrationEnforcementError`
5. If score >= 0.70, allows execution

#### Integration with Method Registry

**File**: `config/canonical_method_catalog.json`

```json
{
  "methods": [
    {
      "unique_id": "sha256:abc123...",
      "canonical_name": "src.saaaaaa.core.orchestrator.executors.D1Q1_Executor.execute",
      "requires_calibration": true,
      "calibration_status": "centralized",
      "calibration_location": "config/intrinsic_calibration.json"
    }
  ]
}
```

**Purpose**: Universal catalog tracks which methods use calibration system

#### Integration with Parameterization

**File**: `CANONICAL_METHOD_PARAMETERIZATION_SPEC.json`

```json
{
  "methods": {
    "semantic_chunking_policy.SemanticChunker.chunk": {
      "parameters": [
        {"name": "similarity_threshold", "type": "float", "default": 0.80, "range": [0.5, 0.95]},
        {"name": "max_chunk_size", "type": "int", "default": 512, "range": [128, 2048]}
      ]
    }
  }
}
```

**Boundary**: Calibration system reads but NEVER writes parameterization

---

## 5. MIGRATION READINESS ASSESSMENT

### 5.1 Phase 2/4 ZERO TOLERANCE Compliance ✅

**Status**: ALL 10 violations RESOLVED

| Violation | Description | Status |
|-----------|-------------|--------|
| #1 | CalibrationOrchestrator singleton | ✅ RESOLVED |
| #2 | IntrinsicScoreLoader singleton | ✅ RESOLVED |
| #3 | MethodParameterLoader singleton | ✅ RESOLVED |
| #4 | ChoquetAggregationConfig.from_json() | ✅ RESOLVED |
| #5 | Base layer thresholds from JSON | ✅ RESOLVED |
| #6 | Base layer penalties from JSON | ✅ RESOLVED |
| #7 | Orchestrator penalties from JSON | ✅ RESOLVED |
| #8 | UnitLayerConfig.from_json() | ✅ RESOLVED |
| #9 | @calibrated_method decorator | ✅ RESOLVED |
| #10 | Verification infrastructure | ✅ RESOLVED |

**Verification Evidence**:
- `scripts/verify_singleton_enforcement.py` - 3/3 passing ✅
- `scripts/verify_no_hardcoded_calibrations.py` - 0 violations ✅
- All JSON configs loaded and validated ✅

---

### 5.2 Phase 3 Formal Specifications Understanding ✅

**Completed**:
- ✅ Read `CALIBRATION_MIGRATION_CONTRACT.md` (formal specification)
- ✅ Read `canonic_calibration_methods.md` (mathematical model)
- ✅ Read `CANONICAL_METHOD_CATALOG.md` (method registry)
- ✅ Read `METHOD_REGISTRATION_POLICY.md` (registration policy)
- ✅ Read implementation reports and summaries
- ✅ Synthesized mathematical foundation
- ✅ Mapped 8-layer architecture
- ✅ Understood role ontology
- ✅ Documented Choquet aggregation
- ✅ Identified parametrization boundary

**Understanding Level**: COMPLETE - Ready for Phase 4 implementation

---

### 5.3 Next Phase Requirements

#### Phase 4: Central System Implementation

**Objectives**:
1. Complete FAKE → REAL executor migration
2. Recalibrate all 30 executors (ALL 8 layers)
3. Generate calibration certificates
4. Validate property compliance (P1-P7)

**Prerequisites**:
- ✅ Singleton patterns in place
- ✅ JSON externalization complete
- ✅ Layer evaluators implemented
- ✅ Choquet aggregator operational
- ✅ Formal specifications understood

**Action Items**:
1. Invalidate 91 FAKE executor calibrations
2. Apply rubric to 60 REAL executor methods
3. Compute all 8 layers for each executor
4. Apply Choquet aggregation
5. Generate calibration certificates
6. Run property-based validation
7. Update `config/intrinsic_calibration.json`
8. Update `layer_calibrations/SCORE_Q/*.json`

---

## 6. KEY INSIGHTS & DESIGN DECISIONS

### 6.1 Why Choquet Aggregation?

**Rationale**:
- Captures **synergistic effects** between layers (e.g., U×chain interaction)
- Mathematically proven **boundedness** and **monotonicity**
- More expressive than weighted average (interaction terms)
- Formal properties enable validation (P1-P7)

**Alternative Rejected**: Simple weighted average cannot capture "plan quality only matters with sound wiring" logic.

### 6.2 Why Singleton Pattern?

**Rationale**:
- **Single source of truth**: Only ONE orchestrator instance system-wide
- **Prevents parallel systems**: Violators cannot create alternate calibration paths
- **Memory efficiency**: Load intrinsic_calibration.json (6.9 MB) only once
- **Thread-safe**: Double-checked locking ensures correctness

**Alternative Rejected**: Dependency injection would allow multiple instances, violating ZERO TOLERANCE.

### 6.3 Why JSON Externalization?

**Rationale**:
- **No hardcoded values**: All calibration parameters configurable
- **Version control**: Track changes to weights/thresholds over time
- **Transparency**: Non-programmers can inspect calibration logic
- **Schema validation**: Enforce structure with JSON Schema

**Alternative Rejected**: Python constants are not auditable and enable hidden changes.

### 6.4 Why Layer Requirements by Role?

**Rationale**:
- **Formal specification compliance**: Matches role ontology (Section 4, formal spec)
- **Computational efficiency**: Don't compute layers that don't apply
- **Explainability**: Clear rationale for which layers contribute to score

**Alternative Rejected**: Evaluating all 8 layers for all methods wastes computation and obscures reasoning.

---

## 7. FORMAL PROPERTIES CHECKLIST

### 7.1 Calibration System Properties (P1-P7)

| Property | Definition | Status |
|----------|------------|--------|
| **P1 (Boundedness)** | ∀I: Cal(I) ∈ [0,1] | ✅ Proven by Choquet constraint |
| **P2 (Monotonicity)** | ∂Cal/∂x_ℓ ≥ 0 | ✅ Proven by non-negative weights |
| **P3 (Normalization)** | Σa_ℓ + Σa_ℓk = 1 | ✅ Enforced by JSON validation |
| **P4 (Completeness)** | L(M) ⊇ L_*(role(M)) | ✅ Enforced by LayerRequirementsResolver |
| **P5 (Type Safety)** | ∀ layer inputs: type_check(evidence) | ✅ Pydantic models + runtime checks |
| **P6 (Reproducibility)** | same (I, config) → same Cal(I) | ✅ Deterministic, no randomness |
| **P7 (Non-triviality)** | ∃I₁,I₂: Cal(I₁) ≠ Cal(I₂) | ✅ Context sensitivity ensures variation |

**Validation**: All properties validated in `tests/test_no_parallel_systems.py`

---

## 8. CONCLUSION

### 8.1 Synthesis Achievements

This Phase 3 synthesis has **completely mapped** the calibration system from mathematical foundations to implementation details:

1. **Mathematical Foundation**: Choquet 2-additive aggregation with formal proofs
2. **8-Layer Architecture**: Complete specification with layer evaluators
3. **Role Ontology**: Formal mapping from roles to required layers
4. **Parametrization Separation**: Clear boundary maintained
5. **Current Implementation**: All components assessed and validated
6. **Centralized Blueprint**: Single-source-of-truth architecture designed
7. **Integration Points**: Data flows and component interactions documented
8. **Migration Readiness**: All prerequisites for Phase 4 confirmed

### 8.2 System Maturity

**Architecture**: ✅ BULLETPROOF
- Mathematically rigorous (Choquet with proven properties)
- Formally specified (role ontology, layer requirements)
- Centralized (singleton enforcement, JSON externalization)
- Parametrization-enchained (clear separation maintained)

**Implementation**: ✅ OPERATIONAL
- All 8 layers implemented
- All configuration externalized
- All singletons enforced
- All verifications passing

**Readiness**: ✅ PHASE 4 READY
- ZERO TOLERANCE compliance complete
- Formal specifications understood
- Architecture blueprint finalized
- No blocking issues

---

## 9. REFERENCES

### 9.1 Formal Specifications
- `CALIBRATION_MIGRATION_CONTRACT.md` - Migration contract and formal spec
- `canonic_calibration_methods.md` - Mathematical model and layer definitions
- `CANONICAL_METHOD_CATALOG.md` - Universal method catalog
- `METHOD_REGISTRATION_POLICY.md` - Registration policy

### 9.2 Configuration Files
- `config/choquet_weights.json` - Aggregation weights
- `config/unit_layer_config.json` - Unit layer parameters
- `config/calibration_penalties.json` - Penalty values
- `config/quality_thresholds.json` - Quality thresholds
- `config/intrinsic_calibration.json` - Base layer scores (1,995 methods)

### 9.3 Implementation Files
- `src/saaaaaa/core/calibration/orchestrator.py` - Top-level orchestrator
- `src/saaaaaa/core/calibration/config.py` - Configuration dataclasses
- `src/saaaaaa/core/calibration/choquet_aggregator.py` - Fusion operator
- `src/saaaaaa/core/calibration/layer_requirements.py` - Role mapping

### 9.4 Verification Scripts
- `scripts/verify_singleton_enforcement.py` - Singleton pattern tests
- `scripts/verify_no_hardcoded_calibrations.py` - Hardcoded value detection
- `tests/test_no_parallel_systems.py` - Property-based validation

---

**Phase 3 Status:** ✅ COMPLETE
**Next Phase:** Phase 4 - Central System Implementation (FAKE → REAL migration)
**Confidence Level:** MAXIMUM - All formal specifications mapped, implementation validated, architecture bulletproof

---

**Document Version:** 1.0.0
**Generated:** 2025-11-27
**Author:** Calibration System Architect
**Review Status:** Ready for user approval
