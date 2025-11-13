#!/usr/bin/env python3
"""
GOLD-CANARIO Comprehensive Integration Tests
=============================================

Full end-to-end integration tests demonstrating the complete GOLD-CANARIO
reporting workflow from micro -> meso -> macro levels.

Tests the integration of:
- Micro: ProvenanceAuditor, BayesianPosteriorExplainer, AntiMilagroStressTester
- Meso: analyze_policy_dispersion, reconcile_cross_metrics, compose_cluster_posterior, calibrate_against_peers
- Macro: CoverageGapStressor, ContradictionScanner, BayesianPortfolioComposer, RoadmapOptimizer, PeerNormalizer
"""

import time

import pytest

from saaaaaa.processing.macro_prompts import (
    BayesianPortfolioComposer,
    ContradictionScanner,
    CoverageGapStressor,
    MacroPromptsOrchestrator,
    PeerNormalizer,
    RoadmapOptimizer,
)
from saaaaaa.analysis.meso_cluster_analysis import (
    analyze_policy_dispersion,
    calibrate_against_peers,
    compose_cluster_posterior,
)
from saaaaaa.processing.micro_prompts import (
    AntiMilagroStressTester,
    BayesianPosteriorExplainer,
    CausalChain,
    ProportionalityPattern,
    ProvenanceAuditor,
    ProvenanceDAG,
    ProvenanceNode,
    QMCMRecord,
    Signal,
)

class TestMicroToMesoIntegration:
    """Test integration from micro to meso level"""

    def test_micro_provenance_to_meso_composition(self):
        """Test micro provenance audit feeds into meso composition"""
        # MICRO: Audit provenance
        auditor = ProvenanceAuditor()

        registry = {
            "r1": QMCMRecord(
                question_id="Q1",
                method_fqn="module.method1",
                contribution_weight=0.8,
                timestamp=time.time(),
                output_schema={}
            )
        }

        nodes = {
            "input1": ProvenanceNode("input1", "input", []),
            "method1": ProvenanceNode("method1", "method", ["input1"], "r1")
        }
        dag = ProvenanceDAG(nodes=nodes, edges=[("input1", "method1")])

        audit_result = auditor.audit(None, registry, dag)

        # Extract contribution weights from audit
        contributions = list(audit_result.contribution_weights.values())

        # MESO: Use contributions to compose posterior
        micro_posteriors = [0.7, 0.8, 0.75]
        meso_result, meso_narrative = compose_cluster_posterior(
            micro_posteriors,
            weighting_trace=contributions + [0.5, 0.5]  # Pad to match length
        )

        assert audit_result.severity == 'LOW'
        assert 0.0 <= meso_result['prior_meso'] <= 1.0
        assert 'prior meso' in meso_narrative.lower()

    def test_micro_bayesian_to_meso_dispersion(self):
        """Test micro Bayesian signals feed into meso dispersion analysis"""
        # MICRO: Explain Bayesian posteriors
        explainer = BayesianPosteriorExplainer()

        signals = [
            Signal("Smoking-Gun", 0.8, 1.0, "E1", True, 0.3),
            Signal("Hoop", 0.7, 1.0, "E2", True, 0.2),
        ]

        bayesian_result = explainer.explain(
            prior=0.5,
            signals=signals,
            posterior=0.8
        )

        # Extract posteriors from multiple micro analyses
        policy_scores = {
            "P1": bayesian_result.posterior,
            "P2": 0.75,
            "P3": 0.82,
            "P4": 0.78
        }

        # MESO: Analyze dispersion across policies
        meso_result, meso_narrative = analyze_policy_dispersion(
            policy_scores,
            peer_dispersion_stats={"cv_median": 0.15, "gap_median": 0.10},
            thresholds={"cv_warn": 0.20, "cv_fail": 0.30, "gap_warn": 0.15, "gap_fail": 0.25}
        )

        assert bayesian_result.posterior == 0.8
        assert meso_result['class'] in ["Concentrado", "Moderado", "Disperso", "Crítico"]
        assert meso_result['cv'] >= 0.0

    def test_micro_stress_to_meso_calibration(self):
        """Test micro stress test results feed into meso peer calibration"""
        # MICRO: Stress test causal chains
        tester = AntiMilagroStressTester()

        chain = CausalChain(
            steps=["A", "B", "C"],
            edges=[("A", "B"), ("B", "C")]
        )
        patterns = [
            ProportionalityPattern("linear", 0.9, "A->B"),
            ProportionalityPattern("dose-response", 0.85, "B->C"),
        ]

        stress_result = tester.stress_test(chain, patterns, [])

        # Use fragility flag to adjust policy scores
        adjustment_factor = 0.9 if not stress_result.fragility_flag else 0.7

        policy_scores = {
            "P1": 0.8 * adjustment_factor,
            "P2": 0.75 * adjustment_factor
        }

        # MESO: Calibrate against peers
        peer_context = {
            "P1": {"median": 0.7, "p25": 0.6, "p75": 0.8},
            "P2": {"median": 0.65, "p25": 0.55, "p75": 0.75}
        }

        meso_result, meso_narrative = calibrate_against_peers(
            policy_scores,
            peer_context
        )

        assert not stress_result.fragility_flag
        assert 'area_positions' in meso_result
        assert 'outliers' in meso_result

