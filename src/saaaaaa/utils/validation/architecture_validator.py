"""Architecture validation utilities for the municipal policy analysis system.

This module provides helpers to enforce that the municipal policy
analysis architecture blueprint references real, implemented methods.
It parses the ``policy_analysis_architecture.json`` specification,
compares every referenced method against the inventoried codebase and
produces coverage reports per analytical dimension.
"""

from __future__ import annotations

import ast
import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from saaaaaa.core.calibration.decorators import calibrated_method

# Regular expression used to capture fully-qualified method references such as
# ``ClassName.method_name``.
METHOD_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*$")

_EXTERNAL_REFERENCE = object()

ALIAS_MAP: dict[str, object] = {
    # Performance analyzer exposes the functionality through a private helper.
    "PerformanceAnalyzer.analyze_loss_function": "PerformanceAnalyzer._calculate_loss_functions",
    # The municipal plan analyzer generates recommendations with a private helper.
    "PDETMunicipalPlanAnalyzer.generate_recommendations": "PDETMunicipalPlanAnalyzer._generate_recommendations",
    # Advanced DAG validation leverages TeoriaCambio utilities internally.
    "AdvancedDAGValidator.validacion_completa": "TeoriaCambio.validacion_completa",
    "AdvancedDAGValidator._validar_orden_causal": "TeoriaCambio._validar_orden_causal",
    "AdvancedDAGValidator._encontrar_caminos_completos": "TeoriaCambio._encontrar_caminos_completos",
    # External dependency references (networkx graphs).
    "nx.DiGraph": _EXTERNAL_REFERENCE,
}

# Root directory of the repository (two levels above this file).
ROOT_DIR = Path(__file__).resolve().parent.parent

@dataclass(frozen=True)
class ArchitectureValidationResult:
    """Container with the outcome of the architecture validation process."""

    resolved_methods: set[str]
    missing_methods: Mapping[str, Mapping[str, list[str]]]
    coverage: float
    total_spec_methods: int
    total_available_methods: int
    per_dimension: Mapping[str, Mapping[str, list[str]]]
    global_methods: tuple[str, ...] = field(default_factory=tuple)

    @calibrated_method("saaaaaa.utils.validation.architecture_validator.ArchitectureValidationResult.to_dict")
    def to_dict(self) -> dict[str, object]:
        """Serialise the validation result into a JSON-compatible dict."""

        return {
            "coverage": self.coverage,
            "total_spec_methods": self.total_spec_methods,
            "total_available_methods": self.total_available_methods,
            "resolved_methods": sorted(self.resolved_methods),
            "missing_methods": {
                dimension: dict(question_map.items())
                for dimension, question_map in self.missing_methods.items()
            },
            "per_dimension": {
                dimension: dict(question_map.items())
                for dimension, question_map in self.per_dimension.items()
            },
            "global_methods": list(self.global_methods),
        }

def load_architecture_spec(path: Path) -> dict[str, object]:
    """Load the JSON architecture specification from ``path``."""

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)

def _extract_method_from_entry(entry: object) -> str | None:
    """Return the method string encoded in ``entry`` if present."""

    if isinstance(entry, str) and METHOD_PATTERN.match(entry):
        return entry

    if isinstance(entry, Mapping):
        # Architecture steps are stored as {"Class.method": "description"}
        for key in entry:
            if isinstance(key, str) and METHOD_PATTERN.match(key):
                return key

        # Some entries are dictionaries using {"name": "method"}. These lack
        # class information and therefore cannot be enforced reliably.
        name = entry.get("name") if isinstance(entry.get("name"), str) else None
        if name and METHOD_PATTERN.match(name):
            return name

    return None

def _extract_methods_from_string(value: str) -> Iterable[str]:
    """Extract additional method references embedded in textual descriptions."""

    for candidate in re.findall(r"[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*", value):
        if METHOD_PATTERN.match(candidate):
            yield candidate

def extract_architecture_methods(spec: Mapping[str, object]) -> tuple[dict[str, dict[str, list[str]]], list[str]]:
    """Extract method sequences per dimension and global method references."""

    policy_spec = spec.get("policy_analysis_architecture", {})
    if not isinstance(policy_spec, Mapping):
        raise ValueError("Malformed architecture specification: missing 'policy_analysis_architecture'.")

    per_dimension: dict[str, dict[str, list[str]]] = {}
    global_methods: list[str] = []

    # --- Component level methods -------------------------------------------------
    orchestration = policy_spec.get("orchestration_flow", {})
    if isinstance(orchestration, Mapping):
        for component in orchestration.get("components", []):
            if not isinstance(component, Mapping):
                continue
            for entry in component.get("key_methods", []):
                method = _extract_method_from_entry(entry)
                if method:
                    global_methods.append(method.strip())
                if isinstance(entry, Mapping):
                    description = entry.get("description")
                    if isinstance(description, str):
                        global_methods.extend(list(_extract_methods_from_string(description)))

    # --- Phase 0 (initialisation) -------------------------------------------------
    phase_zero = policy_spec.get("phase_0_inicializacion_y_carga", {})
    if isinstance(phase_zero, Mapping):
        for step in phase_zero.get("steps", []):
            if not isinstance(step, Mapping):
                continue
            for action in step.get("actions", []):
                method = _extract_method_from_entry(action)
                if method:
                    global_methods.append(method.strip())
                if isinstance(action, Mapping):
                    for value in action.values():
                        if isinstance(value, str):
                            global_methods.extend(list(_extract_methods_from_string(value)))

    # --- Analytical dimensions ----------------------------------------------------
    for dimension in policy_spec.get("dimensiones", []):
        if not isinstance(dimension, Mapping):
            continue
        dim_id = str(dimension.get("id", "UNKNOWN"))
        dimension_methods: dict[str, list[str]] = {}
        for subdimension in dimension.get("subdimension", []):
            if not isinstance(subdimension, Mapping):
                continue
            question_id = str(subdimension.get("pregunta", "UNKNOWN"))
            methods: list[str] = []
            for step in subdimension.get("cadena_metodos", []):
                method = _extract_method_from_entry(step)
                if method:
                    methods.append(method.strip())
                if isinstance(step, Mapping):
                    for value in step.values():
                        if isinstance(value, str):
                            methods.extend(list(_extract_methods_from_string(value)))
            dimension_methods[question_id] = methods
        if dimension_methods:
            per_dimension[dim_id] = dimension_methods

    # --- Transversal modules ------------------------------------------------------
    transversal = policy_spec.get("modulos_transversales", {})
    if isinstance(transversal, Mapping):
        metricas = transversal.get("metricas_rendimiento", {})
        if isinstance(metricas, Mapping):
            for component in metricas.get("componentes", []):
                if not isinstance(component, Mapping):
                    continue
                method = _extract_method_from_entry(component)
                if method:
                    global_methods.append(method.strip())
                description = component.get("descripcion") or component.get("description")
                if isinstance(description, str):
                    global_methods.extend(list(_extract_methods_from_string(description)))

    return per_dimension, global_methods

