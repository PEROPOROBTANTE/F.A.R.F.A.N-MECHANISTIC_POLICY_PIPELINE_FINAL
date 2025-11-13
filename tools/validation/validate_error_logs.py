#!/usr/bin/env python3
"""
Validate error logs against the contract error log schema.

Usage:
    python tools/validation/validate_error_logs.py --log-file logs/errors.jsonl
    python tools/validation/validate_error_logs.py --log-file logs/errors.jsonl --schema schemas/contract_error_log.schema.json
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("Error: jsonschema not installed. Install with: pip install jsonschema", file=sys.stderr)
    sys.exit(1)

def load_schema(schema_path: str) -> dict:
    """Load JSON schema from file."""
    with open(schema_path) as f:
        return json.load(f)

def validate_log_entry(entry: dict, schema: dict, line_num: int) -> tuple[bool, str]:
    """
    Validate a single log entry against schema.

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        jsonschema.validate(instance=entry, schema=schema)
        return True, ""
    except jsonschema.ValidationError as e:
        return False, f"Line {line_num}: {e.message}"
    except jsonschema.SchemaError as e:
        return False, f"Line {line_num}: Schema error: {e.message}"

def validate_log_file(log_path: str, schema_path: str, verbose: bool = False) -> int:
    """
    Validate all entries in a log file.

    Returns:
        Exit code (0 = success, 1 = validation errors)
    """
    # Load schema
    try:
        schema = load_schema(schema_path)
    except FileNotFoundError:
        print(f"Error: Schema file not found: {schema_path}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in schema file: {e}", file=sys.stderr)
        return 1

    # Check if log file exists
    if not Path(log_path).exists():
        print(f"Error: Log file not found: {log_path}", file=sys.stderr)
        return 1

    # Process log file
    valid_count = 0
    invalid_count = 0
    errors: list[str] = []

    with open(log_path) as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue  # Skip empty lines

            try:
                entry = json.loads(line)
            except json.JSONDecodeError as e:
                invalid_count += 1
                error_msg = f"Line {line_num}: Invalid JSON: {e}"
                errors.append(error_msg)
                if verbose:
                    print(f"✗ {error_msg}", file=sys.stderr)
                continue

            is_valid, error_msg = validate_log_entry(entry, schema, line_num)

            if is_valid:
                valid_count += 1
                if verbose:
                    print(f"✓ Line {line_num}: Valid")
            else:
                invalid_count += 1
                errors.append(error_msg)
                if verbose:
                    print(f"✗ {error_msg}", file=sys.stderr)

    # Print summary
    total = valid_count + invalid_count
    print("\nValidation Summary:")
    print(f"  Total entries: {total}")
    print(f"  Valid: {valid_count} ({valid_count*100//total if total > 0 else 0}%)")
    print(f"  Invalid: {invalid_count} ({invalid_count*100//total if total > 0 else 0}%)")

    if invalid_count > 0:
        print("\nErrors found:")
        for error in errors[:10]:  # Show first 10 errors
            print(f"  - {error}")

        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")

        return 1

    print("\n✓ All log entries are valid!")
    return 0

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate error logs against contract error log schema"
    )
    parser.add_argument(
        "--log-file",
        required=True,
        help="Path to log file (JSONL format, one entry per line)"
    )
    parser.add_argument(
        "--schema",
        default="schemas/contract_error_log.schema.json",
        help="Path to JSON schema file (default: schemas/contract_error_log.schema.json)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print validation status for each log entry"
    )

    args = parser.parse_args()

    exit_code = validate_log_file(args.log_file, args.schema, args.verbose)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
