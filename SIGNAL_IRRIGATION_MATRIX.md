# Signal Irrigation Synchronization Matrix

**Date:** 2025-12-03  
**Status:** ARCHITECTURAL SPECIFICATION (PRE-IMPLEMENTATION)

---

## Phase 1: How 60 Chunks Are Produced

### Source Code Analysis
**File:** `src/farfan_pipeline/core/phases/phase1_spc_ingestion_full.py`

**Grid Structure:**
```python
POLICY_AREAS = ["PA01", ..., "PA10"]  # 10 areas
DIMENSIONS = ["DIM01", ..., "DIM06"]   # 6 dimensions
TOTAL_COMBINATIONS = 10 × 6 = 60       # EXACT, IMMUTABLE
```

**Chunk Creation Logic (SP4):**
```python
def _execute_sp4_chunk_creation():
    chunks = []
    idx = 0
    for pa in POLICY_AREAS:
        for dim in DIMENSIONS:
            chunk = Chunk(
                policy_area_id=pa,      # ← KEY FIELD 1
                dimension_id=dim,       # ← KEY FIELD 2
                chunk_index=idx,        # 0-59
                text="[extracted_content]",
                # Metadata fields populated in SP5-SP10
                causal_graph=None,      # SP5
                temporal_markers=None,  # SP8
                arguments=None,         # SP7
                discourse_mode=None,    # SP9
                strategic_rank=None,    # SP10/SP15
                signal_tags=[],         # SP12 (irrigation)
                signal_scores={}        # SP12 (irrigation)
            )
            chunks.append(chunk)
            idx += 1
    return chunks
```

**Validation (HARD CONTRACT - WEIGHT 10000):**
```python
# EXACT COUNT
assert len(chunks) == 60

# UNIQUE COVERAGE - NO DUPLICATES
seen = set()
for chunk in chunks:
    combo = (chunk.policy_area_id, chunk.dimension_id)
    assert combo not in seen  # Dies if duplicate

# COMPLETE COVERAGE - NO GAPS
for pa in POLICY_AREAS:
    for dim in DIMENSIONS:
        assert (pa, dim) in seen  # Dies if missing
```

**Conclusion:** Each chunk is UNIQUELY identified by `(policy_area_id, dimension_id)` tuple. This is the JOIN key.

---

## Phase 2: Signal Source (Questionnaire Monolith)

### JSON Structure Analysis
**File:** `system/config/questionnaire/questionnaire_monolith.json`

**Top-Level:**
```json
{
  "$schema": "...",
  "blocks": {
    "micro_questions": [/* 300 questions */],
    "meso_questions": [...],
    "macro_question": {...},
    "scoring": {...}
  }
}
```

**Micro Question Structure (ONE OF 300):**
```json
{
  "question_id": "Q001",
  "question_global": 1,
  "base_slot": "D1-Q1",
  
  // ← JOIN KEYS (match to chunk)
  "policy_area_id": "PA01",
  "dimension_id": "DIM01",
  "cluster_id": "CL02",
  
  // ← SIGNAL FIELDS FOR IRRIGATION
  "patterns": [
    {
      "id": "PAT-Q001-000",
      "pattern": "línea base|año base",
      "category": "TEMPORAL",
      "confidence_weight": 0.85,
      "match_type": "REGEX",
      "flags": "i"
    },
    // ... 13 more patterns
  ],
  
  "expected_elements": [
    {
      "type": "fuentes_oficiales",
      "minimum": 2,
      "required": true
    },
    // ... 3 more elements
  ],
  
  "validations": {
    "verificar_fuentes": {
      "minimum_required": 2,
      "patterns": ["fuente:", "según", ...],
      "specificity": "MEDIUM"
    },
    // ... 4 more validation rules
  },
  
  "scoring_modality": "TYPE_A",
  "scoring_definition_ref": "scoring_modalities.TYPE_A",
  
  "failure_contract": {
    "abort_if": ["missing_required_element", "incomplete_text"],
    "emit_code": "ABORT-Q001-REQ"
  },
  
  "method_sets": [/* 17 method specifications */],
  
  "text": "¿El diagnóstico presenta datos numéricos..."
}
```

**Key Insight:** Each question has `(policy_area_id, dimension_id)` that MUST match exactly ONE chunk.

---

## Phase 3: Executor Contracts

### Contract Structure (300 v3 Contracts)
**Location:** `config/executor_contracts/specialized/Q001.v3.json` (... Q300.v3.json)

