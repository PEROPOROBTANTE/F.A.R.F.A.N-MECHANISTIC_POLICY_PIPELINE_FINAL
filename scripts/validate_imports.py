#!/usr/bin/env python3
"""
Import Validation Script for SAAAAAA System
===========================================

Validates that all imports work correctly across the entire system.
This is the official import certification tool.

Usage:
    python scripts/validate_imports.py
    python scripts/validate_imports.py --verbose
    python scripts/validate_imports.py --fail-on-dependencies

Exit codes:
    0 - All imports successful (or only dependency failures)
    1 - Core import failures detected
"""

import argparse
import importlib
import sys
from pathlib import Path

# Add project paths

class Color:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

class ImportValidator:
    """Validates all imports in the SAAAAAA system"""

    def __init__(self, verbose: bool = False, fail_on_dependencies: bool = False):
        self.verbose = verbose
        self.fail_on_dependencies = fail_on_dependencies
        self.results: dict[str, list] = {
            "core_success": [],
            "core_failed": [],
            "dependency_success": [],
            "dependency_failed": []
        }

    def test_import(self, module_name: str) -> tuple[bool, str]:
        """Test a single import and return success status and error message"""
        try:
            if self.verbose:
                print(f"  Testing {module_name}...", end=" ")
            importlib.import_module(module_name)
            if self.verbose:
                print(f"{Color.GREEN}✓{Color.END}")
            return True, ""
        except Exception as e:
            if self.verbose:
                print(f"{Color.RED}✗{Color.END}")
                print(f"    Error: {e}")
            return False, str(e)

    def validate_all(self) -> int:
        """
        Run comprehensive import validation

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        self._print_header()

        # Define test groups
        core_shims = [
            "aggregation",
            "contracts",
            "evidence_registry",
            "json_contract_loader",
            "macro_prompts",
            "meso_cluster_analysis",
            "orchestrator",
            "qmcm_hooks",
            "recommendation_engine",
            "runtime_error_fixes",
            "seed_factory",
            "signature_validator",
        ]

        core_packages = [
            "saaaaaa",
            "saaaaaa.core",
            "saaaaaa.processing",
            "saaaaaa.analysis",
            "saaaaaa.utils",
            "saaaaaa.concurrency",
            "saaaaaa.api",
            "saaaaaa.infrastructure",
            "saaaaaa.controls",
        ]

        dependency_modules = [
            ("document_ingestion", "pdfplumber"),
            ("embedding_policy", "numpy"),
            ("micro_prompts", "numpy"),
            ("policy_processor", "numpy"),
            ("schema_validator", "pydantic"),
            ("validation_engine", "pydantic"),
        ]

        # Test core shims
        self._print_section("Core Compatibility Shims")
        for module in core_shims:
            success, error = self.test_import(module)
            if success:
                self.results["core_success"].append(module)
                if not self.verbose:
                    print(f"{Color.GREEN}✓{Color.END} {module}")
            else:
                self.results["core_failed"].append((module, error))
                if not self.verbose:
                    print(f"{Color.RED}✗{Color.END} {module}: {error}")

        # Test core packages
        self._print_section("Core Packages")
        for module in core_packages:
            success, error = self.test_import(module)
            if success:
                self.results["core_success"].append(module)
                if not self.verbose:
                    print(f"{Color.GREEN}✓{Color.END} {module}")
            else:
                self.results["core_failed"].append((module, error))
                if not self.verbose:
                    print(f"{Color.RED}✗{Color.END} {module}: {error}")

        # Test dependency modules
        self._print_section("Dependency-Heavy Modules")
        for module, dep in dependency_modules:
            success, error = self.test_import(module)
            if success:
                self.results["dependency_success"].append(module)
                if not self.verbose:
                    print(f"{Color.GREEN}✓{Color.END} {module}")
            else:
                self.results["dependency_failed"].append((module, error, dep))
                if not self.verbose:
                    print(f"{Color.YELLOW}⚠{Color.END} {module} (requires {dep})")

        return self._print_summary()

    def _print_header(self):
        """Print validation header"""
        print(f"\n{Color.BOLD}{'='*70}{Color.END}")
        print(f"{Color.BOLD}SAAAAAA IMPORT VALIDATION{Color.END}")
        print(f"{Color.BOLD}{'='*70}{Color.END}\n")

    def _print_section(self, title: str):
        """Print section header"""
        print(f"\n{Color.BLUE}{title}{Color.END}")
        print("-" * len(title))

    def _print_summary(self) -> int:
        """Print validation summary and return exit code"""
        print(f"\n{Color.BOLD}{'='*70}{Color.END}")
        print(f"{Color.BOLD}VALIDATION SUMMARY{Color.END}")
        print(f"{Color.BOLD}{'='*70}{Color.END}\n")

        total_core = len(self.results["core_success"]) + len(self.results["core_failed"])
        total_dep = len(self.results["dependency_success"]) + len(self.results["dependency_failed"])

        print(f"Core Modules:        {Color.GREEN}{len(self.results['core_success'])}/{total_core}{Color.END} passed")
        print(f"Dependency Modules:  {Color.YELLOW}{len(self.results['dependency_success'])}/{total_dep}{Color.END} passed")

        # Check for core failures
        if self.results["core_failed"]:
            print(f"\n{Color.RED}{Color.BOLD}{'!'*70}{Color.END}")
            print(f"{Color.RED}{Color.BOLD}CRITICAL: CORE MODULE IMPORT FAILURES{Color.END}")
            print(f"{Color.RED}{Color.BOLD}{'!'*70}{Color.END}\n")
            for module, error in self.results["core_failed"]:
                print(f"{Color.RED}❌ {module}{Color.END}")
                print(f"   {error}\n")
            return 1

        # Check for dependency failures
        if self.results["dependency_failed"]:
            print(f"\n{Color.YELLOW}{'─'*70}{Color.END}")
            print(f"{Color.YELLOW}INFO: Missing Optional Dependencies{Color.END}")
            print(f"{Color.YELLOW}{'─'*70}{Color.END}")
            deps_needed = set()
            for module, error, dep in self.results["dependency_failed"]:
                print(f"{Color.YELLOW}⚠{Color.END} {module} requires {dep}")
                deps_needed.add(dep)

            print(f"\n{Color.BLUE}To install missing dependencies:{Color.END}")
            print(f"  pip install {' '.join(deps_needed)}")

            if self.fail_on_dependencies:
                print(f"\n{Color.RED}Failing due to --fail-on-dependencies flag{Color.END}")
                return 1

        # Success!
        print(f"\n{Color.GREEN}{Color.BOLD}{'='*70}{Color.END}")
        print(f"{Color.GREEN}{Color.BOLD}✅ ALL CORE IMPORTS VALIDATED SUCCESSFULLY{Color.END}")
        print(f"{Color.GREEN}{Color.BOLD}{'='*70}{Color.END}\n")

        return 0

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Validate all imports in the SAAAAAA system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Run validation
  %(prog)s --verbose                 # Show detailed output
  %(prog)s --fail-on-dependencies    # Fail if dependencies missing
        """
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--fail-on-dependencies",
        action="store_true",
        help="Fail validation if dependency modules can't be imported"
    )

    args = parser.parse_args()

    validator = ImportValidator(
        verbose=args.verbose,
        fail_on_dependencies=args.fail_on_dependencies
    )
    exit_code = validator.validate_all()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
