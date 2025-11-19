# PARAMETER IDENTIFICATION REPORT

## Phases 1-2: Identification and Extraction

**Generated:** 2025-11-18T12:26:55.687512+00:00

---

## 📊 SUMMARY

- **Methods identified:** 283
- **Total configurable parameters:** 462
- **Avg parameters per method:** 1.63

## 🔍 FILTERING STATISTICS

- Methods scanned: 2,189
- ✅ Identified: 283
- ❌ No configurable params: 1,703
- ❌ Private methods: 42
- ❌ Excluded by calibration: 161

## 🔝 TOP 10 METHODS (Most Configurable)

1. **from_cli_args** (10 params)
   - Type: general
   - File: src/saaaaaa/core/orchestrator/executor_config.py
   - Parameters: max_tokens, temperature, timeout_s, retry, policy_area, regex_pack, thresholds, entities_whitelist, enable_symbolic_sparse, seed

2. **create** (7 params)
   - Type: general
   - File: src/saaaaaa/core/orchestrator/evidence_registry.py
   - Parameters: source_method, parent_evidence_ids, question_id, document_id, execution_time_ms, metadata, previous_hash

3. **record_evidence** (6 params)
   - Type: general
   - File: src/saaaaaa/core/orchestrator/evidence_registry.py
   - Parameters: source_method, parent_evidence_ids, question_id, document_id, execution_time_ms, metadata

4. **execute_phase_with_timeout** (6 params)
   - Type: general
   - File: src/saaaaaa/core/orchestrator/core.py
   - Parameters: coro, *varargs, handler, args, timeout_s, **kwargs

5. **__init__** (6 params)
   - Type: general
   - File: src/saaaaaa/core/calibration/orchestrator.py
   - Parameters: config, intrinsic_calibration_path, compatibility_path, method_registry_path, method_signatures_path, intrinsic_calibration_path

6. **filter_events** (6 params)
   - Type: general
   - File: src/saaaaaa/patterns/event_tracking.py
   - Parameters: category, level, source, start_time, end_time, tags

7. **evaluate** (5 params)
   - Type: general
   - File: src/saaaaaa/core/calibration/meta_layer.py
   - Parameters: formula_exported, full_trace, logs_conform, signature_valid, execution_time_s

8. **create_policy_processor** (4 params)
   - Type: nlp
   - File: src/saaaaaa/processing/policy_processor.py
   - Parameters: preserve_structure, enable_semantic_tagging, confidence_threshold, **kwargs

9. **load_and_validate_metadata** (4 params)
   - Type: general
   - File: src/saaaaaa/utils/metadata_loader.py
   - Parameters: schema_ref, required_version, expected_checksum, checksum_algorithm

10. **log_contract_mismatch** (4 params)
   - Type: general
   - File: src/saaaaaa/utils/validation/contract_logger.py
   - Parameters: index, file, line, remediation

## 📂 METHODS BY TYPE

### GENERAL
Count: 185

- add_finding (1 params)
- generate_audit_report (1 params)
- get_output_path (1 params)
- try_import (3 params)
- lazy_import (1 params)
- ... and 180 more

### NLP
Count: 46

- __init__ (2 params)
- start_span (3 params)
- start_as_current_span (2 params)
- execute_pipeline (3 params)
- encode (2 params)
- ... and 41 more

### BAYESIAN
Count: 18

- evaluate_policy_metric (2 params)
- define_prior (1 params)
- sample_prior (1 params)
- __init__ (3 params)
- load_catalog (1 params)
- ... and 13 more

### MACHINE_LEARNING
Count: 16

- create_policy_embedder (1 params)
- run_aggregation_pipeline (1 params)
- apply_cluster_weights (1 params)
- aggregate_cluster (1 params)
- unwrap_payload (1 params)
- ... and 11 more

### POLICY_DOMAIN
Count: 14

- from_legacy (1 params)
- get_canonical_policy_areas (1 params)
- construct_pdet_input (1 params)
- construct_policy_processor_input (1 params)
- analyze_municipal_plan_sync (1 params)
- ... and 9 more

### STATISTICAL
Count: 4

- wrap_payload (1 params)
- wrap (2 params)
- set_determinism (4 params)
- get_manifest_entry (2 params)

## 🎯 NEXT STEPS

### Phase 3: Value Determination
For each parameter, apply hierarchy:
1. **Formal specification** (academic papers, standards)
2. **Reference implementation** (sklearn, PyMC3, etc.)
3. **Empirical validation** (cross-validation)
4. **Conservative defaults** (last resort)

### Phase 4: Consistency Validation
- Compare JSON values vs code defaults
- Generate inconsistency report
- Implement CI/CD checks

### Phase 5: Wiring
- Implement ParameterLoader
- Implement ParameterValidator
- Add logging and auditing
- Write integration tests

