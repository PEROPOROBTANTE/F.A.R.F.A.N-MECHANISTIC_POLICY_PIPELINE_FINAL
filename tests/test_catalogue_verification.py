"""Verification suite for canonical_method_catalogue_v2.json."""

from __future__ import annotations

import ast
import json
import math
import random
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = REPO_ROOT / "canonical_method_catalogue_v2.json"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_internal_consistency() -> None:
    catalogue = load_json(CATALOG_PATH)
    errors: list[str] = []

    for method_id, method_data in catalogue.items():
        if method_id.startswith("_"):
            continue

        for param in method_data["input_parameters"]:
            required = param["required"]
            has_default = param["has_default"]
            default_value = param["default_value"]

            if required and has_default:
                errors.append(f"{method_id}.{param['name']}: required=True but has_default=True")

            if not required and not has_default:
                errors.append(f"{method_id}.{param['name']}: required=False but has_default=False")

            if has_default and default_value is None:
                errors.append(f"{method_id}.{param['name']}: has_default=True but default_value is None")

            if not has_default and default_value is not None:
                errors.append(
                    f"{method_id}.{param['name']}: has_default=False but default_value is {default_value}"
                )

    assert not errors, "CONSISTENCY ERRORS:\n" + "\n".join(errors)


def test_catalogue_matches_source() -> None:
    catalogue = load_json(CATALOG_PATH)
    method_ids = [
        name
        for name, data in catalogue.items()
        if not name.startswith("_") and not data.get("auto_generated")
    ]
    rng = random.Random(1337)
    sample_size = min(50, len(method_ids))
    sample = rng.sample(method_ids, sample_size)

    mismatches: list[str] = []
    for method_id in sample:
        method_data = catalogue[method_id]
        actual_params = parse_params_from_source(
            method_data["file_path"],
            method_data["line_number"],
        )
        catalogue_params = method_data["input_parameters"]

        if len(actual_params) != len(catalogue_params):
            mismatches.append(
                f"{method_id}: parameter count mismatch "
                f"(source={len(actual_params)}, catalog={len(catalogue_params)})"
            )
            continue

        for actual, catalogued in zip(actual_params, catalogue_params, strict=False):
            if actual["has_default"] != catalogued["has_default"]:
                mismatches.append(
                    f"{method_id}.{actual['name']}: "
                    f"Source has_default={actual['has_default']}, "
                    f"Catalogue has_default={catalogued['has_default']}"
                )
            if actual["has_default"] and actual["default_value"] != catalogued["default_value"]:
                mismatches.append(
                    f"{method_id}.{actual['name']}: "
                    f"Source default={actual['default_value']}, "
                    f"Catalogue default={catalogued['default_value']}"
                )

    assert not mismatches, "MISMATCH ERRORS:\n" + "\n".join(mismatches)


def test_minimum_coverage() -> None:
    catalogue = load_json(CATALOG_PATH)
    total_methods = 0
    methods_with_defaults = 0
    total_params = 0
    params_with_defaults = 0

    for method_id, method_data in catalogue.items():
        if method_id.startswith("_"):
            continue

        total_methods += 1
        params = method_data["input_parameters"]
        has_any_default = False

        for param in params:
            if param["name"] == "self":
                continue

            total_params += 1
            if param["has_default"]:
                params_with_defaults += 1
                has_any_default = True

        if has_any_default:
            methods_with_defaults += 1

    method_coverage = methods_with_defaults / total_methods if total_methods else 0
    param_coverage = params_with_defaults / total_params if total_params else 0

    assert method_coverage >= 0.25, (
        f"FAIL: Only {method_coverage:.1%} methods have defaults (required: >=25%)"
    )
    assert param_coverage >= 0.15, (
        f"FAIL: Only {param_coverage:.1%} params have defaults (required: >=15%)"
    )
    assert methods_with_defaults >= 100, (
        f"FAIL: Only {methods_with_defaults} methods with defaults (required: >=100)"
    )


