"""
Three-Pillar Calibration System - Layer Computation Functions

This module implements the 8 layer score computation functions as specified
in the SUPERPROMPT Three-Pillar Calibration System.

Spec compliance: Section 3 (Layer Architecture)
"""

import json
import math
from pathlib import Path
from typing import Any

from farfan_pipeline.core.calibration.data_structures import (
    CalibrationConfigError,
    ComputationGraph,
    InterplaySubgraph,
    MethodRole,
)

_unit_transforms_config: dict[str, Any] | None = None


def _load_unit_transforms_config() -> dict[str, Any]:
    """Load unit transforms configuration from system/config/calibration/unit_transforms.json."""
    global _unit_transforms_config

    if _unit_transforms_config is not None:
        return _unit_transforms_config

    config_path = Path("system/config/calibration/unit_transforms.json")
    if not config_path.exists():
        raise FileNotFoundError(f"Unit transforms config not found: {config_path}")

    with open(config_path, encoding='utf-8') as f:
        _unit_transforms_config = json.load(f)

    return _unit_transforms_config


def compute_base_layer(method_id: str, intrinsic_config: dict[str, Any]) -> float:
    """
    Compute base layer score (@b): Intrinsic quality
    
    Spec compliance: Section 3.1
    Formula: x_@b = w_th · b_theory + w_imp · b_impl + w_dep · b_deploy
    
    Args:
        method_id: Canonical method ID
        intrinsic_config: Loaded intrinsic_calibration.json
    
    Returns:
        Score in [0,1]
    
    Raises:
        ValueError: If method not found or scores invalid
    """
    if method_id not in intrinsic_config.get("methods", {}):
        raise ValueError(f"Method {method_id} not found in intrinsic_calibration.json")

    method_data = intrinsic_config["methods"][method_id]
    weights = intrinsic_config["_base_weights"]

    b_theory = method_data["b_theory"]
    b_impl = method_data["b_impl"]
    b_deploy = method_data["b_deploy"]

    # Validate bounds
    for name, value in [("b_theory", b_theory), ("b_impl", b_impl), ("b_deploy", b_deploy)]:
        if not (0.0 <= value <= 1.0):
            raise ValueError(f"{name} must be in [0,1], got {value}")

    # Compute weighted sum
    score = (weights["w_th"] * b_theory +
             weights["w_imp"] * b_impl +
             weights["w_dep"] * b_deploy)

    return score


def compute_chain_layer(node_id: str, graph: ComputationGraph,
                       contextual_config: dict[str, Any]) -> float:
    """
    Compute chain compatibility layer (@chain)
    
    Spec compliance: Section 3.2
    Rule-based discrete mapping
    
    Args:
        node_id: Node identifier
        graph: Computation graph containing node
        contextual_config: Loaded contextual_parametrization.json (deprecated, use unit_transforms.json)
    
    Returns:
        Score in [0,1]
    """
    if node_id not in graph.nodes:
        raise ValueError(f"Node {node_id} not in graph")

    config = _load_unit_transforms_config()
    mappings = config.get("chain_layer", {}).get("discrete_mappings", {})

    if not mappings:
        mappings = contextual_config.get("layer_chain", {}).get("discrete_mappings", {})

    signature = graph.node_signatures.get(node_id, {})
    required_inputs = signature.get("required_inputs", [])

    has_hard_mismatch = False

    incoming_edges = [e for e in graph.edges if e[1] == node_id]

    if not incoming_edges and required_inputs:
        has_hard_mismatch = True

    if has_hard_mismatch:
        return mappings.get("hard_mismatch", 0.0)
    else:
        return mappings.get("all_contracts_pass_no_warnings", 1.0)


