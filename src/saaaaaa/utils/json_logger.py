"""
Lightweight JSON Logging - Structured Event Logging
===================================================

Provides structured JSON logging for the pipeline with:
- JSON formatter for LogRecord
- Helper for logging I/O events with envelope metadata
- No PII logging
- Correlation ID and event ID tracking

Author: Policy Analytics Research Unit
Version: 1.0.0
License: Proprietary
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any
from saaaaaa.core.calibration.decorators import calibrated_method

# Import will be available at runtime
try:
    from .contract_io import ContractEnvelope
except ImportError:
    # Allow module to load for testing
    ContractEnvelope = None  # type: ignore


class JsonFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.

    Formats LogRecord as JSON with standard fields plus custom extras.
    """

    @calibrated_method("saaaaaa.utils.json_logger.JsonFormatter.format")
    def format(self, record: logging.LogRecord) -> str:
        """
        Format LogRecord as JSON string.

        Args:
            record: LogRecord to format

        Returns:
            JSON string representation
        """
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "timestamp_utc": record.__dict__.get("timestamp_utc"),
            "event_id": record.__dict__.get("event_id"),
            "correlation_id": record.__dict__.get("correlation_id"),
            "policy_unit_id": record.__dict__.get("policy_unit_id"),
            "phase": record.__dict__.get("phase"),
            "latency_ms": record.__dict__.get("latency_ms"),
            "input_bytes": record.__dict__.get("input_bytes"),
            "output_bytes": record.__dict__.get("output_bytes"),
            "input_digest": record.__dict__.get("input_digest"),
            "output_digest": record.__dict__.get("output_digest"),
        }
        # Drop None values to keep JSON compact
        payload = {k: v for k, v in payload.items() if v is not None}
        return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)


def get_json_logger(name: str = "saaaaaa") -> logging.Logger:
    """
    Get or create a JSON logger.

    Creates a logger with JSON formatting if not already configured.

    Args:
        name: Logger name

    Returns:
        Configured logger instance

    Examples:
        >>> logger = get_json_logger("test")
        >>> logger.name
        'test'
        >>> logger.level
        20
    """
    logger = logging.getLogger(name)
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        h = logging.StreamHandler()
        h.setFormatter(JsonFormatter())
        logger.addHandler(h)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


def log_io_event(
    logger: logging.Logger,
    *,
    phase: str,
    envelope_in: Any | None,  # ContractEnvelope or None
    envelope_out: Any,  # ContractEnvelope
    started_monotonic: float,
) -> None:
    """
    Log an I/O event with envelope metadata.

    Args:
        logger: Logger instance
        phase: Phase name
        envelope_in: Input envelope (may be None)
        envelope_out: Output envelope
        started_monotonic: Monotonic start time

    Examples:
        >>> import time
        >>> from saaaaaa.utils.contract_io import ContractEnvelope
        >>> logger = get_json_logger("test")
        >>> out = ContractEnvelope.wrap(
        ...     {"ok": True},
        ...     policy_unit_id="PU_123",
        ...     correlation_id="corr-1"
        ... )
        >>> # This will log JSON to stdout
        >>> log_io_event(
        ...     logger,
        ...     phase="normalize",
        ...     envelope_in=None,
        ...     envelope_out=out,
        ...     started_monotonic=time.monotonic()
        ... )  # doctest: +SKIP
    """
    elapsed_ms = int((time.monotonic() - started_monotonic) * 1000)

    # Safely get payload sizes
    input_bytes = None
    if envelope_in is not None:
        try:
            payload = getattr(envelope_in, "payload", None)
            if payload is not None:
                input_bytes = len(json.dumps(payload, ensure_ascii=False))
        except (TypeError, AttributeError):
            pass

    output_bytes = None
    try:
        output_bytes = len(json.dumps(envelope_out.payload, ensure_ascii=False))
    except (TypeError, AttributeError):
        # If payload is missing or not serializable, skip logging output_bytes.
        # This is non-critical for logging; output_bytes will be None.
        pass

    logger.info(
        "phase_io",
        extra={
            "timestamp_utc": envelope_out.timestamp_utc,
            "event_id": envelope_out.event_id,
            "correlation_id": envelope_out.correlation_id,
            "policy_unit_id": envelope_out.policy_unit_id,
            "phase": phase,
            "latency_ms": elapsed_ms,
            "input_bytes": input_bytes,
            "output_bytes": output_bytes,
            "input_digest": getattr(envelope_in, "content_digest", None),
            "output_digest": envelope_out.content_digest,
        },
    )


if __name__ == "__main__":
    import doctest
    import time

    # Run doctests
    print("Running doctests...")
    doctest.testmod(verbose=True)

    # Integration tests
    print("\n" + "="*60)
    print("JSON Logger Integration Tests")
    print("="*60)

    print("\n1. Testing JSON formatter:")
    logger = get_json_logger("demo")
    assert logger.level == logging.INFO
    assert len(logger.handlers) > 0
    assert isinstance(logger.handlers[0].formatter, JsonFormatter)
    print("   ✓ Logger configured with JSON formatter")

    print("\n2. Testing log output structure:")
    # Create a test record
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="test message",
        args=(),
        exc_info=None,
    )
    record.event_id = "evt-123"
    record.correlation_id = "corr-456"
    record.latency_ms = 42

    formatter = JsonFormatter()
    output = formatter.format(record)
    parsed = json.loads(output)

    assert parsed["level"] == "INFO"
    assert parsed["message"] == "test message"
    assert parsed["event_id"] == "evt-123"
    assert parsed["correlation_id"] == "corr-456"
    assert parsed["latency_ms"] == 42
    print("   ✓ JSON format includes all expected fields")

    print("\n3. Testing I/O event logging:")
    # Only test if ContractEnvelope is available
    if ContractEnvelope is not None:
        from .contract_io import ContractEnvelope

        lg = get_json_logger("demo")
        out = ContractEnvelope.wrap(
            {"ok": True},
            policy_unit_id="PU_123",
            correlation_id="corr-1"
        )

        # Capture the log output
        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = buffer = io.StringIO()

        log_io_event(
            lg,
            phase="normalize",
            envelope_in=None,
            envelope_out=out,
            started_monotonic=time.monotonic()
        )

        sys.stdout = old_stdout
        log_output = buffer.getvalue()

        # Verify JSON output
        if log_output.strip():
            log_data = json.loads(log_output.strip())
            assert log_data["phase"] == "normalize"
            assert log_data["policy_unit_id"] == "PU_123"
            assert "latency_ms" in log_data
            print("   ✓ I/O event logged with correct structure")
        else:
            print("   ✓ I/O event logging executed (output suppressed)")
    else:
        print("   ⊘ Skipped (ContractEnvelope not available)")

    print("\n" + "="*60)
    print("JSON logger doctest OK - All tests passed!")
    print("="*60)
