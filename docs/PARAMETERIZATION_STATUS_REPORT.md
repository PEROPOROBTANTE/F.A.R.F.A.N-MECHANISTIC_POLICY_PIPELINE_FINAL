# PARAMETERIZATION STATUS REPORT
## F.A.R.F.A.N Mechanistic Policy Pipeline

**Report Date:** 2025-11-25
**Constitution Version:** 1.0.0
**Report Type:** Constitution-Bound Status Report
**Jobfront:** JOBFRONT 3B – PARAMETERIZATION STATUS REPORT

---

## 🔒 CONSTITUTIONAL AUTHORITY

**This report is bound to `config/PARAMETERIZATION_CONSTITUTION.json` version 1.0.0.**

All artifact classifications, invariants, and governance rules in this report are derived directly from the constitution. This is not a free interpretation—it is a faithful rendering of constitutional truth.

**Repository Mode:** `STRICT`

In STRICT mode:
- All artifacts must be listed in `normative_artifacts` to be treated as source of truth
- Invariants are immutable without source report regeneration
- All changes require constitutional process with full audit trail

---

## ⚠️ CRITICAL RUNTIME PARAMETER SOURCE DECLARATION

**FOR CALIBRATION AND EXECUTORS, THE ONLY RUNTIME SOURCE OF PARAMETER VALUES IS:**

**`config/method_parameters.json` accessed through `MethodParameterLoader`**

**`CANONICAL_METHOD_PARAMETERIZATION_SPEC.json` and `MethodConfigLoader` ARE UPSTREAM DESIGN ARTIFACTS. THEY MUST NEVER BE USED BY CALIBRATION OR EXECUTOR CODE AT RUNTIME.**

These design artifacts were part of the parameterization audit (JOBFRONT phases 1-2) and informed the creation of `config/method_parameters.json`, but they are NOT runtime configuration. Any runtime code that attempts to load from `CANONICAL_METHOD_PARAMETERIZATION_SPEC.json` or use `MethodConfigLoader` is in violation of the architectural boundary.

**Runtime Parameter Access Pattern:**
```python
from src.saaaaaa.core.calibration.parameter_loader import MethodParameterLoader

# CORRECT: Use MethodParameterLoader
loader = MethodParameterLoader("config/method_parameters.json")
threshold = loader.get_executor_threshold("D1Q1_Executor")

# INCORRECT: Never use MethodConfigLoader or CANONICAL_METHOD_PARAMETERIZATION_SPEC.json
# These are design artifacts, not runtime configuration
```

---

## 📋 NORMATIVE ARTIFACTS

**Definition:** Artifacts that serve as the source of truth for the system. Listed in `config/PARAMETERIZATION_CONSTITUTION.json` under `normative_artifacts`.

### Runtime Parameters (3 artifacts)

| Path | Role | Validation Status | Mode of Generation | Version | Authority | SHA256 (first 16) |
|------|------|-------------------|-------------------|---------|-----------|-------------------|
| `config/method_parameters.json` | runtime_parameters | VALIDATED | manual/mixed | 1.0.0 | PRIMARY | b6436fc5ad83d628 |
| `src/saaaaaa/core/calibration/parameter_loader.py` | runtime_parameters | VALIDATED | manual | unknown | PRIMARY | 938850132628da87 |
| `src/saaaaaa/core/calibration/base_layer.py` | runtime_parameters | VALIDATED | manual | unknown | PRIMARY | 44ef9578bec96544 |

**Notes:**
- **config/method_parameters.json**: Contains `_global_thresholds`, `_executor_thresholds` (30 executors), and method-specific parameters. Migration status: `initial_creation`. This is THE runtime source for all method parameters.
- **parameter_loader.py**: Thread-safe, lazy-loaded loader providing typed access via `get_quality_thresholds()`, `get_executor_threshold()`, `get_validation_threshold_for_role()`, `get_method_parameter()`, etc.
- **base_layer.py**: Base Layer (@b) evaluator that reads `config/intrinsic_calibration.json` and uses `MethodParameterLoader.get_base_layer_quality_thresholds()` for configurable thresholds.

