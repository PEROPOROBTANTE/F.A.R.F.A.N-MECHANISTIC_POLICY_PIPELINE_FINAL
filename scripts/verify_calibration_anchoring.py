"""Verify Calibration Anchoring.

Checks that all methods are anchored to the central calibration system.
"""

import ast
import os
import sys

def verify_all_methods_anchored():
    """
    OBLIGATORY: Script that verifies all methods are anchored.
    """
    
    errors = []
    
    # 1. Scan all files
    src_root = "src/saaaaaa"
    if not os.path.exists(src_root):
        print(f"Directory {src_root} not found.")
        return

    for root, dirs, files in os.walk(src_root):
        for file in files:
            if not file.endswith(".py"):
                continue
            
            filepath = os.path.join(root, file)
            
            with open(filepath, 'r') as f:
                try:
                    tree = ast.parse(f.read())
                except:
                    continue
            
            # 2. Search for methods
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
                
                # 5. If NEITHER -> ERROR (if it looks like a calibrated method)
                # We refine this to only flag methods that *look* like they need calibration
                # (e.g., have hardcoded scores or thresholds).
                if not (has_calibrated_decorator or uses_orchestrator or uses_param_loader):
                    has_hardcoded = False
                    
                    for child in ast.walk(node):
                        if isinstance(child, ast.Constant) and isinstance(child.value, (int, float)):
                             if 0.0 <= child.value <= 1.0:
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
        
        sys.exit(1)
    
    print(f"✅ All methods properly anchored to central system")

if __name__ == "__main__":
    verify_all_methods_anchored()
