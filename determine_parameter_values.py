#!/usr/bin/env python3
"""Backward-compatible shim. Uses scripts/generators/determine_parameter_values.py."""
from scripts.generators.determine_parameter_values import *  # noqa

if __name__ == "__main__":
    from scripts.generators.determine_parameter_values import main
    raise SystemExit(main())
