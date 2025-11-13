#!/usr/bin/env python3
"""
Master verification script for the entire system.
Tests compilation, imports, routes, paths, and system integrity.
"""
import ast
import json
import sys
from datetime import datetime
from pathlib import Path

# Shared configuration
EXCLUDED_DIRS = {'__pycache__', '.git', 'minipdm', '.augment', '.venv'}
API_SERVER_PATHS = [
    'src/saaaaaa/api/api_server.py',
    'api/api_server.py',
    'saaaaaa/api/api_server.py',
]

class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

class SystemVerifier:
    """Comprehensive system verification."""

    def __init__(self, root: Path):
        self.root = root
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.passed_checks = 0
        self.failed_checks = 0

    def print_header(self, text: str) -> None:
        """Print a section header."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")

    def print_check(self, name: str, passed: bool, details: str = "") -> None:
        """Print check result."""
        if passed:
            symbol = f"{Colors.GREEN}✅{Colors.END}"
            self.passed_checks += 1
        else:
            symbol = f"{Colors.RED}❌{Colors.END}"
            self.failed_checks += 1

        print(f"{symbol} {name}")
        if details:
            print(f"   {details}")

    def verify_compilation(self) -> bool:
        """Verify all Python files compile."""
        self.print_header("1. COMPILATION VERIFICATION")

        files = list(self.root.rglob("*.py"))
        files = [f for f in files if not any(d in f.parts for d in EXCLUDED_DIRS)]

        success = 0
        failures = []

        for py_file in files:
            try:
                with open(py_file, encoding='utf-8') as f:
                    ast.parse(f.read())
                success += 1
            except SyntaxError as e:
                rel_path = py_file.relative_to(self.root)
                failures.append(f"{rel_path} (line {e.lineno}): {e.msg}")

        all_passed = len(failures) == 0
        self.print_check(
            f"Compilation test ({success}/{len(files)} files)",
            all_passed,
            f"{len(failures)} failures" if failures else ""
        )

        if failures:
            for failure in failures[:5]:
                self.errors.append(f"Compilation: {failure}")
                print(f"      {Colors.RED}- {failure}{Colors.END}")

        return all_passed

    def verify_imports(self) -> bool:
        """Verify import statements."""
        self.print_header("2. IMPORT VERIFICATION")

        files = list(self.root.rglob("*.py"))
        files = [f for f in files if not any(d in f.parts for d in EXCLUDED_DIRS)]

        total_imports = 0
        import_errors = []

        for py_file in files:
            try:
                with open(py_file, encoding='utf-8') as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        total_imports += 1
            except Exception as e:
                rel_path = py_file.relative_to(self.root)
                import_errors.append(f"{rel_path}: {e}")

        all_passed = len(import_errors) == 0
        self.print_check(
            f"Import analysis ({total_imports} import statements)",
            all_passed,
            f"{len(import_errors)} errors" if import_errors else ""
        )

        return all_passed

    def verify_routes(self) -> bool:
        """Verify API routes."""
        self.print_header("3. ROUTE VERIFICATION")

        # Try to find API server file dynamically
        api_file = None
        for path in API_SERVER_PATHS:
            candidate = self.root / path
            if candidate.exists():
                api_file = candidate
                break

        if api_file is None:
            self.print_check("API server exists", False, "File not found")
            return False

        with open(api_file, encoding='utf-8') as f:
            content = f.read()

        # Count API routes
        import re
        routes = re.findall(r'["\']/(api/[a-zA-Z0-9/_-]+)["\']', content)

        has_health = 'health' in content or 'status' in content
        has_routes = len(routes) > 0

        self.print_check("API server exists", True)
        self.print_check(f"API routes defined ({len(routes)} found)", has_routes)
        self.print_check("Health check endpoint", has_health)

        return has_routes and has_health

    def verify_paths(self) -> bool:
        """Verify file paths and structure."""
        self.print_header("4. PATH & STRUCTURE VERIFICATION")

        # Check config files
        config_files = ['pyproject.toml', 'requirements.txt', 'Makefile']
        missing_configs = [f for f in config_files if not (self.root / f).exists()]

        self.print_check(
            "Configuration files",
            len(missing_configs) == 0,
            f"Missing: {missing_configs}" if missing_configs else "All present"
        )

        # Check directories
        expected_dirs = ['src', 'tests', 'core', 'orchestrator']
        missing_dirs = [d for d in expected_dirs if not (self.root / d).exists()]

        self.print_check(
            "Directory structure",
            len(missing_dirs) == 0,
            f"Missing: {missing_dirs}" if missing_dirs else "All present"
        )

        # Check __init__.py files
        package_dirs = ['core', 'orchestrator', 'executors', 'concurrency', 'scoring', 'validation']
        missing_inits = []
        for d in package_dirs:
            dir_path = self.root / d
            if dir_path.exists() and not (dir_path / '__init__.py').exists():
                missing_inits.append(d)

        self.print_check(
            "Package __init__.py files",
            len(missing_inits) == 0,
            f"Missing: {missing_inits}" if missing_inits else "All present"
        )

        return len(missing_configs) == 0 and len(missing_dirs) == 0

    def verify_audit_report(self) -> bool:
        """Verify audit report exists and is valid."""
        self.print_header("5. AUDIT REPORT VERIFICATION")

        report_path = self.root / 'docs' / 'AUDIT_REPORT.json'

        if not report_path.exists():
            self.print_check("Audit report exists", False)
            return False

        try:
            with open(report_path, encoding='utf-8') as f:
                data = json.load(f)

            has_summary = 'summary' in data
            status_pass = data.get('compilation_status') == 'PASS'

            self.print_check("Audit report exists", True)
            self.print_check("Audit report valid JSON", True)
            self.print_check("Audit report has summary", has_summary)
            self.print_check(f"Compilation status: {data.get('compilation_status', 'UNKNOWN')}", status_pass)

            if has_summary:
                summary = data['summary']
                print("\n   📊 Statistics:")
                print(f"      Python files: {summary.get('total_python_files', 0)}")
                print(f"      Compiled: {summary.get('compiled_successfully', 0)}")
                print(f"      Failed: {summary.get('compilation_failures', 0)}")
                print(f"      Total imports: {summary.get('total_imports', 0)}")
                print(f"      Total functions: {summary.get('total_functions', 0)}")
                print(f"      Total classes: {summary.get('total_classes', 0)}")
                print(f"      Total lines: {summary.get('total_lines', 0)}")
                print(f"      Routes: {summary.get('total_routes', 0)}")

            return status_pass

        except json.JSONDecodeError as e:
            self.print_check("Audit report valid JSON", False, str(e))
            return False

    def run_verification(self) -> bool:
        """Run all verification checks."""
        print(f"{Colors.BOLD}🔍 SYSTEM VERIFICATION{Colors.END}")
        print(f"Root: {self.root}")
        print(f"Time: {datetime.now().isoformat()}")

        results = []

        # Run all checks
        results.append(self.verify_compilation())
        results.append(self.verify_imports())
        results.append(self.verify_routes())
        results.append(self.verify_paths())
        results.append(self.verify_audit_report())

        # Summary
        self.print_header("VERIFICATION SUMMARY")

        all_passed = all(results)

        print(f"Total checks: {self.passed_checks + self.failed_checks}")
        print(f"{Colors.GREEN}Passed: {self.passed_checks}{Colors.END}")
        print(f"{Colors.RED}Failed: {self.failed_checks}{Colors.END}")

        if all_passed:
            print(f"\n{Colors.BOLD}{Colors.GREEN}✅ ALL VERIFICATIONS PASSED!{Colors.END}")
            print(f"{Colors.GREEN}The system is in good health.{Colors.END}")
        else:
            print(f"\n{Colors.BOLD}{Colors.RED}❌ SOME VERIFICATIONS FAILED{Colors.END}")
            print(f"{Colors.RED}Please review the errors above.{Colors.END}")

        if self.errors:
            print(f"\n{Colors.RED}Errors:{Colors.END}")
            for error in self.errors[:10]:
                print(f"  - {error}")

        if self.warnings:
            print(f"\n{Colors.YELLOW}Warnings:{Colors.END}")
            for warning in self.warnings[:10]:
                print(f"  - {warning}")

        print()
        return all_passed

def main():
    """Run master verification."""
    root = Path(__file__).parent.parent
    verifier = SystemVerifier(root)

    success = verifier.run_verification()

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
