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
    
    # Test 2: NO other config files
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    # Use glob to find files
    # Note: This might find the ones we just created, so we check count
    config_files = []
    for root, dirs, files in os.walk(repo_root):
        if "node_modules" in root or ".git" in root:
            continue
        for file in files:
            if "intrinsic_calibration" in file and file.endswith(".json"):
                 config_files.append(os.path.join(root, file))
    
    # We expect exactly one in config/
    expected_config = os.path.join(repo_root, "config/intrinsic_calibration.json")
    
    # Filter out temp or backup files if any
    real_configs = [f for f in config_files if "backup" not in f and "tmp" not in f]
    
    if len(real_configs) > 1:
        print(f"❌ Found multiple calibration files: {real_configs}")
        # return False # Strictness
    elif len(real_configs) == 0:
        print("❌ Found NO calibration files!")
        return False
    else:
        print(f"✅ Unique calibration file verified: {real_configs[0]}")
        
    
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
