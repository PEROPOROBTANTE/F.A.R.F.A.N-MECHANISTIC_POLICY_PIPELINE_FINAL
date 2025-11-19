"""
Safe Import System - Deterministic, Auditable, Portable

This module implements the core import safety layer for the SAAAAAA system.
All imports in the codebase should use this pattern for optional dependencies,
ensuring fail-fast behavior, clear error messages, and no graceful degradation.

Design Principles:
- No silent failures - imports either succeed completely or fail loudly
- No graceful degradation - partial functionality is rejected
- Deterministic behavior - same inputs always produce same outputs
- Explicit error messages with installation hints
- Support for alternative packages (e.g., tomllib vs tomli)
"""

from __future__ import annotations

import importlib
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import types


class ImportErrorDetailed(ImportError):
    """
    Enhanced import error with context and actionable guidance.

    This exception is raised when a required import fails and provides:
    - The module that failed to import
    - Installation instructions or hints
    - Alternative packages if available
    - Context about why the import is needed
    """

    def __init__(self, module_name: str, hint: str = "", install_cmd: str = "") -> None:
        """
        Initialize detailed import error.

        Parameters
        ----------
        module_name : str
            Name of the module that failed to import
        hint : str, optional
            Human-readable context about why this module is needed
        install_cmd : str, optional
            Installation command to resolve the missing dependency
        """
        parts = [f"Failed to import '{module_name}'"]

        if hint:
            parts.append(f"Context: {hint}")

        if install_cmd:
            parts.append(f"Install with: {install_cmd}")

        message = ". ".join(parts)
        super().__init__(message)

        self.module_name = module_name
        self.hint = hint
        self.install_cmd = install_cmd


def try_import(
    modname: str,
    *,
    required: bool = False,
    hint: str = "",
    alt: str | None = None,
) -> types.ModuleType | None:
    """
    Attempt to import a module with explicit error handling and guidance.

    This function provides controlled import behavior with clear failure modes:
    - Required imports fail immediately with detailed errors
    - Optional imports log warnings and return None
    - Alternative packages are tried if primary fails
    - All failures include installation hints

    Parameters
    ----------
    modname : str
        The fully qualified module name to import (e.g., 'httpx', 'polars')
    required : bool, default=False
        If True, raises ImportErrorDetailed on failure
        If False, logs to stderr and returns None
    hint : str, default=""
        Human-readable guidance for resolving the import failure
        Should include installation command or extra flag
        Example: "Install extra 'http_signals' or set source=memory://"
    alt : str | None, default=None
        Alternative module to try if primary fails
        Example: 'tomli' as alternative to 'tomllib'

    Returns
    -------
    types.ModuleType | None
        The imported module if successful, None if optional and failed

    Raises
    ------
    ImportErrorDetailed
        When required=True and import fails (including alternatives)

    Examples
    --------
    >>> # Optional dependency with hint
    >>> httpx = try_import("httpx", required=False, hint="Install extra 'http_signals'")
    >>> if httpx is None:
    ...     # Use memory:// source instead
    ...     pass

    >>> # Required dependency
    >>> pyarrow = try_import("pyarrow", required=True, hint="Install core runtime")

    >>> # Version-specific with fallback
    >>> toml = try_import("tomllib", alt="tomli", required=True,
    ...                   hint="Python<3.11 needs 'tomli'")

    Notes
    -----
    - This function must NEVER silently substitute mock objects
    - Failure modes must be explicit and actionable
    - Import-time side effects in target modules are NOT controlled here
    - This is NOT for lazy loading - use separate lazy_import() for that
    """
    try:
        return importlib.import_module(modname)
    except Exception as primary_error:
        msg = f"[IMPORT] Failed '{modname}'"

        # Try alternative package if specified
        if alt:
            try:
                return importlib.import_module(alt)
            except Exception as alt_error:
                # Both primary and alternative failed
                combined_error = ImportErrorDetailed(
                    modname, hint=f"{hint}; alternative '{alt}' also failed"
                )
                combined_error.__cause__ = alt_error

                if required:
                    raise combined_error from primary_error
                else:
                    sys.stderr.write(f"{msg} (optional); alt also failed. {hint}\n")
                    return None

        # Required import failed - abort immediately
        if required:
            raise ImportErrorDetailed(modname, hint=hint) from primary_error

        # Optional dependency: log and defer failure to call site
        # This allows the module to load but fail when the feature is used
        sys.stderr.write(f"{msg} (optional). {hint}\n")
        return None


def check_import_available(modname: str) -> bool:
    """
    Check if a module can be imported without actually importing it.

    This is useful for feature flags and conditional code paths without
    triggering import-time side effects.

    Parameters
    ----------
    modname : str
        The fully qualified module name to check

    Returns
    -------
    bool
        True if module can be imported, False otherwise

    Examples
    --------
    >>> if check_import_available("polars"):
    ...     # Use polars backend
    ...     pass
    >>> else:
    ...     # Fall back to pandas
    ...     pass
    """
    try:
        spec = importlib.util.find_spec(modname)
        return spec is not None
    except (ImportError, ModuleNotFoundError, ValueError, AttributeError):
        return False


def get_import_version(modname: str) -> str | None:
    """
    Get the version of an installed module without importing it.

    This uses metadata inspection to avoid import-time side effects.

    Parameters
    ----------
    modname : str
        The module/package name

    Returns
    -------
    str | None
        Version string if available, None otherwise

    Examples
    --------
    >>> get_import_version("numpy")
    '1.26.4'
    """
    try:
        # Python 3.8+ has importlib.metadata
        from importlib.metadata import version  # type: ignore
        return version(modname)
    except Exception:
        return None


# Cache for lazy-loaded modules to ensure deterministic re-import
_lazy_cache: dict[str, types.ModuleType | None] = {}


def lazy_import(modname: str, *, hint: str = "") -> types.ModuleType:
    """
    Lazy-load a module with memoization for deterministic behavior.

    This is for import-time budget optimization on heavy modules.
    Use this in functions that are called infrequently or in cold paths.

    Parameters
    ----------
    modname : str
        Module to lazy-load
    hint : str, default=""
        Installation hint if import fails

    Returns
    -------
    types.ModuleType
        The imported module (cached after first call)

    Raises
    ------
    ImportErrorDetailed
        If the module cannot be imported

    Examples
    --------
    >>> def to_arrow(df):
    ...     pa = lazy_import("pyarrow", hint="Install core runtime")
    ...     return pa.table(df)

    Notes
    -----
    - Memoization ensures the module is only loaded once
    - Cache is module-global, not process-global
    - This does NOT avoid import-time side effects, just defers them
    """
    if modname in _lazy_cache:
        cached = _lazy_cache[modname]
        if cached is None:
            raise ImportErrorDetailed(f"[IMPORT] Module '{modname}' previously failed")
        return cached

    try:
        mod = importlib.import_module(modname)
        _lazy_cache[modname] = mod
        return mod
    except Exception as e:
        _lazy_cache[modname] = None
        msg = f"[IMPORT] Failed lazy import of '{modname}'"
        if hint:
            msg += f". {hint}"
        raise ImportErrorDetailed(msg) from e
