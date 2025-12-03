"""Import Linter contract that forbids relative imports in farfan_pipeline."""

from __future__ import annotations

import ast
import importlib
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

from grimp import ImportGraph

from importlinter.application import output
from importlinter.domain.contract import Contract, ContractCheck, InvalidContractOptions

RelativeImport = Tuple[str, int, str]


class NoRelativeImportsContract(Contract):
    """Contract that fails if any relative imports are present."""

    def check(self, graph: ImportGraph, verbose: bool) -> ContractCheck:
        package_paths = self._get_package_paths()

        output.verbose_print(verbose, f"Scanning {len(package_paths)} root packages for relatives.")

        violations: list[RelativeImport] = []
        for package_name, package_path in package_paths:
            output.verbose_print(verbose, f"  -> {package_name} ({package_path})")
            violations.extend(self._scan_package(package_path))

        violations.sort(key=lambda item: (item[0], item[1]))
        return ContractCheck(kept=not violations, metadata={"violations": violations})

    def render_broken_contract(self, check: ContractCheck) -> None:
        violations: Sequence[RelativeImport] = check.metadata.get("violations", [])
        output.print_error("Relative imports detected (use absolute farfan_pipeline.* paths):")
        for path, line, statement in violations:
            output.print(f"  {path}:{line}: {statement}")

    def _get_package_paths(self) -> List[tuple[str, Path]]:
        """Resolve filesystem paths for configured root packages."""
        package_paths: list[tuple[str, Path]] = []
        for package_name in self.session_options.get("root_packages", []):
            try:
                module = importlib.import_module(package_name)
            except ModuleNotFoundError as exc:
                raise InvalidContractOptions(
                    {package_name: f"Cannot import root package '{package_name}': {exc}"}
                )

            module_file = getattr(module, "__file__", None)
            if not module_file:
                raise InvalidContractOptions({package_name: "Root package has no __file__."})

            package_paths.append((package_name, Path(module_file).resolve().parent))
        return package_paths

    def _scan_package(self, package_path: Path) -> List[RelativeImport]:
        repo_root = self._find_repo_root(package_path)
        violations: list[RelativeImport] = []

        for py_file in package_path.rglob("*.py"):
            if "__pycache__" in py_file.parts:
                continue

            for line_number, statement in self._find_relative_imports(py_file):
                try:
                    display_path = str(py_file.relative_to(repo_root))
                except ValueError:
                    display_path = str(py_file)
                violations.append((display_path, line_number, statement))

        return violations

    def _find_relative_imports(self, py_file: Path) -> Iterable[tuple[int, str]]:
        try:
            content = py_file.read_text(encoding="utf-8")
        except Exception as exc:
            return [(0, f"[unreadable: {exc}]")]

        try:
            tree = ast.parse(content, filename=str(py_file))
        except SyntaxError as exc:
            line = exc.lineno or 0
            line_text = (
                content.splitlines()[line - 1].strip()
                if line and line - 1 < len(content.splitlines())
                else exc.msg
            )
            return [(line, f"[syntax error] {line_text}")]

        lines = content.splitlines()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level and node.level > 0:
                yield node.lineno, lines[node.lineno - 1].strip()

    def _find_repo_root(self, package_path: Path) -> Path:
        """Find repository root (directory containing pyproject.toml)."""
        for candidate in [package_path, *package_path.parents]:
            if (candidate / "pyproject.toml").exists():
                return candidate
        return package_path
