"""Test No Parallel Systems.

Verifies that singletons are unique and no duplicate configuration files exist.
"""

import os
import sys
import glob

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))


def test_no_parallel_systems():
    """
    OBLIGATORY: Verifies NO parallel systems.
    """

    print("Verifying system uniqueness...")

    # Test 1: Singletons are unique
    try:
        from saaaaaa import get_calibration_orchestrator, get_parameter_loader

        orch1 = get_calibration_orchestrator()
        orch2 = get_calibration_orchestrator()
        if orch1 is not orch2:
            print("❌ CalibrationOrchestrator is NOT singleton!")
            return False

        loader1 = get_parameter_loader()
        loader2 = get_parameter_loader()
        if loader1 is not loader2:
            print("❌ ParameterLoader is NOT singleton!")
            return False

        print("✅ Singletons verified")

    except ImportError as e:
        print(f"❌ Failed to import singletons: {e}")
        return False

    # Test 2: Exactly one live calibration/parameter config in config/ (secondaries allowed elsewhere)
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    config_dir = os.path.join(repo_root, "config")
    secondary_root = os.path.join(config_dir, "secundarios_sistema_c_y_p")

    def is_secondary(path: str) -> bool:
        return os.path.commonpath([os.path.abspath(path), secondary_root]) == os.path.abspath(secondary_root)

    intrinsic = [p for p in glob.glob(os.path.join(config_dir, "intrinsic_calibration*.json")) if not is_secondary(p)]
    params = [p for p in glob.glob(os.path.join(config_dir, "method_parameters*.json")) if not is_secondary(p)]

    if len(intrinsic) != 1:
        print(f"❌ Expected exactly one intrinsic_calibration*.json in config/, found {len(intrinsic)}: {intrinsic}")
        return False
    if len(params) != 1:
        print(f"❌ Expected exactly one method_parameters*.json in config/, found {len(params)}: {params}")
        return False

    print(f"✅ Unique calibration files in config/: {intrinsic[0]}, {params[0]}")

    # Test 3: NO duplicate LAYER_REQUIREMENTS
    layer_req_count = 0
    src_path = os.path.join(repo_root, "src")
    for root, dirs, files in os.walk(src_path):
        for file in files:
            if not file.endswith(".py"):
                continue

            filepath = os.path.join(root, file)
            with open(filepath, 'r') as f:
                content = f.read()

            if 'LAYER_REQUIREMENTS =' in content or 'LAYER_REQUIREMENTS=' in content:
                # Exclude the definition file itself
                if "layer_requirements.py" not in file:
                     print(f"❌ Found LAYER_REQUIREMENTS in {file}")
                     layer_req_count += 1
                else:
                     layer_req_count += 1

    if layer_req_count > 1:
        print(f"❌ Found LAYER_REQUIREMENTS defined in {layer_req_count} places")
        return False

    print("✅ LAYER_REQUIREMENTS uniqueness verified")

    print("✅ NO parallel systems detected. System is unified.")
    return True


if __name__ == "__main__":
    success = test_no_parallel_systems()
    if not success:
        sys.exit(1)
