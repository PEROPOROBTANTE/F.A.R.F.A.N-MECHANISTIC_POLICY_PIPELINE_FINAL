#!/usr/bin/env python3
"""
Validate a questionnaire monolith against the JSON Schema and basic semantic rules.

Exit code:
- 0 if schema validation and semantic checks pass.
- 1 otherwise.

Outputs validation_report.json with:
{
  "validation_passed": bool,
  "errors": [...],
  "warnings": [...],
  "schema_hash": "sha256:<hash>"
}
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MONOLITH = ROOT / "system" / "config" / "questionnaire" / "questionnaire_monolith.json"
DEFAULT_SCHEMA = ROOT / "system" / "config" / "questionnaire" / "questionnaire_schema.json"
DEFAULT_REGISTRY = ROOT / "config" / "json_files_ no_schemas" / "pattern_registry.json"
DEFAULT_REPORT = ROOT / "validation_report.json"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def compute_sha256(path: Path) -> str:
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    return f"sha256:{digest}"


def semantic_checks(monolith: dict[str, Any]) -> list[dict[str, Any]]:
    """Lightweight semantic checks beyond JSON Schema."""
    errors: list[dict[str, Any]] = []

    required_keys = ["canonical_notation", "blocks", "schema_version", "integrity"]
    missing = [k for k in required_keys if k not in monolith]
    if missing:
        errors.append({"type": "semantic", "message": f"Missing required keys: {missing}"})
        return errors

    blocks = monolith.get("blocks", {})
    required_blocks = [
        "macro_question",
        "meso_questions",
        "micro_questions",
        "niveles_abstraccion",
        "scoring",
        "semantic_layers",
    ]
    missing_blocks = [b for b in required_blocks if b not in blocks]
    if missing_blocks:
        errors.append({"type": "semantic", "message": f"Missing required blocks: {missing_blocks}"})

    micro_questions = blocks.get("micro_questions", [])
    if not isinstance(micro_questions, list) or not micro_questions:
        errors.append({"type": "semantic", "message": "micro_questions must be a non-empty list"})
        return errors

    first_q = micro_questions[0]
    required_q_fields = ["question_id", "text", "cluster_id", "dimension_id"]
    missing_q = [f for f in required_q_fields if f not in first_q]
    if missing_q:
        errors.append(
            {"type": "semantic", "message": f"Micro questions missing required fields: {missing_q}"}
        )

    return errors


def validate_pattern_refs(monolith: dict[str, Any], registry_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Validate that all pattern_ref entries resolve to the registry and find unused patterns."""
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    if not registry_path.exists():
        warnings.append(
            {
                "type": "registry",
                "message": f"Registry file not found at {registry_path}",
            }
        )
        return errors, warnings

    registry = load_json(registry_path)
    registry_index = {entry.get("pattern_id"): entry for entry in registry}
    used: set[str] = set()

    for mq in monolith.get("blocks", {}).get("micro_questions", []):
        for pattern in mq.get("patterns", []) or []:
            ref = pattern.get("pattern_ref")
            if ref:
                if ref not in registry_index:
                    errors.append(
                        {
                            "type": "registry",
                            "message": f"pattern_ref '{ref}' not found in registry",
                            "instance_path": ["blocks", "micro_questions", mq.get("question_id"), "patterns"],
                        }
                    )
                else:
                    used.add(ref)

    unused = sorted(set(registry_index) - used)
    if unused:
        warnings.append(
            {
                "type": "registry",
                "message": f"Unused registry patterns: {len(unused)}",
                "details": unused,
            }
        )

    return errors, warnings


def validate(monolith_path: Path, schema_path: Path, registry_path: Path) -> dict[str, Any]:
    monolith = load_json(monolith_path)
    schema = load_json(schema_path)

    validator = Draft7Validator(schema)
    schema_errors = sorted(validator.iter_errors(monolith), key=lambda e: e.path)

    errors: list[dict[str, Any]] = []
    for err in schema_errors:
        errors.append(
            {
                "type": "schema",
                "message": err.message,
                "instance_path": list(err.path),
                "schema_path": list(err.schema_path),
            }
        )

    errors.extend(semantic_checks(monolith))
    registry_errors, registry_warnings = validate_pattern_refs(monolith, registry_path)
    errors.extend(registry_errors)

    validation_passed = len(errors) == 0
    report = {
        "validation_passed": validation_passed,
        "errors": errors,
        "warnings": registry_warnings,
        "schema_hash": compute_sha256(schema_path),
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate questionnaire monolith.")
    parser.add_argument(
        "--monolith",
        type=Path,
        default=DEFAULT_MONOLITH,
        help=f"Path to questionnaire monolith (default: {DEFAULT_MONOLITH})",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=DEFAULT_SCHEMA,
        help=f"Path to JSON Schema (default: {DEFAULT_SCHEMA})",
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=DEFAULT_REGISTRY,
        help=f"Path to pattern registry (default: {DEFAULT_REGISTRY})",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=DEFAULT_REPORT,
        help=f"Path to write validation report (default: {DEFAULT_REPORT})",
    )
    args = parser.parse_args()

    report = validate(args.monolith, args.schema, args.registry)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if report["validation_passed"]:
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
