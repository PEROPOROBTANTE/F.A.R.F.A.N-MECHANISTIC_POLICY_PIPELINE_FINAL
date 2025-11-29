"""
Portable, secure, and deterministic path utilities for SAAAAAA.

This module provides cross-platform path operations that ensure:
- Portability across Linux, macOS, and Windows
- Security through path traversal protection
- Determinism via normalized paths
- Controlled write locations (never in source tree)

All path operations in the repository MUST use these utilities instead of:
- Direct __file__ usage for resource access
- sys.path manipulation
- Hardcoded absolute paths
- os.path functions (use pathlib.Path instead)
"""

from __future__ import annotations

import os
import unicodedata
from pathlib import Path
from typing import Final
from saaaaaa.core.calibration.decorators import calibrated_method


# Custom exception types for path errors
class PathError(Exception):
    """Base exception for path-related errors."""
    pass


class PathTraversalError(PathError):
    """Raised when a path attempts to escape workspace boundaries."""
    pass


class PathNotFoundError(PathError):
    """Raised when a required path does not exist."""
    pass


class PathOutsideWorkspaceError(PathError):
    """Raised when a path is outside the allowed workspace."""
    pass


class UnnormalizedPathError(PathError):
    """Raised when a path is not properly normalized."""
    pass


# Project root detection - computed once at module load
def _detect_project_root() -> Path:
    """
    Detect the project root directory using filesystem markers.

    This function uses a multi-strategy approach to locate the project root:

    1. Primary strategy: Search for pyproject.toml
       - Walks up the directory tree from this file's location
       - Returns the first directory containing pyproject.toml

    2. Secondary strategy: Search for src/saaaaaa layout
       - Looks for directories with both src/saaaaaa and setup.py
       - This supports older project structures

    3. Fallback strategy: Relative path calculation
       - If no markers found, assumes standard layout (src/saaaaaa/utils)
       - Returns path 3 levels up from this file

    The function is called once at module load time, and the result is
    cached in the PROJECT_ROOT constant.

    Returns:
        Path: Absolute path to the project root directory

    Raises:
        No exceptions raised; always returns a path (uses fallback if needed)

    Note:
        This function is intended for internal use. External code should use
        the PROJECT_ROOT constant instead of calling this directly.
    """
    # Start from this file's location
    current = Path(__file__).resolve().parent

    # Walk up to find pyproject.toml
    for parent in [current] + list(current.parents):
        if (parent / "pyproject.toml").exists():
            return parent
        if (parent / "src" / "saaaaaa").exists() and (parent / "setup.py").exists():
            return parent

    # Fallback: if we can't find it, assume we're in src/saaaaaa/utils
    # and go up 3 levels
    return current.parent.parent.parent


# Global constants for common directories
PROJECT_ROOT: Final[Path] = _detect_project_root()
SRC_DIR: Final[Path] = PROJECT_ROOT / "src"
DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
TESTS_DIR: Final[Path] = PROJECT_ROOT / "tests"


def proj_root() -> Path:
    """
    Get the project root directory.

    Returns:
        Absolute path to the project root (where pyproject.toml lives)
    """
    return PROJECT_ROOT


def src_dir() -> Path:
    """Get the src directory path."""
    return SRC_DIR


