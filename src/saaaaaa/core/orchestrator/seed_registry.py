"""
Seed Registry for Deterministic Execution

Centralized seed management for reproducible stochastic operations across
the orchestrator and all executors.

Key Features:
- SHA256-based seed derivation from policy_unit_id + correlation_id + component
- Unique seeds per component (numpy, python, quantum, neuromorphic, meta-learner)
- Version tracking for seed generation algorithm
- Audit trail for debugging non-determinism
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

# Current seed derivation algorithm version
SEED_VERSION = "sha256_v1"


@dataclass
class SeedRecord:
    """Record of a generated seed for audit purposes."""
    policy_unit_id: str
    correlation_id: str
    component: str
    seed: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
    seed_version: str = SEED_VERSION


class SeedRegistry:
    """
    Central registry for deterministic seed generation and tracking.

    Ensures that all stochastic operations (NumPy RNG, Python random, quantum
    optimizers, neuromorphic controllers, meta-learner strategies) receive
    consistent, reproducible seeds derived from execution context.

    Usage:
        registry = SeedRegistry()
        np_seed = registry.get_seed(
            policy_unit_id="plan_2024",
            correlation_id="exec_12345",
            component="numpy"
        )
        rng = np.random.default_rng(np_seed)
    """

    def __init__(self) -> None:
        """Initialize seed registry with empty audit log."""
        self._audit_log: list[SeedRecord] = []
        self._seed_cache: dict[tuple[str, str, str], int] = {}
        logger.info(f"SeedRegistry initialized with version {SEED_VERSION}")

    def get_seed(
        self,
        policy_unit_id: str,
        correlation_id: str,
        component: str
    ) -> int:
        """
        Get deterministic seed for a specific component.

        Args:
            policy_unit_id: Unique identifier for the policy document/unit
            correlation_id: Unique identifier for this execution context
            component: Component name (numpy, python, quantum, neuromorphic, meta_learner)

        Returns:
            Deterministic 32-bit unsigned integer seed

        Examples:
            >>> registry = SeedRegistry()
            >>> seed1 = registry.get_seed("plan_2024", "exec_001", "numpy")
            >>> seed2 = registry.get_seed("plan_2024", "exec_001", "numpy")
            >>> assert seed1 == seed2  # Same inputs = same seed
        """
        # Check cache first
        cache_key = (policy_unit_id, correlation_id, component)
        if cache_key in self._seed_cache:
            return self._seed_cache[cache_key]

        # Derive seed
        base_material = f"{policy_unit_id}:{correlation_id}:{component}"
        seed = self.derive_seed(base_material)

        # Cache and audit
        self._seed_cache[cache_key] = seed
        self._audit_log.append(SeedRecord(
            policy_unit_id=policy_unit_id,
            correlation_id=correlation_id,
            component=component,
            seed=seed
        ))

        logger.debug(
            f"Generated seed {seed} for component={component}, "
            f"policy_unit_id={policy_unit_id}, correlation_id={correlation_id}"
        )

        return seed

    def derive_seed(self, base_material: str) -> int:
        """
        Derive deterministic seed from base material using SHA256.

        Args:
            base_material: String to hash (e.g., "plan_2024:exec_001:numpy")

        Returns:
            32-bit unsigned integer seed derived from hash

        Implementation:
            - Uses SHA256 for cryptographic strength
            - Takes first 4 bytes of digest
            - Converts to unsigned 32-bit integer
            - Ensures seed fits in range [0, 2^32-1]
        """
        digest = hashlib.sha256(base_material.encode("utf-8")).digest()
        seed = int.from_bytes(digest[:4], byteorder="big")
        return seed

    def get_audit_log(self) -> list[SeedRecord]:
        """
        Get complete audit log of all generated seeds.

        Returns:
            List of SeedRecord objects with generation history

        Useful for debugging non-determinism issues.
        """
        return list(self._audit_log)

    def clear_cache(self) -> None:
        """Clear seed cache (useful for testing or isolation)."""
        self._seed_cache.clear()
        logger.debug("Seed cache cleared")

    def get_seeds_for_context(
        self,
        policy_unit_id: str,
        correlation_id: str
    ) -> dict[str, int]:
        """
        Get all standard seeds for an execution context.

        Args:
            policy_unit_id: Unique identifier for the policy document/unit
            correlation_id: Unique identifier for this execution context

        Returns:
            Dictionary mapping component names to seeds

        Components:
            - numpy: NumPy RNG initialization
            - python: Python random module seeding
            - quantum: Quantum optimizer initialization
            - neuromorphic: Neuromorphic controller initialization
            - meta_learner: Meta-learner strategy selection
        """
        components = ["numpy", "python", "quantum", "neuromorphic", "meta_learner"]
        return {
            component: self.get_seed(policy_unit_id, correlation_id, component)
            for component in components
        }

    def get_manifest_entry(
        self,
        policy_unit_id: str | None = None,
        correlation_id: str | None = None
    ) -> dict:
        """
        Get manifest entry for verification manifest.

        Args:
            policy_unit_id: Optional filter by policy_unit_id
            correlation_id: Optional filter by correlation_id

        Returns:
            Dictionary suitable for inclusion in verification_manifest.json
        """
        # Filter audit log if criteria provided
        if policy_unit_id or correlation_id:
            filtered_log = [
                record for record in self._audit_log
                if (not policy_unit_id or record.policy_unit_id == policy_unit_id)
                and (not correlation_id or record.correlation_id == correlation_id)
            ]
        else:
            filtered_log = self._audit_log

        # Use first record for base info (they should all have same context)
        base_record = filtered_log[0] if filtered_log else None

        manifest = {
            "seed_version": SEED_VERSION,
            "seeds_generated": len(filtered_log),
        }

        if base_record:
            manifest["policy_unit_id"] = base_record.policy_unit_id
            manifest["correlation_id"] = base_record.correlation_id

            # Include seed breakdown by component
            manifest["seeds_by_component"] = {
                record.component: record.seed
                for record in filtered_log
            }

        return manifest


# Global registry instance (singleton pattern)
_global_registry: SeedRegistry | None = None


def get_global_seed_registry() -> SeedRegistry:
    """
    Get or create the global seed registry instance.

    Returns:
        Global SeedRegistry singleton
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = SeedRegistry()
    return _global_registry


def reset_global_seed_registry() -> None:
    """Reset the global seed registry (useful for testing)."""
    global _global_registry
    _global_registry = None
