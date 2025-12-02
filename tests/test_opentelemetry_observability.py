"""Tests for production OpenTelemetry integration.

Tests cover:
- Configuration and initialization
- Tracing functionality
- Metrics collection
- Executor instrumentation
- Pipeline instrumentation
- Context propagation

DEPRECATED: Test uses outdated farfan_core module path, should use farfan_pipeline.
See tests/DEPRECATED_TESTS.md for details.
"""

import pytest
from unittest.mock import MagicMock, patch

from farfan_core.observability import (
    OpenTelemetryConfig,
    FARFANObservability,
    get_global_observability,
    initialize_observability,
)

pytestmark = pytest.mark.obsolete


class TestOpenTelemetryConfig:
    """Test OpenTelemetry configuration."""
    
    def test_default_config(self):
        config = OpenTelemetryConfig()
        assert config.service_name == "farfan-pipeline"
        assert config.service_version == "1.0.0"
        assert config.prometheus_port == 9090
    
    def test_custom_config(self):
        config = OpenTelemetryConfig(
            service_name="test-service",
            service_version="2.0.0",
            prometheus_port=8080,
        )
        assert config.service_name == "test-service"
        assert config.service_version == "2.0.0"
        assert config.prometheus_port == 8080


class TestFARFANObservability:
    """Test main observability class."""
    
    @patch("farfan_core.observability.opentelemetry_integration.OTEL_AVAILABLE", False)
    def test_initialization_without_otel(self):
        obs = FARFANObservability()
        assert not obs._initialized
        assert obs.get_tracer() is None
        assert obs.get_meter() is None
    
    def test_start_span_without_otel(self):
        obs = FARFANObservability()
        obs._initialized = False
        
        with obs.start_span("test_span") as span:
            assert span is None
    
    def test_trace_executor_without_otel(self):
        obs = FARFANObservability()
        obs._initialized = False
        
        @obs.trace_executor("D1_Q1_TestExecutor")
        def test_execute(context):
            return {"result": "success"}
        
        result = test_execute({"test": "data"})
        assert result == {"result": "success"}
    
    def test_propagate_context_without_otel(self):
        obs = FARFANObservability()
        obs._initialized = False
        
        carrier = obs.propagate_context()
        assert carrier == {}


class TestGlobalObservability:
    """Test global observability singleton."""
    
    def test_get_global_observability(self):
        obs1 = get_global_observability()
        obs2 = get_global_observability()
        assert obs1 is obs2
    
    def test_initialize_observability(self):
        obs = initialize_observability(
            service_name="test-service",
            enable_jaeger=False,
            enable_prometheus=False,
            auto_instrument=False,
        )
        assert isinstance(obs, FARFANObservability)
        assert obs.config.service_name == "test-service"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
