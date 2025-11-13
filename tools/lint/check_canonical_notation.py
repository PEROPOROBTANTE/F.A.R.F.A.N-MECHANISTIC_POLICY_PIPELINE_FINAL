#!/usr/bin/env python3
"""
Pre-commit hook to enforce canonical notation usage.

This script checks Python files for hardcoded dimension and policy area strings
and ensures they use the canonical notation module instead.

Exit code 0: All checks passed
Exit code 1: Found violations
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

# Hardcoded strings that should not appear in code
FORBIDDEN_DIMENSION_STRINGS = [
    "Diagnóstico y Recursos",
    "Diseño de Intervención",
    "Productos y Outputs",
    "Resultados y Outcomes",
    "Impactos de Largo Plazo",
    "Impactos y Efectos de Largo Plazo",
    "Teoría de Cambio",
    "Teoría de Cambio y Coherencia Causal",
]

FORBIDDEN_POLICY_STRINGS = [
    "Derechos de las mujeres e igualdad de género",
    "Prevención de la violencia y protección",
    "Ambiente sano, cambio climático",
    "Derechos económicos, sociales y culturales",
    "Derechos de las víctimas y construcción de paz",
    "Derecho al buen futuro de la niñez",
    "Tierras y territorios",
    "Líderes y defensores de derechos humanos",
    "Líderes y lideresas, defensores y defensoras",
    "Crisis de derechos de personas privadas",
    "Migración transfronteriza",
]

# Files that are exempt from this check
EXEMPT_FILES = [
    "canonical_notation.py",
    "check_canonical_notation.py",
    "questionnaire_monolith.json",
    "embedding_policy.py",  # Contains enum definitions with inline comments
    "factory.py",  # Contains example docstrings with canonical notation
]

# Directories to skip
SKIP_DIRS = [
    "__pycache__",
    ".git",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
]


def check_file(file_path: Path) -> List[Tuple[int, str, str]]:
    """
    Check a single file for hardcoded strings.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        List of (line_number, violation_string, line_content) tuples
    """
    violations = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Warning: Could not read {file_path}: {e}", file=sys.stderr)
        return violations
    
    all_forbidden = FORBIDDEN_DIMENSION_STRINGS + FORBIDDEN_POLICY_STRINGS
    
    in_docstring = False
    docstring_char = None
    
    for line_num, line in enumerate(lines, start=1):
        # Count triple quotes in line
        triple_double = line.count('"""')
        triple_single = line.count("'''")
        
        # Handle single-line docstrings (e.g., """text""")
        if triple_double >= 2 or triple_single >= 2:
            continue  # Entire line is a docstring
        
        # Track multi-line docstrings
        if '"""' in line and not in_docstring:
            in_docstring = True
            docstring_char = '"""'
            continue
        elif '"""' in line and in_docstring and docstring_char == '"""':
            in_docstring = False
            docstring_char = None
            continue
        elif "'''" in line and not in_docstring:
            in_docstring = True
            docstring_char = "'''"
            continue
        elif "'''" in line and in_docstring and docstring_char == "'''":
            in_docstring = False
            docstring_char = None
            continue
        
        # Skip if inside docstring
        if in_docstring:
            continue
        
        # Skip comments (lines starting with # or containing only inline comments)
        stripped = line.strip()
        if stripped.startswith('#'):
            continue
        
        # Skip lines that are just comments on enum/constant definitions
        if re.match(r'^\s*[A-Z0-9_]+\s*=.*#.*$', line):
            continue
        
        # Check for hardcoded strings in actual code (not comments)
        # Split on # to get the code part only
        code_part = line.split('#')[0] if '#' in line else line
        
        for forbidden in all_forbidden:
            if forbidden in code_part:
                violations.append((line_num, forbidden, line.strip()))
    
    return violations


def is_exempt(file_path: Path) -> bool:
    """Check if a file is exempt from canonical notation checks."""
    # Check if filename is in exempt list
    if file_path.name in EXEMPT_FILES:
        return True
    
    # Check if any parent directory is in skip list
    for part in file_path.parts:
        if part in SKIP_DIRS:
            return True
    
    return False


def main(files: List[str] = None) -> int:
    """
    Main entry point for the pre-commit hook.
    
    Args:
        files: List of files to check (from command line args)
        
    Returns:
        0 if no violations found, 1 otherwise
    """
    if files is None:
        files = sys.argv[1:] if len(sys.argv) > 1 else []
    
    # If no files specified, scan the repository
    if not files:
        repo_root = Path(__file__).resolve().parents[2]
        files = [
            str(p) for p in repo_root.rglob("*.py")
            if not is_exempt(p)
        ]
    
    total_violations = 0
    files_with_violations = []
    
    for file_path_str in files:
        file_path = Path(file_path_str)
        
        # Skip non-Python files and exempt files
        if not file_path.suffix == '.py' or is_exempt(file_path):
            continue
        
        violations = check_file(file_path)
        
        if violations:
            files_with_violations.append(file_path)
            total_violations += len(violations)
            
            print(f"\n❌ {file_path}:")
            for line_num, forbidden_str, line_content in violations:
                print(f"  Line {line_num}: Found hardcoded string '{forbidden_str}'")
                print(f"    → {line_content[:80]}...")
    
    if total_violations > 0:
        print(f"\n{'='*80}")
        print(f"❌ CANONICAL NOTATION VIOLATION")
        print(f"{'='*80}")
        print(f"Found {total_violations} hardcoded dimension/policy area strings")
        print(f"in {len(files_with_violations)} files.\n")
        print("These strings should use the canonical notation module instead:")
        print("  from saaaaaa.core.canonical_notation import get_dimension_info, get_policy_area_info")
        print("\nOr use the factory:")
        print("  from saaaaaa.core.orchestrator.factory import get_canonical_dimensions")
        print(f"{'='*80}\n")
        return 1
    
    print("✅ Canonical notation check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
