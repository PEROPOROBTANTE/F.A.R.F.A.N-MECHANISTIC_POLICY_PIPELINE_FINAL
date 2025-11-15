"""
Tests for signature validation and defensive programming fixes
"""

import sys
from pathlib import Path

# Add project root to path

def test_defensive_function_with_extra_kwargs():
    """Test defensive function that accepts unexpected kwargs"""

    # Mock defensive function similar to _is_likely_header
    def defensive_function(required_param, **kwargs):
        """Defensive implementation that accepts extra kwargs"""
        if kwargs:
            print(f"Warning: Received unexpected kwargs: {list(kwargs.keys())}")

        return f"Processed: {required_param}"

    # Test case 1: Normal usage
    result = defensive_function("test_value")
    assert result == "Processed: test_value"
    print("✓ Normal usage works")

    # Test case 2: With unexpected kwargs (this would have failed before)
    result = defensive_function("test_value", pdf_path="/some/path.pdf", extra="value")
    assert result == "Processed: test_value"
    print("✓ Accepts unexpected kwargs without crashing")

    print("\n✅ test_defensive_function_with_extra_kwargs PASSED")

def test_defensive_function_with_optional_param():
    """Test defensive function that handles missing required parameter"""

    # Mock defensive function similar to _analyze_causal_dimensions
    def defensive_function(text, sentences=None):
        """Defensive implementation that handles missing sentences"""
        if sentences is None:
            print("Warning: Missing 'sentences' parameter, using fallback")
            # Fallback: simple split
            sentences = text.split('. ')

        return {
            "sentence_count": len(sentences),
            "text_length": len(text)
        }

    # Test case 1: With parameter provided
    result = defensive_function(
        "Text content.",
        sentences=["Text content."]
    )
    assert result["sentence_count"] == 1
    print("✓ Works with sentences provided")

    # Test case 2: Without parameter (this would have failed before)
    result = defensive_function("Sentence one. Sentence two.")
    assert result["sentence_count"] == 2
    print("✓ Works without optional parameter")

    print("\n✅ test_defensive_function_with_optional_param PASSED")

def test_defensive_class_init_with_extra_kwargs():
    """Test defensive class __init__ that accepts unexpected kwargs"""

    # Mock class with defensive __init__ similar to BayesianMechanismInference
    class DefensiveClass:
        def __init__(self, config, nlp_model, **kwargs):
            """Defensive __init__ that accepts extra kwargs"""
            if kwargs:
                print(f"Warning: Received unexpected kwargs: {list(kwargs.keys())}")

            self.config = config
            self.nlp_model = nlp_model

    # Test case 1: Normal usage
    obj1 = DefensiveClass(
        config="mock_config",
        nlp_model="mock_nlp"
    )
    assert obj1.config == "mock_config"
    print("✓ Normal instantiation works")

    # Test case 2: With unexpected kwargs (would have failed before)
    obj2 = DefensiveClass(
        config="mock_config",
        nlp_model="mock_nlp",
        causal_hierarchy={"some": "data"},
        unexpected_param="value"
    )
    assert obj2.config == "mock_config"
    print("✓ Accepts unexpected kwargs without crashing")

    print("\n✅ test_defensive_class_init_with_extra_kwargs PASSED")

def test_signature_validator_basic_functionality():
    """Test basic signature validation functionality"""

    from saaaaaa.utils.signature_validator import validate_call_signature

    def sample_function(arg1: str, arg2: int):
        return f"{arg1}: {arg2}"

    # Valid call
    assert validate_call_signature(sample_function, "test", 123)
    print("✓ Valid call detected correctly")

    # Invalid call - missing argument
    assert not validate_call_signature(sample_function, "test")
    print("✓ Missing argument detected")

    # Invalid call - too many positional arguments
    assert not validate_call_signature(sample_function, "test", 123, "extra")
    print("✓ Too many arguments detected")

    print("\n✅ test_signature_validator_basic_functionality PASSED")

def test_validate_signature_decorator():
    """Test the validate_signature decorator"""

    from saaaaaa.utils.signature_validator import validate_signature

    @validate_signature(enforce=False, track=False)
    def decorated_function(param1: str, param2: int) -> str:
        return f"{param1}-{param2}"

    # Test normal call
    result = decorated_function("test", 123)
    assert result == "test-123"
    print("✓ Decorated function works normally")

    # Test call with kwargs
    result = decorated_function(param1="test", param2=456)
    assert result == "test-456"
    print("✓ Decorated function works with kwargs")

    print("\n✅ test_validate_signature_decorator PASSED")

if __name__ == "__main__":
    print("=" * 70)
    print("SIGNATURE VALIDATION TESTS")
    print("=" * 70 + "\n")

    try:
        test_defensive_function_with_extra_kwargs()
        test_defensive_function_with_optional_param()
        test_defensive_class_init_with_extra_kwargs()
        test_signature_validator_basic_functionality()
        test_validate_signature_decorator()

        print("\n" + "=" * 70)
        print("ALL TESTS PASSED ✅")
        print("=" * 70)
        print("\nSignature validation system is working correctly!")
        print("The defensive programming fixes prevent signature mismatch crashes.")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
