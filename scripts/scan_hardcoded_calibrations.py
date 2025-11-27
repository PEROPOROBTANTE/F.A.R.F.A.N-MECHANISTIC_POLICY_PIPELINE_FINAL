"""Scan for Hardcoded Calibrations.

Finds and reports hardcoded calibration values.
"""

import re
import os
import sys

def eliminate_hardcoded_calibrations():
    """
    OBLIGATORY: Finds and eliminates ALL hardcoded calibration.
    """
    
    # Dangerous patterns
    DANGER_PATTERNS = [
        (r'(\w+_score|score_\w+|quality|confidence)\s*=\s*(0\.\d+|1\.0)', 
         "Score assignment"),
        
        (r'(if|elif|while)\s+.*[<>]=?\s*(0\.\d+|1\.0)', 
         "Threshold comparison"),
        
        (r'threshold\w*\s*=\s*(0\.\d+|1\.0)', 
         "Threshold assignment"),
        
        (r'(weight|alpha|beta|gamma)\w*\s*=\s*(0\.\d+|1\.0)', 
         "Weight assignment"),
        
        (r'return\s+["\'](?:PASS|FAIL)["\']', 
         "Hardcoded decision"),
    ]
    
    findings = []
    
    # Scan all files
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
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                for pattern, description in DANGER_PATTERNS:
                    if re.search(pattern, line):
                        # Verify if documented functional constant
                        if "# Functional constant" in line or "# Not calibration" in line:
                            continue
                        
                        findings.append({
                            "file": filepath,
                            "line": line_num,
                            "code": line.strip(),
                            "pattern": description,
                            "severity": "CRITICAL"
                        })
    
    # REPORT AND FAIL
    if findings:
        print("🚨 FOUND HARDCODED CALIBRATIONS:")
        print("=" * 80)
        
        for finding in findings:
            print(f"\n{finding['file']}:{finding['line']}")
            print(f"  Pattern: {finding['pattern']}")
            print(f"  Code: {finding['code']}")
            print(f"  → MUST be moved to method_parameters.json or intrinsic_calibration.json")
        
        print("\n" + "=" * 80)
        print(f"TOTAL: {len(findings)} hardcoded calibrations found")
        sys.exit(1)
    
    print("✅ ZERO hardcoded calibrations found. System is fully centralized.")

if __name__ == "__main__":
    eliminate_hardcoded_calibrations()
