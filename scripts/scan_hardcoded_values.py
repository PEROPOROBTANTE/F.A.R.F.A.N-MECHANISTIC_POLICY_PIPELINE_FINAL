"""
FASE 5.1: Formal scan for ALL hardcoded calibration values.

This script performs a rigorous scan of the codebase to find:
- Type A: Scores (intrinsic quality values in [0.0, 1.0])
- Type B: Thresholds (validation cutoffs, typically >= comparisons)
- Type C: Weights (aggregation coefficients that sum to 1.0)
- Type D: Functional constants (technical constants, penalties, defaults)

Output: Complete catalog with file/line numbers for migration.
"""
import ast
import re
from pathlib import Path
from typing import List, Dict, Tuple, Set
import json


class HardcodedValueScanner(ast.NodeVisitor):
    """AST visitor to find hardcoded numeric literals in calibration context."""

    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.findings = []
        self.current_function = None
        self.current_class = None

    def visit_FunctionDef(self, node):
        """Track current function context."""
        old_func = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_func

    def visit_ClassDef(self, node):
        """Track current class context."""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_Num(self, node):
        """Visit numeric literal."""
        value = node.n

        # Only interested in float values in calibration range [0.0, 1.0]
        if isinstance(value, (int, float)):
            float_val = float(value)

            # Check if in calibration range
            if 0.0 <= float_val <= 1.0:
                self.findings.append({
                    "type": "numeric_literal",
                    "value": float_val,
                    "line": node.lineno,
                    "col": node.col_offset,
                    "context": self._get_context(),
                    "file": str(self.filepath)
                })

        self.generic_visit(node)

    def visit_Constant(self, node):
        """Visit constant (Python 3.8+)."""
        value = node.value

        if isinstance(value, (int, float)):
            float_val = float(value)

            if 0.0 <= float_val <= 1.0:
                self.findings.append({
                    "type": "constant",
                    "value": float_val,
                    "line": node.lineno,
                    "col": node.col_offset,
                    "context": self._get_context(),
                    "file": str(self.filepath)
                })

        self.generic_visit(node)

    def visit_Compare(self, node):
        """Visit comparison operators (to find thresholds)."""
        # Look for patterns like: score >= 0.7, value < 0.5, etc.
        for op, comparator in zip(node.ops, node.comparators):
            if isinstance(comparator, (ast.Num, ast.Constant)):
                value = comparator.n if isinstance(comparator, ast.Num) else comparator.value

                if isinstance(value, (int, float)):
                    float_val = float(value)

                    if 0.0 <= float_val <= 1.0:
                        op_name = op.__class__.__name__
                        self.findings.append({
                            "type": "comparison",
                            "operator": op_name,
                            "value": float_val,
                            "line": node.lineno,
                            "col": node.col_offset,
                            "context": self._get_context(),
                            "file": str(self.filepath)
                        })

        self.generic_visit(node)

    def visit_Assign(self, node):
        """Visit assignments (to find weight definitions)."""
        # Look for patterns like: w_theory = 0.4, threshold = 0.7
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id

                # Check if value is numeric
                if isinstance(node.value, (ast.Num, ast.Constant)):
                    value = node.value.n if isinstance(node.value, ast.Num) else node.value.value

                    if isinstance(value, (int, float)):
                        float_val = float(value)

                        if 0.0 <= float_val <= 1.0:
                            self.findings.append({
                                "type": "assignment",
                                "variable": var_name,
                                "value": float_val,
                                "line": node.lineno,
                                "col": node.col_offset,
                                "context": self._get_context(),
                                "file": str(self.filepath)
                            })

        self.generic_visit(node)

    def _get_context(self):
        """Get current code context."""
        parts = []
        if self.current_class:
            parts.append(self.current_class)
        if self.current_function:
            parts.append(self.current_function)
        return ".".join(parts) if parts else "module_level"


