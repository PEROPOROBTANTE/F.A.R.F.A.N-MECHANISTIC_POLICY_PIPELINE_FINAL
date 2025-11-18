#!/usr/bin/env python3
"""
Validate Executor Method Sequences against the Questionnaire Monolith.

This script performs a critical configuration audit by ensuring that the
`METHOD_SEQUENCE` defined in each Executor class in `executors.py` aligns with
the `method_sets` specified for the corresponding question in the monolith.

It helps prevent configuration drift and ensures that the evidence generated
for each question is based on the correct set of analysis methods.

The script will:
1. Load the questionnaire monolith (`data/questionnaire_monolith.json`).
2. Parse the `executors.py` file using Python's AST module.
3. For each of the 30 main executors (D1-Q1 to D6-Q5):
   a. Extract its `METHOD_SEQUENCE`.
   b. Extract the required methods from the monolith's `method_sets`.
   c. Compare the two, checking for missing or extra methods.
4. Print a detailed report of findings, highlighting any discrepancies.
"""

import ast
import json
import os
from collections import defaultdict
from pathlib import Path

# Constants
ROOT_DIR = Path(__file__).parent.parent
MONOLITH_PATH = ROOT_DIR / "data" / "questionnaire_monolith.json"
EXECUTORS_PATH = ROOT_DIR / "src" / "saaaaaa" / "core" / "orchestrator" / "executors.py"
EXECUTOR_SUFFIX = "_Executor"

def load_monolith_requirements() -> dict[str, set[str]]:
    """
    Loads the monolith and extracts the required methods for each base_slot.

    Returns:
        A dictionary mapping a base_slot (e.g., "D1-Q1") to a set of
        required methods (e.g., {"TextMiningEngine.some_method"}).
    """
    requirements = defaultdict(set)
    try:
        with open(MONOLITH_PATH, "r", encoding="utf-8") as f:
            monolith = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Monolith file not found at {MONOLITH_PATH}")
        return {}
    except json.JSONDecodeError as e:
        print(f"ERROR: Could not decode JSON from {MONOLITH_PATH}: {e}")
        return {}

    micro_questions = monolith.get("blocks", {}).get("micro_questions", [])
    print(f"INFO: Monolith loaded. Found {len(micro_questions)} micro-questions.")
    if not micro_questions:
        print("WARNING: No micro_questions found in monolith, returning empty requirements.")

    for question in micro_questions:
        base_slot = question.get("base_slot")
        method_sets = question.get("method_sets", [])
        if not base_slot:
            continue

        for method_spec in method_sets:
            class_name = method_spec.get("class")
            # The monolith uses 'function' for the method name, not 'method'
            method_name = method_spec.get("function")
            if class_name and method_name:
                requirements[base_slot].add(f"{class_name}.{method_name}")

    total_requirements = sum(len(methods) for methods in requirements.values())
    print(f"INFO: Monolith parsing complete. Found {total_requirements} total method requirements.")
    if not requirements:
        print("WARNING: No method requirements were found in the monolith.")

    return requirements


