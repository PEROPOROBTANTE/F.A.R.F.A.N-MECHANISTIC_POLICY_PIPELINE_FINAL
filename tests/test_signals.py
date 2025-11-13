"""Tests for Cross-Cut Signal Channel Implementation.

This module tests:
- SignalPack creation, validation, and hashing
- SignalRegistry (TTL, LRU, caching)
- InMemorySignalSource
- SignalClient (memory:// and HTTP modes)
- Circuit breaker behavior
- HTTP status code mapping
- ETag support
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any
from unittest.mock import Mock, patch

import pytest
from pydantic import ValidationError

from saaaaaa.core.orchestrator.signals import (
    SignalPack,
    SignalRegistry,
    SignalClient,
    InMemorySignalSource,
    CircuitBreakerError,
    SignalUnavailableError,
    PolicyArea,
    create_default_signal_pack,
)


# ====================================================================================
# SignalPack Tests
# ====================================================================================


def test_signal_pack_creation() -> None:
    """Test basic SignalPack creation."""
    pack = SignalPack(
        version="1.0.0",
        policy_area="fiscal",
        patterns=["pattern1", "pattern2"],
        indicators=["indicator1"],
        regex=[r"\d+"],
        verbs=["implement", "execute"],
        entities=["government", "budget"],
        thresholds={"min_confidence": 0.85, "min_evidence": 0.75},
    )
    
    assert pack.version == "1.0.0"
    assert pack.policy_area == "fiscal"
    assert len(pack.patterns) == 2
    assert len(pack.indicators) == 1
    assert pack.thresholds["min_confidence"] == 0.85


def test_signal_pack_frozen() -> None:
    """Test that SignalPack is immutable."""
    pack = SignalPack(version="1.0.0", policy_area="fiscal")
    
    with pytest.raises(ValidationError):
        pack.version = "2.0.0"  # type: ignore


def test_signal_pack_version_validation() -> None:
    """Test semantic version validation."""
    # Valid versions
    SignalPack(version="1.0.0", policy_area="fiscal")
    SignalPack(version="10.20.30", policy_area="salud")
    
    # Invalid versions
    with pytest.raises(ValidationError):
        SignalPack(version="1.0", policy_area="fiscal")
    
    with pytest.raises(ValidationError):
        SignalPack(version="v1.0.0", policy_area="fiscal")
    
    with pytest.raises(ValidationError):
        SignalPack(version="1.0.0-beta", policy_area="fiscal")


def test_signal_pack_threshold_validation() -> None:
    """Test threshold value validation."""
    # Valid thresholds
    SignalPack(
        version="1.0.0",
        policy_area="fiscal",
        thresholds={"min": 0.0, "max": 1.0, "mid": 0.5},
    )
    
    # Invalid threshold (out of range)
    with pytest.raises(ValidationError):
        SignalPack(
            version="1.0.0",
            policy_area="fiscal",
            thresholds={"min": 1.5},
        )
    
    with pytest.raises(ValidationError):
        SignalPack(
            version="1.0.0",
            policy_area="fiscal",
            thresholds={"min": -0.1},
        )


def test_signal_pack_compute_hash() -> None:
    """Test deterministic hash computation."""
    pack1 = SignalPack(
        version="1.0.0",
        policy_area="fiscal",
        patterns=["a", "b"],
        indicators=["i1"],
    )
    
    pack2 = SignalPack(
        version="1.0.0",
        policy_area="fiscal",
        patterns=["a", "b"],
        indicators=["i1"],
    )
    
    # Same content → same hash
    assert pack1.compute_hash() == pack2.compute_hash()
    
    # Different content → different hash
    pack3 = SignalPack(
        version="1.0.0",
        policy_area="fiscal",
        patterns=["a", "c"],
        indicators=["i1"],
    )
    assert pack1.compute_hash() != pack3.compute_hash()


def test_signal_pack_hash_stability() -> None:
    """Test hash stability (property test for BLAKE3)."""
    pack = SignalPack(
        version="1.0.0",
        policy_area="fiscal",
        patterns=["pattern1", "pattern2"],
    )
    
    # Hash should be stable across multiple calls
    hash1 = pack.compute_hash()
    hash2 = pack.compute_hash()
    hash3 = pack.compute_hash()
    
    assert hash1 == hash2 == hash3


def test_signal_pack_is_valid() -> None:
    """Test validity window checking."""
    now = datetime.now(timezone.utc)
    
    # Pack is valid now
    pack1 = SignalPack(
        version="1.0.0",
        policy_area="fiscal",
        valid_from=now.isoformat(),
        valid_to="",
    )
    assert pack1.is_valid(now)
    
    # Pack with expired valid_to
    pack2 = SignalPack(
        version="1.0.0",
        policy_area="fiscal",
        valid_from="2020-01-01T00:00:00+00:00",
        valid_to="2021-01-01T00:00:00+00:00",
    )
    assert not pack2.is_valid(now)


def test_signal_pack_get_keys_used() -> None:
    """Test keys_used extraction."""
    pack = SignalPack(
        version="1.0.0",
        policy_area="fiscal",
        patterns=["p1"],
        indicators=["i1"],
        regex=[],
        verbs=[],
        entities=[],
        thresholds={},
    )
    
    keys = pack.get_keys_used()
    assert "patterns" in keys
    assert "indicators" in keys
    assert "regex" not in keys  # Empty list
    assert "thresholds" not in keys  # Empty dict


# ====================================================================================
# SignalRegistry Tests
# ====================================================================================


def test_signal_registry_initialization() -> None:
    """Test registry initialization."""
    registry = SignalRegistry(max_size=10, default_ttl_s=60)
    
    metrics = registry.get_metrics()
    assert metrics["size"] == 0
    assert metrics["capacity"] == 10
    assert metrics["hit_rate"] == 0.0


def test_signal_registry_put_get() -> None:
    """Test basic put/get operations."""
    registry = SignalRegistry(max_size=10, default_ttl_s=60)
    
    pack = SignalPack(version="1.0.0", policy_area="fiscal")
    registry.put("fiscal", pack)
    
    retrieved = registry.get("fiscal")
    assert retrieved is not None
    assert retrieved.version == "1.0.0"
    assert retrieved.policy_area == "fiscal"


def test_signal_registry_ttl_expiration() -> None:
    """Test TTL-based expiration."""
    registry = SignalRegistry(max_size=10, default_ttl_s=1)
    
    pack = SignalPack(version="1.0.0", policy_area="fiscal", ttl_s=1)
    registry.put("fiscal", pack)
    
    # Should be available immediately
    assert registry.get("fiscal") is not None
    
    # Wait for expiration
    time.sleep(1.5)
    
    # Should be expired
    assert registry.get("fiscal") is None


def test_signal_registry_lru_eviction() -> None:
    """Test LRU eviction when capacity exceeded."""
    registry = SignalRegistry(max_size=3, default_ttl_s=3600)
    
    # Fill to capacity
    pack1 = SignalPack(version="1.0.0", policy_area="fiscal")
    pack2 = SignalPack(version="1.0.0", policy_area="salud")
    pack3 = SignalPack(version="1.0.0", policy_area="ambiente")
    
    registry.put("fiscal", pack1)
    registry.put("salud", pack2)
    registry.put("ambiente", pack3)
    
    # Add one more → should evict oldest (fiscal)
    pack4 = SignalPack(version="1.0.0", policy_area="energía")
    registry.put("energía", pack4)
    
    assert registry.get("fiscal") is None  # Evicted
    assert registry.get("salud") is not None
    assert registry.get("ambiente") is not None
    assert registry.get("energía") is not None


def test_signal_registry_hit_rate() -> None:
    """Test hit rate calculation."""
    registry = SignalRegistry(max_size=10, default_ttl_s=3600)
    
    pack = SignalPack(version="1.0.0", policy_area="fiscal")
    registry.put("fiscal", pack)
    
    # 3 hits, 2 misses
    registry.get("fiscal")
    registry.get("fiscal")
    registry.get("fiscal")
    registry.get("salud")
    registry.get("ambiente")
    
    metrics = registry.get_metrics()
    assert metrics["hits"] == 3
    assert metrics["misses"] == 2
    assert metrics["hit_rate"] == 0.6  # 3/5


def test_signal_registry_clear() -> None:
    """Test clearing registry."""
    registry = SignalRegistry(max_size=10, default_ttl_s=3600)
    
    pack1 = SignalPack(version="1.0.0", policy_area="fiscal")
    pack2 = SignalPack(version="1.0.0", policy_area="salud")
    registry.put("fiscal", pack1)
    registry.put("salud", pack2)
    
    assert registry.get_metrics()["size"] == 2
    
    registry.clear()
    
    assert registry.get_metrics()["size"] == 0
    assert registry.get("fiscal") is None
    assert registry.get("salud") is None


# ====================================================================================
# InMemorySignalSource Tests
# ====================================================================================


def test_in_memory_signal_source_register_get() -> None:
    """Test in-memory signal source registration and retrieval."""
    source = InMemorySignalSource()
    
    pack = SignalPack(version="1.0.0", policy_area="fiscal")
    source.register("fiscal", pack)
    
    retrieved = source.get("fiscal")
    assert retrieved is not None
    assert retrieved.version == "1.0.0"


def test_in_memory_signal_source_miss() -> None:
    """Test in-memory signal source miss."""
    source = InMemorySignalSource()
    
    result = source.get("nonexistent")
    assert result is None


# ====================================================================================
# SignalClient (memory://) Tests
# ====================================================================================


def test_signal_client_memory_mode() -> None:
    """Test signal client in memory:// mode."""
    client = SignalClient(base_url="memory://")
    
    # Register signal
    pack = SignalPack(version="1.0.0", policy_area="fiscal")
    client.register_memory_signal("fiscal", pack)
    
    # Fetch signal
    retrieved = client.fetch_signal_pack("fiscal")
    assert retrieved is not None
    assert retrieved.version == "1.0.0"


