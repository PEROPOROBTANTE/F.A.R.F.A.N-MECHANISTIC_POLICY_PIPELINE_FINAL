"""Parameter Loader.

Singleton loader for method_parameters.json (System 1).
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

class ParameterLoader:
    _instance = None
    _data: Dict[str, Any] = {}
    _loaded = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ParameterLoader, cls).__new__(cls)
        return cls._instance

    def load(self, config_path: str = "config/method_parameters.json") -> None:
        """Load method parameters from JSON."""
        if self._loaded:
            return

        path = Path(config_path)
        if not path.exists():
            # Try finding it relative to repo root
            repo_root = Path(__file__).parent.parent.parent.parent.parent
            path = repo_root / config_path

        if not path.exists():
             logger.warning(f"Method parameters file not found at {path}. Using empty config.")
             self._data = {}
             self._loaded = True
             return

        try:
            with open(path, "r") as f:
                self._data = json.load(f)
            self._loaded = True
            logger.info(f"Loaded method parameters from {path}")
        except Exception as e:
            logger.error(f"Failed to load method parameters: {e}")
            self._data = {}

    def get(self, method_id: str) -> Dict[str, Any]:
        """Get parameters for a method."""
        if not self._loaded:
            self.load()
        return self._data.get(method_id, {})
