"""Test Interpreter Instantiation.

Verifies that the Python interpreter enforces the central calibration system
during method instantiation and execution.
"""

import sys
import os
from pathlib import Path

# Add repo root to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.append(str(REPO_ROOT / "src"))

from saaaaaa.core.calibration.decorators import calibrated_method, CalibrationError
from saaaaaa import get_calibration_orchestrator

class TestMethod:
    @calibrated_method("test.method")
    def run(self, val):
        return val * 2

def test_interpreter_enforcement():
    print("🧪 Testing Interpreter Enforcement of Central System...")
    
    # 1. Setup Mock Data in Singleton
    orchestrator = get_calibration_orchestrator()
    # Mocking intrinsic loader for test
    orchestrator.intrinsic_loader._data["test.method"] = {
        "intrinsic_score": 0.4, # Low score to force failure
        "layer": "utility"
    }
    orchestrator.intrinsic_loader._loaded = True
    
    # 2. Instantiate and Run
    tm = TestMethod()
    
    try:
        # This should fail because score 0.4 < default threshold 0.7
        print("   Executing method with low score...")
        tm.run(10)
        print("❌ Interpreter FAILED to enforce calibration (Method ran despite low score)")
        return False
    except CalibrationError as e:
        print(f"✅ Interpreter SUCCESSFULLY enforced calibration: {e}")
        return True
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    if test_interpreter_enforcement():
        sys.exit(0)
    else:
        sys.exit(1)
