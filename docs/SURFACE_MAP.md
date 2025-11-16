# Core Modules Surface Map

This document maps the public APIs of each core module, documenting which functions/classes are used by the orchestrator and executors.

## Purpose

- **Surface Map**: Document which APIs are actively used vs. which can be deprecated
- **Contract Alignment**: Ensure contracts match actual usage patterns
- **Migration Guide**: Help migrate from old patterns to new contract-based patterns

## Module: Analyzer_one.py

### Classes Exposed via Registry
```python
# orchestrator/class_registry.py lines 30-33
"SemanticAnalyzer": "Analyzer_one.SemanticAnalyzer",
"PerformanceAnalyzer": "Analyzer_one.PerformanceAnalyzer",
"TextMiningEngine": "Analyzer_one.TextMiningEngine",
"MunicipalOntology": "Analyzer_one.MunicipalOntology",
```

### Used Methods (from executors_COMPLETE_FIXED.py)
- `SemanticAnalyzer._calculate_semantic_complexity()` - Line 217
- `SemanticAnalyzer._classify_policy_domain()` - Line 230

### Constructor Requirements
- `SemanticAnalyzer(ontology: MunicipalOntology)` - Requires ontology instance
- `PerformanceAnalyzer(ontology: MunicipalOntology)` - Requires ontology instance
- `TextMiningEngine(ontology: MunicipalOntology)` - Requires ontology instance
- `MunicipalOntology()` - No parameters

### Contract Mapping
**Input**: Text segments, ontology parameters
**Output**: Semantic analysis results, complexity scores, domain classifications

### I/O Operations to Remove
- Lines 796-800: File reading (with open)
- Lines 891-892: File writing (sample file)
- Lines 1215: PDF reading
- Lines 1303-1306: JSON loading
- Lines 1519-1520: JSON export
- Lines 1595-1653: Text file exports
- Lines 1732-1733: Config loading
- Lines 1748-1749: Config saving
- Lines 1811-1843: Batch results export

### Functions to Deprecate/Move
- `example_usage()` → Move to examples/analyzer_one_demo.py
- `main()` → Move to examples/analyzer_one_cli.py
- `ResultsExporter.*` → Move to orchestrator/exporters.py (if needed)
- `ConfigurationManager.*` → Move to orchestrator/config.py (if needed)
- `BatchProcessor.*` → Move to orchestrator/batch.py (if needed)

---

## Module: derek_beach.py

### Classes Exposed via Registry
```python
# orchestrator/class_registry.py lines 21-24
"CDAFFramework": "derek_beach.CDAFFramework",
"OperationalizationAuditor": "derek_beach.OperationalizationAuditor",
"FinancialAuditor": "derek_beach.FinancialAuditor",
"BayesianMechanismInference": "derek_beach.BayesianMechanismInference",
```

### Used Methods (from executors_COMPLETE_FIXED.py)
- Need to grep executors for derek_beach usage patterns

### Constructor Requirements
- To be documented after analysis

### Contract Mapping
**Input**: Document text, plan metadata, configuration
**Output**: Causal mechanisms, evidential tests, Bayesian inference results

### I/O Operations to Remove
- Multiple file I/O operations (~40 detected)
- To be catalogued specifically

### Functions to Deprecate/Move
- `main()` function → Move to examples/cdaf_demo.py

---

## Module: financiero_viabilidad_tablas.py

### Classes Exposed via Registry
```python
# orchestrator/class_registry.py line 20
"PDETMunicipalPlanAnalyzer": "financiero_viabilidad_tablas.PDETMunicipalPlanAnalyzer",
```

### Used Methods (from executors_COMPLETE_FIXED.py)
- Lines 666-675: `PDETMunicipalPlanAnalyzer.extract_tables()`
- Lines 681: `PDETMunicipalPlanAnalyzer._extract_financial_amounts()`

### Constructor Requirements
- To be documented

### Contract Mapping
**Input**: Document content, extraction parameters
**Output**: Tables, financial indicators, viability scores

### I/O Operations to Remove
- PDF reading operations
- JSON operations
- To be catalogued

### Functions to Deprecate/Move
- `main_example()` → Move to examples/pdet_demo.py

---

## Module: teoria_cambio.py

### Classes Exposed via Registry
```python
# orchestrator/class_registry.py lines 34-35
"TeoriaCambio": "teoria_cambio.TeoriaCambio",
"AdvancedDAGValidator": "teoria_cambio.AdvancedDAGValidator",
```

