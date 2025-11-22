"""
Legacy contract loader shim.

This module exists only to satisfy historical imports. The canonical executor
contract loading path is implemented in BaseExecutorWithContract._load_contract.
Use that path instead of this loader for all new code.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class LoadError(RuntimeError):
    """Raised when legacy contract loading is invoked."""


@dataclass
class LoadResult:
    """Placeholder result for legacy contract loading."""

    contracts: dict[str, Any] | None = None
    errors: list[str] | None = None


class JSONContractLoader:
    """Legacy loader shim that fails fast.

    Contract executors should load contracts via BaseExecutorWithContract._load_contract,
    which validates against the canonical schema. This shim prevents silent fallbacks.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def load_file(self, *args: Any, **kwargs: Any) -> LoadResult:
        raise LoadError(
            "JSONContractLoader is obsolete. Use BaseExecutorWithContract._load_contract "
            "for executor contracts."
        )

    def load_directory(self, *args: Any, **kwargs: Any) -> LoadResult:
        raise LoadError(
            "JSONContractLoader is obsolete. Use BaseExecutorWithContract._load_contract "
            "for executor contracts."
        )

    def load_multiple(self, *args: Any, **kwargs: Any) -> LoadResult:
        raise LoadError(
            "JSONContractLoader is obsolete. Use BaseExecutorWithContract._load_contract "
            "for executor contracts."
        )


__all__ = ["JSONContractLoader", "LoadError", "LoadResult"]
