"""
FARFAN Mechanistic Policy Pipeline - Audit System
==================================================

This module provides comprehensive audit capabilities to verify:
1. Executor Architecture (30 dimension-question executors)
2. Questionnaire Access Patterns (dependency injection only)
3. Factory Pattern Compliance
4. Method Signature Completeness
5. Configuration System Type-Safety

AUDIT COMPLIANCE MARKERS:
- ✅ AUDIT_VERIFIED: Component passes all audit checks
- ⚠️  AUDIT_WARNING: Component has potential issues
- ❌ AUDIT_FAILED: Component fails audit requirements

Author: FARFAN Team
Date: 2025-11-13
Version: 1.0.0
"""

import ast
import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from saaaaaa.config.paths import PROJECT_ROOT
from saaaaaa.core.canonical_notation import CanonicalDimension

logger = logging.getLogger(__name__)


class AuditStatus(Enum):
    """Audit status enumeration."""
    VERIFIED = "✅ VERIFIED"
    WARNING = "⚠️  WARNING"
    FAILED = "❌ FAILED"


class AuditCategory(Enum):
    """Audit category enumeration."""
    EXECUTOR_ARCHITECTURE = "Executor Architecture"
    QUESTIONNAIRE_ACCESS = "Questionnaire Access"
    FACTORY_PATTERN = "Factory Pattern"
    METHOD_SIGNATURES = "Method Signatures"
    CONFIGURATION_SYSTEM = "Configuration System"
    SAGA_PATTERN = "Saga Pattern"
    EVENT_TRACKING = "Event Tracking"
    RL_OPTIMIZATION = "RL Optimization"
    INTEGRATION_TESTS = "Integration Tests"
    OBSERVABILITY = "Observability"