def load_method_inventory(path: Path) -> tuple[set[str], set[str]]:
    """Load available class methods and module functions from the inventory."""

    with path.open("r", encoding="utf-8") as handle:
        inventory = json.load(handle)

    available_methods: set[str] = set()
    functions: set[str] = set()

    candidate_files = inventory.get("files", {})
    for file_name in candidate_files:
        file_path = ROOT_DIR / file_name
        if not file_path.exists():
            continue
        try:
            tree = ast.parse(file_path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.add(node.name)
            elif isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        available_methods.add(f"{node.name}.{item.name}")

    return available_methods, functions

def _resolve_method_reference(
    reference: str,
    available_methods: set[str],
    available_functions: set[str],
) -> str | None:
    """Resolve a method reference using the available inventory."""

    reference = reference.strip()

    alias_target = ALIAS_MAP.get(reference)
    if alias_target is _EXTERNAL_REFERENCE:
        return reference
    if isinstance(alias_target, str):
        if alias_target == reference:
            return reference if reference in available_methods else None
        resolved_alias = _resolve_method_reference(alias_target, available_methods, available_functions)
        if resolved_alias:
            return resolved_alias

    if METHOD_PATTERN.match(reference):
        if reference in available_methods:
            return reference
        # Allow ``Class.init`` aliases for ``Class.__init__``
        if reference.endswith(".init"):
            init_alias = reference[:-4] + "__init__"
            if init_alias in available_methods:
                return init_alias
        return None

    # Plain function reference
    if reference in available_functions:
        return reference
    return None

def validate_architecture(spec_path: Path, inventory_path: Path) -> ArchitectureValidationResult:
    """Validate that every method described in the architecture exists."""

    spec = load_architecture_spec(spec_path)
    per_dimension, global_methods = extract_architecture_methods(spec)

    available_methods, available_functions = load_method_inventory(inventory_path)

    resolved_methods: set[str] = set()
    missing_methods: dict[str, dict[str, list[str]]] = {}

    # Validate global references
    for method in global_methods:
        resolved = _resolve_method_reference(method, available_methods, available_functions)
        if resolved:
            resolved_methods.add(resolved)
        else:
            missing_methods.setdefault("__global__", {}).setdefault("__global__", []).append(method)

    # Validate per-dimension references
    for dimension, question_map in per_dimension.items():
        for question, methods in question_map.items():
            for method in methods:
                resolved = _resolve_method_reference(method, available_methods, available_functions)
                if resolved:
                    resolved_methods.add(resolved)
                else:
                    missing_methods.setdefault(dimension, {}).setdefault(question, []).append(method)

    total_references = len(global_methods)
    total_references += sum(len(methods) for question_map in per_dimension.values() for methods in question_map.values())
    total_references = max(total_references, 1)

    coverage = len(resolved_methods) / total_references

    return ArchitectureValidationResult(
        resolved_methods=resolved_methods,
        missing_methods=missing_methods,
        coverage=coverage,
        total_spec_methods=total_references,
        total_available_methods=len(available_methods),
        per_dimension=per_dimension,
        global_methods=tuple(global_methods),
    )

def write_validation_report(result: ArchitectureValidationResult, output_path: Path) -> None:
    """Write the validation report to ``output_path`` in JSON format."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(result.to_dict(), handle, indent=2, ensure_ascii=False)

def main() -> None:
    """Entry point for CLI usage."""

    spec_path = ROOT_DIR / "policy_analysis_architecture.json"
    inventory_path = ROOT_DIR / "COMPLETE_METHOD_CLASS_MAP.json"
    report_path = ROOT_DIR / "validation" / "architecture_validation_report.json"

    result = validate_architecture(spec_path, inventory_path)
    write_validation_report(result, report_path)

    if result.missing_methods:
        missing_total = sum(len(methods) for dimension in result.missing_methods.values() for methods in dimension.values())
        print(
            f"Architecture validation completed with {missing_total} missing methods. "
            f"Report saved to {report_path}."
        )
    else:
        print(f"Architecture validation successful. Report saved to {report_path}.")

# Note: Main entry point removed to maintain I/O boundary separation.
# For usage, call main() function from a script or see examples/ directory.