**Relevant Sections:**
```json
{
  "identity": {
    "question_id": "Q001",
    "policy_area_id": "PA01",  // ← JOIN KEY 1
    "dimension_id": "DIM01",    // ← JOIN KEY 2
    "base_slot": "D1-Q1"
  },
  
  "question_context": {
    "patterns": [/* SAME as monolith */],
    "expected_elements": [/* SAME as monolith */],
    "validations": {/* SAME as monolith */}
  },
  
  "signal_requirements": {
    "mandatory_signals": [],
    "optional_signals": [],
    "note": "Under development..."
  },
  
  "evidence_assembly": {
    "assembly_rules": [
      {
        "target": "elements_found",
        "sources": ["text_mining.critical_links", ...],
        "merge_strategy": "concat"
      }
    ]
  },
  
  "validation_rules": {
    "rules": [
      {
        "field": "elements_found",
        "must_contain": {"count": 1, "elements": ["cobertura_territorial"]}
      }
    ]
  }
}
```

**Conclusion:** Contracts are ENRICHED versions of monolith questions with additional orchestration metadata.

---

## Phase 4: Information Flow Matrix (BY PIPELINE PHASE)

### 4.1 CHUNKING Phase
**Pipeline Location:** `src/farfan_pipeline/flux/phases.py::run_chunking()`

**Question: What info does chunking need from signals?**

| Signal Field | Needed? | Purpose | Source |
|--------------|---------|---------|--------|
| `patterns` | ❌ NO | Chunking is structural, not pattern-based | N/A |
| `expected_elements` | ❌ NO | Chunking doesn't validate elements | N/A |
| `validations` | ❌ NO | Validation happens AFTER chunking | N/A |
| `scoring_modality` | ❌ NO | Scoring happens AFTER evidence | N/A |
| `dimension_id` | ✅ YES | Chunks ARE created per dimension | Phase 1 |
| `policy_area_id` | ✅ YES | Chunks ARE created per policy area | Phase 1 |

**CONCLUSION:** Chunking PRODUCES (PA, DIM) labeled chunks. It doesn't CONSUME signals.

---

### 4.2 SIGNAL ENRICHMENT Phase
**Pipeline Location:** `src/farfan_pipeline/flux/phases.py::run_signals()`

**Question: What signals should be attached to chunks?**

**Current Implementation (WRONG):**
```python
# Only uses policy_area_hint
pack = registry_get(chunk.policy_area_hint)
chunk["applicable_patterns"] = pack.patterns  # Generic PA patterns
```

**Correct Synchronization:**
```python
# Load ALL 300 questions from monolith
questions = load_questionnaire_monolith()

# For each chunk, find ALL questions matching (PA, DIM)
chunk_signals = {}
for chunk in chunks:
    matching_questions = [
        q for q in questions 
        if q.policy_area_id == chunk.policy_area_id 
        and q.dimension_id == chunk.dimension_id
    ]
    
    # Aggregate patterns from ALL matching questions
    all_patterns = []
    for q in matching_questions:
        all_patterns.extend(q.patterns)
    
    chunk_signals[chunk.id] = {
        "patterns": all_patterns,
        "question_ids": [q.question_id for q in matching_questions],
        "dimension": chunk.dimension_id,
        "policy_area": chunk.policy_area_id
    }
```

**WHY:** Multiple questions can share (PA, DIM). Example:
- Q001: PA01 × DIM01 (14 patterns)
- Q002: PA01 × DIM01 (12 patterns)
- Q003: PA01 × DIM01 (15 patterns)
→ Chunk PA01_DIM01 needs ALL 41 patterns (deduplicated)

---

### 4.3 EVIDENCE ASSEMBLY Phase
**Pipeline Location:** `src/farfan_pipeline/core/orchestrator/evidence_assembler.py`

**Question: What signals does evidence assembly need?**

| Signal Field | Needed? | Purpose | How Used |
|--------------|---------|---------|----------|
| `patterns` | ✅ YES | Extract evidence from text | Regex matching on chunk text |
| `expected_elements` | ✅ YES | Know what to look for | Assembly rules target |
| `method_sets` | ✅ YES | Which methods to invoke | Method orchestration |
| `confidence_weight` | ✅ YES | Weight evidence | Bayesian aggregation |

**Input:** Enriched chunk with patterns
**Process:**
```python
def assemble_evidence(chunk, question_contract):
    evidence = []
    for pattern in chunk.applicable_patterns:
        matches = regex.findall(pattern.pattern, chunk.text)
        for match in matches:
            evidence.append({
                "value": match,
                "pattern_id": pattern.id,
                "confidence": pattern.confidence_weight,
                "category": pattern.category
            })
    
    # Group by expected_elements
    grouped = group_by_element_type(
        evidence, 
        question_contract.expected_elements
    )
    
    return {"elements": grouped, "raw_matches": evidence}
```

