# D1-Q1 Human Answer Structure Design

**Purpose**: Define the expected output structure from D1-Q1's 17 methods after evidence assembly.

## Method Output Mapping

Based on the 17 methods in `D1_Q1_QuantitativeBaselineExtractor`:

### Group 1: Text Mining (Methods 1-2)

**1. TextMiningEngine.diagnose_critical_links**
```python
Output: {
    "critical_links": [
        {
            "link_id": "CL-001",
            "cause": "alta tasa de VBG",
            "effect": "baja autonomía económica de las mujeres",
            "connector": "conduce a",
            "criticality_score": 0.87,
            "sentence_id": 45,
            "context": "La alta tasa de VBG en el municipio conduce a una baja autonomía económica..."
        }
    ],
    "link_count": 5,
    "avg_criticality": 0.78
}
Provides: "text_mining.critical_links"
```

**2. TextMiningEngine._analyze_link_text**
```python
Output: {
    "link_contexts": [
        {
            "link_id": "CL-001",
            "context_window": "... contexto de ±3 oraciones ...",
            "coherence_score": 0.82,
            "supporting_evidence": ["sent_44", "sent_46"],
            "contradicting_evidence": []
        }
    ],
    "avg_coherence": 0.79
}
Provides: "text_mining.link_analysis"
```

### Group 2: Industrial Policy Processing (Methods 3-5)

**3. IndustrialPolicyProcessor.process**
```python
Output: {
    "structural_segments": {
        "pilar_1_genero": {
            "header": "Pilar 1: Igualdad de Género",
            "objectives": [...],
            "content_length": 2500
        }
    },
    "pattern_matches": {
        "baseline_data": 12,
        "targets": 8,
        "indicators": 15
    },
    "structural_completeness": 0.85
}
Provides: "industrial_policy.structure"
```

**4. IndustrialPolicyProcessor._match_patterns_in_sentences**
```python
Output: {
    "sentence_matches": [
        {
            "sentence_id": 45,
            "pattern_id": "PAT-Q001-002",
            "matched_text": "según datos de DANE",
            "start_pos": 123,
            "end_pos": 145
        }
    ],
    "match_density": 0.12  # matches per sentence
}
Provides: "industrial_policy.sentence_patterns"
```

**5. IndustrialPolicyProcessor._extract_point_evidence**
```python
Output: {
    "evidence_points": [
        {
            "type": "quantitative_indicator",
            "value": "tasa de VBG: 12.3%",
            "context_snippet": "La tasa de VBG en 2022 fue del 12.3%",
            "confidence": 0.89,
            "sentence_id": 45
        },
        {
            "type": "official_source",
            "value": "DANE",
            "context_snippet": "según datos de DANE",
            "confidence": 0.95,
            "sentence_id": 45
        }
    ],
    "point_count": 38
}
Provides: "industrial_policy.processed_evidence"
```

### Group 3: Causal Extraction (Methods 6-7)

**6. CausalExtractor._extract_goals**
```python
Output: {
    "goals": [
        {
            "goal_id": "G-001",
            "goal_verb": "reducir",
            "target_entity": "violencia basada en género",
            "quantifier": "20%",
            "sentence": "Reducir la violencia basada en género en un 20%"
        }
    ],
    "goal_count": 7,
    "quantified_goal_count": 5
}
Provides: "causal_extraction.goals"
```

**7. CausalExtractor._parse_goal_context**
```python
Output: {
    "goal_contexts": {
        "G-001": {
            "temporal": "2024-2027",
            "spatial": "zona rural",
            "responsible_actor": "Secretaría de la Mujer",
            "context_completeness": 1.0
        }
    }
}
Provides: "causal_extraction.goal_contexts"
```

### Group 4: Financial Analysis (Methods 8-10)

**8. FinancialAuditor._parse_amount**
```python
Output: {
    "amounts": [
        {
            "raw_text": "$ 15.000.000",
            "normalized_value": 15000000.0,
            "currency": "COP",
            "confidence": 0.98
        }
    ],
    "amount_count": 12,
    "total_budget_cop": 850000000.0
}
Provides: "financial_audit.amounts"
```

**9. PDETMunicipalPlanAnalyzer._extract_financial_amounts**
```python
Output: {
    "categorized_amounts": [
        {
            "amount": 15000000.0,
            "category": "SGR",
            "source_type": "regalías",
            "confidence": 0.92,
            "linked_to": "programa_igualdad_genero"
        }
    ],
    "category_totals": {
        "SGR": 250000000.0,
        "recursos_propios": 180000000.0
    }
}
Provides: "pdet_analysis.financial_data"
```

**10. PDETMunicipalPlanAnalyzer._extract_from_budget_table**
```python
Output: {
    "table_data": [
        {
            "table_id": "T-001",
            "row_label": "Programa: Mujeres Empoderadas",
            "column_label": "2024",
            "amount": 45000000.0
        }
    ],
    "tables_found": 3,
    "multi_year_tables": 2
}
Provides: "pdet_analysis.budget_tables"
```

### Group 5: Contradiction Detection (Methods 11-13)

