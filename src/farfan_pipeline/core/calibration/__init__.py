"""Calibration system - LEGACY STUB for backward compatibility.

This module provides minimal stubs to maintain backward compatibility
after calibration system cleanup. The actual calibration logic should
be migrated to the new structure.
"""

from .decorators import calibrated_method
from .parameter_loader import ParameterLoader, get_parameter_loader

__all__ = ["calibrated_method", "ParameterLoader", "get_parameter_loader"]
