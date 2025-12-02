#!/usr/bin/env python3
"""
Generate canonical layer inventory JSON configuration.

This script generates config/canonic_inventorry_methods_layers.json
with layer assignments and Choquet weights for all executors.
"""

import json
import sys
from pathlib import Path

from farfan_pipeline.core.calibration.layer_assignment import (
    generate_canonical_inventory,
)

repo_root = Path(__file__).parent.parent


def main():
    executors_file = (
        repo_root / "src" / "farfan_pipeline" / "core" / "orchestrator" / "executors.py"
    )
    output_file = repo_root / "config" / "canonic_inventorry_methods_layers.json"

    if not executors_file.exists():
        print(f"ERROR: Executors file not found: {executors_file}")
        sys.exit(1)

    try:
        print(f"Identifying executors from {executors_file}...")
        inventory = generate_canonical_inventory(str(executors_file))

        print(f"Generated inventory with {len(inventory['methods'])} methods")

        for value in inventory["methods"].values():
            if any(
                key in str(value).lower() for key in ["score", "0.", "1.", "2.", "3."]
            ):
                if not isinstance(value, dict):
                    continue
                for k, v in value.items():
                    if k not in ["weights", "interaction_weights"] and isinstance(
                        v, int | float
                    ):
                        raise RuntimeError(
                            f"layer assignment corrupted: Found numeric score in JSON: {k}={v}"
                        )

        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(inventory, f, indent=2, ensure_ascii=False)

        print(f"✅ Successfully generated {output_file}")
        print(f"   Total executors: {inventory['_metadata']['total_executors']}")

    except RuntimeError as e:
        if "layer assignment corrupted" in str(e):
            print(f"❌ ABORT: {e}")
            sys.exit(1)
        raise
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
