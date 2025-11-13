"""
Integration Guide: Bayesian Multi-Level System with Report Assembly
====================================================================

This guide demonstrates how to integrate the Bayesian multi-level analysis system
with the existing report_assembly.py module for comprehensive policy analysis.

Author: Integration Team
Version: 1.0.0
"""

import logging
from pathlib import Path
from typing import Any

# Import Bayesian multi-level components
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
    BayesianPortfolioComposer,
    # Roll-up and composition
    MultiLevelBayesianOrchestrator,
    PeerContext,
    # Bayesian updating
    ProbativeTest,
    ProbativeTestType,
    ValidationRule,
    ValidatorType,
)

# Import existing report assembly components
# Note: These imports would be from the actual report_assembly.py
# from report_assembly import ReportAssembler, MicroLevelAnswer, MesoLevelCluster, MacroLevelConvergence

logger = logging.getLogger(__name__)

class EnhancedReportAssembler:
    """
    Enhanced Report Assembler with Bayesian multi-level analysis integration

    This class wraps the existing ReportAssembler and adds:
    - Reconciliation layer validation
    - Bayesian posterior estimation
    - Dispersion analysis
    - Peer calibration
    - Contradiction detection
    - Penalty-adjusted scoring
    """

    def __init__(
        self,
        validation_rules: list[ValidationRule],
        output_dir: Path = Path("data/bayesian_outputs")
    ):
        """
        Initialize enhanced report assembler

        Args:
            validation_rules: List of validation rules for reconciliation layer
            output_dir: Directory for Bayesian posterior tables
        """
        # Initialize Bayesian orchestrator
        self.bayesian_orchestrator = MultiLevelBayesianOrchestrator(
            validation_rules=validation_rules,
            output_dir=output_dir
        )

        # Components can be accessed individually
        self.validator = self.bayesian_orchestrator.reconciliation_validator
        self.bayesian_updater = self.bayesian_orchestrator.bayesian_updater
        self.dispersion_engine = self.bayesian_orchestrator.dispersion_engine
        self.peer_calibrator = self.bayesian_orchestrator.peer_calibrator
        self.contradiction_scanner = self.bayesian_orchestrator.contradiction_scanner

        logger.info("Enhanced Report Assembler initialized with Bayesian analysis")

    def enhance_micro_answer(
        self,
        question_id: str,
        raw_score: float,
        question_data: dict[str, Any],
        probative_tests: list[tuple] = None
    ) -> dict[str, Any]:
        """
        Enhance a micro-level answer with Bayesian analysis

        Args:
            question_id: Question identifier (e.g., "P1-D1-Q1")
            raw_score: Raw score from existing analysis
            question_data: Additional question data for validation
            probative_tests: List of (ProbativeTest, bool) tuples

        Returns:
            Enhanced analysis with Bayesian posterior and penalties
        """
        # Step 1: Reconciliation validation
        validation_results = self.validator.validate_data(question_data)
        validation_penalty = self.validator.calculate_total_penalty(validation_results)

        # Step 2: Bayesian updating
        if probative_tests:
            final_posterior = self.bayesian_updater.sequential_update(
                raw_score, probative_tests
            )
        else:
            final_posterior = raw_score

        # Step 3: Calculate adjusted score
        adjusted_score = final_posterior * (1 - validation_penalty)

        return {
            'question_id': question_id,
            'raw_score': raw_score,
            'validation_penalty': validation_penalty,
            'validation_results': [
                {
                    'rule': r.rule.field_name,
                    'passed': r.passed,
                    'penalty': r.penalty_applied
                }
                for r in validation_results
            ],
            'final_posterior': final_posterior,
            'adjusted_score': adjusted_score,
            'bayesian_updates': len(probative_tests) if probative_tests else 0
        }

    def enhance_meso_cluster(
        self,
        cluster_id: str,
        micro_scores: list[float],
        peer_contexts: list[PeerContext] = None
    ) -> dict[str, Any]:
        """
        Enhance a meso-level cluster with dispersion analysis and peer calibration

        Args:
            cluster_id: Cluster identifier
            micro_scores: List of micro-level adjusted scores
            peer_contexts: Optional peer contexts for calibration

        Returns:
            Enhanced cluster analysis with dispersion metrics and peer comparison
        """
        # Step 1: Calculate dispersion metrics
        dispersion_penalty, dispersion_metrics = (
            self.dispersion_engine.calculate_dispersion_penalty(micro_scores)
        )

        # Step 2: Raw meso score
        import numpy as np
        raw_meso_score = np.mean(micro_scores)

        # Step 3: Peer calibration
        peer_comparison = None
        peer_penalty = 0.0

        if peer_contexts:
            peer_comparison = self.peer_calibrator.compare_to_peers(
                raw_meso_score, peer_contexts, cluster_id
            )
            peer_penalty = peer_comparison.deviation_penalty

        # Step 4: Calculate adjusted score
        total_penalty = dispersion_penalty + peer_penalty
        adjusted_score = raw_meso_score * (1 - total_penalty)

        return {
            'cluster_id': cluster_id,
            'raw_meso_score': raw_meso_score,
            'dispersion_metrics': dispersion_metrics,
            'dispersion_penalty': dispersion_penalty,
            'peer_comparison': {
                'narrative': peer_comparison.narrative,
                'z_score': peer_comparison.z_score,
                'percentile': peer_comparison.percentile
            } if peer_comparison else None,
            'peer_penalty': peer_penalty,
            'total_penalty': total_penalty,
            'adjusted_score': adjusted_score
        }

    def compose_macro_portfolio(
        self,
        meso_analyses: list[dict[str, Any]],
        total_questions: int = 300
    ) -> dict[str, Any]:
        """
        Compose macro-level portfolio with contradiction detection

        Args:
            meso_analyses: List of meso-level analysis results
            total_questions: Total number of questions in assessment

        Returns:
            Macro portfolio analysis with penalties and recommendations
        """
        # Use the portfolio composer
        composer = BayesianPortfolioComposer()

        # Convert dicts to MesoLevelAnalysis objects for processing
        from saaaaaa.analysis.bayesian_multilevel_system import MesoLevelAnalysis
        meso_objects = [
            MesoLevelAnalysis(
                cluster_id=m['cluster_id'],
                micro_scores=[],  # Already aggregated
                raw_meso_score=m['raw_meso_score'],
                dispersion_metrics=m['dispersion_metrics'],
                dispersion_penalty=m['dispersion_penalty'],
                peer_comparison=None,
                peer_penalty=m['peer_penalty'],
                total_penalty=m['total_penalty'],
                final_posterior=m['adjusted_score'],
                adjusted_score=m['adjusted_score']
            )
            for m in meso_analyses
        ]

        # Compose macro
        macro = composer.compose_macro_portfolio(
            meso_objects,
            total_questions,
            self.contradiction_scanner
        )

        return {
            'overall_posterior': macro.overall_posterior,
            'coverage_score': macro.coverage_score,
            'coverage_penalty': macro.coverage_penalty,
            'dispersion_score': macro.dispersion_score,
            'dispersion_penalty': macro.dispersion_penalty,
            'contradiction_count': macro.contradiction_count,
            'contradiction_penalty': macro.contradiction_penalty,
            'total_penalty': macro.total_penalty,
            'adjusted_score': macro.adjusted_score,
            'cluster_scores': macro.cluster_scores,
            'recommendations': macro.recommendations
        }