def test_known_methods() -> None:
    catalogue = load_json(CATALOG_PATH)

    known_methods = {
        "src.saaaaaa.analysis.Analyzer_one.BatchProcessor.process_directory": {
            "pattern": "*.txt",
        },
        "src.saaaaaa.analysis.Analyzer_one.CanonicalQuestionSegmenter.__init__": {
            "questionnaire_path": "questionnaire.json",
            "rubric_path": "rubric_scoring_FIXED.json",
            "segmentation_method": "paragraph",
        },
        "src.saaaaaa.analysis.Analyzer_one.DocumentProcessor.segment_text": {
            "method": "sentence",
        },
        "src.saaaaaa.analysis.bayesian_multilevel_system.BayesianRollUp.aggregate_micro_to_meso": {
            "dispersion_penalty": 0.0,
            "peer_penalty": 0.0,
            "additional_penalties": "None",
        },
        "src.saaaaaa.analysis.bayesian_multilevel_system.MultiLevelBayesianOrchestrator.run_complete_analysis": {
            "peer_contexts": "None",
            "total_questions": 300,
        },
        "src.saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector.detect": {
            "plan_name": "PDM",
            "dimension": "PolicyDimension.ESTRATEGICO",
        },
        "src.saaaaaa.processing.semantic_chunking_policy.SemanticProcessor.chunk_text": {
            "preserve_structure": True,
        },
        "src.saaaaaa.analysis.derek_beach.AdaptivePriorCalculator.generate_traceability_record": {
            "seed": 42,
        },
        "src.saaaaaa.analysis.bayesian_multilevel_system.ContradictionScanner.__init__": {
            "discrepancy_threshold": 0.3,
        },
        "src.saaaaaa.analysis.bayesian_multilevel_system.DispersionEngine.__init__": {
            "dispersion_threshold": 0.3,
        },
        "src.saaaaaa.analysis.Analyzer_one.ConfigurationManager.__init__": {
            "config_path": "None",
        },
        "src.saaaaaa.analysis.contradiction_deteccion.BayesianConfidenceCalculator.calculate_posterior": {
            "domain_weight": 1.0,
        },
    }

    for method_id, expected_defaults in known_methods.items():
        assert method_id in catalogue, f"Known method {method_id} not in catalogue"
        method_params = catalogue[method_id]["input_parameters"]

        for param_name, expected_value in expected_defaults.items():
            param = next((p for p in method_params if p["name"] == param_name), None)
            assert param is not None, f"{method_id}: Parameter {param_name} not found"
            assert param["has_default"] is True, f"{method_id}.{param_name}: has_default should be True"
            assert param["required"] is False, f"{method_id}.{param_name}: required should be False"
            assert param["default_value"] == expected_value, (
                f"{method_id}.{param_name}: default_value is {param['default_value']}, "
                f"expected {expected_value}"
            )


# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #
def parse_params_from_source(relative_path: str, target_line: int) -> list[dict[str, Any]]:
    file_path = REPO_ROOT / relative_path
    source = file_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(file_path))

    target_node = _locate_function_node(tree, target_line)
    if target_node is None:
        raise AssertionError(f"Unable to locate function at line {target_line} in {relative_path}")

    return _extract_parameters(target_node)


def _locate_function_node(tree: ast.AST, target_line: int) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.lineno == target_line:
            return node
    return None


def _extract_parameters(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[dict[str, Any]]:
    args = node.args
    params: list[dict[str, Any]] = []

    positional = list(args.posonlyargs) + list(args.args)
    defaults = list(args.defaults)
    total_defaults = len(defaults)
    num_without_default = len(positional) - total_defaults

    for index, arg in enumerate(positional):
        has_default = index >= num_without_default
        default_node = defaults[index - num_without_default] if has_default else None
        params.append(
            _build_param_record(arg.arg, has_default, default_node)
        )

    if args.vararg:
        params.append(_build_param_record(f"*{args.vararg.arg}", False, None))

    for kw_arg, kw_default in zip(args.kwonlyargs, args.kw_defaults, strict=False):
        has_default = kw_default is not None
        params.append(_build_param_record(kw_arg.arg, has_default, kw_default))

    if args.kwarg:
        params.append(_build_param_record(f"**{args.kwarg.arg}", False, None))

    return params


def _build_param_record(name: str, has_default: bool, default_node: ast.expr | None) -> dict[str, Any]:
    record = {
        "name": name,
        "has_default": has_default,
        "default_value": None,
    }

    if name.startswith("**"):
        record["has_default"] = True
        record["default_value"] = "dict()"
        return record
    if name.startswith("*"):
        record["has_default"] = True
        record["default_value"] = "tuple()"
        return record

    if has_default and default_node is not None:
        record["default_value"] = _resolve_default_value(default_node)

    return record


def _resolve_default_value(default_node: ast.expr) -> Any:
    try:
        literal_value = ast.literal_eval(default_node)
        return _make_json_safe(literal_value)
    except Exception:
        pass

    try:
        compiled = compile(ast.Expression(default_node), filename="<ast>", mode="eval")
        evaluated = eval(compiled, {}, {})  # noqa: S307 - controlled input
        return _make_json_safe(evaluated)
    except Exception:
        return ast.unparse(default_node)


def _make_json_safe(value: Any) -> Any:
    if value is None:
        return "None"
    if isinstance(value, (bool, int)):
        return value
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return repr(value)
        return value
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="backslashreplace")
    if isinstance(value, (list, tuple, set)):
        return [_make_json_safe(item) for item in list(value)]
    if isinstance(value, dict):
        return {str(key): _make_json_safe(val) for key, val in value.items()}
    return repr(value)
