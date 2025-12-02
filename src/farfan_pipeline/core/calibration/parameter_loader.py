"""Parameter loader - LEGACY STUB for backward compatibility."""


class ParameterLoader:
    """Stub parameter loader for backward compatibility.

    Returns empty dictionaries for all parameter requests.
    """

    def get(self, method_id: str) -> dict[str, object]:  # noqa: ARG002
        """Return empty parameters for any method."""
        return {}


_instance: ParameterLoader | None = None


def get_parameter_loader() -> ParameterLoader:
    """Get singleton parameter loader instance."""
    global _instance  # noqa: PLW0603
    if _instance is None:
        _instance = ParameterLoader()
    return _instance
