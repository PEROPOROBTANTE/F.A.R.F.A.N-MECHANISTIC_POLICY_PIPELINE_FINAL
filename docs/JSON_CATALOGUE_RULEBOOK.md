# JSON Catalogue Rulebook

This rulebook is the zero-to-one orientation for newcomers who need to understand, extend, or audit the data contracts that drive the evaluation system. Treat it as the source of truth for how the catalogue of JSON assets is governed, how they relate to one another, and the workflow required to keep them aligned.

## 1. Canonical Artefacts and Their Roles

| Asset | Scope | Source of Truth Fields | Downstream Dependencies |
|-------|-------|------------------------|-------------------------|
| `questionnaire.json` | 300-question data contract that encodes clusters, policy areas, dimensions, evidence taxonomy, and question payloads | `version`, `content_hash`, `metadata.*`, `questions[*]` | `rubric_scoring.json`, `question_component_map.json`, execution mapping, semantic processors |
| `rubric_scoring.json` | Scoring contract governing weights, penalties, modalities, and NA rules | `requires_questionnaire_version`, `rubric_matrix`, `na_rules`, `penalties` | Report assembly, `schemas/rubric_scoring.schema.json`, recommendation logic |
| `question_component_map.json` | Alignment index between questionnaire, components, and method inventory | `metadata`, `architecture`, `dimension_mappings`, `execution_flow` | `interaction_matrix.csv`, orchestration strategies, onboarding playbooks |
| `inventory.json` | Exhaustive code inventory for the nine producer/preprocessor/aggregator files | `statistics`, `files[*].classes[*]`, `files[*].methods` | `COMPLETE_METHOD_CLASS_MAP.json`, staffing metrics, regression planning |
| `interaction_matrix.csv` | Component interaction topology with dimension coverage and cross-validation rules | Component row metadata, interaction lists | Orchestrator routing, execution planning, integration dashboards |
| `COMPLETE_METHOD_CLASS_MAP.json` | Per-class/per-method accounting including integration targets | `metadata`, `summary`, `files.*.classes` | Integration OKRs, semantic chunking roadmap, onboarding audits |
| `schemas/*.schema.json` | JSON Schema contracts that enforce structure for questionnaire, rubric, segmentation, and execution artefacts | `$id`, `required`, `$defs` blocks | `schema_validator.py`, linting, downstream producers |
| `cuestionario_FIXED.json` | Frozen legacy questionnaire kept only for backward compatibility checks | `metadata.deprecated`, `replacement`, `deprecation_reason` | Historical migrations, legacy diff tooling |

## 2. Global Governance Principles

1. **Semantic versioning and hashing are mandatory.** Every live configuration (`questionnaire.json`, `rubric_scoring.json`, execution mappings) must expose a `version` that follows `MAJOR.MINOR.PATCH` and a 64-character `content_hash`. Validation will fail if hashes diverge from the canonical payloads. 【F:docs/DATA_CONTRACTS.md†L5-L33】
2. **Questionnaire alignment is the reference axis.** The questionnaire anchors counts and identifiers: it declares 4 clusters, 6 dimensions (`DIM01`–`DIM06`), and 10 policy areas bound to legacy IDs. 【F:questionnaire.json†L1-L160】 All derivative artefacts must reference those identifiers exactly.
3. **Inventory totals define the integration baseline.** Both `inventory.json` and `question_component_map.json` enumerate 9 files, 82 classes, and 416 methods. Any change to the codebase must keep these totals in sync or explain the delta. 【F:inventory.json†L1-L120】【F:question_component_map.json†L1-L29】
4. **Determinism, NA behaviour, and penalties stay centralised.** The rubric governs NA rules, penalty weights, and deterministic modality configuration; do not repeat that logic elsewhere. 【F:docs/DATA_CONTRACTS.md†L15-L33】
5. **Schema-first development.** Every structural change starts by updating the relevant schema under `schemas/`. Schemas forbid additional properties, enforce enum patterns, and express minimum counts, so widening structure without schema updates will fail CI. 【F:schemas/questionnaire.schema.json†L1-L200】
6. **Validation is non-negotiable.** Run the full validator, cross-reference check, and JSON linting before committing. CI will repeat these checks. 【F:docs/DATA_CONTRACTS.md†L21-L35】

