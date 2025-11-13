"""Compatibility wrapper exposing orchestrator executors.

IMPORTANT: This is a COMPATIBILITY LAYER for backward compatibility only.
The real executors implementation is in src/saaaaaa/core/orchestrator/executors.

New code should import directly from saaaaaa.core.orchestrator.executors,
not from this compatibility layer.
"""
from __future__ import annotations

from pathlib import Path

# Add src to path for development environments
_SRC_PATH = Path(__file__).resolve().parent.parent / "src"
if _SRC_PATH.exists():  # pragma: no cover - executed at import time
    src_str = str(_SRC_PATH)
from saaaaaa.core.orchestrator import executors as _executors  # noqa: E402

__all__ = getattr(_executors, "__all__", [])

for name in dir(_executors):
    if name.startswith("_"):
        continue
    globals()[name] = getattr(_executors, name)
