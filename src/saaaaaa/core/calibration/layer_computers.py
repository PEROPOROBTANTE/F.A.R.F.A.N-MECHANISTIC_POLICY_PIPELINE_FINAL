"""
Three-Pillar Calibration System - Layer Computation Functions

This module implements the 8 layer score computation functions as specified
in the SUPERPROMPT Three-Pillar Calibration System.

Spec compliance: Section 3 (Layer Architecture)
"""

import math
from typing import Any

from .data_structures import (
    CalibrationConfigError,
    ComputationGraph,
    InterplaySubgraph,
    MethodRole,
)


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
        contextual_config: Loaded contextual_parametrization.json

    Returns:
        Score in [0,1]
    """
    if node_id not in graph.nodes:
        raise ValueError(f"Node {node_id} not in graph")

    mappings = contextual_config["layer_chain"]["discrete_mappings"]

    # Check for hard mismatches (simplified - would need full schema validation)
    signature = graph.node_signatures.get(node_id, {})
    required_inputs = signature.get("required_inputs", [])

    # Simplified validation logic
    has_hard_mismatch = False

    # Check incoming edges for type compatibility
    incoming_edges = [e for e in graph.edges if e[1] == node_id]

    if not incoming_edges and required_inputs:
        has_hard_mismatch = True

    if has_hard_mismatch:
        return mappings["hard_mismatch"]
    # The following branches are unreachable because has_soft_violation and has_warnings are never set to True.
    # If future logic is added to set these flags, restore these branches.
    else:
        return mappings["all_contracts_pass_no_warnings"]


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
        contextual_config: Loaded contextual_parametrization.json

    Returns:
        Score in [0,1]
    """
    if not (0.0 <= unit_quality <= 1.0):
        raise ValueError(f"unit_quality must be in [0,1], got {unit_quality}")

    g_functions = contextual_config["layer_unit_of_analysis"]["g_functions"]
    role_name = role.value

    if role_name not in g_functions:
        # Default: not sensitive
        return 1.0

    g_spec = g_functions[role_name]
    g_type = g_spec["type"]

    if g_type == "identity":
        return unit_quality

    elif g_type == "constant":
        return 1.0

    elif g_type == "piecewise_linear":
        # g(U) = 2*U - 0.6 if U >= 0.3 else 0
        # Per canonic_calibration_methods.md: NO clamping - weights must be configured correctly
        abort_threshold = g_spec.get("abort_threshold", 0.3)
        if unit_quality < abort_threshold:
            return 0.0
        score = 2.0 * unit_quality - 0.6

        # Validate that config produces valid result
        if score < 0.0 or score > 1.0:
            raise CalibrationConfigError(
                f"Unit layer g_function produced out-of-range score: {score} "
                f"for unit_quality={unit_quality}. Config must be adjusted to ensure [0,1] output."
            )
        return score

    elif g_type == "sigmoidal":
        # g(U) = 1 - exp(-k*(U - x0))
        # Per canonic_calibration_methods.md: NO clamping - config must produce [0,1]
        k = g_spec.get("sigmoidal_k", 5.0)
        x0 = g_spec.get("sigmoidal_x0", 0.5)
        score = 1.0 - math.exp(-k * (unit_quality - x0))

        # Validate that config produces valid result
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
        contextual_config: Loaded contextual_parametrization.json

    Returns:
        Score in [0,1]
    """
    if question_id is None:
        # No specific question context
        return contextual_config["layer_question"]["compatibility_levels"]["undeclared"]

    levels = contextual_config["layer_question"]["compatibility_levels"]

    # Find question in monolith
    micro_questions = monolith.get("blocks", {}).get("micro_questions", [])
    question = None
    for q in micro_questions:
        if q.get("question_id") == question_id:
            question = q
            break

    if not question:
        return levels["undeclared"]

    # Check method_sets
    method_sets = question.get("method_sets", [])

    for method_spec in method_sets:
        # Match by function name or class name (simplified)
        if (method_id.endswith(f".{method_spec.get('function', '')}") or
            method_spec.get('class', '') in method_id):

            method_type = method_spec.get("method_type", "")
            priority = method_spec.get("priority", 99)

            if method_type == "extraction" or priority == 1:
                return levels["primary"]
            elif priority == 2:
                return levels["secondary"]
            elif method_type == "validation":
                return levels["validator"]

    return levels["undeclared"]


def compute_dimension_layer(method_id: str, dimension_id: str,
                           contextual_config: dict[str, Any]) -> float:
    """
    Compute dimension compatibility layer (@d)

    Spec compliance: Section 3.5
    Formula: x_@d = D_f(M | D)

    Args:
        method_id: Canonical method ID
        dimension_id: Dimension ID (DIM01-DIM06)
        contextual_config: Loaded contextual_parametrization.json

    Returns:
        Score in [0,1]
    """
    alignment = contextual_config["layer_dimension"]["alignment_matrix"]

    if dimension_id not in alignment:
        raise ValueError(f"Unknown dimension: {dimension_id}")

    dim_spec = alignment[dimension_id]

    # Simplified: return default score
    # Full implementation would check method family compatibility
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
        contextual_config: Loaded contextual_parametrization.json

    Returns:
        Score in [0,1]
    """
    policies = contextual_config["layer_policy"]["policy_areas"]

    if policy_id not in policies:
        raise ValueError(f"Unknown policy area: {policy_id}")

    policy_spec = policies[policy_id]

    # Return default score (0.9 to satisfy anti-universality)
    return policy_spec.get("default_score", 0.9)


