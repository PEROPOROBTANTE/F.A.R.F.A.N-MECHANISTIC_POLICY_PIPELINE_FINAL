"""Prompt Cross analytics utilities.

This module consolidates registry information across micro, meso, and macro
levels and generates cross-cutting diagnostics for coverage, contract health,
and causal path integrity. The calculations use the synthetic dataset stored in
``data/prompt_cross_registry.json`` to demonstrate how the metrics are derived.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

DATA_PATH = Path("data/prompt_cross_registry.json")

def _load_data() -> dict[str, object]:
    """Load the consolidated prompt-cross dataset."""

    with DATA_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)

def _contribution(weight: float, normalized_time: float, depth: int) -> float:
    """Compute contribution score for a single registry entry."""

    safe_depth = max(depth, 1)
    return weight * normalized_time / safe_depth

def consolidate_evidence(records: Iterable[dict[str, object]]) -> dict[str, object]:
    """Deduplicate registry records and compute contribution metrics.

    Args:
        records: Iterable of QMCM registry records.

    Returns:
        Dictionary with consolidated nodes, deduplication ratio, and top
        contributors ranked by contribution score.
    """

    records = list(records)
    canonical: dict[tuple[str, str, str], dict[str, object]] = {}
    record_to_node: dict[str, str] = {}
    parent_links: dict[str, list[str]] = defaultdict(list)
    contributions: dict[str, float] = defaultdict(float)

    for record in records:
        key = (
            record["question_id"],
            record["method_id"],
            record["hash_output"],
        )
        node_id = (
            f"{record['level']}|{record['question_id']}|"
            f"{record['method_id']}|{record['hash_output']}"
        )

        if key not in canonical:
            canonical[key] = {
                "node_id": node_id,
                "level": record["level"],
                "question_id": record["question_id"],
                "method_id": record["method_id"],
                "hash_output": record["hash_output"],
                "dimensions": set(),
                "records": [],
            }

        node_entry = canonical[key]
        node_entry["records"].append(record["record_id"])

        dimension = record.get("dimension")
        if dimension:
            node_entry["dimensions"].add(dimension)

        record_to_node[record["record_id"]] = node_id
        contributions[node_id] += _contribution(
            record["weight"], record["normalized_time"], int(record["depth"])
        )

        parent_record = record.get("parent_record")
        if parent_record:
            parent_links[node_id].append(parent_record)

    # Resolve parent pointers to canonical node identifiers
    resolved_parents: dict[str, list[str]] = {}
    for node_id, parents in parent_links.items():
        resolved = {
            record_to_node[parent]
            for parent in parents
            if parent in record_to_node
        }
        resolved_parents[node_id] = sorted(resolved)

    # Build global node list
    level_order = {"micro": 0, "meso": 1, "macro": 2}
    global_nodes: list[dict[str, object]] = []
    for entry in canonical.values():
        node_id = entry["node_id"]
        global_nodes.append(
            {
                "node_id": node_id,
                "level": entry["level"],
                "question_id": entry["question_id"],
                "method_id": entry["method_id"],
                "hash_output": entry["hash_output"],
                "parent_nodes": resolved_parents.get(node_id, []),
                "record_count": len(entry["records"]),
                "dimensions": sorted(entry["dimensions"]),
                "contribution_score": round(contributions[node_id], 6),
            }
        )

    global_nodes.sort(
        key=lambda node: (
            level_order.get(str(node["level"]), 99),
            str(node["question_id"]),
            str(node["method_id"]),
        )
    )

    total_records = len(records)

    unique_nodes = len(global_nodes)
    dedup_ratio = unique_nodes / total_records if total_records else 0.0

    top_contributors = sorted(
        (
            {
                "node_id": node["node_id"],
                "question_id": node["question_id"],
                "method_id": node["method_id"],
                "contribution_score": node["contribution_score"],
            }
            for node in global_nodes
        ),
        key=lambda item: item["contribution_score"],
        reverse=True,
    )[:5]

    return {
        "global_nodes": global_nodes,
        "dedup_ratio": round(dedup_ratio, 4),
        "top_contributors": top_contributors,
    }

def build_method_coverage(entries: Iterable[dict[str, object]]) -> tuple[dict[str, object], str]:
    """Generate method coverage matrix and heatmap recommendations."""

    dimensions = sorted({entry["dimension"] for entry in entries})
    matrix: dict[str, dict[str, dict[str, float]]] = defaultdict(
        lambda: {dim: {"invocations": 0, "tests": 0} for dim in dimensions}
    )

    for entry in entries:
        method = entry["method_id"]
        dim = entry["dimension"]
        matrix[method][dim]["invocations"] += entry["invocations"]
        matrix[method][dim]["tests"] += entry["tests_executed"]

    recommendations: list[dict[str, object]] = []
    for method, dim_data in matrix.items():
        cold_dims: list[str] = []
        for dim, stats in dim_data.items():
            inv = stats["invocations"]
            tests = stats["tests"]
            coverage_ratio = tests / inv if inv else 0.0
            stats["coverage_ratio"] = round(coverage_ratio, 3)
            if inv and coverage_ratio < 0.25 or not inv:
                cold_dims.append(dim)

        if cold_dims:
            recommendations.append(
                {
                    "method_id": method,
                    "cold_dimensions": cold_dims,
                    "action": "Design targeted regression tests for under-covered dimensions",
                }
            )

    # Build ASCII table
    header = ["Method"] + dimensions
    rows: list[list[str]] = []
    for method in sorted(matrix):
        row = [method]
        for dim in dimensions:
            stats = matrix[method][dim]
            if stats["invocations"]:
                cell = f"{int(stats['invocations'])}/{int(stats['tests'])}"
            else:
                cell = "0/0"
            row.append(cell)
        rows.append(row)

    col_widths = [max(len(row[i]) for row in [header] + rows) for i in range(len(header))]

    def _format_row(row: list[str]) -> str:
        return " | ".join(val.ljust(col_widths[idx]) for idx, val in enumerate(row))

    separator = "-+-".join("-" * width for width in col_widths)
    table_lines = [_format_row(header), separator]
    table_lines.extend(_format_row(row) for row in rows)
    ascii_table = "\n".join(table_lines)

    matrix_serializable = {
        method: {
            dim: {
                "invocations": stats["invocations"],
                "tests": stats["tests"],
                "coverage_ratio": stats.get("coverage_ratio", 0.0),
            }
            for dim, stats in dim_data.items()
        }
        for method, dim_data in matrix.items()
    }

    return (
        {
            "matrix": matrix_serializable,
            "dimensions": dimensions,
            "recommendations": recommendations,
        },
        ascii_table,
    )

SEVERITY_WEIGHTS = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
}

def analyze_contract_failures(
    entries: Iterable[dict[str, object]], inputs: dict[str, int]
) -> tuple[dict[str, object], list[str]]:
    """Aggregate contract failures into a funnel and narrative."""

    level_stats: dict[str, dict[str, object]] = {}
    method_scores: dict[str, dict[str, object]] = defaultdict(
        lambda: {"severity_score": 0, "total_failures": 0}
    )

    for entry in entries:
        level = entry["level"]
        severity = entry["severity"].lower()
        count = entry["count"]

        stats = level_stats.setdefault(
            level,
            {"by_severity": defaultdict(int), "total_failures": 0},
        )
        stats["by_severity"][severity] += count
        stats["total_failures"] += count

        method_key = f"{entry['method_id']}::{entry['question_id']}"
        method_scores[method_key]["severity_score"] += SEVERITY_WEIGHTS.get(severity, 0) * count
        method_scores[method_key]["total_failures"] += count

    for level, stats in level_stats.items():
        entries_prev = inputs.get(level, 0)
        drop_pct = stats["total_failures"] / entries_prev if entries_prev else 0.0
        stats["funnel_drop_pct"] = round(drop_pct * 100, 2)
        stats["by_severity"] = dict(stats["by_severity"])

    top_methods = sorted(
        (
            {
                "method_id": key.split("::")[0],
                "context": key.split("::")[1],
                "severity_score": value["severity_score"],
                "total_failures": value["total_failures"],
            }
            for key, value in method_scores.items()
        ),
        key=lambda item: (item["severity_score"], item["total_failures"]),
        reverse=True,
    )[:5]

    narrative = [
        "Micro layer accumulates the largest absolute failures, primarily from the assembler and processor modules.",
        "Meso layer exhibits a sharper proportional drop, signalling propagation of unresolved micro issues into cluster synthesis.",
        "Macro convergence remains fragile with critical severities persisting despite lower volume.",
        "TeoriaCambio validation spikes as a critical blocker along the causal verification chain.",
        "Prioritize regression tests around ReportAssembler.generate_meso_cluster to contain meso escalations.",
    ]

    return {"funnel": level_stats, "top_methods": top_methods}, narrative

@dataclass
class PathStatus:
    path_id: str
    complete: bool
    missing_dimensions: list[str]
    issues: list[str]

def evaluate_causal_paths(data: dict[str, object]) -> dict[str, object]:
    """Verify causal path continuity across dimensions."""

    expected_sequence: list[str] = data["dimension_sequence"]
    complete_paths: list[dict[str, object]] = []
    broken_paths: list[dict[str, object]] = []
    repair_actions: list[str] = []

    for path in data["causal_paths"]:
        dims: list[str] = path["dimensions"]
        missing = [dim for dim in expected_sequence if dim not in dims]
        unexpected = [dim for dim in dims if dim not in expected_sequence]
        issues: list[str] = []

        if dims != expected_sequence:
            # Check for unexpected dimensions (not in expected sequence)
            if unexpected:
                issues.append(
                    "Unexpected dimensions: " + ", ".join(unexpected)
                )

            # Check for length mismatch
            if len(dims) != len(expected_sequence):
                issues.append(
                    f"Length mismatch: expected {len(expected_sequence)} dimensions but found {len(dims)}"
                )

            # Check for adjacency breaks
            for idx, expected_dim in enumerate(expected_sequence):
                if idx >= len(dims):
                    break
                if dims[idx] != expected_dim:
                    issues.append(
                        f"Expected {expected_dim} at position {idx + 1} but found {dims[idx]}"
                    )

            if missing:
                issues.append(
                    "Missing dimensions: " + ", ".join(sorted(missing))
                )

        status = PathStatus(
            path_id=path["path_id"],
            complete=not issues and not missing,
            missing_dimensions=missing,
            issues=issues,
        )

        if status.complete:
            complete_paths.append(
                {
                    "path_id": status.path_id,
                    "sequence": path["sequence"],
                }
            )
        else:
            broken_paths.append(
                {
                    "path_id": status.path_id,
                    "missing_dimensions": status.missing_dimensions,
                    "issues": status.issues,
                }
            )
            for dim in status.missing_dimensions:
                repair_actions.append(
                    f"Re-evaluate {dim} in {status.path_id} to restore sequential continuity"
                )
            for dim in unexpected:
                repair_actions.append(
                    f"Remove unexpected dimension {dim} from {status.path_id}"
                )

    return {
        "complete_paths": complete_paths,
        "broken_paths": broken_paths,
        "repair_actions": sorted(set(repair_actions)),
    }

def run() -> None:
    """Execute all Prompt Cross analyses and print results."""

    data = _load_data()

    evidence = consolidate_evidence(data["qmcm_records"])
    print("=== Prompt Cross – Evidence Registry Consolidation ===")
    print(json.dumps(evidence, indent=2))

    heatmap_json, ascii_table = build_method_coverage(data["method_coverage"])
    print("\n=== Prompt Cross – Method Coverage Heatmap ===")
    print(json.dumps(heatmap_json, indent=2))
    print("\n" + ascii_table)

    funnel_json, narrative = analyze_contract_failures(
        data["contract_failures"], data["funnel_inputs"]
    )
    print("\n=== Prompt Cross – Contract Failure Funnel ===")
    print(json.dumps(funnel_json, indent=2))
    print("\nNarrativa:")
    for line in narrative:
        print(f"- {line}")

    causal = evaluate_causal_paths(data)
    print("\n=== Prompt Cross – Causal Path Integrity ===")
    print(json.dumps(causal, indent=2))

if __name__ == "__main__":
    run()