**11. PolicyContradictionDetector._extract_quantitative_claims**
```python
Output: {
    "claims": [
        {
            "claim_id": "QC-001",
            "subject": "tasa de VBG",
            "value": 12.3,
            "unit": "%",
            "sentence_id": 45,
            "confidence": 0.91
        }
    ],
    "claim_count": 24
}
Provides: "contradiction_detection.quantitative_claims"
```

**12. PolicyContradictionDetector._parse_number**
```python
Output: {
    "parsed_numbers": [
        {
            "raw_text": "12,3%",
            "parsed_value": 12.3,
            "parsing_confidence": 0.97
        }
    ],
    "parsing_success_rate": 0.95
}
Provides: "contradiction_detection.parsed_numbers"
```

**13. PolicyContradictionDetector._statistical_significance_test**
```python
Output: {
    "test_results": [
        {
            "claim1_id": "QC-001",
            "claim2_id": "QC-012",
            "difference": 0.5,
            "p_value": 0.68,
            "significant": false,
            "interpretation": "No significant contradiction"
        }
    ],
    "contradictions_found": 0,
    "tests_performed": 15
}
Provides: "contradiction_detection.significance_tests"
```

### Group 6: Bayesian Analysis (Methods 14-15)

**14. BayesianNumericalAnalyzer.evaluate_policy_metric**
```python
Output: {
    "metrics": {
        "vbg_rate": {
            "posterior_mean": 0.123,
            "posterior_std": 0.012,
            "credible_interval_95": [0.11, 0.145],
            "prior_mean": 0.15,
            "data_updates_belief": true
        }
    },
    "metrics_evaluated": 8
}
Provides: "bayesian_analysis.policy_metrics"
```

**15. BayesianNumericalAnalyzer.compare_policies**
```python
Output: {
    "comparisons": [
        {
            "entity_a": "municipio_X",
            "entity_b": "promedio_nacional",
            "metric": "vbg_rate",
            "prob_a_higher": 0.87,
            "effect_size": 0.023,
            "interpretation": "Municipio X tiene tasa significativamente mayor"
        }
    ]
}
Provides: "bayesian_analysis.comparisons"
```

### Group 7: Semantic Processing (Methods 16-17)

**16. SemanticProcessor.chunk_text**
```python
Output: {
    "chunks": [
        {
            "chunk_id": 1,
            "text": "El diagnóstico de género del municipio muestra...",
            "start_pos": 0,
            "end_pos": 512,
            "token_count": 128
        }
    ],
    "chunk_count": 45,
    "avg_chunk_size": 120
}
Provides: "semantic_processing.chunks"
```

**17. SemanticProcessor.embed_single**
```python
Output: {
    "embeddings": [
        {
            "chunk_id": 1,
            "embedding": [0.023, -0.145, ..., 0.089],  # 768-dim vector
            "model_id": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
        }
    ],
    "embedding_dim": 768
}
Provides: "semantic_processing.embeddings"
```

---

## Evidence Assembly Process

Based on `assembly_rules` in contract:

### Rule 1: elements_found
```json
{
  "target": "elements_found",
  "sources": [
    "text_mining.critical_links",
    "industrial_policy.processed_evidence",
    "causal_extraction.goals",
    "financial_audit.amounts",
    "pdet_analysis.financial_data",
    "contradiction_detection.quantitative_claims",
    "bayesian_analysis.policy_metrics"
  ],
  "merge_strategy": "concat"
}
```

**Assembled Output**:
```python
{
  "elements_found": [
    # From industrial_policy.processed_evidence
    {"type": "quantitative_indicator", "value": "tasa de VBG: 12.3%", ...},
    {"type": "official_source", "value": "DANE", ...},
    # From financial_audit.amounts
    {"type": "financial_amount", "value": 15000000.0, "currency": "COP", ...},
    # From causal_extraction.goals
    {"type": "policy_goal", "goal_verb": "reducir", "target": "VBG", ...},
    # ... etc (concatenated)
  ]
}
```

### Rule 2: confidence_scores
```json
{
  "target": "confidence_scores",
  "sources": ["*.confidence", "*.bayesian_posterior"],
  "merge_strategy": "weighted_mean"
}
```

**Assembled Output**:
```python
{
  "confidence_scores": 0.876  # weighted mean of all confidence values
}
```

### Rule 3: pattern_matches
```json
{
  "target": "pattern_matches",
  "sources": ["text_mining.patterns", "industrial_policy.patterns"],
  "merge_strategy": "concat"
}
```

**Assembled Output**:
```python
{
  "pattern_matches": [
    {"pattern_id": "PAT-Q001-002", "matched_text": "según DANE", "sentence_id": 45},
    # ... all pattern matches
  ]
}
```

---

## Final Evidence Structure

After all 17 methods execute and evidence is assembled:

