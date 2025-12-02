"""Calibration decorators - LEGACY STUB for backward compatibility."""

import functools
from collections.abc import Callable
from typing import TypeVar

_F = TypeVar("_F", bound=Callable[..., object])


def calibrated_method(method_id: str) -> Callable[[_F], _F]:  # noqa: ARG001
    """No-op decorator for backward compatibility.

    Previously used to apply calibration parameters to methods.
    Now serves as a marker for methods that were calibrated.
    """

    def decorator(func: _F) -> _F:
        @functools.wraps(func)
        def wrapper(*args: object, **kwargs: object) -> object:
            return func(*args, **kwargs)  # type: ignore[call-arg]

        return wrapper  # type: ignore[return-value]

    return decorator
