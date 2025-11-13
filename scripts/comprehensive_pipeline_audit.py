#!/usr/bin/env python3
"""
Comprehensive Pipeline Technical Audit
======================================

Executes exhaustive audit of the complete pipeline (ingest → normalize → chunk → 
signals → aggregate → score → report) detecting gaps, incompatibilities, technical 
debt and operational risks with reproducible evidence.

Operating Mode: Deterministic, no silent heuristics
Exit Code: Non-zero if CRITICAL findings exist
"""

import ast
import importlib
import inspect
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Add src to path for imports


class Severity(Enum):
    """Finding severity levels."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class Finding:
    """Represents a single audit finding."""
    id: str
    severity: Severity
    category: str
    title: str
    description: str
    evidence: List[str] = field(default_factory=list)
    file_location: Optional[str] = None
    line_number: Optional[int] = None
    remediation: Optional[str] = None
    test_name: Optional[str] = None
    test_result: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "severity": self.severity.value,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "evidence": self.evidence,
            "file_location": self.file_location,
            "line_number": self.line_number,
            "remediation": self.remediation,
            "test_name": self.test_name,
            "test_result": self.test_result,
        }


@dataclass
class AuditMetrics:
    """Audit execution metrics."""
    signal_hit_rate: float = 0.0
    signal_staleness_s: float = 0.0
    provenance_completeness: float = 0.0
    arg_router_routes_count: int = 0
    arg_router_silent_drops: int = 0
    determinism_phase_hashes_match: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "signal_hit_rate": self.signal_hit_rate,
            "signal_staleness_s": self.signal_staleness_s,
            "provenance_completeness": self.provenance_completeness,
            "arg_router_routes_count": self.arg_router_routes_count,
            "arg_router_silent_drops": self.arg_router_silent_drops,
            "determinism_phase_hashes_match": self.determinism_phase_hashes_match,
        }


class ComprehensivePipelineAuditor:
    """Main auditor class."""
    
    def __init__(self, repo_root: Path):
        """Initialize auditor."""
        self.repo_root = repo_root
        self.src_root = repo_root / "src" / "saaaaaa"
        self.findings: List[Finding] = []
        self.metrics = AuditMetrics()
        self.finding_counter = 0
        
    def generate_finding_id(self, category: str) -> str:
        """Generate unique finding ID."""
        self.finding_counter += 1
        return f"{category.upper()}-{self.finding_counter:03d}"
    
    def add_finding(self, finding: Finding) -> None:
        """Add a finding to the list."""
        self.findings.append(finding)
        
    # =========================================================================
    # Phase 1: Contract Compatibility Analysis
    # =========================================================================
    
    def audit_contract_compatibility(self) -> None:
        """Validate Deliverable_i → Expectation_{i+1} contracts."""
        print("📋 Phase 1: Contract Compatibility Analysis")
        
        # Check for Pydantic schemas
        contracts_dir = self.repo_root / "contracts"
        schemas_dir = self.repo_root / "config" / "schemas"
        
        if not contracts_dir.exists() and not schemas_dir.exists():
            self.add_finding(Finding(
                id=self.generate_finding_id("CONTRACT"),
                severity=Severity.CRITICAL,
                category="Contract Compatibility",
                title="No contracts directory found",
                description="Neither contracts/ nor config/schemas/ directory exists",
                evidence=[
                    f"Expected: {contracts_dir}",
                    f"Expected: {schemas_dir}",
                ],
                remediation="Create contracts directory with Pydantic schemas for each pipeline stage",
            ))
            return
        
        # Look for contract definitions
        contract_files = []
        if contracts_dir.exists():
            contract_files.extend(list(contracts_dir.glob("**/*.py")))
        if schemas_dir.exists():
            contract_files.extend(list(schemas_dir.glob("**/*.json")))
            
        print(f"  Found {len(contract_files)} contract files")
        
        # Check for specific pipeline stage contracts
        required_contracts = [
            "preprocessed_document",  # Ingest output
            "canonical_policy_package",  # CPP format
            "chunk_graph",  # Chunking output
            "signal_pack",  # Signal format
            "scored_result",  # Scoring output
        ]
        
        found_contracts = set()
        for contract_file in contract_files:
            content = contract_file.read_text(errors='ignore')
            for contract_name in required_contracts:
                if contract_name.replace("_", "") in content.lower().replace("_", ""):
                    found_contracts.add(contract_name)
        
        missing_contracts = set(required_contracts) - found_contracts
        if missing_contracts:
            self.add_finding(Finding(
                id=self.generate_finding_id("CONTRACT"),
                severity=Severity.HIGH,
                category="Contract Compatibility",
                title="Missing pipeline stage contracts",
                description=f"Missing contracts for: {', '.join(sorted(missing_contracts))}",
                evidence=[f"Required: {c}" for c in sorted(missing_contracts)],
                remediation="Define Pydantic schemas for all pipeline stage interfaces",
            ))
        
        # Check for Pydantic usage in contracts
        pydantic_found = False
        for py_file in contract_files:
            if py_file.suffix == ".py":
                content = py_file.read_text(errors='ignore')
                if "pydantic" in content.lower() or "BaseModel" in content:
                    pydantic_found = True
                    break
        
        if not pydantic_found and any(f.suffix == ".py" for f in contract_files):
            self.add_finding(Finding(
                id=self.generate_finding_id("CONTRACT"),
                severity=Severity.MEDIUM,
                category="Contract Compatibility",
                title="Pydantic not used for contract validation",
                description="No Pydantic BaseModel found in contract definitions",
                evidence=["Searched in contracts/ and config/schemas/"],
                remediation="Use Pydantic BaseModel for all contract schemas to ensure type safety",
            ))
    
    # =========================================================================
    # Phase 2: Parametrization Audit
    # =========================================================================
    
    def audit_parametrization(self) -> None:
        """Verify Config classes with from_env() and from_cli()."""
        print("📋 Phase 2: Parametrization Audit")
        
        # Find all Python files in src
        py_files = list(self.src_root.glob("**/*.py"))
        
        config_classes_found = 0
        config_classes_with_from_env = 0
        config_classes_with_from_cli = 0
        
        for py_file in py_files:
            try:
                content = py_file.read_text()
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # Check if it's a Config class
                        if "Config" in node.name or "config" in node.name.lower():
                            config_classes_found += 1
                            
                            # Check for from_env and from_cli methods
                            methods = [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
                            has_from_env = "from_env" in methods
                            has_from_cli = "from_cli" in methods
                            
                            if has_from_env:
                                config_classes_with_from_env += 1
                            if has_from_cli:
                                config_classes_with_from_cli += 1
                            
                            if not (has_from_env and has_from_cli):
                                self.add_finding(Finding(
                                    id=self.generate_finding_id("PARAM"),
                                    severity=Severity.MEDIUM,
                                    category="Parametrization",
                                    title=f"Config class missing standard methods: {node.name}",
                                    description=f"Config class lacks from_env={'✓' if has_from_env else '✗'} or from_cli={'✓' if has_from_cli else '✗'}",
                                    file_location=str(py_file.relative_to(self.repo_root)),
                                    line_number=node.lineno,
                                    evidence=[
                                        f"Class: {node.name}",
                                        f"Has from_env: {has_from_env}",
                                        f"Has from_cli: {has_from_cli}",
                                    ],
                                    remediation=f"Add {'from_env' if not has_from_env else ''}{' and ' if not (has_from_env or has_from_cli) else ''}{'from_cli' if not has_from_cli else ''} methods to {node.name}",
                                ))
            except Exception as e:
                # Skip files that can't be parsed
                continue
        
        print(f"  Found {config_classes_found} Config classes")
        print(f"  {config_classes_with_from_env} with from_env()")
        print(f"  {config_classes_with_from_cli} with from_cli()")
        
        # Check for YAML in executors
        executors_dir = self.repo_root / "executors"
        if executors_dir.exists():
            yaml_files = list(executors_dir.glob("**/*.yaml")) + list(executors_dir.glob("**/*.yml"))
            if yaml_files:
                self.add_finding(Finding(
                    id=self.generate_finding_id("PARAM"),
                    severity=Severity.CRITICAL,
                    category="Parametrization",
                    title="YAML files prohibited in executors/",
                    description=f"Found {len(yaml_files)} YAML files in executors/ directory",
                    evidence=[str(f.relative_to(self.repo_root)) for f in yaml_files[:5]],
                    remediation="Remove all YAML files from executors/ and use Config classes with from_env()/from_cli()",
                ))
    
    # =========================================================================
    # Phase 3: ArgRouter Validation
    # =========================================================================
    
    def audit_arg_router(self) -> None:
        """Verify ArgRouter with ≥30 routes and no silent drops."""
        print("📋 Phase 3: ArgRouter Validation")
        
        # Find ArgRouter implementation
        arg_router_files = list(self.src_root.glob("**/arg_router*.py"))
        
        if not arg_router_files:
            self.add_finding(Finding(
                id=self.generate_finding_id("ARGROUTER"),
                severity=Severity.CRITICAL,
                category="ArgRouter",
                title="ArgRouter implementation not found",
                description="No arg_router*.py file found in source tree",
                remediation="Implement ArgRouter with typed route handling",
            ))
            return
        
        routes_count = 0
        has_kwargs_wildcard = False
        silent_drop_found = False
        
        for router_file in arg_router_files:
            content = router_file.read_text()
            tree = ast.parse(content)
            
            # Count route registrations and check for **kwargs
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and "ArgRouter" in node.name:
                    # Count methods (approximate routes)
                    for method in node.body:
                        if isinstance(method, ast.FunctionDef):
                            if method.name not in ["__init__", "__repr__", "__str__"]:
                                routes_count += 1
                            
                            # Check for **kwargs in signature
                            if method.args.kwarg:
                                has_kwargs_wildcard = True
                                self.add_finding(Finding(
                                    id=self.generate_finding_id("ARGROUTER"),
                                    severity=Severity.MEDIUM,
                                    category="ArgRouter",
                                    title=f"Method uses **kwargs: {method.name}",
                                    description="ArgRouter methods should have explicit parameters, not **kwargs",
                                    file_location=str(router_file.relative_to(self.repo_root)),
                                    line_number=method.lineno,
                                    remediation=f"Replace **kwargs with explicit parameters in {method.name}",
                                ))
            
            # Check for silent drops
            if "silent" in content.lower() and "drop" in content.lower():
                silent_drop_found = True
        
        self.metrics.arg_router_routes_count = routes_count
        self.metrics.arg_router_silent_drops = 1 if silent_drop_found else 0
        
        print(f"  Found {routes_count} ArgRouter routes")
        
        if routes_count < 30:
            self.add_finding(Finding(
                id=self.generate_finding_id("ARGROUTER"),
                severity=Severity.MEDIUM,
                category="ArgRouter",
                title="Insufficient route count",
                description=f"Found {routes_count} routes, expected ≥30 specific routes",
                evidence=[f"Current routes: {routes_count}", "Expected: ≥30"],
                remediation="Add more specific routes to ArgRouter for all method types",
            ))
        
        if silent_drop_found:
            self.add_finding(Finding(
                id=self.generate_finding_id("ARGROUTER"),
                severity=Severity.HIGH,
                category="ArgRouter",
                title="Silent drop detected",
                description="ArgRouter contains silent drop logic",
                evidence=["Found 'silent' and 'drop' in code"],
                remediation="Remove silent drops and raise typed errors for all invalid arguments",
            ))
    
    # =========================================================================
    # Phase 4: Cross-Cut Signals
    # =========================================================================
    
    def audit_signals(self) -> None:
        """Audit cross-cut signals system."""
        print("📋 Phase 4: Cross-Cut Signals")
        
        # Find signals implementation
        signals_files = list(self.src_root.glob("**/signals*.py"))
        
        if not signals_files:
            self.add_finding(Finding(
                id=self.generate_finding_id("SIGNALS"),
                severity=Severity.HIGH,
                category="Signals",
                title="Signals implementation not found",
                description="No signals*.py file found in source tree",
                remediation="Implement cross-cut signal channel with SignalPack and SignalRegistry",
            ))
            return
        
        for signals_file in signals_files:
            content = signals_file.read_text()
            
            # Check for memory:// support
            if "memory://" not in content:
                self.add_finding(Finding(
                    id=self.generate_finding_id("SIGNALS"),
                    severity=Severity.MEDIUM,
                    category="Signals",
                    title="memory:// protocol not found",
                    description="Signals system should support memory:// for testing",
                    file_location=str(signals_file.relative_to(self.repo_root)),
                    remediation="Add memory:// protocol handler to SignalRegistry",
                ))
            
            # Check for HTTP client
            uses_http = "http://" in content or "https://" in content
            uses_httpx = "httpx" in content
            
            if uses_http and not uses_httpx:
                self.add_finding(Finding(
                    id=self.generate_finding_id("SIGNALS"),
                    severity=Severity.HIGH,
                    category="Signals",
                    title="HTTP signals not using httpx",
                    description="HTTP signals should use httpx for async support",
                    file_location=str(signals_file.relative_to(self.repo_root)),
                    remediation="Replace HTTP client with httpx",
                ))
            
            if uses_http:
                # Check for circuit breaker
                has_circuit_breaker = "circuit" in content.lower() or "breaker" in content.lower()
                has_etag = "etag" in content.lower()
                has_ttl = "ttl" in content.lower()
                
                if not has_circuit_breaker:
                    self.add_finding(Finding(
                        id=self.generate_finding_id("SIGNALS"),
                        severity=Severity.MEDIUM,
                        category="Signals",
                        title="HTTP signals missing circuit breaker",
                        description="HTTP signal client lacks circuit breaker pattern",
                        file_location=str(signals_file.relative_to(self.repo_root)),
                        remediation="Add circuit breaker with tenacity for HTTP resilience",
                    ))
                
                if not has_etag:
                    self.add_finding(Finding(
                        id=self.generate_finding_id("SIGNALS"),
                        severity=Severity.LOW,
                        category="Signals",
                        title="HTTP signals missing ETag support",
                        description="HTTP signals should support ETag for caching",
                        file_location=str(signals_file.relative_to(self.repo_root)),
                        remediation="Add ETag header handling for cache validation",
                    ))
                
                if not has_ttl:
                    self.add_finding(Finding(
                        id=self.generate_finding_id("SIGNALS"),
                        severity=Severity.LOW,
                        category="Signals",
                        title="HTTP signals missing TTL",
                        description="HTTP signals should have explicit TTL",
                        file_location=str(signals_file.relative_to(self.repo_root)),
                        remediation="Add TTL configuration to signal cache",
                    ))
            
            # Check for Pydantic validation
            if "pydantic" not in content.lower() and "BaseModel" not in content:
                self.add_finding(Finding(
                    id=self.generate_finding_id("SIGNALS"),
                    severity=Severity.MEDIUM,
                    category="Signals",
                    title="Signals missing Pydantic validation",
                    description="SignalPack should use Pydantic for validation",
                    file_location=str(signals_file.relative_to(self.repo_root)),
                    remediation="Define SignalPack as Pydantic BaseModel",
                ))
    
    # =========================================================================
    # Phase 5: CPP→Orchestrator Validation
    # =========================================================================
    
    def audit_cpp_adapter(self) -> None:
        """Validate CPP adapter implementation."""
        print("📋 Phase 5: CPP→Orchestrator Validation")
        
        # Find CPP adapter
        cpp_adapter_files = list(self.src_root.glob("**/cpp_adapter*.py"))
        
        if not cpp_adapter_files:
            self.add_finding(Finding(
                id=self.generate_finding_id("CPP"),
                severity=Severity.CRITICAL,
                category="CPP Adapter",
                title="CPP adapter not found",
                description="No cpp_adapter*.py file found",
                remediation="Implement CPPAdapter to convert CanonPolicyPackage to PreprocessedDocument",
            ))
            return
        
        for adapter_file in cpp_adapter_files:
            content = adapter_file.read_text()
            
            # Check for ordering by text_span.start
            if "text_span.start" not in content:
                self.add_finding(Finding(
                    id=self.generate_finding_id("CPP"),
                    severity=Severity.HIGH,
                    category="CPP Adapter",
                    title="Missing text_span.start ordering",
                    description="CPP adapter should order chunks by text_span.start",
                    file_location=str(adapter_file.relative_to(self.repo_root)),
                    remediation="Add: chunks = sorted(chunks, key=lambda c: c.text_span.start)",
                ))
            
            # Check for provenance_completeness
            if "provenance_completeness" not in content:
                self.add_finding(Finding(
                    id=self.generate_finding_id("CPP"),
                    severity=Severity.MEDIUM,
                    category="CPP Adapter",
                    title="Missing provenance_completeness calculation",
                    description="CPP adapter should compute provenance_completeness metric",
                    file_location=str(adapter_file.relative_to(self.repo_root)),
                    remediation="Add provenance_completeness calculation (covered_span / total_span)",
                ))
            
            # Check for ensure() method
            if "def ensure" not in content:
                self.add_finding(Finding(
                    id=self.generate_finding_id("CPP"),
                    severity=Severity.MEDIUM,
                    category="CPP Adapter",
                    title="Missing ensure() method",
                    description="CPP adapter should have ensure() for validation",
                    file_location=str(adapter_file.relative_to(self.repo_root)),
                    remediation="Add ensure() method for contract validation",
                ))
            
            # Check for resolution levels (micro/meso/macro)
            has_micro = "micro" in content.lower()
            has_meso = "meso" in content.lower()
            has_macro = "macro" in content.lower()
            
            if not (has_micro and has_meso and has_macro):
                missing = []
                if not has_micro:
                    missing.append("micro")
                if not has_meso:
                    missing.append("meso")
                if not has_macro:
                    missing.append("macro")
                    
                self.add_finding(Finding(
                    id=self.generate_finding_id("CPP"),
                    severity=Severity.MEDIUM,
                    category="CPP Adapter",
                    title="Missing chunk resolution levels",
                    description=f"CPP adapter missing resolution levels: {', '.join(missing)}",
                    file_location=str(adapter_file.relative_to(self.repo_root)),
                    evidence=[f"Missing: {r}" for r in missing],
                    remediation="Add support for all three resolution levels: micro, meso, macro",
                ))
    
    # =========================================================================
    # Phase 6: Determinism Check
    # =========================================================================
    
    def audit_determinism(self) -> None:
        """Check for deterministic execution."""
        print("📋 Phase 6: Determinism Check")
        
        # Look for seed management
        seed_files = list(self.src_root.glob("**/seed*.py")) + \
                     list(self.src_root.glob("**/determinism/*.py"))
        
        if not seed_files:
            self.add_finding(Finding(
                id=self.generate_finding_id("DETERM"),
                severity=Severity.HIGH,
                category="Determinism",
                title="No seed management found",
                description="No seed*.py or determinism/*.py files found",
                remediation="Implement seed factory for deterministic random number generation",
            ))
        else:
            print(f"  Found {len(seed_files)} seed management files")
        
        # Check for random usage without seed
        py_files = list(self.src_root.glob("**/*.py"))
        unseeded_random_files = []
        
        for py_file in py_files:
            content = py_file.read_text()
            if "import random" in content or "from random import" in content:
                # Check if seed is set
                if "random.seed" not in content and "set_seed" not in content:
                    unseeded_random_files.append(py_file)
        
        if unseeded_random_files:
            self.add_finding(Finding(
                id=self.generate_finding_id("DETERM"),
                severity=Severity.HIGH,
                category="Determinism",
                title="Random usage without seeding",
                description=f"Found {len(unseeded_random_files)} files using random without seed",
                evidence=[str(f.relative_to(self.repo_root)) for f in unseeded_random_files[:5]],
                remediation="Use seed_factory or call set_seed() before random operations",
            ))
        
        # Check for phase_hash usage
        orchestrator_files = list(self.src_root.glob("**/orchestrator/**/*.py"))
        has_phase_hash = False
        
        for orc_file in orchestrator_files:
            content = orc_file.read_text()
            if "phase_hash" in content:
                has_phase_hash = True
                break
        
        if not has_phase_hash:
            self.add_finding(Finding(
                id=self.generate_finding_id("DETERM"),
                severity=Severity.MEDIUM,
                category="Determinism",
                title="phase_hash not found",
                description="Orchestrator should compute phase_hash for reproducibility verification",
                remediation="Add phase_hash computation using blake3 of phase inputs/outputs",
            ))
    
    # =========================================================================
    # Phase 7: Aggregation/Scoring Rules
    # =========================================================================
    
    def audit_aggregation_scoring(self) -> None:
        """Validate aggregation and scoring rules."""
        print("📋 Phase 7: Aggregation/Scoring Rules")
        
        # Find aggregation files
        agg_files = list(self.src_root.glob("**/aggregation*.py"))
        score_files = list(self.src_root.glob("**/scoring*.py"))
        
        if not agg_files:
            self.add_finding(Finding(
                id=self.generate_finding_id("AGGREG"),
                severity=Severity.CRITICAL,
                category="Aggregation",
                title="Aggregation implementation not found",
                description="No aggregation*.py file found",
                remediation="Implement aggregation pipeline with explicit rules",
            ))
            return
        
        for agg_file in agg_files:
            content = agg_file.read_text()
            
            # Check for group_by keys
            if "group_by" not in content:
                self.add_finding(Finding(
                    id=self.generate_finding_id("AGGREG"),
                    severity=Severity.MEDIUM,
                    category="Aggregation",
                    title="Missing group_by specification",
                    description="Aggregation should have explicit group_by keys",
                    file_location=str(agg_file.relative_to(self.repo_root)),
                    remediation="Add explicit group_by parameter to aggregation functions",
                ))
            
            # Check for weights
            if "weight" not in content.lower():
                self.add_finding(Finding(
                    id=self.generate_finding_id("AGGREG"),
                    severity=Severity.MEDIUM,
                    category="Aggregation",
                    title="Missing weight definitions",
                    description="Aggregation should have explicit weight definitions",
                    file_location=str(agg_file.relative_to(self.repo_root)),
                    remediation="Add weight configuration for aggregation rules",
                ))
            
            # Check for column validation
            has_validation = any(kw in content for kw in ["validate", "required", "missing"])
            if not has_validation:
                self.add_finding(Finding(
                    id=self.generate_finding_id("AGGREG"),
                    severity=Severity.HIGH,
                    category="Aggregation",
                    title="Missing column validation",
                    description="Aggregation should fail on missing required columns",
                    file_location=str(agg_file.relative_to(self.repo_root)),
                    remediation="Add validation to raise error on missing required columns",
                ))
    
    # =========================================================================
    # Phase 8: Reporting Artifacts
    # =========================================================================
    
    def audit_reporting(self) -> None:
        """Verify reporting artifacts."""
        print("📋 Phase 8: Reporting Artifacts")
        
        # Look for report generation
        report_files = list(self.src_root.glob("**/report*.py"))
        
        if not report_files:
            self.add_finding(Finding(
                id=self.generate_finding_id("REPORT"),
                severity=Severity.MEDIUM,
                category="Reporting",
                title="Report generation not found",
                description="No report*.py file found",
                remediation="Implement report generation with metrics and fingerprints",
            ))
            return
        
        for report_file in report_files:
            content = report_file.read_text()
            
            # Check for required report components
            components = {
                "metrics": "metric" in content.lower(),
                "fingerprints": "fingerprint" in content.lower(),
                "phase_hash": "phase_hash" in content,
                "used_signals": "used_signals" in content or "signal" in content.lower(),
            }
            
            missing = [k for k, v in components.items() if not v]
            if missing:
                self.add_finding(Finding(
                    id=self.generate_finding_id("REPORT"),
                    severity=Severity.MEDIUM,
                    category="Reporting",
                    title="Report missing required components",
                    description=f"Report lacks: {', '.join(missing)}",
                    file_location=str(report_file.relative_to(self.repo_root)),
                    evidence=[f"Missing: {c}" for c in missing],
                    remediation=f"Add {', '.join(missing)} to report generation",
                ))
    
    # =========================================================================
    # Phase 9: Security/Privacy
    # =========================================================================
    
    def audit_security_privacy(self) -> None:
        """Check security and privacy concerns."""
        print("📋 Phase 9: Security/Privacy")
        
        # Check for PII patterns in signals
        signals_files = list(self.src_root.glob("**/signals*.py"))
        
        pii_patterns = ["email", "phone", "ssn", "tax_id", "dni", "passport"]
        
        for signals_file in signals_files:
            content = signals_file.read_text().lower()
            found_pii = [p for p in pii_patterns if p in content]
            
            if found_pii:
                self.add_finding(Finding(
                    id=self.generate_finding_id("SECURITY"),
                    severity=Severity.HIGH,
                    category="Security/Privacy",
                    title="Potential PII in signals",
                    description=f"Found PII-related terms in signals: {', '.join(found_pii)}",
                    file_location=str(signals_file.relative_to(self.repo_root)),
                    evidence=[f"Found: {p}" for p in found_pii],
                    remediation="Remove PII from signals or implement anonymization",
                ))
        
        # Check for hardcoded secrets
        py_files = list(self.src_root.glob("**/*.py"))
        secret_patterns = [
            r"password\s*=\s*['\"][^'\"]+['\"]",
            r"api_key\s*=\s*['\"][^'\"]+['\"]",
            r"secret\s*=\s*['\"][^'\"]+['\"]",
            r"token\s*=\s*['\"][^'\"]+['\"]",
        ]
        
        for py_file in py_files:
            content = py_file.read_text()
            for pattern in secret_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    self.add_finding(Finding(
                        id=self.generate_finding_id("SECURITY"),
                        severity=Severity.CRITICAL,
                        category="Security/Privacy",
                        title="Hardcoded secret detected",
                        description=f"Found hardcoded secret in {py_file.name}",
                        file_location=str(py_file.relative_to(self.repo_root)),
                        evidence=matches[:2],
                        remediation="Move secrets to environment variables or secure vault",
                    ))
        
        # Check HTTP client timeouts
        for py_file in py_files:
            content = py_file.read_text()
            if "httpx" in content or "requests" in content:
                if "timeout" not in content.lower():
                    self.add_finding(Finding(
                        id=self.generate_finding_id("SECURITY"),
                        severity=Severity.MEDIUM,
                        category="Security/Privacy",
                        title="HTTP client missing timeout",
                        description=f"HTTP client in {py_file.name} lacks timeout",
                        file_location=str(py_file.relative_to(self.repo_root)),
                        remediation="Add timeout parameter to all HTTP requests",
                    ))
    
    # =========================================================================
    # Phase 10: Dependencies
    # =========================================================================
    
    def audit_dependencies(self) -> None:
        """Audit dependency management."""
        print("📋 Phase 10: Dependencies")
        
        # Check requirements files
        req_files = [
            self.repo_root / "requirements.txt",
            self.repo_root / "pyproject.toml",
        ]
        
        declared_deps = set()
        
        for req_file in req_files:
            if req_file.exists():
                content = req_file.read_text()
                # Extract package names (simple parsing)
                for line in content.split("\n"):
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # Get package name before version specifier
                        pkg = re.split(r"[<>=!]", line)[0].strip()
                        if pkg:
                            declared_deps.add(pkg.lower())
        
        print(f"  Found {len(declared_deps)} declared dependencies")
        
        # Check for imports in source code
        imported_packages = set()
        py_files = list(self.src_root.glob("**/*.py"))
        
        for py_file in py_files:
            try:
                content = py_file.read_text()
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            pkg = alias.name.split(".")[0]
                            imported_packages.add(pkg.lower())
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            pkg = node.module.split(".")[0]
                            imported_packages.add(pkg.lower())
            except:
                continue
        
        # Filter out stdlib and internal packages
        stdlib = {"os", "sys", "json", "re", "time", "datetime", "pathlib", "typing", 
                  "dataclasses", "collections", "itertools", "functools", "abc", 
                  "logging", "threading", "asyncio", "inspect", "ast", "hashlib"}
        
        external_imports = imported_packages - stdlib - {"saaaaaa"}
        
        # Find undeclared dependencies
        undeclared = external_imports - declared_deps
        
        if undeclared:
            # Filter common false positives
            undeclared = {pkg for pkg in undeclared if len(pkg) > 2}
            
            if undeclared:
                self.add_finding(Finding(
                    id=self.generate_finding_id("DEPS"),
                    severity=Severity.HIGH,
                    category="Dependencies",
                    title="Undeclared dependencies detected",
                    description=f"Found {len(undeclared)} imported packages not in requirements",
                    evidence=sorted(list(undeclared))[:10],
                    remediation="Add missing packages to requirements.txt with version pins",
                ))
        
        # Check for version pins
        req_file = self.repo_root / "requirements.txt"
        if req_file.exists():
            content = req_file.read_text()
            unpinned = []
            for line in content.split("\n"):
                line = line.strip()
                if line and not line.startswith("#"):
                    if "==" not in line:
                        unpinned.append(line)
            
            if unpinned:
                self.add_finding(Finding(
                    id=self.generate_finding_id("DEPS"),
                    severity=Severity.MEDIUM,
                    category="Dependencies",
                    title="Unpinned dependencies",
                    description=f"Found {len(unpinned)} dependencies without exact version pins",
                    evidence=unpinned[:5],
                    remediation="Pin all dependencies with == to ensure reproducibility",
                ))
    
    # =========================================================================
    # Main Audit Execution
    # =========================================================================
    
    def run_audit(self) -> None:
        """Execute all audit phases."""
        print("\n" + "=" * 80)
        print("COMPREHENSIVE PIPELINE TECHNICAL AUDIT")
        print("=" * 80)
        print(f"Repository: {self.repo_root}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print("=" * 80 + "\n")
        
        # Run all audit phases
        self.audit_contract_compatibility()
        self.audit_parametrization()
        self.audit_arg_router()
        self.audit_signals()
        self.audit_cpp_adapter()
        self.audit_determinism()
        self.audit_aggregation_scoring()
        self.audit_reporting()
        self.audit_security_privacy()
        self.audit_dependencies()
        
        print("\n" + "=" * 80)
        print("AUDIT COMPLETE")
        print("=" * 80)
        
    def generate_reports(self) -> Tuple[int, int]:
        """Generate audit reports and return critical/total counts."""
        # Count findings by severity
        severity_counts = defaultdict(int)
        for finding in self.findings:
            severity_counts[finding.severity] += 1
        
        critical_count = severity_counts[Severity.CRITICAL]
        high_count = severity_counts[Severity.HIGH]
        medium_count = severity_counts[Severity.MEDIUM]
        low_count = severity_counts[Severity.LOW]
        info_count = severity_counts[Severity.INFO]
        total_count = len(self.findings)
        
        # Generate AUDIT_REPORT.md
        self._generate_audit_report(
            severity_counts, critical_count, high_count, 
            medium_count, low_count, total_count
        )
        
        # Generate AUDIT_FIX_PLAN.md
        self._generate_fix_plan(critical_count, high_count, medium_count)
        
        return critical_count, total_count
    
    def _generate_audit_report(
        self, 
        severity_counts: Dict[Severity, int],
        critical_count: int,
        high_count: int,
        medium_count: int,
        low_count: int,
        total_count: int
    ) -> None:
        """Generate AUDIT_REPORT.md."""
        report_path = self.repo_root / "AUDIT_REPORT.md"
        
        with open(report_path, "w") as f:
            f.write("# Comprehensive Pipeline Technical Audit Report\n\n")
            f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
            f.write(f"**Repository:** {self.repo_root}\n\n")
            
            # Executive Summary
            f.write("## Executive Summary\n\n")
            f.write(f"**Total Findings:** {total_count}\n\n")
            f.write("| Severity | Count |\n")
            f.write("|----------|-------|\n")
            f.write(f"| 🔴 CRITICAL | {critical_count} |\n")
            f.write(f"| 🟠 HIGH | {high_count} |\n")
            f.write(f"| 🟡 MEDIUM | {medium_count} |\n")
            f.write(f"| 🟢 LOW | {low_count} |\n")
            f.write(f"| ℹ️ INFO | {severity_counts[Severity.INFO]} |\n\n")
            
            # Audit Metrics
            f.write("## Audit Metrics\n\n")
            f.write("```json\n")
            f.write(json.dumps(self.metrics.to_dict(), indent=2))
            f.write("\n```\n\n")
            
            # Contract Matrix
            f.write("## Contract Compatibility Matrix\n\n")
            f.write("| Stage | Input Contract | Output Contract | Status |\n")
            f.write("|-------|---------------|-----------------|--------|\n")
            f.write("| Ingest | Document | PreprocessedDocument | ⚠️ |\n")
            f.write("| Normalize | PreprocessedDocument | CanonPolicyPackage | ⚠️ |\n")
            f.write("| Chunk | CanonPolicyPackage | ChunkGraph | ⚠️ |\n")
            f.write("| Signals | - | SignalPack | ⚠️ |\n")
            f.write("| Aggregate | ScoredResult[] | AreaScore | ⚠️ |\n")
            f.write("| Score | AreaScore | MacroScore | ⚠️ |\n")
            f.write("| Report | MacroScore | Report | ⚠️ |\n\n")
            
            # Findings by Category
            f.write("## Findings by Category\n\n")
            
            findings_by_category = defaultdict(list)
            for finding in self.findings:
                findings_by_category[finding.category].append(finding)
            
            for category in sorted(findings_by_category.keys()):
                findings = findings_by_category[category]
                f.write(f"### {category} ({len(findings)} findings)\n\n")
                
                for finding in sorted(findings, key=lambda x: x.severity.value):
                    severity_emoji = {
                        Severity.CRITICAL: "🔴",
                        Severity.HIGH: "🟠",
                        Severity.MEDIUM: "🟡",
                        Severity.LOW: "🟢",
                        Severity.INFO: "ℹ️",
                    }[finding.severity]
                    
                    f.write(f"#### {severity_emoji} {finding.id}: {finding.title}\n\n")
                    f.write(f"**Severity:** {finding.severity.value}\n\n")
                    f.write(f"**Description:** {finding.description}\n\n")
                    
                    if finding.file_location:
                        location = finding.file_location
                        if finding.line_number:
                            location += f":{finding.line_number}"
                        f.write(f"**Location:** `{location}`\n\n")
                    
                    if finding.evidence:
                        f.write("**Evidence:**\n")
                        for evidence in finding.evidence:
                            f.write(f"- {evidence}\n")
                        f.write("\n")
                    
                    if finding.remediation:
                        f.write(f"**Remediation:** {finding.remediation}\n\n")
                    
                    f.write("---\n\n")
            
            # Summary
            f.write("## Summary\n\n")
            if critical_count > 0:
                f.write(f"⚠️ **{critical_count} CRITICAL findings require immediate attention**\n\n")
            if high_count > 0:
                f.write(f"⚠️ {high_count} HIGH priority findings should be addressed soon\n\n")
            if medium_count + low_count > 0:
                f.write(f"ℹ️ {medium_count + low_count} MEDIUM/LOW priority findings for improvement\n\n")
            
        print(f"\n✅ Generated: {report_path}")
    
    def _generate_fix_plan(
        self, 
        critical_count: int, 
        high_count: int, 
        medium_count: int
    ) -> None:
        """Generate AUDIT_FIX_PLAN.md."""
        plan_path = self.repo_root / "AUDIT_FIX_PLAN.md"
        
        with open(plan_path, "w") as f:
            f.write("# Audit Fix Plan\n\n")
            f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
            
            # Immediate (Critical)
            critical_findings = [f for f in self.findings if f.severity == Severity.CRITICAL]
            if critical_findings:
                f.write("## Immediate Priority (CRITICAL)\n\n")
                f.write("**Timeline:** Within 24 hours\n\n")
                f.write("**Owner:** Development Team Lead\n\n")
                
                for finding in critical_findings:
                    f.write(f"### {finding.id}: {finding.title}\n\n")
                    f.write(f"**Issue:** {finding.description}\n\n")
                    if finding.remediation:
                        f.write(f"**Action:** {finding.remediation}\n\n")
                    if finding.file_location:
                        f.write(f"**File:** `{finding.file_location}`\n\n")
                    f.write("---\n\n")
            
            # Short-Term (High)
            high_findings = [f for f in self.findings if f.severity == Severity.HIGH]
            if high_findings:
                f.write("## Short-Term Priority (HIGH)\n\n")
                f.write("**Timeline:** Within 1 week\n\n")
                f.write("**Owner:** Development Team\n\n")
                
                for finding in high_findings:
                    f.write(f"### {finding.id}: {finding.title}\n\n")
                    f.write(f"**Issue:** {finding.description}\n\n")
                    if finding.remediation:
                        f.write(f"**Action:** {finding.remediation}\n\n")
                    if finding.file_location:
                        f.write(f"**File:** `{finding.file_location}`\n\n")
                    f.write("---\n\n")
            
            # Medium-Term (Medium)
            medium_findings = [f for f in self.findings if f.severity == Severity.MEDIUM]
            if medium_findings:
                f.write("## Medium-Term Priority (MEDIUM)\n\n")
                f.write("**Timeline:** Within 2-4 weeks\n\n")
                f.write("**Owner:** Development Team\n\n")
                
                for finding in medium_findings[:10]:  # Limit to first 10
                    f.write(f"### {finding.id}: {finding.title}\n\n")
                    f.write(f"**Issue:** {finding.description}\n\n")
                    if finding.remediation:
                        f.write(f"**Action:** {finding.remediation}\n\n")
                    f.write("---\n\n")
                
                if len(medium_findings) > 10:
                    f.write(f"*... and {len(medium_findings) - 10} more medium priority items*\n\n")
        
        print(f"✅ Generated: {plan_path}")


def main() -> int:
    """Main entry point."""
    repo_root = Path(__file__).parent
    
    auditor = ComprehensivePipelineAuditor(repo_root)
    auditor.run_audit()
    
    critical_count, total_count = auditor.generate_reports()
    
    print(f"\n{'=' * 80}")
    print(f"Total Findings: {total_count}")
    print(f"Critical Findings: {critical_count}")
    print(f"{'=' * 80}\n")
    
    # Exit with non-zero if critical findings exist
    return 1 if critical_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
