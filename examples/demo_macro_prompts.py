#!/usr/bin/env python3
# demo_macro_prompts.py
# coding=utf-8
"""
Demonstration of the 5 Macro-Level Analysis Prompts

This script shows how to use each of the 5 prompt macros independently
and through the unified orchestrator.
"""

import json

# Verify package is available
try:
    import saaaaaa
except ImportError as e:
    print("❌ ERROR: Cannot import saaaaaa package")
    print(f"   {e}")
    print("\n📦 Please install the package first:")
    print("   pip install -e .")
    print("\nOr set PYTHONPATH:")
    print("   export PYTHONPATH=/path/to/SAAAAAA/src")
    exit(1)

from saaaaaa.processing.macro_prompts import (
    BayesianPortfolioComposer,
    ContradictionScanner,
    CoverageGapStressor,
    MacroPromptsOrchestrator,
    PeerNormalizer,
    RoadmapOptimizer,
)

def demo_coverage_gap_stressor():
    """Demo: Coverage & Structural Gap Stressor"""
    print("=" * 60)
    print("DEMO 1: Coverage & Structural Gap Stressor")
    print("=" * 60)

    stressor = CoverageGapStressor(
        critical_dimensions=["D3", "D6"],
        coverage_threshold=0.70
    )

    result = stressor.evaluate(
        convergence_by_dimension={
            "D1": 0.85, "D2": 0.80, "D3": 0.65,  # D3 below threshold
            "D4": 0.75, "D5": 0.70, "D6": 0.60   # D6 below threshold
        },
        missing_clusters=["CLUSTER_X", "CLUSTER_Y"],
        dimension_coverage={
            "D1": 0.95, "D2": 0.90, "D3": 0.65,
            "D4": 0.80, "D5": 0.75, "D6": 0.60
        },
        policy_area_coverage={
            "P1": 0.85, "P2": 0.80, "P3": 0.90,
            "P4": 0.75, "P5": 0.70
        },
        baseline_confidence=1.0
    )

    print(f"\n✓ Coverage Index: {result.coverage_index:.3f}")
    print(f"✓ Degraded Confidence: {result.degraded_confidence:.3f}")
    print(f"✓ Critical Gaps: {result.critical_dimensions_below_threshold}")
    print("✓ Predictive Uplift (sample):")
    for key, value in list(result.predictive_uplift.items())[:3]:
        print(f"  - {key}: {value:.3f}")
    print()

def demo_contradiction_scanner():
    """Demo: Inter-Level Contradiction Scan"""
    print("=" * 60)
    print("DEMO 2: Inter-Level Contradiction Scanner")
    print("=" * 60)

    scanner = ContradictionScanner(
        contradiction_threshold=3,
        posterior_threshold=0.7
    )

    # Simulated contradictory data: low micro scores vs high macro
    micro_claims = [
        {"dimension": "D1", "score": 0.3, "posterior": 0.85},
        {"dimension": "D1", "score": 0.25, "posterior": 0.80},
        {"dimension": "D1", "score": 0.35, "posterior": 0.90},
        {"dimension": "D1", "score": 0.28, "posterior": 0.75},
        {"dimension": "D2", "score": 0.8, "posterior": 0.85}
    ]

    meso_signals = {
        "D1": {"score": 0.4},
        "D2": {"score": 0.75}
    }

    macro_narratives = {
        "D1": {"score": 0.8},  # High macro contradicts low micro
        "D2": {"score": 0.78}
    }

    result = scanner.scan(micro_claims, meso_signals, macro_narratives)

    print(f"\n✓ Consistency Score: {result.consistency_score:.3f}")
    print(f"✓ Contradictions Found: {len(result.contradictions)}")
    print(f"✓ Suggested Actions: {len(result.suggested_actions)}")

    if result.contradictions:
        print("\n  First Contradiction:")
        contradiction = result.contradictions[0]
        print(f"    - Dimension: {contradiction.get('dimension')}")
        print(f"    - Type: {contradiction.get('type')}")
        print(f"    - Claims: {contradiction.get('contradicting_claims')}")

    if result.suggested_actions:
        print("\n  First Action:")
        action = result.suggested_actions[0]
        print(f"    - Dimension: {action.get('dimension')}")
        print(f"    - Action: {action.get('action')}")
        print(f"    - Reason: {action.get('reason')}")
    print()

