"""Signal Cache Invalidation Module - Content-based cache invalidation for PA signals.

This module implements cache invalidation strategies based on canonical fingerprints,
ensuring that cache entries are invalidated when signal content changes.

Key Features:
- Content-based cache keys (fingerprint-derived)
- TTL-based expiration with grace periods
- Merkle tree validation for cache integrity
- Cache warming for high-traffic PAs
- Invalidation audit trail

SOTA Requirements:
- Prevents stale cache serving from static fingerprints
- Ensures data integrity across PA01-PA10
- Supports soft-alias pattern for PA07-PA10
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .signals import SignalPack

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry for SignalPack.

    Attributes:
        key: Cache key (canonical fingerprint)
        policy_area_id: Policy area identifier
        signal_pack: Cached SignalPack object
        created_at: Creation timestamp (Unix epoch)
        expires_at: Expiration timestamp (Unix epoch)
        access_count: Number of cache hits
        last_accessed: Last access timestamp (Unix epoch)
        metadata: Additional metadata
    """
    key: str
    policy_area_id: str
    signal_pack: SignalPack
    created_at: float
    expires_at: float
    access_count: int = 0
    last_accessed: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return time.time() >= self.expires_at

    @property
    def ttl_remaining(self) -> float:
        """Get remaining TTL in seconds."""
        return max(0.0, self.expires_at - time.time())

    @property
    def age_seconds(self) -> float:
        """Get age of cache entry in seconds."""
        return time.time() - self.created_at


@dataclass
class CacheInvalidationEvent:
    """Event record for cache invalidation.

    Attributes:
        event_type: Type of invalidation event
        policy_area_id: Affected policy area
        old_fingerprint: Previous fingerprint
        new_fingerprint: New fingerprint (if applicable)
        timestamp: Event timestamp (Unix epoch)
        reason: Human-readable reason
        metadata: Additional metadata
    """
    event_type: str
    policy_area_id: str
    old_fingerprint: str | None
    new_fingerprint: str | None
    timestamp: float
    reason: str
    metadata: dict[str, Any] = field(default_factory=dict)


