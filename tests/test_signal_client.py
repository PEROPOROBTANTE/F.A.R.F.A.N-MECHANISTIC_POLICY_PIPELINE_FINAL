"""Test SignalClient implementation in signals.py."""
import pytest

from saaaaaa.core.orchestrator.signals import (
    SignalClient, 
    SignalPack, 
    InMemorySignalSource,
    SignalUnavailableError
)


def test_signal_client_memory_mode():
    """Test SignalClient in memory:// mode."""
    client = SignalClient(base_url="memory://")
    
    # Create a signal pack
    signal_pack = SignalPack(
        version="1.0.0",
        policy_area="fiscal",
        patterns=["pattern1", "pattern2"],
        indicators=["indicator1"],
        regex=["regex1"],
        verbs=["verb1"],
        entities=["entity1"],
        thresholds={"threshold1": 0.5}
    )
    
    # Register it
    client.register_memory_signal("fiscal", signal_pack)
    
    # Fetch it back
    fetched = client.fetch_signal_pack("fiscal")
    
    assert fetched is not None
    assert fetched.version == "1.0.0"
    assert fetched.policy_area == "fiscal"
    assert "pattern1" in fetched.patterns


def test_signal_client_memory_mode_miss():
    """Test SignalClient returns None for missing signal."""
    client = SignalClient(base_url="memory://")
    
    fetched = client.fetch_signal_pack("nonexistent")
    
    assert fetched is None


def test_signal_client_http_disabled_by_default():
    """Test that HTTP signals are disabled by default."""
    # When HTTP URL is provided but enable_http_signals=False,
    # should fall back to memory mode
    client = SignalClient(base_url="http://example.com", enable_http_signals=False)
    
    metrics = client.get_metrics()
    assert metrics["transport"] == "memory"


def test_signal_client_invalid_url_scheme():
    """Test that invalid URL scheme raises ValueError."""
    with pytest.raises(ValueError, match="Invalid base_url scheme"):
        SignalClient(base_url="ftp://invalid")


def test_in_memory_signal_source():
    """Test InMemorySignalSource directly."""
    source = InMemorySignalSource()
    
    signal_pack = SignalPack(
        version="1.0.0",
        policy_area="salud",
        patterns=["health_pattern"]
    )
    
    source.register("salud", signal_pack)
    
    fetched = source.get("salud")
    assert fetched is not None
    assert fetched.policy_area == "salud"
    
    missing = source.get("nonexistent")
    assert missing is None


def test_signal_pack_compute_hash():
    """Test that SignalPack computes deterministic hash."""
    pack1 = SignalPack(
        version="1.0.0",
        policy_area="fiscal",
        patterns=["p1", "p2"]
    )
    
    pack2 = SignalPack(
        version="1.0.0",
        policy_area="fiscal",
        patterns=["p1", "p2"]
    )
    
    # Same content should produce same hash
    assert pack1.compute_hash() == pack2.compute_hash()


def test_signal_pack_different_content_different_hash():
    """Test that different content produces different hash."""
    pack1 = SignalPack(
        version="1.0.0",
        policy_area="fiscal",
        patterns=["p1"]
    )
    
    pack2 = SignalPack(
        version="1.0.0",
        policy_area="fiscal",
        patterns=["p2"]
    )
    
    assert pack1.compute_hash() != pack2.compute_hash()