def parse_executors_ast() -> dict[str, list[str]]:
    """
    Parses the executors.py file and extracts the METHOD_SEQUENCE for each executor.

    Returns:
        A dictionary mapping an executor name (e.g., "D1Q1_Executor") to its
        list of methods.
    """
    sequences = {}
    try:
        with open(EXECUTORS_PATH, "r", encoding="utf-8") as f:
            source_code = f.read()
            tree = ast.parse(source_code)
    except FileNotFoundError:
        print(f"ERROR: Executors file not found at {EXECUTORS_PATH}")
        return {}
    except Exception as e:
        print(f"ERROR: Failed to parse AST from {EXECUTORS_PATH}: {e}")
        return {}

    for class_node in ast.walk(tree):
        if isinstance(class_node, ast.ClassDef) and class_node.name.endswith(EXECUTOR_SUFFIX):
            executor_name = class_node.name
            method_list = []

            # Pattern 1: Find `_get_method_sequence` method (e.g., D1Q1_Executor)
            found_sequence = False
            for method_node in class_node.body:
                if isinstance(method_node, ast.FunctionDef) and method_node.name == '_get_method_sequence':
                    for statement in method_node.body:
                        if isinstance(statement, ast.Return) and isinstance(statement.value, ast.List):
                            for element in statement.value.elts:
                                if (isinstance(element, ast.Tuple) and len(element.elts) == 2 and
                                        isinstance(element.elts[0], ast.Constant) and
                                        isinstance(element.elts[1], ast.Constant)):
                                    class_name = element.elts[0].value
                                    method_name = element.elts[1].value
                                    method_list.append(f"{class_name}.{method_name}")
                            sequences[executor_name] = method_list
                            found_sequence = True
                            break
                    if found_sequence:
                        break

            if found_sequence:
                continue

            # Pattern 2: Find `method_sequence` assignment in `execute` method
            for method_node in class_node.body:
                if isinstance(method_node, ast.FunctionDef) and method_node.name == 'execute':
                    for statement in method_node.body:
                        if (isinstance(statement, ast.Assign) and
                                len(statement.targets) == 1 and
                                isinstance(statement.targets[0], ast.Name) and
                                statement.targets[0].id == 'method_sequence'):
                            if isinstance(statement.value, ast.List):
                                for element in statement.value.elts:
                                    if (isinstance(element, ast.Tuple) and len(element.elts) == 2 and
                                            isinstance(element.elts[0], ast.Constant) and
                                            isinstance(element.elts[1], ast.Constant)):
                                        class_name = element.elts[0].value
                                        method_name = element.elts[1].value
                                        method_list.append(f"{class_name}.{method_name}")
                                sequences[executor_name] = method_list
                                found_sequence = True
                                break
                    if found_sequence:
                        break
    print(f"INFO: AST parsing complete. Found {len(sequences)} executor sequences.")
    if not sequences:
        print("WARNING: No executor sequences were found, returning empty dictionary.")
    return sequences


def main():
    """Main function to run the validation."""
    print("--- Executor Method Sequence Validation ---")

    monolith_reqs = load_monolith_requirements()
    executor_seqs = parse_executors_ast()

    if not monolith_reqs or not executor_seqs:
        print("\nCould not proceed due to errors loading files.")
        exit(1)

    all_valid = True
    total_validated = 0

    # Normalize executor keys for matching (e.g., "D1-Q1" -> "D1Q1_Executor")
    executor_map = {
        f"D{d}-Q{q}": f"D{d}Q{q}{EXECUTOR_SUFFIX}"
        for d in range(1, 7) for q in range(1, 6)
    }

    for base_slot, executor_name in sorted(executor_map.items()):
        print(f"\nValidating [{base_slot}] -> [{executor_name}]...")
        total_validated += 1

        required_methods = monolith_reqs.get(base_slot, set())
        actual_methods = set(executor_seqs.get(executor_name, []))

        if not required_methods:
            print(f"  - 🟡 WARNING: No method requirements found for '{base_slot}' in monolith.")
            continue

        if not actual_methods:
            print(f"  - 🔴 ERROR: No METHOD_SEQUENCE found for executor '{executor_name}'.")
            all_valid = False
            continue

        missing_methods = required_methods - actual_methods
        extra_methods = actual_methods - required_methods

        is_valid = not missing_methods
        if is_valid:
            print(f"  - ✅ PASS: All {len(required_methods)} required methods are present.")
            if extra_methods:
                print(f"  - ℹ️  INFO: Found {len(extra_methods)} extra methods:")
                for method in sorted(list(extra_methods)):
                    print(f"    - {method}")
        else:
            all_valid = False
            print(f"  - 🔴 FAIL: Mismatch found.")
            if missing_methods:
                print(f"    - Missing {len(missing_methods)} required methods:")
                for method in sorted(list(missing_methods)):
                    print(f"      - {method}")
            if extra_methods:
                print(f"    - Found {len(extra_methods)} extra methods:")
                for method in sorted(list(extra_methods)):
                    print(f"      - {method}")

    print("\n--- Summary ---")
    print(f"Validated {total_validated} executors.")
    if all_valid:
        print("✅ All executors passed validation (ignoring extra methods).")
    else:
        print("🔴 One or more executors failed validation due to missing required methods.")
        exit(1)

if __name__ == "__main__":
    main()