class TestMesoToMacroIntegration:
    """Test integration from meso to macro level"""

    def test_meso_dispersion_to_macro_coverage(self):
        """Test meso dispersion feeds into macro coverage analysis"""
        # MESO: Analyze dispersion
        policy_scores = {
            "P1": 0.7,
            "P2": 0.8,
            "P3": 0.65,
            "P4": 0.75
        }

        meso_dispersion, _ = analyze_policy_dispersion(
            policy_scores, {}, {}
        )

        # Extract dimension coverage from policy scores
        dimension_coverage = {
            "D1": meso_dispersion['cv'] < 0.3 and 0.9 or 0.6,
            "D2": 0.8,
            "D3": 0.75,
            "D4": 0.7,
            "D5": 0.85,
            "D6": 0.8
        }

        # MACRO: Evaluate coverage gaps
        stressor = CoverageGapStressor()
        macro_result = stressor.evaluate(
            convergence_by_dimension={},
            missing_clusters=["C1"] if meso_dispersion['class'] == "Crítico" else [],
            dimension_coverage=dimension_coverage,
            policy_area_coverage=policy_scores
        )

        assert meso_dispersion['penalty'] >= 0.0
        assert macro_result.coverage_index >= 0.0
        assert macro_result.degraded_confidence is not None

    def test_meso_composition_to_macro_portfolio(self):
        """Test meso composition feeds into macro portfolio"""
        # MESO: Compose cluster posteriors
        micro_posteriors = [0.7, 0.8, 0.75, 0.82]

        meso_result1, _ = compose_cluster_posterior(
            micro_posteriors[:2],
            reconciliation_penalties={"dispersion_penalty": 0.05}
        )

        meso_result2, _ = compose_cluster_posterior(
            micro_posteriors[2:],
            reconciliation_penalties={"dispersion_penalty": 0.03}
        )

        # MACRO: Compose portfolio from meso posteriors
        composer = BayesianPortfolioComposer()

        meso_posteriors = {
            "C1": meso_result1['posterior_meso'],
            "C2": meso_result2['posterior_meso']
        }
        cluster_weights = {
            "C1": 1.5,
            "C2": 1.0
        }

        macro_portfolio = composer.compose(
            meso_posteriors,
            cluster_weights,
            reconciliation_penalties={
                "coverage": 0.05,
                "dispersion": 0.08
            }
        )

        assert 0.0 <= meso_result1['posterior_meso'] <= 1.0
        assert 0.0 <= macro_portfolio.posterior_global <= 1.0
        assert macro_portfolio.var_global >= 0.0

    def test_meso_calibration_to_macro_peer_normalization(self):
        """Test meso calibration feeds into macro peer normalization"""
        # MESO: Calibrate against peers
        policy_scores = {
            "P1": 0.75,
            "P2": 0.82,
            "P3": 0.68
        }

        peer_context = {
            "P1": {"median": 0.70, "p25": 0.60, "p75": 0.80},
            "P2": {"median": 0.75, "p25": 0.65, "p75": 0.85},
            "P3": {"median": 0.70, "p25": 0.60, "p75": 0.80}
        }

        meso_calibration, _ = calibrate_against_peers(
            policy_scores,
            peer_context
        )

        # Extract positioning for macro normalization
        convergence_by_area = policy_scores

        peer_distributions = {
            area: {
                "mean": peer_context[area]["median"],
                "std": (peer_context[area]["p75"] - peer_context[area]["p25"]) / 1.35
            }
            for area in policy_scores
        }

        # MACRO: Normalize against peers
        normalizer = PeerNormalizer()
        macro_normalization = normalizer.normalize(
            convergence_by_area,
            peer_distributions,
            baseline_confidence=1.0
        )

        assert 'area_positions' in meso_calibration
        assert len(macro_normalization.z_scores) == len(policy_scores)
        assert macro_normalization.peer_position in ["above_average", "average", "below_average"]

