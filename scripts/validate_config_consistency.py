#!/usr/bin/env python3
"""
Configuration Consistency Validator.

This script validates that config.py and contextual_parametrization.json
are consistent with each other, ensuring no parameter drift.

Per harmonization strategy:
- config.py is SINGLE SOURCE OF TRUTH for operational values
- contextual_parametrization.json is SPECIFICATION (documentation)
- This script ensures they match

Exit codes:
    0: All checks passed
    1: Validation failed (mismatch detected)
    2: Configuration files not found
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple


class ConfigConsistencyValidator:
    """Validates consistency between config.py and contextual_parametrization.json"""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_all(self) -> bool:
        """
        Run all validation checks.

        Returns:
            True if all checks passed, False otherwise
        """
        print("=" * 80)
        print("CONFIGURATION CONSISTENCY VALIDATION")
        print("=" * 80)
        print()

        # Load both sources
        try:
            param = self._load_parametrization()
            config = self._load_config()
        except FileNotFoundError as e:
            print(f"❌ ERROR: {e}")
            return False

        # Run checks
        self._check_unit_layer_weights(param, config)
        self._check_meta_layer_weights(param, config)
        self._check_anti_universality_threshold(param, config)

        # Report results
        print()
        print("=" * 80)
        print("VALIDATION RESULTS")
        print("=" * 80)

        if self.errors:
            print(f"\n❌ {len(self.errors)} ERROR(S) FOUND:\n")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")

        if self.warnings:
            print(f"\n⚠️  {len(self.warnings)} WARNING(S):\n")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")

        if not self.errors and not self.warnings:
            print("\n✅ ALL CHECKS PASSED - Configuration is consistent!")

        print()
        return len(self.errors) == 0

    def _load_parametrization(self) -> Dict[str, Any]:
        """Load contextual_parametrization.json"""
        param_path = self.repo_root / "config" / "contextual_parametrization.json"

        if not param_path.exists():
            raise FileNotFoundError(f"Parametrization file not found: {param_path}")

        with open(param_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_config(self) -> Any:
        """Load config.py and return DEFAULT_CALIBRATION_CONFIG"""
        # Import config module
        sys.path.insert(0, str(self.repo_root))

        try:
            from src.saaaaaa.core.calibration.config import DEFAULT_CALIBRATION_CONFIG
            return DEFAULT_CALIBRATION_CONFIG
        except ImportError as e:
            raise FileNotFoundError(f"Could not import config.py: {e}")

    def _check_unit_layer_weights(self, param: Dict, config: Any):
        """Validate Unit layer weights match between sources"""
        print("Checking Unit Layer Weights...")

        # Extract from parametrization
        try:
            param_components = param["layer_unit_of_analysis"]["U_computation"]["components"]
            param_weights = {
                "S": param_components["structural_compliance"]["weight"],
                "M": param_components["mandatory_sections_ratio"]["weight"],
                "I": param_components["indicator_quality_score"]["weight"],
                "P": param_components["ppi_completeness"]["weight"],
            }
        except KeyError as e:
            self.errors.append(
                f"Unit layer weights not found in contextual_parametrization.json: {e}"
            )
            return

        # Extract from config.py
        config_weights = {
            "S": config.unit_layer.w_S,
            "M": config.unit_layer.w_M,
            "I": config.unit_layer.w_I,
            "P": config.unit_layer.w_P,
        }

        # Compare
        tolerance = 0.01  # Allow 1% difference
        mismatches = []

        for component in ["S", "M", "I", "P"]:
            param_w = param_weights[component]
            config_w = config_weights[component]
            diff = abs(param_w - config_w)

            if diff > tolerance:
                mismatches.append(
                    f"  {component}: contextual_parametrization={param_w:.3f} vs "
                    f"config.py={config_w:.3f} (diff={diff:.3f})"
                )

        if mismatches:
            self.errors.append(
                "Unit layer weight mismatch:\n" + "\n".join(mismatches)
            )
            print("  ❌ MISMATCH DETECTED")
        else:
            print("  ✅ PASS - Unit layer weights are consistent")

    def _check_meta_layer_weights(self, param: Dict, config: Any):
        """Validate Meta layer weights match between sources"""
        print("Checking Meta Layer Weights...")

        # Extract from parametrization
        try:
            param_weights = param["layer_meta"]["aggregation"]["weights"]
            param_meta = {
                "transparency": param_weights["transparency"],
                "governance": param_weights["governance"],
                "cost": param_weights["cost"],
            }
        except KeyError as e:
            self.errors.append(
                f"Meta layer weights not found in contextual_parametrization.json: {e}"
            )
            return

        # Extract from config.py
        config_meta = {
            "transparency": config.meta_layer.w_transparency,
            "governance": config.meta_layer.w_governance,
            "cost": config.meta_layer.w_cost,
        }

        # Compare
        tolerance = 0.01
        mismatches = []

        for component in ["transparency", "governance", "cost"]:
            param_w = param_meta[component]
            config_w = config_meta[component]
            diff = abs(param_w - config_w)

            if diff > tolerance:
                mismatches.append(
                    f"  {component}: contextual_parametrization={param_w:.3f} vs "
                    f"config.py={config_w:.3f} (diff={diff:.3f})"
                )

        if mismatches:
            self.errors.append(
                "Meta layer weight mismatch:\n" + "\n".join(mismatches)
            )
            print("  ❌ MISMATCH DETECTED")
        else:
            print("  ✅ PASS - Meta layer weights are consistent")

    def _check_anti_universality_threshold(self, param: Dict, config: Any):
        """Validate anti-universality threshold is consistent"""
        print("Checking Anti-Universality Threshold...")

        # Note: contextual_parametrization.json doesn't specify exact threshold
        # It just states the rule. Config.py has max_avg_compatibility = 0.9

        config_threshold = config.max_avg_compatibility

        # Check it's a reasonable value
        if not (0.8 <= config_threshold <= 0.95):
            self.warnings.append(
                f"Anti-universality threshold in config.py is {config_threshold}, "
                f"expected between 0.8 and 0.95"
            )
            print(f"  ⚠️  WARNING - Threshold {config_threshold} is unusual")
        else:
            print(f"  ✅ PASS - Threshold {config_threshold} is reasonable")


def main():
    """Main entry point"""
    repo_root = Path(__file__).parent.parent

    validator = ConfigConsistencyValidator(repo_root)
    success = validator.validate_all()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
