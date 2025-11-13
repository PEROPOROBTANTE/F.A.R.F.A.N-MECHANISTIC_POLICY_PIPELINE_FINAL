#!/usr/bin/env python3
"""
Demo script for the scoring module.

Shows how to use TYPE_A through TYPE_F scoring modalities.

REQUIREMENTS:
    Install the package first: pip install -e .
    Or set PYTHONPATH: export PYTHONPATH=/path/to/SAAAAAA/src
"""

from pathlib import Path

# Verify package is available
try:
    from saaaaaa.analysis.scoring.scoring import apply_scoring
except ImportError as e:
    print("❌ ERROR: Cannot import saaaaaa package")
    print(f"   {e}")
    print("\n📦 Please install the package first:")
    print("   pip install -e .")
    print("\nOr set PYTHONPATH:")
    print("   export PYTHONPATH=/path/to/SAAAAAA/src")
    exit(1)

print("✓ Package imported successfully\n")

def demo_type_a():
    """Demonstrate TYPE_A (Bayesian) scoring."""
    print("\n=== TYPE_A: Bayesian Numerical Claims ===")

    evidence = {
        "elements": [
            "Baseline gap: 15% unemployment",
            "Risk: inflation at 8%",
            "Target: reduce gap by 30%",
            "Constraint: budget limited to $2M"
        ],
        "confidence": 0.85
    }

    result = apply_scoring(
        question_global=1,
        base_slot="PA01-DIM01-Q001",
        policy_area="PA01",
        dimension="DIM01",
        evidence=evidence,
        modality="TYPE_A"
    )

    print(f"Score: {result.score:.2f} / 4.0")
    print(f"Normalized: {result.normalized_score:.2f}")
    print(f"Quality: {result.quality_level}")
    print(f"Evidence Hash: {result.evidence_hash[:16]}...")

def demo_type_b():
    """Demonstrate TYPE_B (DAG) scoring."""
    print("\n=== TYPE_B: DAG Causal Chains ===")

    evidence = {
        "elements": [
            "Input: Training programs → Activity: Skill development",
            "Activity: Skill development → Output: Certified workers",
            "Output: Certified workers → Outcome: Employment increase"
        ],
        "completeness": 0.92
    }

    result = apply_scoring(
        question_global=2,
        base_slot="PA01-DIM06-Q001",
        policy_area="PA01",
        dimension="DIM06",
        evidence=evidence,
        modality="TYPE_B"
    )

    print(f"Score: {result.score:.2f} / 3.0")
    print(f"Normalized: {result.normalized_score:.2f}")
    print(f"Quality: {result.quality_level}")

def demo_type_c():
    """Demonstrate TYPE_C (Coherence) scoring."""
    print("\n=== TYPE_C: Coherence Analysis ===")

    evidence = {
        "elements": [
            "Policy states budget of $5M",
            "Annex confirms $5M allocation"
        ],
        "coherence_score": 0.95
    }

    result = apply_scoring(
        question_global=3,
        base_slot="PA02-DIM02-Q001",
        policy_area="PA02",
        dimension="DIM02",
        evidence=evidence,
        modality="TYPE_C"
    )

    print(f"Score: {result.score:.2f} / 3.0")
    print(f"Normalized: {result.normalized_score:.2f}")
    print(f"Quality: {result.quality_level}")

def demo_type_d():
    """Demonstrate TYPE_D (Pattern) scoring."""
    print("\n=== TYPE_D: Pattern Matching ===")

    evidence = {
        "elements": [
            "Baseline: unemployment at 12% (matched)",
            "Target: reduce to 8% in 3 years (matched)",
            "Gap quantified as 4 percentage points"
        ],
        "pattern_matches": 2
    }

    result = apply_scoring(
        question_global=4,
        base_slot="PA03-DIM01-Q001",
        policy_area="PA03",
        dimension="DIM01",
        evidence=evidence,
        modality="TYPE_D"
    )

    print(f"Score: {result.score:.2f} / 3.0")
    print(f"Normalized: {result.normalized_score:.2f}")
    print(f"Quality: {result.quality_level}")

def demo_type_e():
    """Demonstrate TYPE_E (Financial) scoring."""
    print("\n=== TYPE_E: Budget Traceability ===")

    evidence = {
        "elements": [
            "Budget line item: Training - $1.2M",
            "Budget line item: Equipment - $800K"
        ],
        "traceability": True
    }

    result = apply_scoring(
        question_global=5,
        base_slot="PA04-DIM03-Q001",
        policy_area="PA04",
        dimension="DIM03",
        evidence=evidence,
        modality="TYPE_E"
    )

    print(f"Score: {result.score:.2f} / 3.0")
    print(f"Normalized: {result.normalized_score:.2f}")
    print(f"Quality: {result.quality_level}")

def demo_type_f():
    """Demonstrate TYPE_F (Beach) scoring."""
    print("\n=== TYPE_F: Mechanism Inference ===")

    evidence = {
        "elements": [
            "Mechanism: Training increases skills",
            "Mechanism: Skills increase employability"
        ],
        "plausibility": 0.88
    }

    result = apply_scoring(
        question_global=6,
        base_slot="PA05-DIM06-Q001",
        policy_area="PA05",
        dimension="DIM06",
        evidence=evidence,
        modality="TYPE_F"
    )

    print(f"Score: {result.score:.2f} / 3.0")
    print(f"Normalized: {result.normalized_score:.2f}")
    print(f"Quality: {result.quality_level}")

def demo_error_handling():
    """Demonstrate error handling."""
    print("\n=== Error Handling Demo ===")

    # Missing required key
    print("\n1. Missing required evidence key:")
    try:
        evidence = {"elements": [1, 2, 3]}  # Missing confidence
        apply_scoring(
            question_global=1,
            base_slot="PA01-DIM01-Q001",
            policy_area="PA01",
            dimension="DIM01",
            evidence=evidence,
            modality="TYPE_A"
        )
    except Exception as e:
        print(f"   ✗ Error caught: {type(e).__name__}: {e}")

    # Invalid modality
    print("\n2. Invalid modality:")
    try:
        evidence = {"elements": [1, 2, 3], "confidence": 0.9}
        apply_scoring(
            question_global=1,
            base_slot="PA01-DIM01-Q001",
            policy_area="PA01",
            dimension="DIM01",
            evidence=evidence,
            modality="TYPE_Z"  # Invalid
        )
    except Exception as e:
        print(f"   ✗ Error caught: {type(e).__name__}: {e}")

    # Invalid confidence value
    print("\n3. Invalid confidence value:")
    try:
        evidence = {"elements": [1, 2, 3], "confidence": 1.5}  # > 1.0
        apply_scoring(
            question_global=1,
            base_slot="PA01-DIM01-Q001",
            policy_area="PA01",
            dimension="DIM01",
            evidence=evidence,
            modality="TYPE_A"
        )
    except Exception as e:
        print(f"   ✗ Error caught: {type(e).__name__}: {e}")

def main():
    """Run all demos."""
    print("=" * 60)
    print("SCORING MODULE DEMO")
    print("=" * 60)

    demo_type_a()
    demo_type_b()
    demo_type_c()
    demo_type_d()
    demo_type_e()
    demo_type_f()
    demo_error_handling()

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
