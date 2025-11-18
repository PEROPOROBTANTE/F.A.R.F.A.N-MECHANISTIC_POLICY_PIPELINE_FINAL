"""
Compatibility Layer - Version Shims and Polyfills

This module provides a unified interface for Python version differences
and third-party package variations. All version-specific imports should
go through this layer.

Shims provided:
- tomllib/tomli (TOML parsing, Python 3.11+ vs earlier)
- importlib.resources (files() API, Python 3.9+ vs earlier)
- typing extensions (backports for older Python)
- typing (future annotations support)

Design:
- Explicit imports only (no star imports)
- Fail-fast on missing required compatibility
- Clear error messages with version requirements
"""

from __future__ import annotations

import sys
from typing import Any

# Lazy loading utilities for heavy dependencies
from .lazy_deps import (
    get_numpy,
    get_pandas,
    get_polars,
    get_pyarrow,
    get_spacy,
    get_torch,
    get_transformers,
)
from .safe_imports import (
    ImportErrorDetailed,
    check_import_available,
    get_import_version,
    lazy_import,
    try_import,
)

# Backward compatibility alias
OptionalDependencyError = ImportErrorDetailed

# Re-export safe import utilities and lazy deps
__all__ = [
    # Core import utilities
    "ImportErrorDetailed",
    "OptionalDependencyError",  # Backward compatibility alias
    "try_import",
    "lazy_import",
    "check_import_available",
    "get_import_version",
    # Version compatibility shims
    "tomllib",
    "resources_files",
    # Lazy loading utilities
    "get_numpy",
    "get_pandas",
    "get_polars",
    "get_pyarrow",
    "get_torch",
    "get_transformers",
    "get_spacy",
]


# ============================================================================
# TOML Parsing - Python 3.11+ tomllib vs tomli
# ============================================================================

if sys.version_info >= (3, 11):
    import tomllib
else:
    # Python < 3.11 needs tomli package
    # try_import with required=True will raise if missing
    tomllib = try_import(  # type: ignore[assignment]
        "tomli",
        required=True,
        hint="Python < 3.11 requires 'tomli' package. Install with: pip install tomli",
    )


# ============================================================================
# Importlib Resources - Python 3.9+ files() vs older resource API
# ============================================================================

try:
    from importlib.resources import files as resources_files
except ImportError:
    # Python < 3.9 needs importlib_resources backport
    # try_import with required=True will raise if missing
    _resources = try_import(
        "importlib_resources",
        required=True,
        hint="Python < 3.9 requires 'importlib_resources'. "
             "Install with: pip install importlib-resources",
    )
    resources_files = _resources.files  # type: ignore[attr-defined]


# ============================================================================
# Typing Extensions - Backports for older Python versions
# ============================================================================

# For maximum compatibility, we always try to import typing_extensions
# Even on Python 3.10+, typing_extensions provides latest features
_typing_extensions_available = check_import_available("typing_extensions")

if _typing_extensions_available:
    import typing_extensions

    # Use typing_extensions versions if available (they're usually more up-to-date)
    TypeAlias = typing_extensions.TypeAlias
    ParamSpec = typing_extensions.ParamSpec
    Concatenate = typing_extensions.Concatenate
    Literal = typing_extensions.Literal
    Protocol = typing_extensions.Protocol
    TypedDict = typing_extensions.TypedDict
    Final = typing_extensions.Final
    Annotated = typing_extensions.Annotated

else:
    # Fall back to stdlib typing
    # This may not have all features on older Python versions
    # TypeAlias added in 3.10
    from typing import (  # type: ignore[misc, assignment]
        Annotated,  # 3.9+
        Concatenate,
        Final,  # 3.8+
        Literal,  # 3.8+
        ParamSpec,
        Protocol,  # 3.8+
        TypeAlias,
        TypedDict,  # 3.8+
    )


# ============================================================================
# Platform Detection Utilities
# ============================================================================

def get_platform_info() -> dict[str, Any]:
    """
    Get comprehensive platform information for debugging.

    Returns
    -------
    dict[str, Any]
        Platform details including OS, architecture, Python version

    Examples
    --------
    >>> info = get_platform_info()
    >>> print(f"Running on {info['system']} {info['architecture']}")
    """
    import platform

    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "architecture": platform.machine(),
        "python_version": sys.version,
        "python_implementation": platform.python_implementation(),
        "python_version_tuple": sys.version_info[:3],
    }


def check_minimum_python_version(major: int, minor: int) -> bool:
    """
    Check if Python version meets minimum requirement.

    Parameters
    ----------
    major : int
        Required major version
    minor : int
        Required minor version

    Returns
    -------
    bool
        True if current version >= required version

    Examples
    --------
    >>> if not check_minimum_python_version(3, 10):
    ...     raise RuntimeError("Python 3.10+ required")
    """
    return sys.version_info >= (major, minor)


# ============================================================================
# Validation on Import
# ============================================================================

# Ensure minimum Python version (as specified in pyproject.toml)
if not check_minimum_python_version(3, 10):
    raise ImportErrorDetailed(
        f"Python 3.10 or later required. Current version: {sys.version}. "
        "Please upgrade Python or use a compatible environment."
    )