def data_dir() -> Path:
    """
    Get the data directory path.
    Creates it if it doesn't exist.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


def tmp_dir() -> Path:
    """
    Get a project-specific temporary directory.

    Uses PROJECT_ROOT/tmp to keep temporary files within the workspace
    and avoid polluting system temp directories.

    Returns:
        Path to tmp directory (created if needed)
    """
    tmp = PROJECT_ROOT / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    return tmp


def build_dir() -> Path:
    """
    Get the build directory for generated artifacts.

    Returns:
        Path to build directory (created if needed)
    """
    build = PROJECT_ROOT / "build"
    build.mkdir(parents=True, exist_ok=True)
    return build


def cache_dir() -> Path:
    """
    Get the cache directory.

    Returns:
        Path to cache directory (created if needed)
    """
    cache = build_dir() / "cache"
    cache.mkdir(parents=True, exist_ok=True)
    return cache


def reports_dir() -> Path:
    """
    Get the reports directory for generated reports.

    Returns:
        Path to reports directory (created if needed)
    """
    reports = build_dir() / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    return reports


def is_within(base: Path, child: Path) -> bool:
    """
    Check if child path is within base directory (no traversal outside).

    Args:
        base: Base directory that should contain child
        child: Path to check

    Returns:
        True if child is within base, False otherwise

    Example:
        >>> project_root = Path("project_root")
        >>> is_within(project_root, project_root / "src" / "file.py")
        True
        >>> other_root = Path("other_project")
        >>> is_within(project_root, other_root / "file.py")
        False
    """
    try:
        base_resolved = base.resolve()
        child_resolved = child.resolve()

        # Check if child is relative to base
        child_resolved.relative_to(base_resolved)
        return True
    except (ValueError, RuntimeError):
        return False


def safe_join(base: Path, *parts: str) -> Path:
    """
    Safely join path components, preventing traversal outside base.

    This prevents directory traversal attacks using ".." components.

    Args:
        base: Base directory
        *parts: Path components to join

    Returns:
        Resolved path within base

    Raises:
        PathTraversalError: If the resulting path would be outside base

    Example:
        >>> project_root = Path("project_root")
        >>> safe_join(project_root, "src", "file.py")
        project_root/src/file.py
        >>> safe_join(project_root, "..", "other")  # raises
        PathTraversalError
    """
    result = base.joinpath(*parts).resolve()

    if not is_within(base, result):
        raise PathTraversalError(
            f"Path traversal detected: '{result}' is outside base '{base}'. "
            f"Use paths within the workspace."
        )

    return result


def normalize_unicode(path: Path, form: str = "NFC") -> Path:
    """
    Normalize Unicode in path for cross-platform consistency.

    Different filesystems handle Unicode differently:
    - macOS (HFS+) uses NFD normalization
    - Linux typically uses NFC
    - Windows uses UTF-16

    Args:
        path: Path to normalize
        form: Unicode normalization form ("NFC", "NFD", "NFKC", "NFKD")
              Default "NFC" for maximum compatibility

    Returns:
        Path with normalized Unicode
    """
    normalized_str = unicodedata.normalize(form, str(path))
    return Path(normalized_str)


def normalize_case(path: Path) -> Path:
    """
    Normalize path case for case-insensitive filesystems.

    On case-insensitive filesystems (Windows, macOS default), this ensures
    consistent casing. On case-sensitive systems (Linux), returns unchanged.

    Args:
        path: Path to normalize

    Returns:
        Path with normalized case
    """
    # Check if filesystem is case-sensitive
    # This is a heuristic - we check if we can create files differing only in case
    if path.exists():
        # Use actual case from filesystem
        try:
            # On Windows/macOS this will resolve to actual case
            return path.resolve()
        except Exception:
            pass

    return path


def resources(package: str, *path_parts: str) -> Path:
    """
    Access packaged resource files in a portable way.

    This uses importlib.resources (Python 3.9+) to access resources that
    are included in the installed package, whether from source or wheel.

    Args:
        package: Package name (e.g., "saaaaaa.core")
        *path_parts: Path components within the package

    Returns:
        Path to the resource

    Raises:
        PathNotFoundError: If resource doesn't exist

    Example:
        >>> resources("saaaaaa.core", "config", "default.yaml")
        Path('/path/to/saaaaaa/core/config/default.yaml')
    """
    try:
        # Python 3.9+ way
        from importlib.resources import files

        pkg_path = files(package)
        for part in path_parts:
            pkg_path = pkg_path.joinpath(part)

        # Convert to Path - files() returns Traversable
        if hasattr(pkg_path, '__fspath__'):
            return Path(pkg_path)
        else:
            # Fallback for Traversable that doesn't support __fspath__
            # Read the resource and return a path to it
            raise PathNotFoundError(
                f"Resource '{'.'.join(path_parts)}' in package '{package}' "
                f"is not accessible as a filesystem path. "
                f"Consider using importlib.resources.read_text() or read_binary() instead."
            )
    except (ImportError, ModuleNotFoundError, FileNotFoundError, TypeError) as e:
        raise PathNotFoundError(
            f"Resource '{'/'.join(path_parts)}' not found in package '{package}'. "
            f"Ensure it's declared in pyproject.toml [tool.setuptools.package-data]. "
            f"Error: {e}"
        ) from e


def validate_read_path(path: Path) -> None:
    """
    Validate a path before reading from it.

    Args:
        path: Path to validate

    Raises:
        PathNotFoundError: If path doesn't exist
        PermissionError: If path is not readable
    """
    if not path.exists():
        raise PathNotFoundError(f"Path does not exist: '{path}'")

    if not os.access(path, os.R_OK):
        raise PermissionError(f"Path is not readable: '{path}'")


def validate_write_path(path: Path, allow_source_tree: bool = False) -> None:
    """
    Validate a path before writing to it.

    By default, prohibits writing to the source tree to prevent
    accidental modification of versioned code.

    Args:
        path: Path to validate
        allow_source_tree: If True, allow writing to source tree
                          (for special cases like code generation)

    Raises:
        PathOutsideWorkspaceError: If path is outside workspace
        PermissionError: If parent directory is not writable
        ValueError: If trying to write to source tree when not allowed
    """
    # Ensure it's within the workspace
    if not is_within(PROJECT_ROOT, path):
        raise PathOutsideWorkspaceError(
            f"Cannot write to '{path}' - outside workspace '{PROJECT_ROOT}'"
        )

    # Prohibit writing to source tree unless explicitly allowed
    if not allow_source_tree and is_within(SRC_DIR, path):
        raise ValueError(
            f"Cannot write to source tree: '{path}'. "
            f"Write to build/, cache/, or reports/ instead. "
            f"If you need to write to source (e.g., code generation), "
            f"set allow_source_tree=True."
        )

    # Ensure parent directory exists and is writable
    parent = path.parent
    if parent.exists() and not os.access(parent, os.W_OK):
        raise PermissionError(f"Parent directory is not writable: '{parent}'")


# Environment variable accessors (typed and safe)

def get_env_path(key: str, default: Path | None = None) -> Path | None:
    """
    Get a path from environment variable.

    Args:
        key: Environment variable name
        default: Default value if not set

    Returns:
        Path from environment or default
    """
    value = os.getenv(key)
    if value is None:
        return default
    return Path(value).resolve()


def get_workdir() -> Path:
    """
    Get the working directory from FLUX_WORKDIR env var or default to project root.
    """
    return get_env_path("FLUX_WORKDIR", PROJECT_ROOT) or PROJECT_ROOT


def get_tmpdir() -> Path:
    """
    Get the temporary directory from FLUX_TMPDIR env var or default to project tmp.
    """
    result = get_env_path("FLUX_TMPDIR", tmp_dir()) or tmp_dir()
    result.mkdir(parents=True, exist_ok=True)
    return result


def get_reports_dir() -> Path:
    """
    Get the reports directory from FLUX_REPORTS env var or default to build/reports.
    """
    result = get_env_path("FLUX_REPORTS", reports_dir()) or reports_dir()
    result.mkdir(parents=True, exist_ok=True)
    return result


__all__ = [
    # Exceptions
    "PathError",
    "PathTraversalError",
    "PathNotFoundError",
    "PathOutsideWorkspaceError",
    "UnnormalizedPathError",
    # Constants
    "PROJECT_ROOT",
    "SRC_DIR",
    "DATA_DIR",
    "TESTS_DIR",
    # Directory accessors
    "proj_root",
    "src_dir",
    "data_dir",
    "tmp_dir",
    "build_dir",
    "cache_dir",
    "reports_dir",
    # Path operations
    "is_within",
    "safe_join",
    "normalize_unicode",
    "normalize_case",
    "resources",
    # Validation
    "validate_read_path",
    "validate_write_path",
    # Environment
    "get_env_path",
    "get_workdir",
    "get_tmpdir",
    "get_reports_dir",
]
