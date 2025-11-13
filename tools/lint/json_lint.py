#!/usr/bin/env python3
"""Basic JSON linter enforcing deterministic data contract hygiene."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterable

try:
    import jsonschema
except ImportError:  # pragma: no cover - optional dependency
    jsonschema = None

class DuplicateKeyError(ValueError):
    """Raised when duplicate keys are encountered."""

def _no_duplicate_object_pairs(pairs: Iterable[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise DuplicateKeyError(f"Duplicate key detected: {key}")
        obj[key] = value
    return obj

def load_json_strict(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle, object_pairs_hook=_no_duplicate_object_pairs)

def find_empty_strings(payload: object, path: str = "") -> Iterable[str]:
    if isinstance(payload, str):
        if not payload.strip():
            yield path
    elif isinstance(payload, dict):
        for key, value in payload.items():
            next_path = f"{path}.{key}" if path else key
            yield from find_empty_strings(value, next_path)
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            next_path = f"{path}[{index}]"
            yield from find_empty_strings(value, next_path)

def find_out_of_range_numbers(payload: object, path: str = "") -> Iterable[str]:
    if isinstance(payload, (int, float)):
        key_lower = path.lower()
        if any(token in key_lower for token in ("weight", "min_score")) and (payload < 0 or payload > 1):
            yield path
    elif isinstance(payload, dict):
        for key, value in payload.items():
            next_path = f"{path}.{key}" if path else key
            yield from find_out_of_range_numbers(value, next_path)
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            next_path = f"{path}[{index}]"
            yield from find_out_of_range_numbers(value, next_path)

def lint_file(path: Path, schema: Path | None) -> int:
    try:
        payload = load_json_strict(path)
    except DuplicateKeyError as exc:
        print(f"❌ {path.name}: {exc}")
        return 1
    except Exception as exc:  # pragma: no cover - CLI guard
        print(f"❌ {path.name}: unable to parse JSON ({exc})")
        return 1

    issues = False

    empty_paths = list(find_empty_strings(payload))
    if empty_paths:
        issues = True
        print(f"❌ {path.name}: empty string values detected at {empty_paths[:5]}")

    out_of_range = list(find_out_of_range_numbers(payload))
    if out_of_range:
        issues = True
        print(f"❌ {path.name}: out-of-range numeric values detected at {out_of_range[:5]}")

    if schema and jsonschema:
        try:
            with schema.open("r", encoding="utf-8") as handle:
                schema_payload = json.load(handle)
            jsonschema.validate(instance=payload, schema=schema_payload)
        except jsonschema.ValidationError as exc:  # pragma: no cover
            issues = True
            print(f"❌ {path.name}: schema violation - {exc.message}")
        except (OSError, json.JSONDecodeError) as exc:  # pragma: no cover
            issues = True
            print(f"❌ {path.name}: unable to load schema ({exc})")
    elif schema and not jsonschema:
        print(f"⚠️  {path.name}: jsonschema not available, schema validation skipped")

    if not issues:
        print(f"✅ {path.name}: lint passed")
    return 1 if issues else 0

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="JSON files to lint")
    parser.add_argument("--schema", type=Path, help="Optional JSON schema path")
    args = parser.parse_args()

    exit_code = 0
    for json_path in args.paths:
        schema_path = args.schema if args.schema and len(args.paths) == 1 else None
        exit_code |= lint_file(json_path, schema_path)
    return exit_code

if __name__ == "__main__":
    raise SystemExit(main())