### Structural Catalogue (2 artifacts)

| Path | Role | Validation Status | Mode of Generation | Version | Authority | SHA256 (first 16) |
|------|------|-------------------|-------------------|---------|-----------|-------------------|
| `canonical_method_catalogue_v2.json` | structural_catalogue | PENDING_VALIDATION | script | 2.0.0 | PRIMARY | 73975d1f5efcefc9 |
| `parameter_identification_report.md` | structural_catalogue | VALIDATED | script/manual | unknown | PRIMARY | e4e6cad652666f63 |

**Notes:**
- **canonical_method_catalogue_v2.json**: Built by `build_canonical_method_catalogue_v2.py`. Total 2,189 methods, 486 with defaults, 5,094 total parameters, 857 configurable. Coverage: 100%. Files parsed: 167. Parse errors: 0. **PENDING VALIDATION** (see Transitional Artifacts section).
- **parameter_identification_report.md**: Phases 1-2 parameter identification. Documents 283 methods identified with 462 total configurable parameters. Methods scanned: 2,189. Identified: 283. Generated: 2025-11-18T12:26:55.687512+00:00.

### Epistemic Audit (3 artifacts)

| Path | Role | Validation Status | Mode of Generation | Version | Authority | SHA256 (first 16) |
|------|------|-------------------|-------------------|---------|-----------|-------------------|
| `parameter_sources_comprehensive.md` | epistemic_audit | VALIDATED | script/manual | unknown | PRIMARY | 81f06b10df150ba8 |
| `parameter_sources.md` | epistemic_audit | VALIDATED | script | unknown | PRIMARY | COMPUTED_SEPARATELY |
| `PARAMETERIZATION_AUDIT_EXECUTIVE_SUMMARY.md` | epistemic_audit | VALIDATED | manual | 1.0.0 | PRIMARY | 93d38e9324e59b3a |

**Notes:**
- **parameter_sources_comprehensive.md**: Phase 3 parameter value determination report. Total parameters: 462. KB recommendations: 319 (69.0%). Code defaults: 143 (31.0%). Academic sources: 16. Library sources: 11. Standards: 10. Generated: 2025-11-18T17:02:06.740407+00:00.
- **parameter_sources.md**: Complete audit trail for every parameter value determination decision (320.4KB). Total decisions: 462. KB recommendations: 4. Conservative defaults: 458.
- **PARAMETERIZATION_AUDIT_EXECUTIVE_SUMMARY.md**: Executive summary of S/M/E ensemble parameterization audit. 416 methods analyzed, 245 requiring parameterization. Methodology: S/M/E Rule-Based Ensemble with Epistemic Validation. Date: 2025-11-13.

### Calibration Integration (4 artifacts)

| Path | Role | Validation Status | Mode of Generation | Version | Authority | SHA256 (first 16) |
|------|------|-------------------|-------------------|---------|-----------|-------------------|
| `CALIBRATION_IMPLEMENTATION_REPORT.md` | calibration_integration | VALIDATED | manual | 1.0.0 | PRIMARY | aa9d988cfad51334 |
| `docs/archive/CALIBRATION_INTEGRATION_STATUS.md` | calibration_integration | VALIDATED | manual | unknown | SECONDARY | 55923cd8afbc8c67 |
| `docs/CALIBRATION_SYSTEM.md` | calibration_integration | VALIDATED | manual | unknown | SECONDARY | a2949f66f41d7b36 |
| `config/intrinsic_calibration.json` | calibration_integration | VALIDATED | script | 1.0.0 | PRIMARY | 453799256e1a898a |

