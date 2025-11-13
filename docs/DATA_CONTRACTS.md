# Data Contracts Hardening

This document captures the operational rules for the questionnaire and rubric configuration files after the v3.0.0 migration to atomic identifiers.

## Versioning and Compatibility

- Every configuration file declares a semantic `version` and a 64-character `content_hash` derived from the canonical JSON payload.
- `rubric_scoring.json` specifies `requires_questionnaire_version` and validation fails if it diverges from `questionnaire.json`.
- Historical schemas are frozen under `schemas/` and any change requires a new semantic version alongside updated compatibility metadata.

## Evidence Taxonomy

`questionnaire.json` enumerates the verification sources in `metadata.sources_of_verification`. All questions reference that taxonomy through `required_evidence_keys`, while the rubric enforces the same keys at matrix and policy-area levels. Unknown keys trigger validation failures.

## Public API Stability Policy

### Type Checking Requirements

All public API functions must use `--strict` mode type checking (mypy) with the following requirements:

```bash
# Run type checking on public API modules
mypy --strict orchestrator.py scoring.py recommendation_engine.py validation_engine.py
```

**Required for all public APIs:**
- Explicit type annotations for all parameters and return types
- No `Any` types without explicit justification
- No implicit `Optional` types

### Keyword Arguments (`**kwargs`) Policy

**Default Rule**: Public APIs must NOT accept arbitrary `**kwargs` to ensure type safety and explicit contracts.

**Allowed Exemptions** (requires explicit documentation):

1. **Backward Compatibility Wrapper** - Legacy API wrappers that delegate to new APIs
   ```python
   def legacy_score(evidence: Dict, modality: str, **deprecated_kwargs) -> ScoredResult:
       """Legacy wrapper for scoring. DO NOT USE in new code.
       
       **kwargs accepted for backward compatibility only. All new calls should
       use apply_scoring() with explicit parameters.
       
       Deprecated: v3.0.0
       Removal: v4.0.0
       """
       warnings.warn("Use apply_scoring() instead", DeprecationWarning)
       return apply_scoring(evidence=evidence, modality=modality)
   ```

2. **Extensible Plugin System** - Where plugins provide additional context
   ```python
   def register_validator(validator_type: str, validator_fn: Callable, 
                         **plugin_metadata: str) -> None:
       """Register a validator with optional plugin metadata.
       
       Args:
           validator_type: Type of validator (must be in ALLOWED_TYPES)
           validator_fn: Validator callable
           **plugin_metadata: Optional metadata (author, version, description)
                             All values must be strings. Unknown keys are logged
                             but do not cause failures.
       """
   ```

3. **Pass-Through Context** - Framework functions that pass context to callbacks
   ```python
   def execute_pipeline(steps: List[PipelineStep], 
                       **execution_context: Any) -> PipelineResult:
       """Execute pipeline with arbitrary execution context.
       
       Args:
           steps: Pipeline steps to execute
           **execution_context: Passed to each step's execute() method.
                               Type and content validated by individual steps.
       """
   ```

**Exemption Request Process:**

1. Document the exemption in the function's docstring with explicit rationale
2. Add type annotation `**kwargs: <Type>` (not `**kwargs: Any`)
3. Add validation logic that logs or rejects unknown keys
4. Add the function to the exemption registry in `docs/API_EXEMPTIONS.md`
5. Include migration timeline if this is a backward compatibility exemption

**Migration Path for Existing APIs:**

| Phase | Timeline | Action |
|-------|----------|--------|
| Phase 1 (v3.0-v3.5) | Current | Add deprecation warnings to `**kwargs` functions |
| Phase 2 (v3.5-v4.0) | 6 months | Introduce explicit alternatives, mark old APIs as deprecated |
| Phase 3 (v4.0+) | 12 months | Remove `**kwargs` from public APIs, keep only documented exemptions |

### Type Checking Enforcement

Type checking is enforced in CI via `.github/workflows/type-check.yml`:

```yaml
- name: Type check public APIs
  run: |
    mypy --strict orchestrator.py scoring.py recommendation_engine.py \
         validation_engine.py policy_processor.py embedding_policy.py \
         semantic_chunking_policy.py
```

Failure criteria: Any type error in strict mode causes build failure.

## Determinism, NA Rules, and Penalties

- Modalities that rely on semantic similarity (`TYPE_F`) must include a `determinism` block containing the seed contract: `{ "seed_required": true, "seed_source": "seed_factory_v1" }`.
- `rubric_scoring.json` centralises NA behaviour in `na_rules`. Missing modality or policy-area entries prevent the rubric from loading.
- Compliance penalties (`contradictory_info`, `missing_indicator`, `OOD_flag`) are declared once with explicit weights.

## Scoring Normalization and Parity

