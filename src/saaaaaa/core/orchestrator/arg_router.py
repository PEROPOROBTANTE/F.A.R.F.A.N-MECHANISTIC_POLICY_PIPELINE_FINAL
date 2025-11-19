"""Argument routing with special routes, strict validation, and comprehensive metrics.

This module provides ExtendedArgRouter (and legacy ArgRouter for compatibility):
- 30+ special route handlers for commonly-called methods
- Strict validation (no silent parameter drops)
- **kwargs support for forward compatibility
- Full observability and metrics
- Base routing and validation utilities

Design Principles:
- Explicit route definitions for high-traffic methods
- Fail-fast on missing required arguments
- Fail-fast on unexpected arguments (unless **kwargs present)
- Full traceability of routing decisions
- Zero tolerance for silent parameter drops
"""

from __future__ import annotations

import inspect
import logging
import os
import random
import threading
from collections.abc import Iterable, Mapping, MutableMapping
from dataclasses import dataclass
from typing import (
    Any,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

import structlog

logger = structlog.get_logger(__name__)
std_logger = logging.getLogger(__name__)

# Sentinel value for missing arguments
MISSING: object = object()


# ============================================================================
# Base Exceptions and Data Classes
# ============================================================================

class ArgRouterError(RuntimeError):
    """Base exception for routing and validation issues."""


class ArgumentValidationError(ArgRouterError):
    """Raised when the provided payload does not match the method signature."""

    def __init__(
        self,
        class_name: str,
        method_name: str,
        *,
        missing: Iterable[str] | None = None,
        unexpected: Iterable[str] | None = None,
        type_mismatches: Mapping[str, str] | None = None,
    ) -> None:
        self.class_name = class_name
        self.method_name = method_name
        self.missing = set(missing or ())
        self.unexpected = set(unexpected or ())
        self.type_mismatches = dict(type_mismatches or {})
        detail = []
        if self.missing:
            detail.append(f"missing={sorted(self.missing)}")
        if self.unexpected:
            detail.append(f"unexpected={sorted(self.unexpected)}")
        if self.type_mismatches:
            detail.append(f"type_mismatches={self.type_mismatches}")
        message = (
            f"Invalid payload for {class_name}.{method_name}"
            + (f" ({'; '.join(detail)})" if detail else "")
        )
        super().__init__(message)


@dataclass(frozen=True)
class _ParameterSpec:
    name: str
    kind: inspect._ParameterKind
    default: Any
    annotation: Any

    @property
    def required(self) -> bool:
        return self.default is MISSING


@dataclass(frozen=True)
class MethodSpec:
    class_name: str
    method_name: str
    positional: tuple[_ParameterSpec, ...]
    keyword_only: tuple[_ParameterSpec, ...]
    has_var_keyword: bool
    has_var_positional: bool

    @property
    def required_arguments(self) -> tuple[str, ...]:
        required = tuple(
            spec.name
            for spec in (*self.positional, *self.keyword_only)
            if spec.required
        )
        return required

    @property
    def accepted_arguments(self) -> tuple[str, ...]:
        accepted = tuple(spec.name for spec in (*self.positional, *self.keyword_only))
        return accepted


# ============================================================================
# Base ArgRouter (Legacy - use ExtendedArgRouter instead)
# ============================================================================

class ArgRouter:
    """Resolve method call payloads based on inspected signatures.

    .. note::
        ExtendedArgRouter is the recommended router to use directly.
        This base class is provided for backward compatibility.
    """

    def __init__(self, class_registry: Mapping[str, type]) -> None:
        self._class_registry = dict(class_registry)
        self._spec_cache: dict[tuple[str, str], MethodSpec] = {}
        self._lock = threading.RLock()

    def describe(self, class_name: str, method_name: str) -> MethodSpec:
        """Return the cached method specification, building it if necessary."""
        key = (class_name, method_name)
        with self._lock:
            if key not in self._spec_cache:
                self._spec_cache[key] = self._build_spec(class_name, method_name)
            return self._spec_cache[key]

    def route(
        self,
        class_name: str,
        method_name: str,
        payload: MutableMapping[str, Any],
    ) -> tuple[tuple[Any, ...], dict[str, Any]]:
        """Validate and split a payload into positional and keyword arguments."""
        spec = self.describe(class_name, method_name)
        provided_keys = set(payload.keys())
        required = set(spec.required_arguments)
        accepted = set(spec.accepted_arguments)

        missing = required - provided_keys
        unexpected = provided_keys - accepted
        if unexpected and spec.has_var_keyword:
            unexpected = set()

        if missing or unexpected:
            raise ArgumentValidationError(
                class_name,
                method_name,
                missing=missing,
                unexpected=unexpected,
            )

        args: list[Any] = []
        kwargs: dict[str, Any] = {}
        type_mismatches: dict[str, str] = {}

        remaining = dict(payload)

        for param in spec.positional:
            if param.name not in remaining:
                if param.required:
                    missing = {param.name}
                    raise ArgumentValidationError(
                        class_name,
                        method_name,
                        missing=missing,
                    )
                continue
            value = remaining.pop(param.name)
            if not self._matches_annotation(value, param.annotation):
                expected = self._describe_annotation(param.annotation)
                type_mismatches[param.name] = expected
            args.append(value)

        for param in spec.keyword_only:
            if param.name not in remaining:
                if param.required:
                    raise ArgumentValidationError(
                        class_name,
                        method_name,
                        missing={param.name},
                    )
                continue
            value = remaining.pop(param.name)
            if not self._matches_annotation(value, param.annotation):
                expected = self._describe_annotation(param.annotation)
                type_mismatches[param.name] = expected
            kwargs[param.name] = value

        if spec.has_var_keyword and remaining:
            kwargs.update(remaining)
            remaining = {}

        if remaining:
            raise ArgumentValidationError(
                class_name,
                method_name,
                unexpected=set(remaining.keys()),
            )

        if type_mismatches:
            raise ArgumentValidationError(
                class_name,
                method_name,
                type_mismatches={
                    name: f"expected {expected}; received {type(payload[name]).__name__}"
                    for name, expected in type_mismatches.items()
                },
            )

        return tuple(args), kwargs

    def expected_arguments(self, class_name: str, method_name: str) -> tuple[str, ...]:
        spec = self.describe(class_name, method_name)
        return spec.accepted_arguments

    def _build_spec(self, class_name: str, method_name: str) -> MethodSpec:
        try:
            cls = self._class_registry[class_name]
        except KeyError as exc:  # pragma: no cover - defensive
            raise ArgRouterError(f"Unknown class '{class_name}'") from exc

        try:
            method = getattr(cls, method_name)
        except AttributeError as exc:
            raise ArgRouterError(f"Class '{class_name}' has no method '{method_name}'") from exc

        signature = inspect.signature(method)
        try:
            type_hints = get_type_hints(method)
        except Exception:
            type_hints = {}
        positional: list[_ParameterSpec] = []
        keyword_only: list[_ParameterSpec] = []
        has_var_keyword = False
        has_var_positional = False

        for parameter in signature.parameters.values():
            if parameter.name == "self":
                continue
            default = (
                parameter.default
                if parameter.default is not inspect._empty
                else MISSING
            )
            annotation = type_hints.get(parameter.name, parameter.annotation)
            param_spec = _ParameterSpec(
                name=parameter.name,
                kind=parameter.kind,
                default=default,
                annotation=annotation,
            )
            if parameter.kind in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            ):
                positional.append(param_spec)
            elif parameter.kind is inspect.Parameter.KEYWORD_ONLY:
                keyword_only.append(param_spec)
            elif parameter.kind is inspect.Parameter.VAR_KEYWORD:
                has_var_keyword = True
            elif parameter.kind is inspect.Parameter.VAR_POSITIONAL:
                has_var_positional = True

        return MethodSpec(
            class_name=class_name,
            method_name=method_name,
            positional=tuple(positional),
            keyword_only=tuple(keyword_only),
            has_var_keyword=has_var_keyword,
            has_var_positional=has_var_positional,
        )

    @staticmethod
    def _matches_annotation(value: Any, annotation: Any) -> bool:
        if annotation in (inspect._empty, Any):
            return True
        origin = get_origin(annotation)
        if origin is None:
            if isinstance(annotation, type):
                return isinstance(value, annotation)
            return True
        args = get_args(annotation)
        if origin is tuple:
            if not isinstance(value, tuple):
                return False
            if not args:
                return True
            if len(args) == 2 and args[1] is Ellipsis:
                return all(ArgRouter._matches_annotation(item, args[0]) for item in value)
            if len(args) != len(value):
                return False
            return all(
                ArgRouter._matches_annotation(item, arg_type)
                for item, arg_type in zip(value, args, strict=False)
            )
        if origin in (list, list):
            if not isinstance(value, list):
                return False
            if not args:
                return True
            return all(ArgRouter._matches_annotation(item, args[0]) for item in value)
        if origin in (set, set):
            if not isinstance(value, set):
                return False
            if not args:
                return True
            return all(ArgRouter._matches_annotation(item, args[0]) for item in value)
        if origin in (dict, dict):
            if not isinstance(value, dict):
                return False
            if len(args) != 2:
                return True
            key_type, value_type = args
            return all(
                ArgRouter._matches_annotation(k, key_type)
                and ArgRouter._matches_annotation(v, value_type)
                for k, v in value.items()
            )
        if origin is Union:
            return any(ArgRouter._matches_annotation(value, arg) for arg in args)
        return True

    @staticmethod
    def _describe_annotation(annotation: Any) -> str:
        if annotation in (inspect._empty, Any):
            return "Any"
        origin = get_origin(annotation)
        if origin is None:
            if isinstance(annotation, type):
                return annotation.__name__
            return str(annotation)
        args = get_args(annotation)
        if origin is tuple:
            return f"Tuple[{', '.join(ArgRouter._describe_annotation(arg) for arg in args)}]"
        if origin in (list, list):
            return f"List[{ArgRouter._describe_annotation(args[0])}]" if args else "List[Any]"
        if origin in (set, set):
            return f"Set[{ArgRouter._describe_annotation(args[0])}]" if args else "Set[Any]"
        if origin in (dict, dict):
            if len(args) == 2:
                return (
                    f"Dict[{ArgRouter._describe_annotation(args[0])}, "
                    f"{ArgRouter._describe_annotation(args[1])}]"
                )
            return "Dict[Any, Any]"
        if origin is Union:
            return " | ".join(ArgRouter._describe_annotation(arg) for arg in args)
        return str(annotation)