class TestFullWorkflowIntegration:
    """Test complete end-to-end workflow"""

    def test_complete_gold_canario_workflow(self):
        """Test complete GOLD-CANARIO workflow from micro to macro"""
        # ===============================
        # MICRO LEVEL ANALYSIS
        # ===============================

        # 1. Provenance Audit
        auditor = ProvenanceAuditor()
        registry = {
            "r1": QMCMRecord("Q1", "method1", 0.8, time.time(), {})
        }
        nodes = {
            "input1": ProvenanceNode("input1", "input", []),
            "method1": ProvenanceNode("method1", "method", ["input1"], "r1")
        }
        dag = ProvenanceDAG(nodes=nodes, edges=[("input1", "method1")])

        micro_audit = auditor.audit(None, registry, dag)

        # 2. Bayesian Posterior Explanation
        explainer = BayesianPosteriorExplainer()
        signals = [
            Signal("Smoking-Gun", 0.9, 1.0, "E1", True, 0.4),
            Signal("Hoop", 0.7, 1.0, "E2", True, 0.2),
        ]
        micro_bayesian = explainer.explain(0.5, signals, 0.85)

        # 3. Anti-Milagro Stress Test
        tester = AntiMilagroStressTester()
        chain = CausalChain(["A", "B", "C"], [("A", "B"), ("B", "C")])
        patterns = [
            ProportionalityPattern("linear", 0.9, "A->B"),
            ProportionalityPattern("dose-response", 0.85, "B->C"),
        ]
        micro_stress = tester.stress_test(chain, patterns, [])

        # ===============================
        # MESO LEVEL ANALYSIS
        # ===============================

        # 4. Policy Dispersion Analysis
        policy_scores = {
            "P1": micro_bayesian.posterior,
            "P2": 0.78,
            "P3": 0.82,
            "P4": 0.75
        }
        meso_dispersion, _ = analyze_policy_dispersion(
            policy_scores,
            {"cv_median": 0.15, "gap_median": 0.10},
            {"cv_warn": 0.20, "cv_fail": 0.30, "gap_warn": 0.15, "gap_fail": 0.25}
        )

        # 5. Cluster Posterior Composition
        micro_posteriors = [0.85, 0.78, 0.82, 0.75]
        meso_composition, _ = compose_cluster_posterior(
            micro_posteriors,
            reconciliation_penalties={
                "dispersion_penalty": meso_dispersion['penalty'],
                "coverage_penalty": 0.03
            }
        )

        # 6. Peer Calibration
        peer_context = {
            area: {"median": 0.70, "p25": 0.60, "p75": 0.80}
            for area in policy_scores
        }
        meso_calibration, _ = calibrate_against_peers(policy_scores, peer_context)

        # ===============================
        # MACRO LEVEL ANALYSIS
        # ===============================

        # 7. Coverage Gap Stressor
        dimension_coverage = {f"D{i}": 0.75 + i*0.03 for i in range(1, 7)}
        stressor = CoverageGapStressor()
        macro_coverage = stressor.evaluate(
            convergence_by_dimension={f"D{i}": 0.8 for i in range(1, 7)},
            missing_clusters=[],
            dimension_coverage=dimension_coverage,
            policy_area_coverage=policy_scores,
            baseline_confidence=1.0
        )

        # 8. Contradiction Scanner
        scanner = ContradictionScanner()
        micro_claims = [
            {"dimension": "D1", "score": 0.85, "posterior": 0.9}
        ]
        macro_contradictions = scanner.scan(
            micro_claims,
            {"D1": {"score": 0.8}},
            {"D1": {"score": 0.85}}
        )

        # 9. Bayesian Portfolio Composer
        composer = BayesianPortfolioComposer()
        macro_portfolio = composer.compose(
            meso_posteriors={"C1": meso_composition['posterior_meso']},
            cluster_weights={"C1": 1.0},
            reconciliation_penalties={
                "coverage": 1.0 - macro_coverage.degraded_confidence,
                "dispersion": meso_dispersion['penalty']
            }
        )

        # 10. Roadmap Optimizer
        optimizer = RoadmapOptimizer()
        critical_gaps = [
            {"id": f"G{i}"} for i in range(1, len(macro_coverage.critical_dimensions_below_threshold) + 1)
        ]
        if not critical_gaps:
            critical_gaps = [{"id": "G1"}]  # At least one gap

        macro_roadmap = optimizer.optimize(
            critical_gaps,
            dependency_graph={},
            effort_estimates={gap["id"]: 2.0 for gap in critical_gaps},
            impact_scores={gap["id"]: 0.8 for gap in critical_gaps}
        )

        # 11. Peer Normalizer
        normalizer = PeerNormalizer()
        peer_distributions = {
            area: {"mean": 0.70, "std": 0.08}
            for area in policy_scores
        }
        macro_normalization = normalizer.normalize(
            policy_scores,
            peer_distributions,
            baseline_confidence=macro_coverage.degraded_confidence
        )

        # ===============================
        # VERIFY COMPLETE WORKFLOW
        # ===============================

        # Micro level results
        assert micro_audit.severity in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        assert 0.0 <= micro_bayesian.posterior <= 1.0
        assert micro_stress.density >= 0.0

        # Meso level results
        assert meso_dispersion['class'] in ["Concentrado", "Moderado", "Disperso", "Crítico"]
        assert 0.0 <= meso_composition['posterior_meso'] <= 1.0
        assert 'area_positions' in meso_calibration

        # Macro level results
        assert 0.0 <= macro_coverage.coverage_index <= 1.0
        assert isinstance(macro_contradictions.contradictions, list)
        assert 0.0 <= macro_portfolio.posterior_global <= 1.0
        assert len(macro_roadmap.phases) == 3
        assert macro_normalization.peer_position in ["above_average", "average", "below_average"]

        # Verify data flows correctly through levels
        assert len(micro_posteriors) > 0
        assert meso_composition['prior_meso'] > 0
        assert macro_portfolio.prior_global > 0

