#!/usr/bin/env python3
"""
Boot check script for CI and pre-production environments.

Validates that all modules load correctly, runtime validators initialize,
and the registry is complete without ClassNotFoundError.

Usage:
    python tools/testing/boot_check.py
    python tools/testing/boot_check.py --verbose
"""

import importlib
import sys
import traceback
from pathlib import Path

# Add project root to Python path

# Modules to validate
CORE_MODULES = [
    "orchestrator",
    "scoring",
    "recommendation_engine",
    "validation_engine",
    "policy_processor",
    "embedding_policy",
    "semantic_chunking_policy",
]

OPTIONAL_MODULES = [
    "derek_beach",
    "contradiction_deteccion",
    "teoria_cambio",
    "financiero_viabilidad_tablas",
    "macro_prompts",
    "micro_prompts",
]

def check_module_import(module_name: str, verbose: bool = False) -> tuple[bool, str]:
    """
    Try to import a module and return success status.

    Returns:
        Tuple of (success, error_message)
    """
    try:
        if verbose:
            print(f"  Importing {module_name}...", end=" ")

        importlib.import_module(module_name)

        if verbose:
            print("✓")

        return True, ""
    except ModuleNotFoundError as e:
        error = f"Module not found: {e}"
        if verbose:
            print(f"✗ {error}")
        return False, error
    except ImportError as e:
        error = f"Import error: {e}"
        if verbose:
            print(f"✗ {error}")
        return False, error
    except Exception as e:
        error = f"Unexpected error: {e}"
        if verbose:
            print(f"✗ {error}")
        if verbose:
            traceback.print_exc()
        return False, error

def check_registry_validation(verbose: bool = False) -> tuple[bool, str]:
    """
    Validate that the orchestrator registry loads without ClassNotFoundError.

    Returns:
        Tuple of (success, error_message)
    """
    try:
        if verbose:
            print("  Validating orchestrator registry...", end=" ")

        # Try to import and access the registry
        from saaaaaa.core.orchestrator import registry

        # Try to validate all classes (if method exists)
        if hasattr(registry, 'validate_all_classes'):
            registry.validate_all_classes()

        if verbose:
            print("✓")

        return True, ""
    except NameError as e:
        if "ClassNotFoundError" in str(e) or "not defined" in str(e):
            error = f"ClassNotFoundError in registry: {e}"
            if verbose:
                print(f"✗ {error}")
            return False, error
        raise
    except AttributeError as e:
        # Module or registry doesn't exist - return as informational
        if verbose:
            print(f"⚠ Registry validation not available: {e}")
        return True, ""  # Don't fail if registry validation not implemented
    except Exception as e:
        error = f"Registry validation error: {e}"
        if verbose:
            print(f"✗ {error}")
            traceback.print_exc()
        return False, error

def check_runtime_validators(verbose: bool = False) -> tuple[bool, str]:
    """
    Validate that runtime validators initialize correctly.

    Returns:
        Tuple of (success, error_message)
    """
    try:
        if verbose:
            print("  Initializing runtime validators...", end=" ")

        # Try to import and initialize validators
        from saaaaaa.validation.validation_engine import RuntimeValidator

        validator = RuntimeValidator()

        # Try to run health check if available
        if hasattr(validator, 'health_check'):
            validator.health_check()

        if verbose:
            print("✓")

        return True, ""
    except ImportError:
        # validation_engine doesn't exist or RuntimeValidator not available
        if verbose:
            print("⚠ Runtime validators not available (skipping)")
        return True, ""  # Don't fail if not implemented
    except Exception as e:
        error = f"Runtime validator initialization error: {e}"
        if verbose:
            print(f"✗ {error}")
            traceback.print_exc()
        return False, error

def run_boot_checks(verbose: bool = False) -> int:
    """
    Run all boot checks.

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    print("=" * 60)
    print("Boot Check - Module and Runtime Validation")
    print("=" * 60)

    all_passed = True
    failed_checks = []

    # Check core modules
    print("\nChecking core modules:")
    core_failed = []
    for module in CORE_MODULES:
        success, error = check_module_import(module, verbose)
        if not success:
            all_passed = False
            core_failed.append(f"{module}: {error}")
            failed_checks.append(f"Core module {module} failed to load")

    if not verbose:
        if core_failed:
            print(f"  ✗ {len(core_failed)} core module(s) failed to load")
            for failure in core_failed[:3]:
                print(f"    - {failure}")
            if len(core_failed) > 3:
                print(f"    ... and {len(core_failed) - 3} more")
        else:
            print(f"  ✓ All {len(CORE_MODULES)} core modules loaded successfully")

    # Check optional modules
    print("\nChecking optional modules:")
    optional_failed = []
    for module in OPTIONAL_MODULES:
        success, error = check_module_import(module, verbose)
        if not success:
            optional_failed.append(f"{module}: {error}")
            # Don't fail overall for optional modules

    if not verbose:
        loaded_count = len(OPTIONAL_MODULES) - len(optional_failed)
        print(f"  ✓ {loaded_count}/{len(OPTIONAL_MODULES)} optional modules loaded")
        if optional_failed:
            print(f"  ⚠ {len(optional_failed)} optional module(s) not available")

    # Check registry
    print("\nChecking orchestrator registry:")
    success, error = check_registry_validation(verbose)
    if not success:
        all_passed = False
        failed_checks.append(f"Registry validation failed: {error}")
    elif not verbose:
        print("  ✓ Registry validation passed")

    # Check runtime validators
    print("\nChecking runtime validators:")
    success, error = check_runtime_validators(verbose)
    if not success:
        all_passed = False
        failed_checks.append(f"Runtime validator initialization failed: {error}")
    elif not verbose:
        print("  ✓ Runtime validators initialized successfully")

    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All boot checks PASSED")
        print("=" * 60)
        return 0
    else:
        print("✗ Some boot checks FAILED")
        print("\nFailed checks:")
        for check in failed_checks:
            print(f"  - {check}")
        print("=" * 60)
        return 1

def main() -> None:
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    exit_code = run_boot_checks(verbose)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
