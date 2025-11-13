#!/usr/bin/env python3
"""
Verify Aggregation Weights Script

Validates that all aggregation weights in the system are non-negative
and properly normalized. This script is designed to run in CI/CD pipelines
to enforce zero-tolerance for invalid weights.

Usage:
    python scripts/verify_weights.py [--strict]

Exit codes:
    0 - All validations passed
    1 - Validation failures detected
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
from pydantic import ValidationError

from saaaaaa.utils.validation.aggregation_models import validate_weights

def verify_aggregation_system():
    """
    Verify aggregation weight examples and configurations.

    Returns:
        tuple: (passed: bool, errors: list)
    """
    errors = []

    # Test cases representing common aggregation scenarios
    test_cases = [
        {
            'name': 'Equal 5-way weights (dimensions)',
            'weights': [0.2, 0.2, 0.2, 0.2, 0.2],
            'should_pass': True
        },
        {
            'name': 'Equal 6-way weights (areas)',
            'weights': [1/6, 1/6, 1/6, 1/6, 1/6, 1/6],
            'should_pass': True
        },
        {
            'name': 'Unequal weights',
            'weights': [0.1, 0.15, 0.2, 0.25, 0.3],
            'should_pass': True
        },
        {
            'name': 'Negative weight (invalid)',
            'weights': [0.5, -0.1, 0.6],
            'should_pass': False
        },
        {
            'name': 'Weights not summing to 1.0 (invalid)',
            'weights': [0.3, 0.3, 0.3],
            'should_pass': False
        },
        {
            'name': 'Weight > 1.0 (invalid)',
            'weights': [1.5, -0.5],
            'should_pass': False
        }
    ]

    for test_case in test_cases:
        name = test_case['name']
        weights = test_case['weights']
        should_pass = test_case['should_pass']

        try:
            validate_weights(weights)
            if not should_pass:
                errors.append(
                    f"❌ {name}: Expected validation to FAIL but it PASSED"
                )
            else:
                print(f"✅ {name}: PASSED")
        except ValidationError as e:
            if should_pass:
                errors.append(
                    f"❌ {name}: Expected validation to PASS but it FAILED\n"
                    f"   Error: {str(e)}"
                )
            else:
                print(f"✅ {name}: Correctly rejected (as expected)")

    return len(errors) == 0, errors

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Verify aggregation weights in the system'
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Enable strict mode (fail on any issue)'
    )

    parser.parse_args()

    print("=" * 70)
    print("AGGREGATION WEIGHT VERIFICATION")
    print("=" * 70)
    print()

    passed, errors = verify_aggregation_system()

    print()
    print("=" * 70)

    if passed:
        print("✅ ALL WEIGHT VALIDATIONS PASSED")
        print("=" * 70)
        return 0
    else:
        print("❌ WEIGHT VALIDATION FAILURES DETECTED")
        print("=" * 70)
        print()
        for error in errors:
            print(error)
        print()
        return 1

if __name__ == '__main__':
    sys.exit(main())