### Modality Score Ranges

Different modalities use different raw score ranges that must be normalized to [0, 1] for quality level assignment:

| Modality | Raw Score Range | Normalization Formula | Quality Threshold Mapping |
|----------|----------------|----------------------|--------------------------|
| TYPE_A | [0, 4] | `normalized = raw_score / 4.0` | 0→0.00, 1→0.25, 2→0.50, 3→0.75, 4→1.00 |
| TYPE_B | [0, 3] | `normalized = raw_score / 3.0` | 0→0.00, 1→0.33, 2→0.67, 3→1.00 |
| TYPE_C | [0, 3] | `normalized = raw_score / 3.0` | 0→0.00, 1→0.33, 2→0.67, 3→1.00 |
| TYPE_D | [0, 3] | `normalized = raw_score / 3.0` | 0→0.00, 1→0.33, 2→0.67, 3→1.00 |
| TYPE_E | [0, 3] | `normalized = raw_score / 3.0` | 0→0.00, 1→0.33, 2→0.67, 3→1.00 |
| TYPE_F | [0, 3] | `normalized = raw_score / 3.0` | 0→0.00, 1→0.33, 2→0.67, 3→1.00 |

### Parity Definition

**Parity** means that questions scored with different modalities achieve the same quality level for equivalent evidence quality:

- A TYPE_A score of 3.4/4.0 (normalized: 0.85) = EXCELENTE
- A TYPE_B score of 2.55/3.0 (normalized: 0.85) = EXCELENTE
- A TYPE_C score of 2.55/3.0 (normalized: 0.85) = EXCELENTE

**Mathematical Definition**: Two scores are "at parity" if their normalized values differ by <0.01 (1%).

### Quality Level Thresholds

Quality levels are assigned based on normalized scores (0-1 range):

```python
QUALITY_THRESHOLDS = {
    "EXCELENTE": 0.85,      # ≥85% of maximum possible score
    "BUENO": 0.70,           # ≥70% of maximum possible score  
    "ACEPTABLE": 0.55,       # ≥55% of maximum possible score
    "INSUFICIENTE": 0.00     # <55% of maximum possible score
}
```

### Automated Parity Validation

Run parity validation to ensure consistent quality assignments across modalities:

```bash
# Validate that equivalent evidence quality produces equivalent quality levels
python tools/validation/validate_scoring_parity.py

# Expected checks:
# 1. Normalization formulas are correct for each modality
# 2. Quality thresholds are identical across all modalities
# 3. Boundary conditions (0.849 vs 0.850) produce correct quality levels
# 4. No modality has an unfair advantage at quality boundaries
```

This validation runs in CI as part of the `data-contracts` workflow.

### Parity Test Cases

The following test cases ensure parity across modalities:

```python
# tests/test_scoring_parity.py
def test_excelente_parity():
    """All modalities assign EXCELENTE at 85% normalized score."""
    assert score_TYPE_A(3.4) == "EXCELENTE"  # 3.4/4.0 = 0.85
    assert score_TYPE_B(2.55) == "EXCELENTE"  # 2.55/3.0 = 0.85
    assert score_TYPE_C(2.55) == "EXCELENTE"  # 2.55/3.0 = 0.85
    
def test_quality_boundaries():
    """Scores at boundaries are handled consistently."""
    # Just below EXCELENTE threshold
    assert score_TYPE_A(3.39) == "BUENO"  # 3.39/4.0 = 0.8475
    assert score_TYPE_B(2.54) == "BUENO"  # 2.54/3.0 = 0.8467
```

## Validation Commands

### Local Validation (Pre-Commit)

Run these commands locally before committing to ensure compliance:

```bash
# Full schema, weight, compatibility, and checksum validation
python schema_validator.py

# Cross-file integrity (Q→PA→CL mapping, weight sums, modality matrix)
python tools/integrity/check_cross_refs.py

# Strict linting with duplicate-key detection and schema enforcement
python tools/lint/json_lint.py questionnaire.json --schema schemas/questionnaire.schema.json
python tools/lint/json_lint.py rubric_scoring.json --schema schemas/rubric_scoring.schema.json

# Run all validation checks at once
./scripts/validate_contracts_local.sh
```

### CI Enforcement

Validation is automatically executed in three places:
1. **On Import**: `orchestrator/__init__.py` validates on module load
2. **Pre-commit Hooks**: `.pre-commit-config.yaml` runs linters
3. **CI Pipeline**: `.github/workflows/data-contracts.yml` enforces all checks

#### CI Job Definitions

The following jobs run in the `data-contracts` workflow:

| Job Name | Command | Failure Criteria | Exit Code on Failure |
|----------|---------|------------------|---------------------|
| `Schema validation` | `python schema_validator.py` | Schema mismatch, missing version, invalid content_hash | 1 |
| `Cross reference integrity` | `python tools/integrity/check_cross_refs.py` | Broken Q→PA→CL references, weight sum ≠ 1.0 | 1 |
| `Questionnaire lint` | `python tools/lint/json_lint.py questionnaire.json --schema schemas/questionnaire.schema.json` | Duplicate keys, schema violations, invalid JSON | 1 |
| `Rubric lint` | `python tools/lint/json_lint.py rubric_scoring.json --schema schemas/rubric_scoring.schema.json` | Duplicate keys, schema violations, invalid JSON | 1 |
| `Deterministic artifact generation` | `diff artifacts/run1/deterministic_snapshot.json artifacts/run2/deterministic_snapshot.json` | Non-identical SHA-256 hashes between runs | 1 |

#### Reproducing CI Failures Locally

If a CI job fails, reproduce it locally:

```bash
# For schema validation failures:
python schema_validator.py --verbose

# For cross-reference failures:
python tools/integrity/check_cross_refs.py --debug

# For linting failures:
python tools/lint/json_lint.py <file> --schema <schema> --verbose

# For determinism failures:
python tools/integrity/dump_artifacts.py artifacts/test_run1
python tools/integrity/dump_artifacts.py artifacts/test_run2
diff -u artifacts/test_run1/deterministic_snapshot.json artifacts/test_run2/deterministic_snapshot.json
```

All failures include:
- Specific file and line number (when applicable)
- Expected vs. actual values
- Remediation steps in error message

## Deterministic Artifacts

The CI pipeline generates two runs of deterministic artifacts and compares their SHA-256 hashes:

```bash
python tools/integrity/dump_artifacts.py artifacts/run1
python tools/integrity/dump_artifacts.py artifacts/run2
diff artifacts/run1/deterministic_snapshot.json artifacts/run2/deterministic_snapshot.json
```

Any divergence indicates a non-deterministic path in the scoring workflow.

## Migrations

Use the canonical migration script to translate legacy P#/D#/Q# structures into PAxx/DIMxx/Qxxx identifiers, normalise weights, and update hashes:

```bash
python tools/migrations/migrate_ids_v1_to_v2.py \
    --questionnaire questionnaire.json \
    --rubric rubric_scoring.json \
    --execution-mapping execution_mapping.yaml \
    --write
```

Running the script rewrites the target files with sorted keys, injects `content_hash`, refreshes `config/metadata_checksums.json`, and enforces the new evidence taxonomy.

## Operational Feasibility Gates

### Runtime Validators

Runtime validators must see non-zero traffic in production-like environments. To enable pre-production testing:

#### Synthetic Traffic Generation

```bash
# Generate synthetic policy analysis requests
python tools/testing/generate_synthetic_traffic.py \
    --volume 100 \
    --modalities TYPE_A,TYPE_B,TYPE_C,TYPE_D,TYPE_E,TYPE_F \
    --policy-areas PA01,PA02,PA03

# Expected output: 100 requests across all modalities and policy areas
# Minimum sample size: 10 requests per modality per policy area
```

#### Canary Workflow

The canary workflow validates runtime behavior in a pre-production environment:

```bash
# Run canary checks before deployment
python tools/testing/canary_checks.py \
    --endpoint http://localhost:5000 \
    --sampling-frequency 1m \
    --duration 10m \
    --min-samples 100

# Validation criteria:
# - All 6 modalities must process ≥10 requests successfully
# - Error rate must be <1%
# - Mean response time must be <500ms
# - All contract validators must report ≥1 validation
```

#### Boot Checks (CI-Friendly)

Registry and runtime validators must start without errors:

```bash
# Validate registry loads without ClassNotFoundError
python -c "from orchestrator import registry; registry.validate_all_classes()"
# Exit code 0 = success, 1 = ClassNotFoundError or other failure

# Validate runtime validators initialize
python -c "from validation_engine import RuntimeValidator; RuntimeValidator().health_check()"
# Exit code 0 = success, 1 = initialization failure

# Complete boot check (includes all validations)
python tools/testing/boot_check.py
# Expected: All modules load, all validators initialize, registry complete
```

#### Sampling Requirements

| Check Type | Frequency | Minimum Sample Size | Duration |
|------------|-----------|---------------------|----------|
| Canary (pre-prod) | Every 1 minute | 100 requests total | 10 minutes |
| Synthetic traffic (CI) | On PR | 10 per modality | N/A |
| Boot check (CI) | On PR and deploy | N/A | <30 seconds |
| Runtime validator traffic | Production | 1 per hour per validator | Continuous |

## Tests

Property-based regression tests covering invalid references, weight violations, missing modalities, absent NA rules, and determinism gaps live under `tests/data/test_questionnaire_and_rubric.py`.