---

### 4.4 EVIDENCE VALIDATION Phase
**Pipeline Location:** `src/farfan_pipeline/core/orchestrator/evidence_validator.py`

**Question: What signals does validation need?**

| Signal Field | Needed? | Purpose | How Used |
|--------------|---------|---------|----------|
| `expected_elements` | ✅ YES | Minimum counts | Assert `len(found) >= minimum` |
| `validations` | ✅ YES | Validation rules | Apply specificity thresholds |
| `failure_contract` | ✅ YES | Abort conditions | Trigger pipeline termination |

**Input:** Assembled evidence
**Process:**
```python
def validate_evidence(evidence, question_contract):
    for expected_elem in question_contract.expected_elements:
        found = evidence.elements.get(expected_elem.type, [])
        
        if expected_elem.required and len(found) == 0:
            return {
                "valid": False,
                "error": question_contract.failure_contract.emit_code,
                "missing": expected_elem.type
            }
        
        if len(found) < expected_elem.minimum:
            return {
                "valid": False,
                "error": f"Insufficient {expected_elem.type}",
                "found": len(found),
                "required": expected_elem.minimum
            }
    
    return {"valid": True}
```

---

### 4.5 SCORING Phase
**Pipeline Location:** `src/farfan_pipeline/analysis/scoring/`

**Question: What signals does scoring need?**

| Signal Field | Needed? | Purpose | How Used |
|--------------|---------|---------|----------|
| `scoring_modality` | ✅ YES | Scoring algorithm | TYPE_A vs TYPE_B logic |
| `scoring_definition_ref` | ✅ YES | Detailed scoring spec | Load from scoring_modalities |
| `confidence_weight` | ✅ YES | Weight evidence | Bayesian aggregation |
| `expected_elements` | ✅ YES | Scoring criteria | Count-based scores |

**Input:** Validated evidence
**Process:**
```python
def score_question(evidence, question_contract):
    if question_contract.scoring_modality == "TYPE_A":
        # Coherence-based scoring
        score = calculate_coherence_score(
            evidence,
            question_contract.expected_elements,
            question_contract.patterns
        )
    elif question_contract.scoring_modality == "TYPE_B":
        # Binary validation scoring
        if evidence.valid:
            score = 1.0
        else:
            score = 0.0
    
    return {
        "score": score,
        "modality": question_contract.scoring_modality,
        "confidence": evidence.mean_confidence
    }
```

---

### 4.6 AGGREGATION Phase
**Pipeline Location:** `src/farfan_pipeline/analysis/aggregation/`

**Question: What signals does aggregation need?**

| Signal Field | Needed? | Purpose | How Used |
|--------------|---------|---------|----------|
| `dimension_id` | ✅ YES | Group micro → meso | Aggregate by dimension |
| `policy_area_id` | ✅ YES | Group meso → macro | Aggregate by policy area |
| `cluster_id` | ✅ YES | Group by cluster | Cross-cutting analysis |

**Input:** Scored questions
**Process:**
```python
def aggregate_to_meso(micro_scores):
    # Group by dimension
    by_dimension = defaultdict(list)
    for score in micro_scores:
        by_dimension[score.dimension_id].append(score.value)
    
    # Aggregate per dimension
    meso_scores = {}
    for dim, scores in by_dimension.items():
        meso_scores[dim] = {
            "mean": np.mean(scores),
            "weighted": weighted_mean(scores, confidences),
            "count": len(scores)
        }
    
    return meso_scores
```

---

## Phase 5: CANONICAL JOIN TABLE

### Table Structure (ACTUAL DATA FROM MONOLITH)

```
ExecutorID | PA    | DIM    | ChunkID              | Patterns | ExpElems | Validations | Modality
-----------|-------|--------|----------------------|----------|----------|-------------|----------
Q001       | PA01  | DIM01  | chunk_PA01_DIM01     | 14       | 4        | 5           | TYPE_A
Q002       | PA01  | DIM01  | chunk_PA01_DIM01     | 9        | 3        | 1           | TYPE_B
Q003       | PA01  | DIM01  | chunk_PA01_DIM01     | 9        | 3        | 1           | TYPE_B
Q004       | PA01  | DIM01  | chunk_PA01_DIM01     | 9        | 5        | 1           | TYPE_B
Q005       | PA01  | DIM01  | chunk_PA01_DIM01     | 10       | 4        | 1           | TYPE_E
Q006       | PA01  | DIM02  | chunk_PA01_DIM02     | [...]    | [...]    | [...]       | [...]
...        | ...   | ...    | ...                  | ...      | ...      | ...         | ...
Q300       | PA10  | DIM06  | chunk_PA10_DIM06     | [...]    | [...]    | [...]       | [...]
```

