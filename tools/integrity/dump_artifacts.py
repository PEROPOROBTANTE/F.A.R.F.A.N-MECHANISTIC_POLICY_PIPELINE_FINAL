#!/usr/bin/env python3
"""Generate deterministic artifact snapshots for CI regression checks."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from saaaaaa.core.seed_factory import DeterministicContext  # noqa: E402

REPO_ROOT = Path(__file__).parent.parent.parent
CHECKSUM_PATH = REPO_ROOT / "config" / "metadata_checksums.json"

def load_checksums() -> dict[str, str]:
    with CHECKSUM_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)

def generate_payload(seed: int, checksums: dict[str, str]) -> dict[str, Any]:
    rng = random.Random(seed)  # noqa: S311 – non-crypto, deterministic CI snapshot
    random_values = [rng.random() for _ in range(5)]
    return {
        "seed": seed,
        "checksums": checksums,
        "random_probe": random_values,
    }

def main(output_dir: Path) -> None:
    checksums = load_checksums()

    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / "deterministic_snapshot.json"

    with DeterministicContext(
        "ci-artifacts", file_checksums=checksums, context={"variant": "baseline"}
    ) as seed:
        payload = generate_payload(seed, checksums)

    with target.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Directory where artifacts will be written")
    args = parser.parse_args()

    main(args.output)
