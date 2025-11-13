#!/usr/bin/env python3
"""
Validate execution_mapping.yaml against its JSON schema.
"""
import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft7Validator

def load_yaml(file_path: str) -> dict:
    """Load YAML configuration file."""
    with open(file_path) as f:
        return yaml.safe_load(f)

def load_schema(schema_path: str) -> dict:
    """Load JSON schema file."""
    with open(schema_path) as f:
        return json.load(f)

def validate_config(config: dict, schema: dict) -> tuple[bool, list[str]]:
    """
    Validate configuration against schema.

    Returns:
        (is_valid, errors) tuple
    """
    validator = Draft7Validator(schema)
    errors = []

    for error in validator.iter_errors(config):
        # Format error message with path
        path = '.'.join(str(p) for p in error.absolute_path) if error.absolute_path else 'root'
        errors.append(f"{path}: {error.message}")

    return len(errors) == 0, errors

def check_module_references(config: dict) -> tuple[bool, list[str]]:
    """
    Validate that module references in dimension chains exist in modules section.
    """
    errors = []

    # Get all defined modules
    defined_modules = set(config.get('modules', {}).keys())

    # Check dimension chains
    for dim_name, dim_config in config.get('dimensions', {}).items():
        for chain_name, chain_config in dim_config.get('typical_chains', {}).items():
            for step in chain_config.get('sequence', []):
                module_ref = step.get('module')
                if module_ref and module_ref not in defined_modules:
                    errors.append(
                        f"{dim_name}.{chain_name}: references undefined module '{module_ref}'"
                    )

    return len(errors) == 0, errors

def check_scoring_module_references(config: dict) -> tuple[bool, list[str]]:
    """
    Validate that modules referenced in scoring modalities exist.
    """
    errors = []

    defined_modules = set(config.get('modules', {}).keys())

    for modality_name, modality_config in config.get('scoring_modalities', {}).items():
        for module_ref in modality_config.get('modules', []):
            if module_ref not in defined_modules:
                errors.append(
                    f"{modality_name}: references undefined module '{module_ref}'"
                )

    return len(errors) == 0, errors

def main() -> None:
    """Main validation entry point."""
    config_path = "config/execution_mapping.yaml"
    schema_path = "config/schemas/execution_mapping.schema.json"

    print(f"=== Validating {config_path} ===\n")

    # Check files exist
    if not Path(config_path).exists():
        print(f"❌ ERROR: {config_path} not found")
        sys.exit(1)

    if not Path(schema_path).exists():
        print(f"⚠️  WARNING: {schema_path} not found, skipping schema validation")
        schema_validation = False
    else:
        schema_validation = True

    # Load configuration
    try:
        config = load_yaml(config_path)
        print("✓ Loaded configuration file")
    except Exception as e:
        print(f"❌ ERROR: Failed to load YAML: {e}")
        sys.exit(1)

    all_valid = True

    # Schema validation
    if schema_validation:
        try:
            schema = load_schema(schema_path)
            print("✓ Loaded JSON schema")

            is_valid, errors = validate_config(config, schema)
            if is_valid:
                print("✓ Schema validation passed")
            else:
                print("❌ Schema validation failed:")
                for error in errors:
                    print(f"  - {error}")
                all_valid = False
        except Exception as e:
            print(f"❌ ERROR: Schema validation error: {e}")
            all_valid = False

    # Module reference validation
    is_valid, errors = check_module_references(config)
    if is_valid:
        print("✓ Module references valid")
    else:
        print("❌ Invalid module references:")
        for error in errors:
            print(f"  - {error}")
        all_valid = False

    # Scoring modality module references
    is_valid, errors = check_scoring_module_references(config)
    if is_valid:
        print("✓ Scoring modality module references valid")
    else:
        print("❌ Invalid scoring modality module references:")
        for error in errors:
            print(f"  - {error}")
        all_valid = False

    # Summary
    print()
    if all_valid:
        print("✅ All validations passed!")

        # Print stats
        print("\nConfiguration statistics:")
        print(f"  Modules defined: {len(config.get('modules', {}))}")
        print(f"  Dimensions: {len(config.get('dimensions', {}))}")
        print(f"  Scoring modalities: {len(config.get('scoring_modalities', {}))}")
        print(f"  Quality thresholds: {len(config.get('thresholds', {}))}")

        sys.exit(0)
    else:
        print("❌ Validation failed - fix errors above")
        sys.exit(1)

if __name__ == '__main__':
    main()
