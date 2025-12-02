"""Legacy parameter loader - now wraps ParameterLoaderV2."""

from typing import Any

from farfan_pipeline.core.parameters import ParameterLoaderV2


class ParameterLoader:
    """Stub parameter loader for backward compatibility.

    Legacy wrapper around ParameterLoaderV2 for backward compatibility.
    DEPRECATED: Use ParameterLoaderV2.get(method_id, param_name) directly.
    """

    def __init__(self) -> None:
        pass

    def load(self) -> None:
        """No-op: ParameterLoaderV2 auto-loads."""
        pass

    def get(
        self, method_id: str, default: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Gets the parameters for a given method_id.
        Delegates to ParameterLoaderV2.
        """
        if default is None:
            default = {}

        params = ParameterLoaderV2.get_all(method_id)
        return params if params else default


_parameter_loader = ParameterLoader()


def get_parameter_loader() -> ParameterLoader:
    """Get the global parameter loader instance."""
    return _parameter_loader
