#!/usr/bin/env python3
"""
Import Fixer Script
Automatically resolves phantom imports by converting them to absolute imports.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

class ImportFixer:
    def __init__(self, root_path: Path, report_path: Path):
        self.root = root_path
        self.report = json.loads(report_path.read_text())
        self.fixes_applied = 0
        self.files_modified = set()
        
    def find_correct_module(self, phantom_module: str, current_file: Path) -> Optional[str]:
        """
        Attempt to find the correct absolute module path for a phantom import.
        """
        # Case 0: It's already a valid absolute path but maybe the auditor flagged it wrongly?
        # Or it's a dotted path that exists but was flagged as phantom because of some other reason?
        # Let's check if the dotted path exists relative to root
        parts = phantom_module.split('.')
        if parts[0] == 'saaaaaa':
            # It's already an absolute path, check if it exists
            potential_path = self.root.parent.joinpath(*parts).with_suffix('.py')
            if potential_path.exists():
                return phantom_module
            # Check if it's a package
            potential_pkg = self.root.parent.joinpath(*parts)
            if potential_pkg.is_dir() and (potential_pkg / "__init__.py").exists():
                return phantom_module

        # Strategy 1: Sibling file (implicit relative import)
        # If phantom_module is "decorators", check current_dir/decorators.py
        sibling_path = current_file.parent / f"{phantom_module}.py"
        if sibling_path.exists():
            return self._path_to_module(sibling_path)
            
        sibling_dir = current_file.parent / phantom_module
        if sibling_dir.is_dir() and (sibling_dir / "__init__.py").exists():
            return self._path_to_module(sibling_dir)

        # Strategy 2: Check standard saaaaaa locations by name
        # Only works if the name is unique in the repo
        name = phantom_module.split('.')[-1]
        matches = list(self.root.rglob(f"{name}.py"))
        if len(matches) == 1:
            return self._path_to_module(matches[0])
        elif len(matches) > 1:
            # If multiple matches, try to find one that makes sense (e.g. closest in tree)
            # For now, just pick the first one or skip to avoid wrong fixes
            pass
            
        # Strategy 3: Check if it's a package
        matches = list(self.root.rglob(name))
        valid_packages = [p for p in matches if p.is_dir() and (p / "__init__.py").exists()]
        if len(valid_packages) == 1:
            return self._path_to_module(valid_packages[0])
            
        return None

    def _path_to_module(self, path: Path) -> str:
        """Convert file path to absolute module path starting with saaaaaa"""
        try:
            rel_path = path.relative_to(self.root)
            parts = list(rel_path.parts)
            
            # Ensure it starts with saaaaaa (since self.root is src/saaaaaa)
            module_parts = ["saaaaaa"] + parts
            
            if module_parts[-1].endswith(".py"):
                module_parts[-1] = module_parts[-1][:-3]
            if module_parts[-1] == "__init__":
                module_parts = module_parts[:-1]
                
            return ".".join(module_parts)
        except ValueError:
            return ""

    def fix_imports(self):
        """Iterate through phantom imports and apply fixes"""
        phantom_imports = [
            p for p in self.report["pathologies"]["CRITICAL"] 
            if p["type"] == "phantom_import"
        ]
        
        print(f"Found {len(phantom_imports)} phantom imports to investigate.")
        
        # Group by file to minimize file I/O
        files_to_fix = {}
        for p in phantom_imports:
            file_path = self.root / p["file"]
            if file_path not in files_to_fix:
                files_to_fix[file_path] = []
            files_to_fix[file_path].append(p)
            
        for file_path, problems in files_to_fix.items():
            try:
                content = file_path.read_text()
                lines = content.splitlines()
                modified = False
                
                # Sort problems by line number descending to avoid offset issues
                problems.sort(key=lambda x: x["line"], reverse=True)
                
                for p in problems:
                    line_idx = p["line"] - 1
                    if line_idx >= len(lines):
                        continue
                        
                    line = lines[line_idx]
                    bad_module = p["module"]
                    
                    # Attempt to resolve
                    correct_module = self.find_correct_module(bad_module, file_path)
                    
                    if correct_module:
                        # Construct new import line
                        # Handle "import X" vs "from X import Y"
                        if line.strip().startswith(f"import {bad_module}"):
                            new_line = line.replace(f"import {bad_module}", f"import {correct_module}")
                        elif line.strip().startswith(f"from {bad_module}"):
                            new_line = line.replace(f"from {bad_module}", f"from {correct_module}")
                        else:
                            # Complex case or multi-line, skip for safety
                            print(f"Skipping complex line in {file_path.name}: {line.strip()}")
                            continue
                            
                        if new_line != line:
                            lines[line_idx] = new_line
                            modified = True
                            self.fixes_applied += 1
                            print(f"Fixed in {file_path.name}: {bad_module} -> {correct_module}")
                    else:
                        print(f"Could not resolve module '{bad_module}' in {file_path.name}")
                
                if modified:
                    file_path.write_text("\n".join(lines) + "\n")
                    self.files_modified.add(str(file_path))
                    
            except Exception as e:
                print(f"Error processing {file_path}: {e}")

def main():
    root_path = Path("/home/recovered/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE_FINAL/src/saaaaaa")
    report_path = Path("/home/recovered/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE_FINAL/import_audit_report.json")
    
    if not report_path.exists():
        print("Audit report not found!")
        sys.exit(1)
        
    fixer = ImportFixer(root_path, report_path)
    fixer.fix_imports()
    
    print("=" * 50)
    print(f"Total fixes applied: {fixer.fixes_applied}")
    print(f"Files modified: {len(fixer.files_modified)}")

if __name__ == "__main__":
    main()