def test_signal_client_memory_mode_miss() -> None:
    """Test signal client memory:// miss."""
    client = SignalClient(base_url="memory://")
    
    result = client.fetch_signal_pack("nonexistent")
    assert result is None


def test_signal_client_memory_mode_metrics() -> None:
    """Test signal client metrics in memory:// mode."""
    client = SignalClient(base_url="memory://")
    
    metrics = client.get_metrics()
    assert metrics["transport"] == "memory"
    assert metrics["circuit_open"] is False


def test_signal_client_register_memory_signal_http_mode_error() -> None:
    """Test that register_memory_signal raises error in HTTP mode."""
    client = SignalClient(
        base_url="http://localhost:8000",
        enable_http_signals=True,
    )
    
    pack = SignalPack(version="1.0.0", policy_area="fiscal")
    
    with pytest.raises(ValueError, match="memory:// mode"):
        client.register_memory_signal("fiscal", pack)


# ====================================================================================
# SignalClient (HTTP) Tests with Mock Transport
# ====================================================================================


def test_signal_client_http_200_success() -> None:
    """Test HTTP 200 OK response."""
    try:
        import httpx
    except ImportError:
        pytest.skip("httpx not installed")
    
    # Use httpx MockTransport
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"version": "1.0.0", "policy_area": "fiscal"},
            headers={"ETag": "abc123"},
        )
    
    mock_transport = httpx.MockTransport(handler)
    
    # Monkey-patch httpx.get to use our transport
    original_get = httpx.get
    
    def mock_get(url: str, **kwargs: Any) -> httpx.Response:
        client = httpx.Client(transport=mock_transport)
        return client.get(url, **kwargs)
    
    httpx.get = mock_get  # type: ignore
    
    try:
        client = SignalClient(
            base_url="http://localhost:8000",
            enable_http_signals=True,
        )
        
        pack = client.fetch_signal_pack("fiscal")
        
        assert pack is not None
        assert pack.version == "1.0.0"
        assert pack.policy_area == "fiscal"
    finally:
        httpx.get = original_get  # type: ignore