## 3. File-by-File Operating Rules

### 3.1 `questionnaire.json`
- **Purpose:** Master definition of the policy evaluation questionnaire, including internationalised labels, evidence keys, and 300 questions (not shown here in full for brevity). 【F:questionnaire.json†L1-L160】
- **Identifiers:** Use atomic IDs—`PAxx` for policy areas, `DIMxx` for dimensions, and `Qxxx` for questions. Never resurrect `P#/D#/Q#` identifiers except in `provenance.legacy` blocks.
- **Evidence taxonomy:** `metadata.sources_of_verification` enumerates the only valid `required_evidence_keys`. Adding a new source requires schema updates and rubric alignment.
- **Changelog discipline:** Append to `changelog` with human-readable `summary` and keep `version`/`content_hash` in lockstep with modifications.
- **Language coverage:** All labels must provide both Spanish and English entries; schema-enforced i18n prevents single-language additions. 【F:schemas/questionnaire.schema.json†L24-L200】

### 3.2 `rubric_scoring.json` and `schemas/rubric_scoring.schema.json`
- **Compatibility lock:** `requires_questionnaire_version` must equal the questionnaire’s `version`. Bump the rubric’s version whenever the questionnaire changes, even if weights remain stable.
- **NA rules and penalties:** Centralise NA defaults, critical failure thresholds, and penalty weights here. Consumers read only this file for such constants; delete redundant copies elsewhere.
- **Modalities:** Ensure each scoring modality defined in the schema has complete aggregation, uncertainty, and recommendation rules before exposing it downstream. 【F:schemas/rubric_scoring.schema.json†L1-L120】
- **Validation:** Run `python tools/lint/json_lint.py rubric_scoring.json --schema schemas/rubric_scoring.schema.json` after edits. 【F:docs/DATA_CONTRACTS.md†L21-L33】

### 3.3 `question_component_map.json`
- **Metadata parity:** Keep `total_methods`, `total_questions`, and `total_components` accurate; they are audited against `inventory.json` and orchestration dashboards. 【F:question_component_map.json†L1-L29】
- **Component definitions:** Each entry under `architecture.producers`/`architecture.preprocessors` must match the file paths from `inventory.json`. Adding a new component requires updating the inventory, interaction matrix, and execution mapping.
- **Dimension coverage:** `dimension_mappings` must list all `PAxx` × `DIMxx` touchpoints used by the components; mismatches signal missing coverage.
- **Execution flow:** Maintain the `execution_flow` arrays when wiring new orchestration phases to ensure the choreographer reflects actual sequencing.

### 3.4 `inventory.json`
- **Scope:** Enumerates every class and method inside the nine canonical files, including adapters, data classes, and utilities. 【F:inventory.json†L1-L120】
- **Update workflow:** Regenerate via `python inventory_generator.py` whenever classes or methods change. Never hand-edit counts; rely on automated extraction.
- **Role tagging:** Preserve `role` (`data_producer`, `preprocessor`, `aggregator`) for staffing and routing logic. Verify that any new file introduced elsewhere is either added here or explicitly excluded.
- **Method enumeration:** Keep method lists exhaustive for main classes (e.g., `PDETMunicipalPlanAnalyzer`); downstream integration tests rely on these lists for coverage assertions. 【F:inventory.json†L12-L120】

### 3.5 `interaction_matrix.csv`
- **Structure:** Rows represent components, columns encode dimension strength (LOW/MEDIUM/HIGH), modality alignment (MICRO/MESO/MACRO), and cross-validation partners. 【F:interaction_matrix.csv†L1-L20】
- **Synchronization rules:** When method counts or roles change in `question_component_map.json`, update the matrix to mirror new method totals, interaction tags, and partner lists.
- **CSV hygiene:** Keep the header exactly as defined; orchestration loaders expect those column names. Use quoted comma-separated lists for primary and secondary interactions.

