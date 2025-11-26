
import ast
import json
import re
from src.saaaaaa.core.orchestrator.method_source_validator import MethodSourceValidator

def audit_executor_methods(executor_class_name: str):
    """
    Parses the docstring of an executor class, validates its declared methods,
    and prints a report.
    """
    with open("src/saaaaaa/core/orchestrator/executors.py", "r", encoding="utf-8") as f:
        source_code = f.read()

    tree = ast.parse(source_code)
    
    executor_node = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == executor_class_name:
            executor_node = node
            break
            
    if not executor_node:
        print(f"Executor class '{executor_class_name}' not found.")
        return

    docstring = ast.get_docstring(executor_node)
    if not docstring:
        print(f"Executor class '{executor_class_name}' has no docstring.")
        return

    # Extract methods from docstring
    declared_methods = []
    for line in docstring.splitlines():
        line = line.strip()
        if line.startswith("-"):
            # Example line: "- CausalExtractor._extract_goals"
            match = re.match(r"-\s*([\w\.]+\._\w+|[\w\.]+\.\w+)", line)
            if match:
                method_fqn = match.group(1).strip()
                declared_methods.append(method_fqn)

    print(f"Auditing executor: {executor_class_name}")
    print(f"Found {len(declared_methods)} declared methods in docstring.")

    # Validate methods against source truth
    validator = MethodSourceValidator()
    source_truth = validator.generate_source_truth_map()

    valid_methods = []
    missing_methods = []
    
    print("\n--- Validation Report ---")
    for method_fqn in declared_methods:
        if method_fqn in source_truth:
            valid_methods.append(method_fqn)
            signature = source_truth[method_fqn].get('signature', 'N/A')
            print(f"[EXISTS] {method_fqn} - Signature: {signature}")
        else:
            missing_methods.append(method_fqn)
            print(f"[MISSING] {method_fqn}")
    
    print("\n--- Summary ---")
    print(f"  - Valid methods: {len(valid_methods)}")
    print(f"  - Missing methods: {len(missing_methods)}")
    
    return valid_methods, missing_methods, source_truth

if __name__ == "__main__":
    audit_executor_methods("D1_Q1_QuantitativeBaselineExtractor")
