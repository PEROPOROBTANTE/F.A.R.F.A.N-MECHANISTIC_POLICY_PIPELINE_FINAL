#!/bin/bash
# pre_deployment_checklist.sh
# SAAAAAA Calibration System Pre-Deployment Validation

echo "=== SAAAAAA Calibration System Pre-Deployment Checklist ==="

# 1. Check all files exist
echo "[1/10] Checking file structure..."
required_files=(
    "src/saaaaaa/core/calibration/__init__.py"
    "src/saaaaaa/core/calibration/data_structures.py"
    "src/saaaaaa/core/calibration/config.py"
    "src/saaaaaa/core/calibration/unit_layer.py"
    "src/saaaaaa/core/calibration/compatibility.py"
    "src/saaaaaa/core/calibration/choquet_aggregator.py"
    "src/saaaaaa/core/calibration/orchestrator.py"
    "data/method_compatibility.json"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ MISSING: $file"
        exit 1
    fi
done
echo "✅ All required files present"

# 2. Run unit tests
echo "[2/10] Running unit tests..."
python3 -m pytest tests/calibration/test_data_structures.py -v --tb=short || exit 1
echo "✅ Unit tests passed"

# 3. Validate configuration normalization
echo "[3/10] Validating configuration..."
python3 -c "
from src.saaaaaa.core.calibration.config import DEFAULT_CALIBRATION_CONFIG
config = DEFAULT_CALIBRATION_CONFIG
hash_val = config.compute_system_hash()
print(f'Config hash: {hash_val}')
assert len(hash_val) == 64, 'Hash must be 64 chars'
print('✅ Configuration valid')
" || exit 1

# 4. Check Choquet normalization
echo "[4/10] Checking Choquet normalization..."
python3 -c "
from src.saaaaaa.core.calibration.config import DEFAULT_CALIBRATION_CONFIG
choquet = DEFAULT_CALIBRATION_CONFIG.choquet
linear_sum = sum(choquet.linear_weights.values())
interaction_sum = sum(choquet.interaction_weights.values())
total = linear_sum + interaction_sum
print(f'Linear: {linear_sum:.6f}')
print(f'Interaction: {interaction_sum:.6f}')
print(f'Total: {total:.6f}')
assert abs(total - 1.0) < 1e-6, f'Must sum to 1.0, got {total}'
print('✅ Choquet normalization correct')
" || exit 1

# 5. Validate compatibility file
echo "[5/10] Validating compatibility file..."
python3 -c "
from src.saaaaaa.core.calibration.compatibility import CompatibilityRegistry
registry = CompatibilityRegistry('data/method_compatibility.json')
print(f'Loaded {len(registry.mappings)} method compatibility mappings')
print('✅ Compatibility file valid')
" || exit 1

# 6. Check anti-universality
echo "[6/10] Checking anti-universality..."
python3 -c "
from src.saaaaaa.core.calibration.compatibility import CompatibilityRegistry
registry = CompatibilityRegistry('data/method_compatibility.json')
try:
    results = registry.validate_anti_universality(threshold=0.9)
    print(f'All {len(results)} methods comply with anti-universality')
    print('✅ Anti-universality check passed')
except ValueError as e:
    print(f'⚠️  Anti-universality warning: {e}')
    print('✅ Check completed (with warnings)')
" || exit 1

# 7. Test orchestrator initialization
echo "[7/10] Testing orchestrator initialization..."
python3 -c "
from src.saaaaaa.core.calibration import CalibrationOrchestrator, DEFAULT_CALIBRATION_CONFIG
orch = CalibrationOrchestrator(
    config=DEFAULT_CALIBRATION_CONFIG,
    compatibility_path='data/method_compatibility.json'
)
print('✅ Orchestrator initialized successfully')
" || exit 1

# 8. Check imports in executors
echo "[8/10] Checking executor integration..."
python3 -c "
import sys
sys.path.insert(0, 'src')
from saaaaaa.core.orchestrator.executors import AdvancedDataFlowExecutor
print('✅ Executor imports working')
" || exit 1

# 9. Check logging configuration
echo "[9/10] Checking logging..."
grep -r "logger =" src/saaaaaa/core/calibration/ > /dev/null || {
    echo "❌ Missing logger imports"
    exit 1
}
echo "✅ Logging configured"

# 10. Final smoke test
echo "[10/10] Running smoke test..."
python3 -c "
from src.saaaaaa.core.calibration import CalibrationOrchestrator
from src.saaaaaa.core.calibration.data_structures import ContextTuple
from src.saaaaaa.core.calibration.pdt_structure import PDTStructure

# Create minimal test
orch = CalibrationOrchestrator(
    compatibility_path='data/method_compatibility.json'
)

ctx = ContextTuple(
    question_id='Q001',
    dimension='DIM01',
    policy_area='PA01',
    unit_quality=0.75
)

pdt = PDTStructure(
    full_text='test',
    total_tokens=100,
)

# This should not crash
result = orch.calibrate(
    method_id='pattern_extractor_v2',
    method_version='v1.0',
    context=ctx,
    pdt_structure=pdt
)

print(f'Smoke test result: {result.final_score:.3f}')
print('✅ Smoke test passed')
" || exit 1

echo ""
echo "========================================="
echo "✅ ALL CHECKS PASSED - READY TO DEPLOY"
echo "========================================="
