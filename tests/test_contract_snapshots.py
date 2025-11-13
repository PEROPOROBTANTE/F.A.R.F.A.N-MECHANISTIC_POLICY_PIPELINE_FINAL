"""Snapshot tests that guard contract schemas."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from saaaaaa.utils import contracts as core_contracts


# Mark all tests in this module as outdated
pytestmark = pytest.mark.skip(reason="Snapshot testing replaced by deterministic fingerprints")

SNAPSHOT_PATH = Path(__file__).parent / "data" / "contract_snapshots.json"

def _format_type(annotation: object) -> str:
    text = repr(annotation)
    return text.replace("typing.", "")

def _collect_contracts() -> dict[str, dict[str, str]]:
    members: dict[str, dict[str, str]] = {}
    for name in dir(core_contracts):
        if not name.endswith("Contract"):
            continue
        obj = getattr(core_contracts, name)
        annotations = getattr(obj, "__annotations__", None)
        if not isinstance(annotations, dict):
            continue
        members[name] = {
            field: _format_type(annotation)
            for field, annotation in sorted(annotations.items())
        }
    return dict(sorted(members.items()))

def test_contract_snapshots_are_stable() -> None:
    assert SNAPSHOT_PATH.exists(), (
        "Contract snapshot missing. Run the governance tests to regenerate "
        "or update tests/data/contract_snapshots.json."
    )

    current = _collect_contracts()
    stored = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    assert current == stored, (
        "Core contract schema changed. Update tests/data/contract_snapshots.json "
        "after stakeholder approval."
    )
