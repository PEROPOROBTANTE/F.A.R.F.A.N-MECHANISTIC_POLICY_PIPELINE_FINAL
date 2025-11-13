"""
Three-Pillar Calibration System

This package implements the SUPERPROMPT Three-Pillar Calibration System
for method calibration in the SAAAAAA policy-pipeline stack.

Main entry point: calibrate()
"""

from .engine import calibrate, CalibrationEngine
from .validators import validate_config_files, validate_certificate, CalibrationValidator
from .data_structures import (
    Context, ComputationGraph, CalibrationCertificate, 
    CalibrationSubject, EvidenceStore, LayerType, MethodRole
)

__all__ = [
    'calibrate',
    'CalibrationEngine',
    'validate_config_files',
    'validate_certificate',
    'CalibrationValidator',
    'Context',
    'ComputationGraph',
    'CalibrationCertificate',
    'CalibrationSubject',
    'EvidenceStore',
    'LayerType',
    'MethodRole',
]
