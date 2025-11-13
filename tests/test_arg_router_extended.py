"""Tests for ExtendedArgRouter - Special Routes and Strict Validation.

These tests verify:
- 25+ special routes are defined
- Strict validation prevents silent parameter drops
- **kwargs awareness for forward compatibility
- Metrics tracking
"""

import pytest

from saaaaaa.core.orchestrator.arg_router import (
    ExtendedArgRouter,
    ArgumentValidationError,
)


# Stub classes for testing
class TestAnalyzer:
    """Test class with various method signatures."""
    
    def _extract_quantitative_claims(
        self,
        content: str,
        context: str = "",
        thresholds: dict[str, float] | None = None,
        **kwargs: object,
    ) -> list[dict[str, object]]:
        """Extract quantitative claims (accepts **kwargs)."""
        return []
    
    def _parse_number(
        self,
        text: str,
        locale: str = "en_US",
        **kwargs: object,
    ) -> float | None:
        """Parse number (accepts **kwargs)."""
        return None
    
    def _compile_pattern_registry(
        self,
        patterns: list[str],
        category: str = "GENERAL",
    ) -> dict[str, object]:
        """Compile patterns (no **kwargs)."""
        return {}
    
    def _regular_method(
        self,
        required_arg: str,
        optional_arg: int = 0,
    ) -> str:
        """Regular method without **kwargs."""
        return ""


@pytest.fixture
def router() -> ExtendedArgRouter:
    """Create router with test class registry."""
    return ExtendedArgRouter({"TestAnalyzer": TestAnalyzer})


def test_router_initialization(router: ExtendedArgRouter) -> None:
    """Test router initializes with special routes."""
    assert router is not None
    assert len(router._special_routes) >= 25


def test_special_route_coverage(router: ExtendedArgRouter) -> None:
    """Test that special route coverage meets target (≥25)."""
    coverage = router.get_special_route_coverage()
    
    assert coverage >= 25, f"Expected ≥25 special routes, got {coverage}"


def test_special_route_list(router: ExtendedArgRouter) -> None:
    """Test listing special routes."""
    routes = router.list_special_routes()
    
    assert len(routes) >= 25
    
    # Check structure
    for route in routes:
        assert "method_name" in route
        assert "required_args" in route
        assert "optional_args" in route
        assert "accepts_kwargs" in route
        assert "description" in route


def test_special_route_with_all_params(router: ExtendedArgRouter) -> None:
    """Test routing special method with all parameters."""
    payload = {
        "content": "test content",
        "context": "test context",
        "thresholds": {"min": 0.5},
        "extra_param": "should be accepted via kwargs",
    }
    
    args, kwargs = router.route("TestAnalyzer", "_extract_quantitative_claims", payload)
    
    # Should route all params to kwargs
    assert len(args) == 0
    assert "content" in kwargs
    assert "context" in kwargs
    assert "thresholds" in kwargs
    assert "extra_param" in kwargs


def test_special_route_missing_required(router: ExtendedArgRouter) -> None:
    """Test that missing required args raises error."""
    payload = {
        "context": "test context",  # Missing 'content'
    }
    
    with pytest.raises(ArgumentValidationError) as exc_info:
        router.route("TestAnalyzer", "_extract_quantitative_claims", payload)
    
    assert "content" in exc_info.value.missing


def test_special_route_no_kwargs_rejects_unexpected(router: ExtendedArgRouter) -> None:
    """Test that unexpected args are rejected for methods without **kwargs."""
    payload = {
        "patterns": ["pattern1", "pattern2"],
        "unexpected_param": "should cause error",
    }
    
    with pytest.raises(ArgumentValidationError) as exc_info:
        router.route("TestAnalyzer", "_compile_pattern_registry", payload)
    
    assert "unexpected_param" in exc_info.value.unexpected


def test_default_route_strict_validation(router: ExtendedArgRouter) -> None:
    """Test strict validation on default routes."""
    payload = {
        "required_arg": "test",
        "optional_arg": 42,
        "unexpected_param": "should cause error",
    }
    
    # Regular method without **kwargs should reject unexpected
    with pytest.raises(ArgumentValidationError) as exc_info:
        router.route("TestAnalyzer", "_regular_method", payload)
    
    assert "unexpected_param" in exc_info.value.unexpected


def test_default_route_accepts_expected(router: ExtendedArgRouter) -> None:
    """Test default route accepts expected parameters."""
    payload = {
        "required_arg": "test",
        "optional_arg": 42,
    }
    
    args, kwargs = router.route("TestAnalyzer", "_regular_method", payload)
    
    # Should succeed
    assert "required_arg" in kwargs or len(args) > 0


