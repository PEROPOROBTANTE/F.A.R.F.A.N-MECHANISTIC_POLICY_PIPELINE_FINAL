"""Import every module in key packages to surface hidden errors."""
from __future__ import annotations

import importlib
import pkgutil
import sys
import traceback
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent

PKG_PREFIXES: Sequence[str] = ("saaaaaa.core.", "saaaaaa.core.orchestrator.executors.", "saaaaaa.core.orchestrator.")

def _iter_modules(prefix: str, errors: list[tuple[str, BaseException, str]]) -> Iterator[str]:
    module_name = prefix[:-1]
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # pragma: no cover - defensive logging
        errors.append((module_name, exc, traceback.format_exc()))
        return
    if hasattr(module, "__path__"):
        for _, name, _ in pkgutil.walk_packages(module.__path__, prefix=prefix):
            yield name

def collect_modules(prefixes: Iterable[str], errors: list[tuple[str, BaseException, str]]) -> list[str]:
    modules = set()
    for prefix in prefixes:
        for name in _iter_modules(prefix, errors):
            modules.add(name)
    return sorted(modules)

def main() -> None:
    errors: list[tuple[str, BaseException, str]] = []
    dependency_errors: list[tuple[str, BaseException, str]] = []
    modules = collect_modules(PKG_PREFIXES, errors)
    
    for module_name in modules:
        try:
            importlib.import_module(module_name)
        except ModuleNotFoundError as exc:  # pragma: no cover - dependency issues
            # Separate dependency errors from architecture issues
            # Check if the missing module is an external dependency (has exc.name attribute)
            missing_name = getattr(exc, "name", str(exc).split("'")[1] if "'" in str(exc) else "")
            # If it's not one of our packages, it's a dependency error
            is_external = missing_name and not any(
                missing_name.startswith(p) for p in ["saaaaaa.core", "saaaaaa.orchestrator", "saaaaaa.executors"]
            )
            if is_external:
                dependency_errors.append((module_name, exc, traceback.format_exc()))
            else:
                errors.append((module_name, exc, traceback.format_exc()))
        except Exception as exc:  # pragma: no cover - enumerating failures
            errors.append((module_name, exc, traceback.format_exc()))
    
    if dependency_errors:
        print("=== DEPENDENCY ERRORS (Install requirements.txt to resolve) ===")
        for idx, (name, error, _) in enumerate(dependency_errors, start=1):
            print(f"[{idx}] {name}: {error}")
    
    if errors:
        print("\n=== IMPORT ERRORS (Architecture/Code Issues) ===")
        for idx, (name, error, tb) in enumerate(errors, start=1):
            print(f"[{idx}] {name}: {error}\n{tb}")
        raise SystemExit(1)
    
    imported_count = len(modules) - len(dependency_errors)
    print(f"Successfully imported {imported_count} modules cleanly.")
    if dependency_errors:
        print(f"Skipped {len(dependency_errors)} modules due to missing dependencies.")

if __name__ == "__main__":  # pragma: no cover
    main()
