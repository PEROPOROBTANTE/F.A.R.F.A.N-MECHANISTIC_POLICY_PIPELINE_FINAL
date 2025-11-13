"""Tests for safe imports module."""

import pytest

from saaaaaa.compat import try_import, OptionalDependencyError


def test_try_import_missing_optional():
    """Test that optional dependency returns None when missing."""
    # Import a package that definitely doesn't exist
    result = try_import("nonexistent_package_12345", required=False)
    assert result is None


def test_try_import_missing_required():
    """Test that required dependency raises error when missing."""
    with pytest.raises(OptionalDependencyError) as exc_info:
        try_import("nonexistent_package_12345", required=True, hint="Testing")
    
    assert "nonexistent_package_12345" in str(exc_info.value)
    assert "Testing" in str(exc_info.value)


def test_try_import_available():
    """Test that available package is imported successfully."""
    # Import a standard library module
    sys = try_import("sys", required=False)
    assert sys is not None
    assert hasattr(sys, "version")


def test_optional_dependency_error_message():
    """Test that error message is prescriptive."""
    error = OptionalDependencyError(
        "test_package",
        hint="Used for testing",
        install_cmd="pip install test_package==1.0.0"
    )
    
    message = str(error)
    assert "test_package" in message
    assert "Used for testing" in message
    assert "pip install test_package==1.0.0" in message


def test_pyarrow_optional():
    """Test that pyarrow is handled as optional."""
    # This should not raise even if pyarrow is not installed
    pyarrow = try_import("pyarrow", required=False, hint="Arrow serialization")
    # Result can be None or module, both are valid
    assert pyarrow is None or hasattr(pyarrow, "__version__")


def test_torch_optional():
    """Test that torch is handled as optional."""
    # This should not raise even if torch is not installed
    torch = try_import("torch", required=False, hint="ML backends")
    # Result can be None or module, both are valid
    assert torch is None or hasattr(torch, "__version__")
