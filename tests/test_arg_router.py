"""Unit tests for the orchestrator argument router."""
from __future__ import annotations

import pytest

from saaaaaa.core.orchestrator.arg_router import ArgRouter, ArgumentValidationError

class SampleExecutor:
    """Test executor for routing validation."""

    def compute(self, x: int, y: int, *, flag: bool = False) -> int:
        """Compute a sample value."""
        return x + y if flag else x - y

    def optional(self, x: int, y: int = 10) -> int:
        """Compute with optional parameter."""
        return x + y

@pytest.fixture()
def router() -> ArgRouter:
    return ArgRouter({"SampleExecutor": SampleExecutor})

def test_route_honors_signature(router: ArgRouter) -> None:
    args, kwargs = router.route(
        "SampleExecutor", "compute", {"x": 4, "y": 2, "flag": True}
    )
    assert args == (4, 2)
    assert kwargs == {"flag": True}

def test_missing_argument_raises(router: ArgRouter) -> None:
    with pytest.raises(ArgumentValidationError) as excinfo:
        router.route("SampleExecutor", "compute", {"x": 4})
    assert excinfo.value.missing == {"y"}

def test_unexpected_argument_raises(router: ArgRouter) -> None:
    with pytest.raises(ArgumentValidationError) as excinfo:
        router.route("SampleExecutor", "compute", {"x": 1, "y": 2, "extra": 5})
    assert excinfo.value.unexpected == {"extra"}

def test_optional_parameters_use_sentinel(router: ArgRouter) -> None:
    args, kwargs = router.route("SampleExecutor", "optional", {"x": 3})
    assert args == (3,)
    assert kwargs == {}

def test_type_mismatch_raises(router: ArgRouter) -> None:
    with pytest.raises(ArgumentValidationError) as excinfo:
        router.route("SampleExecutor", "compute", {"x": "bad", "y": 2})
    type_msgs = excinfo.value.type_mismatches
    assert "x" in type_msgs
    assert "expected int" in type_msgs["x"]
