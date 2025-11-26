#!/usr/bin/env python3
"""
Generate the final D1-Q1.v3.CANONICAL.json with:
1. Correct method_binding.methods array (17 methods)
2. Complete human_answer_structure section
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# Load current contract
current_contract_path = PROJECT_ROOT / "config" / "executor_contracts" / "D1-Q1.v3.CANONICAL.json"
with open(current_contract_path) as f:
    contract = json.load(f)

# Load methods mapping
methods_mapping_path = PROJECT_ROOT / "executor_methods_mapping.json"
with open(methods_mapping_path) as f:
    methods_mapping = json.load(f)

d1q1_methods = methods_mapping["D1-Q1"]

# Define role mapping for each method
method_roles = {
    "diagnose_critical_links": "critical_link_diagnosis",
    "_analyze_link_text": "link_context_analysis",
    "process": "industrial_policy_pattern_processing",
    "_match_patterns_in_sentences": "sentence_level_pattern_matching",
    "_extract_point_evidence": "point_evidence_extraction",
    "_extract_goals": "goal_extraction",
    "_parse_goal_context": "goal_contextualization",
    "_parse_amount": "financial_amount_parsing",
    "_extract_financial_amounts": "pdet_specific_financial_extraction",
    "_extract_from_budget_table": "structured_budget_table_extraction",
    "_extract_quantitative_claims": "quantitative_claim_extraction",
    "_parse_number": "numeric_value_parsing",
    "_statistical_significance_test": "statistical_significance_testing",
    "evaluate_policy_metric": "bayesian_metric_evaluation",
    "compare_policies": "bayesian_policy_comparison",
    "chunk_text": "text_chunking_for_embedding",
    "embed_single": "semantic_embedding",
}

# Define provides mapping (dot-notation keys)
method_provides = {
    "diagnose_critical_links": "text_mining.critical_links",
    "_analyze_link_text": "text_mining.link_analysis",
    "process": "industrial_policy.structure",
    "_match_patterns_in_sentences": "industrial_policy.sentence_patterns",
    "_extract_point_evidence": "industrial_policy.processed_evidence",
    "_extract_goals": "causal_extraction.goals",
    "_parse_goal_context": "causal_extraction.goal_contexts",
    "_parse_amount": "financial_audit.amounts",
    "_extract_financial_amounts": "pdet_analysis.financial_data",
    "_extract_from_budget_table": "pdet_analysis.budget_tables",
    "_extract_quantitative_claims": "contradiction_detection.quantitative_claims",
    "_parse_number": "contradiction_detection.parsed_numbers",
    "_statistical_significance_test": "contradiction_detection.significance_tests",
    "evaluate_policy_metric": "bayesian_analysis.policy_metrics",
    "compare_policies": "bayesian_analysis.comparisons",
    "chunk_text": "semantic_processing.chunks",
    "embed_single": "semantic_processing.embeddings",
}

# Build methods array
methods_array = []
for i, method_info in enumerate(d1q1_methods, start=1):
    class_name = method_info["class"]
    method_name = method_info["method"]

    methods_array.append({
        "class_name": class_name,
        "method_name": method_name,
        "priority": i,
        "provides": method_provides.get(method_name, f"{class_name}.{method_name}"),
        "role": method_roles.get(method_name, f"{class_name}_{method_name}")
    })

# Update method_binding
contract["method_binding"] = {
    "orchestration_mode": "multi_method_pipeline",
    "method_count": 17,
    "methods": methods_array,
    "note": "All 17 methods extracted from D1_Q1_QuantitativeBaselineExtractor in executors.py"
}

# Add human_answer_structure
contract["human_answer_structure"] = {
    "description": "Expected structure of evidence dict after all 17 methods execute and evidence is assembled according to assembly_rules",
    "assembly_flow": {
        "step_1_method_execution": "17 methods execute in priority order, outputs stored with dot-notation keys",
        "step_2_evidence_assembly": "EvidenceAssembler merges outputs according to assembly_rules",
        "step_3_validation": "EvidenceValidator checks against validation_rules",
        "step_4_output_generation": "Phase2QuestionResult constructed with evidence, validation, trace"
    },
    "evidence_structure_schema": {
        "type": "object",
        "description": "Assembled evidence after all methods complete",
        "properties": {
            "elements_found": {
                "type": "array",
                "description": "Concatenated evidence elements from multiple methods (assembly_rules target)",
                "items": {
                    "type": "object",
                    "properties": {
                        "element_id": {"type": "string", "example": "E-001"},
                        "type": {
                            "type": "string",
                            "enum": [
                                "fuentes_oficiales",
                                "indicadores_cuantitativos",
                                "series_temporales_años",
                                "cobertura_territorial_especificada",
                                "financial_amounts",
                                "policy_goals",
                                "causal_links"
                            ]
                        },
                        "value": {"type": "string", "example": "DANE"},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        "source_method": {"type": "string", "example": "IndustrialPolicyProcessor._extract_point_evidence"},
                        "sentence_id": {"type": "integer"},
                        "context": {"type": "string"}
                    }
                },
                "example_count": "Expected 15-50 elements for a complete diagnostic"
            },
            "elements_summary": {
                "type": "object",
                "properties": {
                    "total_count": {"type": "integer"},
                    "by_type": {
                        "type": "object",
                        "properties": {
                            "fuentes_oficiales": {"type": "integer", "minimum_expected": 2},
                            "indicadores_cuantitativos": {"type": "integer", "minimum_expected": 3},
                            "series_temporales_años": {"type": "integer", "minimum_expected": 3},
                            "cobertura_territorial_especificada": {"type": "integer", "minimum_expected": 1}
                        }
                    }
                }
            },
            "confidence_scores": {
                "type": "object",
                "description": "Aggregated confidence metrics (weighted_mean strategy)",
                "properties": {
                    "mean": {"type": "number"},
                    "std": {"type": "number"},
                    "min": {"type": "number"},
                    "max": {"type": "number"},
                    "by_method": {
                        "type": "object",
                        "description": "Average confidence per analyzer class"
                    }
                }
            },
            "pattern_matches": {
                "type": "array",
                "description": "Aggregated pattern matches from text mining methods",
                "items": {
                    "type": "object",
                    "properties": {
                        "pattern_id": {"type": "string"},
                        "count": {"type": "integer"},
                        "avg_confidence": {"type": "number"}
                    }
                }
            },
            "critical_links": {
                "type": "array",
                "description": "Causal links extracted by TextMiningEngine",
                "items": {
                    "type": "object",
                    "properties": {
                        "cause": {"type": "string"},
                        "effect": {"type": "string"},
                        "criticality": {"type": "number"},
                        "coherence": {"type": "number"}
                    }
                }
            },
            "financial_summary": {
                "type": "object",
                "description": "Aggregated financial data from FinancialAuditor and PDETMunicipalPlanAnalyzer",
                "properties": {
                    "total_budget_cop": {"type": "number"},
                    "amounts_found": {"type": "integer"},
                    "by_category": {
                        "type": "object",
                        "properties": {
                            "SGR": {"type": "number"},
                            "recursos_propios": {"type": "number"},
                            "transferencias": {"type": "number"}
                        }
                    }
                }
            },
            "goals_summary": {
                "type": "object",
                "description": "Policy goals extracted by CausalExtractor",
                "properties": {
                    "total_goals": {"type": "integer"},
                    "quantified_goals": {"type": "integer"},
                    "goals_with_complete_context": {"type": "integer"}
                }
            },
            "contradictions": {
                "type": "object",
                "description": "Results from PolicyContradictionDetector",
                "properties": {
                    "found": {"type": "integer"},
                    "tests_performed": {"type": "integer"},
                    "interpretation": {"type": "string"}
                }
            },
            "bayesian_insights": {
                "type": "object",
                "description": "Results from BayesianNumericalAnalyzer",
                "properties": {
                    "metrics_with_high_uncertainty": {"type": "array"},
                    "significant_comparisons": {"type": "integer"}
                }
            },
            "semantic_processing": {
                "type": "object",
                "description": "Results from SemanticProcessor",
                "properties": {
                    "chunks_created": {"type": "integer"},
                    "embeddings_generated": {"type": "integer"},
                    "avg_semantic_similarity_to_query": {"type": "number"}
                }
            },
            "metadata": {
                "type": "object",
                "properties": {
                    "methods_executed": {"type": "integer", "const": 17},
                    "execution_time_ms": {"type": "number"},
                    "document_length": {"type": "integer"},
                    "analysis_timestamp": {"type": "string", "format": "date-time"}
                }
            }
        }
    },
    "concrete_example": {
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
                "recursos_propios": 180000000.0
            }
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
    },
    "validation_against_expected_elements": {
        "cobertura_territorial_especificada": {
            "required": True,
            "found_in_example": True,
            "example_element_id": "E-004"
        },
        "fuentes_oficiales": {
            "minimum": 2,
            "found_in_example": 5,
            "status": "PASS"
        },
        "indicadores_cuantitativos": {
            "minimum": 3,
            "found_in_example": 12,
            "status": "PASS"
        },
        "series_temporales_años": {
            "minimum": 3,
            "found_in_example": 4,
            "status": "PASS"
        },
        "overall_validation_result": "PASS - All required and minimum elements present"
    },
    "template_variable_bindings": {
        "description": "These variables are available for human_readable_output template",
        "variables": {
            "{evidence.elements_found_count}": 38,
            "{score}": "Calculated by scorer based on elements",
            "{quality_level}": "ALTO",
            "{evidence.confidence_scores.mean}": "87.6%",
            "{evidence.pattern_matches_count}": 14,
            "{evidence.official_sources_count}": 5,
            "{evidence.quantitative_indicators_count}": 12,
            "{evidence.temporal_series_count}": 4,
            "{evidence.territorial_coverage}": "municipal - zona rural y urbana"
        }
    },
    "usage_notes": {
        "for_developers": "This structure shows the expected evidence dict after BaseExecutorWithContract._execute_v3() completes all 17 method executions and evidence assembly.",
        "for_validators": "Use this to verify that actual execution output matches expected structure.",
        "for_auditors": "This provides traceability from raw method outputs to final assembled evidence."
    }
}

# Update traceability
contract["traceability"]["contract_generation_method"] = "canonical_prompt_v3_with_multi_method_refactoring"
contract["traceability"]["provenance_note"] = "This contract was generated with full multi-method orchestration support. The method_binding.methods array contains all 17 methods from D1_Q1_QuantitativeBaselineExtractor, and human_answer_structure documents the expected evidence output after execution."

# Write updated contract
output_path = PROJECT_ROOT / "config" / "executor_contracts" / "D1-Q1.v3.FINAL.json"
with open(output_path, 'w') as f:
    json.dump(contract, f, indent=2, ensure_ascii=False)

print(f"✅ Generated: {output_path}")
print(f"   - method_binding.methods: {len(methods_array)} methods")
print(f"   - human_answer_structure: Complete with schema, example, and validation")
print(f"   - File size: {output_path.stat().st_size:,} bytes")
