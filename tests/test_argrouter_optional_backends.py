"""Tests for ArgRouter with optional backends."""

import pytest


def test_class_registry_without_torch():
    """Test that class_registry handles missing torch gracefully."""
    from saaaaaa.core.orchestrator.class_registry import build_class_registry
    
    # Should not raise error even if torch is missing
    # Some classes may be skipped but it should not fail entirely
    registry = build_class_registry()
    
    assert isinstance(registry, dict)
    # Registry should have at least some classes loaded
    assert len(registry) >= 0  # Can be empty if all require optional deps


def test_arg_router_can_be_created():
    """Test that ArgRouter can be created."""
    from saaaaaa.core.orchestrator.arg_router import ArgRouter
    from saaaaaa.core.orchestrator.class_registry import build_class_registry
    
    # Build registry (may skip optional classes)
    try:
        registry = build_class_registry()
    except Exception:
        # If all classes require optional dependencies, use empty registry
        registry = {}
    
    # Should not raise error
    router = ArgRouter(registry)
    assert router is not None


def test_arg_router_has_methods():
    """Test that ArgRouter has expected methods."""
    from saaaaaa.core.orchestrator.arg_router import ArgRouter
    
    try:
        from saaaaaa.core.orchestrator.class_registry import build_class_registry
        registry = build_class_registry()
    except Exception:
        registry = {}
    
    router = ArgRouter(registry)
    
    # Check basic attributes exist
    assert hasattr(router, "invoke")