Additional operational tests:
- `tests/operational/test_synthetic_traffic.py` - Validates synthetic traffic generation
- `tests/operational/test_canary_workflow.py` - Validates canary deployment checks
- `tests/operational/test_boot_checks.py` - Validates module initialization

## Release Management

After merging into `main`, create an immutable tag named `data-contracts-vX.Y.Z`, regenerate `content_hash` values, and refresh `config/metadata_checksums.json`. Any subsequent change must bump the patch component (e.g., `v3.0.1`) and re-run the validation suite before tagging.

## Contract Error Logging

### Machine-Readable Log Schema

All contract validation errors must be logged in a structured format conforming to `schemas/contract_error_log.schema.json`.

**Required Fields:**
- `error_code`: Standardized error code (e.g., `ERR_CONTRACT_MISMATCH`)
- `timestamp`: ISO 8601 timestamp
- `severity`: CRITICAL | ERROR | WARNING | INFO
- `function`: Fully qualified function name
- `message`: Human-readable description
- `context`: Structured error context
  - `key`: Parameter/field that failed
  - `needed`: Expected type/value
  - `got`: Actual value received
  - `index`: (Optional) Index in collection
  - `file`: (Optional) Source file
  - `line`: (Optional) Line number

### Standard Error Codes

| Code | Description | Severity | Example |
|------|-------------|----------|---------|
| `ERR_CONTRACT_MISMATCH` | Required parameter missing or violates contract | ERROR | Missing pdq_context in evidence |
| `ERR_TYPE_VIOLATION` | Type mismatch (expected float, got string) | ERROR | confidence="high" instead of 0.85 |
| `ERR_SCHEMA_VALIDATION` | JSON schema validation failure | ERROR | Invalid questionnaire.json structure |
| `ERR_MISSING_REQUIRED_FIELD` | Required field absent from data structure | ERROR | Missing 'elements' in evidence |
| `ERR_INVALID_MODALITY` | Unknown or invalid modality type | ERROR | modality="TYPE_X" |
| `ERR_DETERMINISM_VIOLATION` | Non-deterministic behavior detected | CRITICAL | Different results with same seed |

### Example Log Entries

#### ERR_CONTRACT_MISMATCH

```json
{
  "error_code": "ERR_CONTRACT_MISMATCH",
  "timestamp": "2024-10-30T02:21:27.988Z",
  "severity": "ERROR",
  "function": "embedding_policy._filter_by_pdq",
  "message": "Contract violation: required parameter 'pdq_context' is missing",
  "context": {
    "key": "pdq_context",
    "needed": true,
    "got": null,
    "index": 0,
    "file": "embedding_policy.py",
    "line": 142
  },
  "remediation": "Ensure pdq_context is provided in the evidence dictionary",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### ERR_TYPE_VIOLATION

```json
{
  "error_code": "ERR_TYPE_VIOLATION",
  "timestamp": "2024-10-30T02:21:28.123Z",
  "severity": "ERROR",
  "function": "scoring.apply_scoring",
  "message": "Type violation: expected float for 'confidence', got string",
  "context": {
    "key": "confidence",
    "needed": "float",
    "got": "high",
    "file": "scoring/scoring.py",
    "line": 234
  },
  "remediation": "Convert confidence value to float between 0.0 and 1.0"
}
```

### Logging Implementation

Use the `ContractErrorLogger` utility class:

```python
from validation.contract_logger import ContractErrorLogger

logger = ContractErrorLogger(module_name="scoring")

# Log a contract mismatch
logger.log_contract_mismatch(
    function="apply_scoring",
    key="confidence",
    needed="float",
    got=evidence.get("confidence"),
    file=__file__,
    line=234,
    remediation="Convert confidence to float between 0.0 and 1.0"
)
```

### Monitoring and Alerting

Contract errors are:
1. **Logged to stdout/stderr** in JSON format (one line per error)
2. **Indexed by log aggregation** (e.g., CloudWatch, Datadog)
3. **Alerted on** when error rate exceeds threshold
4. **Tracked in metrics** for dashboard visualization

**Alert Thresholds:**
- `ERR_CONTRACT_MISMATCH` rate >1% of requests → Page on-call
- `ERR_DETERMINISM_VIOLATION` count >0 → Immediate page
- `ERR_TYPE_VIOLATION` rate >5% → Warning notification

### Validation

Validate log output against schema:

```bash
# Validate log file conforms to schema
python tools/validation/validate_error_logs.py \
    --log-file logs/contract_errors.jsonl \
    --schema schemas/contract_error_log.schema.json

# Expected output: Number of valid/invalid entries, list of schema violations
```

This validation runs in CI when log files are committed to the repository.
