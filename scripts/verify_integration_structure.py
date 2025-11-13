#!/usr/bin/env python3
"""
Structural verification of executor integration (no imports needed).
"""
import re
import sys
from pathlib import Path


def verify_executor_structure():
    """Verify the executor has all required calibration integration code."""

    print("=" * 60)
    print("EXECUTOR INTEGRATION STRUCTURE VERIFICATION")
    print("=" * 60)

    executor_file = Path("src/saaaaaa/core/orchestrator/executors.py")

    # Add error handling for file reading
    try:
        content = executor_file.read_text()
    except FileNotFoundError:
        print(f"\n❌ ERROR: File not found: {executor_file}")
        print("   Ensure you're running this script from the project root directory.")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: Failed to read file: {e}")
        return False

    checks = []

    # Check 1: ContextTuple import
    print("\n1. Checking imports...")
    if "from saaaaaa.core.calibration.data_structures import ContextTuple" in content:
        print("   ✅ ContextTuple import found")
        checks.append(True)
    else:
        print("   ❌ ContextTuple import missing")
        checks.append(False)

    # Check 2: datetime import in calibration output section
    if "from datetime import datetime" in content or "import datetime" in content:
        print("   ✅ datetime import found")
        checks.append(True)
    else:
        print("   ❌ datetime import missing")
        checks.append(False)

    # Check 3: Calibration phase markers
    print("\n2. Checking calibration phase...")
    if "# CALIBRATION PHASE" in content and "# END CALIBRATION PHASE" in content:
        print("   ✅ Calibration phase markers found")
        checks.append(True)
    else:
        print("   ❌ Calibration phase markers missing")
        checks.append(False)

    # Check 4: calibration_results variable (robust regex)
    if re.search(r'calibration_results\s*=\s*(\{\}|dict\(\))', content):
        print("   ✅ calibration_results initialization found")
        checks.append(True)
    else:
        print("   ❌ calibration_results initialization missing")
        checks.append(False)

    # Check 5: skipped_methods variable (robust regex)
    if re.search(r'skipped_methods\s*=\s*(\[\]|list\(\))', content):
        print("   ✅ skipped_methods initialization found")
        checks.append(True)
    else:
        print("   ❌ skipped_methods initialization missing")
        checks.append(False)

    # Check 6: Calibration.calibrate() call
    print("\n3. Checking calibration logic...")
    if re.search(r'self\.calibration\.calibrate\s*\(', content):
        print("   ✅ calibration.calibrate() call found")
        checks.append(True)
    else:
        print("   ❌ calibration.calibrate() call missing")
        checks.append(False)

    # Check 7: Method skipping logic (exact comment)
    print("\n4. Checking method skipping...")
    if "# METHOD SKIPPING BASED ON CALIBRATION" in content:
        print("   ✅ Method skipping markers found")
        checks.append(True)
    else:
        print("   ❌ Method skipping markers missing")
        checks.append(False)

    # Check 8: Skip threshold check (usage pattern)
    if re.search(r'cal_score\s*<\s*self\.\w*SKIP_THRESHOLD', content):
        print("   ✅ Skip threshold usage found")
        checks.append(True)
    else:
        print("   ❌ Skip threshold usage missing")
        checks.append(False)

    # Check 9: Continue statement for skipping (flexible whitespace)
    if re.search(r'continue\s*#\s*SKIP', content):
        print("   ✅ Method skip continue found")
        checks.append(True)
    else:
        print("   ❌ Method skip continue missing")
        checks.append(False)

    # Check 10: Calibration output field
    print("\n5. Checking calibration output...")
    if '"_calibration"' in content or "'_calibration'" in content:
        print("   ✅ _calibration field found")
        checks.append(True)
    else:
        print("   ❌ _calibration field missing")
        checks.append(False)

    # Check 11: executed_at field
    if "executed_at" in content:
        print("   ✅ executed_at timestamp found")
        checks.append(True)
    else:
        print("   ❌ executed_at timestamp missing")
        checks.append(False)

    # Check 12: config_hash field
    if "config_hash" in content:
        print("   ✅ config_hash field found")
        checks.append(True)
    else:
        print("   ❌ config_hash field missing")
        checks.append(False)

    # Check 13: scores field
    if re.search(r'"scores"\s*:', content) or re.search(r"'scores'\s*:", content):
        print("   ✅ scores field found")
        checks.append(True)
    else:
        print("   ❌ scores field missing")
        checks.append(False)

    # Check 14: layer_breakdown field
    if "layer_breakdown" in content:
        print("   ✅ layer_breakdown field found")
        checks.append(True)
    else:
        print("   ❌ layer_breakdown field missing")
        checks.append(False)

    # Check 15: skipped_methods in output (accept single or double quotes)
    if re.search(r'["\']skipped_methods["\']\s*:\s*skipped_methods', content):
        print("   ✅ skipped_methods in output found")
        checks.append(True)
    else:
        print("   ❌ skipped_methods in output missing")
        checks.append(False)

    # Summary
    print("\n" + "=" * 60)
    passed = sum(checks)
    total = len(checks)

    if all(checks):
        print(f"✅ ALL {total} STRUCTURAL CHECKS PASSED - Required code patterns found")
        print("=" * 60)
        print("\nNote: This verifies code structure only. Functional integration")
        print("      tests should be run separately to confirm runtime behavior.")
        return True
    else:
        print(f"❌ {total - passed}/{total} CHECKS FAILED")
        print("=" * 60)
        return False


if __name__ == "__main__":
    success = verify_executor_structure()
    sys.exit(0 if success else 1)
