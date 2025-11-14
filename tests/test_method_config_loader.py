"""
Tests for MethodConfigLoader.

Verifies security fixes and proper parsing of the canonical spec.
"""
import json
import pytest
from pathlib import Path
from src.saaaaaa.utils.method_config_loader import MethodConfigLoader


@pytest.fixture
def minimal_spec(tmp_path):
    """Create a minimal valid spec for testing."""
    spec = {
        "specification_metadata": {
            "version": "1.0.0",
            "generated": "2025-11-13T00:00:00Z"
        },
        "methods": [
            {
                "name": "TEST.Method.test_func",
                "canonical_id": "TEST.M.test_v1",
                "description": "Test method",
                "parameters": [
                    {
                        "name": "threshold",
                        "type": "numeric",
                        "allowed_values": {
                            "kind": "range",
                            "spec": "[0.0, 1.0], inclusive"
                        },
                        "default": 0.5
                    },
                    {
                        "name": "max_features",
                        "type": "numeric",
                        "allowed_values": {
                            "kind": "range",
                            "spec": "[100, 10000], integer"
                        },
                        "default": 1000
                    },
                    {
                        "name": "mode",
                        "type": "string",
                        "allowed_values": {
                            "kind": "set",
                            "spec": ["fast", "accurate", "balanced"]
                        },
                        "default": "balanced"
                    },
                    {
                        "name": "options",
                        "type": "string",
                        "allowed_values": {
                            "kind": "set",
                            "spec": "['opt1', 'opt2', 'opt3']"
                        },
                        "default": "opt1"
                    }
                ]
            }
        ]
    }
    spec_path = tmp_path / "test_spec.json"
    with open(spec_path, "w") as f:
        json.dump(spec, f)
    return spec_path


class TestMethodConfigLoaderSecurity:
    """Test security fixes."""
    
    def test_no_eval_injection(self, minimal_spec):
        """Verify eval() is not used - malicious code should not execute."""
        loader = MethodConfigLoader(minimal_spec)
        
        # This should safely fail, not execute arbitrary code
        spec = loader.get_parameter_spec("TEST.M.test_v1", "options")
        
        # Try to validate with a malicious string that would work with eval()
        # but fail with ast.literal_eval()
        with pytest.raises(ValueError):
            # This would execute with eval(), but ast.literal_eval will reject it
            loader._parse_set("__import__('os').system('echo pwned')")
    
    def test_ast_literal_eval_used(self, minimal_spec):
        """Verify ast.literal_eval is used for safe parsing."""
        loader = MethodConfigLoader(minimal_spec)
        
        # Valid Python literal - should work
        result = loader._parse_set("['a', 'b', 'c']")
        assert result == {'a', 'b', 'c'}
        
        # Invalid Python literal - should fail safely
        with pytest.raises(ValueError):
            loader._parse_set("malformed [}")


class TestMethodConfigLoaderSchemaValidation:
    """Test schema validation."""
    
    def test_missing_required_keys(self, tmp_path):
        """Verify schema validation catches missing keys."""
        spec = {"methods": []}  # Missing specification_metadata
        spec_path = tmp_path / "invalid_spec.json"
        with open(spec_path, "w") as f:
            json.dump(spec, f)
        
        with pytest.raises(ValueError, match="Spec missing required keys"):
            MethodConfigLoader(spec_path)
    
    def test_valid_schema_loads(self, minimal_spec):
        """Verify valid schema loads successfully."""
        loader = MethodConfigLoader(minimal_spec)
        assert loader.spec is not None
        assert "methods" in loader.spec


class TestMethodConfigLoaderRangeParsing:
    """Test improved range parsing."""
    
    def test_parse_range_inclusive(self, minimal_spec):
        """Test parsing range with inclusive modifier."""
        loader = MethodConfigLoader(minimal_spec)
        min_val, max_val = loader._parse_range("[0.0, 1.0], inclusive")
        assert min_val == 0.0
        assert max_val == 1.0
    
    def test_parse_range_integer(self, minimal_spec):
        """Test parsing range with integer modifier."""
        loader = MethodConfigLoader(minimal_spec)
        min_val, max_val = loader._parse_range("[100, 10000], integer")
        assert min_val == 100.0
        assert max_val == 10000.0
    
    def test_parse_range_exclusive(self, minimal_spec):
        """Test parsing range with exclusive modifier."""
        loader = MethodConfigLoader(minimal_spec)
        min_val, max_val = loader._parse_range("[0.0, 1.0], exclusive")
        assert min_val == 0.0
        assert max_val == 1.0
    
    def test_parse_range_multiple_modifiers(self, minimal_spec):
        """Test parsing range with multiple modifiers."""
        loader = MethodConfigLoader(minimal_spec)
        min_val, max_val = loader._parse_range("[0.0, 1.0], inclusive, integer")
        assert min_val == 0.0
        assert max_val == 1.0
    
    def test_parse_range_invalid(self, minimal_spec):
        """Test that invalid range spec raises ValueError."""
        loader = MethodConfigLoader(minimal_spec)
        with pytest.raises(ValueError, match="Invalid range spec"):
            loader._parse_range("invalid")


class TestMethodConfigLoaderSetParsing:
    """Test improved set parsing."""
    
    def test_parse_set_from_list(self, minimal_spec):
        """Test parsing set from list."""
        loader = MethodConfigLoader(minimal_spec)
        result = loader._parse_set(["a", "b", "c"])
        assert result == {"a", "b", "c"}
    
    def test_parse_set_from_string(self, minimal_spec):
        """Test parsing set from string representation."""
        loader = MethodConfigLoader(minimal_spec)
        result = loader._parse_set("['a', 'b', 'c']")
        assert result == {"a", "b", "c"}
    
    def test_parse_set_invalid(self, minimal_spec):
        """Test that invalid set spec raises ValueError."""
        loader = MethodConfigLoader(minimal_spec)
        with pytest.raises(ValueError, match="Invalid set spec"):
            loader._parse_set("not a valid literal")


class TestMethodConfigLoaderFunctionality:
    """Test overall functionality."""
    
    def test_get_method_parameter(self, minimal_spec):
        """Test getting method parameter."""
        loader = MethodConfigLoader(minimal_spec)
        threshold = loader.get_method_parameter("TEST.M.test_v1", "threshold")
        assert threshold == 0.5
    
    def test_get_method_parameter_with_override(self, minimal_spec):
        """Test getting method parameter with override."""
        loader = MethodConfigLoader(minimal_spec)
        threshold = loader.get_method_parameter("TEST.M.test_v1", "threshold", override=0.7)
        assert threshold == 0.7
    
    def test_validate_parameter_range(self, minimal_spec):
        """Test parameter validation for range."""
        loader = MethodConfigLoader(minimal_spec)
        assert loader.validate_parameter_value("TEST.M.test_v1", "threshold", 0.5)
        
        with pytest.raises(ValueError, match="out of range"):
            loader.validate_parameter_value("TEST.M.test_v1", "threshold", 1.5)
    
    def test_validate_parameter_set(self, minimal_spec):
        """Test parameter validation for set."""
        loader = MethodConfigLoader(minimal_spec)
        assert loader.validate_parameter_value("TEST.M.test_v1", "mode", "fast")
        
        with pytest.raises(ValueError, match="not in allowed set"):
            loader.validate_parameter_value("TEST.M.test_v1", "mode", "invalid")
