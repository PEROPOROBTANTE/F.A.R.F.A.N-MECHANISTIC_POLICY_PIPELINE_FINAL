#!/usr/bin/env python3
"""
Advanced orchestration readiness evaluator.

This script performs SOTA-style detection of objective, necessary, and sufficient
conditions required for orchestrator implementation. It validates runtime
constraints, critical file presence, phase wiring, router guarantees, registry
integrity, and questionnaire resource extraction guarantees, and produces a JSON
report consumable by runbooks or CI instrumentation.
"""

from __future__ import annotations

import inspect
import json
import sys
import threading
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


def _record(name: str, passed: bool, severity: str, details: dict[str, Any]) -> dict[str, Any]:
    return {
        "check": name,
        "passed": passed,
        "severity": severity,
        "details": details,
    }


def check_python_version() -> dict[str, Any]:
    required_min = (3, 12)
    required_max = (3, 13)
    actual = sys.version_info[:2]
    passed = required_min <= actual < required_max
    return _record(
        "python_version_window",
        passed,
        "critical",
        {
            "required_range": f"{required_min[0]}.{required_min[1]} <= version < {required_max[0]}.{required_max[1]}",
            "detected": f"{actual[0]}.{actual[1]}",
        },
    )


def check_critical_files() -> dict[str, Any]:
    critical_paths = [
        "src/saaaaaa/core/orchestrator/core.py",
        "src/saaaaaa/core/orchestrator/arg_router.py",
        "src/saaaaaa/core/orchestrator/class_registry.py",
        "src/saaaaaa/core/orchestrator/executors.py",
        "src/saaaaaa/core/orchestrator/factory.py",
        "src/saaaaaa/core/orchestrator/questionnaire_resource_provider.py",
        "src/saaaaaa/core/orchestrator/questionnaire.py",
        "src/saaaaaa/processing/cpp_ingestion/__init__.py",
        "src/saaaaaa/processing/cpp_ingestion/models.py",
    ]
    missing = [p for p in critical_paths if not (REPO_ROOT / p).exists()]
    return _record(
        "critical_orchestration_files_present",
        not missing,
        "critical",
        {"missing": missing, "checked": len(critical_paths)},
    )


def check_phase_definitions() -> dict[str, Any]:
    try:
        from saaaaaa.core.orchestrator.core import Orchestrator
    except Exception as exc:  # pragma: no cover - defensive
        return _record(
            "orchestrator_phase_integrity",
            False,
            "critical",
            {"error": f"Unable to import Orchestrator: {exc!r}"},
        )

    phases = getattr(Orchestrator, "FASES", [])
    ids = [phase[0] for phase in phases]
    handlers_missing: list[str] = []
    mode_mismatches: list[tuple[str, str]] = []

    for _, mode, handler_name, _ in phases:
        handler = getattr(Orchestrator, handler_name, None)
        if handler is None:
            handlers_missing.append(handler_name)
            continue
        is_async = inspect.iscoroutinefunction(handler)
        if mode == "async" and not is_async:
            mode_mismatches.append((handler_name, "expected async"))
        if mode == "sync" and is_async:
            mode_mismatches.append((handler_name, "expected sync"))

    duplicate_ids = len(ids) != len(set(ids))
    monotonic = ids == sorted(ids)

    passed = bool(phases) and not handlers_missing and not mode_mismatches and not duplicate_ids and monotonic
    return _record(
        "phase_definition_consistency",
        passed,
        "critical",
        {
            "phase_count": len(phases),
            "missing_handlers": handlers_missing,
            "mode_mismatches": mode_mismatches,
            "duplicate_ids": duplicate_ids,
            "monotonic_ids": monotonic,
        },
    )


def check_class_registry() -> dict[str, Any]:
    try:
        from saaaaaa.core.orchestrator.class_registry import build_class_registry
    except Exception as exc:  # pragma: no cover - defensive
        return _record(
            "class_registry_build",
            False,
            "critical",
            {"error": f"Unable to import class registry: {exc!r}"},
        )

    try:
        registry = build_class_registry()
        registry_count = len(registry)
        sample = sorted(registry.keys())[:5]
        passed = registry_count >= 20
        return _record(
            "class_registry_build",
            passed,
            "high",
            {"count": registry_count, "sample": sample},
        )
    except Exception as exc:  # pragma: no cover - defensive
        return _record(
            "class_registry_build",
            False,
            "critical",
            {"error": f"build_class_registry failed: {exc!r}"},
        )


def check_extended_router() -> dict[str, Any]:
    try:
        from saaaaaa.core.orchestrator.arg_router import ExtendedArgRouter
        from saaaaaa.core.orchestrator.class_registry import build_class_registry
    except Exception as exc:  # pragma: no cover - defensive
        return _record(
            "extended_router_integrity",
            False,
            "high",
            {"error": f"Unable to import router dependencies: {exc!r}"},
        )

    try:
        router = ExtendedArgRouter(build_class_registry())
    except Exception as exc:
        return _record(
            "extended_router_integrity",
            False,
            "high",
            {"error": f"ExtendedArgRouter initialization failed: {exc!r}"},
        )

    lock_ok = isinstance(getattr(router, "_lock", None), threading.RLock)
    special_routes = getattr(router, "_special_routes", {})
    route_count = len(special_routes)
    passed = lock_ok and route_count >= 25
    return _record(
        "extended_router_integrity",
        passed,
        "medium",
        {
            "lock_is_rlock": lock_ok,
            "special_route_count": route_count,
        },
    )


def check_questionnaire_provider() -> dict[str, Any]:
    try:
        from saaaaaa.core.orchestrator.questionnaire_resource_provider import QuestionnaireResourceProvider
    except Exception as exc:  # pragma: no cover - defensive
        return _record(
            "questionnaire_provider_extracts",
            False,
            "medium",
            {"error": f"Unable to import QuestionnaireResourceProvider: {exc!r}"},
        )

    sample_questionnaire = {
        "version": "diagnostic",
        "schema_version": "diagnostic",
        "blocks": {
            "micro_questions": [],
            "meso_questions": [],
            "macro_question": {},
        },
        "validations": [],
    }

    provider = QuestionnaireResourceProvider(sample_questionnaire)
    patterns = provider.extract_all_patterns()
    validations = provider.extract_all_validations()
    passed = isinstance(patterns, list) and isinstance(validations, list)
    return _record(
        "questionnaire_provider_extracts",
        passed,
        "medium",
        {
            "pattern_count": len(patterns),
            "validation_count": len(validations),
        },
    )


def check_executor_registry() -> dict[str, Any]:
    try:
        from saaaaaa.core.orchestrator.core import Orchestrator
    except Exception as exc:  # pragma: no cover - defensive
        return _record(
            "executor_registry_coverage",
            False,
            "high",
            {"error": f"Unable to import Orchestrator: {exc!r}"},
        )

    executors = getattr(Orchestrator, "executors", {})
    passed = isinstance(executors, dict) and len(executors) >= 25
    return _record(
        "executor_registry_coverage",
        passed,
        "medium",
        {"executor_count": len(executors)},
    )


def run_checks() -> dict[str, Any]:
    checks = [
        check_python_version(),
        check_critical_files(),
        check_phase_definitions(),
        check_class_registry(),
        check_extended_router(),
        check_executor_registry(),
        check_questionnaire_provider(),
    ]
    passed = sum(1 for c in checks if c["passed"])
    failed = len(checks) - passed
    return {
        "total_checks": len(checks),
        "passed": passed,
        "failed": failed,
        "results": checks,
    }


def main() -> None:
    report = run_checks()
    print(json.dumps(report, indent=2))
    if report["failed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
