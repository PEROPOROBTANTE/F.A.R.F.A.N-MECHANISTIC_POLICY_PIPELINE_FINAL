"""
Pytest configuration for SIN_CARRETA compliant test suite.

This file ensures tests run with proper package imports via pip install -e .
No sys.path manipulation is allowed.
"""
import pytest
import sys
from pathlib import Path

# Verify package is properly installed (not via sys.path hacks)
try:
    import saaaaaa
except ImportError:
    pytest.exit(
        "ERROR: Package 'saaaaaa' not installed. "
        "Run 'pip install -e .' before running tests. "
        "SIN_CARRETA compliance: No sys.path manipulation allowed.",
        returncode=1
    )

# Add markers for test obsolescence protocol
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "obsolete: marks tests as obsolete per SIN_CARRETA protocol"
    )
