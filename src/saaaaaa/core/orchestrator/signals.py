"""Cross-Cut Signal Channel: questionnaire.monolith → orchestrator.

This module implements the strategic signal propagation system that continuously
irrigates patterns, indicators, regex, verbs, entities, and thresholds into the
answer-generation process.

Architecture:
- SignalPack: Typed, versioned signal payload
- SignalRegistry: In-memory LRU cache with TTL
- SignalClient: Circuit-breaker enabled HTTP client
- Signal-aware execution integration

Design Principles:
- Deterministic signal application
- Graceful degradation on signal unavailability
- Full traceability of signal usage
- Observability via metrics and structured logging
"""

from __future__ import annotations

import json
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

# Optional dependency - blake3
try:
    import blake3
    BLAKE3_AVAILABLE = True
except ImportError:
    BLAKE3_AVAILABLE = False
    import hashlib
    # Fallback to hashlib if blake3 not available
    class blake3:  # type: ignore
        @staticmethod
        def blake3(data: bytes) -> object:
            class HashResult:
                def __init__(self, data: bytes) -> None:
                    self._hash = hashlib.sha256(data)
                def hexdigest(self) -> str:
                    return self._hash.hexdigest()
            return HashResult(data)
# Optional dependency - structlog
try:
    import structlog
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False
    import logging
    structlog = logging  # type: ignore  # Fallback to standard logging
from pydantic import BaseModel, Field, field_validator

# Optional dependency - tenacity
try:
    from tenacity import (
        retry,
        retry_if_exception_type,
        stop_after_attempt,
        wait_exponential,
    )
    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False
    # Dummy decorator when tenacity not available
    def retry(*args, **kwargs):  # type: ignore
        def decorator(func):
            return func
        return decorator
    def stop_after_attempt(x) -> None:
        return None  # type: ignore
    def wait_exponential(**kwargs) -> None:
        return None  # type: ignore
    def retry_if_exception_type(x) -> None:
        return None  # type: ignore


logger = structlog.get_logger(__name__) if STRUCTLOG_AVAILABLE else logging.getLogger(__name__)


PolicyArea = Literal[
    "PA01", "PA02", "PA03", "PA04", "PA05",
    "PA06", "PA07", "PA08", "PA09", "PA10",
    # Legacy policy areas (kept for backward compatibility)
    "fiscal", "salud", "ambiente", "energía", "transporte"
]