def scan_file(filepath: Path) -> List[Dict]:
    """Scan a single Python file for hardcoded values."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()

        tree = ast.parse(source, filename=str(filepath))
        scanner = HardcodedValueScanner(filepath)
        scanner.visit(tree)

        return scanner.findings

    except SyntaxError as e:
        print(f"  [WARN] Syntax error in {filepath}: {e}")
        return []
    except Exception as e:
        print(f"  [ERROR] Failed to scan {filepath}: {e}")
        return []


def scan_directory(directory: Path, patterns: List[str]) -> List[Dict]:
    """Scan all Python files in directory matching patterns."""
    all_findings = []

    for pattern in patterns:
        for filepath in directory.rglob(pattern):
            if filepath.is_file():
                print(f"Scanning: {filepath}")
                findings = scan_file(filepath)
                all_findings.extend(findings)

    return all_findings


def categorize_findings(findings: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Categorize findings into Type A, B, C, D.

    Type A: Scores - intrinsic quality values
    Type B: Thresholds - validation cutoffs
    Type C: Weights - aggregation coefficients
    Type D: Functional constants - technical constants
    """
    categories = {
        "Type_A_Scores": [],
        "Type_B_Thresholds": [],
        "Type_C_Weights": [],
        "Type_D_Constants": [],
        "Uncategorized": []
    }

    for finding in findings:
        value = finding["value"]
        var_name = finding.get("variable", "")
        file_path = finding.get("file", "")

        # Type C: Weights (w_theory, w_impl, w_deploy, etc.)
        if any(keyword in var_name.lower() for keyword in ["weight", "w_th", "w_imp", "w_dep", "w_"]):
            categories["Type_C_Weights"].append(finding)

        # Type B: Thresholds (threshold, cutoff, min_, max_)
        elif any(keyword in var_name.lower() for keyword in ["threshold", "cutoff", "min_", "max_"]):
            categories["Type_B_Thresholds"].append(finding)

        # Type B: Comparisons (likely thresholds)
        elif finding["type"] == "comparison":
            categories["Type_B_Thresholds"].append(finding)

        # Type A: Scores (b_theory, b_impl, b_deploy, score, quality)
        elif any(keyword in var_name.lower() for keyword in ["score", "b_theory", "b_impl", "b_deploy", "quality"]):
            categories["Type_A_Scores"].append(finding)

        # Type D: Penalties, defaults, technical constants
        elif any(keyword in var_name.lower() for keyword in ["penalty", "default", "epsilon", "tolerance"]):
            categories["Type_D_Constants"].append(finding)

        # Heuristic: Very specific values likely constants
        elif value in [0.0, 1.0, 0.5]:
            categories["Type_D_Constants"].append(finding)

        # Heuristic: Values close to 0.3-0.4 often weights
        elif 0.2 <= value <= 0.5 and "weight" not in var_name.lower():
            # Could be weight or threshold - need manual review
            categories["Uncategorized"].append(finding)

        else:
            categories["Uncategorized"].append(finding)

    return categories


def generate_report(categories: Dict[str, List[Dict]], output_path: Path):
    """Generate comprehensive migration report."""

    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("FASE 5.1: HARDCODED VALUES SCAN REPORT")
    report_lines.append("=" * 80)
    report_lines.append("")

    # Summary
    total = sum(len(findings) for findings in categories.values())
    report_lines.append(f"Total hardcoded values found: {total}")
    report_lines.append("")

    for category, findings in categories.items():
        report_lines.append(f"{category}: {len(findings)} occurrences")

    report_lines.append("")
    report_lines.append("=" * 80)
    report_lines.append("")

    # Detailed breakdown
    for category, findings in categories.items():
        if not findings:
            continue

        report_lines.append(f"\n{'=' * 80}")
        report_lines.append(f"{category}: {len(findings)} occurrences")
        report_lines.append(f"{'=' * 80}\n")

        # Group by file
        by_file = {}
        for finding in findings:
            file_path = finding["file"]
            if file_path not in by_file:
                by_file[file_path] = []
            by_file[file_path].append(finding)

        for file_path, file_findings in sorted(by_file.items()):
            report_lines.append(f"\nFile: {file_path}")
            report_lines.append("-" * 80)

            for f in sorted(file_findings, key=lambda x: x["line"]):
                line = f["line"]
                value = f["value"]
                var_name = f.get("variable", "N/A")
                context = f.get("context", "N/A")
                finding_type = f.get("type", "N/A")

                report_lines.append(f"  Line {line:4d}: {value:.6f}")
                report_lines.append(f"            Type: {finding_type}")
                report_lines.append(f"            Variable: {var_name}")
                report_lines.append(f"            Context: {context}")

                if finding_type == "comparison":
                    operator = f.get("operator", "N/A")
                    report_lines.append(f"            Operator: {operator}")

                report_lines.append("")

    # Write report
    report_text = "\n".join(report_lines)

    with open(output_path, 'w') as f:
        f.write(report_text)

    print(f"\nReport written to: {output_path}")

    # Also save JSON for programmatic access
    json_path = output_path.with_suffix('.json')
    with open(json_path, 'w') as f:
        json.dump(categories, f, indent=2)

    print(f"JSON data written to: {json_path}")

    return report_text


def main():
    """Main scan routine."""
    print("FASE 5.1: Scanning codebase for hardcoded calibration values...")
    print()

    # Directories to scan
    calibration_dir = Path("src/saaaaaa/core/calibration")
    executors_dir = Path("src/saaaaaa/core/orchestrator/executors")

    # Scan
    print("Scanning calibration module...")
    findings = []

    if calibration_dir.exists():
        findings.extend(scan_directory(calibration_dir, ["*.py"]))

    if executors_dir.exists():
        print("\nScanning executors module...")
        findings.extend(scan_directory(executors_dir, ["*.py"]))

    print(f"\nTotal raw findings: {len(findings)}")
    print()

    # Categorize
    print("Categorizing findings...")
    categories = categorize_findings(findings)

    # Generate report
    output_path = Path("docs/FASE_5_1_HARDCODED_SCAN_REPORT.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report = generate_report(categories, output_path)

    # Print summary to console
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    total = sum(len(findings) for findings in categories.values())
    print(f"Total hardcoded values: {total}")
    print()

    for category, findings in categories.items():
        print(f"  {category:25s}: {len(findings):3d}")

    print()
    print("Next step: Review report and proceed to FASE 5.2 (categorization)")
    print()


if __name__ == "__main__":
    main()
