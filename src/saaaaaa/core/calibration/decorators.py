"""Calibration Decorators.

This module provides decorators to enforce the central calibration system.
"""

from functools import wraps
from dataclasses import dataclass
from typing import Any, Dict, Optional
import logging

from saaaaaa import get_calibration_orchestrator, get_parameter_loader

logger = logging.getLogger(__name__)

class CalibrationError(Exception):
    """Raised when calibration fails."""
    pass

@dataclass
class CalibratedResult:
    """Result wrapper for calibrated methods."""
    value: Any
    calibration_score: float
    layer_scores: Dict[str, float]
    metadata: Dict[str, Any]

def calibrated_method(method_id: str):
    """
    OBLIGATORY: Decorator that FORCES anchoring to the central system.
    
    USAGE:
        @calibrated_method("module.Class.method")
        def my_method(self, data):
            # Your code here
            return result
    
    The decorator:
    1. Loads parameters from JSON
    2. Executes the method
    3. Calibrates the result
    4. Validates and returns
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # 1. GET central system
            orchestrator = get_calibration_orchestrator()
            param_loader = get_parameter_loader()
            
            # 2. LOAD parameters
            params = param_loader.get(method_id)
            
            # Merge params into kwargs if they don't exist
            # This allows overriding from caller but defaults to JSON
            for k, v in params.items():
                if k not in kwargs:
                    kwargs[k] = v
            
            # 3. EXECUTE original method
            try:
                raw_result = func(self, *args, **kwargs)
            except Exception as e:
                logger.error(f"Method {method_id} execution failed: {e}")
                raise
            
            # 4. CALIBRATE result
            context = {
                "method_id": method_id,
                "args": args,
                "kwargs": kwargs,
                "instance": self,
                "raw_result": raw_result
            }
            
            try:
                calibration = orchestrator.calibrate(method_id, context)
            except Exception as e:
                logger.error(f"Calibration failed for {method_id}: {e}")
                # Fail safe or raise? Request implies strictness.
                raise CalibrationError(f"Calibration system failure: {e}")
            
            # 5. VALIDATE
            threshold = params.get("validation_threshold", 0.7)
            
            if calibration.final_score < threshold:
                logger.warning(
                    f"Method {method_id} failed calibration: "
                    f"score {calibration.final_score:.3f} < threshold {threshold}"
                )
                # Depending on strictness, we might raise or return a failure object.
                # The prompt example raised CalibrationError.
                raise CalibrationError(
                    f"Method {method_id} failed calibration: "
                    f"score {calibration.final_score:.3f} < threshold {threshold}"
                )
            
            # 6. RETURN result with metadata
            # If the method returns a complex object, we might want to attach metadata to it
            # Or return a wrapper. The prompt example returns CalibratedResult.
            # However, this changes the return type signature.
            # If the original code expects the raw result, this might break things.
            # BUT the prompt explicitly says: "return CalibratedResult"
            # So I will follow the prompt.
            
            return CalibratedResult(
                value=raw_result,
                calibration_score=calibration.final_score,
                layer_scores=calibration.layer_scores,
                metadata=calibration.metadata
            )
        
        return wrapper
    return decorator

# Need to import dataclasses
from dataclasses import dataclass
