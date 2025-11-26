# CALIBRATION MIGRATION CONTRACT
## FAKE → REAL Executor Migration for Mechanistic Policy Pipeline

**Version:** 1.0
**Date:** 2025-11-24
**Scope:** Executor migration and calibration recalibration

---

## 1. FORMAL SPECIFICATION COMPLIANCE

This migration operates under the formal specification:

**"A System-Layer Formalization for Method Calibration in Mechanistic Policy Pipelines"**

All implementations, modifications, and calibrations MUST conform to the following normative definitions:

### 1.1 Core Definitions (Non-Negotiable)

- **Computation Graph Γ**: (V, E, Σ, ξ, ψ) where:
  - V: method nodes
  - E: directed edges (data dependencies)
  - Σ: method signatures
  - ξ: execution contexts
  - ψ: evidential provenance

- **Calibration Subject**: I = (M, v, Γ, G, ctx)
  - M: method implementation
  - v: method version
  - Γ: computation graph
  - G: goal set
  - ctx: execution context

- **8-Layer Architecture**: @b, @chain, @u, @q, @d, @p, @C, @m
  - @b: Intrinsic/base layer (rubric-based foundation)
  - @chain: Integration chain (sequential dependencies)
  - @u: Unit layer (PDT coverage)
  - @q: Question context (D{n}-Q{m} appropriateness)
  - @d: Domain context (policy area relevance)
  - @p: Processing context (workflow compatibility)
  - @C: Congruence (cross-layer consistency)
  - @m: Meta layer (governance, transparency, cost)

- **Choquet 2-Additive Aggregation**: Fuses layers with linear weights and interaction terms
  ```
  C(λ₁,...,λ₈) = Σᵢ wᵢλᵢ + Σᵢ<ⱼ Iᵢⱼ(λᵢ ∧ λⱼ)
  ```
  Subject to constraints:
  - wᵢ ≥ 0, Iᵢⱼ ≥ 0
  - Σᵢ wᵢ + ½Σᵢ<ⱼ Iᵢⱼ = 1
  - Monotonicity: wᵢ + Σⱼ≠ᵢ Iᵢⱼ ≥ 0

### 1.2 Role Ontology Requirements

Each method classified by role with REQUIRED layer sets:

| Role          | Required Layers | Rationale |
|---------------|----------------|-----------|
| EXTRACTOR     | @b, @u, @q     | Context-dependent extraction |
| TRANSFORMER   | @b, @chain     | Sequential transformation |
| ANALYZER      | @b, @u, @q, @d | Domain-specific analysis |
| AGGREGATOR    | @b, @chain, @C | Cross-layer fusion |
| VALIDATOR     | @b, @C         | Consistency checking |
| EXECUTOR      | ALL 8 LAYERS   | Full pipeline orchestration |

### 1.3 Property-Based Validation

All calibrations MUST satisfy properties P1-P7:

- **P1 (Monotonicity)**: c(I₁) ≥ c(I₂) if I₁ dominates I₂
- **P2 (Decomposability)**: c({M₁,M₂}) = c(M₁) ⊕ c(M₂)
- **P3 (Context Sensitivity)**: c(M,ctx₁) ≠ c(M,ctx₂) when contexts differ
- **P4 (Version Invariance)**: c(M,v₁) = c(M,v₂) if implementations equivalent
- **P5 (Calibration Stability)**: Small input changes → small score changes
- **P6 (Layer Independence)**: @q ⊥ @d | @b (conditional independence)
- **P7 (Audit Trail)**: Complete provenance for all calibration inputs

---

## 2. NON-DESTRUCTIVE PRINCIPLES

### 2.1 Existing Calibration Protection

**INVIOLABLE RULE**: The existing intrinsic/base layer (@b) and derived calibrations for real, non-executor methods are **PRESUMED VALID** unless:

1. Direct contradiction with formal specification proven
2. Hard evidence of calculation error provided
3. Explicit instruction to recalibrate given

**Protected Artifacts:**
- `config/intrinsic_calibration.json` (1,470 methods, @b scores)
- `config/intrinsic_calibration_rubric.json` (rubric specification)
- All non-executor method scores for:
  - @b (intrinsic foundation)
  - @chain (where applicable)
  - @u (where applicable)
  - @q, @d, @p (where applicable)
  - @C (cross-layer consistency)

### 2.2 Parameterization System Separation

**STRICT BOUNDARY**: The parameterization system is a **SEPARATE, EVIDENCE-BASED ARTIFACT**:

- **File**: `CANONICAL_METHOD_PARAMETERIZATION_SPEC.json` (416 methods, 5,094 parameters)
- **Purpose**: Define method parameter ranges, defaults, epistemic effects
- **Status**: INDEPENDENT from calibration
- **Rule**: DO NOT merge, overwrite, or casually modify

Parameterization defines **WHAT** can be configured. Calibration defines **HOW WELL** methods perform.

### 2.3 Migration Scope Limitation

**TARGETED RECALIBRATION ONLY**: This migration targets:

1. **Executor methods**: 30 D{n}-Q{m} executors transitioning from FAKE to REAL
2. **Contaminated methods**: Methods whose rubric inputs depended on fake executor behavior
3. **Executor calibration files**: `config/layer_calibrations/SCORE_Q/*.json`

**OUT OF SCOPE**:
- Recalibration of real, non-executor analyzers, validators, transformers
- Modification of intrinsic_calibration.json entries for non-executors
- Changes to parameterization specifications
- Alteration of formal specification definitions

---

## 3. FAKE → REAL MIGRATION DEFINITION

### 3.1 What is "FAKE"?