def compute_unit_layer(method_id: str, role: MethodRole, unit_quality: float,
                      contextual_config: dict[str, Any]) -> float:
    """
    Compute unit-of-analysis sensitivity layer (@u)
    
    Spec compliance: Section 3.3
    Formula: x_@u = g_M(U) if M is U-sensitive, else 1.0
    
    Args:
        method_id: Canonical method ID
        role: Method role
        unit_quality: U in [0,1]
        contextual_config: Loaded contextual_parametrization.json (deprecated, use unit_transforms.json)
    
    Returns:
        Score in [0,1]
    """
    if not (0.0 <= unit_quality <= 1.0):
        raise ValueError(f"unit_quality must be in [0,1], got {unit_quality}")

    config = _load_unit_transforms_config()
    g_functions_config = config.get("g_functions", {})

    role_name = role.value

    g_spec = None
    for g_name, g_def in g_functions_config.items():
        if role_name in g_def.get("applicable_roles", []):
            g_spec = g_def
            break

    if g_spec is None:
        return 1.0

    g_type = g_spec["type"]

    if g_type == "identity":
        return unit_quality

    elif g_type == "constant":
        return g_spec.get("value", 1.0)

    elif g_type == "piecewise_linear":
        abort_threshold = g_spec.get("abort_threshold", 0.3)
        if unit_quality < abort_threshold:
            return 0.0
        slope = g_spec.get("slope", 2.0)
        offset = g_spec.get("offset", -0.6)
        score = slope * unit_quality + offset

        if score < 0.0 or score > 1.0:
            raise CalibrationConfigError(
                f"Unit layer g_function produced out-of-range score: {score} "
                f"for unit_quality={unit_quality}. Config must be adjusted to ensure [0,1] output."
            )
        return score

    elif g_type == "sigmoidal":
        k = g_spec.get("k", 5.0)
        x0 = g_spec.get("x0", 0.5)
        score = 1.0 - math.exp(-k * (unit_quality - x0))

        if score < 0.0 or score > 1.0:
            raise CalibrationConfigError(
                f"Unit layer g_function produced out-of-range score: {score} "
                f"for unit_quality={unit_quality}, k={k}, x0={x0}. "
                f"Config must be adjusted to ensure [0,1] output."
            )
        return score

    else:
        raise ValueError(f"Unknown g_function type: {g_type}")


def compute_question_layer(method_id: str, question_id: str | None,
                          monolith: dict[str, Any],
                          contextual_config: dict[str, Any]) -> float:
    """
    Compute question compatibility layer (@q)
    
    Spec compliance: Section 3.4
    Formula: x_@q = Q_f(M | Q)
    
    Args:
        method_id: Canonical method ID
        question_id: Question ID (or None)
        monolith: Loaded questionnaire_monolith.json
        contextual_config: Loaded contextual_parametrization.json (deprecated, use unit_transforms.json)
    
    Returns:
        Score in [0,1]
    """
    config = _load_unit_transforms_config()
    levels = config.get("question_layer", {}).get("compatibility_levels", {})

    if not levels:
        levels = contextual_config.get("layer_question", {}).get("compatibility_levels", {})

    if question_id is None:
        return levels.get("undeclared", 0.6)

    micro_questions = monolith.get("blocks", {}).get("micro_questions", [])
    question = None
    for q in micro_questions:
        if q.get("question_id") == question_id:
            question = q
            break

    if not question:
        return levels.get("undeclared", 0.6)

    method_sets = question.get("method_sets", [])

    for method_spec in method_sets:
        if (method_id.endswith(f".{method_spec.get('function', '')}") or
            method_spec.get('class', '') in method_id):

            method_type = method_spec.get("method_type", "")
            priority = method_spec.get("priority", 99)

            if method_type == "extraction" or priority == 1:
                return levels.get("primary", 1.0)
            elif priority == 2:
                return levels.get("secondary", 0.8)
            elif method_type == "validation":
                return levels.get("validator", 0.9)

    return levels.get("undeclared", 0.6)


def compute_dimension_layer(method_id: str, dimension_id: str,
                           contextual_config: dict[str, Any]) -> float:
    """
    Compute dimension compatibility layer (@d)
    
    Spec compliance: Section 3.5
    Formula: x_@d = D_f(M | D)
    
    Args:
        method_id: Canonical method ID
        dimension_id: Dimension ID (DIM01-DIM06)
        contextual_config: Loaded contextual_parametrization.json (deprecated, use unit_transforms.json)
    
    Returns:
        Score in [0,1]
    """
    config = _load_unit_transforms_config()
    alignment = config.get("dimension_layer", {}).get("alignment_matrix", {})

    if not alignment:
        alignment = contextual_config.get("layer_dimension", {}).get("alignment_matrix", {})

    if dimension_id not in alignment:
        raise ValueError(f"Unknown dimension: {dimension_id}")

    dim_spec = alignment[dimension_id]

    return dim_spec.get("default_score", 1.0)


