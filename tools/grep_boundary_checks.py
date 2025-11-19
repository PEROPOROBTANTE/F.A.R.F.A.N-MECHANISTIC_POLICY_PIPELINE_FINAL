"""Grep-based boundary violation detector for architectural guardrails."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

try:
    from saaaaaa.config.paths import PROJECT_ROOT
except Exception:  # pragma: no cover - bootstrap fallback
    PROJECT_ROOT = Path(__file__).resolve().parents[1]

if TYPE_CHECKING:
    from collections.abc import Sequence

REPO_ROOT = PROJECT_ROOT

class BoundaryViolation(Exception):
    """Raised when a boundary violation is detected."""


def run_grep(pattern: str, paths: Sequence[str]) -> list[str]:
    """Run grep command and return matching lines."""
    try:
        cmd = ["grep", "-rn", "--include=*.py", pattern, *paths]
        result = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip().split("\n")
        return []
    except Exception as exc:
        print(f"Warning: grep command failed: {exc}", file=sys.stderr)
        return []


def check_no_orchestrator_imports_in_core() -> None:
    """Ensure core and executors don't import from orchestrator."""
    print("Checking: core/executors must not import orchestrator...")
    
    patterns = [
        r"import\s+orchestrator",
        r"from\s+orchestrator\s+import",
    ]
    
    violations = []
    for pattern in patterns:
        matches = run_grep(pattern, ["core", "executors"])
        if matches and matches != [""]:
            violations.extend(matches)
    
    if violations:
        print(f"❌ Found {len(violations)} orchestrator import violations in core/executors:")
        for violation in violations[:10]:  # Show first 10
            print(f"  {violation}")
        raise BoundaryViolation("core/executors must not import orchestrator")
    
    print("  ✓ No orchestrator imports in core/executors")


def check_no_provider_calls_in_core() -> None:
    """Ensure core doesn't call orchestrator provider functions."""
    print("Checking: core must not call get_questionnaire_provider...")
    
    pattern = r"get_questionnaire_provider\s*\("
    matches = run_grep(pattern, ["core", "executors"])
    
    if matches and matches != [""]:
        print(f"❌ Found {len(matches)} provider calls in core/executors:")
        for match in matches[:10]:
            print(f"  {match}")
        raise BoundaryViolation("core/executors must not call orchestrator providers")
    
    print("  ✓ No provider calls in core/executors")


def check_no_json_io_in_core() -> None:
    """Ensure core doesn't perform direct JSON file I/O."""
    print("Checking: core must not perform JSON file I/O...")
    
    # More specific pattern: open() with .json inside parentheses
    pattern = r'open\([^)]*\.json[^)]*\)'
    matches = run_grep(pattern, ["core"])
    
    if matches and matches != [""]:
        print(f"❌ Found {len(matches)} JSON I/O operations in core:")
        for match in matches[:10]:
            print(f"  {match}")
        raise BoundaryViolation("core must not perform direct JSON I/O")
    
    print("  ✓ No JSON I/O in core")


def main() -> None:
    """Run all boundary checks."""
    print("=== Grep-based Boundary Checks ===\n")
    
    checks = [
        check_no_orchestrator_imports_in_core,
        check_no_provider_calls_in_core,
        check_no_json_io_in_core,
    ]
    
    failed = []
    for check in checks:
        try:
            check()
        except BoundaryViolation as exc:
            failed.append(str(exc))
    
    if failed:
        print(f"\n❌ {len(failed)} boundary check(s) failed")
        sys.exit(1)
    
    print("\n✓ All grep-based boundary checks passed")


if __name__ == "__main__":
    main()
