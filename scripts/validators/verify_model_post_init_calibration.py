#!/usr/bin/env python3
"""
Verification Script: model_post_init Layer-Based Calibration

This script verifies that the model_post_init calibration is properly integrated
and can be loaded by the Python interpreter using the centralized calibration system.

Integration Points:
1. config/layer_calibrations/META_TOOL/model_post_init.json (calibration data)
2. config/canonical_method_catalog.json (method metadata)
3. src/saaaaaa/core/calibration/ (calibration system)
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def verify_calibration_file():
    """Verify calibration file exists and is valid JSON."""
    print("="*70)
    print("STEP 1: Verify Calibration File")
    print("="*70)

    calibration_path = Path("config/layer_calibrations/META_TOOL/model_post_init.json")

    if not calibration_path.exists():
        print(f"✗ Calibration file not found: {calibration_path}")
        return False

    print(f"✓ Calibration file exists: {calibration_path}")

    try:
        with open(calibration_path, 'r') as f:
            data = json.load(f)
        print(f"✓ Valid JSON")

        # Check required fields
        required_fields = ['role', 'required_layers', 'layer_scores', 'fusion_parameters', 'final_calibration']
        for field in required_fields:
            if field in data:
                print(f"✓ Has field: {field}")
            else:
                print(f"✗ Missing field: {field}")
                return False

        # Check final score
        final_score = data['final_calibration']['final_score']
        print(f"✓ Final calibration score: {final_score}")

        if not (0 <= final_score <= 1):
            print(f"✗ Score out of range: {final_score}")
            return False

        return True

    except Exception as e:
        print(f"✗ Error loading calibration: {e}")
        return False


def verify_canonical_catalog():
    """Verify method is in canonical catalog."""
    print("\n" + "="*70)
    print("STEP 2: Verify Canonical Catalog Entry")
    print("="*70)

    catalog_path = Path("config/canonical_method_catalog.json")

    if not catalog_path.exists():
        print(f"✗ Canonical catalog not found: {catalog_path}")
        return False

    print(f"✓ Catalog file exists: {catalog_path}")

    try:
        with open(catalog_path, 'r') as f:
            catalog = json.load(f)

        # Find method
        method_found = False
        method_data = None

        for layer in catalog.get('layers', {}).values():
            if isinstance(layer, list):
                for method in layer:
                    if 'model_post_init' in method.get('canonical_name', ''):
                        method_found = True
                        method_data = method
                        break

        if not method_found:
            print("✗ Method not found in catalog")
            return False

        print(f"✓ Method found: {method_data['canonical_name']}")
        print(f"  - Unique ID: {method_data['unique_id']}")
        print(f"  - Layer: {method_data['layer']}")
        print(f"  - Requires calibration: {method_data['requires_calibration']}")
        print(f"  - Calibration status: {method_data['calibration_status']}")

        return True

    except Exception as e:
        print(f"✗ Error loading catalog: {e}")
        return False


def verify_calibration_system():
    """Verify the calibration system can be imported and used."""
    print("\n" + "="*70)
    print("STEP 3: Verify Calibration System Import")
    print("="*70)

    try:
        from saaaaaa.core.calibration import (
            CalibrationOrchestrator,
            LayerID,
            CalibrationSubject,
            ContextTuple
        )
        print("✓ CalibrationOrchestrator imported")
        print("✓ LayerID imported")
        print("✓ CalibrationSubject imported")
        print("✓ ContextTuple imported")

        # Show available layers
        print("\n✓ Available LayerID values:")
        for layer in LayerID:
            print(f"   - LayerID.{layer.name} = '{layer.value}'")

        return True

    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def verify_fusion_spec():
    """Verify fusion specification has META_TOOL weights."""
    print("\n" + "="*70)
    print("STEP 4: Verify Fusion Specification")
    print("="*70)

    fusion_path = Path("config/fusion_specification.json")

    if not fusion_path.exists():
        print(f"✗ Fusion spec not found: {fusion_path}")
        return False

    print(f"✓ Fusion spec exists: {fusion_path}")

    try:
        with open(fusion_path, 'r') as f:
            fusion_spec = json.load(f)

        if 'META_TOOL' not in fusion_spec.get('role_fusion_parameters', {}):
            print("✗ META_TOOL not in fusion specification")
            return False

        meta_tool = fusion_spec['role_fusion_parameters']['META_TOOL']

        print(f"✓ META_TOOL fusion parameters:")
        print(f"  - Required layers: {meta_tool['required_layers']}")
        print(f"  - Linear weights: {meta_tool['linear_weights']}")
        print(f"  - Interaction weights: {meta_tool['interaction_weights']}")

        # Verify weight sum
        linear_sum = sum(meta_tool['linear_weights'].values())
        interaction_sum = sum(meta_tool['interaction_weights'].values())
        total = linear_sum + interaction_sum

        print(f"  - Weight sum: {total} (linear: {linear_sum}, interaction: {interaction_sum})")

        if abs(total - 1.0) > 1e-9:
            print(f"✗ Weights don't sum to 1.0: {total}")
            return False

        print(f"✓ Weights validated")

        return True

    except Exception as e:
        print(f"✗ Error loading fusion spec: {e}")
        return False


def load_and_verify_calibration():
    """Load calibration data and verify it can be used."""
    print("\n" + "="*70)
    print("STEP 5: Load and Verify Calibration Data")
    print("="*70)

    calibration_path = Path("config/layer_calibrations/META_TOOL/model_post_init.json")

    try:
        with open(calibration_path, 'r') as f:
            cal_data = json.load(f)

        print("✓ Calibration data loaded")

        # Extract key values
        role = cal_data['role']
        required_layers = cal_data['required_layers']
        layer_scores = cal_data['layer_scores']
        final_score = cal_data['final_calibration']['final_score']

        print(f"\n  Role: {role}")
        print(f"  Required layers: {required_layers}")
        print(f"\n  Layer Scores:")
        for layer in required_layers:
            score = layer_scores[layer]['value']
            print(f"    - {layer}: {score:.4f}")

        print(f"\n  Final Calibration Score: {final_score}")

        # Verify Choquet fusion manually
        linear_weights = cal_data['fusion_parameters']['linear_weights']
        interaction_weights = cal_data['fusion_parameters']['interaction_weights']

        # Compute linear term
        linear_term = sum(
            linear_weights[layer] * layer_scores[layer]['value']
            for layer in required_layers
        )

        # Compute interaction term
        interaction_term = 0
        for pair_str, weight in interaction_weights.items():
            # Parse "(@ b, @chain)" → ["@b", "@chain"]
            pair = pair_str.strip('()').split(', ')
            layer1, layer2 = pair[0], pair[1]
            interaction_term += weight * min(
                layer_scores[layer1]['value'],
                layer_scores[layer2]['value']
            )

        computed_score = linear_term + interaction_term

        print(f"\n  Verification:")
        print(f"    - Linear term: {linear_term:.4f}")
        print(f"    - Interaction term: {interaction_term:.4f}")
        print(f"    - Computed score: {computed_score:.4f}")
        print(f"    - Stored score: {final_score}")

        if abs(computed_score - final_score) > 1e-4:
            print(f"✗ Score mismatch!")
            return False

        print(f"✓ Choquet fusion verified")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all verification steps."""
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  model_post_init Calibration Verification".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")

    steps = [
        verify_calibration_file,
        verify_canonical_catalog,
        verify_calibration_system,
        verify_fusion_spec,
        load_and_verify_calibration,
    ]

    results = []
    for step in steps:
        try:
            result = step()
            results.append(result)
        except Exception as e:
            print(f"\n✗ FATAL ERROR in {step.__name__}: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    # Summary
    print("\n" + "="*70)
    print("VERIFICATION SUMMARY")
    print("="*70)

    total = len(results)
    passed = sum(results)

    print(f"\n  Total steps: {total}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {total - passed}")

    if all(results):
        print("\n✓ ALL VERIFICATIONS PASSED")
        print("\nThe calibration is properly integrated and ready to use.")
        print("\nIntegration Points:")
        print("  1. Calibration Data: config/layer_calibrations/META_TOOL/model_post_init.json")
        print("  2. Method Catalog: config/canonical_method_catalog.json")
        print("  3. Fusion Weights: config/fusion_specification.json")
        print("  4. Calibration System: src/saaaaaa/core/calibration/")
        return 0
    else:
        print("\n✗ SOME VERIFICATIONS FAILED")
        print("\nPlease review the errors above and fix before using.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