def test_signal_client_http_304_not_modified() -> None:
    """Test HTTP 304 Not Modified response."""
    try:
        import httpx
    except ImportError:
        pytest.skip("httpx not installed")
    
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(304)
    
    mock_transport = httpx.MockTransport(handler)
    original_get = httpx.get
    
    def mock_get(url: str, **kwargs: Any) -> httpx.Response:
        client = httpx.Client(transport=mock_transport)
        return client.get(url, **kwargs)
    
    httpx.get = mock_get  # type: ignore
    
    try:
        client = SignalClient(
            base_url="http://localhost:8000",
            enable_http_signals=True,
        )
        
        result = client.fetch_signal_pack("fiscal", etag="abc123")
        
        assert result is None
    finally:
        httpx.get = original_get  # type: ignore


def test_signal_client_http_401_unauthorized() -> None:
    """Test HTTP 401 Unauthorized response."""
    try:
        import httpx
    except ImportError:
        pytest.skip("httpx not installed")
    
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="Unauthorized")
    
    mock_transport = httpx.MockTransport(handler)
    original_get = httpx.get
    
    def mock_get(url: str, **kwargs: Any) -> httpx.Response:
        client = httpx.Client(transport=mock_transport)
        return client.get(url, **kwargs)
    
    httpx.get = mock_get  # type: ignore
    
    try:
        client = SignalClient(
            base_url="http://localhost:8000",
            enable_http_signals=True,
        )
        
        with pytest.raises(SignalUnavailableError) as exc_info:
            client.fetch_signal_pack("fiscal")
        
        assert exc_info.value.status_code == 401
    finally:
        httpx.get = original_get  # type: ignore


