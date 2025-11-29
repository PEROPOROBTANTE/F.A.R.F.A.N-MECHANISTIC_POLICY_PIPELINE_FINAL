#!/usr/bin/env python3
"""Shim: use scripts/validators/verify_no_hardcoded_calibrations.py"""
from scripts.validators.verify_no_hardcoded_calibrations import *  # noqa

if __name__ == "__main__":
    from scripts.validators.verify_no_hardcoded_calibrations import main
    raise SystemExit(main())
