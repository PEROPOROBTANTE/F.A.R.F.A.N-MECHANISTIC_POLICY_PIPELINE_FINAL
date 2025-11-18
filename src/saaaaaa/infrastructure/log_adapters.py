"""
Logging adapter - Concrete implementation of LogPort.

Provides structured logging with different implementations.
For testing, use InMemoryLogAdapter instead.
"""

import logging
from typing import Any


class StandardLogAdapter:
    """Standard logging adapter using Python's logging module.

    Example:
        >>> log_port = StandardLogAdapter("my_module")
        >>> log_port.info("Processing started", document_id="123")
    """

    def __init__(self, name: str = "saaaaaa") -> None:
        self._logger = logging.getLogger(name)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        if kwargs:
            self._logger.debug(f"{message} {kwargs}")
        else:
            self._logger.debug(message)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        if kwargs:
            self._logger.info(f"{message} {kwargs}")
        else:
            self._logger.info(message)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        if kwargs:
            self._logger.warning(f"{message} {kwargs}")
        else:
            self._logger.warning(message)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        if kwargs:
            self._logger.error(f"{message} {kwargs}")
        else:
            self._logger.error(message)

class InMemoryLogAdapter:
    """In-memory logging adapter for testing.

    Stores log messages in a list instead of emitting them.

    Example:
        >>> log_port = InMemoryLogAdapter()
        >>> log_port.info("Test message", key="value")
        >>> assert len(log_port.messages) == 1
        >>> assert log_port.messages[0]["message"] == "Test message"
    """

    def __init__(self) -> None:
        self.messages: list[dict[str, Any]] = []

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self.messages.append({"level": "debug", "message": message, "data": kwargs})

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self.messages.append({"level": "info", "message": message, "data": kwargs})

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self.messages.append({"level": "warning", "message": message, "data": kwargs})

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        self.messages.append({"level": "error", "message": message, "data": kwargs})

    def clear(self) -> None:
        """Clear all log messages (for testing)."""
        self.messages.clear()

    def get_messages_by_level(self, level: str) -> list[dict[str, Any]]:
        """Get all messages of a specific level (for testing)."""
        return [msg for msg in self.messages if msg["level"] == level]

__all__ = [
    'StandardLogAdapter',
    'InMemoryLogAdapter',
]