class TestMacroOrchestrator:
    """Test MacroPromptsOrchestrator for unified execution"""

    def test_orchestrator_execution(self):
        """Test orchestrator executes all 5 macro analyses"""
        orchestrator = MacroPromptsOrchestrator()

        macro_data = {
            "convergence_by_dimension": {f"D{i}": 0.75 for i in range(1, 7)},
            "convergence_by_policy_area": {f"P{i}": 0.7 + i*0.02 for i in range(1, 5)},
            "missing_clusters": [],
            "dimension_coverage": {f"D{i}": 0.85 for i in range(1, 7)},
            "policy_area_coverage": {f"P{i}": 0.8 for i in range(1, 5)},
            "micro_claims": [],
            "meso_summary_signals": {},
            "macro_narratives": {},
            "meso_posteriors": {"C1": 0.8},
            "cluster_weights": {"C1": 1.0},
            "critical_gaps": [{"id": "G1"}],
            "dependency_graph": {},
            "effort_estimates": {"G1": 2.0},
            "impact_scores": {"G1": 0.8},
            "peer_distributions": {
                f"P{i}": {"mean": 0.70, "std": 0.05}
                for i in range(1, 5)
            },
            "baseline_confidence": 1.0
        }

        results = orchestrator.execute_all(macro_data)

        # Verify all 5 analyses executed
        assert 'coverage_analysis' in results
        assert 'contradiction_report' in results
        assert 'bayesian_portfolio' in results
        assert 'implementation_roadmap' in results
        assert 'peer_normalization' in results

        # Verify structure of each result
        assert 'coverage_index' in results['coverage_analysis']
        assert 'contradictions' in results['contradiction_report']
        assert 'posterior_global' in results['bayesian_portfolio']
        assert 'phases' in results['implementation_roadmap']
        assert 'z_scores' in results['peer_normalization']

class TestErrorHandlingAndEdgeCases:
    """Test error handling across integration points"""

    def test_micro_to_meso_with_empty_data(self):
        """Test graceful handling of empty micro data"""
        # Empty micro posteriors should raise error
        with pytest.raises(ValueError):
            compose_cluster_posterior([])

    def test_meso_to_macro_with_minimal_data(self):
        """Test macro analysis with minimal meso data"""
        composer = BayesianPortfolioComposer()

        # Single cluster should work
        result = composer.compose(
            meso_posteriors={"C1": 0.8},
            cluster_weights={"C1": 1.0}
        )

        assert result.prior_global == 0.8
        assert result.posterior_global == 0.8

    def test_workflow_resilience_to_failures(self):
        """Test workflow continues despite component failures"""
        # Some micro analyses may fail, but workflow should continue
        try:
            # Attempt invalid micro analysis
            explainer = BayesianPosteriorExplainer()
            explainer.explain(0.5, [], 0.5)  # Empty signals

            # Should still be able to continue with meso analysis
            policy_scores = {"P1": 0.7}
            meso_result, _ = analyze_policy_dispersion(policy_scores, {}, {})

            assert meso_result['cv'] >= 0.0
        except Exception as e:
            pytest.fail(f"Workflow should handle failures gracefully: {e}")

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