def test_metrics_tracking(router: ExtendedArgRouter) -> None:
    """Test that metrics are tracked."""
    # Perform some routes
    payload1 = {"content": "test"}
    payload2 = {"patterns": ["p1"]}
    payload3 = {"required_arg": "test"}
    
    try:
        router.route("TestAnalyzer", "_extract_quantitative_claims", payload1)
    except Exception:
        pass
    
    try:
        router.route("TestAnalyzer", "_compile_pattern_registry", payload2)
    except Exception:
        pass
    
    try:
        router.route("TestAnalyzer", "_regular_method", payload3)
    except Exception:
        pass
    
    metrics = router.get_metrics()
    
    assert "total_routes" in metrics
    assert "special_routes_hit" in metrics
    assert "default_routes_hit" in metrics
    assert "validation_errors" in metrics
    assert "silent_drops_prevented" in metrics
    assert "special_route_hit_rate" in metrics
    
    assert metrics["total_routes"] > 0


def test_silent_drop_prevention(router: ExtendedArgRouter) -> None:
    """Test that silent parameter drops are prevented."""
    payload = {
        "required_arg": "test",
        "optional_arg": 42,
        "should_not_be_silently_dropped": "value",
    }
    
    with pytest.raises(ArgumentValidationError):
        router.route("TestAnalyzer", "_regular_method", payload)
    
    metrics = router.get_metrics()
    assert metrics["silent_drops_prevented"] > 0


def test_kwargs_method_accepts_extra_params(router: ExtendedArgRouter) -> None:
    """Test that methods with **kwargs accept extra parameters."""
    payload = {
        "text": "123.45",
        "locale": "en_US",
        "future_param": "forward compatibility",
        "another_future_param": 42,
    }
    
    # Should not raise - method has **kwargs
    args, kwargs = router.route("TestAnalyzer", "_parse_number", payload)
    
    assert "text" in kwargs
    assert "future_param" in kwargs
    assert "another_future_param" in kwargs


@pytest.mark.parametrize("method_name", [
    "_extract_quantitative_claims",
    "_parse_number",
    "_determine_semantic_role",
    "_compile_pattern_registry",
    "_analyze_temporal_coherence",
    "_validate_evidence_chain",
    "_calculate_confidence_score",
    "_extract_indicators",
    "_parse_temporal_reference",
    "_determine_policy_area",
])
def test_specific_special_routes_defined(router: ExtendedArgRouter, method_name: str) -> None:
    """Test that specific special routes are defined."""
    assert method_name in router._special_routes


def test_all_30_routes_defined(router: ExtendedArgRouter) -> None:
    """Test that all 30 target routes are defined."""
    expected_routes = [
        "_extract_quantitative_claims",
        "_parse_number",
        "_determine_semantic_role",
        "_compile_pattern_registry",
        "_analyze_temporal_coherence",
        "_validate_evidence_chain",
        "_calculate_confidence_score",
        "_extract_indicators",
        "_parse_temporal_reference",
        "_determine_policy_area",
        "_compile_regex_patterns",
        "_analyze_source_reliability",
        "_validate_numerical_consistency",
        "_calculate_bayesian_update",
        "_extract_entities",
        "_parse_citation",
        "_determine_validation_type",
        "_compile_indicator_patterns",
        "_analyze_coherence_score",
        "_validate_threshold_compliance",
        "_calculate_evidence_weight",
        "_extract_temporal_markers",
        "_parse_budget_allocation",
        "_determine_risk_level",
        "_compile_validation_rules",
        "_analyze_stakeholder_impact",
        "_validate_governance_structure",
        "_calculate_alignment_score",
        "_extract_constraint_declarations",
        "_parse_implementation_timeline",
    ]
    
    for route in expected_routes:
        assert route in router._special_routes, f"Route {route} not defined"


def test_route_spec_structure(router: ExtendedArgRouter) -> None:
    """Test that route specs have correct structure."""
    for method_name, spec in router._special_routes.items():
        assert "required_args" in spec, f"{method_name} missing required_args"
        assert "optional_args" in spec, f"{method_name} missing optional_args"
        assert "accepts_kwargs" in spec, f"{method_name} missing accepts_kwargs"
        assert "description" in spec, f"{method_name} missing description"
        
        assert isinstance(spec["required_args"], list)
        assert isinstance(spec["optional_args"], list)
        assert isinstance(spec["accepts_kwargs"], bool)
        assert isinstance(spec["description"], str)


def test_metrics_reset_on_new_router() -> None:
    """Test that metrics start at zero for new router."""
    new_router = ExtendedArgRouter({"TestAnalyzer": TestAnalyzer})
    metrics = new_router.get_metrics()
    
    assert metrics["total_routes"] == 0
    assert metrics["special_routes_hit"] == 0
    assert metrics["default_routes_hit"] == 0
    assert metrics["validation_errors"] == 0
    assert metrics["silent_drops_prevented"] == 0
