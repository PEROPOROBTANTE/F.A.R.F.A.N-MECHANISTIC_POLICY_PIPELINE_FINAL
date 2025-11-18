#!/usr/bin/env python3
"""
Fail CI when new PYTHONPATH snippets appear outside the documented allowlist.
"""

from __future__ import annotations

import sys
from pathlib import Path

ALLOWLIST = {
    Path("BUILD_HYGIENE.md"),
    Path("tools/validation/validate_build_hygiene.py"),
    Path("docs/QUICKSTART.md"),
    Path("TEST_AUDIT_REPORT.md"),
    Path("tests/conftest.py"),
    Path("STRATEGIC_WIRING_ARCHITECTURE.md"),
    Path("tools/lint/check_pythonpath_references.py"),
}


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    violations: list[str] = []

    for path in repo_root.rglob("*"):
        if path.suffix in {".pyc", ".png", ".jpg", ".jpeg"}:
            continue
        if any(part in {".git", ".venv", "venv", "__pycache__"} for part in path.parts):
            continue
        if not path.is_file():
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        if "PYTHONPATH" not in text:
            continue

        rel_path = path.relative_to(repo_root)

        if rel_path in ALLOWLIST:
            continue

        for idx, line in enumerate(text.splitlines(), 1):
            if "PYTHONPATH" in line:
                violations.append(f"{rel_path}:{idx}: {line.strip()}")

    if violations:
        print("❌ New PYTHONPATH references detected outside the allowlist:")
        for violation in violations:
            print(f"  - {violation}")
        print("\nUpdate the documentation to remove these references or extend the allowlist intentionally.")
        return 1

    print("✅ No unexpected PYTHONPATH references found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
