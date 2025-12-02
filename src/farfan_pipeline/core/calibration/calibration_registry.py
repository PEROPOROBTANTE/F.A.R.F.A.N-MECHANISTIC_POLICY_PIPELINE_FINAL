from typing import Any, Dict

CALIBRATIONS: Dict[str, Dict[str, Any]] = {
    "farfan_core.analysis.derek_beach.BayesianThresholdsConfig": {
        "kl_divergence": 0.01,
        "convergence_min_evidence": 2,
        "prior_alpha": 2.0,
        "prior_beta": 2.0,
        "laplace_smoothing": 1.0,
    },
    "farfan_core.analysis.derek_beach.MechanismTypeConfig": {
        "administrativo": 0.30,
        "tecnico": 0.25,
        "financiero": 0.20,
        "politico": 0.15,
        "mixto": 0.10,
    },
    "farfan_core.analysis.derek_beach.ConfigLoader._load_default_config": {
        "kl_divergence": 0.01,
        "convergence_min_evidence": 2,
        "prior_alpha": 2.0,
        "prior_beta": 2.0,
        "laplace_smoothing": 1.0,
        "administrativo": 0.30,
        "tecnico": 0.25,
        "financiero": 0.20,
        "politico": 0.15,
        "mixto": 0.10,
        "feedback_weight": 0.1,
    },
    "farfan_core.analysis.derek_beach.ConfigLoader.get_bayesian_threshold": {
        "default": 0.01,
    },
    "farfan_core.analysis.derek_beach.ConfigLoader.get_mechanism_prior": {
        "default": 0.0,
    },
    "farfan_core.analysis.derek_beach.CausalExtractor._calculate_semantic_distance": {
        "default": 0.5,
    },
    "farfan_core.analysis.derek_beach.CausalExtractor._calculate_type_transition_prior": {
        "('programa', 'producto')": 0.85,
        "('producto', 'resultado')": 0.80,
        "('resultado', 'impacto')": 0.75,
        "('programa', 'resultado')": 0.60,
        "('producto', 'impacto')": 0.50,
        "('programa', 'impacto')": 0.30,
        "reverse_multiplier": 0.3,
        "default": 0.40,
    },
    "farfan_core.analysis.derek_beach.CausalExtractor._extract_causal_links": {
        "structural_veto_threshold": 0.6,
        "final_kl_default": 0.0,
    },
    "farfan_core.analysis.derek_beach.CausalExtractor._calculate_language_specificity": {
        "base_score": 0.6,
        "strong_indicator_score": 0.9,
        "moderate_indicator_score": 0.7,
        "weak_indicator_score": 0.5,
        "policy_specificity_boost": 0.15,
        "contextual_specificity_boost": 0.10,
        "final_score_max": 1.0,
    },
    "farfan_core.analysis.derek_beach.CausalExtractor._assess_temporal_coherence": {
        "default": 0.5,
        "in_sequence": 0.85,
        "same_sequence": 0.60,
        "reverse_sequence": 0.30,
    },
    "farfan_core.analysis.derek_beach.CausalExtractor._assess_financial_consistency": {
        "default": 0.5,
        "consistent_min": 0.1,
        "consistent_max": 1.0,
        "consistent_score": 0.85,
        "slightly_inconsistent_max": 1.5,
        "slightly_inconsistent_score": 0.60,
        "very_inconsistent_score": 0.30,
    },
    "farfan_core.analysis.derek_beach.CausalExtractor._calculate_textual_proximity": {
        "default": 0.5,
    },
    "farfan_core.analysis.derek_beach.CausalExtractor._calculate_composite_likelihood": {
        "semantic_distance_weight": 0.25,
        "type_transition_prior_weight": 0.20,
        "language_specificity_weight": 0.20,
        "temporal_coherence_weight": 0.15,
        "financial_consistency_weight": 0.10,
        "textual_proximity_weight": 0.10,
        "likelihood": 0.0,
        "triangulation_bonus_3": 1.15,
        "triangulation_bonus_2": 1.05,
        "triangulation_bonus_default": 1.0,
        "enhanced_likelihood_max": 1.0,
        "insufficient_evidence_penalty": 0.85,
    },
    "farfan_core.analysis.derek_beach.CausalExtractor._build_type_hierarchy": {
        "inferred_strength": 0.5,
    },
    "farfan_core.analysis.derek_beach.CausalExtractor._calculate_confidence": {
        "confidence": 0.5,
        "quantitative_target_bonus": 0.2,
        "causal_indicator_bonus": 0.15,
        "strong_rigor_bonus": 0.15,
        "weak_rigor_penalty": 0.1,
        "max_confidence": 1.0,
        "min_confidence": 0.0,
    },
    "farfan_core.analysis.derek_beach.CausalExtractor._extract_causal_justifications": {
        "confidence": 0.7,
    },
    "farfan_core.analysis.derek_beach.MechanismPartExtractor.extract_entity_activity": {
        "confidence": 0.85,
    },
    "farfan_core.analysis.derek_beach.MechanismPartExtractor._calculate_ea_confidence": {
        "confidence": 0.5,
        "known_entity_bonus": 0.2,
        "strong_verb_bonus": 0.15,
        "grammatical_connection_bonus": 0.15,
        "max_confidence": 1.0,
    },
    "farfan_core.analysis.derek_beach.FinancialAuditor._match_program_to_node": {
        "penalty_factor": 0.85,
        "match_confidence_divisor": 100.0,
    },
    "farfan_core.analysis.derek_beach.FinancialAuditor._perform_counterfactual_budget_check": {
        "necessity_score": 0.0,
        "budget_mechanism_bonus": 0.40,
        "budget_dependency_bonus": 0.30,
        "specific_allocation_bonus": 0.30,
        "excellent_threshold": 0.85,
        "good_threshold": 0.70,
        "acceptable_threshold": 0.50,
        "sufficient_threshold": 0.50,
        "necessary_threshold": 0.70,
    },
    "farfan_core.analysis.derek_beach.FinancialAuditor._calculate_sufficiency": {
        "default": 0.0,
    },
    "farfan_core.analysis.derek_beach.FinancialAuditor._detect_allocation_gaps": {
        "sufficiency_threshold": 0.5,
    },
    "farfan_core.analysis.derek_beach.FinancialAuditor._match_goal_to_budget": {
        "score_threshold": 0.3,
    },
    "farfan_core.analysis.derek_beach.OperationalizationAuditor.audit_evidence_traceability": {
        "partial_credit": 0.5,
    },
    "farfan_core.analysis.derek_beach.OperationalizationAuditor.bayesian_counterfactual_audit": {
        "success_probability_default": 0.0,
        "risk_score_default": 0.0,
    },
    "farfan_core.analysis.derek_beach.OperationalizationAuditor._get_default_historical_priors": {
        "entity_presence_success_rate": 0.94,
        "baseline_presence_success_rate": 0.89,
        "target_presence_success_rate": 0.92,
        "budget_presence_success_rate": 0.78,
        "mechanism_presence_success_rate": 0.65,
        "complete_documentation_success_rate": 0.82,
        "producto_success_rate": 0.85,
        "resultado_success_rate": 0.72,
        "impacto_success_rate": 0.58,
    },
    "farfan_core.analysis.derek_beach.OperationalizationAuditor._audit_direct_evidence": {
        "unwanted_effects_prior_beta": 10.5,
    },
}

def get_calibration(method_id: str) -> Dict[str, Any]:
    """
    Retrieves the calibration parameters for a given method_id.
    """
    return CALIBRATIONS.get(method_id, {})