def compute_interplay_layer(interplay: InterplaySubgraph | None,
                           contextual_config: dict[str, Any]) -> float:
    """
    Compute interplay congruence layer (@C)

    Spec compliance: Section 3.7
    Formula: C_play(G | ctx) = c_scale · c_sem · c_fusion

    Args:
        interplay: Interplay subgraph (or None)
        contextual_config: Loaded contextual_parametrization.json

    Returns:
        Score in [0,1]
    """
    if interplay is None:
        # Not in an interplay
        return contextual_config["layer_interplay"]["default_when_not_in_interplay"]

    components = contextual_config["layer_interplay"]["components"]

    # Simplified computation
    c_scale = components["c_scale"]["same_range"]  # Assume same range
    c_sem = 1.0  # Assume full semantic overlap (simplified)
    c_fusion = components["c_fusion"]["declared_and_satisfied"]  # Assume declared

    return c_scale * c_sem * c_fusion


def compute_meta_layer(evidence: dict[str, Any],
                      contextual_config: dict[str, Any]) -> float:
    """
    Compute meta/governance layer (@m)

    Spec compliance: Section 3.8
    Formula: x_@m = 0.5 · m_transp + 0.4 · m_gov + 0.1 · m_cost

    Args:
        evidence: Evidence dictionary with metrics
        contextual_config: Loaded contextual_parametrization.json

    Returns:
        Score in [0,1]
    """
    meta_spec = contextual_config["layer_meta"]

    # Compute m_transp (transparency)
    transp_conditions = [
        evidence.get("formula_export_valid", False),
        evidence.get("trace_complete", False),
        evidence.get("logs_conform_schema", False)
    ]
    transp_count = sum(transp_conditions)

    transp_values = meta_spec["components"]["m_transp"]
    if transp_count == 3:
        m_transp = transp_values["all_three_conditions"]
    elif transp_count == 2:
        m_transp = transp_values["two_of_three"]
    elif transp_count == 1:
        m_transp = transp_values["one_of_three"]
    else:
        m_transp = transp_values["none"]

    # Compute m_gov (governance)
    gov_conditions = [
        evidence.get("version_tagged", False),
        evidence.get("config_hash_matches", False),
        evidence.get("signature_valid", False)
    ]
    gov_count = sum(gov_conditions)

    gov_values = meta_spec["components"]["m_gov"]
    if gov_count == 3:
        m_gov = gov_values["all_three_conditions"]
    elif gov_count == 2:
        m_gov = gov_values["two_of_three"]
    elif gov_count == 1:
        m_gov = gov_values["one_of_three"]
    else:
        m_gov = gov_values["none"]

    # Compute m_cost
    runtime_ms = evidence.get("runtime_ms", 100)
    thresholds = meta_spec["components"]["m_cost"]["thresholds"]

    if runtime_ms < thresholds["fast_runtime_ms"]:
        m_cost = meta_spec["components"]["m_cost"]["fast"]
    elif runtime_ms < thresholds["acceptable_runtime_ms"]:
        m_cost = meta_spec["components"]["m_cost"]["acceptable"]
    else:
        m_cost = meta_spec["components"]["m_cost"]["slow"]

    # Aggregate
    weights = meta_spec["aggregation"]["weights"]
    score = (weights["transparency"] * m_transp +
             weights["governance"] * m_gov +
             weights["cost"] * m_cost)

    return score
