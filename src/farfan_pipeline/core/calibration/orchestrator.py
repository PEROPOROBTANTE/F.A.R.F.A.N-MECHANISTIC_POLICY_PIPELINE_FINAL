"""Calibration orchestrator - LEGACY STUB for backward compatibility."""


class CalibrationOrchestrator:
    """Stub calibration orchestrator for backward compatibility."""

    def __init__(self, config: dict[str, object] | None = None) -> None:
        self.config = config or {}

    def get_calibration(self, method_id: str) -> dict[str, object]:  # noqa: ARG002
        """Return empty calibration for any method."""
        return {}
