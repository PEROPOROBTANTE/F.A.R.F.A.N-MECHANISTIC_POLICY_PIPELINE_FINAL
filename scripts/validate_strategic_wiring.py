#!/usr/bin/env python3
"""
Strategic High-Level Wiring Validation Script
==============================================

This script performs comprehensive validation of the high-level wiring
across all strategic self-contained files.

Purpose: AUDIT, ENSURE, FORCE, GUARANTEE, and SUSTAIN high-level wiring

Validates:
1. All strategic files exist and are syntactically correct
2. Cross-file imports and dependencies are properly wired
3. Provenance tracking includes all strategic files
4. Module interfaces are properly exposed
5. Integration points are correctly configured
6. Determinism and reproducibility guarantees
7. Golden Rules compliance
8. Evidence registry and audit trail integrity
"""

import ast
import sys
from pathlib import Path

class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    """Print formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 80}")
    print(f"{text:^80}")
    print(f"{'=' * 80}{Colors.RESET}\n")

def print_success(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓{Colors.RESET} {text}")

def print_error(text: str):
    """Print error message."""
    print(f"{Colors.RED}✗{Colors.RESET} {text}")

def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {text}")

def check_file_exists(file_path: Path) -> bool:
    """Check if file exists and is readable."""
    return file_path.exists() and file_path.is_file()

def check_python_syntax(file_path: Path) -> tuple[bool, str]:
    """Check Python file syntax."""
    try:
        with open(file_path, encoding='utf-8') as f:
            ast.parse(f.read())
        return True, "OK"
    except SyntaxError as e:
        return False, f"Syntax error at line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, str(e)

def extract_imports(file_path: Path) -> set[str]:
    """Extract all imports from a Python file."""
    imports = set()
    try:
        with open(file_path, encoding='utf-8') as f:
            tree = ast.parse(f.read())

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split('.')[0])

    except Exception:
        pass

    return imports

def validate_strategic_files() -> dict[str, bool]:
    """Validate all strategic files exist and are syntactically correct."""
    print_header("STRATEGIC FILES VALIDATION")

    strategic_files = {
        "demo_macro_prompts.py": "Macro-level analysis demonstrations",
        "verify_complete_implementation.py": "Implementation verification",
        "validation_engine.py": "Centralized validation engine",
        "validate_system.py": "System validation script",
        "seed_factory.py": "Deterministic seed generation",
        "qmcm_hooks.py": "Quality method call monitoring",
        "meso_cluster_analysis.py": "Meso-level cluster analysis",
        "macro_prompts.py": "Macro-level strategic prompts",
        "json_contract_loader.py": "JSON contract loading",
        "evidence_registry.py": "Append-only evidence registry",
        "document_ingestion.py": "Document ingestion module",
        "scoring.py": "Scoring modalities",
        "recommendation_engine.py": "Recommendation engine",
        "orchestrator.py": "Orchestrator implementation",
        "micro_prompts.py": "Micro-level analysis prompts",
        "coverage_gate.py": "Coverage enforcement gate",
        "scripts/bootstrap_validate.py": "Bootstrap validation",
        "validation/predicates.py": "Validation predicates",
        "validation/golden_rule.py": "Golden rule enforcement",
        "validation/architecture_validator.py": "Architecture validation"
    }

    results = {}

    for file_path, description in strategic_files.items():
        full_path = Path(file_path)

        # Check existence
        if not check_file_exists(full_path):
            print_error(f"{file_path}: File not found")
            results[file_path] = False
            continue

        # Check syntax
        syntax_ok, error_msg = check_python_syntax(full_path)
        if not syntax_ok:
            print_error(f"{file_path}: {error_msg}")
            results[file_path] = False
            continue

        print_success(f"{file_path}: {description}")
        results[file_path] = True

    return results

def validate_provenance() -> bool:
    """Validate provenance.csv includes all strategic files."""
    print_header("PROVENANCE TRACKING VALIDATION")

    provenance_path = Path("provenance.csv")

    if not provenance_path.exists():
        print_error("provenance.csv not found")
        return False

    with open(provenance_path) as f:
        provenance_content = f.read()

    strategic_files = [
        "demo_macro_prompts.py",
        "verify_complete_implementation.py",
        "validation_engine.py",
        "validate_system.py",
        "seed_factory.py",
        "qmcm_hooks.py",
        "meso_cluster_analysis.py",
        "macro_prompts.py",
        "json_contract_loader.py",
        "evidence_registry.py",
        "document_ingestion.py",
        "scoring.py",
        "recommendation_engine.py",
        "orchestrator.py",
        "micro_prompts.py",
        "coverage_gate.py"
    ]

    all_tracked = True
    for file_name in strategic_files:
        if file_name in provenance_content:
            print_success(f"{file_name} tracked in provenance")
        else:
            print_error(f"{file_name} NOT tracked in provenance")
            all_tracked = False

    return all_tracked

def validate_cross_file_wiring() -> bool:
    """Validate cross-file imports and dependencies."""
    print_header("CROSS-FILE WIRING VALIDATION")

    wiring_specs = [
        {
            "file": "validation_engine.py",
            "must_import": ["validation.predicates"],
            "description": "ValidationEngine uses ValidationPredicates"
        },
        {
            "file": "demo_macro_prompts.py",
            "must_import": ["macro_prompts"],
            "description": "Demo imports MacroPrompts classes"
        },
        {
            "file": "seed_factory.py",
            "must_import": ["hashlib", "hmac"],
            "description": "SeedFactory uses cryptographic hashing"
        },
        {
            "file": "evidence_registry.py",
            "must_import": ["hashlib"],
            "description": "EvidenceRegistry uses hashing for immutability"
        }
    ]

    all_wired = True

    for spec in wiring_specs:
        file_path = Path(spec["file"])
        imports = extract_imports(file_path)

        missing = []
        for required in spec["must_import"]:
            # Check if the required module is imported (handle dot notation)
            base_module = required.split('.')[0]
            if base_module not in imports and required not in imports:
                missing.append(required)

        if not missing:
            print_success(f"{spec['file']}: {spec['description']}")
        else:
            print_error(f"{spec['file']}: Missing imports: {', '.join(missing)}")
            all_wired = False

    return all_wired

def validate_module_interfaces() -> bool:
    """Validate that modules expose expected interfaces."""
    print_header("MODULE INTERFACE VALIDATION")

    interface_specs = [
        {
            "module": "seed_factory",
            "expected_classes": ["SeedFactory", "DeterministicContext"],
            "expected_functions": ["create_deterministic_seed"]
        },
        {
            "module": "evidence_registry",
            "expected_classes": ["EvidenceRegistry", "EvidenceRecord"],
            "expected_functions": []
        },
        {
            "module": "json_contract_loader",
            "expected_classes": ["JSONContractLoader", "ContractDocument", "ContractLoadReport"],
            "expected_functions": []
        },
        {
            "module": "qmcm_hooks",
            "expected_classes": ["QMCMRecorder"],
            "expected_functions": ["get_global_recorder", "qmcm_record"]
        },
        {
            "module": "validation_engine",
            "expected_classes": ["ValidationEngine", "ValidationReport"],
            "expected_functions": []
        }
    ]

    all_valid = True

    for spec in interface_specs:
        try:
            module = __import__(spec["module"])

            missing = []
            for class_name in spec["expected_classes"]:
                if not hasattr(module, class_name):
                    missing.append(f"class {class_name}")

            for func_name in spec["expected_functions"]:
                if not hasattr(module, func_name):
                    missing.append(f"function {func_name}")

            if not missing:
                print_success(f"{spec['module']}: All interfaces exposed")
            else:
                print_error(f"{spec['module']}: Missing {', '.join(missing)}")
                all_valid = False

        except ImportError as e:
            print_error(f"{spec['module']}: Import failed - {e}")
            all_valid = False

    return all_valid

def validate_determinism() -> bool:
    """Validate determinism guarantees."""
    print_header("DETERMINISM VALIDATION")

    try:
        from saaaaaa.core.seed_factory import create_deterministic_seed

        # Test deterministic seed generation
        seed1 = create_deterministic_seed("test-001", question_id="Q1", policy_area="P1")
        seed2 = create_deterministic_seed("test-001", question_id="Q1", policy_area="P1")

        if seed1 == seed2:
            print_success("SeedFactory produces deterministic seeds")
        else:
            print_error("SeedFactory NOT producing deterministic seeds")
            return False

        # Test different inputs produce different seeds
        seed3 = create_deterministic_seed("test-002", question_id="Q1", policy_area="P1")
        if seed1 != seed3:
            print_success("SeedFactory produces unique seeds for different inputs")
        else:
            print_error("SeedFactory producing identical seeds for different inputs")
            return False

        return True

    except Exception as e:
        print_error(f"Determinism validation failed: {e}")
        return False

def validate_immutability() -> bool:
    """Validate immutability guarantees."""
    print_header("IMMUTABILITY VALIDATION")

    try:
        from saaaaaa.core.evidence_registry import EvidenceRegistry

        registry = EvidenceRegistry(auto_load=False)

        record1 = registry.append(
            method_name="test_method",
            evidence=["evidence1"],
            metadata={"key": "value"}
        )

        # Try to modify frozen record (should fail)
        try:
            record1.index = 999
            print_error("EvidenceRecord NOT properly frozen (immutable)")
            return False
        except Exception:
            print_success("EvidenceRecord is properly frozen (immutable)")

        # Verify chain integrity
        record2 = registry.append(
            method_name="test_method_2",
            evidence=["evidence2"],
            metadata={"key2": "value2"}
        )

        if record2.previous_hash == record1.entry_hash:
            print_success("Evidence chain integrity maintained")
        else:
            print_error("Evidence chain integrity BROKEN")
            return False

        return True

    except Exception as e:
        print_error(f"Immutability validation failed: {e}")
        return False

def validate_golden_rules() -> bool:
    """Validate Golden Rules enforcement."""
    print_header("GOLDEN RULES VALIDATION")

    try:
        from saaaaaa.utils.validation.golden_rule import GoldenRuleValidator, GoldenRuleViolation

        step_catalog = ["step1", "step2", "step3"]
        questionnaire_hash = "test_hash_123"

        validator = GoldenRuleValidator(questionnaire_hash, step_catalog)

        # Test immutable metadata enforcement
        try:
            validator.assert_immutable_metadata(questionnaire_hash, step_catalog)
            print_success("Golden Rules: Immutable metadata validated")
        except GoldenRuleViolation:
            print_error("Golden Rules: Immutable metadata validation failed")
            return False

        # Test mutation detection
        try:
            validator.assert_immutable_metadata("different_hash", step_catalog)
            print_error("Golden Rules: Failed to detect metadata mutation")
            return False
        except GoldenRuleViolation:
            print_success("Golden Rules: Metadata mutation detected")

        # Test deterministic DAG
        try:
            validator.assert_deterministic_dag(["step1", "step2"])
            print_success("Golden Rules: Deterministic DAG validated")
        except GoldenRuleViolation:
            print_error("Golden Rules: Deterministic DAG validation failed")
            return False

        return True

    except Exception as e:
        print_error(f"Golden Rules validation failed: {e}")
        return False

def generate_wiring_report():
    """Generate comprehensive wiring validation report."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║         STRATEGIC HIGH-LEVEL WIRING VALIDATION REPORT                     ║")
    print("║              AUDIT · ENSURE · FORCE · GUARANTEE · SUSTAIN                 ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print(Colors.RESET)

    results = {
        "Strategic Files": validate_strategic_files(),
        "Provenance Tracking": validate_provenance(),
        "Cross-File Wiring": validate_cross_file_wiring(),
        "Module Interfaces": validate_module_interfaces(),
        "Determinism": validate_determinism(),
        "Immutability": validate_immutability(),
        "Golden Rules": validate_golden_rules()
    }

    # Summary
    print_header("VALIDATION SUMMARY")

    all_passed = all(
        all(v for v in result.values()) if isinstance(result, dict) else result
        for result in results.values()
    )

    for category, result in results.items():
        if isinstance(result, dict):
            passed = sum(1 for v in result.values() if v)
            total = len(result)
            if passed == total:
                print_success(f"{category}: {passed}/{total} checks passed")
            else:
                print_error(f"{category}: {passed}/{total} checks passed")
        else:
            if result:
                print_success(f"{category}: PASSED")
            else:
                print_error(f"{category}: FAILED")

    print("\n" + "=" * 80)

    if all_passed:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ ALL VALIDATIONS PASSED")
        print("Strategic high-level wiring is properly configured and sustained{Colors.RESET}\n")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ VALIDATION FAILED")
        print("Strategic high-level wiring requires attention{Colors.RESET}\n")
        return 1

def main():
    """Main entry point."""
    return generate_wiring_report()

if __name__ == "__main__":
    sys.exit(main())
