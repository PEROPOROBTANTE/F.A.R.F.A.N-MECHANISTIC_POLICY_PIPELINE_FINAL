#!/usr/bin/env python3
"""
Validate Schema Script

Validates the questionnaire monolith schema at initialization.
This script is designed to run in CI/CD pipelines to ensure schema
integrity before deployment.

Usage:
    python scripts/validate_schema.py [monolith_file] [--strict] [--report OUTPUT]

Exit codes:
    0 - Schema validation passed
    1 - Schema validation failed
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
from saaaaaa.utils.validation.schema_validator import MonolithSchemaValidator, SchemaInitializationError

# Try to import orchestrator, but make it optional
try:
    from saaaaaa.core.orchestrator.factory import load_questionnaire_monolith
    from saaaaaa.core.orchestrator import get_questionnaire_provider
    HAS_ORCHESTRATOR = True
except ImportError:
    HAS_ORCHESTRATOR = False
    load_questionnaire_monolith = None

def load_monolith(monolith_path: str = None):
    """
    Load monolith via factory (architecture-compliant).

    This function now uses factory.load_questionnaire_monolith() instead of
    direct file I/O, ensuring compliance with the questionnaire access architecture.

    Args:
        monolith_path: Optional path to monolith file

    Returns:
        dict: Monolith configuration
    """
    if monolith_path:
        # Use factory for I/O-based loading (architecture-compliant)
        if not HAS_ORCHESTRATOR or load_questionnaire_monolith is None:
            raise ImportError(
                "Orchestrator module not available. Cannot load questionnaire monolith."
            )
        return load_questionnaire_monolith(Path(monolith_path))
    else:
        # Use orchestrator provider if available
        if not HAS_ORCHESTRATOR:
            raise ImportError(
                "Orchestrator module not available. Please provide a monolith file path."
            )
        provider = get_questionnaire_provider()
        return provider.load()

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Validate questionnaire monolith schema'
    )
    parser.add_argument(
        'monolith_file',
        nargs='?',
        default=None,
        help='Path to monolith file (uses orchestrator default if not provided)'
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Enable strict mode (raise exception on failure)'
    )
    parser.add_argument(
        '--report',
        type=str,
        help='Path to save validation report JSON'
    )
    parser.add_argument(
        '--schema',
        type=str,
        help='Path to JSON schema file for validation'
    )

    args = parser.parse_args()

    print("=" * 70)
    print("MONOLITH SCHEMA VALIDATION")
    print("=" * 70)
    print()

    try:
        # Load monolith
        print("Loading monolith...")
        if args.monolith_file:
            print(f"  Source: {args.monolith_file}")
        else:
            print("  Source: orchestrator default")

        monolith = load_monolith(args.monolith_file)
        print("  ✅ Loaded successfully")
        print()

        # Validate schema
        print("Validating schema...")
        validator = MonolithSchemaValidator(schema_path=args.schema)
        report = validator.validate_monolith(monolith, strict=args.strict)

        print()
        print("=" * 70)
        print("VALIDATION RESULTS")
        print("=" * 70)
        print()

        print(f"Schema version: {report.schema_version}")
        print(f"Timestamp: {report.timestamp}")
        print(f"Schema hash: {report.schema_hash[:16]}...")
        print()

        print("Question counts:")
        for level, count in report.question_counts.items():
            print(f"  {level}: {count}")
        print()

        print("Referential integrity:")
        for check, passed in report.referential_integrity.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {check}: {'PASS' if passed else 'FAIL'}")
        print()

        if report.warnings:
            print(f"⚠️  Warnings ({len(report.warnings)}):")
            for warning in report.warnings:
                print(f"  - {warning}")
            print()

        if report.errors:
            print(f"❌ Errors ({len(report.errors)}):")
            for error in report.errors:
                print(f"  - {error}")
            print()

        # Save report if requested
        if args.report:
            report_path = Path(args.report)
            report_path.parent.mkdir(parents=True, exist_ok=True)

            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report.model_dump(), f, indent=2, ensure_ascii=False)

            print(f"📄 Report saved to: {args.report}")
            print()

        print("=" * 70)

        if report.validation_passed:
            print("✅ SCHEMA VALIDATION PASSED")
            print("=" * 70)
            return 0
        else:
            print("❌ SCHEMA VALIDATION FAILED")
            print("=" * 70)
            return 1

    except SchemaInitializationError as e:
        print()
        print("=" * 70)
        print("❌ SCHEMA INITIALIZATION ERROR")
        print("=" * 70)
        print()
        print(str(e))
        print()
        return 1

    except Exception as e:
        print()
        print("=" * 70)
        print("❌ UNEXPECTED ERROR")
        print("=" * 70)
        print()
        print(f"Error: {e}")
        print()
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
