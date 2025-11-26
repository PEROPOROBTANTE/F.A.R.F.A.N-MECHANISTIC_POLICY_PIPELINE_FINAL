
import ast
import os
import json
from typing import Dict, List, Any

class MethodSourceValidator:
    def __init__(self, base_path: str = "src/saaaaaa"):
        self.base_path = base_path
        self.source_map = self._build_source_map()

    def _build_source_map(self) -> Dict[str, Dict[str, Any]]:
        class_map = {}
        for root, _, files in os.walk(self.base_path):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    with open(file_path, "r", encoding="utf-8") as f:
                        try:
                            tree = ast.parse(f.read(), filename=file_path)
                            for node in ast.walk(tree):
                                if isinstance(node, ast.ClassDef):
                                    class_name = node.name
                                    methods = []
                                    for item in node.body:
                                        if isinstance(item, ast.FunctionDef):
                                            methods.append(item.name)
                                    
                                    if class_name in class_map:
                                        # In case of duplicate class names, we might need a more robust way
                                        # to handle this, but for now we'll just overwrite.
                                        # A better approach could be to store a list of locations.
                                        pass

                                    class_map[class_name] = {
                                        "file_path": file_path,
                                        "methods": methods,
                                    }
                        except Exception as e:
                            print(f"Error parsing {file_path}: {e}")
        return class_map

    def validate_executor_methods(self, executor_methods_path: str = "src/saaaaaa/core/orchestrator/executors_methods.json") -> Dict[str, List[str]]:
        with open(executor_methods_path, "r") as f:
            executor_data = json.load(f)

        declared_methods = set()
        for executor_info in executor_data:
            for method_info in executor_info.get("methods", []):
                class_name = method_info.get("class")
                method_name = method_info.get("method")
                if class_name and method_name:
                    declared_methods.add(f"{class_name}.{method_name}")

        valid = []
        missing = []
        
        for method_fqn in declared_methods:
            if "." not in method_fqn:
                # Assuming methods are always Class.method
                continue
            
            class_name, method_name = method_fqn.split(".", 1)

            if class_name not in self.source_map:
                missing.append(method_fqn)
                continue

            class_info = self.source_map[class_name]
            if method_name not in class_info["methods"]:
                missing.append(method_fqn)
            else:
                valid.append(method_fqn)

        # Phantom methods would be those in source but not declared. 
        # The user's request seems to focus on missing/valid from declaration.
        # "phantom" is defined by user as "executors call fantasy methods"
        # which is covered by "missing"
        return {"valid": valid, "missing": missing, "phantom": []}


    def generate_source_truth_map(self) -> Dict[str, Dict[str, Any]]:
        source_truth = {}
        for class_name, info in self.source_map.items():
            file_path = info["file_path"]
            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=file_path)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef) and node.name == class_name:
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef):
                                method_name = item.name
                                fqn = f"{class_name}.{method_name}"
                                
                                # Basic signature extraction
                                args = [arg.arg for arg in item.args.args]
                                signature = f"({', '.join(args)})"
                                # A more advanced version would parse type hints if they exist

                                source_truth[fqn] = {
                                    "exists": True,
                                    "file": file_path,
                                    "line": item.lineno,
                                    "signature": signature,
                                }
        return source_truth

if __name__ == "__main__":
    validator = MethodSourceValidator() 
    
    # 1. Generate the ground-truth map
    source_truth_map = validator.generate_source_truth_map()
    output_path = "method_source_truth.json"
    with open(output_path, "w") as f:
        json.dump(source_truth_map, f, indent=4)
    print(f"Generated source truth map at {output_path}")

    # 2. Validate executor methods
    validation_report = validator.validate_executor_methods()
    report_path = "executor_validation_report.json"
    with open(report_path, "w") as f:
        json.dump(validation_report, f, indent=4)
    print(f"Validation report generated at {report_path}")
    
    print("\nValidation Summary:")
    print(f"  - Valid methods: {len(validation_report['valid'])}")
    print(f"  - Missing methods: {len(validation_report['missing'])}")
    if validation_report['missing']:
        print("\nMissing methods:")
        for method in validation_report['missing']:
            print(f"  - {method}")