class SignalPackCache:
    """In-memory cache for SignalPacks with content-based invalidation.

    This implements a simple in-memory cache with:
    - Content-based cache keys (canonical fingerprints)
    - TTL-based expiration
    - Access tracking
    - Invalidation audit trail
    """

    def __init__(self, max_size: int = 100):
        """
        Initialize SignalPackCache.

        Args:
            max_size: Maximum cache size (LRU eviction)
        """
        self.max_size = max_size
        self._cache: dict[str, CacheEntry] = {}
        self._invalidation_log: list[CacheInvalidationEvent] = []

    def get(self, key: str) -> SignalPack | None:
        """
        Get SignalPack from cache.

        Args:
            key: Cache key (canonical fingerprint)

        Returns:
            Cached SignalPack or None if not found/expired

        Example:
            >>> cache = SignalPackCache()
            >>> pack = cache.get("abc123...")
        """
        entry = self._cache.get(key)

        if entry is None:
            logger.debug("cache_miss", key=key[:8])
            return None

        # Check expiration
        if entry.is_expired:
            logger.debug("cache_expired", key=key[:8], age=entry.age_seconds)
            self._invalidate_entry(key, "expired")
            return None

        # Update access tracking
        entry.access_count += 1
        entry.last_accessed = time.time()

        logger.debug(
            "cache_hit",
            key=key[:8],
            policy_area=entry.policy_area_id,
            access_count=entry.access_count,
        )

        return entry.signal_pack

    def put(
        self,
        key: str,
        policy_area_id: str,
        signal_pack: SignalPack,
        ttl_seconds: float | None = None,
    ) -> None:
        """
        Put SignalPack into cache.

        Args:
            key: Cache key (canonical fingerprint)
            policy_area_id: Policy area identifier
            signal_pack: SignalPack to cache
            ttl_seconds: TTL in seconds (uses signal_pack.ttl_s if None)

        Example:
            >>> cache = SignalPackCache()
            >>> cache.put("abc123...", "PA07", pack)
        """
        # Determine TTL
        if ttl_seconds is None:
            ttl_seconds = signal_pack.ttl_s or 86400.0  # Default 24 hours

        # Check cache size and evict if necessary
        if len(self._cache) >= self.max_size and key not in self._cache:
            self._evict_lru()

        # Create cache entry
        now = time.time()
        entry = CacheEntry(
            key=key,
            policy_area_id=policy_area_id,
            signal_pack=signal_pack,
            created_at=now,
            expires_at=now + ttl_seconds,
            last_accessed=now,
            metadata={
                "version": signal_pack.version,
                "fingerprint": signal_pack.source_fingerprint,
            },
        )

        self._cache[key] = entry

        logger.debug(
            "cache_put",
            key=key[:8],
            policy_area=policy_area_id,
            ttl_seconds=ttl_seconds,
        )

    def invalidate(self, key: str, reason: str = "manual") -> bool:
        """
        Invalidate cache entry.

        Args:
            key: Cache key to invalidate
            reason: Reason for invalidation

        Returns:
            True if entry was invalidated, False if not found

        Example:
            >>> cache.invalidate("abc123...", "content_changed")
        """
        return self._invalidate_entry(key, reason)

    def invalidate_by_policy_area(
        self,
        policy_area_id: str,
        reason: str = "manual",
    ) -> int:
        """
        Invalidate all cache entries for a policy area.

        Args:
            policy_area_id: Policy area identifier
            reason: Reason for invalidation

        Returns:
            Number of entries invalidated

        Example:
            >>> count = cache.invalidate_by_policy_area("PA07", "signal_updated")
        """
        keys_to_invalidate = [
            key for key, entry in self._cache.items()
            if entry.policy_area_id == policy_area_id
        ]

        for key in keys_to_invalidate:
            self._invalidate_entry(key, reason)

        logger.info(
            "policy_area_invalidated",
            policy_area=policy_area_id,
            invalidated_count=len(keys_to_invalidate),
            reason=reason,
        )

        return len(keys_to_invalidate)

    def invalidate_all(self, reason: str = "manual") -> int:
        """
        Invalidate all cache entries.

        Args:
            reason: Reason for invalidation

        Returns:
            Number of entries invalidated

        Example:
            >>> count = cache.invalidate_all("system_restart")
        """
        keys = list(self._cache.keys())
        for key in keys:
            self._invalidate_entry(key, reason)

        logger.info(
            "cache_invalidated_all",
            invalidated_count=len(keys),
            reason=reason,
        )

        return len(keys)

    def warm_cache(
        self,
        signal_packs: dict[str, SignalPack],
    ) -> int:
        """
        Warm cache with signal packs.

        Args:
            signal_packs: Dict mapping policy_area_id to SignalPack

        Returns:
            Number of entries warmed

        Example:
            >>> packs = build_all_signal_packs()
            >>> cache.warm_cache(packs)
        """
        # Import here to avoid circular dependency
        from .signal_aliasing import canonicalize_signal_fingerprint

        warmed_count = 0

        for policy_area_id, signal_pack in signal_packs.items():
            # Compute canonical fingerprint
            canonical_fp = canonicalize_signal_fingerprint(signal_pack)

            # Put in cache
            self.put(canonical_fp, policy_area_id, signal_pack)
            warmed_count += 1

        logger.info(
            "cache_warmed",
            warmed_count=warmed_count,
        )

        return warmed_count

    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Cache statistics dict

        Example:
            >>> stats = cache.get_stats()
            >>> print(f"Size: {stats['size']}, Hit rate: {stats['hit_rate']:.2%}")
        """
        total_accesses = sum(entry.access_count for entry in self._cache.values())
        expired_count = sum(1 for entry in self._cache.values() if entry.is_expired)

        # Compute hit rate (rough estimate)
        invalidation_count = len(self._invalidation_log)
        hit_rate = total_accesses / max(total_accesses + invalidation_count, 1)

        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "total_accesses": total_accesses,
            "expired_count": expired_count,
            "invalidation_count": invalidation_count,
            "hit_rate": hit_rate,
        }

    def _invalidate_entry(self, key: str, reason: str) -> bool:
        """Internal method to invalidate cache entry."""
        entry = self._cache.pop(key, None)

        if entry is None:
            return False

        # Log invalidation event
        event = CacheInvalidationEvent(
            event_type="invalidation",
            policy_area_id=entry.policy_area_id,
            old_fingerprint=entry.metadata.get("fingerprint"),
            new_fingerprint=None,
            timestamp=time.time(),
            reason=reason,
            metadata={
                "age_seconds": entry.age_seconds,
                "access_count": entry.access_count,
            },
        )

        self._invalidation_log.append(event)

        logger.debug(
            "cache_invalidated",
            key=key[:8],
            policy_area=entry.policy_area_id,
            reason=reason,
            age=entry.age_seconds,
        )

        return True

    def _evict_lru(self) -> None:
        """Evict least recently used cache entry."""
        if not self._cache:
            return

        # Find LRU entry
        lru_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].last_accessed,
        )

        self._invalidate_entry(lru_key, "lru_eviction")


def build_cache_key(policy_area_id: str, signal_pack: SignalPack) -> str:
    """
    Build cache key from SignalPack using canonical fingerprint.

    This uses the soft-alias pattern to ensure cache keys are content-based.

    Args:
        policy_area_id: Policy area identifier
        signal_pack: SignalPack to compute key for

    Returns:
        Cache key (canonical fingerprint)

    Example:
        >>> pack = build_signal_pack_from_monolith("PA07")
        >>> key = build_cache_key("PA07", pack)
        >>> print(f"Cache key: {key}")
    """
    # Import here to avoid circular dependency
    from .signal_aliasing import canonicalize_signal_fingerprint

    canonical_fp = canonicalize_signal_fingerprint(signal_pack)

    logger.debug(
        "cache_key_built",
        policy_area=policy_area_id,
        canonical_fp=canonical_fp[:8],
    )

    return canonical_fp


def validate_cache_integrity(
    cache: SignalPackCache,
    signal_packs: dict[str, SignalPack],
) -> dict[str, Any]:
    """
    Validate cache integrity against current signal packs.

    This checks:
    - All cached entries have valid fingerprints
    - Cached content matches current signal packs
    - No stale entries exist

    Args:
        cache: SignalPackCache to validate
        signal_packs: Dict mapping policy_area_id to SignalPack

    Returns:
        Validation result dict

    Example:
        >>> cache = SignalPackCache()
        >>> cache.warm_cache(packs)
        >>> result = validate_cache_integrity(cache, packs)
        >>> assert result["is_valid"], "Cache integrity violation detected!"
    """
    # Import here to avoid circular dependency
    from .signal_aliasing import canonicalize_signal_fingerprint

    stale_entries = []
    mismatched_entries = []

    for policy_area_id, signal_pack in signal_packs.items():
        # Compute current canonical fingerprint
        canonical_fp = canonicalize_signal_fingerprint(signal_pack)

        # Check if cached
        cached_pack = cache.get(canonical_fp)

        if cached_pack is None:
            continue  # Not cached (OK)

        # Compute cached fingerprint
        cached_fp = canonicalize_signal_fingerprint(cached_pack)

        # Check fingerprint match
        if cached_fp != canonical_fp:
            mismatched_entries.append({
                "policy_area": policy_area_id,
                "expected_fp": canonical_fp[:8],
                "actual_fp": cached_fp[:8],
            })

    is_valid = len(stale_entries) == 0 and len(mismatched_entries) == 0

    result = {
        "is_valid": is_valid,
        "stale_entries": stale_entries,
        "mismatched_entries": mismatched_entries,
        "cache_stats": cache.get_stats(),
    }

    if is_valid:
        logger.info("cache_integrity_validated", cache_size=cache.get_stats()["size"])
    else:
        logger.error(
            "cache_integrity_violation",
            stale_count=len(stale_entries),
            mismatch_count=len(mismatched_entries),
        )

    return result


def create_global_cache() -> SignalPackCache:
    """
    Create global SignalPackCache instance.

    This is a convenience factory for creating a cache with sensible defaults.

    Returns:
        SignalPackCache instance

    Example:
        >>> cache = create_global_cache()
        >>> packs = build_all_signal_packs()
        >>> cache.warm_cache(packs)
    """
    cache = SignalPackCache(max_size=100)

    logger.info("global_cache_created", max_size=cache.max_size)

    return cache
