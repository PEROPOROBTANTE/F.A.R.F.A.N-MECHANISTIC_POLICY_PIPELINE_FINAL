# Runtime Pipeline Validation Report

**Generated:** 2025-11-06 07:27:25

## Summary

- ✅ Passed: 4
- ⚠️ Warnings: 1
- ❌ Failed: 3

## Test Results

### ❌ import_chain

**Status:** FAIL

**Imported Modules:** ['saaaaaa.core.orchestrator.core', 'saaaaaa.processing.aggregation', 'saaaaaa.processing.document_ingestion', 'saaaaaa.core.orchestrator.signals', 'saaaaaa.core.orchestrator.arg_router', 'saaaaaa.analysis.recommendation_engine']

**Errors:**
- saaaaaa.utils.cpp_adapter: No module named 'pyarrow'

---

### ✅ contract_schemas

**Status:** PASS

**Pydantic Models:** ['PreprocessedDocument', 'ScoredResult', 'DimensionScore', 'AreaScore', 'ClusterScore', 'MacroScore', 'SignalPack (Pydantic)']

---

### ❌ arg_router_routes

**Status:** FAIL

**Errors:**
- /home/runner/.local/lib/python3.12/site-packages/torch/lib/libtorch_global_deps.so: cannot open shared object file: No such file or directory

---

### ❌ cpp_adapter_conversion

**Status:** FAIL

**Errors:**
- No module named 'pyarrow'

---

### ✅ determinism_setup

**Status:** PASS

**Seed Modules:** ['SeedFactory', 'determinism.seeds']

---

### ✅ signal_registry

**Status:** PASS

**Features:** ['SignalPack imported', 'SignalPack creation', 'Pydantic validation']

---

### ✅ aggregation_pipeline

**Status:** PASS

**Errors:**
- DimensionAggregator: DimensionAggregator.__init__() missing 1 required positional argument: 'monolith'
- AreaPolicyAggregator: AreaPolicyAggregator.__init__() missing 1 required positional argument: 'monolith'
- ClusterAggregator: ClusterAggregator.__init__() missing 1 required positional argument: 'monolith'
- MacroAggregator: MacroAggregator.__init__() missing 1 required positional argument: 'monolith'

---

### ⚠️ config_parametrization

**Status:** WARNING

**Configs Tested:** ['ExecutorConfig']

**Missing Methods:** ['ExecutorConfig.from_cli']

---

## Recommendations

### Critical Issues

- Fix import_chain: saaaaaa.utils.cpp_adapter: No module named 'pyarrow'
- Fix arg_router_routes: /home/runner/.local/lib/python3.12/site-packages/torch/lib/libtorch_global_deps.so: cannot open shared object file: No such file or directory
- Fix cpp_adapter_conversion: No module named 'pyarrow'

### Warnings

- Review config_parametrization: 

