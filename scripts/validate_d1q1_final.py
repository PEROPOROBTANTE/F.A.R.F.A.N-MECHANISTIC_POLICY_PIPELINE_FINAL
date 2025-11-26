#!/usr/bin/env python3
"""Validate D1-Q1.v3.FINAL.json against executor_contract.v3.schema.json"""

import json
from pathlib import Path
from jsonschema import Draft7Validator

PROJECT_ROOT = Path(__file__).parent.parent

# Load schema
schema_path = PROJECT_ROOT / "config" / "schemas" / "executor_contract.v3.schema.json"
with open(schema_path) as f:
    schema = json.load(f)

# Load contract
contract_path = PROJECT_ROOT / "config" / "executor_contracts" / "D1-Q1.v3.FINAL.json"
with open(contract_path) as f:
    contract = json.load(f)

# Validate
validator = Draft7Validator(schema)
errors = list(validator.iter_errors(contract))

if errors:
    print(f"❌ VALIDATION FAILED: {len(errors)} errors found\n")
    for i, error in enumerate(errors, 1):
        print(f"Error {i}:")
        print(f"  Path: {' > '.join(str(p) for p in error.path)}")
        print(f"  Message: {error.message}")
        print()
else:
    print("✅ VALIDATION PASSED!")
    print(f"   Contract: {contract_path.name}")
    print(f"   Schema: {schema_path.name}")
    print(f"   Contract version: {contract['identity']['contract_version']}")
    print(f"   Methods: {contract['method_binding']['method_count']}")
    print(f"   Orchestration mode: {contract['method_binding']['orchestration_mode']}")
    print(f"   Has human_answer_structure: {'human_answer_structure' in contract}")