class SignalPack(BaseModel):
    """
    Versioned strategic signal payload for policy-aware execution.

    Contains curated patterns, indicators, and thresholds specific to a policy area.
    All packs carry fingerprints for drift detection and validation windows.

    Attributes:
        version: Semantic version string (e.g., "1.0.0")
        policy_area: Policy domain this pack targets
        patterns: Text patterns for narrative detection
        indicators: Key performance indicators for scoring
        regex: Regular expressions for structured extraction
        verbs: Action verbs for policy intent detection
        entities: Named entities relevant to policy area
        thresholds: Named thresholds for scoring/filtering
        ttl_s: Time-to-live in seconds for cache management
        source_fingerprint: BLAKE3 hash of source content
        valid_from: ISO timestamp when signal becomes valid
        valid_to: ISO timestamp when signal expires
        metadata: Optional additional metadata
    """

    version: str = Field(
        description="Semantic version string (e.g., '1.0.0')"
    )
    policy_area: PolicyArea = Field(
        description="Policy domain this pack targets"
    )
    patterns: list[str] = Field(
        default_factory=list,
        description="Text patterns for narrative detection"
    )
    indicators: list[str] = Field(
        default_factory=list,
        description="Key performance indicators for scoring"
    )
    regex: list[str] = Field(
        default_factory=list,
        description="Regular expressions for structured extraction"
    )
    verbs: list[str] = Field(
        default_factory=list,
        description="Action verbs for policy intent detection"
    )
    entities: list[str] = Field(
        default_factory=list,
        description="Named entities relevant to policy area"
    )
    thresholds: dict[str, float] = Field(
        default_factory=dict,
        description="Named thresholds for scoring/filtering"
    )
    ttl_s: int = Field(
        default=3600,
        ge=0,
        description="Time-to-live in seconds for cache management"
    )
    source_fingerprint: str = Field(
        default="",
        description="BLAKE3 hash of source content"
    )
    valid_from: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp when signal becomes valid"
    )
    valid_to: str = Field(
        default="",
        description="ISO timestamp when signal expires"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional additional metadata"
    )

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate semantic version format."""
        parts = v.split(".")
        if len(parts) != 3:
            raise ValueError(f"Version must be in format 'X.Y.Z', got '{v}'")
        for part in parts:
            if not part.isdigit():
                raise ValueError(f"Version parts must be numeric, got '{v}'")
        return v

    @field_validator("thresholds")
    @classmethod
    def validate_thresholds(cls, v: dict[str, float]) -> dict[str, float]:
        """Validate threshold values are in valid range."""
        for key, value in v.items():
            if not (0.0 <= value <= 1.0):
                raise ValueError(
                    f"Threshold '{key}' must be in range [0.0, 1.0], got {value}"
                )
        return v

    def compute_hash(self) -> str:
        """
        Compute deterministic BLAKE3 hash of signal pack content.

        Returns:
            Hex string of BLAKE3 hash
        """
        # Use model_dump to get a dict, then sort keys manually
        content_dict = self.model_dump(
            exclude={"source_fingerprint", "valid_from", "valid_to", "metadata"},
        )

        # Sort keys for deterministic hashing
        content_json = json.dumps(content_dict, sort_keys=True, separators=(',', ':'))
        return blake3.blake3(content_json.encode("utf-8")).hexdigest()

    @staticmethod
    def _parse_iso_timestamp(timestamp_str: str) -> datetime:
        """
        Parse ISO timestamp with Z suffix to datetime.

        Args:
            timestamp_str: ISO 8601 timestamp string

        Returns:
            Parsed datetime object
        """
        return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))

    def is_valid(self, now: datetime | None = None) -> bool:
        """
        Check if signal pack is currently valid.

        Args:
            now: Current time (defaults to utcnow)

        Returns:
            True if signal is within validity window
        """
        if now is None:
            now = datetime.now(timezone.utc)

        valid_from_dt = self._parse_iso_timestamp(self.valid_from)
        if now < valid_from_dt:
            return False

        if self.valid_to:
            valid_to_dt = self._parse_iso_timestamp(self.valid_to)
            if now > valid_to_dt:
                return False

        return True

    def get_keys_used(self) -> list[str]:
        """
        Get list of signal keys that have non-empty values.

        Returns:
            List of key names with content
        """
        keys = []
        if self.patterns:
            keys.append("patterns")
        if self.indicators:
            keys.append("indicators")
        if self.regex:
            keys.append("regex")
        if self.verbs:
            keys.append("verbs")
        if self.entities:
            keys.append("entities")
        if self.thresholds:
            keys.append("thresholds")
        return keys


@dataclass
class CacheEntry:
    """Entry in the signal registry cache."""
    signal_pack: SignalPack
    inserted_at: float
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)


class SignalRegistry:
    """
    In-memory LRU cache for signal packs with TTL management.

    Features:
    - LRU eviction when capacity exceeded
    - TTL-based expiration
    - Access tracking for observability
    - Thread-safe operations (single-process)

    Attributes:
        max_size: Maximum number of cached signal packs
        default_ttl_s: Default TTL for cached entries
    """

    def __init__(self, max_size: int = 100, default_ttl_s: int = 3600) -> None:
        """
        Initialize signal registry.

        Args:
            max_size: Maximum cache size
            default_ttl_s: Default TTL in seconds
        """
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._default_ttl_s = default_ttl_s
        self._hits = 0
        self._misses = 0
        self._evictions = 0

        logger.info(
            "signal_registry_initialized",
            max_size=max_size,
            default_ttl_s=default_ttl_s,
        )

    def put(self, policy_area: str, signal_pack: SignalPack) -> None:
        """
        Store signal pack in registry.

        Args:
            policy_area: Policy area key
            signal_pack: Signal pack to store
        """
        now = time.time()

        # Remove expired entries before insertion
        self._evict_expired()

        # LRU eviction if at capacity
        if len(self._cache) >= self._max_size and policy_area not in self._cache:
            oldest_key = next(iter(self._cache))
            self._cache.pop(oldest_key)
            self._evictions += 1
            logger.debug("signal_registry_evicted_lru", key=oldest_key)

        # Insert or update
        entry = CacheEntry(signal_pack=signal_pack, inserted_at=now)
        self._cache[policy_area] = entry
        self._cache.move_to_end(policy_area)  # Mark as most recently used

        logger.info(
            "signal_registry_put",
            policy_area=policy_area,
            version=signal_pack.version,
            hash=signal_pack.compute_hash()[:16],
        )

    def get(self, policy_area: str) -> SignalPack | None:
        """
        Retrieve signal pack from registry.

        Args:
            policy_area: Policy area key

        Returns:
            Signal pack if found and valid, None otherwise
        """
        now = time.time()

        entry = self._cache.get(policy_area)
        if entry is None:
            self._misses += 1
            logger.debug("signal_registry_miss", policy_area=policy_area)
            return None

        # Check TTL expiration
        ttl = entry.signal_pack.ttl_s or self._default_ttl_s
        if now - entry.inserted_at > ttl:
            # Expired, remove from cache
            self._cache.pop(policy_area)
            self._misses += 1
            logger.debug(
                "signal_registry_expired",
                policy_area=policy_area,
                age_s=now - entry.inserted_at,
            )
            return None

        # Check validity window
        if not entry.signal_pack.is_valid():
            self._cache.pop(policy_area)
            self._misses += 1
            logger.debug("signal_registry_invalid", policy_area=policy_area)
            return None

        # Valid hit
        entry.access_count += 1
        entry.last_accessed = now
        self._cache.move_to_end(policy_area)  # Mark as most recently used
        self._hits += 1

        logger.debug(
            "signal_registry_hit",
            policy_area=policy_area,
            access_count=entry.access_count,
        )

        return entry.signal_pack

    def _evict_expired(self) -> None:
        """Remove expired entries from cache."""
        now = time.time()
        expired_keys = []

        for key, entry in self._cache.items():
            ttl = entry.signal_pack.ttl_s or self._default_ttl_s
            if now - entry.inserted_at > ttl:
                expired_keys.append(key)

        for key in expired_keys:
            self._cache.pop(key)
            self._evictions += 1

        if expired_keys:
            logger.debug("signal_registry_evicted_expired", count=len(expired_keys))

    def get_metrics(self) -> dict[str, Any]:
        """
        Get registry metrics for observability.

        Returns:
            Dict with metrics:
            - hit_rate: Cache hit rate [0.0, 1.0]
            - size: Current cache size
            - capacity: Maximum cache size
            - hits: Total cache hits
            - misses: Total cache misses
            - evictions: Total evictions
        """
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0

        # Compute staleness stats
        now = time.time()
        staleness_values = []
        for entry in self._cache.values():
            staleness_values.append(now - entry.inserted_at)

        avg_staleness = sum(staleness_values) / len(staleness_values) if staleness_values else 0.0
        max_staleness = max(staleness_values) if staleness_values else 0.0

        return {
            "hit_rate": hit_rate,
            "size": len(self._cache),
            "capacity": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "evictions": self._evictions,
            "staleness_avg_s": avg_staleness,
            "staleness_max_s": max_staleness,
        }

    def clear(self) -> None:
        """Clear all entries from registry."""
        self._cache.clear()
        logger.info("signal_registry_cleared")


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""
    pass


class SignalUnavailableError(Exception):
    """Raised when signal service is unavailable or returns error."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class InMemorySignalSource:
    """
    In-memory signal source for local/testing mode.

    Provides signal packs directly from memory without HTTP calls.
    Used when base_url starts with "memory://".
    """

    def __init__(self) -> None:
        """Initialize in-memory signal source."""
        self._signals: dict[str, SignalPack] = {}
        logger.info("in_memory_signal_source_initialized")

    def register(self, policy_area: str, signal_pack: SignalPack) -> None:
        """
        Register a signal pack for a policy area.

        Args:
            policy_area: Policy area key
            signal_pack: Signal pack to register
        """
        self._signals[policy_area] = signal_pack
        logger.debug(
            "signal_registered",
            policy_area=policy_area,
            version=signal_pack.version,
        )

    def get(self, policy_area: str) -> SignalPack | None:
        """
        Get signal pack for policy area.

        Args:
            policy_area: Policy area key

        Returns:
            SignalPack if found, None otherwise
        """
        pack = self._signals.get(policy_area)
        if pack:
            logger.debug("memory_signal_hit", policy_area=policy_area)
        else:
            logger.debug("memory_signal_miss", policy_area=policy_area)
        return pack


