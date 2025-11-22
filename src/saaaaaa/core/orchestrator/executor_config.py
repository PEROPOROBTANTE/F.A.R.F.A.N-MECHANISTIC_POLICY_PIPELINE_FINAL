from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ExecutorConfig:
    """
    Lightweight configuration for executors.

    This is intentionally minimal and only covers the parameters currently
    referenced by wiring/bootstrap code. Extend cautiously if new executor
    settings are required.
    """

    max_tokens: int | None = None
    temperature: float | None = None
    timeout_s: float | None = None
    retry: int | None = None
    seed: int | None = None
    extra: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        # Basic type guards without altering semantics
        if self.max_tokens is not None and self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive when provided")
        if self.retry is not None and self.retry < 0:
            raise ValueError("retry must be non-negative when provided")


__all__ = ["ExecutorConfig"]
