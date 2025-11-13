#!/usr/bin/env python3
"""
Generate synthetic policy analysis traffic for testing runtime validators.

This script creates realistic policy analysis requests to validate that runtime
validators see non-zero traffic in pre-production environments.

Usage:
    python tools/testing/generate_synthetic_traffic.py --volume 100
    python tools/testing/generate_synthetic_traffic.py --volume 100 --modalities TYPE_A,TYPE_B
    python tools/testing/generate_synthetic_traffic.py --volume 100 --output traffic.jsonl
"""

import argparse
import json
import random
import sys
from typing import Any

# Modality definitions and their evidence requirements
MODALITY_TEMPLATES = {
    "TYPE_A": {
        "elements_range": (1, 4),
        "confidence_range": (0.5, 1.0),
        "score_range": (0, 4),
    },
    "TYPE_B": {
        "elements_range": (1, 3),
        "completeness_range": (0.5, 1.0),
        "score_range": (0, 3),
    },
    "TYPE_C": {
        "elements_range": (1, 2),
        "coherence_range": (0.5, 1.0),
        "score_range": (0, 3),
    },
    "TYPE_D": {
        "elements_range": (1, 3),
        "pattern_matches_range": (0, 3),
        "score_range": (0, 3),
    },
    "TYPE_E": {
        "elements_range": (1, 3),
        "traceability_options": [True, False],
        "score_range": (0, 3),
    },
    "TYPE_F": {
        "elements_range": (1, 3),
        "plausibility_range": (0.5, 1.0),
        "score_range": (0, 3),
    },
}

POLICY_AREAS = ["PA01", "PA02", "PA03", "PA04", "PA05", "PA06", "PA07", "PA08", "PA09", "PA10"]
DIMENSIONS = ["DIM01", "DIM02", "DIM03", "DIM04", "DIM05", "DIM06"]

def generate_evidence(modality: str) -> dict[str, Any]:
    """Generate synthetic evidence for a modality."""
    template = MODALITY_TEMPLATES[modality]

    elements_count = random.randint(*template["elements_range"])
    elements = [f"Element {i+1} for {modality}" for i in range(elements_count)]

    evidence = {"elements": elements}

    if modality == "TYPE_A":
        evidence["confidence"] = random.uniform(*template["confidence_range"])
    elif modality == "TYPE_B":
        evidence["completeness"] = random.uniform(*template["completeness_range"])
    elif modality == "TYPE_C":
        evidence["coherence_score"] = random.uniform(*template["coherence_range"])
    elif modality == "TYPE_D":
        evidence["pattern_matches"] = random.randint(*template["pattern_matches_range"])
    elif modality == "TYPE_E":
        evidence["traceability"] = random.choice(template["traceability_options"])
    elif modality == "TYPE_F":
        evidence["plausibility"] = random.uniform(*template["plausibility_range"])

    return evidence

def generate_request(
    modalities: list[str],
    policy_areas: list[str],
    request_id: int
) -> dict[str, Any]:
    """Generate a synthetic policy analysis request."""
    modality = random.choice(modalities)
    policy_area = random.choice(policy_areas)
    dimension = random.choice(DIMENSIONS)

    # Generate question number (1-300)
    question_global = random.randint(1, 300)

    # Generate base slot
    question_local = random.randint(1, 30)
    base_slot = f"{policy_area}-{dimension}-Q{question_local:03d}"

    return {
        "request_id": f"synthetic-{request_id:06d}",
        "question_global": question_global,
        "base_slot": base_slot,
        "policy_area": policy_area,
        "dimension": dimension,
        "modality": modality,
        "evidence": generate_evidence(modality),
        "metadata": {
            "synthetic": True,
            "generator_version": "1.0.0",
        }
    }

