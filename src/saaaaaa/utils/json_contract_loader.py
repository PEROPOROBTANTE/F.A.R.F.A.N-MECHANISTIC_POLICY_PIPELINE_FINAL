"""Utility helpers to load and validate JSON contract documents."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

PathLike = Union[str, Path]

def _canonical_dump(payload: Mapping[str, object]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

@dataclass(frozen=True)
class ContractDocument:
    """Materialized JSON contract with checksum information."""

    path: Path
    payload: dict[str, object]
    checksum: str

@dataclass
class ContractLoadReport:
    """Result of attempting to load multiple contract documents."""

    documents: dict[str, ContractDocument]
    errors: list[str]

    @property
    def is_successful(self) -> bool:
        return not self.errors

    def summary(self) -> str:
        parts = [f"contracts={len(self.documents)}"]
        if self.errors:
            parts.append(f"errors={len(self.errors)}")
        return ", ".join(parts)

class JSONContractLoader:
    """Load JSON contract files and compute integrity metadata.

    ARCHITECTURAL BOUNDARY: This loader is for generic JSON contracts ONLY.
    It must NOT be used to load questionnaire_monolith.json directly.

    For questionnaire access, use:
    - factory.load_questionnaire() for canonical loading (returns CanonicalQuestionnaire)
    - QuestionnaireResourceProvider for pattern extraction
    """

    def __init__(self, base_path: Path | None = None) -> None:
        self.base_path = base_path or Path(__file__).resolve().parent

    def load(self, paths: Iterable[PathLike]) -> ContractLoadReport:
        documents: dict[str, ContractDocument] = {}
        errors: list[str] = []
        for raw in paths:
            path = self._resolve_path(raw)
            try:
                payload = self._read_payload(path)
            except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
                errors.append(f"{path}: {exc}")
                continue

            checksum = hashlib.sha256(_canonical_dump(payload).encode("utf-8")).hexdigest()
            documents[str(path)] = ContractDocument(path=path, payload=payload, checksum=checksum)
        return ContractLoadReport(documents=documents, errors=errors)

    def load_directory(self, relative_directory: PathLike, pattern: str = "*.json") -> ContractLoadReport:
        directory = self._resolve_path(relative_directory)
        if not directory.exists():
            return ContractLoadReport(documents={}, errors=[f"Directory not found: {directory}"])
        if not directory.is_dir():
            return ContractLoadReport(documents={}, errors=[f"Not a directory: {directory}"])

        paths = sorted(directory.glob(pattern))
        return self.load(paths)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _resolve_path(self, raw: PathLike) -> Path:
        path = Path(raw)
        if not path.is_absolute():
            path = self.base_path / path
        return path

    @staticmethod
    def _read_payload(path: Path) -> dict[str, object]:
        # ARCHITECTURAL GUARD: Block unauthorized questionnaire monolith access
        if path.name == "questionnaire_monolith.json":
            raise ValueError(
                "ARCHITECTURAL VIOLATION: questionnaire_monolith.json must ONLY be "
                "loaded via factory.load_questionnaire() which enforces hash verification. "
                "Use factory.load_questionnaire() for canonical loading."
            )

        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("Contract document must be a JSON object")
        return data

__all__ = [
    "ContractDocument",
    "ContractLoadReport",
    "JSONContractLoader",
]
