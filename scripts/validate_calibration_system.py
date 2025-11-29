#!/usr/bin/env python3
"""Shim: use scripts/validators/validate_calibration_system.py"""
from scripts.validators.validate_calibration_system import *  # noqa

if __name__ == "__main__":
    from scripts.validators.validate_calibration_system import main
    raise SystemExit(main())
