"""Architecture guardrail tests for pure core modules and layering.

This module enforces the architectural guardrails requested by the
refactoring plan:

* Every ``saaaaaa.core`` module must be importable without crashing.
* Pure library modules must stay free from ``__main__`` blocks and direct I/O.
* ``import-linter`` layer contracts must remain satisfied when available.
"""

from __future__ import annotations

import ast
import importlib
import importlib.util
import pkgutil
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterable

# Define the package root directory
REPO_ROOT = Path(__file__).parent.parent
PACKAGE_ROOT = Path(__file__).parent.parent / "src" / "saaaaaa"

# Modules that must stay pure (no __main__ and no direct I/O).
PURE_MODULE_PATHS: dict[str, Path] = {
    "saaaaaa.processing.embedding_policy": PACKAGE_ROOT / "processing" / "embedding_policy.py",
}

# Legacy modules still undergoing I/O migration. We record them so that the
# detector can surface the locations without failing the build yet.
LEGACY_IO_MODULES: dict[str, Path] = {
    "saaaaaa.analysis.Analyzer_one": PACKAGE_ROOT / "analysis" / "Analyzer_one.py",
    "saaaaaa.analysis.derek_beach": PACKAGE_ROOT / "analysis" / "derek_beach.py",
    "saaaaaa.analysis.financiero_viabilidad_tablas": PACKAGE_ROOT / "analysis" / "financiero_viabilidad_tablas.py",
    "saaaaaa.analysis.teoria_cambio": PACKAGE_ROOT / "analysis" / "teoria_cambio.py",
    "saaaaaa.analysis.contradiction_deteccion": PACKAGE_ROOT / "analysis" / "contradiction_deteccion.py",
    "saaaaaa.processing.semantic_chunking_policy": PACKAGE_ROOT / "processing" / "semantic_chunking_policy.py",
}

class _IODetector(ast.NodeVisitor):
    """AST visitor that flags direct file/network I/O usage."""

    IO_FUNCTIONS = {
        "open",
        "read",
        "write",
        "load",
        "dump",
        "loads",
        "dumps",
        "read_csv",
        "read_excel",
        "read_json",
        "read_sql",
        "read_parquet",
        "to_csv",
        "to_excel",
        "to_json",
        "to_sql",
        "to_parquet",
    }
    IO_MODULES = {"pickle", "json", "yaml", "toml", "pathlib"}

    def __init__(self) -> None:
        self.matches: list[int] = []

    def visit_Call(self, node: ast.Call) -> None:  # pragma: no cover - simple visitor
        func = node.func
        if isinstance(func, ast.Name):
            if func.id in self.IO_FUNCTIONS:
                self.matches.append(node.lineno)
        elif isinstance(func, ast.Attribute) and isinstance(func.attr, str):
            if func.attr in self.IO_FUNCTIONS or isinstance(func.value, ast.Name) and func.value.id in self.IO_MODULES:
                self.matches.append(node.lineno)
        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:  # pragma: no cover - simple visitor
        for item in node.items:
            ctx = item.context_expr
            if isinstance(ctx, ast.Call) and isinstance(ctx.func, ast.Name):
                if ctx.func.id == "open":
                    self.matches.append(node.lineno)
        self.generic_visit(node)

class _MainDetector(ast.NodeVisitor):
    """AST visitor that flags ``if __name__ == '__main__'`` blocks."""

    def __init__(self) -> None:
        self.locations: list[int] = []

    def visit_If(self, node: ast.If) -> None:  # pragma: no cover - simple visitor
        test = node.test
        if (
            isinstance(test, ast.Compare)
            and isinstance(test.left, ast.Name)
            and test.left.id == "__name__"
        ):
            for comparator in test.comparators:
                if isinstance(comparator, ast.Constant) and comparator.value == "__main__":
                    self.locations.append(node.lineno)
        self.generic_visit(node)

def _load_source(path: Path) -> ast.AST:
    with path.open("r", encoding="utf-8") as handle:
        source = handle.read()
    try:
        return ast.parse(source, filename=str(path))
    except SyntaxError as exc:  # pragma: no cover - sanity guard
        pytest.fail(f"Syntax error while parsing {path}: {exc}")

def _iter_core_modules() -> Iterable[str]:
    package_path = PACKAGE_ROOT / "core"
    for module_info in pkgutil.walk_packages([str(package_path)], prefix="saaaaaa.core."):
        if not module_info.ispkg:
            yield module_info.name

@pytest.mark.parametrize("module_name", sorted(_iter_core_modules()))
def test_core_modules_import_cleanly(module_name: str) -> None:
    """Every module inside ``saaaaaa.core`` must be importable."""

    spec = importlib.util.find_spec(module_name)
    if spec is None:
        pytest.fail(f"Cannot find module {module_name} on sys.path")

    try:
        importlib.import_module(module_name)
    except ImportError as exc:  # pragma: no cover - exercised only when failing
        pytest.fail(f"Importing {module_name} failed: {exc}")

@pytest.mark.parametrize("qualified_name, path", sorted(PURE_MODULE_PATHS.items()))
def test_pure_modules_have_no_main_blocks(qualified_name: str, path: Path) -> None:
    tree = _load_source(path)
    detector = _MainDetector()
    detector.visit(tree)
    assert not detector.locations, (
        f"{qualified_name} contains __main__ guards at lines {detector.locations}. "
        "Pure modules must not ship executable entry points."
    )

@pytest.mark.parametrize("qualified_name, path", sorted({
    **PURE_MODULE_PATHS,
    **LEGACY_IO_MODULES,
}.items()))
def test_ast_scanner_reports_io_usage(qualified_name: str, path: Path) -> None:
    """Detect direct I/O in core analysis modules."""

    if not path.exists():
        pytest.skip(f"Module file for {qualified_name} is missing")

    tree = _load_source(path)
    detector = _IODetector()
    detector.visit(tree)
    if qualified_name in LEGACY_IO_MODULES:
        if detector.matches:
            pytest.skip(
                f"{qualified_name} still performs I/O at lines {detector.matches[:10]}. "
                "Track migrations before flipping this test to strict mode."
            )
        return

    assert not detector.matches, (
        f"{qualified_name} contains I/O operations at lines {detector.matches}. "
        "Core libraries must remain pure."
    )

def test_import_linter_layer_contract(tmp_path: Path) -> None:
    """Run a lightweight import-linter contract when the tool is available."""

    if importlib.util.find_spec("importlinter") is None:
        pytest.skip("import-linter is not installed in this environment")

    config = tmp_path / "importlinter.ini"
    config.write_text(
        """
[importlinter]
root_package = saaaaaa

[contract:core-does-not-import-tests]
name = Core package must not import tests
type = forbidden
source_modules =
    saaaaaa.core
forbidden_modules =
    tests
    saaaaaa.tests
        """.strip()
    )

    completed = subprocess.run(
        [sys.executable, "-m", "importlinter", "contracts", "--config", str(config)],
        cwd=str(REPO_ROOT),
        check=False,
        capture_output=True,
        text=True,
    )

    if completed.returncode == 2:
        pytest.skip("import-linter not configured correctly in this environment")

    stdout = completed.stdout + completed.stderr
    assert completed.returncode == 0, (
        "import-linter detected a layering violation:\n" + stdout
    )

def test_boundary_scanner_tool_exists() -> None:
    scanner_path = REPO_ROOT / "tools" / "scan_boundaries.py"
    assert scanner_path.exists(), "Boundary scanner tool not found"
    _ = _load_source(scanner_path)
