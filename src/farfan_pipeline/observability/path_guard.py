"""
Path Guard

Runtime interception of filesystem operations.
Validates paths against PathPolicy during execution.

NOTE:
This module is verification-focused: it logs violations into PolicyReport.
Whether to treat violations as hard failures is decided by the harness.
"""

from __future__ import annotations

import builtins
import os
from contextlib import contextmanager
from pathlib import Path

from .path_import_policy import ImportPolicy, PathPolicy, PolicyReport, PolicyViolation


def _is_under_prefixes(resolved: Path, prefixes: frozenset[Path]) -> bool:
    """Return True if 'resolved' is under any prefix in 'prefixes'."""
    for prefix in prefixes:
        try:
            resolved.relative_to(prefix)
            return True
        except ValueError:
            continue
    return False


def _path_allowed(
    path: Path,
    operation: str,
    policy: PathPolicy,
) -> tuple[bool, str | None]:
    """
    Check if path operation is allowed by policy.

    Args:
        path: Path being accessed.
        operation: "read" or "write".
        policy: PathPolicy to validate against.

    Returns:
        (allowed, error_message)
    """
    try:
        resolved = path.resolve()
    except Exception as e:
        return False, f"Cannot resolve path {path!r}: {e}"

    if operation == "write":
        if _is_under_prefixes(resolved, policy.allowed_write_prefixes) or _is_under_prefixes(
            resolved, policy.allowed_external_prefixes
        ):
            return True, None
        return False, f"Write not allowed: {resolved} not under allowed write prefixes"

    if operation == "read":
        if _is_under_prefixes(resolved, policy.allowed_read_prefixes) or _is_under_prefixes(
            resolved, policy.allowed_external_prefixes
        ):
            return True, None
        return False, f"Read not allowed: {resolved} not under allowed read prefixes"

    return True, None


@contextmanager
def guard_paths_and_imports(
    path_policy: PathPolicy,
    import_policy: ImportPolicy,  # kept for future dynamic-import guards
    report: PolicyReport,
):
    """
    Context manager that guards filesystem paths during execution.

    Args:
        path_policy: Policy for filesystem access.
        import_policy: Policy for imports (reserved for future dynamic import guards).
        report: PolicyReport to populate with violations.

    Note:
        This implementation logs violations but does not block execution by itself.
        The harness decides whether any violation is fatal.
    """
    original_open = builtins.open
    original_os_open = os.open

    in_guard = {"value": False}

    def guarded_open(file, mode="r", *args, **kwargs):
        if in_guard["value"]:
            return original_open(file, mode, *args, **kwargs)

        in_guard["value"] = True
        try:
            path = Path(file)
            is_write = any(m in mode for m in ("w", "a", "x", "+"))
            operation = "write" if is_write else "read"

            allowed, error_msg = _path_allowed(path, operation, path_policy)
            if not allowed:
                report.path_violations.append(
                    PolicyViolation(
                        kind="path",
                        message=error_msg or f"Path access violation: {operation}",
                        file=path,
                        line=None,
                        operation=operation,
                        target=str(path),
                    )
                )

            return original_open(file, mode, *args, **kwargs)
        finally:
            in_guard["value"] = False

    def guarded_os_open(path, flags, *args, **kwargs):
        if in_guard["value"]:
            return original_os_open(path, flags, *args, **kwargs)

        in_guard["value"] = True
        try:
            path_obj = Path(path)
            is_write = bool(
                flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
            )
            operation = "write" if is_write else "read"

            allowed, error_msg = _path_allowed(path_obj, operation, path_policy)
            if not allowed:
                report.path_violations.append(
                    PolicyViolation(
                        kind="path",
                        message=error_msg or f"Path access violation: {operation}",
                        file=path_obj,
                        line=None,
                        operation=operation,
                        target=str(path_obj),
                    )
                )

            return original_os_open(path, flags, *args, **kwargs)
        finally:
            in_guard["value"] = False

    builtins.open = guarded_open
    os.open = guarded_os_open

    try:
        yield
    finally:
        builtins.open = original_open
        os.open = original_os_open