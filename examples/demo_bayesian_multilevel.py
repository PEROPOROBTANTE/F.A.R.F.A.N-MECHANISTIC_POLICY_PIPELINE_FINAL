#!/usr/bin/env python3
"""
Demonstration of Bayesian Multi-Level Analysis System

This script demonstrates the complete multi-level Bayesian analysis pipeline:
- MICRO: Reconciliation validators + Bayesian updating
- MESO: Dispersion analysis + Peer calibration
- MACRO: Contradiction scanning + Portfolio composition
"""

from pathlib import Path

# Add parent to path if needed
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

from saaaaaa.analysis.bayesian_multilevel_system import (
    MultiLevelBayesianOrchestrator,
    PeerContext,
    ProbativeTest,
    ProbativeTestType,
    ValidationRule,
    ValidatorType,
)

def main():
    print("=" * 80)
    print("BAYESIAN MULTI-LEVEL ANALYSIS SYSTEM - DEMONSTRATION")
    print("=" * 80)
    print()

    # ========================================================================
    # SETUP: Define validation rules
    # ========================================================================
    print("[SETUP] Defining validation rules...")
    validation_rules = [
        ValidationRule(
            validator_type=ValidatorType.RANGE,
            field_name="score",
            expected_range=(0.0, 1.0),
            penalty_factor=0.15
        ),
        ValidationRule(
            validator_type=ValidatorType.UNIT,
            field_name="budget_unit",
            expected_unit="COP",
            penalty_factor=0.10
        ),
        ValidationRule(
            validator_type=ValidatorType.PERIOD,
            field_name="time_period",
            expected_period="2024-2027",
            penalty_factor=0.12
        ),
        ValidationRule(
            validator_type=ValidatorType.ENTITY,
            field_name="municipality",
            expected_entity="Example Municipality",
            penalty_factor=0.08
        )
    ]
    print(f"  ✓ Defined {len(validation_rules)} validation rules")
    print()

    # ========================================================================
    # MICRO DATA: Prepare sample question data
    # ========================================================================
    print("[MICRO DATA] Preparing sample questions...")

    # Define probative tests for evidence evaluation
    baseline_test = ProbativeTest(
        test_type=ProbativeTestType.HOOP_TEST,
        test_name="Baseline data existence",
        evidence_strength=0.6,
        prior_probability=0.5
    )

    budget_test = ProbativeTest(
        test_type=ProbativeTestType.SMOKING_GUN,
        test_name="Budget allocation documented",
        evidence_strength=0.9,
        prior_probability=0.5
    )

    causal_test = ProbativeTest(
        test_type=ProbativeTestType.DOUBLY_DECISIVE,
        test_name="Theory of Change validated",
        evidence_strength=1.0,
        prior_probability=0.5
    )

    # Sample micro-level data (300 questions in real scenario)
    micro_data = [
        # Policy Area 1 (PA01) - Dimension 1 (DIM01: Diagnóstico y Recursos)
        {
            'question_id': 'P1-D1-Q1',
            'raw_score': 0.75,
            'score': 0.75,
            'budget_unit': 'COP',
            'time_period': '2024-2027',
            'municipality': 'Example Municipality',
            'probative_tests': [
                (baseline_test, True),
                (budget_test, True)
            ]
        },
        {
            'question_id': 'P1-D1-Q2',
            'raw_score': 0.68,
            'score': 0.68,
            'budget_unit': 'COP',
            'time_period': '2024-2027',
            'municipality': 'Example Municipality',
            'probative_tests': [
                (baseline_test, True)
            ]
        },
        {
            'question_id': 'P1-D1-Q3',
            'raw_score': 0.82,
            'score': 0.82,
            'budget_unit': 'COP',
            'time_period': '2024-2027',
            'municipality': 'Example Municipality',
            'probative_tests': [
                (budget_test, True)
            ]
        },

        # Policy Area 1 (PA01) - Dimension 2 (DIM02: Diseño de Intervención)
        {
            'question_id': 'P1-D2-Q1',
            'raw_score': 0.71,
            'score': 0.71,
            'budget_unit': 'COP',
            'time_period': '2024-2027',
            'municipality': 'Example Municipality',
            'probative_tests': [
                (ProbativeTest(ProbativeTestType.HOOP_TEST, "Activity design", 0.6, 0.5), True)
            ]
        },
        {
            'question_id': 'P1-D2-Q2',
            'raw_score': 0.64,
            'score': 0.64,
            'budget_unit': 'COP',
            'time_period': '2024-2027',
            'municipality': 'Example Municipality',
            'probative_tests': []
        },

        # Policy Area 2 - Dimension 1
        {
            'question_id': 'P2-D1-Q1',
            'raw_score': 0.55,
            'score': 0.55,
            'budget_unit': 'COP',
            'time_period': '2024-2027',
            'municipality': 'Example Municipality',
            'probative_tests': [
                (baseline_test, False)  # Test failed
            ]
        },
        {
            'question_id': 'P2-D1-Q2',
            'raw_score': 0.58,
            'score': 0.58,
            'budget_unit': 'COP',
            'time_period': '2024-2027',
            'municipality': 'Example Municipality',
            'probative_tests': []
        },

        # Policy Area 3 - Dimension 6 (Teoría de Cambio)
        {
            'question_id': 'P3-D6-Q1',
            'raw_score': 0.88,
            'score': 0.88,
            'budget_unit': 'COP',
            'time_period': '2024-2027',
            'municipality': 'Example Municipality',
            'probative_tests': [
                (causal_test, True)
            ]
        },
        {
            'question_id': 'P3-D6-Q2',
            'raw_score': 0.85,
            'score': 0.85,
            'budget_unit': 'COP',
            'time_period': '2024-2027',
            'municipality': 'Example Municipality',
            'probative_tests': [
                (causal_test, True)
            ]
        },
    ]

    print(f"  ✓ Prepared {len(micro_data)} sample questions")
    print()

    # ========================================================================
    # CLUSTER MAPPING: Group questions into meso-level clusters
    # ========================================================================
    print("[CLUSTER MAPPING] Defining meso-level clusters...")
    cluster_mapping = {
        'D1_DIAGNOSTICO': ['P1-D1-Q1', 'P1-D1-Q2', 'P1-D1-Q3', 'P2-D1-Q1', 'P2-D1-Q2'],
        'D2_DISENO': ['P1-D2-Q1', 'P1-D2-Q2'],
        'D6_TEORIA_CAMBIO': ['P3-D6-Q1', 'P3-D6-Q2'],
    }

    for cluster_id, questions in cluster_mapping.items():
        print(f"  - {cluster_id}: {len(questions)} questions")
    print()

    # ========================================================================
    # PEER CONTEXTS: Define peer comparison data
    # ========================================================================
    print("[PEER CONTEXTS] Defining peer municipalities...")
    peer_contexts = [
        PeerContext(
            peer_id="peer_mun_1",
            peer_name="Bogotá",
            scores={
                'D1_DIAGNOSTICO': 0.72,
                'D2_DISENO': 0.68,
                'D6_TEORIA_CAMBIO': 0.85
            }
        ),
        PeerContext(
            peer_id="peer_mun_2",
            peer_name="Medellín",
            scores={
                'D1_DIAGNOSTICO': 0.75,
                'D2_DISENO': 0.70,
                'D6_TEORIA_CAMBIO': 0.88
            }
        ),
        PeerContext(
            peer_id="peer_mun_3",
            peer_name="Cali",
            scores={
                'D1_DIAGNOSTICO': 0.68,
                'D2_DISENO': 0.65,
                'D6_TEORIA_CAMBIO': 0.82
            }
        ),
    ]

    print(f"  ✓ Defined {len(peer_contexts)} peer municipalities for calibration")
    print()

    # ========================================================================
    # ORCHESTRATOR: Initialize and run analysis
    # ========================================================================
    print("[ORCHESTRATOR] Initializing Bayesian multi-level system...")
    output_dir = Path("data/bayesian_outputs")
    orchestrator = MultiLevelBayesianOrchestrator(
        validation_rules=validation_rules,
        output_dir=output_dir
    )
    print(f"  ✓ Outputs will be saved to: {output_dir}")
    print()

    # ========================================================================
    # RUN ANALYSIS
    # ========================================================================
    print("[ANALYSIS] Running complete multi-level Bayesian analysis...")
    print()

    micro_analyses, meso_analyses, macro_analysis = orchestrator.run_complete_analysis(
        micro_data=micro_data,
        cluster_mapping=cluster_mapping,
        peer_contexts=peer_contexts,
        total_questions=300  # Simulating 300 total questions
    )

    # ========================================================================
    # RESULTS: Display key findings
    # ========================================================================
    print("\n" + "=" * 80)
    print("ANALYSIS RESULTS")
    print("=" * 80)
    print()

    # Micro level summary
    print("[MICRO LEVEL] Question-by-question analysis:")
    print(f"  Total questions analyzed: {len(micro_analyses)}")
    avg_micro_score = sum(m.adjusted_score for m in micro_analyses) / len(micro_analyses)
    print(f"  Average adjusted score: {avg_micro_score:.4f}")

    # Show sample micro results
    print("\n  Sample results:")
    for micro in micro_analyses[:3]:
        print(f"    {micro.question_id}:")
        print(f"      Raw score: {micro.raw_score:.4f}")
        print(f"      Validation penalty: {micro.validation_penalty:.4f}")
        print(f"      Final posterior: {micro.final_posterior:.4f}")
        print(f"      Adjusted score: {micro.adjusted_score:.4f}")
    print()

    # Meso level summary
    print("[MESO LEVEL] Cluster analysis:")
    print(f"  Total clusters: {len(meso_analyses)}")

    for meso in meso_analyses:
        print(f"\n  {meso.cluster_id}:")
        print(f"    Questions in cluster: {len(meso.micro_scores)}")
        print(f"    Raw meso score: {meso.raw_meso_score:.4f}")
        print(f"    Dispersion penalty: {meso.dispersion_penalty:.4f}")
        print(f"    Peer penalty: {meso.peer_penalty:.4f}")
        print(f"    Adjusted score: {meso.adjusted_score:.4f}")

        # Dispersion metrics
        print("    Dispersion metrics:")
        print(f"      CV: {meso.dispersion_metrics.get('cv', 0):.4f}")
        print(f"      Max gap: {meso.dispersion_metrics.get('max_gap', 0):.4f}")
        print(f"      Gini: {meso.dispersion_metrics.get('gini', 0):.4f}")

        # Peer comparison
        if meso.peer_comparison:
            print("    Peer calibration:")
            print(f"      {meso.peer_comparison.narrative}")

    print()

    # Macro level summary
    print("[MACRO LEVEL] Portfolio-wide analysis:")
    print(f"  Overall raw posterior: {macro_analysis.overall_posterior:.4f}")
    print(f"  Coverage score: {macro_analysis.coverage_score:.4f}")
    print(f"  Coverage penalty: {macro_analysis.coverage_penalty:.4f}")
    print(f"  Dispersion penalty: {macro_analysis.dispersion_penalty:.4f}")
    print(f"  Contradictions detected: {macro_analysis.contradiction_count}")
    print(f"  Contradiction penalty: {macro_analysis.contradiction_penalty:.4f}")
    print(f"  Total penalty: {macro_analysis.total_penalty:.4f}")
    print(f"  FINAL ADJUSTED SCORE: {macro_analysis.adjusted_score:.4f}")

    print("\n  Strategic Recommendations:")
    for i, rec in enumerate(macro_analysis.recommendations, 1):
        print(f"    {i}. {rec}")

    print()

    # ========================================================================
    # OUTPUT FILES
    # ========================================================================
    print("[OUTPUT FILES] Generated CSV reports:")
    print(f"  ✓ {output_dir / 'posterior_table_micro.csv'}")
    print(f"  ✓ {output_dir / 'posterior_table_meso.csv'}")
    print(f"  ✓ {output_dir / 'posterior_table_macro.csv'}")
    print()

    print("=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)
    print()
    print("The Bayesian multi-level analysis system successfully:")
    print("  ✓ Validated data against range/unit/period/entity rules")
    print("  ✓ Applied Bayesian updating using probative test taxonomy")
    print("  ✓ Computed dispersion metrics (CV, max_gap, Gini)")
    print("  ✓ Performed peer calibration with narrative hooks")
    print("  ✓ Rolled up micro→meso→macro with penalty integration")
    print("  ✓ Scanned for contradictions across levels")
    print("  ✓ Generated comprehensive portfolio composition")
    print("  ✓ Exported posterior tables to CSV")
    print()

if __name__ == "__main__":
    main()
