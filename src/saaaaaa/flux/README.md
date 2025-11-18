# FLUX Pipeline

**Fine-grained, Deterministic Processing Pipeline**

FLUX is a production-grade pipeline system with explicit contracts, typed configurations, deterministic execution, and comprehensive quality gates. Designed for Python 3.12+ with modern tooling.

## Features

### Core Principles

1. **Explicit Contracts**: Every phase defines clear `Deliverable` and `Expectation` types. Runtime validation ensures compatibility.

2. **Deterministic Execution**: 
   - Single-thread per document
   - Seeded randomness
   - Blake3 fingerprinting for each phase
   - Stable ordering guarantees

3. **Type-Safe Configuration**:
   - Pydantic v2 frozen models
   - No YAML in runtime paths
   - Environment variable support
   - CLI parameterization with Typer

4. **Runtime Validation**:
   - Preconditions (`requires:`)
   - Postconditions (`ensures:`)
   - Typed exceptions with actionable messages

5. **Observability**:
   - OpenTelemetry traces and metrics
   - Structlog structured logging
   - Per-phase metrics and fingerprints

## Architecture

### Integration with SPC Phase-One

**IMPORTANT**: FLUX phases are complementary to SPC (Smart Policy Chunks) Phase-One ingestion.

**Canonical Entry Point**: Use `CPPIngestionPipeline` from `saaaaaa.processing.spc_ingestion` for document ingestion. SPC is the ONLY authorized Phase-One system.

**FLUX Role**: FLUX provides downstream processing phases that consume SPC output:

### Pipeline Phases

1. ~~**Ingest**~~: **REMOVED** - Use SPC `CPPIngestionPipeline` instead
2. **Normalize**: Unicode normalization and sentence segmentation (receives `IngestDeliverable` from SPC or external source)
3. **Chunk**: Multi-resolution chunking (micro/meso/macro)
4. **Signals**: Cross-cutting pattern enrichment
5. **Aggregate**: Feature engineering with PyArrow
6. **Score**: Multi-metric scoring with Polars
7. **Report**: Artifact generation and provenance

### Typical Usage Pattern

```python
# Phase-One: SPC Ingestion (CANONICAL ENTRY POINT)
from saaaaaa.processing.spc_ingestion import CPPIngestionPipeline
from pathlib import Path

pipeline = CPPIngestionPipeline()
cpp_result = await pipeline.process(
    document_path=Path("policy.pdf"),
    document_id="POL-2024-001",
    title="Plan Nacional 2024"
)

# cpp_result is now a CanonPolicyPackage with:
# - chunks[], chunk_graph, quality_metrics, provenance_map

# Phase-Two+: FLUX Processing (OPTIONAL)
from saaaaaa.flux import run_normalize, NormalizeConfig
from saaaaaa.flux.models import IngestDeliverable, DocManifest

# Convert SPC output to FLUX input if needed
ing = IngestDeliverable(
    manifest=DocManifest(document_id=cpp_result.manifest.document_id),
    raw_text=cpp_result.get_full_text(),  # or use chunks
    provenance_ok=True
)

# Run FLUX normalize phase
normalize_cfg = NormalizeConfig(unicode_form="NFC", keep_diacritics=True)
norm_result = run_normalize(normalize_cfg, ing, policy_unit_id="POL-2024-001")

# Continue with chunk, signals, aggregate, score, report as needed
```

### Phase Contracts

Each phase `i → i+1` has explicit handoff:

```
IngestDeliverable       → NormalizeExpectation
NormalizeDeliverable    → ChunkExpectation
ChunkDeliverable        → SignalsExpectation
SignalsDeliverable      → AggregateExpectation
AggregateDeliverable    → ScoreExpectation
ScoreDeliverable        → ReportExpectation
```

Validated at runtime with `assert_compat(deliverable, expectation_cls)`.

## Installation

### Dependencies

```bash
# Core dependencies (pinned)
pip install pydantic==2.5.3 typer==0.15.1 polars==1.17.1 pyarrow==18.1.0
pip install structlog==24.4.0 blake3==0.4.1 tenacity==9.0.0
pip install opentelemetry-api==1.28.2 opentelemetry-sdk==1.28.2

# Development
pip install pytest==7.4.3 hypothesis==6.92.2 mypy==1.0.0
```

### From Source

```bash
cd src/saaaaaa/flux
python -m pip install -e .
```

## Usage

### Python API

```python
from saaaaaa.flux import (
    IngestConfig,
    NormalizeConfig,
    ChunkConfig,
    run_ingest,
    run_normalize,
    run_chunk,
)

# Configure phases
ingest_cfg = IngestConfig(enable_ocr=True)
normalize_cfg = NormalizeConfig(unicode_form="NFC")
chunk_cfg = ChunkConfig(priority_resolution="MESO")

# Execute pipeline
ingest_out = run_ingest(ingest_cfg, input_uri="doc.pdf")
ingest_del = IngestDeliverable.model_validate(ingest_out.payload)

normalize_out = run_normalize(normalize_cfg, ingest_del)
normalize_del = NormalizeDeliverable.model_validate(normalize_out.payload)

chunk_out = run_chunk(chunk_cfg, normalize_del)
# ... continue through phases
```

### CLI

```bash
# Run full pipeline
python -m saaaaaa.flux.cli run input.pdf

# Dry run (validation only)
python -m saaaaaa.flux.cli run input.pdf --dry-run

# Print contracts
python -m saaaaaa.flux.cli contracts

# Validate configs from environment
python -m saaaaaa.flux.cli validate-configs

# Custom parameters
python -m saaaaaa.flux.cli run input.pdf \
  --ingest-enable-ocr true \
  --normalize-unicode-form NFC \
  --chunk-priority-resolution MESO \
  --score-metrics precision,coverage,risk
```

