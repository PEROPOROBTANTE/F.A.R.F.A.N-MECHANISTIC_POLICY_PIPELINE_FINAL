"""Tests for ExecutorConfig CLI integration."""

import pytest


def test_executor_config_has_from_cli():
    """Test that ExecutorConfig has from_cli method."""
    from saaaaaa.core.orchestrator.executor_config import ExecutorConfig
    
    assert hasattr(ExecutorConfig, "from_cli")
    assert callable(ExecutorConfig.from_cli)


def test_executor_config_from_cli_without_app():
    """Test from_cli returns default config when no app provided."""
    from saaaaaa.core.orchestrator.executor_config import ExecutorConfig
    
    config = ExecutorConfig.from_cli(app=None)
    
    assert isinstance(config, ExecutorConfig)
    assert config.max_tokens == 2048  # Default value
    assert config.temperature == 0.0  # Default value


def test_executor_config_from_cli_args():
    """Test from_cli_args with parameters."""
    from saaaaaa.core.orchestrator.executor_config import ExecutorConfig
    
    config = ExecutorConfig.from_cli_args(
        max_tokens=4096,
        temperature=0.7,
        seed=42
    )
    
    assert config.max_tokens == 4096
    assert config.temperature == 0.7
    assert config.seed == 42


def test_executor_config_describe():
    """Test that config can describe itself."""
    from saaaaaa.core.orchestrator.executor_config import ExecutorConfig
    
    config = ExecutorConfig(max_tokens=1024, temperature=0.5)
    description = config.describe()
    
    assert isinstance(description, str)
    assert "1024" in description
    assert "0.5" in description
    assert "ExecutorConfig" in description


def test_executor_config_from_env():
    """Test that from_env method exists and works."""
    from saaaaaa.core.orchestrator.executor_config import ExecutorConfig
    
    # Should return default config when no env vars set
    config = ExecutorConfig.from_env()
    
    assert isinstance(config, ExecutorConfig)
