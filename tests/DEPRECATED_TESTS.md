# Deprecated Tests Manifest

This document catalogs all tests marked with `@pytest.mark.obsolete` that require substantial refactoring (>50 LOC changes) before they can be integrated into the active test suite.

## Overview

**Last Updated:** 2025-01-XX  
**Total Deprecated Tests:** 6 test files  
**Estimated Refactoring Effort:** ~850 LOC changes

## Deprecation Policy

Tests marked as obsolete:
- Are excluded from default `pytest` runs via `pytest.ini` configuration
- Will fail imports or assertions due to outdated dependencies
- Require >50 LOC substantive refactoring to align with current architecture
- Must not block CI/CD pipelines or development workflows

## Deprecated Test Files

### 1. `tests/test_intrinsic_pipeline_behavior.py`

**Status:** DEPRECATED  
**Lines of Code:** ~220  
**Estimated Refactoring:** ~150 LOC changes

#### Why Deprecated

- **Outdated Import Path:** Uses `src.farfan_pipeline.core.calibration.intrinsic_calibration_loader` instead of `farfan_pipeline.core.calibration.intrinsic_calibration_loader`
- **Legacy Loader Interface:** `IntrinsicCalibrationLoader` API has changed significantly (fallback behavior now handled by `CalibrationOrchestrator`)
- **Hardcoded Test Data:** Relies on inline JSON fixture instead of actual calibration files
- **Obsolete Fallback Logic:** Tests pending→0.5, excluded→None, none→0.3 fallbacks that are no longer used

#### What Replaces It

- `tests/core/test_orchestrator_mandatory_path.py` - Tests calibration orchestrator with proper context resolution
- `tests/test_intrinsic_purity.py` - Tests intrinsic calibration file structure and purity
- Future: `tests/core/test_calibration_orchestrator_fallbacks.py` (needs creation)

#### Refactoring Requirements

1. Update imports to use `farfan_pipeline` namespace
2. Replace `IntrinsicCalibrationLoader` with `CalibrationOrchestrator`
3. Use `CalibrationContext.from_question_id()` for context creation
4. Test against actual `config/intrinsic_calibration.json` file
5. Update assertions for new fallback behavior (orchestrator-based)
6. Add tests for `MissingIntrinsicCalibrationError`, `InsufficientContextError`

---

### 2. `tests/test_inventory_completeness.py`

**Status:** DEPRECATED  
**Lines of Code:** ~185  
**Estimated Refactoring:** ~120 LOC changes

#### Why Deprecated

- **Hardcoded File Path:** Uses `methods_inventory_raw.json` which has been replaced by AST-based inventory system
- **Outdated Critical Methods List:** References `analysis.derek_beach.*` and `core.aggregation.*` methods that have been refactored
- **Legacy Epistemology Tags:** Tests `epistemology_tags` field that is no longer part of method metadata
- **Obsolete Role Categories:** Tests for roles (`ingest`, `processor`, etc.) that have been restructured

#### What Replaces It

- `tests/core/test_method_inventory_ast.py` - Tests AST-based method extraction pipeline
- `tests/calibration_system/test_inventory_consistency.py` - Tests inventory-calibration consistency
- Future: `tests/core/test_method_inventory_completeness.py` (needs creation with updated patterns)

#### Refactoring Requirements

1. Remove dependency on `methods_inventory_raw.json`
2. Use `farfan_pipeline.core.method_inventory` module for dynamic inventory generation
3. Update critical methods list to match current architecture:
   - Replace `analysis.derek_beach.*` with actual analysis module methods
   - Replace `core.aggregation.*` with `processing.aggregation.*`
   - Add new critical methods from `core.orchestrator.executors`
4. Remove tests for `epistemology_tags` (no longer used)
5. Update role categories to match `LAYER_REQUIREMENTS` in `layer_assignment.py`
6. Add tests for AST extraction completeness (walk_python_files, parse_file, etc.)

---

### 3. `tests/test_layer_assignment.py`

**Status:** DEPRECATED  
**Lines of Code:** ~280  
**Estimated Refactoring:** ~180 LOC changes

