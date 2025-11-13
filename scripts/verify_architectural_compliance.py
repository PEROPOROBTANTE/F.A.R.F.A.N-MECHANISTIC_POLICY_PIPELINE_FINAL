#!/usr/bin/env python3
"""
Architectural Compliance Verification
======================================

Verifies that the codebase adheres to the 6 core architectural requirements:

1. Single Source of Truth: QuestionnaireResourceProvider only
2. I/O Boundary: factory.py only for questionnaire file I/O
3. Orchestrator DI: Dependency injection pattern
4. Router Decoupling: No questionnaire imports
5. Evidence Registry Decoupling: No questionnaire imports
6. No Reimplemented Logic: Pattern extraction only in provider

Exit code 0: All checks pass
Exit code 1: One or more violations found
"""

import re
import sys
from pathlib import Path
from typing import Tuple

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "saaaaaa"


def check_single_source_of_truth() -> Tuple[bool, list[str]]:
    """
    REQUIREMENT 1: QuestionnaireResourceProvider is the ONLY module
    that interprets questionnaire schemas and derives patterns.
    """
    violations = []
    
    # Find all Python files that might extract patterns
    pattern_keywords = [
        "extract.*pattern",
        "derive.*pattern",
        "compile.*pattern",
        "pattern.*extraction"
    ]
    
    for py_file in SRC.rglob("*.py"):
        # Skip the provider itself
        if "questionnaire_resource_provider.py" in str(py_file):
            continue
        
        with open(py_file, encoding='utf-8') as f:
            content = f.read()
        
        for keyword in pattern_keywords:
            if re.search(keyword, content, re.IGNORECASE):
                # Check if it's defining a method (potential violation)
                if re.search(rf"def\s+\w*{keyword}\w*", content, re.IGNORECASE):
                    violations.append(
                        f"{py_file.relative_to(ROOT)}: "
                        f"Contains pattern extraction logic outside provider"
                    )
                    break
    
    return len(violations) == 0, violations


def check_io_boundary() -> Tuple[bool, list[str]]:
    """
    REQUIREMENT 2: factory.py is the ONLY module that performs
    questionnaire-monolith file I/O.
    """
    violations = []
    
    # Check for direct file access to questionnaire_monolith.json
    for py_file in SRC.rglob("*.py"):
        # Skip factory files
        if "factory.py" in str(py_file):
            continue
        
        with open(py_file, encoding='utf-8') as f:
            content = f.read()
        
        # Check for direct file opens
        if re.search(r'open\s*\([^)]*questionnaire_monolith\.json', content):
            violations.append(
                f"{py_file.relative_to(ROOT)}: "
                f"Direct file I/O for questionnaire_monolith.json (use factory)"
            )
        
        # Check for Path reads
        if re.search(r'Path\([^)]*questionnaire_monolith\.json[^)]*\)\.read', content):
            violations.append(
                f"{py_file.relative_to(ROOT)}: "
                f"Direct Path read for questionnaire_monolith.json (use factory)"
            )
    
    return len(violations) == 0, violations


def check_orchestrator_di() -> Tuple[bool, list[str]]:
    """
    REQUIREMENT 3: core.py Orchestrator receives QuestionnaireResourceProvider
    via dependency injection.
    """
    violations = []
    
    core_file = SRC / "core" / "orchestrator" / "core.py"
    if not core_file.exists():
        return False, ["core.py not found"]
    
    with open(core_file, encoding='utf-8') as f:
        content = f.read()
    
    # Check that Orchestrator doesn't directly load questionnaire
    if re.search(r'open\s*\([^)]*questionnaire', content, re.IGNORECASE):
        violations.append(
            "core.py: Orchestrator performs direct file I/O (should use DI)"
        )
    
    # Check for proper dependency injection pattern
    if not re.search(r'questionnaire.*provider', content, re.IGNORECASE):
        violations.append(
            "core.py: No evidence of questionnaire_provider dependency injection"
        )
    
    return len(violations) == 0, violations


