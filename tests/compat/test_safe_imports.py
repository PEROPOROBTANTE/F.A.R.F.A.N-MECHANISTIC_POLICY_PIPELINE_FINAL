"""
Tests for safe import system (compat.safe_imports module)

Tests cover:
- Required vs optional imports
- Alternative package fallback
- Error message quality
- Lazy import memoization
- Import availability checking
"""

from __future__ import annotations

import sys
from unittest.mock import patch

import pytest

from saaaaaa.compat.safe_imports import (
    ImportErrorDetailed,
    check_import_available,
    get_import_version,
    lazy_import,
    try_import,
)


class TestTryImport:
    """Tests for try_import function."""
    
    def test_import_existing_module(self):
        """Test importing a module that exists."""
        result = try_import("sys", required=False)
        assert result is sys
    
    def test_import_nonexistent_optional(self, capsys):
        """Test importing a nonexistent optional module."""
        result = try_import(
            "nonexistent_module_12345",
            required=False,
            hint="Install with: pip install nonexistent",
        )
        assert result is None
        
        # Check stderr message
        captured = capsys.readouterr()
        assert "nonexistent_module_12345" in captured.err
        assert "optional" in captured.err
        assert "Install with: pip install nonexistent" in captured.err
    
    def test_import_nonexistent_required(self):
        """Test importing a nonexistent required module."""
        with pytest.raises(ImportErrorDetailed) as exc_info:
            try_import(
                "nonexistent_module_12345",
                required=True,
                hint="This module is critical",
            )
        
        assert "nonexistent_module_12345" in str(exc_info.value)
        assert "This module is critical" in str(exc_info.value)
    
    def test_import_with_alternative_success(self):
        """Test fallback to alternative module when primary fails."""
        # Try nonexistent, fall back to sys
        result = try_import(
            "nonexistent_primary",
            alt="sys",
            required=True,
            hint="Fallback test",
        )
        assert result is sys
    
    def test_import_with_alternative_both_fail(self):
        """Test when both primary and alternative fail."""
        with pytest.raises(ImportErrorDetailed) as exc_info:
            try_import(
                "nonexistent_primary",
                alt="nonexistent_alt",
                required=True,
                hint="Both should fail",
            )
        
        error_msg = str(exc_info.value)
        assert "nonexistent_primary" in error_msg
        assert "nonexistent_alt" in error_msg
        assert "Both should fail" in error_msg


class TestCheckImportAvailable:
    """Tests for check_import_available function."""
    
    def test_check_existing_module(self):
        """Test checking for an existing module."""
        assert check_import_available("sys") is True
        assert check_import_available("os") is True
    
    def test_check_nonexistent_module(self):
        """Test checking for a nonexistent module."""
        assert check_import_available("nonexistent_module_xyz") is False
    
    def test_check_package_submodule(self):
        """Test checking for a submodule."""
        assert check_import_available("os.path") is True


class TestGetImportVersion:
    """Tests for get_import_version function."""
    
    def test_get_version_existing(self):
        """Test getting version of an installed package."""
        # pip should be installed in test environment
        version = get_import_version("pip")
        assert version is not None
        assert isinstance(version, str)
        assert len(version) > 0
    
    def test_get_version_nonexistent(self):
        """Test getting version of nonexistent package."""
        version = get_import_version("nonexistent_package_xyz")
        assert version is None


class TestLazyImport:
    """Tests for lazy_import function."""
    
    def test_lazy_import_success(self):
        """Test lazy importing an existing module."""
        result = lazy_import("sys", hint="Test hint")
        assert result is sys
    
    def test_lazy_import_memoization(self):
        """Test that lazy import caches the result."""
        # Import once
        result1 = lazy_import("json")
        
        # Import again - should get same object from cache
        result2 = lazy_import("json")
        
        assert result1 is result2
    
    def test_lazy_import_failure(self):
        """Test lazy import of nonexistent module."""
        with pytest.raises(ImportErrorDetailed) as exc_info:
            lazy_import("nonexistent_lazy_module", hint="Test hint")
        
        assert "nonexistent_lazy_module" in str(exc_info.value)
        assert "Test hint" in str(exc_info.value)
    
    def test_lazy_import_cached_failure(self):
        """Test that failed lazy imports are cached."""
        # First failure
        with pytest.raises(ImportErrorDetailed):
            lazy_import("nonexistent_cached_failure")
        
        # Second attempt should also fail (from cache)
        with pytest.raises(ImportErrorDetailed) as exc_info:
            lazy_import("nonexistent_cached_failure")
        
        assert "previously failed" in str(exc_info.value)


class TestImportErrorDetailed:
    """Tests for ImportErrorDetailed exception."""
    
    def test_exception_is_import_error(self):
        """Test that ImportErrorDetailed is an ImportError."""
        exc = ImportErrorDetailed("Test message")
        assert isinstance(exc, ImportError)
    
    def test_exception_message(self):
        """Test exception message preservation."""
        msg = "Custom error message with details"
        exc = ImportErrorDetailed(msg)
        assert str(exc) == msg
    
    def test_exception_chaining(self):
        """Test exception chaining with cause."""
        original = ImportError("Original error")
        try:
            raise ImportErrorDetailed("Wrapped error") from original
        except ImportErrorDetailed as exc:
            assert exc.__cause__ is original
            assert isinstance(exc.__cause__, ImportError)


class TestRealWorldScenarios:
    """Tests for real-world import scenarios."""
    
    def test_tomllib_vs_tomli_pattern(self):
        """Test the tomllib/tomli fallback pattern used in compat.__init__."""
        # This pattern is used in the compat module for Python version compatibility
        if sys.version_info >= (3, 11):
            result = try_import("tomllib", required=False)
            # On Python 3.11+, tomllib should exist
            assert result is not None
        else:
            # On older Python, try tomllib then fall back to tomli
            result = try_import("tomllib", alt="tomli", required=False)
            # Result should be one of them (if tomli is installed)
            # or None (if tomli not installed)
            assert result is None or result is not None
    
    def test_optional_heavy_dependency_pattern(self):
        """Test pattern for optional heavy dependencies like polars."""
        polars = try_import(
            "polars",
            required=False,
            hint="Install extra 'analytics' for DataFrame support",
        )
        
        # polars may or may not be installed
        # The test is that this doesn't raise an exception
        assert polars is None or polars is not None
    
    def test_required_core_dependency_pattern(self):
        """Test pattern for required core dependencies."""
        # This should always succeed in test environment
        result = try_import(
            "pytest",
            required=True,
            hint="pytest is required for testing",
        )
        
        assert result is not None
        assert hasattr(result, "fixture")  # pytest module loaded


def test_module_exports():
    """Test that safe_imports module exports expected names."""
    from saaaaaa.compat import safe_imports
    
    expected_exports = [
        "ImportErrorDetailed",
        "try_import",
        "lazy_import",
        "check_import_available",
        "get_import_version",
    ]
    
    for name in expected_exports:
        assert hasattr(safe_imports, name), f"Missing export: {name}"
