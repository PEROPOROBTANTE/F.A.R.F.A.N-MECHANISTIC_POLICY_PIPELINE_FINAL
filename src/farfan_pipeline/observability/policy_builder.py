"""
Policy Builder

Constructs ImportPolicy and PathPolicy from the actual repository state.
Anchored to real files and dependencies.

"Maximum hardness" assumptions:
- Repo root MUST contain farfan_core/farfan_core.
- Third-party allowlist MUST come from an explicit dependency_lockdown module.
- Any failure to compute a clear policy is treated as a fatal configuration error.
"""

from __future__ import annotations

import site
import sys
import tempfile
from pathlib import Path
from typing import FrozenSet, Set

from .path_import_policy import ImportPolicy, PathPolicy


def compute_repo_root() -> Path:
    """
    Compute repository root by locating the directory containing farfan_core package.

    Strategy:
    - Walk parents of this file until we find one that contains farfan_core/farfan_core.
    - Fallback to farfan_core.config.paths.PROJECT_ROOT if available.
    - If nothing matches, fail hard.

    Returns:
        Path to repository root.

    Raises:
        RuntimeError: If repo root cannot be determined.
    """
    here = Path(__file__).resolve()

    for candidate in here.parents:
        if (candidate / "farfan_core" / "farfan_core").exists():
            return candidate

    # Fallback: use PROJECT_ROOT from config if available
    try:
        from farfan_pipeline.config.paths import PROJECT_ROOT  # type: ignore[attr-defined]

        project_root = Path(PROJECT_ROOT).resolve()
        if (project_root / "farfan_core" / "farfan_core").exists():
            return project_root
    except Exception:
        pass

    raise RuntimeError(
        f"Cannot determine repo root. Scanned parents of {here} and did not find a "
        f"directory containing farfan_core/farfan_core, nor a valid PROJECT_ROOT."
    )


def _load_third_party_from_lockdown(repo_root: Path) -> FrozenSet[str]:
    """
    Load third-party module allowlist from an explicit lockdown module.

    Maximum hardness:
    - We do NOT silently fall back to requirements.txt.
    - If the lockdown module is missing or empty, this is a configuration error.
    """
    try:
        # Module is expected to live under farfan_core/farfan_core/config/dependency_lockdown.py
        from farfan_pipeline.config.dependency_lockdown import ALLOWED_THIRD_PARTY_MODULES  # type: ignore[attr-defined]

        allowed = frozenset(ALLOWED_THIRD_PARTY_MODULES)
        if not allowed:
            raise RuntimeError("ALLOWED_THIRD_PARTY_MODULES is empty; lockdown too weak.")
        return allowed
    except Exception as exc:
        raise RuntimeError(
            "Failed to load ALLOWED_THIRD_PARTY_MODULES from "
            "farfan_core.config.dependency_lockdown. This module MUST exist "
            "and define a non-empty ALLOWED_THIRD_PARTY_MODULES FrozenSet[str]."
        ) from exc


def build_import_policy(repo_root: Path) -> ImportPolicy:
    """
    Build ImportPolicy from repository state.

    Args:
        repo_root: Repository root path.

    Returns:
        ImportPolicy with allowed imports.

    Maximum hardness:
    - Internal imports allowed only under 'farfan_core.*'.
    - Third-party imports allowed only if explicitly declared in dependency_lockdown.
    - Dynamic imports allowed only if explicitly declared in the same lockdown file (optional).
    """
    # Internal prefixes: explicit farfan_core namespace.
    allowed_internal: FrozenSet[str] = frozenset(
        {
            "farfan_core.core",
            "farfan_core.entrypoint",
            "farfan_core.scripts",
            "farfan_core.analysis",
            "farfan_core.audit",
            "farfan_core.observability",
            "farfan_core.utils",
            "farfan_core.scoring",
            "farfan_core.processing",
            "farfan_core.patterns",
            "farfan_core.infrastructure",
            "farfan_core.flux",
            "farfan_core.config",
            "farfan_core.controls",
            "farfan_core.concurrency",
            "farfan_core.optimization",
            "farfan_core.api",
            "farfan_core",
        }
    )

    # Stdlib modules set
    stdlib: FrozenSet[str] = (
        frozenset(sys.stdlib_module_names)
        if hasattr(sys, "stdlib_module_names")
        else frozenset()
    )

    # Third-party lockdown (MUST exist)
    allowed_third_party: FrozenSet[str] = _load_third_party_from_lockdown(repo_root)

    # Dynamic imports: default empty, but can be extended in lockdown config
    allowed_dynamic: Set[str] = set()
    try:
        from farfan_pipeline.config.dependency_lockdown import ALLOWED_DYNAMIC_IMPORTS  # type: ignore[attr-defined]

        allowed_dynamic.update(ALLOWED_DYNAMIC_IMPORTS)
    except Exception:
        # Optional; absence means "no dynamic imports whitelisted"
        pass

    return ImportPolicy(
        allowed_internal_prefixes=allowed_internal,
        allowed_third_party=allowed_third_party,
        allowed_dynamic_imports=frozenset(allowed_dynamic),
        stdlib_modules=stdlib,
    )


def build_path_policy(repo_root: Path) -> PathPolicy:
    """
    Build PathPolicy from repository state.

    Args:
        repo_root: Repository root path.

    Returns:
        PathPolicy with allowed paths.

    Maximum hardness:
    - Writes allowed only under known artifact/log/output dirs (or explicit external prefixes).
    - Reads allowed only under repo_root or explicit external prefixes.
    """
    # Allowed write prefixes (where artifacts / logs / outputs can be written)
    allowed_write: FrozenSet[Path] = frozenset(
        {
            repo_root / "artifacts",
            repo_root / "logs",
            repo_root / "output",
        }
    )

    # Allowed read prefixes: entire repo
    allowed_read: FrozenSet[Path] = frozenset(
        {
            repo_root,
        }
    )

    # Allowed external prefixes (outside repo)
    external_paths: Set[Path] = set()

    # Temp directory
    external_paths.add(Path(tempfile.gettempdir()))

    # Site-packages (installed dependencies)
    try:
        for site_dir in site.getsitepackages():
            external_paths.add(Path(site_dir))
    except Exception:
        # getsitepackages may not exist in some environments (e.g. venvs)
        pass

    # User site-packages
    try:
        if site.ENABLE_USER_SITE:
            user_site = site.getusersitepackages()
            if user_site:
                external_paths.add(Path(user_site))
    except Exception:
        pass

    allowed_external: FrozenSet[Path] = frozenset(external_paths)

    return PathPolicy(
        repo_root=repo_root,
        allowed_write_prefixes=allowed_write,
        allowed_read_prefixes=allowed_read,
        allowed_external_prefixes=allowed_external,
    )