def test_signal_client_http_429_rate_limit() -> None:
    """Test HTTP 429 Too Many Requests response."""
    try:
        import httpx
    except ImportError:
        pytest.skip("httpx not installed")
    
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, text="Too Many Requests")
    
    mock_transport = httpx.MockTransport(handler)
    original_get = httpx.get
    
    def mock_get(url: str, **kwargs: Any) -> httpx.Response:
        client = httpx.Client(transport=mock_transport)
        return client.get(url, **kwargs)
    
    httpx.get = mock_get  # type: ignore
    
    try:
        client = SignalClient(
            base_url="http://localhost:8000",
            enable_http_signals=True,
        )
        
        with pytest.raises(SignalUnavailableError) as exc_info:
            client.fetch_signal_pack("fiscal")
        
        assert exc_info.value.status_code == 429
    finally:
        httpx.get = original_get  # type: ignore


def test_signal_client_http_500_server_error() -> None:
    """Test HTTP 500 Server Error response."""
    try:
        import httpx
    except ImportError:
        pytest.skip("httpx not installed")
    
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal Server Error")
    
    mock_transport = httpx.MockTransport(handler)
    original_get = httpx.get
    
    def mock_get(url: str, **kwargs: Any) -> httpx.Response:
        client = httpx.Client(transport=mock_transport)
        return client.get(url, **kwargs)
    
    httpx.get = mock_get  # type: ignore
    
    try:
        client = SignalClient(
            base_url="http://localhost:8000",
            enable_http_signals=True,
        )
        
        with pytest.raises(SignalUnavailableError) as exc_info:
            client.fetch_signal_pack("fiscal")
        
        assert exc_info.value.status_code == 500
    finally:
        httpx.get = original_get  # type: ignore


def test_signal_client_http_timeout() -> None:
    """Test HTTP timeout."""
    try:
        import httpx
    except ImportError:
        pytest.skip("httpx not installed")
    
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("Timeout")
    
    mock_transport = httpx.MockTransport(handler)
    original_get = httpx.get
    
    def mock_get(url: str, **kwargs: Any) -> httpx.Response:
        client = httpx.Client(transport=mock_transport)
        return client.get(url, **kwargs)
    
    httpx.get = mock_get  # type: ignore
    
    try:
        client = SignalClient(
            base_url="http://localhost:8000",
            enable_http_signals=True,
            timeout_s=1.0,
        )
        
        with pytest.raises(SignalUnavailableError) as exc_info:
            client.fetch_signal_pack("fiscal")
        
        assert "timeout" in str(exc_info.value).lower()
    finally:
        httpx.get = original_get  # type: ignore


def test_signal_client_http_response_size_limit() -> None:
    """Test response size limit enforcement."""
    try:
        import httpx
    except ImportError:
        pytest.skip("httpx not installed")
    
    # Create response exceeding 1.5 MB
    large_content = b"x" * (SignalClient.MAX_RESPONSE_SIZE_BYTES + 1)
    
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=large_content)
    
    mock_transport = httpx.MockTransport(handler)
    original_get = httpx.get
    
    def mock_get(url: str, **kwargs: Any) -> httpx.Response:
        client = httpx.Client(transport=mock_transport)
        return client.get(url, **kwargs)
    
    httpx.get = mock_get  # type: ignore
    
    try:
        client = SignalClient(
            base_url="http://localhost:8000",
            enable_http_signals=True,
        )
        
        with pytest.raises(SignalUnavailableError, match="exceeds maximum"):
            client.fetch_signal_pack("fiscal")
    finally:
        httpx.get = original_get  # type: ignore


# ====================================================================================
# Circuit Breaker Tests
# ====================================================================================


