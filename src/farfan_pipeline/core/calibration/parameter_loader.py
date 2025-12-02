from typing import Any, Dict
from .calibration_registry import CALIBRATIONS

class ParameterLoader:
    """
    Loads and provides access to calibration parameters.
    """
    def __init__(self):
        self._params: Dict[str, Dict[str, Any]] | None = None

    def load(self):
        """
        Loads parameters from the central registry.
        """
        self._params = CALIBRATIONS

    def get(self, method_id: str, default: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Gets the parameters for a given method_id.
        """
        if self._params is None:
            self.load()

        if default is None:
            default = {}

        return self._params.get(method_id, default)
