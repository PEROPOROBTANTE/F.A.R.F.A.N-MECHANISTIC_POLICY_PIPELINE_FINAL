# Canonical Method Inventory Verification

This directory contains the canonical method inventory and verification scripts for the F.A.R.F.A.N policy analysis pipeline.

## Files

- `canonical_method_inventory.json` - The canonical inventory of all methods in the pipeline
- `verify_inventory.py` - Verification script to validate the inventory against required criteria

## Usage

To verify the canonical method inventory:

```bash
python scripts/inventory/verify_inventory.py
```

The script will exit with code 0 if all checks pass, or code 1 if any check fails.

## Verification Criteria

The verification script checks:

1. **Total methods ≥ 1995** - Ensures the inventory contains at least 1995 methods
2. **All 30 D1Q1-D6Q5 executors present** - Validates that all 30 dimension-question executors are present with `is_executor=true`
3. **No duplicate canonical IDs** - Ensures there are no duplicate canonical identifiers
4. **Every method has non-empty role** - Validates that every method has a non-empty role field

## Inventory Structure

The `canonical_method_inventory.json` file should have the following structure:

```json
{
  "metadata": {
    "scan_timestamp": "ISO 8601 timestamp",
    "repository": "Repository name",
    "total_methods": 2000,
    "description": "Description"
  },
  "methods": {
    "method_id": {
      "method_id": "unique identifier",
      "canonical_name": "ClassName.method_name",
      "class_name": "ClassName",
      "is_executor": true/false,
      "role": "EXECUTOR|UTILITY|ANALYZER|..."
    }
  }
}
```

## Executor Naming Convention

Executors must follow the D{n}Q{m} naming pattern where:
- n = dimension (1-6)
- m = question (1-5)

Examples: D1Q1, D1Q2, ..., D6Q5 (30 total executors)

The verification script will match executors using various patterns:
- `D1Q1`
- `D1_Q1`
- `D1-Q1`
- `D1_Q_1`
