#!/usr/bin/env python3
"""
Test Coverage Gap Analysis
===========================

Analyzes the current test suite to identify critical gaps that could
lead to major failures in production. Proposes new tests to cover these gaps.

Focus areas:
1. Integration between components
2. Error handling and edge cases
3. Performance and scalability
4. Data integrity and validation
5. Security and compliance
6. End-to-end workflows
"""

import ast
import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set

REPO_ROOT = Path(__file__).parent.parent
SRC_DIR = REPO_ROOT / "src" / "saaaaaa"
TESTS_DIR = REPO_ROOT / "tests"
OUTPUT_DIR = REPO_ROOT / "reports"


@dataclass
class CoverageGap:
    """Represents a gap in test coverage."""

    category: str  # Integration, Error Handling, Performance, etc.
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    component: str  # Which component/module is affected
    description: str
    potential_impact: str
    proposed_test: str
    proposed_test_file: str


class CoverageGapAnalyzer:
    """Analyzes test coverage gaps."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.src_dir = repo_root / "src" / "saaaaaa"
        self.tests_dir = repo_root / "tests"
        self.output_dir = repo_root / "reports"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.source_modules: Dict[str, Path] = {}
        self.tested_modules: Set[str] = set()
        self.coverage_gaps: List[CoverageGap] = []

    def run_analysis(self) -> List[CoverageGap]:
        """Run complete gap analysis."""
        print("🔍 Test Coverage Gap Analysis - Starting")
        print("=" * 80)

        # Step 1: Discover source modules
        print("\n[1/6] Discovering source modules...")
        self._discover_source_modules()
        print(f"   Found {len(self.source_modules)} source modules")

        # Step 2: Identify tested modules
        print("\n[2/6] Identifying tested modules...")
        self._identify_tested_modules()
        print(f"   Found {len(self.tested_modules)} tested modules")

        # Step 3: Find untested modules
        print("\n[3/6] Finding untested modules...")
        self._find_untested_modules()

        # Step 4: Analyze integration gaps
        print("\n[4/6] Analyzing integration gaps...")
        self._analyze_integration_gaps()

        # Step 5: Analyze error handling gaps
        print("\n[5/6] Analyzing error handling gaps...")
        self._analyze_error_handling_gaps()

        # Step 6: Analyze critical workflow gaps
        print("\n[6/6] Analyzing critical workflow gaps...")
        self._analyze_workflow_gaps()

        print(f"\n✅ Analysis complete! Found {len(self.coverage_gaps)} coverage gaps")
        return self.coverage_gaps

    def _discover_source_modules(self) -> None:
        """Discover all source modules."""
        for py_file in self.src_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue

            rel_path = py_file.relative_to(self.src_dir)
            module_parts = list(rel_path.parts[:-1]) + [rel_path.stem]
            module_name = ".".join(module_parts)
            self.source_modules[module_name] = py_file

    def _identify_tested_modules(self) -> None:
        """Identify which modules have tests."""
        for test_file in self.tests_dir.rglob("test_*.py"):
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content, filename=str(test_file))

                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module and node.module.startswith("saaaaaa."):
                            module_path = node.module[8:]  # Remove "saaaaaa."
                            self.tested_modules.add(module_path)

            except Exception:
                pass

    def _find_untested_modules(self) -> None:
        """Find modules without any tests."""
        untested = set(self.source_modules.keys()) - self.tested_modules

        # Categorize by importance
        critical_patterns = ["orchestrator", "core", "calibration", "processing"]
        high_priority_patterns = ["analysis", "validation", "contracts"]

        for module in sorted(untested):
            severity = "LOW"
            if any(p in module for p in critical_patterns):
                severity = "CRITICAL"
            elif any(p in module for p in high_priority_patterns):
                severity = "HIGH"
            else:
                severity = "MEDIUM"

            self.coverage_gaps.append(CoverageGap(
                category="UNTESTED_MODULE",
                severity=severity,
                component=module,
                description=f"Module '{module}' has no associated tests",
                potential_impact=f"Bugs in {module} may go undetected until production",
                proposed_test=f"test_{module.split('.')[-1]}",
                proposed_test_file=f"tests/test_{module.replace('.', '_')}.py"
            ))

    def _analyze_integration_gaps(self) -> None:
        """Analyze integration test gaps."""

        # Gap 1: Calibration system end-to-end
        self.coverage_gaps.append(CoverageGap(
            category="INTEGRATION",
            severity="CRITICAL",
            component="calibration",
            description="Missing end-to-end calibration system integration test",
            potential_impact="Calibration pipeline may fail when components are combined, " +
                            "causing incorrect policy analysis results",
            proposed_test="test_calibration_e2e_integration",
            proposed_test_file="tests/integration/test_calibration_e2e.py"
        ))

        # Gap 2: SPC to analysis bridge
        self.coverage_gaps.append(CoverageGap(
            category="INTEGRATION",
            severity="HIGH",
            component="spc_causal_bridge",
            description="Missing integration test for SPC to causal analysis workflow",
            potential_impact="Data may be lost or corrupted when transitioning from " +
                            "SPC ingestion to causal analysis",
            proposed_test="test_spc_to_analysis_integration",
            proposed_test_file="tests/integration/test_spc_analysis_bridge.py"
        ))

        # Gap 3: Multi-executor coordination
        self.coverage_gaps.append(CoverageGap(
            category="INTEGRATION",
            severity="CRITICAL",
            component="orchestrator",
            description="Missing stress test for concurrent multi-executor coordination",
            potential_impact="Race conditions or deadlocks may occur when multiple " +
                            "executors run in parallel, causing pipeline failures",
            proposed_test="test_concurrent_executor_coordination",
            proposed_test_file="tests/integration/test_executor_concurrency.py"
        ))

        # Gap 4: Provenance chain integrity
        self.coverage_gaps.append(CoverageGap(
            category="INTEGRATION",
            severity="CRITICAL",
            component="processing.cpp_ingestion",
            description="Missing end-to-end provenance chain validation",
            potential_impact="Provenance data may be corrupted across pipeline stages, " +
                            "violating audit trail requirements",
            proposed_test="test_provenance_chain_integrity_e2e",
            proposed_test_file="tests/integration/test_provenance_integrity.py"
        ))

    def _analyze_error_handling_gaps(self) -> None:
        """Analyze error handling and edge case gaps."""

        # Gap 1: Malformed PDF handling
        self.coverage_gaps.append(CoverageGap(
            category="ERROR_HANDLING",
            severity="HIGH",
            component="processing.document_ingestion",
            description="Missing tests for corrupted/malformed PDF handling",
            potential_impact="System may crash or produce incorrect results when processing " +
                            "malformed PDFs from municipalities",
            proposed_test="test_malformed_pdf_handling",
            proposed_test_file="tests/test_document_ingestion_errors.py"
        ))

        # Gap 2: Network failures in signal client
        self.coverage_gaps.append(CoverageGap(
            category="ERROR_HANDLING",
            severity="HIGH",
            component="core.orchestrator.signals",
            description="Missing tests for network timeout and retry logic",
            potential_impact="Signal client may fail silently or retry indefinitely, " +
                            "causing pipeline hangs",
            proposed_test="test_signal_client_network_failures",
            proposed_test_file="tests/test_signal_client_resilience.py"
        ))

        # Gap 3: Memory exhaustion scenarios
        self.coverage_gaps.append(CoverageGap(
            category="ERROR_HANDLING",
            severity="CRITICAL",
            component="processing",
            description="Missing tests for memory exhaustion with large documents",
            potential_impact="Pipeline may crash when processing very large development plans " +
                            "(>500 pages), losing all progress",
            proposed_test="test_large_document_memory_management",
            proposed_test_file="tests/test_memory_limits.py"
        ))

        # Gap 4: Invalid questionnaire schema
        self.coverage_gaps.append(CoverageGap(
            category="ERROR_HANDLING",
            severity="CRITICAL",
            component="core.orchestrator.questionnaire",
            description="Missing tests for malformed questionnaire JSON handling",
            potential_impact="Corrupted questionnaire file may cause pipeline to fail " +
                            "with unclear error messages",
            proposed_test="test_questionnaire_schema_validation",
            proposed_test_file="tests/test_questionnaire_error_handling.py"
        ))

    def _analyze_workflow_gaps(self) -> None:
        """Analyze critical workflow gaps."""

        # Gap 1: Complete pipeline with real data
        self.coverage_gaps.append(CoverageGap(
            category="E2E_WORKFLOW",
            severity="CRITICAL",
            component="full_pipeline",
            description="Missing end-to-end test with real municipal development plan",
            potential_impact="Pipeline may fail on real data despite passing synthetic tests, " +
                            "causing production failures",
            proposed_test="test_real_plan_e2e_execution",
            proposed_test_file="tests/integration/test_real_plan_e2e.py"
        ))

        # Gap 2: Multi-document batch processing
        self.coverage_gaps.append(CoverageGap(
            category="E2E_WORKFLOW",
            severity="HIGH",
            component="orchestrator",
            description="Missing test for batch processing multiple plans concurrently",
            potential_impact="Batch processing may cause resource contention or data corruption " +
                            "when analyzing multiple plans",
            proposed_test="test_batch_plan_processing",
            proposed_test_file="tests/integration/test_batch_processing.py"
        ))

        # Gap 3: Report generation completeness
        self.coverage_gaps.append(CoverageGap(
            category="E2E_WORKFLOW",
            severity="HIGH",
            component="analysis.report_assembly",
            description="Missing test for complete report generation from analysis results",
            potential_impact="Reports may be incomplete or malformed, missing critical policy " +
                            "recommendations",
            proposed_test="test_complete_report_assembly",
            proposed_test_file="tests/test_report_assembly_complete.py"
        ))

        # Gap 4: Determinism across environments
        self.coverage_gaps.append(CoverageGap(
            category="E2E_WORKFLOW",
            severity="CRITICAL",
            component="full_pipeline",
            description="Missing test for deterministic execution across different platforms",
            potential_impact="Analysis results may differ between development and production, " +
                            "violating reproducibility requirements",
            proposed_test="test_cross_platform_determinism",
            proposed_test_file="tests/test_platform_determinism.py"
        ))

        # Gap 5: Bayesian scoring edge cases
        self.coverage_gaps.append(CoverageGap(
            category="ERROR_HANDLING",
            severity="HIGH",
            component="analysis.bayesian_multilevel_system",
            description="Missing tests for edge cases in Bayesian scoring (zero evidence, " +
                       "conflicting evidence)",
            potential_impact="Bayesian scores may be NaN or Inf in edge cases, causing " +
                            "downstream failures",
            proposed_test="test_bayesian_scoring_edge_cases",
            proposed_test_file="tests/test_bayesian_edge_cases.py"
        ))

        # Gap 6: Circuit breaker state transitions
        self.coverage_gaps.append(CoverageGap(
            category="ERROR_HANDLING",
            severity="MEDIUM",
            component="infrastructure",
            description="Missing tests for circuit breaker state transition edge cases",
            potential_impact="Circuit breaker may get stuck in open state, preventing recovery " +
                            "from transient failures",
            proposed_test="test_circuit_breaker_state_transitions",
            proposed_test_file="tests/test_circuit_breaker_advanced.py"
        ))

    def generate_report(self) -> str:
        """Generate coverage gap report."""
        lines = []
        lines.append("=" * 80)
        lines.append("TEST COVERAGE GAP ANALYSIS REPORT")
        lines.append("=" * 80)
        lines.append("")

        # Summary by severity
        by_severity = defaultdict(list)
        for gap in self.coverage_gaps:
            by_severity[gap.severity].append(gap)

        lines.append("SUMMARY BY SEVERITY")
        lines.append("-" * 80)
        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            count = len(by_severity[severity])
            lines.append(f"{severity:12s}: {count:3d} gaps")
        lines.append("")

        # Summary by category
        by_category = defaultdict(list)
        for gap in self.coverage_gaps:
            by_category[gap.category].append(gap)

        lines.append("SUMMARY BY CATEGORY")
        lines.append("-" * 80)
        for category in sorted(by_category.keys()):
            count = len(by_category[category])
            lines.append(f"{category:20s}: {count:3d} gaps")
        lines.append("")

        # Detailed gaps
        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            gaps = by_severity[severity]
            if not gaps:
                continue

            lines.append("")
            lines.append("=" * 80)
            lines.append(f"{severity} PRIORITY GAPS: {len(gaps)}")
            lines.append("=" * 80)

            for gap in gaps:
                lines.append("")
                lines.append(f"[{gap.category}] {gap.component}")
                lines.append(f"  Description: {gap.description}")
                lines.append(f"  Potential Impact: {gap.potential_impact}")
                lines.append(f"  Proposed Test: {gap.proposed_test}")
                lines.append(f"  Test File: {gap.proposed_test_file}")

        return "\n".join(lines)

    def save_json_report(self, output_path: Path) -> None:
        """Save detailed JSON report."""
        data = {
            "summary": {
                "total_gaps": len(self.coverage_gaps),
                "by_severity": {
                    "critical": len([g for g in self.coverage_gaps if g.severity == "CRITICAL"]),
                    "high": len([g for g in self.coverage_gaps if g.severity == "HIGH"]),
                    "medium": len([g for g in self.coverage_gaps if g.severity == "MEDIUM"]),
                    "low": len([g for g in self.coverage_gaps if g.severity == "LOW"]),
                },
                "by_category": {}
            },
            "gaps": []
        }

        # Count by category
        by_category = defaultdict(int)
        for gap in self.coverage_gaps:
            by_category[gap.category] += 1
        data["summary"]["by_category"] = dict(by_category)

        # Add gaps
        for gap in self.coverage_gaps:
            data["gaps"].append({
                "category": gap.category,
                "severity": gap.severity,
                "component": gap.component,
                "description": gap.description,
                "potential_impact": gap.potential_impact,
                "proposed_test": gap.proposed_test,
                "proposed_test_file": gap.proposed_test_file,
            })

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)


def main() -> int:
    """Main entry point."""
    analyzer = CoverageGapAnalyzer(REPO_ROOT)

    # Run analysis
    analyzer.run_analysis()

    # Generate reports
    print("\n" + "=" * 80)
    print("Generating reports...")

    text_report = analyzer.generate_report()
    print(text_report)

    # Save reports
    text_report_path = analyzer.output_dir / "test_coverage_gaps.txt"
    with open(text_report_path, 'w', encoding='utf-8') as f:
        f.write(text_report)
    print(f"\n📄 Text report saved to: {text_report_path}")

    json_report_path = analyzer.output_dir / "test_coverage_gaps.json"
    analyzer.save_json_report(json_report_path)
    print(f"📄 JSON report saved to: {json_report_path}")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