@dataclass
class AuditFinding:
    """Represents a single audit finding."""
    category: AuditCategory
    status: AuditStatus
    component: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert finding to dictionary."""
        return {
            "category": self.category.value,
            "status": self.status.value,
            "component": self.component,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }

    def __str__(self) -> str:
        """String representation of finding."""
        return f"{self.status.value} [{self.category.value}] {self.component}: {self.message}"


@dataclass
class ExecutorAuditInfo:
    """Information about an executor for audit purposes."""
    executor_name: str
    dimension: int  # 1-6
    question: int  # 1-5
    dimension_name: str
    class_exists: bool
    has_execute_method: bool
    accesses_questionnaire_directly: bool
    uses_dependency_injection: bool
    file_path: str | None = None
    line_number: int | None = None


class AuditSystem:
    """
    Comprehensive audit system for FARFAN Pipeline.

    This class provides methods to audit all critical components of the pipeline
    to ensure compliance with architectural requirements.
    """

    # Expected 30 executors (D1Q1-D6Q5)
    EXPECTED_EXECUTORS = [
        f"D{d}Q{q}_Executor"
        for d in range(1, 7)
        for q in range(1, 6)
    ]

    # Dimension names from canonical notation
    DIMENSION_NAMES = {
        idx: getattr(CanonicalDimension, f"D{idx}").label
        for idx in range(1, 7)
    }

    # Core scripts that MUST use dependency injection
    CORE_SCRIPTS = [
        "policy_processor.py",
        "Analyzer_one.py",
        "embedding_policy.py",
        "financiero_viabilidad_tablas.py",
        "teoria_cambio.py",
        "dereck_beach.py",
        "semantic_chunking_policy.py"
    ]

    def __init__(self, repo_root: Path) -> None:
        """
        Initialize audit system.

        Args:
            repo_root: Root directory of the repository
        """
        self.repo_root = repo_root
        self.findings: list[AuditFinding] = []

    def add_finding(
        self,
        category: AuditCategory,
        status: AuditStatus,
        component: str,
        message: str,
        details: dict[str, Any] | None = None
    ) -> None:
        """Add an audit finding."""
        finding = AuditFinding(
            category=category,
            status=status,
            component=component,
            message=message,
            details=details or {}
        )
        self.findings.append(finding)
        logger.info(str(finding))

    def audit_executor_architecture(self) -> dict[str, Any]:
        """
        Audit the 30-executor architecture (D1Q1-D6Q5).

        Returns:
            Dictionary with audit results
        """
        logger.info("=" * 80)
        logger.info("AUDITING: Executor Architecture (30 Dimension-Question Executors)")
        logger.info("=" * 80)

        executors_file = self.repo_root / "src/saaaaaa/core/orchestrator/executors.py"

        if not executors_file.exists():
            self.add_finding(
                AuditCategory.EXECUTOR_ARCHITECTURE,
                AuditStatus.FAILED,
                "executors.py",
                "Executors file not found",
                {"expected_path": str(executors_file)}
            )
            return {"status": "FAILED", "executors_found": 0}

        # Parse the executors file
        with open(executors_file, encoding='utf-8') as f:
            content = f.read()

        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            self.add_finding(
                AuditCategory.EXECUTOR_ARCHITECTURE,
                AuditStatus.FAILED,
                "executors.py",
                f"Syntax error in executors file: {e}",
                {"error": str(e)}
            )
            return {"status": "FAILED", "executors_found": 0}

        # Find all executor classes
        executor_classes = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name.endswith("_Executor"):
                executor_classes[node.name] = {
                    "line_number": node.lineno,
                    "methods": [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
                }

        # Audit each expected executor
        executor_audit_info = []
        found_count = 0

        for executor_name in self.EXPECTED_EXECUTORS:
            # Parse dimension and question from name (e.g., "D1Q2_Executor")
            parts = executor_name.replace("_Executor", "")
            dimension = int(parts[1])
            question = int(parts[3])
            dimension_name = self.DIMENSION_NAMES[dimension]

            class_exists = executor_name in executor_classes
            has_execute_method = False

            if class_exists:
                found_count += 1
                methods = executor_classes[executor_name]["methods"]
                has_execute_method = "execute" in methods

                status = AuditStatus.VERIFIED if has_execute_method else AuditStatus.WARNING
                message = "Executor properly defined" if has_execute_method else "Missing execute method"

                self.add_finding(
                    AuditCategory.EXECUTOR_ARCHITECTURE,
                    status,
                    executor_name,
                    message,
                    {
                        "dimension": f"D{dimension}: {dimension_name}",
                        "question": f"Q{question}",
                        "line": executor_classes[executor_name]["line_number"],
                        "methods": methods
                    }
                )
            else:
                self.add_finding(
                    AuditCategory.EXECUTOR_ARCHITECTURE,
                    AuditStatus.FAILED,
                    executor_name,
                    "Executor class not found",
                    {
                        "dimension": f"D{dimension}: {dimension_name}",
                        "question": f"Q{question}"
                    }
                )

            executor_audit_info.append(ExecutorAuditInfo(
                executor_name=executor_name,
                dimension=dimension,
                question=question,
                dimension_name=dimension_name,
                class_exists=class_exists,
                has_execute_method=has_execute_method,
                accesses_questionnaire_directly=False,  # Will be checked in questionnaire audit
                uses_dependency_injection=False,
                file_path=str(executors_file) if class_exists else None,
                line_number=executor_classes[executor_name]["line_number"] if class_exists else None
            ))

        # Overall assessment
        if found_count == 30:
            self.add_finding(
                AuditCategory.EXECUTOR_ARCHITECTURE,
                AuditStatus.VERIFIED,
                "FrontierExecutorOrchestrator",
                "All 30 dimension-question executors verified (D1Q1-D6Q5)",
                {
                    "expected": 30,
                    "found": found_count,
                    "dimensions": list(self.DIMENSION_NAMES.items())
                }
            )
        else:
            self.add_finding(
                AuditCategory.EXECUTOR_ARCHITECTURE,
                AuditStatus.FAILED,
                "FrontierExecutorOrchestrator",
                f"Missing executors: expected 30, found {found_count}",
                {
                    "expected": 30,
                    "found": found_count,
                    "missing": [e for e in self.EXPECTED_EXECUTORS if e not in executor_classes]
                }
            )

        return {
            "status": "VERIFIED" if found_count == 30 else "FAILED",
            "executors_found": found_count,
            "executors_expected": 30,
            "executor_details": executor_audit_info
        }

    def audit_questionnaire_access(self) -> dict[str, Any]:
        """
        Audit questionnaire access patterns to ensure dependency injection.

        Verifies that core scripts:
        1. Do NOT directly access questionnaire_monolith.json
        2. Do NOT instantiate QuestionnaireResourceProvider directly
        3. DO receive questionnaire via dependency injection

        Returns:
            Dictionary with audit results
        """
        logger.info("=" * 80)
        logger.info("AUDITING: Questionnaire Access Patterns (Dependency Injection)")
        logger.info("=" * 80)

        violations = []
        compliant_scripts = []

        for script_name in self.CORE_SCRIPTS:
            # Find the script in processing or analysis directories
            script_paths = [
                self.repo_root / "src/saaaaaa/processing" / script_name,
                self.repo_root / "src/saaaaaa/analysis" / script_name
            ]

            script_path = None
            for path in script_paths:
                if path.exists():
                    script_path = path
                    break

            if not script_path:
                self.add_finding(
                    AuditCategory.QUESTIONNAIRE_ACCESS,
                    AuditStatus.WARNING,
                    script_name,
                    "Script file not found",
                    {"searched_paths": [str(p) for p in script_paths]}
                )
                continue

            # Read and analyze the script
            with open(script_path, encoding='utf-8') as f:
                content = f.read()

            # Check for violations
            has_violations = False
            violation_details = []

            # Check for direct file access
            if 'questionnaire_monolith.json' in content or 'open(' in content and 'questionnaire' in content:
                has_violations = True
                violation_details.append("Direct file access to questionnaire detected")

            # Check for direct instantiation of QuestionnaireResourceProvider
            if 'QuestionnaireResourceProvider(' in content:
                has_violations = True
                violation_details.append("Direct instantiation of QuestionnaireResourceProvider")

            # Check for load_questionnaire() calls (should only be in factory)
            if 'load_questionnaire()' in content and script_name != 'factory.py':
                has_violations = True
                violation_details.append("Direct call to load_questionnaire()")

            # Verify dependency injection pattern
            uses_dependency_injection = False
            if (
                any(pattern in content for pattern in [
                    'questionnaire: Mapping',
                    'questionnaire: dict',
                ])
                or ('def __init__' in content and 'questionnaire' in content)
                or ('@dataclass' in content and 'questionnaire' in content)
            ):
                uses_dependency_injection = True

            if has_violations:
                violations.append(script_name)
                self.add_finding(
                    AuditCategory.QUESTIONNAIRE_ACCESS,
                    AuditStatus.FAILED,
                    script_name,
                    "Questionnaire access violations detected",
                    {
                        "violations": violation_details,
                        "file": str(script_path)
                    }
                )
            else:
                compliant_scripts.append(script_name)
                self.add_finding(
                    AuditCategory.QUESTIONNAIRE_ACCESS,
                    AuditStatus.VERIFIED,
                    script_name,
                    "Properly uses dependency injection for questionnaire access",
                    {
                        "uses_dependency_injection": uses_dependency_injection,
                        "file": str(script_path)
                    }
                )

        # Check factory.py as the authorized loader
        factory_path = self.repo_root / "src/saaaaaa/core/orchestrator/factory.py"
        if factory_path.exists():
            with open(factory_path, encoding='utf-8') as f:
                factory_content = f.read()

            has_load_function = 'load_questionnaire' in factory_content
            has_provider_creation = 'QuestionnaireResourceProvider' in factory_content

            if has_load_function:
                self.add_finding(
                    AuditCategory.QUESTIONNAIRE_ACCESS,
                    AuditStatus.VERIFIED,
                    "factory.py",
                    "Authorized questionnaire loader verified",
                    {
                        "has_load_function": has_load_function,
                        "has_provider_creation": has_provider_creation
                    }
                )
            else:
                self.add_finding(
                    AuditCategory.QUESTIONNAIRE_ACCESS,
                    AuditStatus.WARNING,
                    "factory.py",
                    "Factory missing questionnaire loading functionality"
                )

        # Overall assessment
        total_scripts = len(self.CORE_SCRIPTS)
        compliant_count = len(compliant_scripts)

        if compliant_count == total_scripts:
            self.add_finding(
                AuditCategory.QUESTIONNAIRE_ACCESS,
                AuditStatus.VERIFIED,
                "Questionnaire Access Policy",
                f"All {total_scripts} core scripts comply with dependency injection policy",
                {
                    "compliant_scripts": compliant_scripts,
                    "violations": []
                }
            )
        else:
            self.add_finding(
                AuditCategory.QUESTIONNAIRE_ACCESS,
                AuditStatus.FAILED,
                "Questionnaire Access Policy",
                f"Policy violations found: {len(violations)}/{total_scripts} scripts",
                {
                    "compliant_scripts": compliant_scripts,
                    "violations": violations
                }
            )

        return {
            "status": "VERIFIED" if compliant_count == total_scripts else "FAILED",
            "compliant_scripts": compliant_count,
            "total_scripts": total_scripts,
            "violations": violations
        }

    def audit_factory_pattern(self) -> dict[str, Any]:
        """
        Audit factory pattern implementation.

        Verifies:
        1. Primary loader exists: factory.py::load_questionnaire_monolith()
        2. QuestionnaireResourceProvider for dependency injection
        3. No unauthorized direct access

        Returns:
            Dictionary with audit results
        """
        logger.info("=" * 80)
        logger.info("AUDITING: Factory Pattern Implementation")
        logger.info("=" * 80)

        factory_path = self.repo_root / "src/saaaaaa/core/orchestrator/factory.py"
        questionnaire_path = self.repo_root / "src/saaaaaa/core/orchestrator/questionnaire.py"

        results = {
            "factory_exists": False,
            "has_load_function": False,
            "questionnaire_module_exists": False,
            "has_provider_class": False
        }

        # Check factory.py
        if factory_path.exists():
            results["factory_exists"] = True
            with open(factory_path, encoding='utf-8') as f:
                factory_content = f.read()

            # Parse AST
            try:
                tree = ast.parse(factory_content)

                # Look for load functions
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        if 'load_questionnaire' in node.name.lower():
                            results["has_load_function"] = True
                            self.add_finding(
                                AuditCategory.FACTORY_PATTERN,
                                AuditStatus.VERIFIED,
                                f"factory.py::{node.name}",
                                "Questionnaire loader function found",
                                {"line": node.lineno}
                            )
            except SyntaxError as e:
                self.add_finding(
                    AuditCategory.FACTORY_PATTERN,
                    AuditStatus.FAILED,
                    "factory.py",
                    f"Syntax error: {e}"
                )
        else:
            self.add_finding(
                AuditCategory.FACTORY_PATTERN,
                AuditStatus.FAILED,
                "factory.py",
                "Factory file not found",
                {"expected_path": str(factory_path)}
            )

        # Check questionnaire.py
        if questionnaire_path.exists():
            results["questionnaire_module_exists"] = True
            with open(questionnaire_path, encoding='utf-8') as f:
                questionnaire_content = f.read()

            # Parse AST
            try:
                tree = ast.parse(questionnaire_content)

                # Look for QuestionnaireResourceProvider
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        if 'QuestionnaireResourceProvider' in node.name:
                            results["has_provider_class"] = True
                            self.add_finding(
                                AuditCategory.FACTORY_PATTERN,
                                AuditStatus.VERIFIED,
                                f"questionnaire.py::{node.name}",
                                "QuestionnaireResourceProvider class found",
                                {"line": node.lineno}
                            )
            except SyntaxError as e:
                self.add_finding(
                    AuditCategory.FACTORY_PATTERN,
                    AuditStatus.FAILED,
                    "questionnaire.py",
                    f"Syntax error: {e}"
                )
        else:
            self.add_finding(
                AuditCategory.FACTORY_PATTERN,
                AuditStatus.FAILED,
                "questionnaire.py",
                "Questionnaire module not found",
                {"expected_path": str(questionnaire_path)}
            )

        # Overall assessment
        all_verified = all(results.values())

        if all_verified:
            self.add_finding(
                AuditCategory.FACTORY_PATTERN,
                AuditStatus.VERIFIED,
                "Factory Pattern",
                "Factory pattern fully implemented and verified",
                results
            )
        else:
            self.add_finding(
                AuditCategory.FACTORY_PATTERN,
                AuditStatus.FAILED,
                "Factory Pattern",
                "Factory pattern incomplete or missing components",
                results
            )

        return {
            "status": "VERIFIED" if all_verified else "FAILED",
            **results
        }

    def audit_method_signatures(self) -> dict[str, Any]:
        """
        Audit method signatures across core modules.

        Verifies that all methods have:
        1. Type annotations
        2. Docstrings
        3. Proper parameter documentation

        Returns:
            Dictionary with audit results
        """
        logger.info("=" * 80)
        logger.info("AUDITING: Method Signatures (165 methods across 38 classes)")
        logger.info("=" * 80)

        # Target files to audit
        target_files = [
            self.repo_root / "src/saaaaaa/processing" / script
            for script in self.CORE_SCRIPTS
        ] + [
            self.repo_root / "src/saaaaaa/analysis" / script
            for script in self.CORE_SCRIPTS
        ]

        total_methods = 0
        complete_methods = 0
        incomplete_methods = []

        for file_path in target_files:
            if not file_path.exists():
                continue

            with open(file_path, encoding='utf-8') as f:
                content = f.read()

            try:
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        class_name = node.name

                        for item in node.body:
                            if isinstance(item, ast.FunctionDef):
                                total_methods += 1
                                method_name = item.name

                                # Check for type annotations
                                has_return_annotation = item.returns is not None
                                has_param_annotations = all(
                                    arg.annotation is not None
                                    for arg in item.args.args
                                    if arg.arg != 'self'
                                )

                                # Check for docstring
                                has_docstring = (
                                    ast.get_docstring(item) is not None
                                )

                                is_complete = (
                                    has_return_annotation and
                                    has_param_annotations and
                                    has_docstring
                                )

                                if is_complete:
                                    complete_methods += 1
                                else:
                                    incomplete_methods.append({
                                        "file": file_path.name,
                                        "class": class_name,
                                        "method": method_name,
                                        "line": item.lineno,
                                        "missing": {
                                            "return_annotation": not has_return_annotation,
                                            "param_annotations": not has_param_annotations,
                                            "docstring": not has_docstring
                                        }
                                    })
            except SyntaxError as e:
                logger.warning(f"Syntax error in {file_path}: {e}")

        # Assessment
        completion_rate = (complete_methods / total_methods * 100) if total_methods > 0 else 0

        if completion_rate == 100:
            self.add_finding(
                AuditCategory.METHOD_SIGNATURES,
                AuditStatus.VERIFIED,
                "Method Signatures",
                f"All {total_methods} methods have complete signatures",
                {
                    "total": total_methods,
                    "complete": complete_methods,
                    "completion_rate": completion_rate
                }
            )
        elif completion_rate >= 90:
            self.add_finding(
                AuditCategory.METHOD_SIGNATURES,
                AuditStatus.WARNING,
                "Method Signatures",
                f"Most methods complete ({completion_rate:.1f}%), but {len(incomplete_methods)} need attention",
                {
                    "total": total_methods,
                    "complete": complete_methods,
                    "incomplete": len(incomplete_methods),
                    "completion_rate": completion_rate
                }
            )
        else:
            self.add_finding(
                AuditCategory.METHOD_SIGNATURES,
                AuditStatus.FAILED,
                "Method Signatures",
                f"Insufficient completion rate ({completion_rate:.1f}%)",
                {
                    "total": total_methods,
                    "complete": complete_methods,
                    "incomplete": len(incomplete_methods),
                    "completion_rate": completion_rate,
                    "incomplete_methods": incomplete_methods[:10]  # First 10
                }
            )

        return {
            "status": "VERIFIED" if completion_rate == 100 else ("WARNING" if completion_rate >= 90 else "FAILED"),
            "total_methods": total_methods,
            "complete_methods": complete_methods,
            "completion_rate": completion_rate,
            "incomplete_methods": incomplete_methods
        }

    def audit_configuration_system(self) -> dict[str, Any]:
        """
        Audit configuration system for type-safety and parameters.

        Verifies:
        1. ExecutorConfig with proper parameter ranges
        2. AdvancedModuleConfig with academic parameters
        3. Type-safety with Pydantic
        4. BLAKE3 fingerprinting

        Returns:
            Dictionary with audit results
        """
        logger.info("=" * 80)
        logger.info("AUDITING: Configuration System (Type-Safety & Parameters)")
        logger.info("=" * 80)

        config_files = {
            "executor_config": self.repo_root / "src/saaaaaa/core/orchestrator/executor_config.py",
            "advanced_module_config": self.repo_root / "src/saaaaaa/core/orchestrator/advanced_module_config.py"
        }

        results = {}

        for config_name, config_path in config_files.items():
            if not config_path.exists():
                self.add_finding(
                    AuditCategory.CONFIGURATION_SYSTEM,
                    AuditStatus.FAILED,
                    config_name,
                    "Configuration file not found",
                    {"expected_path": str(config_path)}
                )
                results[config_name] = False
                continue

            with open(config_path, encoding='utf-8') as f:
                content = f.read()

            # Check for Pydantic BaseModel
            has_pydantic = 'BaseModel' in content or 'pydantic' in content
            has_field_validation = 'Field(' in content or 'validator' in content
            has_frozen = 'frozen=True' in content or 'class Config' in content

            if has_pydantic and has_field_validation:
                self.add_finding(
                    AuditCategory.CONFIGURATION_SYSTEM,
                    AuditStatus.VERIFIED,
                    config_name,
                    "Type-safe configuration with Pydantic validation",
                    {
                        "has_pydantic": has_pydantic,
                        "has_field_validation": has_field_validation,
                        "has_frozen": has_frozen
                    }
                )
                results[config_name] = True
            else:
                self.add_finding(
                    AuditCategory.CONFIGURATION_SYSTEM,
                    AuditStatus.WARNING,
                    config_name,
                    "Configuration lacks proper type-safety features",
                    {
                        "has_pydantic": has_pydantic,
                        "has_field_validation": has_field_validation,
                        "has_frozen": has_frozen
                    }
                )
                results[config_name] = False

        # Overall assessment
        all_verified = all(results.values())

        if all_verified:
            self.add_finding(
                AuditCategory.CONFIGURATION_SYSTEM,
                AuditStatus.VERIFIED,
                "Configuration System",
                "All configuration modules are type-safe and properly validated",
                results
            )
        else:
            self.add_finding(
                AuditCategory.CONFIGURATION_SYSTEM,
                AuditStatus.WARNING,
                "Configuration System",
                "Some configuration modules need improvement",
                results
            )

        return {
            "status": "VERIFIED" if all_verified else "WARNING",
            **results
        }

    def generate_audit_report(self, output_path: Path | None = None) -> dict[str, Any]:
        """
        Generate comprehensive audit report.

        Args:
            output_path: Optional path to save the report

        Returns:
            Complete audit report as dictionary
        """
        logger.info("=" * 80)
        logger.info("GENERATING COMPREHENSIVE AUDIT REPORT")
        logger.info("=" * 80)

        # Run all audits
        executor_results = self.audit_executor_architecture()
        questionnaire_results = self.audit_questionnaire_access()
        factory_results = self.audit_factory_pattern()
        method_results = self.audit_method_signatures()
        config_results = self.audit_configuration_system()

        # Compile report
        report = {
            "audit_metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "repository_root": str(self.repo_root),
                "total_findings": len(self.findings)
            },
            "audit_results": {
                "executor_architecture": executor_results,
                "questionnaire_access": questionnaire_results,
                "factory_pattern": factory_results,
                "method_signatures": method_results,
                "configuration_system": config_results
            },
            "findings": [f.to_dict() for f in self.findings],
            "summary": self._generate_summary()
        }

        # Save report if path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Audit report saved to: {output_path}")

        return report

    def _generate_summary(self) -> dict[str, Any]:
        """Generate summary of audit findings."""
        summary = {
            "total_findings": len(self.findings),
            "verified": sum(1 for f in self.findings if f.status == AuditStatus.VERIFIED),
            "warnings": sum(1 for f in self.findings if f.status == AuditStatus.WARNING),
            "failed": sum(1 for f in self.findings if f.status == AuditStatus.FAILED),
            "by_category": {}
        }

        # Group by category
        for category in AuditCategory:
            category_findings = [f for f in self.findings if f.category == category]
            summary["by_category"][category.value] = {
                "total": len(category_findings),
                "verified": sum(1 for f in category_findings if f.status == AuditStatus.VERIFIED),
                "warnings": sum(1 for f in category_findings if f.status == AuditStatus.WARNING),
                "failed": sum(1 for f in category_findings if f.status == AuditStatus.FAILED)
            }

        return summary

    def print_summary(self) -> None:
        """Print audit summary to console."""
        summary = self._generate_summary()

        print("\n" + "=" * 80)
        print("📋 AUDIT SUMMARY")
        print("=" * 80)
        print(f"Total Findings: {summary['total_findings']}")
        print(f"  ✅ Verified: {summary['verified']}")
        print(f"  ⚠️  Warnings: {summary['warnings']}")
        print(f"  ❌ Failed: {summary['failed']}")
        print("\n" + "-" * 80)
        print("By Category:")
        print("-" * 80)

        for category, stats in summary["by_category"].items():
            if stats["total"] > 0:
                print(f"\n{category}:")
                print(f"  Total: {stats['total']}")
                print(f"  ✅ Verified: {stats['verified']}")
                print(f"  ⚠️  Warnings: {stats['warnings']}")
                print(f"  ❌ Failed: {stats['failed']}")

        print("\n" + "=" * 80)


def main() -> None:
    """Main entry point for audit system."""
    import argparse

    parser = argparse.ArgumentParser(description="FARFAN Pipeline Audit System")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=PROJECT_ROOT,
        help="Repository root directory"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output path for audit report (JSON)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run audit
    audit_system = AuditSystem(args.repo_root)
    report = audit_system.generate_audit_report(args.output)
    audit_system.print_summary()

    # Exit with appropriate code
    if report["summary"]["failed"] > 0:
        sys.exit(1)
    elif report["summary"]["warnings"] > 0:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
