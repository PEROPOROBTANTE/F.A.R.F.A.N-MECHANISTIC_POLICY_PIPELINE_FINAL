"""Saaaaaa Package Initialization.

Exposes central calibration singletons.
"""

from .core.calibration.orchestrator import CalibrationOrchestrator
from .core.calibration.parameter_loader import ParameterLoader

_calibration_orchestrator = None
_parameter_loader = None

def get_calibration_orchestrator() -> CalibrationOrchestrator:
    """
    OBLIGATORY: Single way to get the orchestrator.
    
    Singleton global - guarantees EVERYONE uses the same one.
    """
    global _calibration_orchestrator
    
    if _calibration_orchestrator is None:
        _calibration_orchestrator = CalibrationOrchestrator()
        _calibration_orchestrator.initialize()
    
    return _calibration_orchestrator

def get_parameter_loader() -> ParameterLoader:
    """
    OBLIGATORY: Single way to get the parameter loader.
    
    Singleton global - guarantees EVERYONE uses the same one.
    """
    global _parameter_loader
    
    if _parameter_loader is None:
        _parameter_loader = ParameterLoader()
        _parameter_loader.load()
    
    return _parameter_loader
