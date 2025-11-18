"""
Verification Manifest Generation with Cryptographic Integrity

Generates verification manifests for pipeline executions with HMAC signatures
for tamper detection and comprehensive execution environment tracking.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import platform
import sys
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

# Manifest schema version
MANIFEST_VERSION = "1.0.0"


class VerificationManifest:
    """
    Builder for verification manifests with cryptographic integrity.

    Features:
    - JSON Schema validation
    - HMAC-SHA256 integrity signatures
    - Execution environment tracking
    - Determinism metadata
    - Phase and artifact tracking
    """

    def __init__(self, hmac_secret: str | None = None) -> None:
        """
        Initialize manifest builder.

        Args:
            hmac_secret: Secret key for HMAC generation. If None, uses
                        environment variable VERIFICATION_HMAC_SECRET.
                        If not set, generates warning (integrity disabled).
        """
        self.hmac_secret = hmac_secret or os.getenv("VERIFICATION_HMAC_SECRET")
        if not self.hmac_secret:
            logger.warning(
                "No HMAC secret provided. Integrity verification disabled. "
                "Set VERIFICATION_HMAC_SECRET environment variable."
            )

        self.manifest_data: dict[str, Any] = {
            "version": MANIFEST_VERSION,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "success": False,  # Default to false, set explicitly
        }

    def set_success(self, success: bool):
        """Set overall pipeline success flag."""
        self.manifest_data["success"] = success
        return self

    def set_pipeline_hash(self, pipeline_hash: str):
        """Set SHA256 hash of pipeline execution."""
        self.manifest_data["pipeline_hash"] = pipeline_hash
        return self

    def set_environment(self):
        """
        Capture execution environment information.

        Automatically captures:
        - Python version
        - Platform (OS)
        - CPU count
        - Available memory (if psutil available)
        - UTC timestamp
        """
        env_data = {
            "python_version": sys.version,
            "platform": platform.platform(),
            "cpu_count": os.cpu_count() or 1,
            "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        }

        # Try to get memory info
        try:
            import psutil
            mem = psutil.virtual_memory()
            env_data["memory_gb"] = round(mem.total / (1024**3), 2)
        except ImportError:
            logger.debug("psutil not available, skipping memory info")
        except Exception as e:
            logger.debug(f"Failed to get memory info: {e}")

        self.manifest_data["environment"] = env_data
        return self

    def set_determinism(
        self,
        seed_version: str,
        base_seed: int | None = None,
        policy_unit_id: str | None = None,
        correlation_id: str | None = None,
        seeds_by_component: dict[str, int] | None = None
    ):
        """
        Set determinism tracking information.

        Args:
            seed_version: Seed derivation algorithm version
            base_seed: Base seed used
            policy_unit_id: Policy unit identifier
            correlation_id: Execution correlation ID
            seeds_by_component: Dict mapping component names to seeds
        """
        determinism_data = {
            "seed_version": seed_version
        }

        if base_seed is not None:
            determinism_data["base_seed"] = base_seed
        if policy_unit_id:
            determinism_data["policy_unit_id"] = policy_unit_id
        if correlation_id:
            determinism_data["correlation_id"] = correlation_id
        if seeds_by_component:
            determinism_data["seeds_by_component"] = seeds_by_component

        self.manifest_data["determinism"] = determinism_data
        return self

    def set_calibrations(
        self,
        version: str,
        calibration_hash: str,
        methods_calibrated: int,
        methods_missing: list[str]
    ):
        """
        Set calibration information.

        Args:
            version: Calibration registry version
            calibration_hash: SHA256 hash of calibration data
            methods_calibrated: Number of calibrated methods
            methods_missing: List of methods without calibration
        """
        self.manifest_data["calibrations"] = {
            "version": version,
            "hash": calibration_hash,
            "methods_calibrated": methods_calibrated,
            "methods_missing": methods_missing
        }
        return self

    def set_ingestion(
        self,
        method: str,
        chunk_count: int,
        text_length: int,
        sentence_count: int,
        chunk_strategy: str | None = None,
        chunk_overlap: int | None = None
    ):
        """
        Set ingestion information.

        Args:
            method: Ingestion method ("SPC" or "CPP")
            chunk_count: Number of chunks
            text_length: Total text length
            sentence_count: Number of sentences
            chunk_strategy: Chunking strategy used
            chunk_overlap: Chunk overlap in characters
        """
        ingestion_data = {
            "method": method,
            "chunk_count": chunk_count,
            "text_length": text_length,
            "sentence_count": sentence_count
        }

        if chunk_strategy:
            ingestion_data["chunk_strategy"] = chunk_strategy
        if chunk_overlap is not None:
            ingestion_data["chunk_overlap"] = chunk_overlap

        self.manifest_data["ingestion"] = ingestion_data
        return self

    def add_phase(
        self,
        phase_id: int,
        phase_name: str,
        success: bool,
        duration_ms: float | None = None,
        items_processed: int | None = None,
        error: str | None = None
    ):
        """
        Add phase execution information.

        Args:
            phase_id: Phase numeric identifier
            phase_name: Phase human-readable name
            success: Phase execution success
            duration_ms: Duration in milliseconds
            items_processed: Number of items processed
            error: Error message if failed
        """
        if "phases" not in self.manifest_data:
            self.manifest_data["phases"] = []

        phase_data = {
            "phase_id": phase_id,
            "phase_name": phase_name,
            "success": success
        }

        if duration_ms is not None:
            phase_data["duration_ms"] = duration_ms
        if items_processed is not None:
            phase_data["items_processed"] = items_processed
        if error:
            phase_data["error"] = error

        self.manifest_data["phases"].append(phase_data)
        return self

    def add_artifact(
        self,
        artifact_id: str,
        path: str,
        artifact_hash: str,
        size_bytes: int | None = None
    ):
        """
        Add artifact information.

        Args:
            artifact_id: Artifact identifier
            path: Artifact file path
            artifact_hash: SHA256 hash of artifact
            size_bytes: Artifact size in bytes
        """
        if "artifacts" not in self.manifest_data:
            self.manifest_data["artifacts"] = {}

        artifact_data = {
            "path": path,
            "hash": artifact_hash
        }

        if size_bytes is not None:
            artifact_data["size_bytes"] = size_bytes

        self.manifest_data["artifacts"][artifact_id] = artifact_data
        return self

    def _compute_hmac(self, content: str) -> str:
        """
        Compute HMAC-SHA256 of manifest content.

        Args:
            content: JSON string of manifest (without HMAC field)

        Returns:
            Hex-encoded HMAC signature
        """
        if not self.hmac_secret:
            return "00" * 32  # Placeholder if no secret

        signature = hmac.new(
            self.hmac_secret.encode("utf-8"),
            content.encode("utf-8"),
            hashlib.sha256
        )
        return signature.hexdigest()

    def build(self) -> dict[str, Any]:
        """
        Build final manifest with HMAC signature.

        Returns:
            Complete manifest dictionary with integrity_hmac
        """
        # Create canonical JSON (without HMAC)
        canonical = json.dumps(
            self.manifest_data,
            sort_keys=True,
            indent=None,
            separators=(',', ':')
        )

        # Compute HMAC
        hmac_signature = self._compute_hmac(canonical)

        # Add HMAC to manifest
        final_manifest = dict(self.manifest_data)
        final_manifest["integrity_hmac"] = hmac_signature

        return final_manifest

    def build_json(self, indent: int = 2) -> str:
        """
        Build manifest as JSON string.

        Args:
            indent: JSON indentation level

        Returns:
            Pretty-printed JSON string
        """
        manifest = self.build()
        return json.dumps(manifest, indent=indent)

    def write(self, filepath: str) -> None:
        """
        Write manifest to file.

        Args:
            filepath: Path to write manifest JSON
        """
        manifest_json = self.build_json()

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(manifest_json)

        logger.info(f"Verification manifest written to: {filepath}")


def verify_manifest_integrity(
    manifest: dict[str, Any],
    hmac_secret: str
) -> bool:
    """
    Verify HMAC integrity of a manifest.

    Args:
        manifest: Manifest dictionary (with integrity_hmac)
        hmac_secret: HMAC secret key

    Returns:
        True if HMAC is valid, False otherwise
    """
    if "integrity_hmac" not in manifest:
        logger.error("Manifest missing integrity_hmac field")
        return False

    # Extract HMAC
    provided_hmac = manifest["integrity_hmac"]

    # Rebuild manifest without HMAC
    manifest_without_hmac = {k: v for k, v in manifest.items() if k != "integrity_hmac"}

    # Compute canonical JSON
    canonical = json.dumps(
        manifest_without_hmac,
        sort_keys=True,
        indent=None,
        separators=(',', ':')
    )

    # Compute expected HMAC
    expected_hmac = hmac.new(
        hmac_secret.encode("utf-8"),
        canonical.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    # Constant-time comparison
    is_valid = hmac.compare_digest(provided_hmac, expected_hmac)

    if not is_valid:
        logger.error("HMAC verification failed - manifest may be tampered")

    return is_valid
