#!/usr/bin/env python3
"""
Calibrate All 30 Executors (D1Q1-D6Q5) with 8-Layer System

This script generates proper 8-layer calibrations for all 30 question executors,
ensuring 100% compliance with the calibration system specification.

Per canonic_calibration_methods.md Definition 4.2:
  L_*(SCORE_Q) = {@b, @chain, @q, @d, @p, @C, @u, @m}  # 8 layers ALWAYS
"""

import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Repository root
REPO_ROOT = Path(__file__).parent.parent
INTRINSIC_CAL_FILE = REPO_ROOT / "config" / "intrinsic_calibration.json"
FUSION_SPEC_FILE = REPO_ROOT / "config" / "fusion_specification.json"
OUTPUT_DIR = REPO_ROOT / "config" / "layer_calibrations" / "SCORE_Q"

# All 30 executors
DIMENSIONS = ["D1", "D2", "D3", "D4", "D5", "D6"]
QUESTIONS = ["Q1", "Q2", "Q3", "Q4", "Q5"]

# 8-layer configuration for SCORE_Q role per canonical spec
REQUIRED_LAYERS = ["@b", "@u", "@q", "@d", "@p", "@C", "@chain", "@m"]


def load_fusion_weights() -> dict:
    """Load official Choquet fusion weights for SCORE_Q role."""
    with open(FUSION_SPEC_FILE) as f:
        fusion_spec = json.load(f)

    return fusion_spec["role_fusion_parameters"]["SCORE_Q"]


def generate_executor_calibration(executor_id: str, dimension: str, question: str) -> dict:
    """Generate 8-layer calibration for an executor.

    Args:
        executor_id: Executor ID (e.g., "D1Q1")
        dimension: Dimension ID (e.g., "D1")
        question: Question ID (e.g., "Q1")

    Returns:
        Calibration dictionary with all 8 layers
    """
    # Placeholder layer scores - in production these would be computed
    # via the proper CalibrationOrchestrator process
    #
    # For now, using conservative estimates based on executor role
    # TODO: Replace with actual computed scores

    layer_scores = {
        "@b": {
            "value": 0.75,  # Base intrinsic quality (executor-specific)
            "components": {
                "b_theory": 0.80,  # Well-defined analytical task
                "b_impl": 0.70,    # Executor implementation quality
                "b_deploy": 0.75   # Production deployment readiness
            },
            "note": "Placeholder - compute via BaseLayerEvaluator"
        },
        "@u": {
            "value": 0.85,  # Unit (PDT) quality
            "components": {
                "pdt_coverage": 0.90,  # PDT element coverage
                "pdt_quality": 0.80     # PDT structural quality
            },
            "note": "Placeholder - compute via UnitLayerEvaluator"
        },
        "@q": {
            "value": 0.90,  # Question compatibility
            "note": "Placeholder - compute via ContextualLayerEvaluator"
        },
        "@d": {
            "value": 0.85,  # Dimension compatibility
            "note": "Placeholder - compute via ContextualLayerEvaluator"
        },
        "@p": {
            "value": 0.80,  # Policy compatibility
            "note": "Placeholder - compute via ContextualLayerEvaluator"
        },
        "@C": {
            "value": 0.75,  # Congruence with ensemble
            "note": "Placeholder - compute via CongruenceLayerEvaluator"
        },
        "@chain": {
            "value": 1.0,   # Chain compatibility (executors typically clean)
            "note": "Placeholder - compute via ChainLayerEvaluator"
        },
        "@m": {
            "value": 0.70,  # Meta (governance/observability)
            "components": {
                "m_transp": 0.75,  # Transparency
                "m_gov": 0.65,     # Governance
                "m_cost": 0.70     # Computational cost
            },
            "note": "Placeholder - compute via MetaLayerEvaluator"
        }
    }

    # Load fusion weights
    fusion_params = load_fusion_weights()

    # Compute Choquet 2-additive fusion
    # Formula: Cal = Σ(a_ℓ × x_ℓ) + Σ(a_ℓk × min(x_ℓ, x_k))

    linear_weights = fusion_params["linear_weights"]
    interaction_weights = fusion_params["interaction_weights"]

    # Linear term
    linear_term = sum(
        linear_weights[layer] * layer_scores[layer]["value"]
        for layer in REQUIRED_LAYERS
    )

    # Interaction term
    interaction_term = 0.0
    for pair_str, weight in interaction_weights.items():
        # Parse "(@ b, @u)" -> ["@b", "@u"]
        pair = pair_str.strip('()').replace(' ', '').split(',')
        layer1, layer2 = pair[0], pair[1]
        interaction_term += weight * min(
            layer_scores[layer1]["value"],
            layer_scores[layer2]["value"]
        )

    final_score = linear_term + interaction_term

    return {
        "_metadata": {
            "executor_id": executor_id,
            "dimension": dimension,
            "question": question,
            "generated": "2025-11-19",
            "status": "PLACEHOLDER",
            "warning": "These are placeholder scores. Must be replaced with actual computed values via CalibrationOrchestrator."
        },
        "role": "SCORE_Q",
        "canonical_name": f"src.saaaaaa.core.orchestrator.executors.{executor_id}_Executor.execute",
        "required_layers": REQUIRED_LAYERS,
        "layer_scores": layer_scores,
        "fusion_parameters": fusion_params,
        "fusion_computation": {
            "linear_term": linear_term,
            "interaction_term": interaction_term
        },
        "final_calibration": {
            "final_score": final_score,
            "interpretation": f"Executor {executor_id} calibration score (8-layer Choquet fusion)"
        },
        "notes": [
            "All 8 layers present per Definition 4.2 (SCORE_Q role)",
            "Choquet 2-additive fusion per Definition 5.1",
            "PLACEHOLDER scores - must be computed via proper calibration process",
            "In production: use CalibrationOrchestrator.calibrate()"
        ]
    }