### Environment Configuration

All config parameters can be set via environment:

```bash
export FLUX_INGEST_ENABLE_OCR=true
export FLUX_INGEST_OCR_THRESHOLD=0.85
export FLUX_NORMALIZE_UNICODE_FORM=NFC
export FLUX_CHUNK_PRIORITY_RESOLUTION=MESO
export FLUX_AGGREGATE_GROUP_BY=policy_area,year
export FLUX_SCORE_METRICS=precision,coverage,risk
export FLUX_REPORT_FORMATS=json,md

python -m saaaaaa.flux.cli run input.pdf
```

## Quality Gates

FLUX includes comprehensive quality gates:

1. **Compatibility Gate**: All phase transitions pass `assert_compat`
2. **Determinism Gate**: Identical inputs → identical fingerprints
3. **No-YAML Gate**: Zero YAML reads in runtime
4. **Type Gate**: Strict mypy/pyright (no `Any`, no ignores)
5. **Secret Scan Gate**: No secrets in code
6. **Coverage Gate**: Test coverage ≥ threshold

```python
from saaaaaa.flux.gates import QualityGates

# Run all gates
gate_results = QualityGates.run_all_gates(
    phase_outcomes=outcomes,
    run1_fingerprints=fp1,
    run2_fingerprints=fp2,
    source_paths=[Path("src/saaaaaa/flux")],
    mypy_output=mypy_result,
    coverage_percentage=85.0,
)

# Emit checklist
checklist = QualityGates.emit_checklist(gate_results, fingerprints)
# {
#   "contracts_ok": true,
#   "determinism_ok": true,
#   "gates": {...},
#   "fingerprints": {...}
# }
```

## Testing

### Unit & Contract Tests

```bash
pytest tests/test_flux_contracts.py -v
```

Includes:
- Compatibility validation
- Precondition/postcondition checks
- Determinism verification
- Config validation

### Property-Based Tests

```bash
pytest tests/test_flux_contracts.py::TestPropertyBasedContracts -v
```

Uses Hypothesis for:
- Fingerprint uniqueness
- Sentence count preservation
- Chunk count invariants

### Integration Tests

```bash
pytest tests/test_flux_integration.py -v
```

Covers:
- Full pipeline execution
- Quality gates
- CLI commands
- Error handling

## Configuration Reference

### IngestConfig

```python
IngestConfig(
    enable_ocr: bool = True,
    ocr_threshold: float = 0.85,
    max_mb: int = 250,
)
```

### NormalizeConfig

```python
NormalizeConfig(
    unicode_form: Literal["NFC", "NFKC"] = "NFC",
    keep_diacritics: bool = True,
)
```

### ChunkConfig

```python
ChunkConfig(
    priority_resolution: Literal["MICRO", "MESO", "MACRO"] = "MESO",
    overlap_max: float = 0.15,
    max_tokens_micro: int = 400,
    max_tokens_meso: int = 1200,
)
```

### SignalsConfig

```python
SignalsConfig(
    source: Literal["memory", "http"] = "memory",
    http_timeout_s: float = 3.0,
    ttl_s: int = 3600,
    allow_threshold_override: bool = False,
)
```

### AggregateConfig

```python
AggregateConfig(
    feature_set: Literal["minimal", "full"] = "full",
    group_by: list[str] = ["policy_area", "year"],
)
```

### ScoreConfig

```python
ScoreConfig(
    metrics: list[str] = ["precision", "coverage", "risk"],
    calibration_mode: Literal["none", "isotonic", "platt"] = "none",
)
```

### ReportConfig

```python
ReportConfig(
    formats: list[str] = ["json", "md"],
    include_provenance: bool = True,
)
```

## Error Handling

FLUX uses typed exceptions with actionable messages:

### PreconditionError

```python
raise PreconditionError(
    phase="run_ingest",
    condition="non-empty input_uri",
    message="input_uri must be a non-empty string"
)
```

### PostconditionError

```python
raise PostconditionError(
    phase="run_normalize",
    condition="non-empty sentences",
    message="Must produce at least one sentence"
)
```

### CompatibilityError

```python
raise CompatibilityError(
    source="IngestDeliverable",
    target="NormalizeExpectation",
    validation_error=ve
)
```

## Examples

See `examples/flux_demo.py` for a complete demonstration.

## Development

### Type Checking

```bash
mypy src/saaaaaa/flux --strict
pyright src/saaaaaa/flux
```

### Linting

```bash
ruff check src/saaaaaa/flux
black --check src/saaaaaa/flux
```

### Coverage

```bash
pytest tests/test_flux*.py --cov=src/saaaaaa/flux --cov-report=html
```

## Design Decisions

1. **Why frozen configs?** Immutability prevents accidental state mutation during pipeline execution.

2. **Why Blake3?** Faster than SHA256 with same security properties, optimized for modern CPUs.

3. **Why Polars/PyArrow?** Columnar data structures enable efficient aggregation at scale.

4. **Why no YAML?** Runtime YAML parsing adds dependencies and complexity. Code-based config is type-safe and explicit.

5. **Why Tenacity?** Declarative retry policies with exponential backoff for transient failures.

## Non-Goals

- Network calls from executors (use dependency injection)
- Mutable global state
- Probabilistic heuristics without seeds
- Schema drift without version bump
- Implicit configuration from files

## License

See repository root for license information.

## Contributing

See CONTRIBUTING.md for guidelines.