**Notes:**
- **CALIBRATION_IMPLEMENTATION_REPORT.md**: Phase 1 calibration system implementation. All 30 executors configured. Integration tests: 17/17 passing (100%). Hardcoded scan: 100+ instances catalogued. Date: 2025-11-18.
- **CALIBRATION_INTEGRATION_STATUS.md**: Phases 1-5.4 status report. Tests: 11/11 passing. Critical bug fixed: BaseLayerEvaluator weights. Branch: claude/calibration-system-integration-011dKHrEpz9cPcb4mi829oB4.
- **CALIBRATION_SYSTEM.md**: Documentation covering MethodCalibration, CalibrationContext, CalibrationModifier, empirical testing framework, and integration patterns.
- **intrinsic_calibration.json**: Generated by `rigorous_calibration_triage.py` using `config/intrinsic_calibration_rubric.json`. Total methods: 1,995 (1,470 calibrated, 525 excluded). Rubric version: 1.0.0. Base weights: w_th=0.4, w_imp=0.35, w_dep=0.25. Generated: 2025-11-10T08:23:00Z. Last triaged: 2025-11-10T18:36:07.566234+00:00.

**Total Normative Artifacts: 12**

---

## 🔄 TRANSITIONAL ARTIFACTS

**Definition:** Artifacts that are structurally normative but require validation before being fully trusted. Listed in `config/PARAMETERIZATION_CONSTITUTION.json` under `transitional_artifacts`.

| Path | Role | Reason | Validation Required | Version | SHA256 (first 16) |
|------|------|--------|---------------------|---------|-------------------|
| `canonical_method_catalogue_v2.json` | structural_catalogue | PENDING_VALIDATION | ✅ Yes | 2.0.0 | 73975d1f5efcefc9 |

**Validation Criteria:**
1. Manual review of complex defaults (36 instances)
2. Verification of parameter type inference
3. Confirmation of method signature accuracy
4. Validation of default value extraction

**Target Validation Date:** TBD

**Constitutional Rule Applied:**
*"Transitional artifacts may not be treated as fully normative until their validation criteria are satisfied."* (Rule 5)

**Note:** This file appears in both `normative_artifacts` (for structural reference) and `transitional_artifacts` (for validation gate). Once validation criteria are satisfied, it should be removed from `transitional_artifacts`.

**Total Transitional Artifacts: 1**

---

## 🗂️ LEGACY ARTIFACTS

**Definition:** Deprecated artifacts that must never be used as sources of truth. Listed in `config/PARAMETERIZATION_CONSTITUTION.json` under `legacy_artifacts`.

| Path | Status | Reason | Deletion Date |
|------|--------|--------|---------------|
| `config/catalogo_principal.yaml` | DELETED | Empty file (34-line header only), orphaned configuration | before 2025-11-25 |
| `config/causal_exctractor_2.yaml` | DELETED | Duplicate backup file | before 2025-11-25 |
| `config/trazabilidad_cohrencia.yaml` | DELETED_OR_MIGRATED | Method parameters migrated to JSON, audit rules extracted, unimplemented sections deleted | before 2025-11-25 |
| `config/causalextractor.yaml` | DELETED_OR_MIGRATED | Scoring thresholds migrated to JSON, patterns retained in data/patterns/ | before 2025-11-25 |
| `config/causal_exctractor.yaml` | DELETED_OR_MIGRATED | Scoring modalities migrated to JSON, unimplemented sections deleted | before 2025-11-25 |

**Constitutional Rule Applied:**
*"Legacy artifacts must never be used as sources of truth, even if they still exist in the repository."* (Rule 6)

**Migration Notes:**
- **trazabilidad_cohrencia.yaml**: Severity weights, bayesian_coupling, sector_weights migrated to `config/method_parameters.json`. Audit rules retained in `data/audit_rules/`.
- **causalextractor.yaml**: Scoring thresholds, discourse_controls, preprocessing migrated to JSON. Eslabones patterns and verb sequences retained in `data/patterns/`.
- **causal_exctractor.yaml**: Scoring modalities migrated to JSON. Micro assessment validation retained. Macro/meso assessment not implemented (deleted).

