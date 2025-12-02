#!/usr/bin/env python3
"""
Verification Script for 15-Contract Suite
Runs all tests and tools, then validates certificates.
"""
import os
import sys
import subprocess
import json
import glob

CONTRACTS_DIR = "farfan_core/farfan_core/contracts"
TOOLS_DIR = os.path.join(CONTRACTS_DIR, "tools")
TESTS_DIR = os.path.join(CONTRACTS_DIR, "tests")

def run_command(cmd, description):
    print(f"Running {description}...")
    try:
        # Add farfan_core to PYTHONPATH
        env = os.environ.copy()
        # Assuming we are running from the root of the repo, and the package is in farfan_core/
        # We need to add 'farfan_core' directory to PYTHONPATH so that 'import farfan_core' works.
        # Structure: ./farfan_core/farfan_core/contracts
        # So we need to add ./farfan_core to path
        
        cwd = os.getcwd()
        farfan_core_path = os.path.join(cwd, "farfan_core")
        env["PYTHONPATH"] = f"{farfan_core_path}:{env.get('PYTHONPATH', '')}"
        
        subprocess.check_call(cmd, shell=True, env=env)
        print(f"✅ {description} PASSED")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ {description} FAILED")
        return False

def main():
    print("=== STARTING VERIFICATION OF 15-CONTRACT SUITE ===")
    
    # 1. Run Pytest Suite
    print("\n--- 1. RUNNING TESTS ---")
    if not run_command(f"pytest {TESTS_DIR} -v", "All Contract Tests"):
        sys.exit(1)

    # 2. Run CLI Tools to generate certificates
    print("\n--- 2. GENERATING CERTIFICATES ---")
    tools = glob.glob(os.path.join(TOOLS_DIR, "*.py"))
    for tool in tools:
        tool_name = os.path.basename(tool)
        if not run_command(f"python3 {tool}", f"Tool: {tool_name}"):
            sys.exit(1)

    # 3. Verify Certificates
    print("\n--- 3. VERIFYING CERTIFICATES ---")
    certs = glob.glob("*.json")
    cert_files = [c for c in certs if c.endswith("_certificate.json")]
    
    all_passed = True
    for cert_file in cert_files:
        try:
            with open(cert_file, "r") as f:
                data = json.load(f)
                if data.get("pass") is True:
                    print(f"✅ {cert_file}: PASS")
                else:
                    print(f"❌ {cert_file}: FAIL (pass != true)")
                    all_passed = False
        except Exception as e:
            print(f"❌ {cert_file}: ERROR ({e})")
            all_passed = False

    if all_passed:
        print("\n=== ALL SYSTEM CONTRACTS VERIFIED SUCCESSFULLY ===")
        sys.exit(0)
    else:
        print("\n=== VERIFICATION FAILED ===")
        sys.exit(1)

if __name__ == "__main__":
    main()