#### Why Deprecated

- **Obsolete Config File:** Expects `config/canonic_inventorry_methods_layers.json` (typo in name, file structure outdated)
- **8-Layer Assumption:** Tests assume exactly 8 layers for executors, but current system uses dynamic layer assignment
- **Legacy Weights Structure:** Tests `weights` and `interaction_weights` summing to 1.0, but Choquet integral now uses capacity-based weights
- **Hardcoded Executor Count:** Assumes exactly 30 executors (D1-D6 × Q1-5), but system is now more flexible

#### What Replaces It

- `tests/calibration_system/test_layer_correctness.py` - Tests layer assignment correctness
- `tests/core/test_orchestrator_mandatory_path.py` - Tests layer evaluation in calibration context
- Future: `tests/core/test_layer_assignment_dynamic.py` (needs creation)

#### Refactoring Requirements

1. Remove dependency on `canonic_inventorry_methods_layers.json`
2. Use `farfan_pipeline.core.calibration.layer_assignment.LAYER_REQUIREMENTS` dynamically
3. Update executor detection to use AST-based method inventory
4. Replace 8-layer hard check with dynamic layer requirements per role
5. Update weights testing to account for Choquet integral capacity values
6. Remove fixed 30-executor assumption
7. Test against `CalibrationOrchestrator.evaluate_runtime_layers()` method
8. Add tests for dynamic layer computation based on `CalibrationContext`

---

### 4. `tests/test_opentelemetry_observability.py`

**Status:** DEPRECATED  
**Lines of Code:** ~95  
**Estimated Refactoring:** ~60 LOC changes

#### Why Deprecated

- **Wrong Import Path:** Uses `farfan_core.observability` instead of `farfan_pipeline.observability`
- **Incomplete Mock Testing:** Only tests the "no OTEL available" path, doesn't test actual OpenTelemetry integration
- **Missing Span Attributes:** Doesn't test span attributes, metrics, or context propagation properly
- **No Integration with Orchestrator:** Doesn't test observability hooks in actual pipeline execution

#### What Replaces It

- `tests/integration/test_opentelemetry_integration.py` (needs creation)
- Future: Tests should be integrated into `test_pipeline_e2e_deterministic.py` to verify tracing

#### Refactoring Requirements

1. Update import path to `farfan_pipeline.observability`
2. Add tests for actual OTEL initialization (not just mocks)
3. Test span creation with proper attributes:
   - `executor.name`, `executor.dimension`, `executor.question`
   - `method.name`, `method.layer`, `method.calibration_score`
4. Test metrics collection:
   - `farfan.executor.duration`
   - `farfan.calibration.score`
   - `farfan.pipeline.phase_completion`
5. Test context propagation across async boundaries
6. Integrate with `PhaseOrchestrator` to test end-to-end tracing
7. Add Jaeger/Prometheus export tests (optional, behind feature flag)

---

### 5. `tests/calibration_system/test_orchestrator_runtime.py`

**Status:** DEPRECATED  
**Lines of Code:** ~160  
**Estimated Refactoring:** ~100 LOC changes

#### Why Deprecated

- **Obsolete Layer Order:** Tests hardcoded layer execution order (`ingestion`, `extraction`, etc.) that no longer applies
- **Wrong Executors File:** References `src/farfan_pipeline/core/orchestrator/executors_methods.json` (non-existent)
- **Legacy Import Path:** Uses `src.farfan_pipeline` import prefix instead of `farfan_pipeline`
- **Missing Calibration Context:** Doesn't test with proper `CalibrationContext` objects
- **Simulation Instead of Real Execution:** Uses mock simulations instead of testing actual orchestrator behavior

#### What Replaces It

- `tests/core/test_orchestrator_mandatory_path.py` - Tests real orchestrator calibration behavior
- `tests/integration/test_pipeline_e2e_deterministic.py` - Tests end-to-end pipeline execution
- Future: `tests/core/test_calibration_orchestrator_runtime.py` (needs creation)

#### Refactoring Requirements

