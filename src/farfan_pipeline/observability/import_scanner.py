"""
Import Scanner

AST-based static analysis of import statements.
Validates imports against ImportPolicy without executing code.

"Maximum hardness" semantics:
- Any import that cannot be resolved to:
    - an internal farfan_core.* module, OR
    - a stdlib module, OR
    - an explicitly allowed third-party module
  is a violation.
- Any file that cannot be read or parsed is a violation.
- Any relative import that cannot be resolved to an absolute module name is a violation.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterable, Optional

from .path_import_policy import ImportPolicy, PolicyReport, PolicyViolation


def _is_stdlib_module(module_name: str, stdlib_modules: frozenset[str]) -> bool:
    """Check if module is from stdlib (module or any parent package)."""
    if module_name in stdlib_modules:
        return True

    parts = module_name.split(".")
    for i in range(1, len(parts)):
        candidate = ".".join(parts[: i + 1])
        if candidate in stdlib_modules:
            return True

    return False


def _is_internal_module(module_name: str, allowed_prefixes: frozenset[str]) -> bool:
    """Check if module is internal (starts with any allowed prefix)."""
    for prefix in allowed_prefixes:
        if module_name == prefix or module_name.startswith(prefix + "."):
            return True
    return False


def _is_allowed_third_party(module_name: str, allowed_third_party: frozenset[str]) -> bool:
    """Check if module is an allowed third-party module or submodule."""
    parts = module_name.split(".")

    # Try longest prefix → shortest (e.g. foo.bar.baz → foo.bar.baz, foo.bar, foo)
    for i in range(len(parts), 0, -1):
        candidate = ".".join(parts[:i])
        if candidate in allowed_third_party:
            return True

    # As a last resort, allow if any single segment is explicitly whitelisted
    for part in parts:
        if part in allowed_third_party:
            return True

    return False


def _validate_import(
    module_name: str,
    policy: ImportPolicy,
    file_path: Path,
    line_number: int,
) -> Optional[PolicyViolation]:
    """
    Validate a single import against policy.

    Returns:
        PolicyViolation if import violates policy, None otherwise.
    """
    if not module_name:
        return None

    # Internal?
    if _is_internal_module(module_name, policy.allowed_internal_prefixes):
        return None

    # Stdlib?
    if _is_stdlib_module(module_name, policy.stdlib_modules):
        return None

    # Third-party?
    if _is_allowed_third_party(module_name, policy.allowed_third_party):
        return None

    # Otherwise: violation
    return PolicyViolation(
        kind="static_import",
        message=f"Import '{module_name}' not allowed by ImportPolicy",
        file=file_path,
        line=line_number,
        operation="import",
        target=module_name,
    )


def _module_name_from_path(py_file: Path, repo_root: Path) -> Optional[str]:
    """
    Compute fully-qualified module name for a given .py file
    assuming it lives under farfan_core/farfan_core.

    Example:
        <REPO>/farfan_core/farfan_core/core/foo/bar.py
        -> farfan_core.core.foo.bar
    """
    try:
        rel = py_file.resolve().relative_to(repo_root)
    except Exception:
        return None

    parts = rel.with_suffix("").parts  # drop ".py"
    if len(parts) >= 2 and parts[0] == "farfan_core" and parts[1] == "farfan_core":
        # ("farfan_core", "farfan_core", "core", "foo") -> "farfan_core.core.foo"
        return ".".join(("farfan_core",) + parts[2:])
    return None


def _resolve_from_import_module(
    node: ast.ImportFrom,
    current_module: Optional[str],
) -> Optional[str]:
    """
    Resolve absolute module name for a 'from ... import ...' statement.

    For absolute imports (level == 0), returns node.module.
    For relative imports (level > 0), uses current_module as base.

    If resolution is ambiguous or impossible, returns None.
    """
    if node.level == 0:
        # from x import y
        return node.module or None

    if current_module is None:
        # Cannot resolve relative import without knowing current module
        return None

    base_parts = current_module.split(".")
    if len(base_parts) < node.level:
        # from ... import beyond root: ambiguous
        return None

    parent_parts = base_parts[: -node.level]

    if node.module:
        parent_parts.extend(node.module.split("."))

    return ".".join(parent_parts)


def validate_imports(
    roots: Iterable[Path],
    import_policy: ImportPolicy,
    repo_root: Path,
) -> PolicyReport:
    """
    Scan Python files under roots and validate imports.

    Args:
        roots: Directories to scan for .py files.
        import_policy: Policy defining allowed imports.
        repo_root: Repository root path, used to resolve module names from paths.

    Returns:
        PolicyReport with any static_import_violations found.
    """
    report = PolicyReport()

    for root in roots:
        if not root.exists():
            continue

        for py_file in root.rglob("*.py"):
            # Skip __pycache__
            if "__pycache__" in py_file.parts:
                continue

            try:
                source = py_file.read_text(encoding="utf-8")
            except Exception as e:
                # Treat unreadable files as violations, not silent skips
                report.static_import_violations.append(
                    PolicyViolation(
                        kind="static_import",
                        message=f"Failed to read file for import scan: {e}",
                        file=py_file,
                        line=None,
                        operation="read_source",
                        target=str(py_file),
                    )
                )
                continue

            try:
                tree = ast.parse(source, filename=str(py_file))
            except SyntaxError as e:
                report.static_import_violations.append(
                    PolicyViolation(
                        kind="static_import",
                        message=f"Syntax error while parsing for import scan: {e.msg}",
                        file=py_file,
                        line=e.lineno or None,
                        operation="parse",
                        target=str(py_file),
                    )
                )
                continue
            except Exception as e:
                report.static_import_violations.append(
                    PolicyViolation(
                        kind="static_import",
                        message=f"Unexpected error while parsing for import scan: {e}",
                        file=py_file,
                        line=None,
                        operation="parse",
                        target=str(py_file),
                    )
                )
                continue

            current_module = _module_name_from_path(py_file, repo_root)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name
                        violation = _validate_import(
                            module_name,
                            import_policy,
                            py_file,
                            node.lineno,
                        )
                        if violation:
                            report.static_import_violations.append(violation)

                elif isinstance(node, ast.ImportFrom):
                    abs_module = _resolve_from_import_module(node, current_module)
                    if not abs_module:
                        # Could not resolve; treat as a hard violation
                        report.static_import_violations.append(
                            PolicyViolation(
                                kind="static_import",
                                message=(
                                    "Unable to resolve relative import "
                                    f"(module={node.module!r}, level={node.level})"
                                ),
                                file=py_file,
                                line=node.lineno,
                                operation="import_from",
                                target=node.module or "",
                            )
                        )
                        continue

                    violation = _validate_import(
                        abs_module,
                        import_policy,
                        py_file,
                        node.lineno,
                    )
                    if violation:
                        report.static_import_violations.append(violation)

    return report