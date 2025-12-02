"""
FARFAN Mechanistic Policy Pipeline - Observability Module
==========================================================

OpenTelemetry-based observability for distributed tracing and monitoring.

Author: FARFAN Team
Date: 2025-11-13
Version: 1.0.0
"""

from .opentelemetry_integration import (
    ExecutorSpanDecorator,
    OpenTelemetryObservability,
    Span,
    SpanContext,
    SpanKind,
    SpanStatus,
    Tracer,
    executor_span,
    get_global_observability,
    get_tracer,
)

__all__ = [
    "ExecutorSpanDecorator",
    "OpenTelemetryObservability",
    "Span",
    "SpanContext",
    "SpanKind",
    "SpanStatus",
    "Tracer",
    "executor_span",
    "get_global_observability",
    "get_tracer",
]
