"""Test for _expected_type_name method in arg_router.py."""
import pytest


# Mark all tests in this module as outdated
pytestmark = pytest.mark.skip(reason="Merged into test_arg_router_extended.py")

from saaaaaa.core.orchestrator.arg_router import PayloadDriftMonitor


def test_expected_type_name_with_tuple():
    """Test _expected_type_name with tuple of types."""
    expected = (str, int, float)
    result = PayloadDriftMonitor._expected_type_name(expected)
    assert "str" in result
    assert "int" in result
    assert "float" in result
    assert "," in result


def test_expected_type_name_with_single_type():
    """Test _expected_type_name with single type."""
    expected = str
    result = PayloadDriftMonitor._expected_type_name(expected)
    assert result == "str"


def test_expected_type_name_with_custom_class():
    """Test _expected_type_name with custom class."""
    class CustomClass:
        pass
    
    expected = CustomClass
    result = PayloadDriftMonitor._expected_type_name(expected)
    assert result == "CustomClass"


def test_expected_type_name_fallback():
    """Test _expected_type_name fallback for objects without __name__."""
    expected = 42  # An int instance, not a type
    result = PayloadDriftMonitor._expected_type_name(expected)
    assert result == "42"
