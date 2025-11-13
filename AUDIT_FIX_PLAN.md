# Audit Fix Plan

**Generated:** 2025-11-06T07:25:37.146896

## Short-Term Priority (HIGH)

**Timeline:** Within 1 week

**Owner:** Development Team

### CONTRACT-001: Missing pipeline stage contracts

**Issue:** Missing contracts for: canonical_policy_package, chunk_graph, preprocessed_document, scored_result, signal_pack

**Action:** Define Pydantic schemas for all pipeline stage interfaces

---

### ARGROUTER-033: Silent drop detected

**Issue:** ArgRouter contains silent drop logic

**Action:** Remove silent drops and raise typed errors for all invalid arguments

---

### DETERM-037: Random usage without seeding

**Issue:** Found 3 files using random without seed

**Action:** Use seed_factory or call set_seed() before random operations

---

### AGGREG-041: Missing column validation

**Issue:** Aggregation should fail on missing required columns

**Action:** Add validation to raise error on missing required columns

**File:** `src/saaaaaa/core/aggregation.py`

---

### DEPS-047: Undeclared dependencies detected

**Issue:** Found 71 imported packages not in requirements

**Action:** Add missing packages to requirements.txt with version pins

---

## Medium-Term Priority (MEDIUM)

**Timeline:** Within 2-4 weeks

**Owner:** Development Team

### CONTRACT-002: Pydantic not used for contract validation

**Issue:** No Pydantic BaseModel found in contract definitions

**Action:** Use Pydantic BaseModel for all contract schemas to ensure type safety

---

### PARAM-003: Config class missing standard methods: APIConfig

**Issue:** Config class lacks from_env=✗ or from_cli=✗

**Action:** Add from_env and from_cli methods to APIConfig

---

### PARAM-004: Config class missing standard methods: WorkerPoolConfig

**Issue:** Config class lacks from_env=✗ or from_cli=✗

**Action:** Add from_env and from_cli methods to WorkerPoolConfig

---

### PARAM-005: Config class missing standard methods: ChunkingConfig

**Issue:** Config class lacks from_env=✗ or from_cli=✗

**Action:** Add from_env and from_cli methods to ChunkingConfig

---

### PARAM-006: Config class missing standard methods: PolicyEmbeddingConfig

**Issue:** Config class lacks from_env=✗ or from_cli=✗

**Action:** Add from_env and from_cli methods to PolicyEmbeddingConfig

---

### PARAM-007: Config class missing standard methods: SemanticConfig

**Issue:** Config class lacks from_env=✗ or from_cli=✗

**Action:** Add from_env and from_cli methods to SemanticConfig

---

### PARAM-008: Config class missing standard methods: ProcessorConfig

**Issue:** Config class lacks from_env=✗ or from_cli=✗

**Action:** Add from_env and from_cli methods to ProcessorConfig

---

### PARAM-009: Config class missing standard methods: IngestConfig

**Issue:** Config class lacks from_env=✓ or from_cli=✗

**Action:** Add from_cli methods to IngestConfig

---

### PARAM-010: Config class missing standard methods: NormalizeConfig

**Issue:** Config class lacks from_env=✓ or from_cli=✗

**Action:** Add from_cli methods to NormalizeConfig

---

### PARAM-011: Config class missing standard methods: ChunkConfig

**Issue:** Config class lacks from_env=✓ or from_cli=✗

**Action:** Add from_cli methods to ChunkConfig

---

*... and 32 more medium priority items*

