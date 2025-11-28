# P02-EN: Phase 2 — Micro Questions (N2)

> **Status:** STABLE  
> **Version:** 1.0.0  
> **Last Updated:** 2025-11-27  
> **Classification:** CANONICAL  

---

## 1. Phase Definition

**Phase 2 (N2)** is the execution engine for the **Micro Questions** layer of the F.A.R.F.A.N. pipeline. It is responsible for the granular interrogation of the policy document using a deterministic, dimension-first approach.

*   **Node ID:** `N2`
*   **Name:** Micro Questions Execution
*   **Input:** `PreprocessedDocument` (from N1) + `MicroQuestionConfig` (from N0)
*   **Output:** `Phase2Result` (List of 300 `MicroQuestionRun` objects)
*   **Cardinality:** 1 Document → 300 Answers

---

## 2. Strict Deterministic Flow (The "Canonical Path")

Phase 2 enforces a unique, non-negotiable execution path to ensure determinism and structural integrity.

### 2.1. Prerequisite: The 60-Chunk Invariant
Phase 1 (N1) **MUST** produce a `PreprocessedDocument` containing exactly **60 Smart Policy Chunks (SPCs)**.
*   **Structure:** 10 Policy Areas (PA) × 6 Dimensions (DIM).
*   **Validation:** `P01_EXPECTED_CHUNK_COUNT = 60`.
*   **Metadata:** Each chunk is tagged with `policy_area_id` (PA01-PA10) and `dimension_id` (DIM01-DIM06).

### 2.2. Execution Ordering
Questions are executed in a strict **Dimension-First** order to ensure logical progression:
1.  **Dimension 1 (DIM01)**: All 10 Policy Areas (PA01-PA10).
2.  **Dimension 2 (DIM02)**: All 10 Policy Areas.
3.  ...
4.  **Dimension 6 (DIM06)**: All 10 Policy Areas.

**Sorting Key:** `(dimension_id, policy_area_id, question_id)`

### 2.3. Scoped Execution (The "Filter")
For each micro-question, the Orchestrator enforces **strict data scoping**:
1.  Identify the question's target `policy_area_id` and `dimension_id`.
2.  **Filter** the 60 chunks to find ONLY those matching the target PA and DIM.
3.  Create a **Scoped Document** containing only the filtered chunks.
4.  Pass this Scoped Document to the Executor.

> **Constraint:** An executor for `D1-Q1` (Dimension 1) **CANNOT** see chunks from Dimension 2. This isolation is enforced by the Orchestrator.

---

## 3. Signal Irrigation

Executors are "irrigated" with context-specific signals derived from the Canonical Questionnaire.

### 3.1. Mechanism
1.  **Injection:** `SignalRegistry` is injected into every Executor instance at instantiation.
2.  **Pull:** Inside `execute()`, the Executor calls `signal_registry.get_micro_answering_signals(question_id)`.
3.  **Extraction:** The Registry extracts patterns, expected elements, and indicators specific to that question from the loaded Questionnaire.

### 3.2. Signal Types
*   **Pattern Signals:** Regex/semantic patterns for evidence extraction.
*   **Validation Signals:** Rules for answer completeness.
*   **Indicator Signals:** Specific metrics to look for (e.g., "Budget", "Timeline").

---

## 4. Contracts

### 4.1. Input Contract
```python
class Phase2Input:
    document: PreprocessedDocument  # Must have 60 chunks with PA/DIM tags
    config: dict                    # Must contain "micro_questions" list (300 items)
```

### 4.2. Output Contract
```python
class MicroQuestionRun:
    question_id: str          # e.g., "Q001"
    base_slot: str            # e.g., "D1-Q1"
    metadata: dict            # PA, DIM, Cluster, Modality
    evidence: Evidence        # Extracted text + Confidence
    error: str | None         # Error message if failed
    duration_ms: float        # Execution time
```

---

## 5. Error Handling

*   **Circuit Breakers:** Per-slot (e.g., D1-Q1) failure counting. 3 consecutive failures open the circuit for that slot.
*   **Resource Limits:** CPU and Memory usage monitored per question.
*   **Fallbacks:** If a chunk is missing (rare), the executor returns empty evidence with a specific flag, preserving the pipeline flow.

---

## 6. Verification

To certify this phase:
1.  Verify `PreprocessedDocument` has 60 chunks.
2.  Verify `chunks` have `policy_area_id` and `dimension_id`.
3.  Verify execution log shows Dimension-ordered processing.
4.  Verify Executors receive only relevant chunks.