**Total Legacy Artifacts: 5** (all deleted or migrated)

---

## 📦 RETAINED CONFIGURATION FILES

**Definition:** Configuration files that remain in the repository for specific purposes (workflow metadata, pattern libraries, datasets) but are NOT method parameter sources. Listed in `config/PARAMETERIZATION_CONSTITUTION.json` under `retained_configuration_files`.

| Path | Role | Reason | Notes |
|------|------|--------|-------|
| `config/execution_mapping.yaml` | workflow_metadata | RETAINED | Workflow definitions, module mappings, dimension execution flow. Quality thresholds should migrate to method_parameters.json. |
| `config/schemas/derek_beach/config.yaml` | pattern_library | RETAINED | System patterns, lexicons, entity aliases. Bayesian thresholds should migrate to method_parameters.json. |
| `data/calibration/vfarfan_d1q1_calibration_dataset.yaml` | calibration_dataset | RETAINED | Calibration dataset (300 examples) for VFARFAN D1Q1. This is data, not configuration. |

**Total Retained Configuration Files: 3**

**Important:** These files are retained for their non-parameter content (workflow structure, patterns, datasets). Any method parameters or thresholds in these files should be migrated to `config/method_parameters.json` to maintain a single source of truth for runtime parameterization.

---

## 📊 CONSTITUTIONAL INVARIANTS

**These invariants are extracted from the current constitution and must not be changed outside constitution update flows.**

Source: `config/PARAMETERIZATION_CONSTITUTION.json` → `invariants`

### Parameterization Invariants

| Invariant | Value | Source | Last Verified |
|-----------|-------|--------|---------------|
| **methods_identified** | 283 | parameter_identification_report.md | 2025-11-18T12:26:55.687512+00:00 |
| **total_configurable_parameters** | 462 | parameter_identification_report.md | 2025-11-18T12:26:55.687512+00:00 |
| **total_parameters** | 462 | parameter_sources_comprehensive.md | 2025-11-18T17:02:06.740407+00:00 |
| **kb_recommendations** | 319 (69.0%) | parameter_sources_comprehensive.md | 2025-11-18T17:02:06.740407+00:00 |
| **code_defaults** | 143 (31.0%) | parameter_sources_comprehensive.md | 2025-11-18T17:02:06.740407+00:00 |

**Description:**
- **methods_identified**: Total number of methods identified as requiring parameterization in Phases 1-2
- **total_configurable_parameters**: Total number of configurable parameters across all identified methods
- **total_parameters**: Total parameters analyzed in Phase 3 value determination
- **kb_recommendations**: Number of parameters with knowledge base recommendations (academic sources, library references, standards)
- **code_defaults**: Number of parameters using code defaults (conservative defaults requiring validation)

### Calibration Invariants

| Invariant | Value | Source | Last Verified |
|-----------|-------|--------|---------------|
| **intrinsic_methods** | 1,995 (1,470 calibrated, 525 excluded) | config/intrinsic_calibration.json | 2025-11-10T18:36:07.566234+00:00 |
| **executors_calibrated** | 30 | config/method_parameters.json | 2025-11-18 |
| **base_layer_weights** | w_th=0.4, w_imp=0.35, w_dep=0.25 | config/intrinsic_calibration.json | 2025-11-10T08:23:00Z |

**Description:**
- **intrinsic_methods**: Total methods in intrinsic calibration registry
  - Calibrated: 1,470 methods have computed b_theory, b_impl, b_deploy scores
  - Excluded: 525 methods excluded (non-analytical utility functions, etc.)
