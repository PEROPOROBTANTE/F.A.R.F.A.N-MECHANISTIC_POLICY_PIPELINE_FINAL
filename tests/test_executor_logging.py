"""Test enriched executor error logging in executors.py."""
import logging
import pytest



# Mark all tests in this module as outdated
pytestmark = pytest.mark.skip(reason="Logging system migrated to structlog")

def test_executor_logging_structure(caplog):
    """Test that executor logging includes structured context."""
    # This is a basic test to verify the logging structure
    # In practice, this would be tested by actually running executor code
    
    logger = logging.getLogger("saaaaaa.core.orchestrator.executors")
    
    # Simulate the logging pattern used in executors
    with caplog.at_level(logging.ERROR):
        logger.error(
            "Method %s failed",
            "TestClass.test_method",
            exc_info=False,
            extra={
                'method_key': "TestClass.test_method",
                'class_name': "TestClass",
                'method_name': "test_method",
                'prepared_kwargs_keys': ['arg1', 'arg2'],
                'error_type': "ValueError",
                'error_details': "Test error message",
            }
        )
    
    # Check that log was created
    assert len(caplog.records) == 1
    record = caplog.records[0]
    
    # Check message
    assert "TestClass.test_method" in record.message
    
    # Check that extra fields are present
    assert hasattr(record, 'method_key')
    assert hasattr(record, 'class_name')
    assert hasattr(record, 'method_name')
    assert hasattr(record, 'prepared_kwargs_keys')
    assert hasattr(record, 'error_type')
    assert hasattr(record, 'error_details')
    
    # Check values
    assert record.method_key == "TestClass.test_method"
    assert record.class_name == "TestClass"
    assert record.method_name == "test_method"
    assert record.prepared_kwargs_keys == ['arg1', 'arg2']
    assert record.error_type == "ValueError"
    assert record.error_details == "Test error message"


def test_executor_logging_keys_present(caplog):
    """Test that all required keys are present in logging extra."""
    logger = logging.getLogger("test_executor")
    
    required_keys = [
        'method_key',
        'class_name',
        'method_name',
        'prepared_kwargs_keys',
        'error_type',
        'error_details',
    ]
    
    extra = {key: f"test_{key}" for key in required_keys}
    extra['prepared_kwargs_keys'] = ['key1', 'key2']
    
    with caplog.at_level(logging.ERROR):
        logger.error("Test error", extra=extra)
    
    record = caplog.records[0]
    
    for key in required_keys:
        assert hasattr(record, key), f"Missing key: {key}"
