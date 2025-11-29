#!/usr/bin/env python3
"""Backward-compatible shim. Uses scripts/generators/determine_parameter_values_v3.py."""
from scripts.generators.determine_parameter_values_v3 import *  # noqa

if __name__ == "__main__":
    from scripts.generators.determine_parameter_values_v3 import main
    raise SystemExit(main())
