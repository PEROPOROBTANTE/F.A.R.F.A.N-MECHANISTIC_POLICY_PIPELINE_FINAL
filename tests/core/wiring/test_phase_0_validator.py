
import pytest
from saaaaaa.core.wiring.phase_0_validator import Phase0Validator, Phase0ValidationError

@pytest.fixture
def valid_config(tmp_path):
    """Provides a valid configuration for testing."""
    monolith_path = tmp_path / "monolith.json"
    monolith_path.touch()
    monolith_path.chmod(0o444)  # Read-only

    executor_path = tmp_path / "executor.json"
    executor_path.touch()

    return {
        "monolith_path": str(monolith_path),
        "questionnaire_hash": "some_hash",
        "executor_config_path": str(executor_path),
        "calibration_profile": "default",
        "abort_on_insufficient": True,
        "resource_limits": {"max_memory_mb": 4096},
    }

def test_phase_0_validator_valid_config(valid_config):
    """
    Tests that the Phase0Validator passes with a valid configuration.
    """
    validator = Phase0Validator()
    validator.validate(valid_config)

def test_phase_0_validator_missing_keys(valid_config):
    """
    Tests that the Phase0Validator fails when mandatory keys are missing.
    """
    del valid_config["monolith_path"]
    validator = Phase0Validator()

    with pytest.raises(Phase0ValidationError) as excinfo:
        validator.validate(valid_config)

    assert "Missing mandatory configuration keys" in str(excinfo.value)
    assert "monolith_path" in excinfo.value.missing_keys

def test_phase_0_validator_invalid_paths(valid_config):
    """
    Tests that the Phase0Validator fails when file paths are invalid.
    """
    valid_config["monolith_path"] = "/path/to/nonexistent/file.json"
    validator = Phase0Validator()

    with pytest.raises(Phase0ValidationError) as excinfo:
        validator.validate(valid_config)

    assert "Invalid file paths in configuration" in str(excinfo.value)
    assert "monolith_path" in excinfo.value.invalid_paths

def test_phase_0_validator_invalid_permissions(valid_config, tmp_path):
    """
    Tests that the Phase0Validator fails when the monolith file is not read-only.
    """
    monolith_path = tmp_path / "monolith.json"
    monolith_path.touch()
    monolith_path.chmod(0o666)  # Read-write

    valid_config["monolith_path"] = str(monolith_path)
    validator = Phase0Validator()

    with pytest.raises(Phase0ValidationError) as excinfo:
        validator.validate(valid_config)

    assert "Invalid file permissions in configuration" in str(excinfo.value)
    assert "monolith_path" in excinfo.value.invalid_paths