# ============================================================================
# INTEGRATION EXAMPLE: Extending ReportAssembler
# ============================================================================

def example_integration_workflow():
    """
    Example: How to integrate Bayesian analysis into existing workflow
    """
    print("=" * 80)
    print("INTEGRATION EXAMPLE: Bayesian Multi-Level + Report Assembly")
    print("=" * 80)
    print()

    # Step 1: Define validation rules
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
    ]

    # Step 2: Initialize enhanced assembler
    assembler = EnhancedReportAssembler(
        validation_rules=validation_rules,
        output_dir=Path("data/bayesian_outputs")
    )

    # Step 3: Process micro-level questions
    print("[MICRO] Processing questions with Bayesian enhancement...")

    # Define probative test
    baseline_test = ProbativeTest(
        test_type=ProbativeTestType.HOOP_TEST,
        test_name="Baseline data check",
        evidence_strength=0.6,
        prior_probability=0.5
    )

    # Enhance a micro answer
    micro_enhanced = assembler.enhance_micro_answer(
        question_id="P1-D1-Q1",
        raw_score=0.75,
        question_data={
            'score': 0.75,
            'budget_unit': 'COP'
        },
        probative_tests=[(baseline_test, True)]
    )

    print(f"  Question: {micro_enhanced['question_id']}")
    print(f"  Raw score: {micro_enhanced['raw_score']:.4f}")
    print(f"  Final posterior: {micro_enhanced['final_posterior']:.4f}")
    print(f"  Adjusted score: {micro_enhanced['adjusted_score']:.4f}")
    print()

    # Step 4: Process meso-level clusters
    print("[MESO] Aggregating to cluster level with dispersion analysis...")

    peer_contexts = [
        PeerContext("peer1", "Bogotá", {"CLUSTER_D1": 0.72}),
        PeerContext("peer2", "Medellín", {"CLUSTER_D1": 0.75}),
    ]

    meso_enhanced = assembler.enhance_meso_cluster(
        cluster_id="CLUSTER_D1",
        micro_scores=[0.75, 0.72, 0.68],
        peer_contexts=peer_contexts
    )

    print(f"  Cluster: {meso_enhanced['cluster_id']}")
    print(f"  Raw meso score: {meso_enhanced['raw_meso_score']:.4f}")
    print(f"  Dispersion penalty: {meso_enhanced['dispersion_penalty']:.4f}")
    print(f"  Adjusted score: {meso_enhanced['adjusted_score']:.4f}")
    if meso_enhanced['peer_comparison']:
        print(f"  Peer narrative: {meso_enhanced['peer_comparison']['narrative']}")
    print()

    # Step 5: Compose macro portfolio
    print("[MACRO] Composing portfolio-wide analysis...")

    macro_enhanced = assembler.compose_macro_portfolio(
        meso_analyses=[meso_enhanced],
        total_questions=300
    )

    print(f"  Overall posterior: {macro_enhanced['overall_posterior']:.4f}")
    print(f"  Coverage penalty: {macro_enhanced['coverage_penalty']:.4f}")
    print(f"  Final adjusted score: {macro_enhanced['adjusted_score']:.4f}")
    print("  Recommendations:")
    for rec in macro_enhanced['recommendations']:
        print(f"    - {rec}")
    print()

    print("=" * 80)
    print("INTEGRATION COMPLETE")
    print("=" * 80)
    print()
    print("The enhanced system successfully integrates:")
    print("  ✓ Validation layer with existing question processing")
    print("  ✓ Bayesian updating with probative evidence")
    print("  ✓ Dispersion analysis at meso level")
    print("  ✓ Peer calibration with narrative generation")
    print("  ✓ Macro portfolio composition with penalties")
    print()

