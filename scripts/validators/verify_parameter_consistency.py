#!/usr/bin/env python3
"""
Parameter Consistency Verification Script

VERIFICATION CONDITIONS:
1. Every parameter has all required fields
2. No parameter has both required=true AND has_default=true
3. default_type is one of [literal, expression, complex]
4. Determinism: re-run produces identical results

FAILURE CONDITION:
- If ANY parameter violates invariant or if re-run produces different results,
  ABORT with 'parameter extraction inconsistent' error
- No parametrizable method may lack input_parameters block
"""
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


class ParameterConsistencyError(Exception):
    """Raised when parameter consistency checks fail."""
    pass


def compute_hash(data: dict[str, Any]) -> str:
    """Compute deterministic hash of JSON data."""
    json_str = json.dumps(data, sort_keys=True, indent=None)
    return hashlib.sha256(json_str.encode('utf-8')).hexdigest()


def validate_parameter(param: dict[str, Any], method_id: str) -> list[str]:
    """
    Validate a single parameter descriptor.
    
    Returns list of error messages (empty if valid).
    """
    errors = []

    required_fields = ['name', 'type_hint', 'has_default', 'required',
                      'default_value', 'default_type', 'default_source']

    for field in required_fields:
        if field not in param:
            errors.append(
                f"Parameter '{param.get('name', 'UNKNOWN')}' in method '{method_id}' "
                f"missing required field: {field}"
            )

    if len(errors) > 0:
        return errors

    if param['required'] and param['has_default']:
        errors.append(
            f"Parameter '{param['name']}' in method '{method_id}' "
            f"violates invariant: required=True AND has_default=True"
        )

    if param['required'] != (not param['has_default']):
        errors.append(
            f"Parameter '{param['name']}' in method '{method_id}' "
            f"violates invariant: required != !has_default"
        )

    if param['has_default'] and param['default_type'] is not None:
        valid_types = ['literal', 'expression', 'complex']
        if param['default_type'] not in valid_types:
            errors.append(
                f"Parameter '{param['name']}' in method '{method_id}' "
                f"has invalid default_type: '{param['default_type']}' "
                f"(must be one of {valid_types})"
            )

    return errors


def validate_method(method_id: str, method_data: dict[str, Any]) -> list[str]:
    """
    Validate a single method's parameter structure.
    
    Returns list of error messages (empty if valid).
    """
    errors = []

    signature = method_data.get('signature', {})
    requiere_parametrizacion = signature.get('requiere_parametrizacion', False)
    input_parameters = signature.get('input_parameters')

    if requiere_parametrizacion:
        if input_parameters is None:
            errors.append(
                f"Method '{method_id}' has requiere_parametrizacion=true "
                f"but lacks input_parameters block"
            )
            return errors

        if not isinstance(input_parameters, list):
            errors.append(
                f"Method '{method_id}' input_parameters is not a list"
            )
            return errors

        for param in input_parameters:
            param_errors = validate_parameter(param, method_id)
            errors.extend(param_errors)

    return errors


def validate_inventory(inventory_path: Path) -> tuple[list[str], str]:
    """
    Validate inventory file for parameter consistency.
    
    Returns (errors, hash) tuple.
    """
    if not inventory_path.exists():
        raise FileNotFoundError(f"Inventory file not found: {inventory_path}")

    with open(inventory_path) as f:
        data = json.load(f)

    inventory_hash = compute_hash(data)

    errors = []
    methods = data.get('methods', {})

    for method_id, method_data in methods.items():
        method_errors = validate_method(method_id, method_data)
        errors.extend(method_errors)

    return errors, inventory_hash


def run_extraction() -> Path:
    """
    Run the method inventory extraction.
    
    Returns path to generated inventory file.
    """
    output_path = Path("artifacts/test_runs/method_inventory_verification.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        from farfan_pipeline.core.method_inventory import (
            build_method_inventory,
            method_inventory_to_json,
        )

        inventory = build_method_inventory()
        data = method_inventory_to_json(inventory)

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        return output_path
    except Exception as e:
        raise RuntimeError(f"Extraction failed: {e}") from e


def main() -> int:
    """Main verification routine."""
    print("=" * 80)
    print("PARAMETER CONSISTENCY VERIFICATION")
    print("=" * 80)

    try:
        print("\n[1/4] Running first extraction...")
        inventory_path_1 = run_extraction()
        print(f"      ✓ Generated: {inventory_path_1}")

        print("\n[2/4] Validating first extraction...")
        errors_1, hash_1 = validate_inventory(inventory_path_1)

        if errors_1:
            print(f"      ✗ FAILED: {len(errors_1)} errors found")
            for error in errors_1[:10]:
                print(f"        - {error}")
            if len(errors_1) > 10:
                print(f"        ... and {len(errors_1) - 10} more errors")
            raise ParameterConsistencyError(
                f"parameter extraction inconsistent: {len(errors_1)} validation errors"
            )

        print("      ✓ All parameters valid")
        print(f"      ✓ Hash: {hash_1[:16]}...")

        print("\n[3/4] Running second extraction (determinism check)...")
        inventory_path_2 = run_extraction()
        print(f"      ✓ Generated: {inventory_path_2}")

        print("\n[4/4] Comparing hashes...")
        errors_2, hash_2 = validate_inventory(inventory_path_2)

        if errors_2:
            print(f"      ✗ FAILED: Second run has {len(errors_2)} errors")
            raise ParameterConsistencyError(
                "parameter extraction inconsistent: second run validation failed"
            )

        if hash_1 != hash_2:
            print("      ✗ FAILED: Hashes differ")
            print(f"        Run 1: {hash_1}")
            print(f"        Run 2: {hash_2}")
            raise ParameterConsistencyError(
                "parameter extraction inconsistent: non-deterministic results"
            )

        print(f"      ✓ Hashes match: {hash_2[:16]}...")

        print("\n" + "=" * 80)
        print("✓ VERIFICATION PASSED")
        print("=" * 80)
        print("  - All parameters have required fields")
        print("  - No parameter violates required/has_default invariant")
        print("  - All default_types are valid")
        print("  - Extraction is deterministic")
        print("=" * 80)

        return 0

    except ParameterConsistencyError as e:
        print("\n" + "=" * 80)
        print("✗ VERIFICATION FAILED")
        print("=" * 80)
        print(f"ERROR: {e}")
        print("=" * 80)
        return 1

    except Exception as e:
        print("\n" + "=" * 80)
        print("✗ VERIFICATION ERROR")
        print("=" * 80)
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 80)
        return 2


if __name__ == "__main__":
    sys.exit(main())
