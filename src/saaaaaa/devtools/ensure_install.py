"""
Environment check to ensure the editable install is configured correctly.

Usage:
    python -m saaaaaa.devtools.ensure_install
"""

from __future__ import annotations

import sys
from pathlib import Path

import saaaaaa
from saaaaaa.config.paths import PROJECT_ROOT


def _describe_status() -> tuple[bool, str]:
    package_path = Path(saaaaaa.__file__).resolve()
    source_root = PROJECT_ROOT / "src" / "saaaaaa"

    if not package_path.exists():
        return False, f"Package path {package_path} does not exist"

    if not package_path.is_relative_to(source_root):
        return False, (
            "saaaaaa was imported from"
            f" {package_path}, but expected an editable install rooted at {source_root}"
        )

    if str(PROJECT_ROOT / "src") not in sys.path:
        return True, (
            "Editable install detected via .pth file "
            f"(import path: {package_path})"
        )

    return True, (
        "Editable install detected with direct src/ entry on sys.path. "
        "Prefer running `pip install -e .` and invoking modules via `python -m ...`."
    )


def main() -> int:
    """CLI entrypoint."""
    success, message = _describe_status()
    status = "OK" if success else "ERROR"
    print(f"[{status}] {message}")
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
