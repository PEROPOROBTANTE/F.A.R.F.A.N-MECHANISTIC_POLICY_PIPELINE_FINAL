#!/usr/bin/env python3
"""CI Scanner: Detect YAML files in executors directory.

This script scans for YAML/YML files in the executors directory and fails
if any are found. This enforces the no-YAML-in-executors requirement.

Exit codes:
- 0: No YAML files found (pass)
- 1: YAML files found (fail)
- 2: Error during scan

Usage:
    python scripts/scan_no_yaml_in_executors.py
"""

import sys
from pathlib import Path
from typing import List


def find_yaml_files(base_path: Path) -> List[Path]:
    """
    Find all YAML files in the executors directory tree.
    
    Args:
        base_path: Base path to search from
        
    Returns:
        List of paths to YAML files found
    """
    yaml_files = []
    
    # Search for .yaml and .yml files
    for pattern in ["**/*.yaml", "**/*.yml"]:
        yaml_files.extend(base_path.glob(pattern))
    
    return yaml_files


def main() -> int:
    """
    Main scanner entry point.
    
    Returns:
        Exit code (0 = pass, 1 = fail, 2 = error)
    """
    try:
        # Get repository root
        script_path = Path(__file__).resolve()
        repo_root = script_path.parent.parent
        
        # Check both executor locations
        executors_paths = [
            repo_root / "executors",
            repo_root / "src" / "saaaaaa" / "core" / "orchestrator" / "executors",
        ]
        
        all_yaml_files = []
        
        print("=" * 70)
        print("CI Quality Gate: no_yaml_in_executors")
        print("=" * 70)
        print()
        
        for executors_path in executors_paths:
            if not executors_path.exists():
                print(f"⚠ Skipping (not found): {executors_path}")
                continue
            
            print(f"Scanning: {executors_path}")
            
            yaml_files = find_yaml_files(executors_path)
            
            if yaml_files:
                all_yaml_files.extend(yaml_files)
                print(f"  ❌ Found {len(yaml_files)} YAML file(s):")
                for yaml_file in yaml_files:
                    rel_path = yaml_file.relative_to(repo_root)
                    print(f"     - {rel_path}")
            else:
                print(f"  ✅ No YAML files found")
        
        print()
        print("-" * 70)
        
        if all_yaml_files:
            print(f"❌ FAIL: Found {len(all_yaml_files)} YAML file(s) in executors")
            print()
            print("Action Required:")
            print("  Remove all YAML files from executors directory.")
            print("  Configuration must live in Python code, not YAML.")
            print()
            return 1
        else:
            print("✅ PASS: No YAML files found in executors")
            print()
            print("Metric: no_yaml_in_executors = True")
            print()
            return 0
    
    except Exception as e:
        print(f"❌ ERROR: Scanner failed: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
