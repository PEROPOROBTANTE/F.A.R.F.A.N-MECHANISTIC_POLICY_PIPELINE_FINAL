#!/usr/bin/env python3
"""Fail fast if multiple live calibration/parameter files exist in config/.

Rules:
- Only one `intrinsic_calibration*.json` allowed in config/ (primario).
- Only one `method_parameters*.json` allowed in config/ (primario).
- Duplicates permitted in `config/secundarios_sistema_c_y_p/`.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO_ROOT / "config"
SECONDARY_ROOT = CONFIG_DIR / "secundarios_sistema_c_y_p"


def _is_secondary(path: Path) -> bool:
    try:
        path.relative_to(SECONDARY_ROOT)
        return True
    except ValueError:
        return False


def _gather(pattern: str) -> list[Path]:
    return [p for p in CONFIG_DIR.glob(pattern) if p.is_file() and not _is_secondary(p)]


def _describe(path: Path) -> str:
    meta = {}
    try:
        data = json.loads(path.read_text())
        meta = data.get("_metadata") if isinstance(data, dict) else {}
    except Exception:
        pass
    status = meta.get("status") if isinstance(meta, dict) else None
    live_flag = None
    if isinstance(data := locals().get("data"), dict):
        live_flag = data.get("_live")
    return f"{path} (status={status}, _live={live_flag})"


def main() -> int:
    intrinsic = _gather("intrinsic_calibration*.json")
    params = _gather("method_parameters*.json")

    errors = []
    if len(intrinsic) > 1:
        errors.append("Multiple intrinsic_calibration files in config/:\n  " + "\n  ".join(_describe(p) for p in intrinsic))
    if len(params) > 1:
        errors.append("Multiple method_parameters files in config/:\n  " + "\n  ".join(_describe(p) for p in params))

    # Presence check for clarity
    if not intrinsic:
        errors.append("No intrinsic_calibration.json found in config/")
    if not params:
        errors.append("No method_parameters.json found in config/")

    if errors:
        for msg in errors:
            sys.stderr.write(msg + "\n")
        return 1

    print("OK: single primaries present in config/; extras only allowed under secundarios_sistema_c_y_p/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
