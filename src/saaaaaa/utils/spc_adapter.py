"""SPC to Orchestrator Adapter (Shim).

This module is a shim for backward compatibility. The canonical implementation
has been moved to `saaaaaa.utils.cpp_adapter` to align with the Canon Policy Package (CPP)
terminology.

Please use `saaaaaa.utils.cpp_adapter.CPPAdapter` instead.
"""

from __future__ import annotations

import warnings
from saaaaaa.utils.cpp_adapter import (
from saaaaaa.core.calibration.decorators import calibrated_method
    CPPAdapter as SPCAdapter,
    CPPAdapterError as SPCAdapterError,
    adapt_cpp_to_orchestrator as adapt_spc_to_orchestrator
)

# Issue deprecation warning when module is imported
warnings.warn(
    "saaaaaa.utils.spc_adapter is deprecated. Use saaaaaa.utils.cpp_adapter instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = [
    'SPCAdapter',
    'SPCAdapterError',
    'adapt_spc_to_orchestrator',
]