def check_router_decoupling() -> Tuple[bool, list[str]]:
    """
    REQUIREMENT 4: arg_router_extended.py does NOT import
    QuestionnaireResourceProvider.
    """
    violations = []
    
    router_file = SRC / "core" / "orchestrator" / "arg_router_extended.py"
    if not router_file.exists():
        # File doesn't exist, requirement is trivially satisfied
        return True, []
    
    with open(router_file, encoding='utf-8') as f:
        content = f.read()
    
    if re.search(r'from.*QuestionnaireResourceProvider', content):
        violations.append(
            "arg_router_extended.py: Imports QuestionnaireResourceProvider (violation)"
        )
    
    if re.search(r'import.*questionnaire_resource_provider', content):
        violations.append(
            "arg_router_extended.py: Imports questionnaire_resource_provider module"
        )
    
    return len(violations) == 0, violations


def check_evidence_registry_decoupling() -> Tuple[bool, list[str]]:
    """
    REQUIREMENT 5: evidence_registry.py does NOT import
    QuestionnaireResourceProvider.
    """
    violations = []
    
    registry_files = [
        SRC / "utils" / "evidence_registry.py",
        SRC / "core" / "orchestrator" / "evidence_registry.py"
    ]
    
    for registry_file in registry_files:
        if not registry_file.exists():
            continue
        
        with open(registry_file, encoding='utf-8') as f:
            content = f.read()
        
        if re.search(r'from.*QuestionnaireResourceProvider', content):
            violations.append(
                f"{registry_file.relative_to(ROOT)}: "
                f"Imports QuestionnaireResourceProvider (violation)"
            )
        
        if re.search(r'import.*questionnaire_resource_provider', content):
            violations.append(
                f"{registry_file.relative_to(ROOT)}: "
                f"Imports questionnaire_resource_provider module"
            )
    
    return len(violations) == 0, violations


def check_no_reimplemented_logic() -> Tuple[bool, list[str]]:
    """
    REQUIREMENT 6: No pattern extraction, validation derivation, or
    questionnaire schema interpretation outside QuestionnaireResourceProvider.
    """
    violations = []
    
    # Check for reimplemented pattern extraction
    for py_file in SRC.rglob("*.py"):
        if "questionnaire_resource_provider.py" in str(py_file):
            continue
        
        with open(py_file, encoding='utf-8') as f:
            content = f.read()
        
        # Look for pattern compilation/regex operations on questionnaire data
        suspicious_patterns = [
            r're\.compile\([^)]*question',
            r'Pattern\([^)]*question',
            r'extract.*validation.*question',
            r'derive.*threshold.*question',
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                violations.append(
                    f"{py_file.relative_to(ROOT)}: "
                    f"Possible reimplemented questionnaire logic (verify manually)"
                )
                break
    
    return len(violations) == 0, violations


def main() -> int:
    """Run all compliance checks"""
    print("=" * 80)
    print("ARCHITECTURAL COMPLIANCE VERIFICATION")
    print("=" * 80)
    print()
    
    checks = [
        ("Single Source of Truth", check_single_source_of_truth),
        ("I/O Boundary Enforcement", check_io_boundary),
        ("Orchestrator Dependency Injection", check_orchestrator_di),
        ("Router Decoupling", check_router_decoupling),
        ("Evidence Registry Decoupling", check_evidence_registry_decoupling),
        ("No Reimplemented Logic", check_no_reimplemented_logic),
    ]
    
    all_passed = True
    
    for i, (name, check_func) in enumerate(checks, 1):
        print(f"[{i}] {name}")
        passed, violations = check_func()
        
        if passed:
            print(f"    ✅ COMPLIANT")
        else:
            print(f"    ❌ VIOLATIONS FOUND:")
            for violation in violations:
                print(f"       - {violation}")
            all_passed = False
        
        print()
    
    print("=" * 80)
    if all_passed:
        print("✅ ALL ARCHITECTURAL REQUIREMENTS MET")
        print("=" * 80)
        return 0
    else:
        print("❌ ARCHITECTURAL VIOLATIONS DETECTED")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
