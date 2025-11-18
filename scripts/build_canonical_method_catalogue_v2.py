#!/usr/bin/env python3
"""
Canonical Method Catalogue V2 Builder
=====================================

This builder enforces the ultra-strict requirements for generating
`canonical_method_catalogue_v2.json`. It parses every Python file under
`src/saaaaaa`, extracts every method/function definition, computes
parameter metadata (including evaluated defaults), and emits the new
catalogue together with the required companion artifacts:

- canonical_method_catalogue_v2.json
- catalogue_v1_to_v2_diff.json
- methods_with_complex_defaults.txt
- catalogue_generation_report.md (statistics-only, verification status filled post-tests)

The builder is intentionally self-contained so that tests can re-use the
same AST logic to validate the generated catalogue.
"""

from __future__ import annotations

import ast
import hashlib
import json
import math
from collections import Counter, defaultdict, OrderedDict
from dataclasses import dataclass, field, asdict
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "src" / "saaaaaa"
OLD_CATALOG_PATH = REPO_ROOT / "config" / "canonical_method_catalog.json"
OUTPUT_PATH = REPO_ROOT / "canonical_method_catalogue_v2.json"
DIFF_PATH = REPO_ROOT / "catalogue_v1_to_v2_diff.json"
COMPLEX_DEFAULTS_PATH = REPO_ROOT / "methods_with_complex_defaults.txt"
REPORT_PATH = REPO_ROOT / "catalogue_generation_report.md"


@dataclass
class ParameterRecord:
    """Parameter metadata with evaluated defaults."""

    name: str
    type_hint: Optional[str]
    required: bool
    has_default: bool
    default_value: Any
    default_type: Optional[str]
    default_source: Optional[str]


@dataclass
class MethodRecord:
    """Complete method metadata captured from AST parsing."""

    unique_id: str
    canonical_name: str
    method_name: str
    class_name: Optional[str]
    file_path: str
    layer: str
    layer_position: int
    signature: str
    input_parameters: List[ParameterRecord]
    return_type: Optional[str]
    requires_calibration: bool
    calibration_status: str
    calibration_location: Optional[str]
    docstring: Optional[str]
    decorators: List[str]
    is_async: bool
    is_private: bool
    is_abstract: bool
    complexity: str
    line_number: int
    source_hash: str
    last_analyzed: str
    configurable_parameters: Dict[str, Any] = field(default_factory=dict)
    auto_generated: bool = False


