#!/usr/bin/env python3
"""Backward-compatible shim. Uses scripts/generators/rigorous_calibration_triage.py."""
from scripts.generators.rigorous_calibration_triage import *  # noqa

if __name__ == "__main__":
    from scripts.generators.rigorous_calibration_triage import main
    raise SystemExit(main())
