"""Intrinsic Calibration Loader.

Singleton loader for intrinsic_calibration.json (System 2).
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class IntrinsicCalibrationLoader:
    _instance = None
    _data: Dict[str, Any] = {}
    _loaded = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(IntrinsicCalibrationLoader, cls).__new__(cls)
        return cls._instance

    def load(self, config_path: str = "config/intrinsic_calibration.json") -> None:
        """Load intrinsic calibration data from JSON."""
        if self._loaded:
            return

        path = Path(config_path)
        if not path.exists():
            # Try finding it relative to repo root if running from src
            repo_root = Path(__file__).parent.parent.parent.parent.parent
            path = repo_root / config_path
            
        if not path.exists():
             logger.warning(f"Intrinsic calibration file not found at {path}. Using empty config.")
             self._data = {}
             self._loaded = True
             return

        try:
            with open(path, "r") as f:
                self._data = json.load(f)
            self._loaded = True
            logger.info(f"Loaded intrinsic calibration from {path}")
        except Exception as e:
            logger.error(f"Failed to load intrinsic calibration: {e}")
            self._data = {}

    def get_intrinsic_score(self, method_id: str) -> float:
        """Get intrinsic score (@b) for a method."""
        if not self._loaded:
            self.load()
            
        method_data = self._data.get(method_id)
        if method_data:
            return method_data.get("intrinsic_score", 0.5)
        return 0.5

    def get_metadata(self, method_id: str) -> Optional[Dict[str, Any]]:
        """Get full metadata for a method."""
        if not self._loaded:
            self.load()
        return self._data.get(method_id)