def update_intrinsic_calibration_json():
    """Update intrinsic_calibration.json with 8-layer executor calibrations."""
    logger.info(f"Loading {INTRINSIC_CAL_FILE}")

    with open(INTRINSIC_CAL_FILE) as f:
        cal_data = json.load(f)

    methods = cal_data.get("methods", {})
    updated_count = 0

    for dimension in DIMENSIONS:
        for question in QUESTIONS:
            executor_id = f"{dimension}{question}"
            method_key = f"src.saaaaaa.core.orchestrator.executors.{executor_id}_Executor.execute"

            if method_key not in methods:
                logger.warning(f"Method {method_key} not found in catalog! Skipping.")
                continue

            # Generate calibration
            calibration = generate_executor_calibration(executor_id, dimension, question)

            # Update method entry
            methods[method_key]["layer_scores"] = calibration["layer_scores"]
            methods[method_key]["role"] = "SCORE_Q"
            methods[method_key]["status"] = "placeholder_computed"
            methods[method_key]["final_score"] = calibration["final_calibration"]["final_score"]
            methods[method_key]["_note"] = "PLACEHOLDER calibration - replace with actual computed values"

            updated_count += 1
            logger.info(f"✓ Updated {executor_id}: {calibration['final_calibration']['final_score']:.4f}")

    # Write back
    logger.info(f"\nWriting updated calibration data to {INTRINSIC_CAL_FILE}")
    with open(INTRINSIC_CAL_FILE, 'w') as f:
        json.dump(cal_data, f, indent=2)

    logger.info(f"✓ Updated {updated_count} executors")

    return updated_count


def generate_individual_layer_calibration_files():
    """Generate individual layer calibration files in config/layer_calibrations/SCORE_Q/."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"\nGenerating individual calibration files in {OUTPUT_DIR}")

    for dimension in DIMENSIONS:
        for question in QUESTIONS:
            executor_id = f"{dimension}{question}"
            calibration = generate_executor_calibration(executor_id, dimension, question)

            output_file = OUTPUT_DIR / f"{executor_id.lower()}_execute.json"
            with open(output_file, 'w') as f:
                json.dump(calibration, f, indent=2)

            logger.info(f"✓ Created {output_file.name}")

    logger.info(f"✓ Generated 30 individual calibration files")


def main():
    """Main execution."""
    logger.info("=" * 70)
    logger.info("CALIBRATING ALL 30 EXECUTORS (D1Q1-D6Q5)")
    logger.info("=" * 70)
    logger.info("")
    logger.info("Role: SCORE_Q")
    logger.info(f"Required layers: {', '.join(REQUIRED_LAYERS)}")
    logger.info(f"Total layers per executor: {len(REQUIRED_LAYERS)}")
    logger.info("")

    # Step 1: Update intrinsic_calibration.json
    updated_count = update_intrinsic_calibration_json()

    # Step 2: Generate individual layer calibration files
    generate_individual_layer_calibration_files()

    logger.info("")
    logger.info("=" * 70)
    logger.info("✅ ALL 30 EXECUTORS CALIBRATED")
    logger.info("=" * 70)
    logger.info("")
    logger.info(f"Total executors updated: {updated_count}")
    logger.info("Configuration files:")
    logger.info(f"  - Updated: {INTRINSIC_CAL_FILE}")
    logger.info(f"  - Created: {OUTPUT_DIR}/*.json (30 files)")
    logger.info("")
    logger.info("⚠️  WARNING: These are PLACEHOLDER scores!")
    logger.info("In production, replace with actual computed calibrations via:")
    logger.info("  CalibrationOrchestrator.calibrate(subject)")
    logger.info("")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