**FAKE executors** are the OLD implementation in:
- **File**: `src/saaaaaa/core/orchestrator/executors.py` (3,929 lines)
- **Architecture**: Hardcoded `execute()` methods, manual method invocation
- **Classes**: 30 executors inheriting from `BaseExecutor`:
  - `D1_Q1_QuantitativeBaselineExtractor`
  - `D1_Q2_ProblemDimensioningAnalyzer`
  - ... (all 30 D{n}_Q{m}_* classes)

**Characteristics:**
- Explicit `execute(self, context: Dict) -> Dict` methods
- Direct method calls via `self._execute_method(class_name, method_name, ...)`
- Hardcoded execution order
- No contract validation
- No evidence assembly rules
- Snapshot preserved in `executors_snapshot/executors.py`

### 3.2 What is "REAL"?

**REAL executors** are the NEW implementation in:
- **File**: `src/saaaaaa/core/orchestrator/executors_contract.py` (216 lines)
- **Architecture**: Contract-driven routing through `MethodExecutor`
- **Classes**: 30 executors inheriting from `BaseExecutorWithContract`:
  - `D1Q1_Executor_Contract` (aliased as `D1Q1_Executor`)
  - `D1Q2_Executor_Contract` (aliased as `D1Q2_Executor`)
  - ... (all 30 D{n}Q{m}_Executor_Contract classes)

**Characteristics:**
- Minimal class definition (just `get_base_slot()` method)
- Execution routed through `BaseExecutorWithContract.execute()`
- Contract-based method sequencing from JSON files
- Schema validation (`config/executor_contract.schema.json`)
- Evidence assembly via `EvidenceAssembler`
- Evidence validation via `EvidenceValidator`
- Failure contracts and abort conditions
- Full audit trail and provenance

**Active Import**: `core.py:55` → `from . import executors_contract as executors`

### 3.3 Migration Status

**COMPLETED**:
- ✅ Executor contract classes implemented
- ✅ `BaseExecutorWithContract` routing implemented
- ✅ Contract JSON files for all 30 executors
- ✅ Evidence assembler and validator implemented
- ✅ Core orchestrator import switched to `executors_contract`
- ✅ Old implementation preserved in `executors_snapshot/`

**PENDING** (This Migration):
- ⏳ Classification of all methods into REAL_NON_EXEC, FAKE_EXEC, REAL_EXEC
- ⏳ Invalidation of calibration scores for FAKE_EXEC
- ⏳ Generation of calibration scores for REAL_EXEC (all 8 layers)
- ⏳ Verification that REAL_NON_EXEC calibrations remain untouched
- ⏳ Property-based validation of new calibrations (P1-P7)
- ⏳ Certificate generation and audit trail

---

## 4. COMPLIANCE OBLIGATIONS

All code changes, calibration updates, and documentation MUST:

1. **Respect the formal specification** as normative truth
2. **Preserve existing calibrations** for REAL_NON_EXEC methods
3. **Maintain separation** between calibration and parameterization
4. **Target executors only** (plus contaminated dependencies)
5. **Provide complete audit trails** for all calibration changes
6. **Validate against properties P1-P7** before committing
7. **Generate calibration certificates** for transparency

---

## 5. MIGRATION WORKFLOW

### Phase 1: Classification (JOBFRONT 2)
- Inspect codebase to identify REAL_NON_EXEC, FAKE_EXEC, REAL_EXEC
- Generate machine-readable classification artifact
- Cross-reference with `intrinsic_calibration.json`

### Phase 2: Invalidation
- Mark FAKE_EXEC calibrations as invalid
- Document why each score is discarded
- Preserve original values for audit trail

### Phase 3: Recalibration
- Apply rubric to REAL_EXEC executors (all 8 layers)
- Use existing rubric for @b layer
- Compute contextual layers (@u, @q, @d, @p, @C, @chain, @m)
- Apply Choquet aggregation with validated weights

### Phase 4: Validation
- Run property-based tests (P1-P7)
- Verify layer requirements for EXECUTOR role
- Check Choquet constraint satisfaction
- Generate calibration certificates

### Phase 5: Integration
- Update `config/layer_calibrations/SCORE_Q/*.json`
- Preserve `intrinsic_calibration.json` REAL_NON_EXEC entries
- Document changes in migration report
- Commit with descriptive messages

---

## 6. ARTIFACT REQUIREMENTS

Each migration phase MUST produce:

1. **Classification Artifact** (JSON): REAL_NON_EXEC, FAKE_EXEC, REAL_EXEC lists
2. **Invalidation Report** (Markdown): Why FAKE_EXEC scores discarded
3. **Recalibration Report** (Markdown): New REAL_EXEC scores with justifications
4. **Property Validation Report** (Markdown): P1-P7 test results
5. **Calibration Certificates** (JSON): Provenance for all score changes
6. **Migration Summary** (Markdown): Complete audit trail

---

## 7. SUCCESS CRITERIA

Migration is complete when:

1. ✅ All 30 REAL_EXEC executors have 8-layer calibration scores
2. ✅ All FAKE_EXEC scores removed from active calibration files
3. ✅ All REAL_NON_EXEC scores remain unchanged (verified by hash)
4. ✅ All property tests (P1-P7) pass
5. ✅ All role requirements satisfied (EXECUTOR → all 8 layers)
6. ✅ All Choquet constraints satisfied
7. ✅ All calibration certificates generated
8. ✅ All migration artifacts committed to repository

---

**REMEMBER**: This is a formal, specification-driven migration. No shortcuts, no approximations, no "good enough" solutions. The formal specification is law; all implementations must prove conformance.

---

**Contract Acknowledged By:**
Claude Code Agent (Senior Python Engineer & Calibration Architect)
**Date:** 2025-11-24
**Branch:** `claude/fake-real-executor-migration-01DkQrq2dtSN3scUvzNVKqGy`
