#!/usr/bin/env python3
"""Cross-file integrity checks for policy analysis data contracts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping

REPO_ROOT = Path(__file__).parent.parent.parent
QUESTIONNAIRE_PATH = REPO_ROOT / "questionnaire.json"
RUBRIC_PATH = REPO_ROOT / "rubric_scoring.json"

FLOAT_TOLERANCE = 1e-6

def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)

def weights_sum_to_one(weights: Mapping[str, float]) -> bool:
    return abs(sum(weights.values()) - 1.0) <= FLOAT_TOLERANCE

def ensure(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)

def main() -> int:
    errors: list[str] = []

    try:
        questionnaire = load_json(QUESTIONNAIRE_PATH)
    except Exception as exc:  # pragma: no cover - CLI guard
        print(f"❌ Unable to load questionnaire.json: {exc}")
        return 1

    try:
        rubric = load_json(RUBRIC_PATH)
    except Exception as exc:  # pragma: no cover - CLI guard
        print(f"❌ Unable to load rubric_scoring.json: {exc}")
        return 1

    ensure(
        questionnaire.get("version") == rubric.get("requires_questionnaire_version"),
        "Rubric version requirement does not match questionnaire version",
        errors,
    )

    metadata = questionnaire.get("metadata", {})
    policy_areas = metadata.get("policy_areas", [])
    dimensions = metadata.get("dimensions", [])
    clusters = metadata.get("clusters", [])

    pa_lookup = {pa["policy_area_id"]: pa for pa in policy_areas}
    dim_ids = {dim["dimension_id"] for dim in dimensions}

    cluster_for_pa: dict[str, str] = {}
    for cluster in clusters:
        cluster_id = cluster.get("cluster_id")
        for pa in cluster.get("policy_area_ids", []):
            cluster_for_pa[pa] = cluster_id
            if pa not in pa_lookup:
                errors.append(f"Cluster {cluster_id} references unknown policy area {pa}")

    for pa in policy_areas:
        expected_cluster = cluster_for_pa.get(pa["policy_area_id"])
        if expected_cluster and pa.get("cluster_id") != expected_cluster:
            errors.append(
                f"Policy area {pa['policy_area_id']} mismatch: metadata cluster {pa.get('cluster_id')} vs {expected_cluster}"
            )

    rubric_matrix = rubric.get("rubric_matrix", {})
    aggregation = rubric.get("aggregation", {})

    for cluster_id, weights in aggregation.get("cluster_policy_area_weights", {}).items():
        if not weights_sum_to_one(weights):
            errors.append(f"Cluster weights for {cluster_id} must sum to 1.0")
        for pa in weights:
            if pa not in cluster_for_pa:
                errors.append(f"Cluster {cluster_id} has weight for unknown policy area {pa}")
            elif cluster_for_pa[pa] != cluster_id:
                errors.append(f"Cluster {cluster_id} weight references policy area {pa} assigned to {cluster_for_pa[pa]}")

    macro_weights = aggregation.get("macro_cluster_weights", {})
    if not weights_sum_to_one(macro_weights):
        errors.append("Macro cluster weights must sum to 1.0")

    pa_dim_weights = aggregation.get("policy_area_dimension_weights", {})
    for pa_id, weights in pa_dim_weights.items():
        if not weights_sum_to_one(weights):
            errors.append(f"Dimension weights for {pa_id} must sum to 1.0")
        missing_dims = dim_ids - set(weights.keys())
        if missing_dims:
            errors.append(f"Policy area {pa_id} missing weights for dimensions {sorted(missing_dims)}")

    dimension_question_weights = aggregation.get("dimension_question_weights", {})
    for dim_id, weights in dimension_question_weights.items():
        if not weights_sum_to_one(weights):
            errors.append(f"Question weights for {dim_id} must sum to 1.0")

    questions = questionnaire.get("questions", [])
    dimension_questions = {dim: set(weights.keys()) for dim, weights in dimension_question_weights.items()}

    for question in questions:
        qid = question.get("question_id")
        pa_id = question.get("policy_area_id")
        dim_id = question.get("dimension_id")
        modality = question.get("scoring_modality")

        matrix_entry = rubric_matrix.get(pa_id, {}).get(dim_id)
        if not matrix_entry:
            errors.append(f"Rubric matrix missing entry for {pa_id}/{dim_id}")
        else:
            allowed = matrix_entry.get("allowed_modalities", [])
            if modality not in allowed:
                errors.append(f"Question {qid} modality {modality} not allowed for {pa_id}/{dim_id}")

        if dim_id in dimension_questions and qid not in dimension_questions[dim_id]:
            errors.append(f"Question {qid} missing weight in dimension_question_weights for {dim_id}")

        expected_cluster = cluster_for_pa.get(pa_id)
        if expected_cluster and question.get("cluster_id") != expected_cluster:
            errors.append(f"Question {qid} cluster mismatch: expected {expected_cluster}")

    for pa_id, dims in rubric_matrix.items():
        for dim_id, entry in dims.items():
            allowed = entry.get("allowed_modalities", [])
            default_modality = entry.get("default_modality")
            if default_modality not in allowed:
                errors.append(f"Rubric matrix default modality for {pa_id}/{dim_id} not in allowed list")

    if errors:
        print("❌ Cross-reference validation failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("✅ Cross-reference validation passed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
