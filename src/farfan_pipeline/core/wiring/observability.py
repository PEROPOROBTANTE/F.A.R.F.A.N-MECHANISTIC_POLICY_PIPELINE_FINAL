"""Observability instrumentation for wiring system.

Provides OpenTelemetry tracing and structured logging for all wiring operations.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from collections.abc import Iterator

try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode

    HAS_OTEL = True
    tracer = trace.get_tracer("farfan_core.wiring")
except ImportError:
    HAS_OTEL = False
    tracer = None


logger = structlog.get_logger(__name__)


@contextmanager
def trace_wiring_link(
    link_name: str,
    **attributes: Any,
) -> Iterator[dict[str, Any]]:
    """Trace a wiring link operation.

    Creates an OpenTelemetry span (if available) and logs structured messages.

    Args:
        link_name: Name of the wiring link (e.g., "cpp->adapter")
        **attributes: Additional attributes to include in span/log

    Yields:
        Dict for adding dynamic attributes during operation

    Example:
        with trace_wiring_link("cpp->adapter", document_id="doc123") as attrs:
            result = adapter.convert(cpp)
            attrs["chunk_count"] = len(result.chunks)
    """
    start_time = time.time()
    dynamic_attrs: dict[str, Any] = {}

    # Start span if OpenTelemetry is available
    span = None
    if HAS_OTEL and tracer:
        span = tracer.start_span(f"wiring.link.{link_name}")
        span.set_attribute("link", link_name)
        for key, value in attributes.items():
            if isinstance(value, (str, int, float, bool)):
                span.set_attribute(key, value)

    # Log start
    logger.info(
        "wiring_link_start",
        link=link_name,
        **attributes,
    )

    try:
        yield dynamic_attrs

        # Success
        latency_ms = (time.time() - start_time) * 1000

        if span:
            span.set_attribute("latency_ms", latency_ms)
            span.set_attribute("ok", True)
            for key, value in dynamic_attrs.items():
                if isinstance(value, (str, int, float, bool)):
                    span.set_attribute(key, value)
            span.set_status(Status(StatusCode.OK))

        logger.info(
            "wiring_link_complete",
            link=link_name,
            latency_ms=latency_ms,
            ok=True,
            **attributes,
            **dynamic_attrs,
        )

    except Exception as e:
        # Failure
        latency_ms = (time.time() - start_time) * 1000

        if span:
            span.set_attribute("latency_ms", latency_ms)
            span.set_attribute("ok", False)
            span.set_attribute("error_type", type(e).__name__)
            span.set_attribute("error_message", str(e))
            span.set_status(Status(StatusCode.ERROR, str(e)))

        logger.error(
            "wiring_link_failed",
            link=link_name,
            latency_ms=latency_ms,
            ok=False,
            error_type=type(e).__name__,
            error_message=str(e),
            **attributes,
        )

        raise

    finally:
        if span:
            span.end()


@contextmanager
def trace_wiring_init(
    phase: str,
    **attributes: Any,
) -> Iterator[dict[str, Any]]:
    """Trace a wiring initialization phase.

    Args:
        phase: Name of initialization phase
        **attributes: Additional attributes

    Yields:
        Dict for adding dynamic attributes
    """
    start_time = time.time()
    dynamic_attrs: dict[str, Any] = {}

    span = None
    if HAS_OTEL and tracer:
        span = tracer.start_span(f"wiring.init.{phase}")
        span.set_attribute("phase", phase)
        for key, value in attributes.items():
            if isinstance(value, (str, int, float, bool)):
                span.set_attribute(key, value)

    logger.info(
        "wiring_init_start",
        phase=phase,
        **attributes,
    )

    try:
        yield dynamic_attrs

        latency_ms = (time.time() - start_time) * 1000

        if span:
            span.set_attribute("latency_ms", latency_ms)
            span.set_attribute("ok", True)
            for key, value in dynamic_attrs.items():
                if isinstance(value, (str, int, float, bool)):
                    span.set_attribute(key, value)
            span.set_status(Status(StatusCode.OK))

        logger.info(
            "wiring_init_complete",
            phase=phase,
            latency_ms=latency_ms,
            ok=True,
            **attributes,
            **dynamic_attrs,
        )

    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000

        if span:
            span.set_attribute("latency_ms", latency_ms)
            span.set_attribute("ok", False)
            span.set_attribute("error_type", type(e).__name__)
            span.set_attribute("error_message", str(e))
            span.set_status(Status(StatusCode.ERROR, str(e)))

        logger.error(
            "wiring_init_failed",
            phase=phase,
            latency_ms=latency_ms,
            ok=False,
            error_type=type(e).__name__,
            error_message=str(e),
            **attributes,
        )

        raise

    finally:
        if span:
            span.end()


def log_wiring_metric(
    metric_name: str,
    value: float | int,
    **labels: Any,
) -> None:
    """Log a wiring metric.

    Args:
        metric_name: Name of the metric
        value: Metric value
        **labels: Metric labels
    """
    logger.info(
        "wiring_metric",
        metric=metric_name,
        value=value,
        **labels,
    )


__all__ = [
    'trace_wiring_link',
    'trace_wiring_init',
    'log_wiring_metric',
    'HAS_OTEL',
]
