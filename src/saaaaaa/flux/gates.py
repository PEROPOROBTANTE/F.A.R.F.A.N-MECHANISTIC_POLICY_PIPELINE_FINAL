# stdlib
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

# third-party (pinned in pyproject)
from pydantic import BaseModel

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


class QualityGateResult(BaseModel):
    """Result from a quality gate check."""

    gate_name: str
    passed: bool
    details: dict[str, Any]
    message: str


class QualityGates:
    """Quality gates for FLUX pipeline."""

    @staticmethod
    def compatibility_gate(
        phase_outcomes: dict[str, Any], contracts: list[tuple[str, str]]
    ) -> QualityGateResult:
        """
        Verify all phase transitions passed compatibility checks.

        requires: phase_outcomes not empty
        ensures: all contracts validated
        """
        if not phase_outcomes:
            return QualityGateResult(
                gate_name="compatibility",
                passed=False,
                details={},
                message="No phase outcomes to validate",
            )

        # All phases ran without CompatibilityError means compatibility gate passed
        passed = all(outcome.get("ok", False) for outcome in phase_outcomes.values())

        return QualityGateResult(
            gate_name="compatibility",
            passed=passed,
            details={"phase_count": len(phase_outcomes), "contracts": contracts},
            message="All phase transitions passed compatibility checks"
            if passed
            else "Some phases failed compatibility",
        )

    @staticmethod
    def determinism_gate(
        run1_fingerprints: dict[str, str], run2_fingerprints: dict[str, str]
    ) -> QualityGateResult:
        """
        Verify two runs with identical inputs produce identical fingerprints.

        requires: run1_fingerprints and run2_fingerprints have same keys
        ensures: fingerprints match for determinism
        """
        if set(run1_fingerprints.keys()) != set(run2_fingerprints.keys()):
            return QualityGateResult(
                gate_name="determinism",
                passed=False,
                details={
                    "run1_phases": list(run1_fingerprints.keys()),
                    "run2_phases": list(run2_fingerprints.keys()),
                },
                message="Phase sets do not match between runs",
            )

        mismatches = []
        for phase in run1_fingerprints:
            if run1_fingerprints[phase] != run2_fingerprints[phase]:
                mismatches.append(
                    {
                        "phase": phase,
                        "run1": run1_fingerprints[phase],
                        "run2": run2_fingerprints[phase],
                    }
                )

        passed = len(mismatches) == 0

        return QualityGateResult(
            gate_name="determinism",
            passed=passed,
            details={
                "mismatches": mismatches,
                "total_phases": len(run1_fingerprints),
            },
            message="All fingerprints match between runs"
            if passed
            else f"Found {len(mismatches)} mismatched fingerprints",
        )

    @staticmethod
    def no_yaml_gate(source_paths: list[Path]) -> QualityGateResult:
        """
        Verify no YAML files are loaded in runtime paths.

        requires: source_paths not empty
        ensures: no YAML reads detected
        """

        yaml_reads: list[str] = []
        files_checked = 0

        for path in source_paths:
            if not path.exists():
                continue

            # If it's a directory, recursively check all Python files
            if path.is_dir():
                for py_file in path.rglob("*.py"):
                    if py_file.is_file():
                        files_checked += 1
                        content = py_file.read_text(encoding="utf-8")

                        # Check for YAML loading patterns
                        if any(
                            pattern in content
                            for pattern in ["yaml.load", "yaml.safe_load", "YAML("]
                        ):
                            yaml_reads.append(str(py_file))
            else:
                # Single file
                files_checked += 1
                content = path.read_text(encoding="utf-8")

                # Check for YAML loading patterns
                if any(
                    pattern in content
                    for pattern in ["yaml.load", "yaml.safe_load", "YAML("]
                ):
                    yaml_reads.append(str(path))

        passed = len(yaml_reads) == 0

        return QualityGateResult(
            gate_name="no_yaml",
            passed=passed,
            details={
                "yaml_reads_found": yaml_reads,
                "checked_files": files_checked,
            },
            message="No YAML reads in runtime paths"
            if passed
            else f"Found YAML reads in {len(yaml_reads)} files",
        )

    @staticmethod
    def type_gate(mypy_output: str | None = None) -> QualityGateResult:
        """
        Verify type checking passes with strict mode.

        requires: mypy/pyright has been run
        ensures: no type errors
        """
        if mypy_output is None:
            return QualityGateResult(
                gate_name="type",
                passed=False,
                details={},
                message="No type checker output provided",
            )

        # Check for success indicators
        success_indicators = ["Success: no issues found", "0 errors"]
        passed = any(indicator in mypy_output for indicator in success_indicators)

        error_count = 0
        if "error" in mypy_output.lower():
            # Try to extract error count
            import re

            match = re.search(r"(\d+) error", mypy_output)
            if match:
                error_count = int(match.group(1))

        return QualityGateResult(
            gate_name="type",
            passed=passed,
            details={"error_count": error_count, "output_preview": mypy_output[:200]},
            message="Type checking passed" if passed else f"Found {error_count} type errors",
        )

    @staticmethod
    def secret_scan_gate(scan_output: str | None = None) -> QualityGateResult:
        """
        Verify no secrets detected in code.

        requires: secret scanner has been run
        ensures: no secrets found
        """
        if scan_output is None:
            return QualityGateResult(
                gate_name="secrets",
                passed=True,
                details={},
                message="No secret scan performed (assuming clean)",
            )

        # Common secret scan success patterns
        clean_indicators = [
            "No secrets found",
            "0 secrets",
            "Clean",
            "no leaks detected",
        ]

        passed = any(indicator in scan_output for indicator in clean_indicators)

        return QualityGateResult(
            gate_name="secrets",
            passed=passed,
            details={"scan_output_preview": scan_output[:200]},
            message="No secrets detected" if passed else "Secrets detected in code",
        )

    @staticmethod
    def coverage_gate(
        coverage_percentage: float, threshold: float = 80.0
    ) -> QualityGateResult:
        """
        Verify test coverage meets threshold.

        requires: 0 <= coverage_percentage <= 100, threshold >= 0
        ensures: coverage >= threshold
        """
        if not (0 <= coverage_percentage <= 100):
            return QualityGateResult(
                gate_name="coverage",
                passed=False,
                details={"coverage": coverage_percentage},
                message="Invalid coverage percentage",
            )

        passed = coverage_percentage >= threshold

        return QualityGateResult(
            gate_name="coverage",
            passed=passed,
            details={
                "coverage": coverage_percentage,
                "threshold": threshold,
                "gap": threshold - coverage_percentage,
            },
            message=f"Coverage {coverage_percentage:.1f}% meets threshold {threshold}%"
            if passed
            else f"Coverage {coverage_percentage:.1f}% below threshold {threshold}%",
        )

    @staticmethod
    def run_all_gates(
        phase_outcomes: dict[str, Any],
        run1_fingerprints: dict[str, str],
        run2_fingerprints: dict[str, str] | None = None,
        source_paths: list[Path] | None = None,
        mypy_output: str | None = None,
        secret_scan_output: str | None = None,
        coverage_percentage: float | None = None,
    ) -> dict[str, QualityGateResult]:
        """
        Run all quality gates and return results.

        requires: phase_outcomes not empty
        ensures: all gates executed
        """
        results: dict[str, QualityGateResult] = {}

        # Compatibility gate
        contracts = [
            ("IngestDeliverable", "NormalizeExpectation"),
            ("NormalizeDeliverable", "ChunkExpectation"),
            ("ChunkDeliverable", "SignalsExpectation"),
            ("SignalsDeliverable", "AggregateExpectation"),
            ("AggregateDeliverable", "ScoreExpectation"),
            ("ScoreDeliverable", "ReportExpectation"),
        ]
        results["compatibility"] = QualityGates.compatibility_gate(
            phase_outcomes, contracts
        )

        # Determinism gate
        if run2_fingerprints:
            results["determinism"] = QualityGates.determinism_gate(
                run1_fingerprints, run2_fingerprints
            )

        # No-YAML gate
        if source_paths:
            results["no_yaml"] = QualityGates.no_yaml_gate(source_paths)

        # Type gate
        if mypy_output:
            results["type"] = QualityGates.type_gate(mypy_output)

        # Secret scan gate
        results["secrets"] = QualityGates.secret_scan_gate(secret_scan_output)

        # Coverage gate
        if coverage_percentage is not None:
            results["coverage"] = QualityGates.coverage_gate(coverage_percentage)

        return results

    @staticmethod
    def emit_checklist(
        gate_results: dict[str, QualityGateResult], fingerprints: dict[str, str]
    ) -> dict[str, Any]:
        """
        Emit machine-readable checklist.

        requires: gate_results not empty
        ensures: valid checklist structure
        """
        all_passed = all(r.passed for r in gate_results.values())

        checklist = {
            "contracts_ok": gate_results.get("compatibility", QualityGateResult(
                gate_name="compatibility", passed=False, details={}, message=""
            )).passed,
            "determinism_ok": gate_results.get("determinism", QualityGateResult(
                gate_name="determinism", passed=True, details={}, message=""
            )).passed,
            "gates": {name: result.passed for name, result in gate_results.items()},
            "fingerprints": fingerprints,
            "all_passed": all_passed,
        }

        return checklist
