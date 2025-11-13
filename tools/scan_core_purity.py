"""Static guard ensuring the `core` package stays free of runtime side effects."""
from __future__ import annotations

import ast
import pathlib
import re

ROOT = pathlib.Path("core")
BAD_CALLS = re.compile(r"\b(open|json\.load|json\.dump|requests\.|pandas\.read_)", re.I)

class _PurityViolation(SystemExit):
    """Custom exit used to signal violations without stack traces."""

def _check(path: pathlib.Path) -> None:
    code = path.read_text(encoding="utf-8")
    tree = ast.parse(code, filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            test = getattr(node, "test", None)
            if isinstance(test, ast.Compare):
                left = getattr(test, "left", None)
                if isinstance(left, ast.Name) and left.id == "__name__":
                    raise _PurityViolation(f"{path}: __main__ block found")
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and BAD_CALLS.match(node.func.id or ""):
                raise _PurityViolation(f"{path}: forbidden I/O pattern")
            if isinstance(node.func, ast.Attribute):
                value = node.func.value
                attr_call = f"{getattr(value, 'id', '')}.{node.func.attr}"
                if BAD_CALLS.search(attr_call):
                    raise _PurityViolation(f"{path}: forbidden I/O pattern")
    if BAD_CALLS.search(code):
        raise _PurityViolation(f"{path}: forbidden I/O pattern")

def main() -> None:
    for file_path in sorted(ROOT.rglob("*.py")):
        _check(file_path)
    print("Core purity: OK")

if __name__ == "__main__":  # pragma: no cover - manual invocation only
    try:
        main()
    except _PurityViolation as exc:
        raise SystemExit(str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive catch
        raise SystemExit(str(exc)) from exc