### 3.6 `COMPLETE_METHOD_CLASS_MAP.json`
- **Purpose:** Deep audit referencing totals, integration targets, and per-class method counts. 【F:COMPLETE_METHOD_CLASS_MAP.json†L1-L120】
- **Integration targets:** Maintain `integration_target` (currently `95% minimum`) and `integration_target_methods`. Update both when scope expands to avoid false positives in OKR dashboards.
- **Class detail:** For each file, ensure `method_count` matches the length of the enumerated list. Automated diff scripts verify these counts.
- **Key file callouts:** The `summary.key_file` flag highlights the highest leverage file (currently `derek_beach.py` with 99 methods); adjust if ownership shifts.

### 3.7 `cuestionario_FIXED.json`
- **Status:** Marked `"deprecated": true` with `replacement` pointing to `questionnaire.json`. 【F:cuestionario_FIXED.json†L1-L90】
- **Usage:** Do not edit except to document deprecation metadata. Any fixes belong in the atomic questionnaire; leave this file untouched for regression comparisons.
- **Automation:** Legacy tooling may still diff against this payload—if removal is desired, coordinate with the migration script owners first.

### 3.8 Execution and Segmentation Schemas
- **`schemas/question_segmentation.schema.json`:** Validates segmentation outputs with required `metadata`, `question_segment_index`, and `question_segments`. Use it for NLP pre-processing deliverables. 【F:schemas/question_segmentation.schema.json†L1-L120】
- **`schemas/execution_step.schema.json`:** Defines structure for each execution step (`step_id`, `fq_method`, `inputs`, `artifacts_in/out`, `evidence_contract`). Keep this aligned with actual orchestrator step outputs to avoid runtime validation errors. 【F:schemas/execution_step.schema.json†L1-L120】
- **`schemas/execution_mapping.schema.json`:** Governs the full execution mapping, including modules, observability hooks, scoring modalities, and thresholds. Edit this first when wiring new modules or modalities so configuration diffs fail fast. 【F:schemas/execution_mapping.schema.json†L1-L120】
- **`schemas/rubric.schema.json`:** Describes macro/meso structures and chess phases used by higher-level scoring frameworks. Any adjustment to strategic weights must happen here before touching downstream YAML/JSON. 【F:schemas/rubric.schema.json†L1-L120】

## 4. Change Management Workflow

1. **Design the change:** Update schema(s) to reflect new structure or constraints.
2. **Regenerate derived artefacts:** Use automation (inventory generator, migration scripts) rather than manual edits to keep counts authoritative.
3. **Update dependent files in lockstep:** For example, adding a new method requires touching `inventory.json`, `question_component_map.json`, `interaction_matrix.csv`, and `COMPLETE_METHOD_CLASS_MAP.json` in the same commit.
4. **Refresh hashes and versions:** Compute new `content_hash` values and bump semantic versions when any payload changes.
5. **Run the validation suite:** Execute `python schema_validator.py`, `python tools/integrity/check_cross_refs.py`, and targeted `json_lint` invocations. 【F:docs/DATA_CONTRACTS.md†L21-L35】
6. **Document the change:** Update this rulebook or `docs/DATA_CONTRACTS.md` when governance rules evolve so newcomers always see the latest authority.

## 5. Onboarding Checklist for New Contributors

- [ ] Read this rulebook end-to-end and skim the relevant schema(s).
- [ ] Familiarise yourself with the questionnaire metadata (clusters, dimensions, policy areas). 【F:questionnaire.json†L1-L160】
- [ ] Inspect `inventory.json` to understand the code surface area and key classes. 【F:inventory.json†L1-L120】
- [ ] Trace your component through `question_component_map.json` and `interaction_matrix.csv` to see its orchestration context. 【F:question_component_map.json†L1-L29】【F:interaction_matrix.csv†L1-L20】
- [ ] Run the validation suite locally before proposing any change. 【F:docs/DATA_CONTRACTS.md†L21-L35】

Treat these artefacts as a single contract: if one changes, audit them all. That discipline keeps questionnaire-aligned tooling deterministic and auditable for every release.
