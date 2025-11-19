# Wiring & Contract Canonical Audit

## Executive Summary
- **Objective**: verify that the modo wiring fino stack (`src/saaaaaa/core/wiring`) and the contract-enforcement program (`CONTRACT_ENFORCEMENT_COMPLETE.md`) satisfy canonical guarantees: explicit links, deterministic bootstrap, envelope-ready contracts, and cryptographic evidence.
- **Method**: reviewed wiring bootstrap + validation modules, the eight deliverable→expectation pairs, determinism/logging infrastructure, and the eleven contract-enforcement sections plus CI coverage. Cross-referenced supporting artifacts (`docs/WIRING_ARCHITECTURE.md`, `WIRING_SYSTEM_README.md`, `SPC_STRUCTURE_COMPATIBILITY_ANALYSIS.md`, CI manifests, and tests).
- **Result**: all wiring links map to validated contract pairs with deterministic hashing + observability; contract infrastructure is 92 % complete (11/12 sections) with the runner integration pending. Evidence is stored in repo artifacts (certificates, manifests, CI logs) and can be re-run via the listed commands.

## Scope & Inputs
| Asset | Purpose |
| --- | --- |
| `src/saaaaaa/core/wiring/{bootstrap,contracts,validation,observability}.py` | Wiring initialization, contract schemas, validators, and tracing |
| `docs/WIRING_ARCHITECTURE.md`, `WIRING_SYSTEM_README.md` | Canonical wiring description (modo wiring fino) |
| `CONTRACT_ENFORCEMENT_COMPLETE.md`, `CONTRACT_ENFORCEMENT_PROGRESS.md` | Enforcement roadmap + completion evidence |
| `SPC_STRUCTURE_COMPATIBILITY_ANALYSIS.md`, `METHOD_REGISTRATION_POLICY.md` | Terminology migration + method registry rules |
| Tests `tests/test_wiring_core.py`, `tests/test_wiring_e2e.py`, `tests/test_determinism.py`, CI workflows | Execution evidence |

## Phase 0 – Canonical Inventory & Baseline Capture
- **Goal**: prove that every wiring/contract asset is registered, immutable, and tied to canonical language.
- **Actions**:
  - Confirmed the nine-phase initialization order and prohibition rules (`docs/WIRING_ARCHITECTURE.md`, §Overview/Design Principles) and the canonical quick-start in `WIRING_SYSTEM_README.md`.
  - Captured inventory of 9 port definitions, 16 Pydantic contract models, 6 typed errors, 7 feature flags, and the bootstrap/observability stack (see “Components” table in `WIRING_SYSTEM_README.md`).
  - Verified provenance trail in `provenance.csv` and contract-specific docs (`SPC_STRUCTURE_COMPATIBILITY_ANALYSIS.md`, `METHOD_REGISTRATION_POLICY.md`).
- **Outcome**: baseline asset list is canonized; any delta can be diffed against this inventory.

## Phase 1 – Wiring Bootstrap Integrity
- **Goal**: ensure deterministic creation of the wiring graph (factory, signal system, ArgRouter, validators).
- **Evidence**:
  - `src/saaaaaa/core/wiring/bootstrap.py` follows the nine deterministic steps (resource load → signal system → executor config → factory → registry → ArgRouter → validator → signal seeding → hash computation). Each step maps to the documentation phases listed in `docs/WIRING_ARCHITECTURE.md`.
  - Feature flags (`feature_flags.py`) lock strict mode, determinism, and observability defaults.
  - Observability instrumentation (`observability.py`) emits OpenTelemetry spans + structured logs, turning tracing into structural requirement.
  - Validation harness (`scripts/validate_wiring_system.py`, cited in the README) is available for reproducible bootstrap checks.
- **Status**: bootstrap is canonical; no mutable global state or YAML fallbacks remain. Hashes (BLAKE3) provide drift detection.

## Phase 2 – Link Contract Validation (8 Wiring Links)
- **Goal**: verify that each i→i+1 link uses deliverable and expectation contracts validated by `LinkValidator`.
- **Implementation**: `src/saaaaaa/core/wiring/validation.py` instantiates eight validators and enforces deliverable schema → expectation schema → deterministic hash (+ metrics). Failures raise `WiringContractError` with prescriptive fixes.
- **Contract Table**:

| Link | Deliverable | Expectation | Highlights / Evidence |
| --- | --- | --- | --- |
| CPP Ingestion → Adapter | `CPPDeliverable` / `SPCDeliverable` | `AdapterExpectation` | Requires `chunk_graph`, `policy_manifest`, and `provenance_completeness==1.0`; validator `validate_cpp_to_adapter()` |
| Adapter → Orchestrator | `PreprocessedDocumentDeliverable` | `OrchestratorExpectation` | Sentence metadata + document_id enforcement |
| Orchestrator → ArgRouter | `ArgRouterPayloadDeliverable` | `ArgRouterExpectation` | Class/method/payload validation ensuring registry coverage |
| ArgRouter → Executors | `ExecutorInputDeliverable` | (implicit via executor validators) | Validates args/kwargs/method_signature; deterministic method dispatch |
| Signals Client → Registry | `SignalPackDeliverable` | `SignalRegistryExpectation` | Version/policy_area requirements; version guarding validator |
| Executors → Aggregate | `EnrichedChunkDeliverable` | `AggregateExpectation` | Requires chunk_id, enrichment payload, ≥1 chunk |
| Aggregate → Score | `FeatureTableDeliverable` | `ScoreExpectation` | Table type + column requirements (PyArrow) |
| Score → Report | `ScoresDeliverable` | `ReportExpectation` | Polars DataFrame + manifest flag; ensures reporting completeness |

