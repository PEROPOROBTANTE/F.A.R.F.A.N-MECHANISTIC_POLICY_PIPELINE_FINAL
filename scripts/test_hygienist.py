#!/usr/bin/env python3
"""
Test Hygienist Script
=====================

Comprehensive test suite analyzer that:
1. Detects outdated tests
2. Measures degree of obsolescence
3. Determines value added by each test
4. Calculates refactoring complexity
5. Recommends refactor/update vs deprecation

Evidence-based decision making for test suite hygiene.
"""

import ast
import json
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Configuration
REPO_ROOT = Path(__file__).parent.parent
SRC_DIR = REPO_ROOT / "src"
TESTS_DIR = REPO_ROOT / "tests"
OUTPUT_DIR = REPO_ROOT / "reports"


@dataclass
class TestMetrics:
    """Metrics for a single test file."""

    file_path: Path
    test_name: str

    # Import analysis
    imports_valid: bool = True
    missing_imports: List[str] = field(default_factory=list)
    import_errors: List[str] = field(default_factory=list)

    # Execution analysis
    can_execute: bool = True
    execution_errors: List[str] = field(default_factory=list)

    # Complexity metrics
    lines_of_code: int = 0
    num_test_functions: int = 0
    cyclomatic_complexity: int = 0

    # Value metrics
    coverage_percentage: float = 0.0
    tests_unique_code: bool = True
    tests_structural_issues: bool = True
    test_redundancy_score: float = 0.0  # 0.0 = unique, 1.0 = completely redundant

    # Temporal metrics
    days_since_modification: int = 0
    related_source_modified: bool = False

    # Scores
    value_score: float = 0.0  # 0-100: higher is more valuable
    refactoring_complexity: float = 0.0  # 0-100: higher is more complex

    # Recommendation
    recommendation: str = ""  # "REFACTOR", "DEPRECATE", "KEEP"
    justification: str = ""


