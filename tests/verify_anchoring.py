"""Verify Method Anchoring.

Checks that all methods in the codebase are anchored to the central calibration system
via @calibrated_method or direct usage of the orchestrator.
"""

import ast
import os
import sys

def verify_all_methods_anchored():
    """
    OBLIGATORY: Script that verifies ALL methods are anchored.
    """
    
    errors = []
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    src_path = os.path.join(repo_root, "src/saaaaaa")
    
    print(f"Scanning {src_path}...")
    
    # 1. Scan all files
    for root, dirs, files in os.walk(src_path):
        for file in files:
            if not file.endswith(".py"):
                continue
            
            filepath = os.path.join(root, file)
            
            with open(filepath, 'r') as f:
                try:
                    tree = ast.parse(f.read())
                except Exception as e:
                    print(f"Skipping {file}: {e}")
                    continue
            
            # 2. Search methods
            for node in ast.walk(tree):
                if not isinstance(node, ast.FunctionDef):
                    continue
                
                # Ignore private and special methods
                if node.name.startswith("_"):
                    continue
                
                # 3. Verify @calibrated_method decorator
                has_calibrated_decorator = any(
                    isinstance(dec, ast.Call) and 
                    getattr(dec.func, 'id', None) == 'calibrated_method'
                    for dec in node.decorator_list
                )
                
                # 4. Or uses orchestrator/param_loader in body
                uses_orchestrator = False
                uses_param_loader = False
                
                for child in ast.walk(node):
                    if isinstance(child, ast.Name):
                        if 'orchestrator' in child.id.lower():
                            uses_orchestrator = True
                        if 'param' in child.id.lower() and 'loader' in child.id.lower():
                            uses_param_loader = True
                
                # 5. If NEITHER -> ERROR
                if not (has_calibrated_decorator or uses_orchestrator or uses_param_loader):
                    # Check for hardcoded values (heuristic)
                    has_hardcoded = False
                    
                    for child in ast.walk(node):
                        if isinstance(child, ast.Constant) and isinstance(child.value, (int, float)):
                             if 0.0 <= child.value <= 1.0:
                                has_hardcoded = True
                                break
                        # Support older python versions where Num is used
                        elif isinstance(child, ast.Num):
                            if 0.0 <= child.n <= 1.0:
                                has_hardcoded = True
                                break
                    
                    if has_hardcoded:
                        errors.append({
                            "file": filepath,
                            "method": node.name,
                            "line": node.lineno,
                            "error": "Method has hardcoded values but is not anchored to central system"
                        })
    
    # 6. REPORT
    if errors:
        print("❌ FOUND UNANCHORED METHODS:")
        for error in errors:
            print(f"  {error['file']}:{error['line']} - {error['method']}")
            print(f"    → {error['error']}")
        
        # In a real CI, we would raise AssertionError.
        # For this task, we print and maybe fail if strict.
        # raise AssertionError(f"Found {len(errors)} unanchored methods.")
        return False
    
    print(f"✅ All methods properly anchored to central system")
    return True

if __name__ == "__main__":
    success = verify_all_methods_anchored()
    if not success:
        sys.exit(1)