- **executors_calibrated**: Number of D1Q1-D6Q5 executor methods with configured calibration thresholds
  - **Complete list:** D1Q1_Executor, D1Q2_Executor, D1Q3_Executor, D1Q4_Executor, D1Q5_Executor, D2Q1_Executor, D2Q2_Executor, D2Q3_Executor, D2Q4_Executor, D2Q5_Executor, D3Q1_Executor, D3Q2_Executor, D3Q3_Executor, D3Q4_Executor, D3Q5_Executor, D4Q1_Executor, D4Q2_Executor, D4Q3_Executor, D4Q4_Executor, D4Q5_Executor, D5Q1_Executor, D5Q2_Executor, D5Q3_Executor, D5Q4_Executor, D5Q5_Executor, D6Q1_Executor, D6Q2_Executor, D6Q3_Executor, D6Q4_Executor, D6Q5_Executor
- **base_layer_weights**: Weights for computing intrinsic score from b_theory, b_impl, b_deploy
  - Constraint: w_th + w_imp + w_dep = 1.0

### Structural Invariants

| Invariant | Value | Source | Last Verified |
|-----------|-------|--------|---------------|
| **total_methods_in_catalogue** | 2,189 | canonical_method_catalogue_v2.json | 2025-11-18T11:59:15.245947+00:00 |
| **methods_with_defaults** | 486 (22.2%) | canonical_method_catalogue_v2.json | 2025-11-18T11:59:15.245947+00:00 |
| **files_parsed** | 167 (0 parse errors) | canonical_method_catalogue_v2.json | 2025-11-18T11:59:15.245947+00:00 |

**Description:**
- **total_methods_in_catalogue**: Total methods catalogued in method signature analysis
- **methods_with_defaults**: Methods with default parameter values in their signatures
- **files_parsed**: Number of Python source files parsed by build_canonical_method_catalogue_v2.py

**Constitutional Rule Applied:**
*"You may not change any invariant without regenerating the corresponding source report under a dedicated jobfront."* (Rule 3)

---

## ⚖️ CONSTITUTIONAL RULES

As stated in `config/PARAMETERIZATION_CONSTITUTION.json`:

1. **Normative Authority** (Rule 1)
   *"You may not treat any artifact as normative unless it appears in normative_artifacts."*

2. **No Direct Edits** (Rule 2)
   *"You may not edit PARAMETERIZATION_CONSTITUTION.json directly in normal work. It may only be changed as part of a dedicated 'constitution update' task, with a full audit."*

3. **Invariant Immutability** (Rule 3)
   *"You may not change any invariant without regenerating the corresponding source report under a dedicated jobfront."*

4. **Reinterpretation Forbidden** (Rule 4)
   *"You are not allowed to 'reinterpret' facts stated in source reports. You must obey them."*

5. **Validation Gate** (Rule 5)
   *"Transitional artifacts may not be treated as fully normative until their validation criteria are satisfied."*

6. **Legacy Prohibition** (Rule 6)
   *"Legacy artifacts must never be used as sources of truth, even if they still exist in the repository."*

---

## 🔍 ARTIFACT SUMMARY STATISTICS

| Category | Count | Authority Level Distribution |
|----------|-------|------------------------------|
| **Normative Artifacts** | 12 | PRIMARY: 9, SECONDARY: 3 |
| **Transitional Artifacts** | 1 | PRIMARY: 1 (pending validation) |
| **Legacy Artifacts** | 5 | N/A (all deleted or migrated) |
| **Retained Configuration Files** | 3 | N/A (non-parameter content) |

**Normative Artifacts by Role:**
- runtime_parameters: 3
- structural_catalogue: 2
- epistemic_audit: 3
- calibration_integration: 4

**Mode of Generation Distribution:**
- script: 3 (canonical_method_catalogue_v2.json, config/intrinsic_calibration.json, parameter_sources.md)
- manual: 5 (Python source files, documentation)
- mixed/script+manual: 4 (reports with manual curation)

---

## 📝 GOVERNANCE NOTES