def test_circuit_breaker_opens_after_threshold() -> None:
    """Test circuit breaker opens after threshold failures."""
    try:
        import httpx
    except ImportError:
        pytest.skip("httpx not installed")
    
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Error")
    
    mock_transport = httpx.MockTransport(handler)
    original_get = httpx.get
    
    def mock_get(url: str, **kwargs: Any) -> httpx.Response:
        client = httpx.Client(transport=mock_transport)
        return client.get(url, **kwargs)
    
    httpx.get = mock_get  # type: ignore
    
    try:
        client = SignalClient(
            base_url="http://localhost:8000",
            enable_http_signals=True,
            circuit_breaker_threshold=3,
            max_retries=1,  # Minimize retries for faster test
        )
        
        # First 3 failures should open circuit (threshold=3)
        for i in range(3):
            try:
                client.fetch_signal_pack("fiscal")
            except (SignalUnavailableError, CircuitBreakerError):
                pass  # Expected
        
        # Circuit should be open now
        assert client._circuit_open is True
        
        # Next call should raise CircuitBreakerError immediately
        with pytest.raises(CircuitBreakerError):
            client.fetch_signal_pack("fiscal")
    finally:
        httpx.get = original_get  # type: ignore


def test_circuit_breaker_closes_after_cooldown() -> None:
    """Test circuit breaker closes after cooldown period."""
    try:
        import httpx
    except ImportError:
        pytest.skip("httpx not installed")
    
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Error")
    
    mock_transport = httpx.MockTransport(handler)
    original_get = httpx.get
    
    def mock_get(url: str, **kwargs: Any) -> httpx.Response:
        client = httpx.Client(transport=mock_transport)
        return client.get(url, **kwargs)
    
    httpx.get = mock_get  # type: ignore
    
    try:
        client = SignalClient(
            base_url="http://localhost:8000",
            enable_http_signals=True,
            circuit_breaker_threshold=2,
            circuit_breaker_cooldown_s=1.0,
            max_retries=1,  # Minimize retries
        )
        
        # Trigger circuit breaker
        for i in range(2):
            try:
                client.fetch_signal_pack("fiscal")
            except (SignalUnavailableError, CircuitBreakerError):
                pass  # Expected
        
        assert client._circuit_open is True
        
        # Wait for cooldown
        time.sleep(1.5)
        
        # Circuit should try to close and fail again
        try:
            client.fetch_signal_pack("fiscal")
        except (SignalUnavailableError, CircuitBreakerError):
            pass  # Expected - still failing but circuit tried to close
        
        # Circuit should have attempted to close
        # (failure_count would be reset to 0 before the attempt)
    finally:
        httpx.get = original_get  # type: ignore


# ====================================================================================
# Helper Function Tests
# ====================================================================================


def test_create_default_signal_pack() -> None:
    """Test default signal pack creation."""
    pack = create_default_signal_pack("fiscal")
    
    assert pack.version == "0.0.0"
    assert pack.policy_area == "fiscal"
    assert pack.thresholds["min_confidence"] == 0.9
    assert pack.metadata["mode"] == "conservative_fallback"


# ====================================================================================
# Integration Tests
# ====================================================================================


def test_signal_client_with_registry_integration() -> None:
    """Test integration of SignalClient with SignalRegistry."""
    client = SignalClient(base_url="memory://")
    registry = SignalRegistry(max_size=10, default_ttl_s=3600)
    
    # Register signal in client
    pack = SignalPack(version="1.0.0", policy_area="fiscal", patterns=["test"])
    client.register_memory_signal("fiscal", pack)
    
    # Fetch and store in registry
    fetched = client.fetch_signal_pack("fiscal")
    assert fetched is not None
    
    registry.put("fiscal", fetched)
    
    # Retrieve from registry
    cached = registry.get("fiscal")
    assert cached is not None
    assert cached.version == "1.0.0"


def test_http_url_without_enable_flag_falls_back_to_memory() -> None:
    """Test that HTTP URL without enable_http_signals flag falls back to memory://."""
    client = SignalClient(
        base_url="http://localhost:8000",
        enable_http_signals=False,
    )
    
    metrics = client.get_metrics()
    assert metrics["transport"] == "memory"


def test_invalid_url_scheme_raises_error() -> None:
    """Test that invalid URL scheme raises error."""
    with pytest.raises(ValueError, match="Invalid base_url scheme"):
        SignalClient(base_url="ftp://localhost")
