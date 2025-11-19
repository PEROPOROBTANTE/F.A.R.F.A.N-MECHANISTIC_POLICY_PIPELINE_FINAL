"""Append-only evidence registry with cryptographic hashing.

This module implements a small ledger that stores evidence entries produced by
analysis components. Each entry links to the previous one through a SHA-256
hash, producing an immutable chain that can be verified for tampering.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterable

def _canonical_json(payload: dict[str, Any]) -> str:
    """Return a canonical JSON representation with sorted keys."""
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

@dataclass(frozen=True)
class EvidenceRecord:
    """Single append-only evidence entry."""

    index: int
    timestamp: str
    method_name: str
    evidence: list[str]
    metadata: dict[str, Any]
    previous_hash: str
    entry_hash: str

    @staticmethod
    def create(
        index: int,
        method_name: str,
        evidence: Iterable[str],
        metadata: dict[str, Any] | None,
        previous_hash: str,
        timestamp: datetime | None = None,
    ) -> EvidenceRecord:
        """Build a new evidence record and compute its hash."""
        ts = (timestamp or datetime.utcnow()).isoformat() + "Z"
        metadata_dict = dict(metadata or {})
        evidence_list = list(evidence)

        payload = {
            "index": index,
            "timestamp": ts,
            "method_name": method_name,
            "evidence": evidence_list,
            "metadata": metadata_dict,
            "previous_hash": previous_hash,
        }
        digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
        return EvidenceRecord(
            index=index,
            timestamp=ts,
            method_name=method_name,
            evidence=evidence_list,
            metadata=metadata_dict,
            previous_hash=previous_hash,
            entry_hash=digest,
        )

class EvidenceRegistry:
    """Append-only registry that persists evidence records to disk."""

    def __init__(self, storage_path: Path | None = None, auto_load: bool = True) -> None:
        self.storage_path = storage_path or Path(".evidence_registry.json")
        self._records: list[EvidenceRecord] = []
        if auto_load and self.storage_path.exists():
            self._records = self._load_records(self.storage_path)

    @property
    def records(self) -> tuple[EvidenceRecord, ...]:
        """Expose records as an immutable tuple."""
        return tuple(self._records)

    def append(
        self,
        method_name: str,
        evidence: Iterable[str],
        metadata: dict[str, Any] | None = None,
        monolith_hash: str | None = None,
    ) -> EvidenceRecord:
        """Append a new evidence record to the registry.

        Args:
            method_name: Name of the method producing evidence
            evidence: Evidence strings
            metadata: Additional metadata dictionary
            monolith_hash: SHA-256 hash of questionnaire_monolith.json (recommended)

        ARCHITECTURAL NOTE: Including monolith_hash ensures evidence is
        traceable to the specific questionnaire version that generated it.
        Use factory.compute_monolith_hash() to generate this value.
        """
        previous_hash = self._records[-1].entry_hash if self._records else "GENESIS"

        # Merge monolith_hash into metadata if provided
        enriched_metadata = dict(metadata or {})
        if monolith_hash is not None:
            enriched_metadata['monolith_hash'] = monolith_hash

        record = EvidenceRecord.create(
            index=len(self._records),
            method_name=method_name,
            evidence=evidence,
            metadata=enriched_metadata,
            previous_hash=previous_hash,
        )
        self._records.append(record)
        return record

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def save(self) -> None:
        """Persist the registry to disk."""
        payload = [_serialize_record(record) for record in self._records]
        self.storage_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _load_records(self, path: Path) -> list[EvidenceRecord]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Evidence registry at {path} is not valid JSON: {exc}") from exc

        if not isinstance(data, list):
            raise ValueError("Evidence registry payload must be a list")

        records: list[EvidenceRecord] = []
        for index, raw in enumerate(data):
            if not isinstance(raw, dict):
                raise ValueError("Evidence record must be a JSON object")
            expected_index = raw.get("index")
            if expected_index != index:
                raise ValueError(
                    f"Evidence record index mismatch at position {index}: found {expected_index}"
                )
            record = EvidenceRecord(
                index=index,
                timestamp=str(raw.get("timestamp")),
                method_name=str(raw.get("method_name")),
                evidence=list(raw.get("evidence", [])),
                metadata=dict(raw.get("metadata", {})),
                previous_hash=str(raw.get("previous_hash")),
                entry_hash=str(raw.get("entry_hash")),
            )
            records.append(record)

        self._assert_chain(records)
        return records

    # ------------------------------------------------------------------
    # Verification utilities
    # ------------------------------------------------------------------
    def verify(self) -> bool:
        """Verify registry integrity by recomputing all hashes."""
        self._assert_chain(self._records)
        return True

    @staticmethod
    def _assert_chain(records: list[EvidenceRecord]) -> None:
        previous_hash = "GENESIS"
        for expected_index, record in enumerate(records):
            if record.index != expected_index:
                raise ValueError(
                    f"Evidence record out of order: expected index {expected_index}, got {record.index}"
                )
            payload = {
                "index": record.index,
                "timestamp": record.timestamp,
                "method_name": record.method_name,
                "evidence": record.evidence,
                "metadata": record.metadata,
                "previous_hash": previous_hash,
            }
            computed = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
            if computed != record.entry_hash:
                raise ValueError(
                    "Evidence record hash mismatch at index "
                    f"{record.index}: expected {computed}, found {record.entry_hash}"
                )
            previous_hash = record.entry_hash

def _serialize_record(record: EvidenceRecord) -> dict[str, Any]:
    payload = asdict(record)
    payload["evidence"] = list(record.evidence)
    payload["metadata"] = dict(record.metadata)
    return payload

__all__ = [
    "EvidenceRecord",
    "EvidenceRegistry",
]
