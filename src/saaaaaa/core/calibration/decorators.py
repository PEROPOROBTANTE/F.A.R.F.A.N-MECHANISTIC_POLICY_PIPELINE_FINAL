"""
Calibration enforcement decorators.

Provides @calibrated_method decorator to enforce calibration requirements
on all methods in the mechanistic policy pipeline.

ZERO TOLERANCE ENFORCEMENT:
- Methods must be registered in calibration system
- Methods must meet minimum quality thresholds
- Execution blocked if calibration fails
"""
import functools
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class CalibrationEnforcementError(Exception):
    """
    Raised when a method fails calibration enforcement.

    This is a HARD ERROR - execution cannot proceed without valid calibration.
    """
    pass


def calibrated_method(
    min_score: float = 0.0,
    role: Optional[str] = None,
    enforce: bool = True,
    log_score: bool = True
) -> Callable:
    """
    Decorator to enforce calibration requirements on methods.

    This decorator:
    1. Checks method exists in calibration system
    2. Retrieves calibration score
    3. Enforces minimum quality threshold
    4. Logs calibration info
    5. Raises exception if calibration fails (when enforce=True)

    Args:
        min_score: Minimum calibration score required (0.0-1.0)
                  Default 0.0 means no threshold enforcement
        role: Expected method role (analyzer, processor, executor, etc.)
             If specified, validates role matches
        enforce: If True, raises exception on calibration failure
                If False, logs warning but allows execution
        log_score: If True, logs calibration score for each invocation

    Returns:
        Decorated function with calibration enforcement

    Raises:
        CalibrationEnforcementError: When calibration check fails and enforce=True

    Usage:
        @calibrated_method(min_score=0.70, role="analyzer")
        def analyze_document(self, document: Document) -> Analysis:
            # Method implementation
            pass

        @calibrated_method(min_score=0.85, role="executor", enforce=True)
        def execute(self, context: ExecutionContext) -> Result:
            # Executor implementation - high standards enforced
            pass

    Example:
        >>> @calibrated_method(min_score=0.70)
        ... def my_analyzer(data):
        ...     return analyze(data)
        ...
        >>> my_analyzer(test_data)  # Will check calibration before execution
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Extract method identifier from function
            method_id = _get_method_id(func)

            try:
                # Import here to avoid circular dependencies
                from .intrinsic_loader import IntrinsicScoreLoader

                # Get singleton calibration loader
                loader = IntrinsicScoreLoader.get_instance()

                # Check if method is calibrated
                if not loader.is_calibrated(method_id):
                    error_msg = (
                        f"Method '{method_id}' is NOT in calibration system. "
                        f"All methods MUST be calibrated. "
                        f"Run calibration triage to add this method."
                    )

                    if enforce:
                        logger.error(
                            "calibration_enforcement_failed",
                            extra={
                                "method_id": method_id,
                                "reason": "not_calibrated",
                                "enforce": enforce
                            }
                        )
                        raise CalibrationEnforcementError(error_msg)
                    else:
                        logger.warning(
                            "calibration_missing_but_allowed",
                            extra={
                                "method_id": method_id,
                                "reason": "not_calibrated",
                                "enforce": False
                            }
                        )

                # Get calibration score
                score = loader.get_score(method_id, default=0.0)
                method_data = loader.get_method_data(method_id)

                # Check minimum score threshold
                if score < min_score:
                    error_msg = (
                        f"Method '{method_id}' calibration score {score:.3f} "
                        f"is below minimum threshold {min_score:.3f}. "
                        f"Method quality is insufficient for use."
                    )

                    if enforce:
                        logger.error(
                            "calibration_score_insufficient",
                            extra={
                                "method_id": method_id,
                                "score": score,
                                "min_score": min_score,
                                "enforce": enforce
                            }
                        )
                        raise CalibrationEnforcementError(error_msg)
                    else:
                        logger.warning(
                            "calibration_score_low_but_allowed",
                            extra={
                                "method_id": method_id,
                                "score": score,
                                "min_score": min_score,
                                "enforce": False
                            }
                        )

                # Check role if specified
                if role is not None and method_data is not None:
                    actual_role = method_data.get("layer", "unknown")
                    if actual_role != role:
                        error_msg = (
                            f"Method '{method_id}' has role '{actual_role}' "
                            f"but expected role '{role}'. "
                            f"Role mismatch indicates configuration error."
                        )

                        if enforce:
                            logger.error(
                                "calibration_role_mismatch",
                                extra={
                                    "method_id": method_id,
                                    "expected_role": role,
                                    "actual_role": actual_role,
                                    "enforce": enforce
                                }
                            )
                            raise CalibrationEnforcementError(error_msg)
                        else:
                            logger.warning(
                                "calibration_role_mismatch_but_allowed",
                                extra={
                                    "method_id": method_id,
                                    "expected_role": role,
                                    "actual_role": actual_role,
                                    "enforce": False
                                }
                            )

                # Log successful calibration check
                if log_score:
                    logger.info(
                        "calibrated_method_executed",
                        extra={
                            "method_id": method_id,
                            "score": score,
                            "min_score": min_score,
                            "passed": True
                        }
                    )

            except CalibrationEnforcementError:
                # Re-raise enforcement errors
                raise
            except Exception as e:
                # Calibration system error - handle gracefully
                error_msg = (
                    f"Calibration system error for method '{method_id}': {e}. "
                    f"This should not happen - check calibration system integrity."
                )

                if enforce:
                    logger.error(
                        "calibration_system_error",
                        extra={
                            "method_id": method_id,
                            "error": str(e),
                            "enforce": enforce
                        }
                    )
                    raise CalibrationEnforcementError(error_msg) from e
                else:
                    logger.warning(
                        "calibration_system_error_but_allowed",
                        extra={
                            "method_id": method_id,
                            "error": str(e),
                            "enforce": False
                        }
                    )

            # Execute the actual method
            return func(*args, **kwargs)

        return wrapper
    return decorator


def _get_method_id(func: Callable) -> str:
    """
    Extract method identifier from function.

    Constructs canonical method ID in format: module.Class.method

    Args:
        func: Function to extract ID from

    Returns:
        Canonical method identifier string

    Example:
        >>> def my_func(): pass
        >>> _get_method_id(my_func)
        '__main__.my_func'
    """
    # Get module name
    module = func.__module__

    # Get qualified name (includes class if method)
    qualname = func.__qualname__

    # Construct canonical ID
    return f"{module}.{qualname}"


# Convenience decorators with preset thresholds

def analyzer_method(func: Callable) -> Callable:
    """
    Decorator for analyzer methods (min_score=0.70, role="analyzer").

    Usage:
        @analyzer_method
        def analyze_text(self, text: str) -> Analysis:
            pass
    """
    return calibrated_method(min_score=0.70, role="analyzer")(func)


def executor_method(func: Callable) -> Callable:
    """
    Decorator for executor methods (min_score=0.70, role="executor", enforce=True).

    Executors have strict enforcement - must pass calibration.

    Usage:
        @executor_method
        def execute(self, context: ExecutionContext) -> Result:
            pass
    """
    return calibrated_method(min_score=0.70, role="executor", enforce=True)(func)


def processor_method(func: Callable) -> Callable:
    """
    Decorator for processor methods (min_score=0.65, role="processor").

    Usage:
        @processor_method
        def process_data(self, data: Data) -> ProcessedData:
            pass
    """
    return calibrated_method(min_score=0.65, role="processor")(func)


def validator_method(func: Callable) -> Callable:
    """
    Decorator for validator methods (min_score=0.75, role="validator", enforce=True).

    Validators have high standards - precision and reliability critical.

    Usage:
        @validator_method
        def validate_structure(self, structure: Structure) -> ValidationResult:
            pass
    """
    return calibrated_method(min_score=0.75, role="validator", enforce=True)(func)
