"""
Pytest configuration for SIN_CARRETA compliant test suite.

This file ensures tests run with proper package imports via pip install -e .
No sys.path manipulation is allowed.
"""
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

# Verify package is properly installed (not via sys.path hacks)
try:
    import saaaaaa  # noqa: F401
except ImportError:
    pytest.exit(
        "ERROR: Package 'saaaaaa' not installed. "
        "Run 'pip install -e .' before running tests. "
        "SIN_CARRETA compliance: No sys.path manipulation allowed.",
        returncode=1
    )


@pytest.fixture(scope="session", autouse=True)
def _assert_no_manual_src_injection() -> None:
    """Fail early when tests are executed with PYTHONPATH=src."""
    first_entry = Path(sys.path[0]).resolve()
    if first_entry == SRC_DIR:
        pytest.exit(
            "Detected manual sys.path injection of src/. "
            "Use 'pip install -e .' and run tests via 'python -m pytest'.",
            returncode=1,
        )

# Add markers for test obsolescence protocol
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "obsolete: marks tests as obsolete per SIN_CARRETA protocol"
    )
