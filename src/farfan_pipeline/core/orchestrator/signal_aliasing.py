"""Signal Aliasing Module - Soft-alias pattern for PA07-PA10 fingerprint canonicalization.

This module implements the soft-alias pattern to prevent duplicate fingerprints
and ensure proper cache invalidation for policy areas PA07-PA10.

Key Features:
- Canonical fingerprint computation from signal content (not static strings)
- Backward-compatible alias mapping for legacy fingerprints
- Cache invalidation support via content-based hashing
- Merkle tree integrity for PA07-PA10

SOTA Requirements:
- Prevents silent degradation from static fingerprints
- Enables observability for PA coverage gaps
- Supports intelligent fallback fusion
"""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .signals import SignalPack

try:
    import blake3
    BLAKE3_AVAILABLE = True
except ImportError:
    BLAKE3_AVAILABLE = False

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


def resolve_fingerprint_alias(fingerprint: str, legacy_aliases: dict[str, str]) -> str:
    """
    Resolve legacy fingerprint to canonical policy area using a provided alias map.

    Args:
        fingerprint: Fingerprint to resolve (may be legacy or canonical).
        legacy_aliases: A dictionary mapping legacy fingerprints to canonical IDs.

    Returns:
        Canonical policy area ID (PA01-PA10) or original fingerprint.

    Example:
        >>> aliases = {"pa07_v1_land_territory": "PA07"}
        >>> resolve_fingerprint_alias("pa07_v1_land_territory", aliases)
        'PA07'
        >>> resolve_fingerprint_alias("abc123...", aliases)
        'abc123...'
    """
    return legacy_aliases.get(fingerprint, fingerprint)


def build_fingerprint_index(
    signal_packs: dict[str, SignalPack]
) -> dict[str, str]:
    """
    Build fingerprint index mapping canonical fingerprints to policy areas.

    This creates a reverse index for cache lookups:
    - canonical_fingerprint -> policy_area_id
    - Supports both legacy and content-based fingerprints

    Args:
        signal_packs: Dict mapping policy_area_id to SignalPack

    Returns:
        Dict mapping canonical_fingerprint to policy_area_id

    Example:
        >>> packs = build_all_signal_packs()
        >>> index = build_fingerprint_index(packs)
        >>> print(f"Index size: {len(index)}")
    """
    fingerprint_index = {}

    for policy_area_id, signal_pack in signal_packs.items():
        # Compute canonical fingerprint
        canonical_fp = canonicalize_signal_fingerprint(signal_pack)

        # Map canonical fingerprint to policy area
        fingerprint_index[canonical_fp] = policy_area_id

        # Also map legacy fingerprint for backward compatibility
        legacy_fp = signal_pack.source_fingerprint
        if legacy_fp and legacy_fp != canonical_fp:
            fingerprint_index[legacy_fp] = policy_area_id

    logger.info(
        "fingerprint_index_built",
        index_size=len(fingerprint_index),
        policy_areas=len(signal_packs),
    )

    return fingerprint_index


def validate_fingerprint_uniqueness(
    signal_packs: dict[str, SignalPack]
) -> dict[str, Any]:
    """
    Validate that all fingerprints are unique (no duplicates).

    This is a quality gate to prevent fingerprint collisions that would
    break cache invalidation and Merkle tree integrity.

    Args:
        signal_packs: Dict mapping policy_area_id to SignalPack

    Returns:
        Validation result with:
        - is_valid: bool
        - duplicates: list of duplicate fingerprints
        - collisions: dict mapping fingerprint to list of policy areas

    Example:
        >>> packs = build_all_signal_packs()
        >>> result = validate_fingerprint_uniqueness(packs)
        >>> assert result["is_valid"], "Fingerprint collision detected!"
    """
    fingerprint_to_pas = {}

    for policy_area_id, signal_pack in signal_packs.items():
        canonical_fp = canonicalize_signal_fingerprint(signal_pack)

        if canonical_fp not in fingerprint_to_pas:
            fingerprint_to_pas[canonical_fp] = []

        fingerprint_to_pas[canonical_fp].append(policy_area_id)

    # Find duplicates
    duplicates = {
        fp: pas
        for fp, pas in fingerprint_to_pas.items()
        if len(pas) > 1
    }

    is_valid = len(duplicates) == 0

    result = {
        "is_valid": is_valid,
        "total_fingerprints": len(fingerprint_to_pas),
        "unique_fingerprints": len([pas for pas in fingerprint_to_pas.values() if len(pas) == 1]),
        "duplicates": list(duplicates.keys()),
        "collisions": duplicates,
    }

    if not is_valid:
        logger.error(
            "fingerprint_collision_detected",
            duplicates=duplicates,
        )
    else:
        logger.info(
            "fingerprint_uniqueness_validated",
            total_fingerprints=result["total_fingerprints"],
        )

    return result


def upgrade_legacy_fingerprints(
    signal_packs: dict[str, SignalPack]
) -> dict[str, SignalPack]:
    """
    Upgrade legacy fingerprints to canonical content-based fingerprints.

    This is a migration helper for PA07-PA10 to transition from static
    fingerprints to content-based fingerprints.

    Args:
        signal_packs: Dict mapping policy_area_id to SignalPack

    Returns:
        Updated signal_packs with canonical fingerprints

    Example:
        >>> packs = build_all_signal_packs()
        >>> upgraded_packs = upgrade_legacy_fingerprints(packs)
        >>> for pa, pack in upgraded_packs.items():
        >>>     print(f"{pa}: {pack.source_fingerprint}")
    """
    upgraded_packs = {}

    for policy_area_id, signal_pack in signal_packs.items():
        # Compute canonical fingerprint
        canonical_fp = canonicalize_signal_fingerprint(signal_pack)

        # Update source_fingerprint to canonical
        signal_pack.source_fingerprint = canonical_fp

        # Add migration metadata
        if "migration" not in signal_pack.metadata:
            signal_pack.metadata["migration"] = {}

        signal_pack.metadata["migration"]["upgraded_to_canonical"] = True
        signal_pack.metadata["migration"]["canonical_fingerprint"] = canonical_fp

        upgraded_packs[policy_area_id] = signal_pack

    logger.info(
        "legacy_fingerprints_upgraded",
        upgraded_count=len(upgraded_packs),
    )

    return upgraded_packs