class PayloadDriftMonitor:
    """Sampling validator for ingress/egress payloads."""

    CRITICAL_KEYS = {
        "content": str,
        "pdq_context": (dict, type(None)),
    }

    def __init__(self, *, sample_rate: float, enabled: bool) -> None:
        self.sample_rate = max(0.0, min(sample_rate, 1.0))
        self.enabled = enabled and self.sample_rate > 0.0

    @classmethod
    def from_env(cls) -> PayloadDriftMonitor:
        enabled = os.getenv("ORCHESTRATOR_SAMPLING_VALIDATION", "").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        try:
            sample_rate = float(os.getenv("ORCHESTRATOR_SAMPLING_RATE", "0.05"))
        except ValueError:
            sample_rate = 0.05
        return cls(sample_rate=sample_rate, enabled=enabled)

    def maybe_validate(self, payload: Mapping[str, Any], *, producer: str, consumer: str) -> None:
        if not self.enabled:
            return
        if random.random() > self.sample_rate:
            return
        if not isinstance(payload, Mapping):
            return
        keys = set(payload.keys())
        if not keys.intersection(self.CRITICAL_KEYS):
            return

        missing = [key for key in self.CRITICAL_KEYS if key not in payload]
        type_mismatches = {
            key: self._expected_type_name(expected)
            for key, expected in self.CRITICAL_KEYS.items()
            if key in payload and not isinstance(payload[key], expected)
        }
        if missing or type_mismatches:
            std_logger.error(
                "Payload drift detected [%s -> %s]: missing=%s type_mismatches=%s",
                producer,
                consumer,
                missing,
                type_mismatches,
            )
        else:
            std_logger.debug(
                "Payload validation OK [%s -> %s]", producer, consumer
            )

    @staticmethod
    def _expected_type_name(expected: object) -> str:
        if isinstance(expected, tuple):
            return ", ".join(getattr(t, "__name__", str(t)) for t in expected)
        if hasattr(expected, "__name__"):
            return expected.__name__  # type: ignore[arg-type]
        return str(expected)