class TestHygienist:
    """Analyzes test suite for outdated tests and provides recommendations."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.src_dir = repo_root / "src"
        self.tests_dir = repo_root / "tests"
        self.output_dir = repo_root / "reports"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.test_metrics: Dict[str, TestMetrics] = {}
        self.source_modules: Set[str] = set()
        self.test_coverage_data: Dict[str, float] = {}

    def run_analysis(self) -> Dict[str, TestMetrics]:
        """Run complete hygienist analysis."""
        print("🔍 F.A.R.F.A.N Test Hygienist - Starting Analysis")
        print("=" * 80)

        # Step 1: Discover source modules
        print("\n[1/7] Discovering source modules...")
        self._discover_source_modules()
        print(f"   Found {len(self.source_modules)} source modules")

        # Step 2: Discover all test files
        print("\n[2/7] Discovering test files...")
        test_files = self._discover_test_files()
        print(f"   Found {len(test_files)} test files")

        # Step 3: Analyze imports
        print("\n[3/7] Analyzing imports...")
        for test_file in test_files:
            self._analyze_imports(test_file)

        # Step 4: Analyze code complexity
        print("\n[4/7] Analyzing code complexity...")
        for test_file in test_files:
            self._analyze_complexity(test_file)

        # Step 5: Analyze temporal metrics
        print("\n[5/7] Analyzing temporal metrics...")
        for test_file in test_files:
            self._analyze_temporal_metrics(test_file)

        # Step 6: Calculate value and complexity scores
        print("\n[6/7] Calculating value and complexity scores...")
        for test_name in self.test_metrics:
            self._calculate_scores(test_name)

        # Step 7: Generate recommendations
        print("\n[7/7] Generating recommendations...")
        for test_name in self.test_metrics:
            self._generate_recommendation(test_name)

        print("\n✅ Analysis complete!")
        return self.test_metrics

    def _discover_source_modules(self) -> None:
        """Discover all importable source modules."""
        for py_file in self.src_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue

            # Convert file path to module name
            rel_path = py_file.relative_to(self.src_dir)
            module_parts = list(rel_path.parts[:-1]) + [rel_path.stem]
            module_name = ".".join(module_parts)
            self.source_modules.add(module_name)

    def _discover_test_files(self) -> List[Path]:
        """Discover all test files."""
        test_files = []
        for pattern in ["test_*.py", "*_test.py"]:
            test_files.extend(self.tests_dir.rglob(pattern))
        return test_files

    def _analyze_imports(self, test_file: Path) -> None:
        """Analyze imports in a test file."""
        test_name = test_file.stem

        if test_name not in self.test_metrics:
            self.test_metrics[test_name] = TestMetrics(
                file_path=test_file,
                test_name=test_name
            )

        metrics = self.test_metrics[test_name]

        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content, filename=str(test_file))

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self._check_import(alias.name, metrics)

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self._check_import(node.module, metrics)

        except SyntaxError as e:
            metrics.imports_valid = False
            metrics.import_errors.append(f"Syntax error: {e}")
        except Exception as e:
            metrics.imports_valid = False
            metrics.import_errors.append(f"Parse error: {e}")

    def _check_import(self, module_name: str, metrics: TestMetrics) -> None:
        """Check if an import is valid."""
        # Check if it's a saaaaaa module
        if module_name.startswith("saaaaaa."):
            # Extract the part after "saaaaaa."
            module_path = module_name[8:]  # Remove "saaaaaa."

            # Check if this module exists
            if module_path not in self.source_modules:
                # Check if it's a package (directory with __init__.py)
                possible_path = self.src_dir / "saaaaaa" / module_path.replace(".", "/")
                if not (possible_path.exists() or (possible_path.parent / "__init__.py").exists()):
                    metrics.missing_imports.append(module_name)
                    metrics.imports_valid = False

    def _analyze_complexity(self, test_file: Path) -> None:
        """Analyze code complexity metrics."""
        test_name = test_file.stem
        metrics = self.test_metrics[test_name]

        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Count lines of code (excluding comments and blank lines)
            lines = [line.strip() for line in content.split('\n')]
            metrics.lines_of_code = len([l for l in lines if l and not l.startswith('#')])

            # Parse AST
            tree = ast.parse(content, filename=str(test_file))

            # Count test functions
            test_funcs = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if node.name.startswith('test_'):
                        test_funcs.append(node.name)
                        metrics.num_test_functions += 1

            # Calculate cyclomatic complexity (simplified)
            complexity = 1  # Base complexity
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                    complexity += 1
                elif isinstance(node, ast.BoolOp):
                    complexity += len(node.values) - 1

            metrics.cyclomatic_complexity = complexity

        except Exception as e:
            metrics.execution_errors.append(f"Complexity analysis error: {e}")

    def _analyze_temporal_metrics(self, test_file: Path) -> None:
        """Analyze temporal metrics (git history)."""
        test_name = test_file.stem
        metrics = self.test_metrics[test_name]

        try:
            # Get last modification date from git
            result = subprocess.run(
                ['git', 'log', '-1', '--format=%ct', '--', str(test_file)],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0 and result.stdout.strip():
                last_modified = int(result.stdout.strip())
                current_time = datetime.now().timestamp()
                metrics.days_since_modification = int((current_time - last_modified) / 86400)

            # Check if related source files were modified more recently
            # Extract potential source file references from test name
            source_hints = self._extract_source_hints(test_name)
            for hint in source_hints:
                source_files = list(self.src_dir.rglob(f"*{hint}*.py"))
                for source_file in source_files:
                    result = subprocess.run(
                        ['git', 'log', '-1', '--format=%ct', '--', str(source_file)],
                        cwd=self.repo_root,
                        capture_output=True,
                        text=True,
                        timeout=5
                    )

                    if result.returncode == 0 and result.stdout.strip():
                        source_modified = int(result.stdout.strip())
                        if source_modified > last_modified:
                            metrics.related_source_modified = True
                            break

        except Exception as e:
            # Git not available or other error - not critical
            pass

    def _extract_source_hints(self, test_name: str) -> List[str]:
        """Extract potential source file names from test name."""
        # Remove 'test_' prefix
        name = test_name.replace('test_', '')

        # Split by underscore and return non-trivial parts
        parts = [p for p in name.split('_') if len(p) > 3]
        return parts

    def _calculate_scores(self, test_name: str) -> None:
        """Calculate value and refactoring complexity scores."""
        metrics = self.test_metrics[test_name]

        # VALUE SCORE (0-100, higher is better)
        value_score = 0.0

        # Component 1: Import validity (20 points)
        if metrics.imports_valid:
            value_score += 20
        else:
            # Partial credit if some imports are valid
            if len(metrics.missing_imports) < 3:
                value_score += 10

        # Component 2: Test uniqueness (30 points)
        # Based on redundancy score (inverted)
        uniqueness = (1.0 - metrics.test_redundancy_score) * 30
        value_score += uniqueness

        # Component 3: Structural testing (25 points)
        # Tests with higher complexity likely test structural issues
        if metrics.cyclomatic_complexity > 5:
            value_score += 25
        elif metrics.cyclomatic_complexity > 2:
            value_score += 15
        else:
            value_score += 5

        # Component 4: Test coverage (15 points)
        value_score += metrics.coverage_percentage * 0.15

        # Component 5: Number of test cases (10 points)
        if metrics.num_test_functions >= 5:
            value_score += 10
        elif metrics.num_test_functions >= 3:
            value_score += 7
        elif metrics.num_test_functions >= 1:
            value_score += 3

        metrics.value_score = min(100, value_score)

        # REFACTORING COMPLEXITY SCORE (0-100, higher is more complex)
        complexity_score = 0.0

        # Component 1: Lines of code (30 points)
        if metrics.lines_of_code > 500:
            complexity_score += 30
        elif metrics.lines_of_code > 200:
            complexity_score += 20
        elif metrics.lines_of_code > 100:
            complexity_score += 10
        else:
            complexity_score += 5

        # Component 2: Cyclomatic complexity (25 points)
        complexity_score += min(25, metrics.cyclomatic_complexity * 2)

        # Component 3: Import errors (25 points)
        complexity_score += min(25, len(metrics.missing_imports) * 5)

        # Component 4: Number of test functions (10 points)
        complexity_score += min(10, metrics.num_test_functions * 2)

        # Component 5: Age (10 points) - older = potentially more complex to refactor
        if metrics.days_since_modification > 365:
            complexity_score += 10
        elif metrics.days_since_modification > 180:
            complexity_score += 7
        elif metrics.days_since_modification > 90:
            complexity_score += 4

        metrics.refactoring_complexity = min(100, complexity_score)

    def _generate_recommendation(self, test_name: str) -> None:
        """Generate recommendation: REFACTOR, DEPRECATE, or KEEP."""
        metrics = self.test_metrics[test_name]

        value = metrics.value_score
        complexity = metrics.refactoring_complexity

        # Decision matrix:
        # High value + Low complexity = KEEP (maintain as is)
        # High value + High complexity = REFACTOR (worth the effort)
        # Low value + Low complexity = REFACTOR (easy fix)
        # Low value + High complexity = DEPRECATE (not worth it)

        if value >= 60:
            if complexity <= 40:
                metrics.recommendation = "KEEP"
                metrics.justification = (
                    f"High value ({value:.1f}/100) with manageable complexity "
                    f"({complexity:.1f}/100). Test provides good coverage."
                )
            else:
                metrics.recommendation = "REFACTOR"
                metrics.justification = (
                    f"High value ({value:.1f}/100) justifies refactoring despite "
                    f"high complexity ({complexity:.1f}/100). Important test to preserve."
                )

        elif value >= 30:
            if complexity <= 50:
                metrics.recommendation = "REFACTOR"
                metrics.justification = (
                    f"Moderate value ({value:.1f}/100) with reasonable complexity "
                    f"({complexity:.1f}/100). Worth updating."
                )
            else:
                metrics.recommendation = "DEPRECATE"
                metrics.justification = (
                    f"Moderate value ({value:.1f}/100) doesn't justify high "
                    f"refactoring complexity ({complexity:.1f}/100). Consider deprecating."
                )

        else:  # value < 30
            if complexity <= 30:
                metrics.recommendation = "REFACTOR"
                metrics.justification = (
                    f"Low value ({value:.1f}/100) but very low complexity "
                    f"({complexity:.1f}/100). Easy to fix, might as well update."
                )
            else:
                metrics.recommendation = "DEPRECATE"
                metrics.justification = (
                    f"Low value ({value:.1f}/100) and high complexity "
                    f"({complexity:.1f}/100). Strong candidate for deprecation."
                )

        # Additional factors
        issues = []
        if not metrics.imports_valid:
            issues.append(f"{len(metrics.missing_imports)} missing imports")
        if metrics.related_source_modified:
            issues.append("related source code modified")
        if metrics.days_since_modification > 180:
            issues.append(f"{metrics.days_since_modification} days since last update")

        if issues:
            metrics.justification += f" Issues: {', '.join(issues)}."

    def generate_report(self) -> str:
        """Generate comprehensive analysis report."""
        lines = []
        lines.append("=" * 80)
        lines.append("F.A.R.F.A.N TEST HYGIENIST REPORT")
        lines.append("=" * 80)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Total tests analyzed: {len(self.test_metrics)}")
        lines.append("")

        # Summary statistics
        recommendations = defaultdict(int)
        for metrics in self.test_metrics.values():
            recommendations[metrics.recommendation] += 1

        lines.append("SUMMARY")
        lines.append("-" * 80)
        lines.append(f"KEEP:       {recommendations['KEEP']:3d} tests")
        lines.append(f"REFACTOR:   {recommendations['REFACTOR']:3d} tests")
        lines.append(f"DEPRECATE:  {recommendations['DEPRECATE']:3d} tests")
        lines.append("")

        # Group by recommendation
        for recommendation in ["DEPRECATE", "REFACTOR", "KEEP"]:
            tests = [m for m in self.test_metrics.values()
                    if m.recommendation == recommendation]

            if not tests:
                continue

            lines.append("")
            lines.append("=" * 80)
            lines.append(f"{recommendation}: {len(tests)} tests")
            lines.append("=" * 80)

            # Sort by value score (descending)
            tests.sort(key=lambda m: m.value_score, reverse=True)

            for metrics in tests:
                lines.append("")
                lines.append(f"Test: {metrics.test_name}")
                lines.append(f"  File: {metrics.file_path.relative_to(self.repo_root)}")
                lines.append(f"  Value Score: {metrics.value_score:.1f}/100")
                lines.append(f"  Refactoring Complexity: {metrics.refactoring_complexity:.1f}/100")
                lines.append(f"  Lines of Code: {metrics.lines_of_code}")
                lines.append(f"  Test Functions: {metrics.num_test_functions}")
                lines.append(f"  Cyclomatic Complexity: {metrics.cyclomatic_complexity}")
                lines.append(f"  Days Since Modified: {metrics.days_since_modification}")

                if metrics.missing_imports:
                    lines.append(f"  Missing Imports: {', '.join(metrics.missing_imports[:5])}")

                if metrics.import_errors:
                    lines.append(f"  Import Errors: {metrics.import_errors[0]}")

                lines.append(f"  Justification: {metrics.justification}")

        return "\n".join(lines)

    def save_json_report(self, output_path: Path) -> None:
        """Save detailed JSON report."""
        data = {
            "generated": datetime.now().isoformat(),
            "total_tests": len(self.test_metrics),
            "summary": {
                "keep": sum(1 for m in self.test_metrics.values() if m.recommendation == "KEEP"),
                "refactor": sum(1 for m in self.test_metrics.values() if m.recommendation == "REFACTOR"),
                "deprecate": sum(1 for m in self.test_metrics.values() if m.recommendation == "DEPRECATE"),
            },
            "tests": []
        }

        for metrics in sorted(self.test_metrics.values(),
                            key=lambda m: (m.recommendation, -m.value_score)):
            data["tests"].append({
                "name": metrics.test_name,
                "file": str(metrics.file_path.relative_to(self.repo_root)),
                "recommendation": metrics.recommendation,
                "value_score": round(metrics.value_score, 2),
                "refactoring_complexity": round(metrics.refactoring_complexity, 2),
                "metrics": {
                    "lines_of_code": metrics.lines_of_code,
                    "num_test_functions": metrics.num_test_functions,
                    "cyclomatic_complexity": metrics.cyclomatic_complexity,
                    "days_since_modification": metrics.days_since_modification,
                    "imports_valid": metrics.imports_valid,
                    "related_source_modified": metrics.related_source_modified,
                },
                "issues": {
                    "missing_imports": metrics.missing_imports,
                    "import_errors": metrics.import_errors,
                    "execution_errors": metrics.execution_errors,
                },
                "justification": metrics.justification,
            })

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)


def main() -> int:
    """Main entry point."""
    hygienist = TestHygienist(REPO_ROOT)

    # Run analysis
    hygienist.run_analysis()

    # Generate and save reports
    print("\n" + "=" * 80)
    print("Generating reports...")

    text_report = hygienist.generate_report()
    print(text_report)

    # Save reports
    text_report_path = hygienist.output_dir / "test_hygienist_report.txt"
    with open(text_report_path, 'w', encoding='utf-8') as f:
        f.write(text_report)
    print(f"\n📄 Text report saved to: {text_report_path}")

    json_report_path = hygienist.output_dir / "test_hygienist_report.json"
    hygienist.save_json_report(json_report_path)
    print(f"📄 JSON report saved to: {json_report_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