def demo_bayesian_portfolio():
    """Demo: Bayesian Portfolio Composer"""
    print("=" * 60)
    print("DEMO 3: Bayesian Portfolio Composer")
    print("=" * 60)

    composer = BayesianPortfolioComposer(default_variance=0.05)

    result = composer.compose(
        meso_posteriors={
            "CL01": 0.85,
            "CL02": 0.78,
            "CL03": 0.82,
            "CL04": 0.75
        },
        cluster_weights={
            "CL01": 0.3,
            "CL02": 0.3,
            "CL03": 0.25,
            "CL04": 0.15
        },
        reconciliation_penalties={
            "coverage": 0.08,
            "dispersion": 0.05,
            "contradictions": 0.03
        }
    )

    print(f"\n✓ Prior Global: {result.prior_global:.3f}")
    print(f"✓ Posterior Global: {result.posterior_global:.3f}")
    print(f"✓ Variance: {result.var_global:.4f}")
    print(f"✓ 95% CI: [{result.confidence_interval[0]:.3f}, {result.confidence_interval[1]:.3f}]")
    print("✓ Penalties Applied:")
    for penalty_name, penalty_value in result.penalties_applied.items():
        print(f"  - {penalty_name}: {penalty_value:.3f}")
    print()

def demo_roadmap_optimizer():
    """Demo: Roadmap Optimizer"""
    print("=" * 60)
    print("DEMO 4: Roadmap Optimizer")
    print("=" * 60)

    optimizer = RoadmapOptimizer()

    critical_gaps = [
        {"id": "GAP_1", "name": "Establish baseline data"},
        {"id": "GAP_2", "name": "Build causal model"},
        {"id": "GAP_3", "name": "Implement tracking system"},
        {"id": "GAP_4", "name": "Train team on methodology"},
        {"id": "GAP_5", "name": "Validate with pilot"}
    ]

    dependency_graph = {
        "GAP_1": [],
        "GAP_2": ["GAP_1"],
        "GAP_3": ["GAP_1", "GAP_4"],
        "GAP_4": [],
        "GAP_5": ["GAP_2", "GAP_3"]
    }

    effort_estimates = {
        "GAP_1": 3.0,
        "GAP_2": 5.0,
        "GAP_3": 4.0,
        "GAP_4": 2.0,
        "GAP_5": 2.0
    }

    impact_scores = {
        "GAP_1": 0.95,
        "GAP_2": 0.90,
        "GAP_3": 0.85,
        "GAP_4": 0.80,
        "GAP_5": 0.75
    }

    result = optimizer.optimize(
        critical_gaps,
        dependency_graph,
        effort_estimates,
        impact_scores
    )

    print(f"\n✓ Total Expected Uplift: {result.total_expected_uplift:.3f}")
    print(f"✓ Critical Path: {' → '.join(result.critical_path)}")
    print("\n✓ Roadmap Phases:")

    for phase in result.phases:
        print(f"\n  {phase['name']}:")
        print(f"    Effort: {phase['effort']:.1f}/{phase['max_effort']:.1f} person-months")
        print("    Actions:")
        for action in phase['actions']:
            print(f"      - {action['name']} (impact: {action['impact']:.2f})")

    print("\n✓ Resource Requirements:")
    for phase_name, resources in result.resource_requirements.items():
        print(f"  {phase_name}:")
        print(f"    - Team Size: {resources['recommended_team_size']} people")
        print(f"    - Total Effort: {resources['total_effort_months']:.1f} person-months")
    print()

def demo_peer_normalizer():
    """Demo: Peer Normalization & Confidence Scaling"""
    print("=" * 60)
    print("DEMO 5: Peer Normalization & Confidence Scaling")
    print("=" * 60)

    normalizer = PeerNormalizer(
        penalty_threshold=3,
        outlier_z_threshold=2.0
    )

    result = normalizer.normalize(
        convergence_by_policy_area={
            "P1": 0.85,  # Above average
            "P2": 0.92,  # High outlier
            "P3": 0.74,  # Average
            "P4": 0.40,  # Below average
            "P5": 0.76   # Average
        },
        peer_distributions={
            "P1": {"mean": 0.75, "std": 0.08},
            "P2": {"mean": 0.75, "std": 0.08},
            "P3": {"mean": 0.75, "std": 0.08},
            "P4": {"mean": 0.75, "std": 0.08},
            "P5": {"mean": 0.75, "std": 0.08}
        },
        baseline_confidence=0.85
    )

    print(f"\n✓ Peer Position: {result.peer_position}")
    print(f"✓ Adjusted Confidence: {result.adjusted_confidence:.3f}")
    print(f"✓ Outlier Areas: {result.outlier_areas}")
    print("\n✓ Z-Scores by Policy Area:")
    for area, z_score in result.z_scores.items():
        status = "🔺" if z_score > 1.0 else "🔻" if z_score < -1.0 else "✓"
        print(f"  {status} {area}: {z_score:+.2f}")
    print()