# ============================================================================
# Extended ArgRouter with Special Routes
# ============================================================================


@dataclass
class RoutingMetrics:
    """Metrics for monitoring routing behavior."""

    total_routes: int = 0
    special_routes_hit: int = 0
    default_routes_hit: int = 0
    validation_errors: int = 0
    silent_drops_prevented: int = 0


class ExtendedArgRouter(ArgRouter):
    """
    Extended argument router with special route handling.

    Extends base ArgRouter with:
    - 25+ special route definitions
    - Strict validation (no silent drops)
    - **kwargs awareness for forward compatibility
    - Comprehensive metrics

    Special Routes (≥25):
    1. _extract_quantitative_claims
    2. _parse_number
    3. _determine_semantic_role
    4. _compile_pattern_registry
    5. _analyze_temporal_coherence
    6. _validate_evidence_chain
    7. _calculate_confidence_score
    8. _extract_indicators
    9. _parse_temporal_reference
    10. _determine_policy_area
    11. _compile_regex_patterns
    12. _analyze_source_reliability
    13. _validate_numerical_consistency
    14. _calculate_bayesian_update
    15. _extract_entities
    16. _parse_citation
    17. _determine_validation_type
    18. _compile_indicator_patterns
    19. _analyze_coherence_score
    20. _validate_threshold_compliance
    21. _calculate_evidence_weight
    22. _extract_temporal_markers
    23. _parse_budget_allocation
    24. _determine_risk_level
    25. _compile_validation_rules
    26. _analyze_stakeholder_impact
    27. _validate_governance_structure
    28. _calculate_alignment_score
    29. _extract_constraint_declarations
    30. _parse_implementation_timeline
    """

    def __init__(self, class_registry: Mapping[str, type]) -> None:
        """
        Initialize extended router.

        Args:
            class_registry: Mapping of class names to class types
        """
        super().__init__(class_registry)
        self._special_routes = self._build_special_routes()
        self._metrics = RoutingMetrics()

        logger.info(
            "extended_arg_router_initialized",
            special_routes=len(self._special_routes),
            classes=len(class_registry),
        )

    def _build_special_routes(self) -> dict[str, dict[str, Any]]:
        """
        Build special route definitions for commonly-called methods.

        Each route specifies:
        - required_args: List of required parameter names
        - optional_args: List of optional parameter names
        - accepts_kwargs: Whether method accepts **kwargs
        - description: Human-readable description

        Returns:
            Dict mapping method names to route specs
        """
        routes = {
            "_extract_quantitative_claims": {
                "required_args": ["content"],
                "optional_args": ["context", "thresholds", "patterns"],
                "accepts_kwargs": True,
                "description": "Extract quantitative claims from content",
            },
            "_parse_number": {
                "required_args": ["text"],
                "optional_args": ["locale", "unit_system"],
                "accepts_kwargs": True,
                "description": "Parse numerical value from text",
            },
            "_determine_semantic_role": {
                "required_args": ["text", "context"],
                "optional_args": ["role_taxonomy", "confidence_threshold"],
                "accepts_kwargs": True,
                "description": "Determine semantic role of text element",
            },
            "_compile_pattern_registry": {
                "required_args": ["patterns"],
                "optional_args": ["category", "flags"],
                "accepts_kwargs": False,
                "description": "Compile patterns into regex registry",
            },
            "_analyze_temporal_coherence": {
                "required_args": ["content"],
                "optional_args": ["temporal_patterns", "baseline_date"],
                "accepts_kwargs": True,
                "description": "Analyze temporal coherence of content",
            },
            "_validate_evidence_chain": {
                "required_args": ["claims", "evidence"],
                "optional_args": ["validation_rules", "min_confidence"],
                "accepts_kwargs": True,
                "description": "Validate evidence chain for claims",
            },
            "_calculate_confidence_score": {
                "required_args": ["evidence"],
                "optional_args": ["prior", "weights"],
                "accepts_kwargs": True,
                "description": "Calculate Bayesian confidence score",
            },
            "_extract_indicators": {
                "required_args": ["content"],
                "optional_args": ["indicator_patterns", "extraction_mode"],
                "accepts_kwargs": True,
                "description": "Extract KPI indicators from content",
            },
            "_parse_temporal_reference": {
                "required_args": ["text"],
                "optional_args": ["reference_date", "format_hints"],
                "accepts_kwargs": True,
                "description": "Parse temporal reference from text",
            },
            "_determine_policy_area": {
                "required_args": ["content"],
                "optional_args": ["taxonomy", "multi_label"],
                "accepts_kwargs": True,
                "description": "Classify content into policy area",
            },
            "_compile_regex_patterns": {
                "required_args": ["pattern_list"],
                "optional_args": ["flags", "validate"],
                "accepts_kwargs": False,
                "description": "Compile list of regex patterns",
            },
            "_analyze_source_reliability": {
                "required_args": ["source"],
                "optional_args": ["source_patterns", "reliability_threshold"],
                "accepts_kwargs": True,
                "description": "Analyze reliability of information source",
            },
            "_validate_numerical_consistency": {
                "required_args": ["numbers"],
                "optional_args": ["tolerance", "consistency_rules"],
                "accepts_kwargs": True,
                "description": "Validate numerical consistency across values",
            },
            "_calculate_bayesian_update": {
                "required_args": ["prior", "likelihood", "evidence"],
                "optional_args": ["normalization"],
                "accepts_kwargs": True,
                "description": "Calculate Bayesian posterior update",
            },
            "_extract_entities": {
                "required_args": ["content"],
                "optional_args": ["entity_types", "confidence_threshold"],
                "accepts_kwargs": True,
                "description": "Extract named entities from content",
            },
            "_parse_citation": {
                "required_args": ["text"],
                "optional_args": ["citation_style", "strict_mode"],
                "accepts_kwargs": True,
                "description": "Parse citation from text",
            },
            "_determine_validation_type": {
                "required_args": ["validation_spec"],
                "optional_args": ["context"],
                "accepts_kwargs": True,
                "description": "Determine type of validation to apply",
            },
            "_compile_indicator_patterns": {
                "required_args": ["indicators"],
                "optional_args": ["category", "weights"],
                "accepts_kwargs": False,
                "description": "Compile indicator patterns for matching",
            },
            "_analyze_coherence_score": {
                "required_args": ["content"],
                "optional_args": ["coherence_patterns", "scoring_mode"],
                "accepts_kwargs": True,
                "description": "Analyze narrative coherence score",
            },
            "_validate_threshold_compliance": {
                "required_args": ["value", "thresholds"],
                "optional_args": ["strict_mode"],
                "accepts_kwargs": True,
                "description": "Validate value against thresholds",
            },
            "_calculate_evidence_weight": {
                "required_args": ["evidence"],
                "optional_args": ["weighting_scheme", "normalization"],
                "accepts_kwargs": True,
                "description": "Calculate evidence weight for scoring",
            },
            "_extract_temporal_markers": {
                "required_args": ["content"],
                "optional_args": ["temporal_patterns", "extraction_depth"],
                "accepts_kwargs": True,
                "description": "Extract temporal markers from content",
            },
            "_parse_budget_allocation": {
                "required_args": ["text"],
                "optional_args": ["currency", "fiscal_year"],
                "accepts_kwargs": True,
                "description": "Parse budget allocation from text",
            },
            "_determine_risk_level": {
                "required_args": ["indicators"],
                "optional_args": ["risk_thresholds", "aggregation_method"],
                "accepts_kwargs": True,
                "description": "Determine risk level from indicators",
            },
            "_compile_validation_rules": {
                "required_args": ["rules"],
                "optional_args": ["rule_format"],
                "accepts_kwargs": False,
                "description": "Compile validation rules for execution",
            },
            "_analyze_stakeholder_impact": {
                "required_args": ["stakeholders", "policy"],
                "optional_args": ["impact_dimensions", "time_horizon"],
                "accepts_kwargs": True,
                "description": "Analyze stakeholder impact of policy",
            },
            "_validate_governance_structure": {
                "required_args": ["structure"],
                "optional_args": ["governance_standards", "strict_mode"],
                "accepts_kwargs": True,
                "description": "Validate governance structure compliance",
            },
            "_calculate_alignment_score": {
                "required_args": ["policy_content", "reference_framework"],
                "optional_args": ["alignment_weights", "scoring_method"],
                "accepts_kwargs": True,
                "description": "Calculate alignment score with framework",
            },
            "_extract_constraint_declarations": {
                "required_args": ["content"],
                "optional_args": ["constraint_types", "extraction_mode"],
                "accepts_kwargs": True,
                "description": "Extract constraint declarations from content",
            },
            "_parse_implementation_timeline": {
                "required_args": ["text"],
                "optional_args": ["reference_date", "granularity"],
                "accepts_kwargs": True,
                "description": "Parse implementation timeline from text",
            },
        }

        return routes

    def route(
        self,
        class_name: str,
        method_name: str,
        payload: MutableMapping[str, Any],
    ) -> tuple[tuple[Any, ...], dict[str, Any]]:
        """
        Route method call with special handling and strict validation.

        This override:
        1. Checks for special route definitions
        2. Applies strict validation
        3. Prevents silent parameter drops
        4. Tracks metrics

        Args:
            class_name: Target class name
            method_name: Target method name
            payload: Method parameters

        Returns:
            Tuple of (args, kwargs) for method invocation

        Raises:
            ArgumentValidationError: On validation failure
        """
        self._metrics.total_routes += 1

        # Check for special route
        if method_name in self._special_routes:
            return self._route_special(class_name, method_name, payload)

        # Use default routing with enhanced validation
        return self._route_default_strict(class_name, method_name, payload)

    def _route_special(
        self,
        class_name: str,
        method_name: str,
        payload: MutableMapping[str, Any],
    ) -> tuple[tuple[Any, ...], dict[str, Any]]:
        """
        Route using special route definition.

        Args:
            class_name: Target class name
            method_name: Target method name
            payload: Method parameters

        Returns:
            Tuple of (args, kwargs)
        """
        self._metrics.special_routes_hit += 1

        route_spec = self._special_routes[method_name]
        required_args = set(route_spec["required_args"])
        optional_args = set(route_spec["optional_args"])
        accepts_kwargs = route_spec["accepts_kwargs"]

        provided_keys = set(payload.keys())

        # Check required arguments
        missing = required_args - provided_keys
        if missing:
            self._metrics.validation_errors += 1
            logger.error(
                "special_route_missing_args",
                class_name=class_name,
                method=method_name,
                missing=sorted(missing),
            )
            raise ArgumentValidationError(
                class_name,
                method_name,
                missing=missing,
            )

        # Check unexpected arguments
        expected = required_args | optional_args
        unexpected = provided_keys - expected

        if unexpected and not accepts_kwargs:
            # Method doesn't accept **kwargs, so unexpected args are an error
            self._metrics.validation_errors += 1
            self._metrics.silent_drops_prevented += 1

            logger.error(
                "special_route_unexpected_args",
                class_name=class_name,
                method=method_name,
                unexpected=sorted(unexpected),
                accepts_kwargs=accepts_kwargs,
            )
            raise ArgumentValidationError(
                class_name,
                method_name,
                unexpected=unexpected,
            )

        # Build kwargs (all parameters go to kwargs for special routes)
        kwargs = dict(payload)

        logger.debug(
            "special_route_applied",
            class_name=class_name,
            method=method_name,
            params_count=len(kwargs),
        )

        return (), kwargs

    def _route_default_strict(
        self,
        class_name: str,
        method_name: str,
        payload: MutableMapping[str, Any],
    ) -> tuple[tuple[Any, ...], dict[str, Any]]:
        """
        Route using default strategy with strict validation.

        This prevents silent parameter drops by failing when:
        - Required arguments are missing
        - Unexpected arguments are provided AND method lacks **kwargs

        Args:
            class_name: Target class name
            method_name: Target method name
            payload: Method parameters

        Returns:
            Tuple of (args, kwargs)
        """
        self._metrics.default_routes_hit += 1

        # Use base implementation for inspection
        spec = self.describe(class_name, method_name)

        # Strict validation: if unexpected args and no **kwargs, fail
        provided_keys = set(payload.keys())
        accepted = set(spec.accepted_arguments)
        unexpected = provided_keys - accepted

        if unexpected and not spec.has_var_keyword:
            # Method doesn't accept **kwargs - unexpected args are errors
            self._metrics.validation_errors += 1
            self._metrics.silent_drops_prevented += 1

            logger.error(
                "default_route_unexpected_args_strict",
                class_name=class_name,
                method=method_name,
                unexpected=sorted(unexpected),
                has_var_keyword=spec.has_var_keyword,
            )
            raise ArgumentValidationError(
                class_name,
                method_name,
                unexpected=unexpected,
            )

        # Delegate to base implementation
        try:
            result = super().route(class_name, method_name, payload)
            logger.debug(
                "default_route_applied",
                class_name=class_name,
                method=method_name,
            )
            return result
        except ArgumentValidationError:
            self._metrics.validation_errors += 1
            raise

    def get_special_route_coverage(self) -> int:
        """
        Get count of special routes defined.

        Returns:
            Number of special routes (target: ≥25)
        """
        return len(self._special_routes)

    def get_metrics(self) -> dict[str, Any]:
        """
        Get routing metrics.

        Returns:
            Dict with routing statistics
        """
        total = self._metrics.total_routes or 1  # Avoid division by zero

        return {
            "total_routes": self._metrics.total_routes,
            "special_routes_hit": self._metrics.special_routes_hit,
            "special_routes_coverage": len(self._special_routes),
            "default_routes_hit": self._metrics.default_routes_hit,
            "validation_errors": self._metrics.validation_errors,
            "silent_drops_prevented": self._metrics.silent_drops_prevented,
            "special_route_hit_rate": self._metrics.special_routes_hit / total,
            "error_rate": self._metrics.validation_errors / total,
        }

    def list_special_routes(self) -> list[dict[str, Any]]:
        """
        List all special routes with their specifications.

        Returns:
            List of route specifications
        """
        routes = []
        for method_name, spec in sorted(self._special_routes.items()):
            routes.append({
                "method_name": method_name,
                "required_args": spec["required_args"],
                "optional_args": spec["optional_args"],
                "accepts_kwargs": spec["accepts_kwargs"],
                "description": spec["description"],
            })
        return routes
