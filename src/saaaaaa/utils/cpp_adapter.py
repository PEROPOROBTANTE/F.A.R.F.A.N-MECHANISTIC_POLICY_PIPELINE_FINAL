"""
DEPRECATED: CPP Adapter (Compatibility Wrapper)

This module provides backward compatibility for code using the old CPPAdapter name.
All functionality has been moved to spc_adapter.py with the SPCAdapter class.

CPP (Canon Policy Package) has been renamed to SPC (Smart Policy Chunks).
Please update your imports to use SPCAdapter from spc_adapter.

This wrapper will be removed in a future version.
"""

import warnings

# Import everything from the new module
# Note: This must use absolute imports to avoid circular import
from saaaaaa.utils.spc_adapter import (
    SPCAdapter as _SPCAdapter,
)
from saaaaaa.utils.spc_adapter import (
    SPCAdapterError as _SPCAdapterError,
)
from saaaaaa.utils.spc_adapter import (
    adapt_spc_to_orchestrator as _adapt_spc_to_orchestrator,
)

__all__ = ["CPPAdapter", "CPPAdapterError", "adapt_cpp_to_orchestrator"]


class CPPAdapter(_SPCAdapter):
    """
    DEPRECATED: Use SPCAdapter from spc_adapter instead.

    This is a compatibility wrapper that will be removed in a future version.
    """

    def __init__(self) -> None:
        warnings.warn(
            "CPPAdapter is deprecated, use SPCAdapter from saaaaaa.utils.spc_adapter instead",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__()


class CPPAdapterError(_SPCAdapterError):
    """
    DEPRECATED: Use SPCAdapterError from spc_adapter instead.

    This is a compatibility wrapper that will be removed in a future version.
    """
    pass


def adapt_cpp_to_orchestrator(*args, **kwargs):
    """
    DEPRECATED: Use adapt_spc_to_orchestrator from spc_adapter instead.

    This is a compatibility wrapper that will be removed in a future version.
    """
    warnings.warn(
        "adapt_cpp_to_orchestrator is deprecated, use adapt_spc_to_orchestrator from saaaaaa.utils.spc_adapter instead",
        DeprecationWarning,
        stacklevel=2
    )
    return _adapt_spc_to_orchestrator(*args, **kwargs)
