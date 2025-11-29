"""
Method Configuration Loader for Canonical JSON Specification.

Provides unified access to method parameters from the canonical
parameterization specification.
"""
import ast
import json
from pathlib import Path
from typing import Any
from saaaaaa import get_parameter_loader
from saaaaaa.core.calibration.decorators import calibrated_method


class MethodConfigLoader:
    """
    Loads and provides access to method parameters from canonical JSON.

    Usage:
        loader = MethodConfigLoader("CANONICAL_METHOD_PARAMETERIZATION_SPEC.json")
        threshold = loader.get_method_parameter(
            "CAUSAL.BMI.infer_mech_v1",
            "kl_divergence_threshold"
        )

    Note:
        The loader expects the JSON spec to follow the canonical schema with
        keys: specification_metadata, methods, and epistemic_validation_summary.
    """

    def __init__(self, spec_path: str | Path) -> None:
        self.spec_path = Path(spec_path)
        with open(self.spec_path) as f:
            self.spec = json.load(f)

        # Validate schema before use
        self.validate_spec_schema()

        # Build index for fast lookup
        self._method_index = {
            method["canonical_id"]: method
            for method in self.spec["methods"]
        }

    @calibrated_method("saaaaaa.utils.method_config_loader.MethodConfigLoader.validate_spec_schema")
    def validate_spec_schema(self) -> None:
        """
        Validate JSON spec matches expected schema.

        Raises:
            ValueError: If spec is missing required keys
        """
        required_keys = {"specification_metadata", "methods"}
        # Note: epistemic_validation_summary is optional in some versions
        if not required_keys.issubset(self.spec.keys()):
            missing = required_keys - set(self.spec.keys())
            raise ValueError(f"Spec missing required keys: {missing}")

    def get_method_parameter(
        self,
        canonical_id: str,
        param_name: str,
        override: Any = None
    ) -> Any:
        """
        Get parameter value for a method.

        Args:
            canonical_id: Canonical method ID (e.g., "CAUSAL.BMI.infer_mech_v1")
            param_name: Parameter name
            override: Optional override value (takes precedence over default)

        Returns:
            Parameter value (default or override)

        Raises:
            KeyError: If method or parameter not found
        """
        if canonical_id not in self._method_index:
            raise KeyError(f"Method {canonical_id} not found in canonical spec")

        method = self._method_index[canonical_id]

        for param in method["parameters"]:
            if param["name"] == param_name:
                return override if override is not None else param["default"]

        raise KeyError(f"Parameter {param_name} not found for method {canonical_id}")

    @calibrated_method("saaaaaa.utils.method_config_loader.MethodConfigLoader.get_method_description")
    def get_method_description(self, canonical_id: str) -> str:
        """Get method description."""
        return self._method_index[canonical_id]["description"]

    @calibrated_method("saaaaaa.utils.method_config_loader.MethodConfigLoader.get_parameter_spec")
    def get_parameter_spec(self, canonical_id: str, param_name: str) -> dict:
        """Get full parameter specification including allowed values."""
        method = self._method_index[canonical_id]
        for param in method["parameters"]:
            if param["name"] == param_name:
                return param
        raise KeyError(f"Parameter {param_name} not found")

    def validate_parameter_value(
        self,
        canonical_id: str,
        param_name: str,
        value: Any
    ) -> bool:
        """
        Validate parameter value against allowed_values specification.

        Returns:
            True if valid, raises ValueError if invalid
        """
        param_spec = self.get_parameter_spec(canonical_id, param_name)
        allowed = param_spec["allowed_values"]

        if allowed["kind"] == "range":
            spec = allowed["spec"]
            min_val, max_val = self._parse_range(spec)
            if not (min_val <= value <= max_val):
                raise ValueError(f"{param_name}={value} out of range {spec}")

        elif allowed["kind"] == "set":
            spec = allowed["spec"]
            valid_values = self._parse_set(spec)
            if value not in valid_values:
                raise ValueError(f"{param_name}={value} not in allowed set {spec}")

        return True

    @calibrated_method("saaaaaa.utils.method_config_loader.MethodConfigLoader._parse_range")
    def _parse_range(self, spec: str) -> tuple[float, float]:
        """
        Parse range specification like '[get_parameter_loader().get("saaaaaa.utils.method_config_loader.MethodConfigLoader._parse_range").get("auto_param_L135_41", 0.0), get_parameter_loader().get("saaaaaa.utils.method_config_loader.MethodConfigLoader._parse_range").get("auto_param_L135_46", 1.0)], inclusive' or '[100, 10000], integer'.

        Args:
            spec: Range specification string with format "[min, max], modifiers"
                  Modifiers can include: inclusive, exclusive, integer

        Returns:
            Tuple of (min_val, max_val) as floats

        Raises:
            ValueError: If spec format is invalid

        Note:
            The inclusive/exclusive and integer modifiers are parsed but not
            currently enforced in validation. This maintains compatibility with
            the current spec while allowing future enhancement.
        """
        try:
            # Extract bracketed part before any modifiers
            bracket_part = spec.split("]")[0] + "]"
            parts = bracket_part.replace("[", "").replace("]", "").split(",")
            min_val = float(parts[0].strip())
            max_val = float(parts[1].strip())
            return min_val, max_val
        except (IndexError, ValueError) as e:
            raise ValueError(f"Invalid range spec: {spec}") from e

    @calibrated_method("saaaaaa.utils.method_config_loader.MethodConfigLoader._parse_set")
    def _parse_set(self, spec: str | list) -> set:
        """
        Parse set specification safely.

        Args:
            spec: Either a list or a string representation of a Python literal

        Returns:
            Set of allowed values

        Raises:
            ValueError: If spec cannot be parsed safely

        Note:
            Uses ast.literal_eval() for safe parsing of string specs.
            Only Python literals (strings, numbers, tuples, lists, dicts,
            booleans, None) are supported - no arbitrary code execution.
        """
        if isinstance(spec, list):
            return set(spec)
        try:
            # Use ast.literal_eval for safer parsing
            return set(ast.literal_eval(spec))
        except (ValueError, SyntaxError) as e:
            raise ValueError(f"Invalid set spec: {spec}") from e