### Used Methods (from executors_COMPLETE_FIXED.py)
- To be documented after executor analysis

### Contract Mapping
**Input**: Document text, strategic goals
**Output**: Causal DAG, validation results, Monte Carlo simulations

### Functions to Deprecate/Move
- `main()` → Move to examples/teoria_cambio_demo.py

---

## Module: contradiction_deteccion.py

### Classes Exposed via Registry
```python
# orchestrator/class_registry.py lines 17-19
"PolicyContradictionDetector": "contradiction_deteccion.PolicyContradictionDetector",
"TemporalLogicVerifier": "contradiction_deteccion.TemporalLogicVerifier",
"BayesianConfidenceCalculator": "contradiction_deteccion.BayesianConfidenceCalculator",
```

### Used Methods (from executors_COMPLETE_FIXED.py)
- To be documented

### Contract Mapping
**Input**: Text, plan name, policy dimension
**Output**: Contradictions, confidence scores, temporal conflicts

### Functions to Deprecate/Move
- Example code at end → Move to examples/contradiction_demo.py

---

## Module: embedding_policy.py

### Classes Exposed via Registry
```python
# orchestrator/class_registry.py lines 25-29
"BayesianNumericalAnalyzer": "embedding_policy.BayesianNumericalAnalyzer",
"PolicyAnalysisEmbedder": "embedding_policy.PolicyAnalysisEmbedder",
"AdvancedSemanticChunker": "embedding_policy.AdvancedSemanticChunker",
"SemanticChunker": "embedding_policy.AdvancedSemanticChunker",  # Alias
```

### Used Methods (from executors_COMPLETE_FIXED.py)
- Lines 243-252: `BayesianNumericalAnalyzer.evaluate_policy_metric()`
- Lines 258-265: `BayesianNumericalAnalyzer._classify_evidence_strength()`
- Lines 437-444: `BayesianNumericalAnalyzer._compute_coherence()`

### Contract Mapping
**Input**: Text, dimensions, model config
**Output**: Embeddings, similarity scores, Bayesian evaluations

### Functions to Deprecate/Move
- `example_pdm_analysis()` → Move to examples/embedding_demo.py

---

## Module: semantic_chunking_policy.py

### Classes Exposed via Registry
Not directly in registry, but may be used via PolicyDocumentAnalyzer

### Used Methods (from executors_COMPLETE_FIXED.py)
- To be documented

### Contract Mapping
**Input**: Text, structure preservation, config
**Output**: Semantic chunks, causal dimensions, key excerpts

### Functions to Deprecate/Move
- `main()` → Move to examples/semantic_chunking_demo.py

---

## Module: policy_processor.py

### Classes Exposed via Registry
```python
# orchestrator/class_registry.py lines 14-16
"IndustrialPolicyProcessor": "policy_processor.IndustrialPolicyProcessor",
"PolicyTextProcessor": "policy_processor.PolicyTextProcessor",
"BayesianEvidenceScorer": "policy_processor.BayesianEvidenceScorer",
```

### Used Methods (from executors_COMPLETE_FIXED.py)
- Lines 36-44: `IndustrialPolicyProcessor.process()`
- Lines 50-57: `IndustrialPolicyProcessor._match_patterns_in_sentences()`
- Many more...

### Contract Mapping
**Input**: Data, text, sentences, tables
**Output**: Processed data, evidence bundles, Bayesian scores

### I/O Status
- policy_processor.py is already relatively pure
- Verify no I/O operations present

---

## Migration Strategy

1. **Phase 1**: Document all usage patterns in executors
2. **Phase 2**: Create factory methods in orchestrator/factory.py
3. **Phase 3**: Refactor core modules to accept contracts
4. **Phase 4**: Update executors to use new APIs
5. **Phase 5**: Move demo code to examples/
6. **Phase 6**: Remove I/O from core modules

## Contract Validation

Each contract should be validated with:
- Type checking (mypy --strict)
- Runtime validation helpers
- Example usage in docstrings
- Integration tests

## Deprecation Timeline

- **v1.0**: Introduce contracts alongside existing APIs
- **v1.1**: Mark old APIs as deprecated (warnings)
- **v2.0**: Remove old APIs, contracts only

---

**Status**: Initial mapping (to be refined with detailed executor analysis)
**Last Updated**: 2025-10-31
