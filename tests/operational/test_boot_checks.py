"""
Tests for boot check functionality.

These tests validate that the boot check script correctly identifies
module loading issues and runtime validator initialization problems.
"""

import unittest
from pathlib import Path

# Add project root to path
from tools.testing.boot_check import (
    check_module_import,
    check_registry_validation,
    check_runtime_validators,
)

class TestBootCheck(unittest.TestCase):
    """Test boot check functionality."""

    def test_check_valid_module(self):
        """Test importing a valid built-in module."""
        success, error = check_module_import("sys", verbose=False)

        self.assertTrue(success)
        self.assertEqual(error, "")

    def test_check_invalid_module(self):
        """Test importing a non-existent module."""
        success, error = check_module_import("nonexistent_module_12345", verbose=False)

        self.assertFalse(success)
        self.assertIn("not found", error.lower())

    def test_check_registry_validation_graceful_failure(self):
        """Test that registry validation doesn't fail hard if not implemented."""
        # This should not raise an exception even if orchestrator doesn't exist
        success, error = check_registry_validation(verbose=False)

        # Either succeeds (registry works) or returns True with no error (not implemented)
        self.assertIsInstance(success, bool)
        self.assertIsInstance(error, str)

    def test_check_runtime_validators_graceful_failure(self):
        """Test that runtime validator check doesn't fail hard if not implemented."""
        # This should not raise an exception even if validation_engine doesn't exist
        success, error = check_runtime_validators(verbose=False)

        # Either succeeds or returns True with no error (not implemented)
        self.assertIsInstance(success, bool)
        self.assertIsInstance(error, str)

if __name__ == "__main__":
    unittest.main()