def generate_traffic(
    volume: int,
    modalities: list[str],
    policy_areas: list[str],
    output_file: str = None
) -> list[dict[str, Any]]:
    """
    Generate synthetic traffic.

    Args:
        volume: Number of requests to generate
        modalities: List of modalities to use
        policy_areas: List of policy areas to use
        output_file: Optional output file (JSONL format)

    Returns:
        List of generated requests
    """
    requests = []

    for i in range(volume):
        request = generate_request(modalities, policy_areas, i + 1)
        requests.append(request)

        # Write to output file if specified
        if output_file:
            with open(output_file, 'a') as f:
                f.write(json.dumps(request) + '\n')

    return requests

def print_statistics(requests: list[dict[str, Any]]) -> None:
    """Print statistics about generated traffic."""
    print("\n" + "=" * 60)
    print("Synthetic Traffic Generation Summary")
    print("=" * 60)

    # Count by modality
    modality_counts = {}
    for req in requests:
        modality = req["modality"]
        modality_counts[modality] = modality_counts.get(modality, 0) + 1

    print("\nRequests by Modality:")
    for modality in sorted(modality_counts.keys()):
        count = modality_counts[modality]
        percentage = (count / len(requests)) * 100
        print(f"  {modality}: {count} ({percentage:.1f}%)")

    # Count by policy area
    policy_area_counts = {}
    for req in requests:
        policy_area = req["policy_area"]
        policy_area_counts[policy_area] = policy_area_counts.get(policy_area, 0) + 1

    print("\nRequests by Policy Area:")
    for policy_area in sorted(policy_area_counts.keys()):
        count = policy_area_counts[policy_area]
        percentage = (count / len(requests)) * 100
        print(f"  {policy_area}: {count} ({percentage:.1f}%)")

    # Check minimum sample size requirement (10 per modality per policy area)
    print("\nMinimum Sample Size Check (10 per modality per policy area):")
    violations = []
    for modality in MODALITY_TEMPLATES:
        for policy_area in POLICY_AREAS:
            count = sum(1 for r in requests
                       if r["modality"] == modality and r["policy_area"] == policy_area)
            if count > 0 and count < 10:
                violations.append(f"  {modality} x {policy_area}: {count} (needs ≥10)")

    if violations:
        print("  ⚠ Warning: Some combinations below minimum:")
        for v in violations[:5]:
            print(v)
        if len(violations) > 5:
            print(f"  ... and {len(violations) - 5} more")
    else:
        print("  ✓ All populated combinations meet minimum requirements")

    print("\nTotal requests generated: " + str(len(requests)))
    print("=" * 60 + "\n")

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate synthetic policy analysis traffic"
    )
    parser.add_argument(
        "--volume",
        type=int,
        default=100,
        help="Number of synthetic requests to generate (default: 100)"
    )
    parser.add_argument(
        "--modalities",
        type=str,
        default="TYPE_A,TYPE_B,TYPE_C,TYPE_D,TYPE_E,TYPE_F",
        help="Comma-separated list of modalities (default: all)"
    )
    parser.add_argument(
        "--policy-areas",
        type=str,
        default="PA01,PA02,PA03",
        help="Comma-separated list of policy areas (default: PA01,PA02,PA03)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file for requests (JSONL format)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Random seed for reproducibility"
    )

    args = parser.parse_args()

    # Parse modalities and policy areas
    modalities = [m.strip() for m in args.modalities.split(",")]
    policy_areas = [p.strip() for p in args.policy_areas.split(",")]

    # Validate modalities
    invalid_modalities = [m for m in modalities if m not in MODALITY_TEMPLATES]
    if invalid_modalities:
        print(f"Error: Invalid modalities: {invalid_modalities}", file=sys.stderr)
        print(f"Valid modalities: {list(MODALITY_TEMPLATES.keys())}", file=sys.stderr)
        return 1

    # Set random seed if provided
    if args.seed:
        random.seed(args.seed)

    # Clear output file if it exists
    if args.output:
        open(args.output, 'w').close()

    # Generate traffic
    print(f"Generating {args.volume} synthetic requests...")
    requests = generate_traffic(args.volume, modalities, policy_areas, args.output)

    # Print statistics
    print_statistics(requests)

    if args.output:
        print(f"✓ Output written to {args.output}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