**CRITICAL OBSERVATION:** First 5 questions (Q001-Q005) ALL map to chunk_PA01_DIM01
- This is MANY-TO-ONE mapping
- Chunk PA01_DIM01 receives: 14+9+9+9+10 = 51 total patterns (before deduplication)
- Mixed scoring modalities: TYPE_A, TYPE_B, TYPE_E on SAME chunk

### Key Observations

1. **MANY-TO-ONE:** Multiple executors (Q001, Q002, Q003) → ONE chunk (PA01_DIM01)
2. **NO ONE-TO-MANY:** Each executor has EXACTLY ONE chunk (enforced by unique PA×DIM in contract)
3. **SIGNAL AGGREGATION:** Chunk receives UNION of all patterns from matching questions

### Build Logic

```python
def build_join_table(contracts: list, chunks: list) -> list[Binding]:
    bindings = []
    
    for contract in contracts:
        # Find matching chunk
        chunk = find_chunk(
            chunks,
            policy_area_id=contract.identity.policy_area_id,
            dimension_id=contract.identity.dimension_id
        )
        
        if chunk is None:
            raise FatalError(
                f"Contract {contract.identity.question_id} "
                f"requires chunk ({contract.identity.policy_area_id}, "
                f"{contract.identity.dimension_id}) but NONE FOUND"
            )
        
        binding = Binding(
            executor_contract_id=contract.identity.question_id,
            policy_area_id=contract.identity.policy_area_id,
            dimension_id=contract.identity.dimension_id,
            chunk_id=chunk.id,
            
            # Signals to irrigate
            patterns=contract.question_context.patterns,
            expected_elements=contract.question_context.expected_elements,
            validations=contract.question_context.validations,
            scoring_modality=contract.question_context.scoring_modality,
            failure_contract=contract.error_handling.failure_contract,
            
            # Tracking
            irrigated_at=None,  # Populated during irrigation
            consumed_at=None    # Populated during execution
        )
        
        bindings.append(binding)
    
    # VALIDATION: Ensure all 60 chunks are covered
    covered_chunks = set(b.chunk_id for b in bindings)
    assert len(covered_chunks) == 60, \
        f"Only {len(covered_chunks)} chunks covered, need 60"
    
    return bindings
```

---

## Phase 6: IRRIGATION IMPLEMENTATION

### Correct Architecture

```python
def run_signals(
    chunks: ChunksDeliverable,
    contracts: list[ExecutorContract]
) -> SignalsDeliverable:
    """
    Irrigate signals from 300 contracts to 60 chunks.
    Each chunk receives signals from ALL contracts matching its (PA, DIM).
    """
    
    # STEP 1: Build JOIN table
    join_table = build_join_table(contracts, chunks.chunks)
    
    # STEP 2: Group bindings by chunk
    signals_by_chunk = defaultdict(lambda: {
        "patterns": [],
        "expected_elements": [],
        "validations": {},
        "scoring_modalities": set(),
        "bound_questions": []
    })
    
    for binding in join_table:
        chunk_signals = signals_by_chunk[binding.chunk_id]
        
        # Aggregate patterns (deduplicate by ID)
        existing_pattern_ids = {p["id"] for p in chunk_signals["patterns"]}
        for pattern in binding.patterns:
            if pattern["id"] not in existing_pattern_ids:
                chunk_signals["patterns"].append(pattern)
        
        # Aggregate expected elements
        chunk_signals["expected_elements"].extend(binding.expected_elements)
        
        # Merge validations (union)
        for key, val in binding.validations.items():
            if key not in chunk_signals["validations"]:
                chunk_signals["validations"][key] = val
        
        # Track scoring modalities
        chunk_signals["scoring_modalities"].add(binding.scoring_modality)
        
        # Track bound questions
        chunk_signals["bound_questions"].append({
            "question_id": binding.executor_contract_id,
            "base_slot": f"D{binding.dimension_id[-1]}-Q{binding.executor_contract_id[1:]}"
        })
    
    # STEP 3: Enrich chunks
    enriched_chunks = []
    for chunk in chunks.chunks:
        signals = signals_by_chunk[chunk.id]
        
        enriched_chunks.append({
            **chunk.dict(),
            "signal_enrichment": {
                "patterns": signals["patterns"],
                "expected_elements": signals["expected_elements"],
                "validations": signals["validations"],
                "scoring_modalities": list(signals["scoring_modalities"]),
                "bound_questions": signals["bound_questions"],
                "pattern_count": len(signals["patterns"]),
                "question_count": len(signals["bound_questions"])
            }
        })
    
    # STEP 4: Generate manifest
    manifest = {
        "success": True,
        "timestamp": datetime.now().isoformat(),
        "total_chunks": len(enriched_chunks),
        "total_contracts": len(contracts),
        "bindings": [
            {
                "executor_contract_id": b.executor_contract_id,
                "chunk_id": b.chunk_id,
                "policy_area_id": b.policy_area_id,
                "dimension_id": b.dimension_id,
                "patterns_delivered": len(b.patterns)
            }
            for b in join_table
        ],
        "invariants_validated": {
            "all_contracts_have_chunks": len(join_table) == 300,
            "all_chunks_covered": len(set(b.chunk_id for b in join_table)) == 60,
            "no_orphan_chunks": all(
                chunk.id in signals_by_chunk for chunk in chunks.chunks
            )
        }
    }
    
    return SignalsDeliverable(
        enriched_chunks=enriched_chunks,
        manifest=manifest
    )
```

