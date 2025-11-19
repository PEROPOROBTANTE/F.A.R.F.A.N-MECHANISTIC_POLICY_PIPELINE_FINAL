#!/usr/bin/env python3
"""
Comprehensive Test Executor and Analyzer
=========================================

Executes ALL tests in the repository with complete transparency.
NO filtering, NO manipulation, NO stubbing.

Analyzes results to identify:
- Structural obstacles (root causes in architecture, core logic, contracts)
- Consequential obstacles (symptoms, surface bugs, noise)

Groups obstacles by workfront for systematic intervention.

KARMIC COMPLIANCE: Every test result is reported honestly.
"""

import json
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple

REPO_ROOT = Path(__file__).parent.parent
REPORTS_DIR = REPO_ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class TestFailure:
    """Represents a test failure."""
    test_id: str
    test_file: str
    error_type: str
    error_message: str
    traceback: str
    is_structural: bool = False  # To be determined by analysis
    workfront: str = ""  # Domain, module, boundary, infrastructure, data
    root_cause: str = ""


@dataclass
class TestExecutionReport:
    """Complete test execution report."""
    timestamp: str
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    skipped: int = 0
    duration_seconds: float = 0.0

    failures: List[TestFailure] = field(default_factory=list)

    # Classification
    structural_failures: List[TestFailure] = field(default_factory=list)
    consequential_failures: List[TestFailure] = field(default_factory=list)

    # Workfront grouping
    workfronts: Dict[str, List[TestFailure]] = field(default_factory=lambda: defaultdict(list))