```json
{
  "elements_found": [
    {
      "element_id": "E-001",
      "type": "fuentes_oficiales",
      "value": "DANE",
      "confidence": 0.95,
      "source_method": "IndustrialPolicyProcessor._extract_point_evidence",
      "source_sentence": "según datos de DANE para el año 2022",
      "sentence_id": 45,
      "position": {"start": 123, "end": 145}
    },
    {
      "element_id": "E-002",
      "type": "indicadores_cuantitativos",
      "value": "tasa de VBG: 12.3%",
      "normalized_value": 12.3,
      "unit": "%",
      "confidence": 0.89,
      "source_method": "PolicyContradictionDetector._extract_quantitative_claims",
      "bayesian_posterior": {
        "mean": 0.123,
        "ci_95": [0.11, 0.145]
      },
      "sentence_id": 45
    },
    {
      "element_id": "E-003",
      "type": "series_temporales_años",
      "years": [2020, 2021, 2022],
      "confidence": 0.92,
      "source_method": "TextMiningEngine.diagnose_critical_links"
    },
    {
      "element_id": "E-004",
      "type": "cobertura_territorial_especificada",
      "coverage": "municipal - zona rural y urbana",
      "confidence": 0.88,
      "source_method": "CausalExtractor._parse_goal_context"
    }
  ],
  "elements_summary": {
    "total_count": 38,
    "by_type": {
      "fuentes_oficiales": 5,
      "indicadores_cuantitativos": 12,
      "series_temporales_años": 4,
      "cobertura_territorial_especificada": 1,
      "financial_amounts": 8,
      "policy_goals": 7,
      "causal_links": 5
    }
  },
  "confidence_scores": {
    "mean": 0.876,
    "std": 0.089,
    "min": 0.72,
    "max": 0.98,
    "by_method": {
      "TextMiningEngine": 0.83,
      "IndustrialPolicyProcessor": 0.91,
      "CausalExtractor": 0.79,
      "FinancialAuditor": 0.94,
      "PDETMunicipalPlanAnalyzer": 0.88,
      "PolicyContradictionDetector": 0.90,
      "BayesianNumericalAnalyzer": 0.92,
      "SemanticProcessor": 0.85
    }
  },
  "pattern_matches": [
    {"pattern_id": "PAT-Q001-000", "count": 3, "avg_confidence": 0.87},
    {"pattern_id": "PAT-Q001-001", "count": 12, "avg_confidence": 0.91},
    {"pattern_id": "PAT-Q001-002", "count": 5, "avg_confidence": 0.95}
  ],
  "critical_links": [
    {
      "cause": "alta tasa de VBG",
      "effect": "baja autonomía económica",
      "criticality": 0.87,
      "coherence": 0.82
    }
  ],
  "financial_summary": {
    "total_budget_cop": 850000000.0,
    "amounts_found": 12,
    "by_category": {
      "SGR": 250000000.0,
      "recursos_propios": 180000000.0,
      "transferencias": 120000000.0
    },
    "multi_year_commitment": true
  },
  "goals_summary": {
    "total_goals": 7,
    "quantified_goals": 5,
    "goals_with_complete_context": 4
  },
  "contradictions": {
    "found": 0,
    "tests_performed": 15,
    "interpretation": "No statistical contradictions in quantitative claims"
  },
  "bayesian_insights": {
    "metrics_with_high_uncertainty": [],
    "significant_comparisons": 1
  },
  "semantic_processing": {
    "chunks_created": 45,
    "embeddings_generated": 45,
    "avg_semantic_similarity_to_query": 0.78
  },
  "metadata": {
    "methods_executed": 17,
    "execution_time_ms": 2845,
    "document_length": 15230,
    "analysis_timestamp": "2025-11-26T12:34:56Z"
  }
}
```

---

## Validation Against Expected Elements

Contract specifies (from `expected_elements`):
- `cobertura_territorial_especificada` (required): ✅ Found (E-004)
- `fuentes_oficiales` (minimum 2): ✅ Found 5
- `indicadores_cuantitativos` (minimum 3): ✅ Found 12
- `series_temporales_años` (minimum 3): ✅ Found 4 (years: 2020, 2021, 2022, 2023)

**Validation Result**: ✅ **PASS** - All required and minimum elements present

---

## Human-Readable Output Template Variables

Based on this evidence structure, the template variables are populated:

- `{evidence.elements_found_count}` → `38`
- `{score}` → Calculated by scorer based on elements
- `{quality_level}` → "ALTO" (all requirements met)
- `{evidence.confidence_scores.mean}` → `87.6`
- `{evidence.pattern_matches_count}` → `14` (all 14 patterns detected)
- `{evidence.official_sources_count}` → `5`
- `{evidence.quantitative_indicators_count}` → `12`
- `{evidence.temporal_series_count}` → `4`
- `{evidence.territorial_coverage}` → "municipal - zona rural y urbana"

---

## Conclusion

This structure represents the **expected output** when all 17 methods execute successfully and their outputs are assembled according to the contract's `assembly_rules`. It provides:

1. **Concrete data types** for each method output
2. **Assembly logic** showing how 17 outputs merge into unified evidence
3. **Validation mapping** to contract's `expected_elements`
4. **Template variable bindings** for human-readable output

This structure should be added to the contract as `human_answer_structure` to make the contract **fully actionable** for developers.
