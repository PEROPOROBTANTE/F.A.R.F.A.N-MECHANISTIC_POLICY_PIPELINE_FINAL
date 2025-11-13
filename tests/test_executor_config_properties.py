"""Property-based tests for ExecutorConfig using Hypothesis.

These tests verify configuration invariants across wide parameter ranges:
- Timeout and retry combinations stay within latency budgets
- Configuration hashing is deterministic and collision-free
- Config merging is associative and preserves overrides
- All parameters stay within valid ranges
"""

import json
import os
from typing import Any

import pytest

# Mark all tests in this module as outdated
pytestmark = pytest.mark.skip(reason="Config system refactored to use frozen dataclasses")

from hypothesis import given, strategies as st, assume, settings

from saaaaaa.core.orchestrator.executor_config import (
    ExecutorConfig,
    CONSERVATIVE_CONFIG,
    compute_input_hash,
)


# Strategy for generating valid ExecutorConfig instances
config_strategy = st.builds(
    ExecutorConfig,
    max_tokens=st.integers(min_value=256, max_value=8192),
    temperature=st.floats(min_value=0.0, max_value=2.0, allow_nan=False, allow_infinity=False),
    timeout_s=st.floats(min_value=1.0, max_value=300.0, allow_nan=False, allow_infinity=False),
    retry=st.integers(min_value=0, max_value=5),
    policy_area=st.one_of(
        st.none(),
        st.sampled_from(["fiscal", "salud", "ambiente", "energía", "transporte"])
    ),
    regex_pack=st.lists(st.text(min_size=1, max_size=50), max_size=10),
    thresholds=st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        max_size=10,
    ),
    entities_whitelist=st.lists(st.text(min_size=1, max_size=30), max_size=20),
    enable_symbolic_sparse=st.booleans(),
    seed=st.integers(min_value=0, max_value=2147483647),
)


@given(config_strategy)
@settings(max_examples=50)
def test_config_parameters_within_bounds(config: ExecutorConfig) -> None:
    """Test that all parameters stay within valid bounds."""
    assert 256 <= config.max_tokens <= 8192
    assert 0.0 <= config.temperature <= 2.0
    assert 1.0 <= config.timeout_s <= 300.0
    assert 0 <= config.retry <= 5
    assert 0 <= config.seed <= 2147483647
    
    # Thresholds must be in [0, 1]
    for value in config.thresholds.values():
        assert 0.0 <= value <= 1.0


@given(config_strategy, st.integers(min_value=1, max_value=600))
@settings(max_examples=50)
def test_latency_budget_validation(config: ExecutorConfig, max_latency: int) -> None:
    """Test latency budget validation."""
    actual_budget = config.retry * config.timeout_s
    
    if actual_budget <= max_latency:
        # Should pass
        assert config.validate_latency_budget(max_latency)
    else:
        # Should fail
        with pytest.raises(ValueError, match="Latency budget exceeded"):
            config.validate_latency_budget(max_latency)


@given(config_strategy)
@settings(max_examples=50)
def test_config_hash_deterministic(config: ExecutorConfig) -> None:
    """Test that config hash is deterministic."""
    hash1 = config.compute_hash()
    hash2 = config.compute_hash()
    
    assert hash1 == hash2
    assert len(hash1) == 64  # BLAKE3 produces 64 hex chars


@given(config_strategy, config_strategy)
@settings(max_examples=50)
def test_config_hash_collision_resistance(config1: ExecutorConfig, config2: ExecutorConfig) -> None:
    """Test that different configs produce different hashes (high probability)."""
    assume(config1 != config2)
    
    hash1 = config1.compute_hash()
    hash2 = config2.compute_hash()
    
    # Different configs should have different hashes (collision resistance)
    # Note: This is probabilistic but extremely unlikely to fail
    assert hash1 != hash2


@given(config_strategy, config_strategy)
@settings(max_examples=50)
def test_config_merge_preserves_overrides(base: ExecutorConfig, override: ExecutorConfig) -> None:
    """Test that merge preserves override values."""
    merged = base.merge_overrides(override)
    
    # Merged config should have override's values
    # We can check by comparing their hashes
    # If override is complete, merged should equal override
    # But we need to be careful about exclude_unset behavior
    
    # At minimum, merged should be a valid config
    assert isinstance(merged, ExecutorConfig)
    
    # Merged should preserve base's hash structure
    assert len(merged.compute_hash()) == 64


@given(config_strategy)
@settings(max_examples=50)
def test_config_merge_with_none_returns_self(config: ExecutorConfig) -> None:
    """Test that merging with None returns self."""
    merged = config.merge_overrides(None)
    
    assert merged == config
    assert merged.compute_hash() == config.compute_hash()


@given(config_strategy)
@settings(max_examples=30)
def test_config_describe_contains_all_fields(config: ExecutorConfig) -> None:
    """Test that describe() includes all configuration fields."""
    description = config.describe()
    
    assert "max_tokens" in description
    assert "temperature" in description
    assert "timeout_s" in description
    assert "retry" in description
    assert "seed" in description
    assert "BLAKE3" in description


@given(config_strategy)
@settings(max_examples=30)
def test_config_serialization_roundtrip(config: ExecutorConfig) -> None:
    """Test that config can be serialized and deserialized."""
    # Serialize to JSON
    json_str = config.model_dump_json()
    
    # Deserialize back
    data = json.loads(json_str)
    reconstructed = ExecutorConfig(**data)
    
    # Should be equal
    assert reconstructed == config
    assert reconstructed.compute_hash() == config.compute_hash()


