"""SPC to Orchestrator Adapter (Shim).

This module is a shim for backward compatibility. The canonical implementation
has been moved to `farfan_core.utils.cpp_adapter` to align with the Canon Policy Package (CPP)
terminology.

Please use `farfan_core.utils.cpp_adapter.CPPAdapter` instead.
"""

from __future__ import annotations

import warnings
from farfan_pipeline.utils.cpp_adapter import (
    CPPAdapter as SPCAdapter,
    CPPAdapterError as SPCAdapterError,
    adapt_cpp_to_orchestrator as adapt_spc_to_orchestrator
)
from farfan_pipeline.core.calibration.decorators import calibrated_method

# Issue deprecation warning when module is imported
warnings.warn(
    "farfan_core.utils.spc_adapter is deprecated. Use farfan_core.utils.cpp_adapter instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = [
    'SPCAdapter',
    'SPCAdapterError',
    'adapt_spc_to_orchestrator',
]