class ComprehensiveTestExecutor:
    """Executes and analyzes all tests systematically."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.reports_dir = REPORTS_DIR
        self.report = TestExecutionReport(timestamp=datetime.now().isoformat())

    def execute_all_tests(self) -> TestExecutionReport:
        """
        Execute ALL tests with complete transparency.

        NO filtering, NO skipping, NO manipulation.
        """
        print("=" * 80)
        print("COMPREHENSIVE TEST EXECUTION - COMPLETE INVENTORY")
        print("=" * 80)
        print(f"Timestamp: {self.report.timestamp}")
        print(f"Repository: {self.repo_root}")
        print()
        print("KARMIC COMPLIANCE: All tests will be executed honestly.")
        print("NO stubbing, NO filtering, NO manipulation.")
        print("=" * 80)
        print()

        # Execute pytest with comprehensive options
        cmd = [
            "pytest",
            "tests/",
            "-v",  # Verbose
            "--tb=short",  # Short traceback
            "--strict-markers",  # Strict marker validation
            "--strict-config",  # Strict config validation
            "-ra",  # Show all test summary info
            "--continue-on-collection-errors",  # Don't stop on collection errors
        ]

        print(f"Executing: {' '.join(cmd)}")
        print()

        start_time = datetime.now()

        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes max
            )

            end_time = datetime.now()
            self.report.duration_seconds = (end_time - start_time).total_seconds()

            # Save raw output
            output_file = self.reports_dir / "pytest_raw_output.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("STDOUT:\n")
                f.write("=" * 80 + "\n")
                f.write(result.stdout)
                f.write("\n\nSTDERR:\n")
                f.write("=" * 80 + "\n")
                f.write(result.stderr)
                f.write("\n\nRETURN CODE:\n")
                f.write("=" * 80 + "\n")
                f.write(str(result.returncode))

            print(f"Raw output saved to: {output_file}")

            # Parse JSON report if available
            json_report_path = self.reports_dir / 'pytest_report.json'
            if json_report_path.exists():
                with open(json_report_path, 'r', encoding='utf-8') as f:
                    pytest_data = json.load(f)
                self._parse_pytest_json(pytest_data)
            else:
                # Parse from text output
                self._parse_text_output(result.stdout, result.stderr)

            # Print immediate summary
            self._print_summary()

            return self.report

        except subprocess.TimeoutExpired:
            print("❌ ERROR: Test execution timed out after 10 minutes")
            return self.report
        except Exception as e:
            print(f"❌ ERROR: Test execution failed: {e}")
            import traceback
            traceback.print_exc()
            return self.report

    def _parse_pytest_json(self, data: dict) -> None:
        """Parse pytest JSON report."""
        summary = data.get('summary', {})
        self.report.total_tests = summary.get('total', 0)
        self.report.passed = summary.get('passed', 0)
        self.report.failed = summary.get('failed', 0)
        self.report.errors = summary.get('error', 0)
        self.report.skipped = summary.get('skipped', 0)

        # Parse test results
        for test in data.get('tests', []):
            if test.get('outcome') in ['failed', 'error']:
                failure = TestFailure(
                    test_id=test.get('nodeid', ''),
                    test_file=test.get('nodeid', '').split('::')[0] if '::' in test.get('nodeid', '') else '',
                    error_type=test.get('call', {}).get('crash', {}).get('path', 'Unknown'),
                    error_message=test.get('call', {}).get('longrepr', 'No message'),
                    traceback=str(test.get('call', {}))
                )
                self.report.failures.append(failure)

    def _parse_text_output(self, stdout: str, stderr: str) -> None:
        """Parse text output if JSON not available."""
        import re

        lines = stdout.split('\n')

        # Parse summary line
        for line in lines:
            if 'passed' in line or 'failed' in line:
                passed_match = re.search(r'(\d+) passed', line)
                failed_match = re.search(r'(\d+) failed', line)
                error_match = re.search(r'(\d+) error', line)
                skipped_match = re.search(r'(\d+) skipped', line)

                if passed_match:
                    self.report.passed = int(passed_match.group(1))
                if failed_match:
                    self.report.failed = int(failed_match.group(1))
                if error_match:
                    self.report.errors = int(error_match.group(1))
                if skipped_match:
                    self.report.skipped = int(skipped_match.group(1))

        self.report.total_tests = (
            self.report.passed +
            self.report.failed +
            self.report.errors +
            self.report.skipped
        )

        # Parse failures from FAILED sections
        current_failure = None
        in_traceback = False
        traceback_lines = []

        for i, line in enumerate(lines):
            # Match FAILED test lines
            if line.startswith('FAILED '):
                if current_failure and traceback_lines:
                    current_failure.traceback = '\n'.join(traceback_lines)
                    self.report.failures.append(current_failure)

                # Extract test ID
                match = re.search(r'FAILED (.*?) -', line)
                if match:
                    test_id = match.group(1)
                    test_file = test_id.split('::')[0] if '::' in test_id else ''
                    current_failure = TestFailure(
                        test_id=test_id,
                        test_file=test_file,
                        error_type='',
                        error_message='',
                        traceback=''
                    )
                    traceback_lines = []
                    in_traceback = False

            # Capture error types and messages from short tracebacks
            elif current_failure and ('Error' in line or 'Exception' in line or 'Failed' in line):
                if not current_failure.error_type:
                    error_match = re.search(r'(\w+Error|\w+Exception):', line)
                    if error_match:
                        current_failure.error_type = error_match.group(1)
                        current_failure.error_message = line.split(':', 1)[1].strip() if ':' in line else line
                traceback_lines.append(line)
            elif current_failure:
                traceback_lines.append(line)

        # Add last failure if exists
        if current_failure and traceback_lines:
            current_failure.traceback = '\n'.join(traceback_lines)
            self.report.failures.append(current_failure)

    def _print_summary(self) -> None:
        """Print execution summary."""
        print()
        print("=" * 80)
        print("TEST EXECUTION SUMMARY")
        print("=" * 80)
        print(f"Total Tests:     {self.report.total_tests}")
        print(f"Passed:          {self.report.passed} ({self._percentage(self.report.passed)}%)")
        print(f"Failed:          {self.report.failed} ({self._percentage(self.report.failed)}%)")
        print(f"Errors:          {self.report.errors} ({self._percentage(self.report.errors)}%)")
        print(f"Skipped:         {self.report.skipped} ({self._percentage(self.report.skipped)}%)")
        print(f"Duration:        {self.report.duration_seconds:.2f}s")
        print("=" * 80)
        print()

    def _percentage(self, count: int) -> float:
        """Calculate percentage."""
        if self.report.total_tests == 0:
            return 0.0
        return round((count / self.report.total_tests) * 100, 1)

    def analyze_failures(self) -> None:
        """
        STEP 4: Classify failures as structural vs consequential.

        Structural: root causes in architecture, core logic, data contracts
        Consequential: symptoms, noise, surface bugs
        """
        print("=" * 80)
        print("STEP 4: CLASSIFYING OBSTACLES")
        print("=" * 80)
        print()

        # Analyze each failure
        for failure in self.report.failures:
            self._classify_failure(failure)

        # Separate into structural and consequential
        self.report.structural_failures = [
            f for f in self.report.failures if f.is_structural
        ]
        self.report.consequential_failures = [
            f for f in self.report.failures if not f.is_structural
        ]

        print(f"Structural Failures:    {len(self.report.structural_failures)}")
        print(f"Consequential Failures: {len(self.report.consequential_failures)}")
        print()

        # Group by workfront
        for failure in self.report.structural_failures:
            self.report.workfronts[failure.workfront].append(failure)

        print("WORKFRONT DISTRIBUTION:")
        for workfront, failures in sorted(self.report.workfronts.items()):
            print(f"  {workfront}: {len(failures)} failures")
        print()

    def _classify_failure(self, failure: TestFailure) -> None:
        """
        Classify a failure as structural or consequential.

        Structural indicators:
        - ModuleNotFoundError (missing dependencies, imports)
        - ImportError (architectural issues)
        - AttributeError in core modules
        - TypeErrors in contracts
        - Configuration errors

        Consequential indicators:
        - AssertionError (test expectations)
        - ValueError in test setup
        - Fixture issues (test infrastructure)
        """
        error_msg = failure.error_message.lower()
        error_type = failure.error_type.lower()

        # Structural patterns
        structural_patterns = [
            'modulenotfounderror',
            'importerror',
            'no module named',
            'cannot import',
            'attribute error',  # In production code
            'configuration error',
            'contract',
            'schema',
            'validation error',  # In core
        ]

        # Check for structural indicators
        is_structural = any(pattern in error_msg or pattern in error_type
                          for pattern in structural_patterns)

        # Additional structural checks
        if 'core' in failure.test_file or 'orchestrator' in failure.test_file:
            # Errors in core/orchestrator are likely structural
            if 'attributeerror' in error_type or 'typeerror' in error_type:
                is_structural = True

        failure.is_structural = is_structural

        # Assign workfront
        if is_structural:
            failure.workfront = self._determine_workfront(failure)
            failure.root_cause = self._infer_root_cause(failure)

    def _determine_workfront(self, failure: TestFailure) -> str:
        """Determine which workfront this failure belongs to."""
        file_path = failure.test_file.lower()
        error_msg = failure.error_message.lower()

        # Domain workfronts
        if 'calibration' in file_path:
            return 'WORKFRONT_CALIBRATION'
        elif 'orchestrator' in file_path:
            return 'WORKFRONT_ORCHESTRATOR'
        elif 'processing' in file_path:
            return 'WORKFRONT_PROCESSING'
        elif 'analysis' in file_path:
            return 'WORKFRONT_ANALYSIS'

        # Cross-cutting workfronts
        elif 'import' in error_msg or 'module' in error_msg:
            return 'WORKFRONT_DEPENDENCIES'
        elif 'contract' in error_msg or 'schema' in error_msg:
            return 'WORKFRONT_CONTRACTS'
        elif 'validation' in file_path:
            return 'WORKFRONT_VALIDATION'

        # Infrastructure
        elif 'fixture' in error_msg or 'conftest' in file_path:
            return 'WORKFRONT_TEST_INFRASTRUCTURE'

        return 'WORKFRONT_UNKNOWN'

    def _infer_root_cause(self, failure: TestFailure) -> str:
        """Infer the root cause of a structural failure."""
        error_msg = failure.error_message.lower()

        if 'no module named' in error_msg or 'modulenotfounderror' in error_msg:
            # Extract module name
            import re
            match = re.search(r"no module named ['\"]([^'\"]+)['\"]", error_msg)
            if match:
                return f"Missing module: {match.group(1)}"
            return "Missing Python module/package"

        elif 'importerror' in error_msg or 'cannot import' in error_msg:
            return "Import dependency issue or circular import"

        elif 'attributeerror' in error_msg:
            return "Missing attribute in production code (API change or incomplete implementation)"

        elif 'typeerror' in error_msg:
            return "Type mismatch in contracts or function signatures"

        elif 'configuration' in error_msg:
            return "Configuration file or environment setup issue"

        return "Unknown structural issue"

    def generate_comprehensive_report(self) -> Path:
        """Generate comprehensive analysis report."""
        report_path = self.reports_dir / "comprehensive_test_analysis.md"

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# Comprehensive Test Execution Analysis\n\n")
            f.write(f"**Generated:** {self.report.timestamp}\n\n")
            f.write(f"**Duration:** {self.report.duration_seconds:.2f}s\n\n")

            f.write("## Executive Summary\n\n")
            f.write(f"- **Total Tests:** {self.report.total_tests}\n")
            f.write(f"- **Passed:** {self.report.passed} ({self._percentage(self.report.passed)}%)\n")
            f.write(f"- **Failed:** {self.report.failed} ({self._percentage(self.report.failed)}%)\n")
            f.write(f"- **Errors:** {self.report.errors} ({self._percentage(self.report.errors)}%)\n")
            f.write(f"- **Skipped:** {self.report.skipped} ({self._percentage(self.report.skipped)}%)\n\n")

            f.write("## Obstacle Classification\n\n")
            f.write(f"- **Structural Failures:** {len(self.report.structural_failures)}\n")
            f.write(f"- **Consequential Failures:** {len(self.report.consequential_failures)}\n\n")

            f.write("## Workfront Distribution\n\n")
            for workfront, failures in sorted(self.report.workfronts.items()):
                f.write(f"### {workfront}: {len(failures)} failures\n\n")
                for failure in failures:
                    f.write(f"**Test:** `{failure.test_id}`\n")
                    f.write(f"**Root Cause:** {failure.root_cause}\n")
                    f.write(f"**Error:** {failure.error_message[:200]}...\n\n")

            f.write("## Next Steps\n\n")
            f.write("1. Address structural failures by workfront\n")
            f.write("2. Design interventions at workfront level\n")
            f.write("3. Fix root causes, not symptoms\n")
            f.write("4. Re-run tests to verify fixes\n")

        return report_path


def main() -> int:
    """Main entry point."""
    executor = ComprehensiveTestExecutor(REPO_ROOT)

    # STEP 1: Execute all tests
    print("STEP 1: EXECUTING ALL TESTS")
    print()
    report = executor.execute_all_tests()

    # STEP 4: Analyze and classify
    print()
    executor.analyze_failures()

    # Generate report
    report_path = executor.generate_comprehensive_report()
    print(f"Comprehensive report generated: {report_path}")

    # Return exit code
    if report.failed > 0 or report.errors > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