---

## Phase 7: DOWNSTREAM CONSUMPTION

### 7.1 Evidence Assembler

**Input:** Enriched chunk with signals
**Consumption:**
```python
def assemble(self, chunk, question_contract):
    # Use chunk's aggregated patterns
    patterns = chunk.signal_enrichment.patterns
    
    # Extract evidence using all patterns
    evidence = []
    for pattern in patterns:
        matches = self._apply_pattern(pattern, chunk.text)
        evidence.extend(matches)
    
    # Group by expected elements (from question contract, NOT chunk)
    grouped = self._group_evidence(
        evidence,
        question_contract.question_context.expected_elements
    )
    
    return grouped
```

### 7.2 Evidence Validator

**Input:** Assembled evidence + question contract
**Consumption:**
```python
def validate(self, evidence, question_contract):
    # Use question's specific validation rules
    rules = question_contract.question_context.validations
    
    for rule_name, rule_spec in rules.items():
        result = self._apply_validation_rule(evidence, rule_spec)
        if not result.passed:
            return ValidationResult(
                valid=False,
                failed_rule=rule_name,
                error_code=question_contract.error_handling.failure_contract.emit_code
            )
    
    return ValidationResult(valid=True)
```

### 7.3 Scorer

**Input:** Validated evidence + question contract
**Consumption:**
```python
def score(self, evidence, question_contract):
    modality = question_contract.question_context.scoring_modality
    
    if modality == "TYPE_A":
        score = self._coherence_scoring(evidence, question_contract)
    elif modality == "TYPE_B":
        score = self._binary_scoring(evidence, question_contract)
    
    return Score(
        value=score,
        modality=modality,
        question_id=question_contract.identity.question_id
    )
```

---

## CONCLUSION: Implementation Checklist

### ✅ Already Correct
1. Chunks are produced with (PA, DIM) labels ✓
2. Contracts have (PA, DIM) identity ✓
3. Monolith questions have (PA, DIM) identity ✓

### ❌ Currently Broken
1. Signal irrigation uses PA-only lookup (should use PA×DIM)
2. No JOIN table validation (should assert 1:many executor:chunk)
3. No signal aggregation (multiple questions → one chunk)
4. No manifest generation (should prove synchronization)

### 🔨 Implementation Tasks

**Task 1:** Create JOIN table builder
- Load 300 contracts
- Match to 60 chunks by (PA, DIM)
- Validate coverage (all contracts have chunks, all chunks covered)

**Task 2:** Aggregate signals per chunk
- Group contracts by chunk_id
- Union patterns (deduplicate by ID)
- Union expected_elements
- Merge validations
- Track bound questions

**Task 3:** Generate verification manifest
- Prove all_contracts_have_chunks = True
- Prove all_chunks_covered = True
- Prove no_duplicate_irrigation = True
- Export manifest.json for CI validation

**Task 4:** Update downstream consumers
- Evidence assembler uses chunk.signal_enrichment.patterns
- Evidence validator uses question_contract.validations
- Scorer uses question_contract.scoring_modality

### 📊 Success Metrics

**Manifest must show:**
```json
{
  "success": true,
  "total_contracts": 300,
  "total_chunks": 60,
  "invariants_validated": {
    "all_contracts_have_chunks": true,
    "all_chunks_covered": true,
    "no_orphan_chunks": true,
    "average_questions_per_chunk": 5.0  // 300/60
  }
}
```

---

**Next Step:** Implement JOIN table builder with full validation.