def demo_orchestrator():
    """Demo: Unified Orchestrator (all 5 prompts)"""
    print("=" * 60)
    print("DEMO 6: Unified MacroPromptsOrchestrator")
    print("=" * 60)

    orchestrator = MacroPromptsOrchestrator()

    macro_data = {
        "convergence_by_dimension": {
            "D1": 0.85, "D2": 0.80, "D3": 0.75,
            "D4": 0.70, "D5": 0.68, "D6": 0.72
        },
        "convergence_by_policy_area": {
            "P1": 0.80, "P2": 0.75, "P3": 0.85
        },
        "missing_clusters": ["CLUSTER_X"],
        "dimension_coverage": {
            "D1": 0.90, "D2": 0.85, "D3": 0.80,
            "D4": 0.75, "D5": 0.72, "D6": 0.78
        },
        "policy_area_coverage": {
            "P1": 0.85, "P2": 0.80, "P3": 0.90
        },
        "micro_claims": [
            {"dimension": "D1", "score": 0.8, "posterior": 0.85},
            {"dimension": "D2", "score": 0.75, "posterior": 0.80}
        ],
        "meso_summary_signals": {
            "D1": {"score": 0.78},
            "D2": {"score": 0.74}
        },
        "macro_narratives": {
            "D1": {"score": 0.79},
            "D2": {"score": 0.76}
        },
        "meso_posteriors": {
            "CL01": 0.80,
            "CL02": 0.75
        },
        "cluster_weights": {
            "CL01": 0.6,
            "CL02": 0.4
        },
        "critical_gaps": [
            {"id": "GAP_1", "name": "Gap 1"},
            {"id": "GAP_2", "name": "Gap 2"}
        ],
        "dependency_graph": {
            "GAP_1": [],
            "GAP_2": ["GAP_1"]
        },
        "effort_estimates": {
            "GAP_1": 2.0,
            "GAP_2": 3.0
        },
        "impact_scores": {
            "GAP_1": 0.9,
            "GAP_2": 0.8
        },
        "peer_distributions": {
            "P1": {"mean": 0.75, "std": 0.1},
            "P2": {"mean": 0.75, "std": 0.1},
            "P3": {"mean": 0.75, "std": 0.1}
        },
        "baseline_confidence": 0.85
    }

    results = orchestrator.execute_all(macro_data)

    print("\n✓ All 5 macro analyses completed successfully!")
    print("\n  Analysis Results:")
    print(f"    1. Coverage Index: {results['coverage_analysis']['coverage_index']:.3f}")
    print(f"    2. Consistency Score: {results['contradiction_report']['consistency_score']:.3f}")
    print(f"    3. Posterior Global: {results['bayesian_portfolio']['posterior_global']:.3f}")
    print(f"    4. Total Uplift: {results['implementation_roadmap']['total_expected_uplift']:.3f}")
    print(f"    5. Adjusted Confidence: {results['peer_normalization']['adjusted_confidence']:.3f}")

    print("\n  JSON Export (sample - coverage_analysis):")
    print(json.dumps(results['coverage_analysis'], indent=2)[:500] + "...")
    print()

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("MACRO PROMPTS DEMONSTRATION")
    print("5 Strategic Macro-Level Analysis Prompts")
    print("=" * 60 + "\n")

    demo_coverage_gap_stressor()
    demo_contradiction_scanner()
    demo_bayesian_portfolio()
    demo_roadmap_optimizer()
    demo_peer_normalizer()
    demo_orchestrator()

    print("=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)
    print("\nFor more information, see MACRO_PROMPTS_README.md")
    print()
