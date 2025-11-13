"""Lightweight core package exposing shared typed contracts.

IMPORTANT: This is a COMPATIBILITY LAYER for backward compatibility only.
The real core contracts implementation is in src/saaaaaa/core/.

New code should import directly from saaaaaa.core, not from this
compatibility layer.
"""
from __future__ import annotations

from pathlib import Path

# Add src to path for development environments
_SRC_PATH = Path(__file__).resolve().parent.parent / "src"
if _SRC_PATH.exists():  # pragma: no cover - executed at import time
    src_str = str(_SRC_PATH)
from .contracts import IndustrialInput, IndustrialOutput  # noqa: E402

__all__ = ["IndustrialInput", "IndustrialOutput"]