class SignalClient:
    """
    Signal client supporting both memory:// and HTTP transports.

    Features:
    - memory:// URL scheme for in-process signals (default)
    - HTTP with httpx (behind enable_http_signals flag)
    - ETag support for conditional requests (304 Not Modified)
    - Circuit breaker for fault isolation
    - Automatic retry with exponential backoff
    - Response size validation (≤1.5 MB)
    - Timeout enforcement (≤5s by default)
    - Structured logging and observability

    URL Schemes:
    - memory://: In-process signal source (no network calls)
    - http://...: HTTP signal service with circuit breaker
    - https://...: HTTPS signal service with circuit breaker

    HTTP Status Code Mapping:
    - 200 OK → SignalPack (validated with Pydantic)
    - 304 Not Modified → None (cache is fresh)
    - 401/403 Unauthorized/Forbidden → SignalUnavailableError
    - 429 Too Many Requests → SignalUnavailableError (with retry)
    - 500+ Server Error → SignalUnavailableError (with retry)
    - Timeout → SignalUnavailableError
    """

    # Maximum response size: 1.5 MB
    MAX_RESPONSE_SIZE_BYTES = 1_500_000

    def __init__(
        self,
        base_url: str = "memory://",
        max_retries: int = 3,
        timeout_s: float = 5.0,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_cooldown_s: float = 60.0,
        enable_http_signals: bool = False,
        memory_source: InMemorySignalSource | None = None,
    ) -> None:
        """
        Initialize signal client.

        Args:
            base_url: Base URL for signal service or "memory://" for in-process
            max_retries: Maximum retry attempts for HTTP
            timeout_s: Request timeout in seconds (≤5s recommended)
            circuit_breaker_threshold: Failures before circuit opens (default: 5)
            circuit_breaker_cooldown_s: Cooldown period in seconds (default: 60s)
            enable_http_signals: Enable HTTP transport (requires http:// or https:// URL)
            memory_source: InMemorySignalSource for memory:// mode
        """
        self._base_url = base_url.rstrip("/")
        self._max_retries = max_retries
        self._timeout_s = min(timeout_s, 5.0)  # Cap at 5s
        self._circuit_breaker_threshold = circuit_breaker_threshold
        self._circuit_breaker_cooldown_s = circuit_breaker_cooldown_s
        self._enable_http_signals = enable_http_signals

        # Circuit breaker state
        self._failure_count = 0
        self._circuit_open = False
        self._last_failure_time = 0.0
        self._state_changes: list[dict[str, Any]] = []
        self._max_history = 100

        # Determine transport mode
        if base_url.startswith("memory://"):
            self._transport = "memory"
            self._memory_source = memory_source or InMemorySignalSource()
        elif base_url.startswith(("http://", "https://")):
            if not enable_http_signals:
                logger.warning(
                    "http_signals_disabled",
                    message="HTTP URL provided but enable_http_signals=False. "
                            "Falling back to memory:// mode.",
                )
                self._transport = "memory"
                self._memory_source = memory_source or InMemorySignalSource()
            else:
                self._transport = "http"
                self._memory_source = None
                # Import httpx only when needed
                try:
                    import httpx
                    self._httpx = httpx
                except ImportError as e:
                    raise ImportError(
                        "httpx is required for HTTP signal transport. "
                        "Install with: pip install httpx"
                    ) from e
        else:
            raise ValueError(
                f"Invalid base_url scheme: {base_url}. "
                "Must start with 'memory://', 'http://', or 'https://'"
            )

        # ETag cache for conditional requests
        self._etag_cache: dict[str, str] = {}

        logger.info(
            "signal_client_initialized",
            base_url=base_url,
            transport=self._transport,
            timeout_s=self._timeout_s,
            enable_http_signals=enable_http_signals,
        )

    def fetch_signal_pack(
        self,
        policy_area: str,
        etag: str | None = None,
    ) -> SignalPack | None:
        """
        Fetch signal pack from signal source.

        Args:
            policy_area: Policy area to fetch
            etag: Optional ETag for conditional request (HTTP only)

        Returns:
            SignalPack if successful and fresh
            None if 304 Not Modified or service unavailable

        Raises:
            CircuitBreakerError: If circuit breaker is open
            SignalUnavailableError: If service returns error status
        """
        if self._transport == "memory":
            return self._fetch_from_memory(policy_area)
        else:
            return self._fetch_from_http(policy_area, etag)

    def _fetch_from_memory(self, policy_area: str) -> SignalPack | None:
        """Fetch signal pack from in-memory source."""
        if self._memory_source is None:
            logger.error("memory_source_not_initialized")
            return None

        return self._memory_source.get(policy_area)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(ConnectionError),
    )
    def _fetch_from_http(
        self,
        policy_area: str,
        etag: str | None = None,
    ) -> SignalPack | None:
        """Fetch signal pack from HTTP service."""
        # Check circuit breaker
        if self._circuit_open:
            now = time.time()
            if now - self._last_failure_time < self._circuit_breaker_cooldown_s:
                logger.warning(
                    "signal_client_circuit_open",
                    policy_area=policy_area,
                    cooldown_remaining=self._circuit_breaker_cooldown_s - (now - self._last_failure_time),
                )
                raise CircuitBreakerError(
                    f"Circuit breaker is open. Cooldown remaining: "
                    f"{self._circuit_breaker_cooldown_s - (now - self._last_failure_time):.1f}s"
                )
            else:
                # Try to close circuit
                old_open = self._circuit_open
                self._circuit_open = False
                self._failure_count = 0

                # Record state change
                self._state_changes.append({
                    'timestamp': time.time(),
                    'from_open': old_open,
                    'to_open': self._circuit_open,
                    'failures': self._failure_count,
                })

                # Trim history
                if len(self._state_changes) > self._max_history:
                    self._state_changes = self._state_changes[-self._max_history:]

                logger.info("signal_client_circuit_closed")

        # Build request
        url = f"{self._base_url}/signals/{policy_area}"
        headers = {}

        # Add If-None-Match header if ETag provided
        if etag:
            headers["If-None-Match"] = etag
        elif policy_area in self._etag_cache:
            headers["If-None-Match"] = self._etag_cache[policy_area]

        try:
            response = self._httpx.get(
                url,
                headers=headers,
                timeout=self._timeout_s,
            )

            # Handle status codes
            if response.status_code == 200:
                # Validate response size
                content_length = len(response.content)
                if content_length > self.MAX_RESPONSE_SIZE_BYTES:
                    self._record_failure()
                    raise SignalUnavailableError(
                        f"Response size {content_length} bytes exceeds maximum "
                        f"{self.MAX_RESPONSE_SIZE_BYTES} bytes",
                        status_code=200,
                    )

                # Parse and validate with Pydantic
                data = response.json()
                signal_pack = SignalPack(**data)

                # Cache ETag
                if "ETag" in response.headers:
                    self._etag_cache[policy_area] = response.headers["ETag"]

                # Reset failure count on success
                self._failure_count = 0

                logger.info(
                    "signal_pack_fetched",
                    policy_area=policy_area,
                    version=signal_pack.version,
                    content_length=content_length,
                )

                return signal_pack

            elif response.status_code == 304:
                # Not Modified - cache is fresh
                logger.debug("signal_not_modified", policy_area=policy_area)
                return None

            elif response.status_code in (401, 403):
                # Authentication/Authorization error
                self._record_failure()
                raise SignalUnavailableError(
                    f"Authentication failed: {response.status_code} {response.text}",
                    status_code=response.status_code,
                )

            elif response.status_code == 429:
                # Rate limit - retry will handle this
                self._record_failure()
                raise SignalUnavailableError(
                    "Rate limit exceeded (429 Too Many Requests)",
                    status_code=429,
                )

            elif response.status_code >= 500:
                # Server error - retry will handle this
                self._record_failure()
                raise SignalUnavailableError(
                    f"Server error: {response.status_code} {response.text}",
                    status_code=response.status_code,
                )

            else:
                # Other error
                self._record_failure()
                raise SignalUnavailableError(
                    f"Unexpected status: {response.status_code} {response.text}",
                    status_code=response.status_code,
                )

        except self._httpx.TimeoutException as e:
            self._record_failure()
            raise SignalUnavailableError(
                f"Request timeout after {self._timeout_s}s",
                status_code=None,
            ) from e

        except self._httpx.RequestError as e:
            # Network error
            self._record_failure()
            raise SignalUnavailableError(
                f"Network error: {e}",
                status_code=None,
            ) from e

        except Exception as e:
            # Unexpected error
            logger.error(
                "signal_client_fetch_failed",
                policy_area=policy_area,
                error=str(e),
                error_type=type(e).__name__,
            )
            self._record_failure()
            raise

    def _record_failure(self) -> None:
        """Record a failure and potentially open circuit."""
        old_open = self._circuit_open

        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._failure_count >= self._circuit_breaker_threshold:
            self._circuit_open = True

        # Record state change if circuit opened
        if old_open != self._circuit_open:
            self._state_changes.append({
                'timestamp': time.time(),
                'from_open': old_open,
                'to_open': self._circuit_open,
                'failures': self._failure_count,
            })

            # Trim history
            if len(self._state_changes) > self._max_history:
                self._state_changes = self._state_changes[-self._max_history:]

            logger.warning(
                "signal_client_circuit_opened",
                failure_count=self._failure_count,
                old_open=old_open,
                new_open=self._circuit_open,
            )
        else:
            # Just log the failure increment
            logger.debug(
                "signal_client_failure_recorded",
                failure_count=self._failure_count,
                threshold=self._circuit_breaker_threshold,
            )

    def get_metrics(self) -> dict[str, Any]:
        """
        Get client metrics for observability.

        Returns:
            Dict with metrics:
            - transport: Transport mode (memory or http)
            - circuit_open: Whether circuit breaker is open
            - failure_count: Current failure count
            - etag_cache_size: Number of cached ETags
            - state_change_count: Number of circuit breaker state changes
            - last_failure_time: Timestamp of last failure (or None)
        """
        return {
            "transport": self._transport,
            "circuit_open": self._circuit_open,
            "failure_count": self._failure_count,
            "etag_cache_size": len(self._etag_cache),
            "state_change_count": len(self._state_changes),
            "last_failure_time": self._last_failure_time if self._last_failure_time else None,
        }

    def get_state_history(self) -> list[dict[str, Any]]:
        """
        Get history of circuit breaker state changes for monitoring.

        Returns:
            List of state change records with timestamps
        """
        return list(self._state_changes)

    def register_memory_signal(self, policy_area: str, signal_pack: SignalPack) -> None:
        """
        Register signal pack in memory source (memory:// mode only).

        Args:
            policy_area: Policy area key
            signal_pack: Signal pack to register

        Raises:
            ValueError: If not in memory:// mode
        """
        if self._transport != "memory" or self._memory_source is None:
            raise ValueError("Can only register signals in memory:// mode")

        self._memory_source.register(policy_area, signal_pack)


@dataclass
class SignalUsageMetadata:
    """
    Metadata about signal usage in an execution.

    Attributes:
        version: Signal pack version used
        policy_area: Policy area of signals
        hash: Content hash of signal pack
        keys_used: List of signal keys actually used
        timestamp_utc: ISO timestamp of usage
    """

    version: str
    policy_area: str
    hash: str
    keys_used: list[str]
    timestamp_utc: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "version": self.version,
            "policy_area": self.policy_area,
            "hash": self.hash,
            "keys_used": self.keys_used,
            "timestamp_utc": self.timestamp_utc,
        }


def create_default_signal_pack(policy_area: PolicyArea) -> SignalPack:
    """
    Create default signal pack for a policy area (conservative mode).

    Args:
        policy_area: Policy area

    Returns:
        SignalPack with conservative defaults
    """
    return SignalPack(
        version="0.0.0",
        policy_area=policy_area,
        patterns=[],
        indicators=[],
        regex=[],
        verbs=[],
        entities=[],
        thresholds={
            "min_confidence": 0.9,
            "min_evidence": 0.8,
        },
        ttl_s=0,  # No expiration for defaults
        source_fingerprint="default",
        metadata={"mode": "conservative_fallback"},
    )