# ============================================================================
# INTEGRATION PATTERNS
# ============================================================================

class IntegrationPatterns:
    """
    Common integration patterns for the Bayesian multi-level system
    """

    @staticmethod
    def pattern_1_extend_micro_answer():
        """
        Pattern 1: Extend existing MicroLevelAnswer with Bayesian analysis

        Use this when you want to add Bayesian posterior to existing micro answers
        """
        code = '''
        # In report_assembly.py, modify generate_micro_answer():

        def generate_micro_answer(self, question_spec, execution_results, plan_text):
            # ... existing code to calculate base score ...

            # NEW: Add Bayesian enhancement
            if self.bayesian_assembler:
                bayesian_result = self.bayesian_assembler.enhance_micro_answer(
                    question_id=question_spec.canonical_id,
                    raw_score=score,
                    question_data=execution_results,
                    probative_tests=self._extract_probative_tests(execution_results)
                )

                # Use adjusted score instead of raw score
                score = bayesian_result['adjusted_score']

                # Add Bayesian metadata
                micro_answer.metadata['bayesian_posterior'] = bayesian_result['final_posterior']
                micro_answer.metadata['validation_penalty'] = bayesian_result['validation_penalty']

            # ... continue with existing code ...
        '''
        return code

    @staticmethod
    def pattern_2_enhance_meso_cluster():
        """
        Pattern 2: Add dispersion and peer analysis to meso clusters
        """
        code = '''
        # In report_assembly.py, modify generate_meso_cluster():

        def generate_meso_cluster(self, cluster_id, micro_answers):
            # ... existing code to calculate base cluster score ...

            # NEW: Add dispersion and peer calibration
            if self.bayesian_assembler:
                micro_scores = [m.adjusted_score for m in micro_answers]

                meso_result = self.bayesian_assembler.enhance_meso_cluster(
                    cluster_id=cluster_id,
                    micro_scores=micro_scores,
                    peer_contexts=self._load_peer_contexts()
                )

                # Use adjusted meso score
                cluster.avg_score = meso_result['adjusted_score'] * 100  # to percentage

                # Add dispersion metrics to metadata
                cluster.metadata['dispersion'] = meso_result['dispersion_metrics']
                cluster.metadata['peer_comparison'] = meso_result['peer_comparison']

            # ... continue with existing code ...
        '''
        return code

    @staticmethod
    def pattern_3_macro_composition():
        """
        Pattern 3: Integrate macro contradiction detection and portfolio composition
        """
        code = '''
        # In report_assembly.py, modify generate_macro_convergence():

        def generate_macro_convergence(self, micro_answers, meso_clusters):
            # ... existing code to calculate base macro score ...

            # NEW: Add contradiction detection and penalty composition
            if self.bayesian_assembler:
                meso_analyses = [
                    {
                        'cluster_id': c.cluster_name,
                        'raw_meso_score': c.avg_score / 100,
                        'dispersion_metrics': c.metadata.get('dispersion', {}),
                        'dispersion_penalty': c.metadata.get('dispersion', {}).get('total_penalty', 0),
                        'peer_penalty': 0.0,
                        'total_penalty': 0.0,
                        'adjusted_score': c.avg_score / 100
                    }
                    for c in meso_clusters
                ]

                macro_result = self.bayesian_assembler.compose_macro_portfolio(
                    meso_analyses=meso_analyses,
                    total_questions=300
                )

                # Use adjusted macro score
                convergence.overall_score = macro_result['adjusted_score'] * 100

                # Add penalty breakdown
                convergence.metadata['coverage_penalty'] = macro_result['coverage_penalty']
                convergence.metadata['dispersion_penalty'] = macro_result['dispersion_penalty']
                convergence.metadata['contradiction_penalty'] = macro_result['contradiction_penalty']
                convergence.metadata['contradictions'] = macro_result['contradiction_count']

                # Add strategic recommendations
                convergence.strategic_recommendations.extend(macro_result['recommendations'])

            # ... continue with existing code ...
        '''
        return code

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # Run integration example
    example_integration_workflow()

    print("\n" + "=" * 80)
    print("INTEGRATION PATTERNS")
    print("=" * 80)
    print()
    print("Pattern 1: Extend Micro Answers")
    print(IntegrationPatterns.pattern_1_extend_micro_answer())
    print()
    print("Pattern 2: Enhance Meso Clusters")
    print(IntegrationPatterns.pattern_2_enhance_meso_cluster())
    print()
    print("Pattern 3: Macro Composition")
    print(IntegrationPatterns.pattern_3_macro_composition())