### Repository Mode: STRICT

**Current Mode Rationale:**
*"System is in production. Parameterization and calibration are complete. All changes must follow constitutional process."*

In STRICT mode:
- ✅ All artifacts listed in `normative_artifacts` are authoritative
- ✅ Invariants are immutable without source report regeneration
- ✅ Constitutional rules are enforced
- ❌ No ad-hoc file walks for parameter sources
- ❌ No reinterpretation of source facts
- ❌ No use of legacy artifacts as truth sources

### Next Constitutional Review

**Scheduled:** TBD - To be scheduled after canonical_method_catalogue_v2.json validation is complete

**Validation Required for:**
- canonical_method_catalogue_v2.json (transitional artifact)
  - Manual review of 36 complex defaults
  - Verification of parameter type inference
  - Confirmation of method signature accuracy
  - Validation of default value extraction

Once validation is complete, this artifact can be removed from `transitional_artifacts` and remain in `normative_artifacts` with `validation_status: "VALIDATED"`.

---

## 🚨 CRITICAL ARCHITECTURAL BOUNDARIES (REPEATED FOR EMPHASIS)

**FOR CALIBRATION AND EXECUTORS:**

**✅ CORRECT RUNTIME PARAMETER SOURCE:**
- `config/method_parameters.json`
- Accessed via `src/saaaaaa/core/calibration/parameter_loader.py` → `MethodParameterLoader`

**❌ INCORRECT (DESIGN ARTIFACTS, NOT RUNTIME):**
- `CANONICAL_METHOD_PARAMETERIZATION_SPEC.json` (upstream design artifact from audit)
- `MethodConfigLoader` (upstream design tool, not for runtime use)

**Enforcement:**
- Any runtime code (calibration system, executors, scoring, etc.) that loads parameters MUST use `MethodParameterLoader`
- Any code that attempts to use `CANONICAL_METHOD_PARAMETERIZATION_SPEC.json` or `MethodConfigLoader` at runtime is violating the architectural boundary
- Design artifacts are for documentation and upstream analysis only

**Rationale:**
- Clear separation of concerns: design/audit artifacts vs. runtime configuration
- Single source of truth for runtime parameters: `config/method_parameters.json`
- Maintainability: one config file to update, one loader to maintain

---

## 📜 AUDIT TRAIL

**Constitution Creation:**
- **Date:** 2025-11-25T00:00:00Z
- **Jobfront:** JOBFRONT 3A - PARAMETERIZATION CONSTITUTION (HARD GATE)
- **Created By:** Claude (AI Agent)
- **Method:** Automated constitution generation from normative source reports

**This Status Report:**
- **Date:** 2025-11-25
- **Jobfront:** JOBFRONT 3B – PARAMETERIZATION STATUS REPORT (BOUND TO CONSTITUTION)
- **Created By:** Claude (AI Agent)
- **Method:** Direct extraction from config/PARAMETERIZATION_CONSTITUTION.json version 1.0.0
- **Modifications to Constitution:** None (report only, no constitutional changes)

---

## ✅ REPORT VERIFICATION

This report was generated by:
1. ✅ Reading `config/PARAMETERIZATION_CONSTITUTION.json` in full
2. ✅ Extracting all artifact entries from `normative_artifacts`, `transitional_artifacts`, `legacy_artifacts`, and `retained_configuration_files`
3. ✅ Echoing all invariants from `invariants` section
4. ✅ Extracting mode_of_generation from artifact metadata where available
5. ✅ Stating runtime parameter source boundaries in bold
6. ✅ Including all 6 constitutional rules
7. ✅ No ad-hoc file walks or free interpretation

**Report Status:** COMPLETE AND CONSTITUTIONALLY BOUND

**Report Authority:** This report faithfully represents the state defined in `config/PARAMETERIZATION_CONSTITUTION.json` version 1.0.0.

---

**End of Report**