def compute_policy_layer(method_id: str, policy_id: str,
                        contextual_config: dict[str, Any]) -> float:
    """
    Compute policy area compatibility layer (@p)
    
    Spec compliance: Section 3.6
    Formula: x_@p = P_f(M | P)
    
    Args:
        method_id: Canonical method ID
        policy_id: Policy area ID (PA01-PA10)
        contextual_config: Loaded contextual_parametrization.json (deprecated, use unit_transforms.json)
    
    Returns:
        Score in [0,1]
    """
    config = _load_unit_transforms_config()
    policies = config.get("policy_layer", {}).get("policy_areas", {})

    if not policies:
        policies = contextual_config.get("layer_policy", {}).get("policy_areas", {})

    if policy_id not in policies:
        raise ValueError(f"Unknown policy area: {policy_id}")

    policy_spec = policies[policy_id]

    return policy_spec.get("default_score", 0.9)


def compute_interplay_layer(interplay: InterplaySubgraph | None,
                           contextual_config: dict[str, Any]) -> float:
    """
    Compute interplay congruence layer (@C)
    
    Spec compliance: Section 3.7
    Formula: C_play(G | ctx) = c_scale · c_sem · c_fusion
    
    Args:
        interplay: Interplay subgraph (or None)
        contextual_config: Loaded contextual_parametrization.json (deprecated, use unit_transforms.json)
    
    Returns:
        Score in [0,1]
    """
    config = _load_unit_transforms_config()
    interplay_config = config.get("interplay_layer", {})

    if not interplay_config:
        interplay_config = contextual_config.get("layer_interplay", {})

    if interplay is None:
        return interplay_config.get("default_when_not_in_interplay", 1.0)

    components = interplay_config.get("components", {})

    c_scale = components.get("c_scale", {}).get("same_range", 1.0)
    c_sem = 1.0
    c_fusion = components.get("c_fusion", {}).get("declared_and_satisfied", 1.0)

    return c_scale * c_sem * c_fusion


def compute_meta_layer(evidence: dict[str, Any],
                      contextual_config: dict[str, Any]) -> float:
    """
    Compute meta/governance layer (@m)
    
    Spec compliance: Section 3.8
    Formula: x_@m = 0.5 · m_transp + 0.4 · m_gov + 0.1 · m_cost
    
    Args:
        evidence: Evidence dictionary with metrics
        contextual_config: Loaded contextual_parametrization.json (deprecated, use unit_transforms.json)
    
    Returns:
        Score in [0,1]
    """
    config = _load_unit_transforms_config()
    meta_spec = config.get("meta_layer", {})

    if not meta_spec:
        meta_spec = contextual_config.get("layer_meta", {})

    transp_conditions = [
        evidence.get("formula_export_valid", False),
        evidence.get("trace_complete", False),
        evidence.get("logs_conform_schema", False)
    ]
    transp_count = sum(transp_conditions)

    transp_values = meta_spec.get("components", {}).get("m_transp", {})
    if transp_count == 3:
        m_transp = transp_values.get("all_three_conditions", 1.0)
    elif transp_count == 2:
        m_transp = transp_values.get("two_of_three", 0.8)
    elif transp_count == 1:
        m_transp = transp_values.get("one_of_three", 0.5)
    else:
        m_transp = transp_values.get("none", 0.0)

    gov_conditions = [
        evidence.get("version_tagged", False),
        evidence.get("config_hash_matches", False),
        evidence.get("signature_valid", False)
    ]
    gov_count = sum(gov_conditions)

    gov_values = meta_spec.get("components", {}).get("m_gov", {})
    if gov_count == 3:
        m_gov = gov_values.get("all_three_conditions", 1.0)
    elif gov_count == 2:
        m_gov = gov_values.get("two_of_three", 0.8)
    elif gov_count == 1:
        m_gov = gov_values.get("one_of_three", 0.5)
    else:
        m_gov = gov_values.get("none", 0.0)

    runtime_ms = evidence.get("runtime_ms", 100)
    thresholds = meta_spec.get("components", {}).get("m_cost", {}).get("thresholds", {})

    fast_threshold = thresholds.get("fast_runtime_ms", 50)
    acceptable_threshold = thresholds.get("acceptable_runtime_ms", 200)

    cost_values = meta_spec.get("components", {}).get("m_cost", {})
    if runtime_ms < fast_threshold:
        m_cost = cost_values.get("fast", 1.0)
    elif runtime_ms < acceptable_threshold:
        m_cost = cost_values.get("acceptable", 0.8)
    else:
        m_cost = cost_values.get("slow", 0.5)

    weights = meta_spec.get("aggregation", {}).get("weights", {})
    score = (weights.get("transparency", 0.5) * m_transp +
             weights.get("governance", 0.4) * m_gov +
             weights.get("cost", 0.1) * m_cost)

    return score