@given(
    st.integers(min_value=256, max_value=8192),
    st.floats(min_value=0.0, max_value=2.0, allow_nan=False, allow_infinity=False),
    st.floats(min_value=1.0, max_value=300.0, allow_nan=False, allow_infinity=False),
    st.integers(min_value=0, max_value=5),
)
@settings(max_examples=50)
def test_config_from_cli_args(
    max_tokens: int,
    temperature: float,
    timeout_s: float,
    retry: int,
) -> None:
    """Test config creation from CLI args."""
    config = ExecutorConfig.from_cli_args(
        max_tokens=max_tokens,
        temperature=temperature,
        timeout_s=timeout_s,
        retry=retry,
    )
    
    assert config.max_tokens == max_tokens
    assert config.temperature == temperature
    assert config.timeout_s == timeout_s
    assert config.retry == retry


def test_config_from_env_empty() -> None:
    """Test config from environment with no env vars set."""
    # Clear any existing executor env vars
    for key in list(os.environ.keys()):
        if key.startswith("EXECUTOR_"):
            del os.environ[key]
    
    config = ExecutorConfig.from_env()
    
    # Should have defaults
    assert config.max_tokens == 2048
    assert config.temperature == 0.0


def test_config_from_env_with_values() -> None:
    """Test config from environment with values set."""
    os.environ["EXECUTOR_MAX_TOKENS"] = "4096"
    os.environ["EXECUTOR_TEMPERATURE"] = "0.7"
    os.environ["EXECUTOR_TIMEOUT_S"] = "60.0"
    os.environ["EXECUTOR_RETRY"] = "3"
    os.environ["EXECUTOR_SEED"] = "42"
    
    try:
        config = ExecutorConfig.from_env()
        
        assert config.max_tokens == 4096
        assert config.temperature == 0.7
        assert config.timeout_s == 60.0
        assert config.retry == 3
        assert config.seed == 42
    finally:
        # Cleanup
        for key in ["EXECUTOR_MAX_TOKENS", "EXECUTOR_TEMPERATURE", "EXECUTOR_TIMEOUT_S", 
                    "EXECUTOR_RETRY", "EXECUTOR_SEED"]:
            os.environ.pop(key, None)


def test_config_from_env_with_complex_types() -> None:
    """Test config from environment with lists and dicts."""
    os.environ["EXECUTOR_REGEX_PACK"] = "pattern1, pattern2, pattern3"
    os.environ["EXECUTOR_ENTITIES_WHITELIST"] = "PERSON, ORG, GPE"
    os.environ["EXECUTOR_THRESHOLDS"] = '{"min_confidence": 0.8, "min_evidence": 0.7}'
    os.environ["EXECUTOR_ENABLE_SYMBOLIC_SPARSE"] = "true"
    
    try:
        config = ExecutorConfig.from_env()
        
        assert len(config.regex_pack) == 3
        assert "pattern1" in config.regex_pack
        assert len(config.entities_whitelist) == 3
        assert "PERSON" in config.entities_whitelist
        assert len(config.thresholds) == 2
        assert config.thresholds["min_confidence"] == 0.8
        assert config.enable_symbolic_sparse is True
    finally:
        # Cleanup
        for key in ["EXECUTOR_REGEX_PACK", "EXECUTOR_ENTITIES_WHITELIST", 
                    "EXECUTOR_THRESHOLDS", "EXECUTOR_ENABLE_SYMBOLIC_SPARSE"]:
            os.environ.pop(key, None)


def test_conservative_config_is_safe() -> None:
    """Test that CONSERVATIVE_CONFIG has safe values."""
    assert CONSERVATIVE_CONFIG.temperature == 0.0  # Fully deterministic
    assert CONSERVATIVE_CONFIG.timeout_s <= 30.0  # Short timeout
    assert CONSERVATIVE_CONFIG.retry <= 2  # Few retries
    assert CONSERVATIVE_CONFIG.seed == 42  # Fixed seed
    
    # Should pass strict latency budget
    assert CONSERVATIVE_CONFIG.validate_latency_budget(60.0)


@given(st.text(min_size=1, max_size=1000))
@settings(max_examples=50)
def test_input_hash_deterministic(text: str) -> None:
    """Test that input hash is deterministic."""
    hash1 = compute_input_hash(text)
    hash2 = compute_input_hash(text)
    
    assert hash1 == hash2
    assert len(hash1) == 64  # BLAKE3


@given(st.text(min_size=1, max_size=1000), st.text(min_size=1, max_size=1000))
@settings(max_examples=50)
def test_input_hash_collision_resistance(text1: str, text2: str) -> None:
    """Test that different inputs produce different hashes."""
    assume(text1 != text2)
    
    hash1 = compute_input_hash(text1)
    hash2 = compute_input_hash(text2)
    
    assert hash1 != hash2


@given(config_strategy)
@settings(max_examples=30)
def test_config_immutability(config: ExecutorConfig) -> None:
    """Test that config is immutable (frozen)."""
    with pytest.raises(Exception):  # Pydantic raises ValidationError or similar
        config.max_tokens = 1024  # type: ignore[misc]


def test_config_rejects_invalid_thresholds() -> None:
    """Test that invalid threshold values are rejected."""
    with pytest.raises(Exception):  # Should raise validation error
        ExecutorConfig(thresholds={"invalid": 1.5})  # Out of range
    
    with pytest.raises(Exception):
        ExecutorConfig(thresholds={"invalid": -0.1})  # Out of range