- **Testing**: `tests/test_wiring_core.py` (23 unit tests) and `tests/test_wiring_e2e.py` backstop validation logic; `WIRING_SYSTEM_README.md` documents the pass count and how to run them.

## Phase 3 – Contract-Enforcement Program (11/12 Sections Complete)
- **Goal**: confirm that the broader contract hardening initiative aligns to canonical sections with traceable evidence (`CONTRACT_ENFORCEMENT_COMPLETE.md`).
- **Completed Sections** (all ✅):
  1. **CPP→SPC Migration** – adapter rename, deprecation shim, 18 ingestion models, policy/method docs, guardrail fixes.
  2. **Seed Management + Determinism** – `seed_registry.py`, SHA256 derivation, component-specific seeds, audit log, 18 test cases.
  3. **ExecutorConfig Enforcement** – mandatory configs, validation, config hashing, propagation through 34 executors.
  4. **Calibration Contract Enforcement** – version compatibility, manifest integration, fail-fast behavior.
  5. **Method Sequence Validation** – `METHOD_SEQUENCE` declarations, runtime tracking, manifest logging.
  6. **Signal Registry Integration** – explicit registry requirement, deterministic signal usage logging.
  7. **Advanced Module Configuration** – frozen configs with citations + activation tracking.
  8. **Ingestion Contract Hardening** – SPC-only enforcement, logging, metadata capture.
  9. **Verification Manifest Contract** – schema + builder, HMAC integrity, environment capture.
  10. **CI Contract Enforcement** – documented `contract-enforcement.yml` + `determinism-test.yml` jobs (per completion report) covering METHOD_SEQUENCE, calibration versions, seed propagation, and manifest checks.
  11. **Rollback Safety & Versioning** – `versions.py`, compatibility helpers, manifest exports.
- **Pending Section 12**: integrate seed registry + manifest output with `run_policy_pipeline_verified.py` and emit `PIPELINE_VERIFIED=1`. Estimated effort 1–2 h (per completion doc). No other gaps.

## Phase 4 – Determinism, Observability & Envelope Readiness
- **Goal**: prove deterministic execution and auditable IO for every phase.
- **Determinism**: `seed_registry.py` supplies per-component seeds; `tests/test_determinism.py` exercises reproducibility, RNG context managers, and manifest hashing. Deterministic contexts (see `ContractEnvelope` guide) replace ambient randomness.
- **Observability**: `WIRING_SYSTEM_README.md` and `ContractEnvelope` guide enforce structured logging via `log_io_event()` with policy/correlation IDs, digests, and latency. `observability.py` ensures OpenTelemetry spans for each link.
- **Envelope Integration**: `CONTRACT_ENVELOPE_INTEGRATION.md` prescribes wrapping FLUX phases and executors to carry canonical metadata, gradually migrating to envelope-only APIs without breaking compatibility.

## Phase 5 – Evidence, Certification & CI Hooks
- **Artifacts**:
  - `EXECUTOR_WIRING_CERTIFICATION.txt`, `ARCHITECTURE_COMPLIANCE_CERTIFICATE.txt`, `AUDIT_COMPLIANCE_REPORT.md` (macro certification trail).
  - Machine-readable reports (`AUDIT_DRY_RUN_REPORT.json`, `ARCHITECTURE_AUDIT_REPORT.json`) plus human summaries.
  - CI hooks: existing `.github/workflows/path-audit.yml`, `questionnaire_integrity.yml`, and `pyre.yml`, plus the contract/determinism workflows specified in `CONTRACT_ENFORCEMENT_COMPLETE.md` ready for inclusion.
  - Tests and scripts enumerated in README sections (pytest targets and `scripts/validate_wiring_system.py`).
- **Re-Run Guidance**:
  - `pytest tests/test_wiring_core.py -v`
  - `pytest tests/test_wiring_e2e.py -v`
  - `pytest tests/test_determinism.py -v`
  - `./scripts/validate_wiring_system.py`
  - `python -m saaaaaa.core.orchestrator.verification_manifest --validate manifest.json`

## Residual Work & Canonical Next Steps
1. **Pipeline Runner Integration** – wire `SeedRegistry` + `VerificationManifest` into `run_policy_pipeline_verified.py`, emit `PIPELINE_VERIFIED=1`, capture calibration/ingestion/signal metadata.
2. **Audit Automation Loop** – schedule `scripts/validate_wiring_system.py` + determinism suite in CI nightly to guard against regressions in wiring contracts.
3. **Envelope-Only Cutover** – flip consumers to `ContractEnvelope` outputs exclusively once downstream tooling is ready; update manifest schema version accordingly.
4. **Certification Refresh** – after Section 12 merges, regenerate `ARCHITECTURE_COMPLIANCE_CERTIFICATE.txt` / `EXECUTOR_WIRING_CERTIFICATION.txt` to capture the final canonical state.

This audit canonically links wiring assets, contract enforcement stages, and their verification evidence so subsequent reviews can diff against a formally captured baseline.