1. Remove hardcoded layer execution order tests (no longer applicable)
2. Update to use dynamic executor discovery via AST-based method inventory
3. Replace simulated method calls with actual `CalibrationOrchestrator.calibrate_method()` calls
4. Test with real `CalibrationContext.from_question_id()` contexts
5. Add tests for:
   - `evaluate_runtime_layers()` correctness
   - `choquet_integral()` aggregation
   - `weighted_sum()` for non-executors
6. Test error propagation: `MissingIntrinsicCalibrationError`, `MethodBelowThresholdError`
7. Test calibration threshold enforcement (>= 0.7)
8. Remove `executors_methods.json` dependency

---

### 6. `tests/calibration_system/test_performance_benchmarks.py`

**Status:** DEPRECATED  
**Lines of Code:** ~190  
**Estimated Refactoring:** ~120 LOC changes

#### Why Deprecated

- **Hardcoded File Paths:** Uses `system/config/calibration/intrinsic_calibration.json` and `src/farfan_pipeline/core/orchestrator/executors_methods.json`
- **Legacy Performance Assumptions:** Tests calibration as simple JSON lookup, doesn't account for orchestrator overhead
- **Missing Runtime Context:** Doesn't test performance with actual `CalibrationContext` and `RuntimeLayers` computation
- **Obsolete Metrics:** Tests 30-executor and 200-method calibration speeds without considering Choquet integral computation

#### What Replaces It

- Future: `tests/performance/test_calibration_orchestrator_benchmarks.py` (needs creation)
- Future: `tests/performance/test_pipeline_e2e_performance.py` (needs creation)

#### Refactoring Requirements

1. Update file paths to use `farfan_pipeline.config.paths` module for path resolution
2. Test `CalibrationOrchestrator` performance instead of raw JSON loading
3. Add benchmarks for:
   - `calibrate_method()` with real contexts (target: <10ms per method)
   - `evaluate_runtime_layers()` computation (target: <5ms)
   - `choquet_integral()` aggregation (target: <1ms)
4. Test concurrent calibration performance (thread-safety)
5. Add memory profiling for calibration data structures
6. Test performance with different context complexities (D1Q1 vs D6Q30)
7. Remove executors_methods.json dependency
8. Add performance regression detection (compare against baseline)

---

## Configuration

Tests marked with `@pytest.mark.obsolete` are excluded from default runs via `pytest.ini`:

```ini
[tool.pytest.ini_options]
addopts = "-v --strict-markers --tb=short -m 'not obsolete'"
markers = [
    "obsolete: Tests marked obsolete per SIN_CARRETA protocol - will be removed",
]
```

## Running Deprecated Tests

To explicitly run deprecated tests (for debugging or refactoring):

```bash
pytest -v -m obsolete
```

To run all tests including deprecated ones:

```bash
pytest -v -m ""
```

## Refactoring Workflow

1. **Assess Priority:** Use coverage analysis to determine which deprecated tests cover critical untested paths
2. **Create Replacement:** Write new test with current architecture before removing obsolete test
3. **Verify Coverage:** Ensure new test provides equivalent or better coverage
4. **Remove Obsolete Marker:** Once refactored, remove `pytestmark = pytest.mark.obsolete`
5. **Delete or Archive:** After 2 sprint cycles, delete deprecated test or move to `tests/archive/`

## Summary Statistics

| Category | Count | LOC | Refactoring Estimate |
|----------|-------|-----|---------------------|
| Core Tests | 3 | 685 | ~450 LOC |
| Calibration System Tests | 2 | 350 | ~220 LOC |
| Observability Tests | 1 | 95 | ~60 LOC |
| **Total** | **6** | **1130** | **~730 LOC** |

## Notes

- All deprecated tests have been documented with inline deprecation comments
- None of the deprecated tests block current development workflows
- New tests covering equivalent functionality are either in place or planned
- Tests are marked obsolete (not deleted) to preserve institutional knowledge of what was tested

---

**Maintenance:** Update this manifest whenever tests are marked obsolete or successfully refactored.