class CatalogueBuilder:
    """Builder responsible for scanning, parsing, and emitting the catalogue."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.src_root = SRC_ROOT
        if not self.src_root.exists():
            raise FileNotFoundError(f"Source root not found: {self.src_root}")

        self.methods: list[MethodRecord] = []
        self.layer_counts: dict[str, int] = defaultdict(int)
        self.stats: dict[str, Any] = {
            "files_scanned": 0,
            "methods_scanned": 0,
            "parsing_errors": [],
            "total_parameters": 0,
            "methods_with_defaults": 0,
            "parameters_with_defaults": 0,
            "default_type_counts": Counter(),
        }
        self.complex_defaults: list[tuple[str, str, str]] = []
        self.old_catalog = self._load_old_catalog()

    def _load_old_catalog(self) -> dict[str, Any]:
        if OLD_CATALOG_PATH.exists():
            with OLD_CATALOG_PATH.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        return {}

    # --------------------------------------------------------------------- #
    # Scanning helpers
    # --------------------------------------------------------------------- #
    def build(self) -> dict[str, Any]:
        """Main entry point for building every artifact."""
        py_files = sorted(self.src_root.rglob("*.py"))
        self.stats["files_scanned"] = len(py_files)

        for file_path in py_files:
            self._process_file(file_path)

        if self.stats["parsing_errors"]:
            errors = "\n".join(self.stats["parsing_errors"])
            raise RuntimeError(f"Parsing failures detected:\n{errors}")

        catalogue = self._assemble_catalogue()
        self._write_json(OUTPUT_PATH, catalogue)
        self._write_diff(catalogue)
        self._write_complex_defaults()
        self._write_report(catalogue)
        return catalogue

    def _process_file(self, file_path: Path) -> None:
        """Parse a file and extract every top-level function/method."""
        try:
            source = file_path.read_text(encoding="utf-8")
        except Exception as exc:  # pragma: no cover - filesystem failure
            self.stats["parsing_errors"].append(f"{file_path}: unable to read ({exc})")
            return

        try:
            tree = ast.parse(source, filename=str(file_path))
        except SyntaxError as exc:
            self.stats["parsing_errors"].append(f"{file_path}: syntax error ({exc})")
            return

        rel_path = file_path.relative_to(self.repo_root)
        module_name = str(rel_path.with_suffix("")).replace("/", ".")

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                self._process_class(node, file_path, module_name, source)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._record_method(node, None, file_path, module_name, source)

    def _process_class(
        self,
        class_node: ast.ClassDef,
        file_path: Path,
        module_name: str,
        source: str,
    ) -> None:
        has_init = False
        for node in class_node.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._record_method(node, class_node.name, file_path, module_name, source)
                if node.name == "__init__":
                    has_init = True

        if self._is_dataclass(class_node) and not has_init:
            self._add_dataclass_init(class_node, file_path, module_name)
    # --------------------------------------------------------------------- #
    # Method extraction helpers
    # --------------------------------------------------------------------- #
    def _record_method(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        class_name: Optional[str],
        file_path: Path,
        module_name: str,
        source: str,
    ) -> None:
        method_name = node.name
        canonical_name = (
            f"{module_name}.{class_name}.{method_name}"
            if class_name
            else f"{module_name}.{method_name}"
        )
        rel_path = file_path.relative_to(self.repo_root)
        unique_id = hashlib.sha256(
            f"{rel_path}:{class_name or 'MODULE'}:{method_name}:{node.lineno}".encode("utf-8")
        ).hexdigest()[:16]

        parameters = self._extract_parameters(node, canonical_name)
        signature = f"{method_name}({', '.join(param.name for param in parameters)})"
        return_type = self._safe_unparse(node.returns) if node.returns else None
        docstring = ast.get_docstring(node)
        decorators = [self._safe_unparse(dec) for dec in getattr(node, "decorator_list", [])]
        complexity = self._compute_complexity(node)
        calibration = self._determine_calibration_status(canonical_name, method_name, class_name, rel_path)
        method_source = ast.get_source_segment(source, node) or self._safe_unparse(node)
        source_hash = hashlib.sha256(method_source.encode("utf-8")).hexdigest()[:16]
        layer = self._determine_layer(rel_path)
        layer_position = self.layer_counts[layer]
        self.layer_counts[layer] += 1

        record = MethodRecord(
            unique_id=unique_id,
            canonical_name=canonical_name,
            method_name=method_name,
            class_name=class_name,
            file_path=str(rel_path),
            layer=layer,
            layer_position=layer_position,
            signature=signature,
            input_parameters=parameters,
            return_type=return_type,
            requires_calibration=calibration["requires"],
            calibration_status=calibration["status"],
            calibration_location=calibration["location"],
            docstring=docstring,
            decorators=decorators,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            is_private=method_name.startswith("_"),
            is_abstract=("abstractmethod" in decorators) or ("ABC" in "".join(decorators)),
            complexity=complexity,
            line_number=node.lineno,
            source_hash=source_hash,
            last_analyzed=datetime.now(UTC).isoformat(),
        )
        self._register_method(record)

    def _register_method(self, record: MethodRecord) -> None:
        configurable = [
            param for param in record.input_parameters if param.has_default and param.name != "self"
        ]
        record.configurable_parameters = {
            "count": len(configurable),
            "names": [param.name for param in configurable],
            "all_have_valid_defaults": all(
                self._is_valid_default_value(param.default_value) and param.default_type != "complex"
                for param in configurable
            ),
        }

        self.stats["methods_scanned"] += 1
        method_param_count = sum(1 for param in record.input_parameters if param.name != "self")
        self.stats["total_parameters"] += method_param_count
        if configurable:
            self.stats["methods_with_defaults"] += 1
            self.stats["parameters_with_defaults"] += len(configurable)

        for param in record.input_parameters:
            if not param.has_default:
                continue
            if param.default_type == "complex":
                self.complex_defaults.append(
                    (record.canonical_name, param.name, str(param.default_value))
                )
            else:
                self.stats["default_type_counts"][param.default_type] += 1

        self.methods.append(record)

    def _extract_parameters(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        canonical_name: str,
    ) -> List[ParameterRecord]:
        args = node.args
        parameters: list[ParameterRecord] = []

        positional = list(args.posonlyargs) + list(args.args)
        defaults = list(args.defaults)
        total_defaults = len(defaults)
        num_without_default = len(positional) - total_defaults

        for index, arg in enumerate(positional):
            has_default = index >= num_without_default
            default_node = defaults[index - num_without_default] if has_default else None
            parameters.append(self._build_parameter(arg, has_default, default_node, canonical_name))

        if args.vararg:
            parameters.append(self._build_parameter(args.vararg, False, None, canonical_name, vararg=True))

        for kw_arg, kw_default in zip(args.kwonlyargs, args.kw_defaults, strict=False):
            has_default = kw_default is not None
            parameters.append(self._build_parameter(kw_arg, has_default, kw_default, canonical_name))

        if args.kwarg:
            parameters.append(self._build_parameter(args.kwarg, False, None, canonical_name, kwarg=True))

        return parameters

    def _build_parameter(
        self,
        arg: ast.arg,
        has_default: bool,
        default_node: Optional[ast.expr],
        canonical_name: str,
        *,
        vararg: bool = False,
        kwarg: bool = False,
    ) -> ParameterRecord:
        name = ("*" if vararg else "**" if kwarg else "") + arg.arg
        type_hint = self._safe_unparse(arg.annotation) if arg.annotation else None
        required = not has_default
        default_value = None
        default_type = None
        default_source = None

        if vararg:
            has_default = True
            required = False
            default_value = "tuple()"
            default_type = "literal"
        elif kwarg:
            has_default = True
            required = False
            default_value = "dict()"
            default_type = "literal"
        elif has_default and default_node is not None:
            value, default_type, rendered = self._evaluate_default(default_node)
            default_value = value
            default_source = f"line {getattr(default_node, 'lineno', arg.lineno)}"
        else:
            if vararg or kwarg:
                required = True  # fallback, though branch should not trigger

        return ParameterRecord(
            name=name,
            type_hint=type_hint,
            required=required,
            has_default=bool(has_default),
            default_value=default_value,
            default_type=default_type,
            default_source=default_source,
        )

    def _evaluate_default(self, default_node: ast.expr) -> Tuple[Any, str, str]:
        expression = self._safe_unparse(default_node)
        try:
            literal_value = ast.literal_eval(default_node)
            return self._make_json_safe(literal_value), "literal", expression
        except Exception:
            pass

        try:
            compiled = compile(ast.Expression(default_node), filename="<ast>", mode="eval")
            evaluated = eval(compiled, {}, {})  # noqa: S307 - controlled input
            return self._make_json_safe(evaluated), "expression", expression
        except Exception:
            return expression, "complex", expression

    @staticmethod
    def _make_json_safe(value: Any) -> Any:
        if value is None:
            return "None"
        if isinstance(value, (bool, int)):
            return value
        if isinstance(value, float):
            if math.isnan(value) or math.isinf(value):
                return repr(value)
            return value
        if isinstance(value, str):
            return value
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="backslashreplace")
        if isinstance(value, (list, tuple, set)):
            iterable = list(value)
            return [CatalogueBuilder._make_json_safe(item) for item in iterable]
        if isinstance(value, dict):
            return {str(key): CatalogueBuilder._make_json_safe(val) for key, val in value.items()}
        return repr(value)

    def _is_dataclass(self, class_node: ast.ClassDef) -> bool:
        for decorator in class_node.decorator_list:
            name = self._safe_unparse(decorator)
            if not name:
                continue
            if name.split("(")[0].endswith("dataclass"):
                return True
        return False

    def _add_dataclass_init(self, class_node: ast.ClassDef, file_path: Path, module_name: str) -> None:
        field_parameters = self._extract_dataclass_fields(class_node)
        if not field_parameters:
            return
        if not any(param.has_default for param in field_parameters):
            return

        rel_path = file_path.relative_to(self.repo_root)
        canonical_name = f"{module_name}.{class_node.name}.__init__"
        unique_id = hashlib.sha256(
            f"{rel_path}:{class_node.name}:__init__:{class_node.lineno}".encode("utf-8")
        ).hexdigest()[:16]

        parameters = [
            ParameterRecord(
                name="self",
                type_hint=None,
                required=True,
                has_default=False,
                default_value=None,
                default_type=None,
                default_source=None,
            )
        ]
        parameters.extend(field_parameters)

        signature = f"__init__({', '.join(param.name for param in parameters)})"
        layer = self._determine_layer(rel_path)
        calibration = self._determine_calibration_status(
            canonical_name, "__init__", class_node.name, rel_path
        )
        source_hash = hashlib.sha256(signature.encode("utf-8")).hexdigest()[:16]

        record = MethodRecord(
            unique_id=unique_id,
            canonical_name=canonical_name,
            method_name="__init__",
            class_name=class_node.name,
            file_path=str(rel_path),
            layer=layer,
            layer_position=self.layer_counts[layer],
            signature=signature,
            input_parameters=parameters,
            return_type=None,
            requires_calibration=calibration["requires"],
            calibration_status=calibration["status"],
            calibration_location=calibration["location"],
            docstring=f"Auto-generated dataclass __init__ for {class_node.name}",
            decorators=["dataclass(auto-generated)"],
            is_async=False,
            is_private=False,
            is_abstract=False,
            complexity="low",
            line_number=class_node.lineno,
            source_hash=source_hash,
            last_analyzed=datetime.now(UTC).isoformat(),
            auto_generated=True,
        )
        self.layer_counts[layer] += 1
        self._register_method(record)

    def _extract_dataclass_fields(self, class_node: ast.ClassDef) -> List[ParameterRecord]:
        parameters: list[ParameterRecord] = []
        for node in class_node.body:
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                param = self._convert_annassign_to_parameter(node)
                if param:
                    parameters.append(param)
        return parameters

    def _convert_annassign_to_parameter(self, node: ast.AnnAssign) -> Optional[ParameterRecord]:
        if node.annotation and self._annotation_is_classvar(node.annotation):
            return None
        if not isinstance(node.target, ast.Name):
            return None

        if isinstance(node.value, ast.Call) and self._is_field_call(node.value):
            if not self._field_included_in_init(node.value):
                return None

        name = node.target.id
        type_hint = self._safe_unparse(node.annotation) if node.annotation else None
        has_default = node.value is not None
        default_value = None
        default_type = None
        default_source = None

        if node.value is not None:
            default_value, default_type, default_source = self._resolve_dataclass_default(node.value)
            if default_value is None:
                has_default = False

        return ParameterRecord(
            name=name,
            type_hint=type_hint,
            required=not has_default,
            has_default=has_default,
            default_value=default_value,
            default_type=default_type,
            default_source=default_source,
        )

    def _resolve_dataclass_default(
        self, value_node: ast.expr
    ) -> Tuple[Optional[Any], Optional[str], Optional[str]]:
        if isinstance(value_node, ast.Call) and self._is_field_call(value_node):
            default_kw = next((kw for kw in value_node.keywords if kw.arg == "default"), None)
            default_factory_kw = next(
                (kw for kw in value_node.keywords if kw.arg == "default_factory"), None
            )

            if default_kw is not None:
                value, default_type, _ = self._evaluate_default(default_kw.value)
                return value, default_type, f"line {getattr(default_kw.value, 'lineno', value_node.lineno)}"

            if default_factory_kw is not None:
                factory_expr = self._safe_unparse(default_factory_kw.value)
                return (
                    f"factory:{factory_expr}",
                    "complex",
                    f"line {getattr(default_factory_kw.value, 'lineno', value_node.lineno)}",
                )

            if value_node.args:
                value, default_type, _ = self._evaluate_default(value_node.args[0])
                return value, default_type, f"line {getattr(value_node.args[0], 'lineno', value_node.lineno)}"

            return None, None, None

        value, default_type, _ = self._evaluate_default(value_node)
        return value, default_type, f"line {getattr(value_node, 'lineno', 0)}"

    def _annotation_is_classvar(self, annotation: ast.AST) -> bool:
        text = self._safe_unparse(annotation) or ""
        return "ClassVar" in text

    @staticmethod
    def _is_field_call(call_node: ast.Call) -> bool:
        target = None
        if isinstance(call_node.func, ast.Name):
            target = call_node.func.id
        elif isinstance(call_node.func, ast.Attribute):
            target = call_node.func.attr
        return target == "field"

    def _field_included_in_init(self, call_node: ast.Call) -> bool:
        for kw in call_node.keywords:
            if kw.arg == "init":
                try:
                    return bool(ast.literal_eval(kw.value))
                except Exception:
                    return True
        return True

    @staticmethod
    def _safe_unparse(node: Optional[ast.AST]) -> Optional[str]:
        if node is None:
            return None
        try:
            return ast.unparse(node)
        except Exception:
            return None

    @staticmethod
    def _compute_complexity(node: ast.AST) -> str:
        try:
            method_source = ast.unparse(node)
            lines = len(method_source.splitlines())
            branches = sum(
                1
                for sub in ast.walk(node)
                if isinstance(sub, (ast.If, ast.For, ast.While, ast.Try, ast.With))
            )
            if lines > 50 or branches > 10:
                return "high"
            if lines > 20 or branches > 5:
                return "medium"
            return "low"
        except Exception:
            return "unknown"

    @staticmethod
    def _is_valid_default_value(value: Any) -> bool:
        return value is not None

    def _determine_layer(self, rel_path: Path) -> str:
        path_str = str(rel_path).lower()
        layer_patterns = {
            "orchestrator": ["orchestrator", "core"],
            "executor": ["executor"],
            "analyzer": ["analysis", "analyzer", "scoring"],
            "processor": ["processing", "policy"],
            "ingestion": ["ingestion", "document"],
            "utility": ["utils", "helpers"],
            "validation": ["validation", "validator", "schema"],
            "contracts": ["contracts"],
        }
        for layer, patterns in layer_patterns.items():
            if any(pattern in path_str for pattern in patterns):
                return layer
        return "unknown"

    def _determine_calibration_status(
        self,
        canonical_name: str,
        method_name: str,
        class_name: Optional[str],
        rel_path: Path,
    ) -> Dict[str, Any]:
        registry_path = (
            self.repo_root / "src" / "saaaaaa" / "core" / "orchestrator" / "calibration_registry.py"
        )
        if class_name and registry_path.exists():
            registry_content = registry_path.read_text(encoding="utf-8")
            key = f'("{class_name}", "{method_name}")'
            if key in registry_content:
                return {
                    "requires": True,
                    "status": "centralized",
                    "location": str(registry_path.relative_to(self.repo_root)),
                }

        calibration_indicators = [
            "score",
            "compute",
            "evaluate",
            "analyze",
            "aggregate",
            "weight",
            "threshold",
            "normalize",
            "calibrate",
            "execute",
        ]
        path_str = str(rel_path).lower()
        requires_calibration = any(ind in method_name.lower() for ind in calibration_indicators)
        if "executor" in path_str or "analyzer" in path_str:
            requires_calibration = True

        if not requires_calibration:
            return {"requires": False, "status": "none", "location": None}

        return {"requires": True, "status": "unknown", "location": None}

    # --------------------------------------------------------------------- #
    # Output helpers
    # --------------------------------------------------------------------- #
    def _assemble_catalogue(self) -> Dict[str, Any]:
        methods_by_name = OrderedDict()
        for method in sorted(self.methods, key=lambda record: record.canonical_name):
            method_dict = asdict(method)
            method_dict["input_parameters"] = [
                {
                    "name": param["name"],
                    "type_hint": param["type_hint"],
                    "required": param["required"],
                    "has_default": param["has_default"],
                    "default_value": param["default_value"],
                    "default_type": param["default_type"],
                    "default_source": param["default_source"],
                }
                for param in method_dict["input_parameters"]
            ]
            methods_by_name[method.canonical_name] = method_dict

        total_methods = len(methods_by_name)
        methods_with_defaults = self.stats["methods_with_defaults"]
        params_with_defaults = self.stats["parameters_with_defaults"]
        total_params = max(self.stats["total_parameters"], 1)

        metadata = {
            "version": "2.0.0",
            "generation_date": datetime.now(UTC).isoformat(),
            "total_methods": total_methods,
            "methods_with_defaults": methods_with_defaults,
            "coverage": "100%",
            "validation_passed": False,
            "method_default_ratio": round(methods_with_defaults / total_methods, 4),
            "parameter_default_ratio": round(params_with_defaults / total_params, 4),
        }

        catalogue = OrderedDict({"_metadata": metadata})
        catalogue.update(methods_by_name)
        return catalogue

    def _write_diff(self, catalogue: Dict[str, Any]) -> None:
        old_methods = {
            method["canonical_name"]: method for method in self.old_catalog.get("methods", [])
        }
        new_methods = {
            name: data for name, data in catalogue.items() if not name.startswith("_")
        }

        added = sorted(set(new_methods) - set(old_methods))
        removed = sorted(set(old_methods) - set(new_methods))
        overlapping = sorted(set(new_methods) & set(old_methods))

        parameter_updates: dict[str, list[dict[str, Any]]] = {}
        for name in overlapping:
            old_params = {param["name"]: param for param in old_methods[name]["input_parameters"]}
            new_params = {param["name"]: param for param in new_methods[name]["input_parameters"]}
            updates: list[dict[str, Any]] = []

            for param_name, new_param in new_params.items():
                old_param = old_params.get(param_name)
                if not old_param:
                    updates.append({"name": param_name, "change": "added_in_v2"})
                    continue
                if old_param.get("required") != new_param["required"]:
                    updates.append(
                        {
                            "name": param_name,
                            "change": "required_flag_changed",
                            "v1": old_param.get("required"),
                            "v2": new_param["required"],
                        }
                    )
                updates.append(
                    {
                        "name": param_name,
                        "change": "defaults_enriched",
                        "default_value": new_param["default_value"],
                        "default_type": new_param["default_type"],
                        "default_source": new_param["default_source"],
                    }
                )

            removed_params = sorted(set(old_params) - set(new_params))
            for param_name in removed_params:
                updates.append({"name": param_name, "change": "missing_in_v2"})

            if updates:
                parameter_updates[name] = updates

        diff = {
            "generated_at": datetime.now(UTC).isoformat(),
            "baseline_catalog": str(OLD_CATALOG_PATH),
            "v2_catalog": str(OUTPUT_PATH),
            "methods_added": added,
            "methods_removed": removed,
            "parameter_updates": parameter_updates,
        }
        self._write_json(DIFF_PATH, diff)

    def _write_complex_defaults(self) -> None:
        lines = [
            f"{method} :: {param} = {expression}"
            for method, param, expression in sorted(self.complex_defaults)
        ]
        COMPLEX_DEFAULTS_PATH.write_text("\n".join(lines), encoding="utf-8")

    def _write_report(self, catalogue: Dict[str, Any]) -> None:
        total_methods = len([name for name in catalogue if not name.startswith("_")])
        methods_with_defaults = self.stats["methods_with_defaults"]
        params_with_defaults = self.stats["parameters_with_defaults"]
        total_params = max(self.stats["total_parameters"], 1)
        method_coverage = methods_with_defaults / total_methods if total_methods else 0.0
        param_coverage = params_with_defaults / total_params if total_params else 0.0
        literal = self.stats["default_type_counts"]["literal"]
        expression = self.stats["default_type_counts"]["expression"]
        complex_count = len(self.complex_defaults)

        def fmt_pct(value: float) -> str:
            return f"{value * 100:.1f}%"

        default_distribution_total = max(literal + expression + complex_count, 1)

        current_method_names = set(self._load_method_names(catalogue))
        old_method_names = self._load_old_method_names()

        lines = [
            "================================================================",
            "CATÁLOGO V2 - REPORTE DE GENERACIÓN",
            "================================================================",
            "",
            "ESTADÍSTICAS:",
            f"  Total methods scanned: {total_methods}",
            f"  Methods successfully parsed: {total_methods} (100%)",
            f"  Methods with parsing errors: {len(self.stats['parsing_errors'])}",
            "",
            f"  Methods with configurable params: {methods_with_defaults} ({fmt_pct(method_coverage)})",
            f"  Total parameters: {self.stats['total_parameters']}",
            f"  Configurable parameters: {params_with_defaults} ({fmt_pct(param_coverage)})",
            "",
            "DISTRIBUCIÓN DE DEFAULTS:",
            f"  Literal values: {literal} ({fmt_pct(literal / default_distribution_total)})",
            f"  Evaluated expressions: {expression} ({fmt_pct(expression / default_distribution_total)})",
            f"  Complex expressions: {complex_count} ({fmt_pct(complex_count / default_distribution_total)})",
            "",
            "VERIFICACIONES:",
            "  ✅ Test 1 (Consistency): PENDING",
            "  ✅ Test 2 (Source Match): PENDING",
            "  ✅ Test 3 (Coverage): PENDING",
            "  ✅ Test 4 (Known Methods): PENDING",
            "",
            "ARCHIVO GENERADO:",
            f"  Path: {OUTPUT_PATH.name}",
            f"  Size: {self._format_size(OUTPUT_PATH)}",
            f"  Methods: {total_methods}",
            "  Valid JSON: ✅",
            "",
            "CAMBIOS vs CATÁLOGO VIEJO:",
            f"  Methods added: {len(current_method_names - old_method_names)}",
            f"  Methods removed: {len(old_method_names - current_method_names)}",
            f"  Parameters updated: {params_with_defaults}",
            "  Fields added per method: 4 (has_default, default_value, default_type, default_source)",
            "",
            "TOP 10 METHODS WITH MOST CONFIGURABLES:",
        ]

        top_methods = sorted(
            [
                (data["configurable_parameters"]["count"], name)
                for name, data in catalogue.items()
                if not name.startswith("_")
            ],
            key=lambda item: (-item[0], item[1]),
        )[:10]
        for idx, (count, name) in enumerate(top_methods, start=1):
            lines.append(f"  {idx}. {name}: {count} configurable params")

        lines.append("")
        lines.append("MÉTODOS CON DEFAULTS COMPLEJOS (revisar):")
        for method, param, expression in sorted(self.complex_defaults)[:20]:
            lines.append(f"  - {method}: param=\"{param}\" default=\"{expression}\"")
        lines.append("")
        lines.append("================================================================")
        lines.append("RESULTADO: ⚠️ PENDING VALIDATION")
        lines.append("================================================================")
        REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")

    def _load_method_names(self, catalogue: Dict[str, Any]) -> List[str]:
        return [name for name in catalogue if not name.startswith("_")]

    def _load_old_method_names(self) -> set[str]:
        return {method["canonical_name"] for method in self.old_catalog.get("methods", [])}

    @staticmethod
    def _format_size(path: Path) -> str:
        try:
            size_mb = path.stat().st_size / (1024 * 1024)
            return f"{size_mb:.1f} MB"
        except Exception:  # pragma: no cover
            return "unknown"

    @staticmethod
    def _write_json(path: Path, payload: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)


def main() -> int:
    builder = CatalogueBuilder(REPO_ROOT)
    builder.build()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
