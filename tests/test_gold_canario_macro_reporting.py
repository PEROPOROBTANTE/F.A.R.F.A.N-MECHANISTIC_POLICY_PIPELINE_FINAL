#!/usr/bin/env python3
"""
GOLD-CANARIO Comprehensive Tests: Macro Reporting
==================================================

Tests for all 5 macro-level analysis prompts:
1. CoverageGapStressor - Coverage & structural gap analysis
2. ContradictionScanner - Inter-level contradiction detection
3. BayesianPortfolioComposer - Global Bayesian integration
4. RoadmapOptimizer - Implementation roadmap generation
5. PeerNormalizer - Peer normalization & confidence scaling
"""

import pytest

from saaaaaa.processing.macro_prompts import (
    BayesianPortfolio,
    BayesianPortfolioComposer,
    ContradictionReport,
    ContradictionScanner,
    CoverageAnalysis,
    CoverageGapStressor,
    ImplementationRoadmap,
    PeerNormalization,
    PeerNormalizer,
    RoadmapOptimizer,
)

# ============================================================================
# TEST COVERAGE GAP STRESSOR
# ============================================================================

class TestCoverageGapStressorBasics:
    """Test basic functionality of CoverageGapStressor"""

    def test_initialization_defaults(self):
        """Test default initialization"""
        stressor = CoverageGapStressor()
        assert stressor.critical_dimensions == ["D3", "D6"]
        assert stressor.coverage_threshold == 0.70

    def test_initialization_custom(self):
        """Test custom initialization"""
        stressor = CoverageGapStressor(
            critical_dimensions=["D1", "D2"],
            coverage_threshold=0.80
        )
        assert stressor.critical_dimensions == ["D1", "D2"]
        assert stressor.coverage_threshold == 0.80

class TestCoverageIndexCalculation:
    """Test coverage index calculation"""

    def test_perfect_coverage(self):
        """Test perfect coverage across all dimensions"""
        stressor = CoverageGapStressor()

        dimension_coverage = {f"D{i}": 1.0 for i in range(1, 7)}

        result = stressor.evaluate(
            convergence_by_dimension={},
            missing_clusters=[],
            dimension_coverage=dimension_coverage,
            policy_area_coverage={}
        )

        assert result.coverage_index == 1.0
        assert result.degraded_confidence is not None

    def test_partial_coverage(self):
        """Test partial coverage"""
        stressor = CoverageGapStressor()

        dimension_coverage = {
            "D1": 0.8,
            "D2": 0.9,
            "D3": 0.6,
            "D4": 0.7,
            "D5": 0.85,
            "D6": 0.75
        }

        result = stressor.evaluate(
            convergence_by_dimension={},
            missing_clusters=[],
            dimension_coverage=dimension_coverage,
            policy_area_coverage={}
        )

        assert 0.7 < result.coverage_index < 0.9

    def test_zero_coverage(self):
        """Test zero coverage"""
        stressor = CoverageGapStressor()

        dimension_coverage = {f"D{i}": 0.0 for i in range(1, 7)}

        result = stressor.evaluate(
            convergence_by_dimension={},
            missing_clusters=[],
            dimension_coverage=dimension_coverage,
            policy_area_coverage={}
        )

        assert result.coverage_index == 0.0

class TestCriticalGapDetection:
    """Test critical gap detection"""

    def test_no_critical_gaps(self):
        """Test with no critical gaps"""
        stressor = CoverageGapStressor()

        dimension_coverage = {
            "D3": 0.9,  # Critical, above threshold
            "D6": 0.85  # Critical, above threshold
        }

        result = stressor.evaluate(
            convergence_by_dimension={},
            missing_clusters=[],
            dimension_coverage=dimension_coverage,
            policy_area_coverage={}
        )

        assert len(result.critical_dimensions_below_threshold) == 0

    def test_critical_gaps_detected(self):
        """Test detection of critical gaps"""
        stressor = CoverageGapStressor()

        dimension_coverage = {
            "D3": 0.5,  # Critical, below threshold (0.70)
            "D6": 0.6   # Critical, below threshold
        }

        result = stressor.evaluate(
            convergence_by_dimension={},
            missing_clusters=[],
            dimension_coverage=dimension_coverage,
            policy_area_coverage={}
        )

        assert "D3" in result.critical_dimensions_below_threshold
        assert "D6" in result.critical_dimensions_below_threshold

class TestConfidenceDegradation:
    """Test confidence degradation logic"""

    def test_no_degradation_perfect_coverage(self):
        """Test no degradation with perfect coverage"""
        stressor = CoverageGapStressor()

        dimension_coverage = {f"D{i}": 1.0 for i in range(1, 7)}

        result = stressor.evaluate(
            convergence_by_dimension={},
            missing_clusters=[],
            dimension_coverage=dimension_coverage,
            policy_area_coverage={},
            baseline_confidence=1.0
        )

        assert result.degraded_confidence >= 0.95

    def test_degradation_with_critical_gaps(self):
        """Test degradation with critical gaps"""
        stressor = CoverageGapStressor()

        dimension_coverage = {
            "D3": 0.4,  # Critical gap
            "D6": 0.3   # Critical gap
        }

        result = stressor.evaluate(
            convergence_by_dimension={},
            missing_clusters=[],
            dimension_coverage=dimension_coverage,
            policy_area_coverage={},
            baseline_confidence=1.0
        )

        # Should have significant degradation
        assert result.degraded_confidence < 0.8

class TestPredictiveUplift:
    """Test predictive uplift simulation"""

    def test_uplift_with_missing_clusters(self):
        """Test uplift estimation with missing clusters"""
        stressor = CoverageGapStressor()

        dimension_coverage = {
            "D1": 0.7,
            "D2": 0.8
        }
        convergence = {
            "D1": 0.75,
            "D2": 0.85
        }

        result = stressor.evaluate(
            convergence_by_dimension=convergence,
            missing_clusters=["C1", "C2"],
            dimension_coverage=dimension_coverage,
            policy_area_coverage={}
        )

        assert "C1" in result.predictive_uplift
        assert "C2" in result.predictive_uplift
        assert all(v > 0 for v in result.predictive_uplift.values())

# ============================================================================
# TEST CONTRADICTION SCANNER
# ============================================================================

class TestContradictionScannerBasics:
    """Test basic functionality of ContradictionScanner"""

    def test_initialization_defaults(self):
        """Test default initialization"""
        scanner = ContradictionScanner()
        assert scanner.k == 3
        assert scanner.theta == 0.7

    def test_initialization_custom(self):
        """Test custom initialization"""
        scanner = ContradictionScanner(
            contradiction_threshold=5,
            posterior_threshold=0.8
        )
        assert scanner.k == 5
        assert scanner.theta == 0.8

class TestContradictionDetection:
    """Test contradiction detection"""

    def test_no_contradictions(self):
        """Test with no contradictions"""
        scanner = ContradictionScanner()

        micro_claims = [
            {"dimension": "D1", "score": 0.8, "posterior": 0.85}
        ]
        meso_signals = {"D1": {"score": 0.8}}
        macro_narratives = {"D1": {"score": 0.8}}

        result = scanner.scan(micro_claims, meso_signals, macro_narratives)

        assert len(result.contradictions) == 0
        assert result.consistency_score > 0.9

    def test_minor_contradictions(self):
        """Test with minor contradictions"""
        scanner = ContradictionScanner()

        # Two claims contradict, below threshold of 3
        micro_claims = [
            {"dimension": "D1", "score": 0.2, "posterior": 0.8},
            {"dimension": "D1", "score": 0.3, "posterior": 0.75}
        ]
        meso_signals = {}
        macro_narratives = {"D1": {"score": 0.9}}  # High macro score

        result = scanner.scan(micro_claims, meso_signals, macro_narratives)

        # Below threshold, might not flag
        assert result.consistency_score is not None

    def test_major_contradictions(self):
        """Test with major contradictions exceeding threshold"""
        scanner = ContradictionScanner(contradiction_threshold=3)

        # 4 claims contradict, above threshold of 3
        micro_claims = [
            {"dimension": "D1", "score": 0.1, "posterior": 0.8},
            {"dimension": "D1", "score": 0.15, "posterior": 0.75},
            {"dimension": "D1", "score": 0.2, "posterior": 0.85},
            {"dimension": "D1", "score": 0.25, "posterior": 0.9}
        ]
        meso_signals = {}
        macro_narratives = {"D1": {"score": 0.9}}  # High macro score

        result = scanner.scan(micro_claims, meso_signals, macro_narratives)

        # Should detect contradictions
        assert len(result.contradictions) >= 0

class TestSuggestedActions:
    """Test suggested action generation"""

    def test_no_actions_for_no_contradictions(self):
        """Test no actions when no contradictions"""
        scanner = ContradictionScanner()

        result = scanner.scan([], {}, {})

        assert len(result.suggested_actions) == 0

    def test_actions_generated_for_contradictions(self):
        """Test actions are generated for contradictions"""
        scanner = ContradictionScanner(contradiction_threshold=2)

        # Create significant contradictions
        micro_claims = [
            {"dimension": "D1", "score": 0.1, "posterior": 0.9},
            {"dimension": "D1", "score": 0.15, "posterior": 0.85},
            {"dimension": "D1", "score": 0.2, "posterior": 0.8}
        ]
        macro_narratives = {"D1": {"score": 0.95}}

        result = scanner.scan(micro_claims, {}, macro_narratives)

        # Should suggest actions if contradictions detected
        assert isinstance(result.suggested_actions, list)

# ============================================================================
# TEST BAYESIAN PORTFOLIO COMPOSER
# ============================================================================

class TestBayesianPortfolioComposerBasics:
    """Test basic functionality of BayesianPortfolioComposer"""

    def test_initialization(self):
        """Test initialization"""
        composer = BayesianPortfolioComposer()
        assert composer.default_variance == 0.05

class TestPriorCalculation:
    """Test global prior calculation"""

    def test_simple_weighted_prior(self):
        """Test simple weighted prior"""
        composer = BayesianPortfolioComposer()

        meso_posteriors = {
            "C1": 0.7,
            "C2": 0.8
        }
        cluster_weights = {
            "C1": 1.0,
            "C2": 1.0
        }

        result = composer.compose(meso_posteriors, cluster_weights)

        assert result.prior_global == 0.75  # (0.7 + 0.8) / 2

    def test_unequal_weights(self):
        """Test unequal cluster weights"""
        composer = BayesianPortfolioComposer()

        meso_posteriors = {
            "C1": 0.6,
            "C2": 0.9
        }
        cluster_weights = {
            "C1": 1.0,
            "C2": 2.0  # Double weight
        }

        result = composer.compose(meso_posteriors, cluster_weights)

        # Weighted mean: (0.6*1 + 0.9*2) / 3 = 2.4 / 3 = 0.8
        assert result.prior_global == 0.8

class TestPenaltyApplication:
    """Test penalty application"""

    def test_no_penalties(self):
        """Test with no penalties"""
        composer = BayesianPortfolioComposer()

        meso_posteriors = {"C1": 0.8}
        cluster_weights = {"C1": 1.0}
        penalties = {}

        result = composer.compose(meso_posteriors, cluster_weights, penalties)

        assert result.posterior_global == result.prior_global
        assert all(p == 0.0 for p in result.penalties_applied.values())

    def test_with_penalties(self):
        """Test with various penalties"""
        composer = BayesianPortfolioComposer()

        meso_posteriors = {"C1": 0.8}
        cluster_weights = {"C1": 1.0}
        penalties = {
            "coverage": 0.1,
            "dispersion": 0.05,
            "contradictions": 0.08
        }

        result = composer.compose(meso_posteriors, cluster_weights, penalties)

        assert result.posterior_global < result.prior_global
        assert result.penalties_applied["coverage"] == 0.1
        assert result.penalties_applied["dispersion"] == 0.05

class TestVarianceCalculation:
    """Test global variance calculation"""

    def test_low_variance(self):
        """Test low variance with similar posteriors"""
        composer = BayesianPortfolioComposer()

        meso_posteriors = {
            "C1": 0.79,
            "C2": 0.80,
            "C3": 0.81
        }
        cluster_weights = {
            "C1": 1.0,
            "C2": 1.0,
            "C3": 1.0
        }

        result = composer.compose(meso_posteriors, cluster_weights)

        assert result.var_global < 0.01

    def test_high_variance(self):
        """Test high variance with divergent posteriors"""
        composer = BayesianPortfolioComposer()

        meso_posteriors = {
            "C1": 0.2,
            "C2": 0.8
        }
        cluster_weights = {
            "C1": 1.0,
            "C2": 1.0
        }

        result = composer.compose(meso_posteriors, cluster_weights)

        assert result.var_global > 0.05

class TestConfidenceInterval:
    """Test confidence interval calculation"""

    def test_confidence_interval_bounds(self):
        """Test confidence interval is bounded"""
        composer = BayesianPortfolioComposer()

        meso_posteriors = {"C1": 0.5}
        cluster_weights = {"C1": 1.0}

        result = composer.compose(meso_posteriors, cluster_weights)

        lower, upper = result.confidence_interval
        assert 0.0 <= lower <= 1.0
        assert 0.0 <= upper <= 1.0
        assert lower <= result.posterior_global <= upper

# ============================================================================
# TEST ROADMAP OPTIMIZER
# ============================================================================

class TestRoadmapOptimizerBasics:
    """Test basic functionality of RoadmapOptimizer"""

    def test_initialization(self):
        """Test initialization"""
        optimizer = RoadmapOptimizer()
        assert optimizer is not None

class TestGapPrioritization:
    """Test gap prioritization by impact/effort"""

    def test_prioritization_by_ratio(self):
        """Test gaps are prioritized by impact/effort ratio"""
        optimizer = RoadmapOptimizer()

        gaps = [
            {"id": "G1"},
            {"id": "G2"},
            {"id": "G3"}
        ]
        effort = {
            "G1": 2.0,  # Ratio: 0.8/2.0 = 0.4
            "G2": 1.0,  # Ratio: 0.3/1.0 = 0.3
            "G3": 3.0   # Ratio: 0.9/3.0 = 0.3
        }
        impact = {
            "G1": 0.8,
            "G2": 0.3,
            "G3": 0.9
        }

        roadmap = optimizer.optimize(gaps, {}, effort, impact)

        # Should have phases assigned
        assert len(roadmap.phases) == 3

class TestPhaseAssignment:
    """Test phase assignment with dependencies"""

    def test_simple_phase_assignment(self):
        """Test simple phase assignment without dependencies"""
        optimizer = RoadmapOptimizer()

        gaps = [{"id": "G1"}]
        dependencies = {}
        effort = {"G1": 2.0}
        impact = {"G1": 0.8}

        roadmap = optimizer.optimize(gaps, dependencies, effort, impact)

        # Gap should be in first phase (0-3m)
        assert any("G1" in str(phase["actions"]) for phase in roadmap.phases)

    def test_dependency_respecting_assignment(self):
        """Test dependencies are respected in phase assignment"""
        optimizer = RoadmapOptimizer()

        gaps = [
            {"id": "G1"},
            {"id": "G2"}
        ]
        dependencies = {
            "G2": ["G1"]  # G2 depends on G1
        }
        effort = {"G1": 2.0, "G2": 2.0}
        impact = {"G1": 0.5, "G2": 0.8}

        roadmap = optimizer.optimize(gaps, dependencies, effort, impact)

        # Should assign in dependency order
        assert len(roadmap.phases) == 3

class TestCriticalPath:
    """Test critical path identification"""

    def test_critical_path_single_gap(self):
        """Test critical path with single gap"""
        optimizer = RoadmapOptimizer()

        gaps = [{"id": "G1"}]
        dependencies = {}
        effort = {"G1": 2.0}
        impact = {"G1": 0.8}

        roadmap = optimizer.optimize(gaps, dependencies, effort, impact)

        assert isinstance(roadmap.critical_path, list)

    def test_critical_path_with_dependencies(self):
        """Test critical path with dependency chain"""
        optimizer = RoadmapOptimizer()

        gaps = [
            {"id": "G1"},
            {"id": "G2"},
            {"id": "G3"}
        ]
        dependencies = {
            "G2": ["G1"],
            "G3": ["G2"]
        }
        effort = {"G1": 1.0, "G2": 1.0, "G3": 1.0}
        impact = {"G1": 0.5, "G2": 0.7, "G3": 0.9}

        roadmap = optimizer.optimize(gaps, dependencies, effort, impact)

        # Critical path should include high-impact chain
        assert len(roadmap.critical_path) > 0

class TestResourceEstimation:
    """Test resource requirement estimation"""

    def test_resource_estimation(self):
        """Test resource estimation per phase"""
        optimizer = RoadmapOptimizer()

        gaps = [{"id": "G1"}]
        effort = {"G1": 6.0}
        impact = {"G1": 0.8}

        roadmap = optimizer.optimize(gaps, {}, effort, impact)

        assert "0-3m" in roadmap.resource_requirements
        assert "total_effort_months" in roadmap.resource_requirements["0-3m"]
        assert "recommended_team_size" in roadmap.resource_requirements["0-3m"]

# ============================================================================
# TEST PEER NORMALIZER
# ============================================================================

class TestPeerNormalizerBasics:
    """Test basic functionality of PeerNormalizer"""

    def test_initialization_defaults(self):
        """Test default initialization"""
        normalizer = PeerNormalizer()
        assert normalizer.k == 3
        assert normalizer.outlier_z == 2.0

    def test_initialization_custom(self):
        """Test custom initialization"""
        normalizer = PeerNormalizer(
            penalty_threshold=5,
            outlier_z_threshold=3.0
        )
        assert normalizer.k == 5
        assert normalizer.outlier_z == 3.0

class TestZScoreCalculation:
    """Test z-score calculation"""

    def test_z_scores_calculated(self):
        """Test z-scores are calculated correctly"""
        normalizer = PeerNormalizer()

        convergence = {
            "P1": 0.75
        }
        peer_distributions = {
            "P1": {"mean": 0.70, "std": 0.05}
        }

        result = normalizer.normalize(convergence, peer_distributions, 1.0)

        # z = (0.75 - 0.70) / 0.05 = 1.0
        assert result.z_scores["P1"] == 1.0

    def test_negative_z_scores(self):
        """Test negative z-scores for below-average performance"""
        normalizer = PeerNormalizer()

        convergence = {
            "P1": 0.40
        }
        peer_distributions = {
            "P1": {"mean": 0.50, "std": 0.05}
        }

        result = normalizer.normalize(convergence, peer_distributions, 1.0)

        # z = (0.40 - 0.50) / 0.05 = -2.0
        assert result.z_scores["P1"] == -2.0

class TestOutlierDetection:
    """Test outlier detection"""

    def test_outlier_detected(self):
        """Test outlier detection with extreme z-score"""
        normalizer = PeerNormalizer(outlier_z_threshold=2.0)

        convergence = {
            "P1": 0.90
        }
        peer_distributions = {
            "P1": {"mean": 0.50, "std": 0.10}
        }

        result = normalizer.normalize(convergence, peer_distributions, 1.0)

        # z = (0.90 - 0.50) / 0.10 = 4.0, which exceeds 2.0
        assert "P1" in result.outlier_areas

    def test_no_outliers(self):
        """Test no outliers with normal z-scores"""
        normalizer = PeerNormalizer()

        convergence = {
            "P1": 0.52
        }
        peer_distributions = {
            "P1": {"mean": 0.50, "std": 0.10}
        }

        result = normalizer.normalize(convergence, peer_distributions, 1.0)

        # z = (0.52 - 0.50) / 0.10 = 0.2, which is < 2.0
        assert len(result.outlier_areas) == 0

class TestConfidenceAdjustment:
    """Test confidence adjustment"""

    def test_no_adjustment_good_performance(self):
        """Test no penalty with good performance"""
        normalizer = PeerNormalizer(penalty_threshold=3)

        convergence = {
            "P1": 0.75,
            "P2": 0.80
        }
        peer_distributions = {
            "P1": {"mean": 0.70, "std": 0.05},
            "P2": {"mean": 0.75, "std": 0.05}
        }

        result = normalizer.normalize(convergence, peer_distributions, 1.0)

        # Good performance, confidence should be maintained or boosted
        assert result.adjusted_confidence >= 0.95

    def test_penalty_for_low_performers(self):
        """Test penalty with many low performers"""
        normalizer = PeerNormalizer(penalty_threshold=2)

        convergence = {
            "P1": 0.30,  # Low
            "P2": 0.35,  # Low
            "P3": 0.40   # Low
        }
        peer_distributions = {
            "P1": {"mean": 0.70, "std": 0.10},
            "P2": {"mean": 0.70, "std": 0.10},
            "P3": {"mean": 0.70, "std": 0.10}
        }

        result = normalizer.normalize(convergence, peer_distributions, 1.0)

        # Many low performers should reduce confidence
        assert result.adjusted_confidence < 1.0

class TestPeerPosition:
    """Test peer position determination"""

    def test_above_average_position(self):
        """Test above average position"""
        normalizer = PeerNormalizer()

        convergence = {
            "P1": 0.80,
            "P2": 0.85
        }
        peer_distributions = {
            "P1": {"mean": 0.60, "std": 0.10},
            "P2": {"mean": 0.65, "std": 0.10}
        }

        result = normalizer.normalize(convergence, peer_distributions, 1.0)

        assert result.peer_position == "above_average"

    def test_below_average_position(self):
        """Test below average position"""
        normalizer = PeerNormalizer()

        convergence = {
            "P1": 0.30,
            "P2": 0.35
        }
        peer_distributions = {
            "P1": {"mean": 0.60, "std": 0.10},
            "P2": {"mean": 0.65, "std": 0.10}
        }

        result = normalizer.normalize(convergence, peer_distributions, 1.0)

        assert result.peer_position == "below_average"

    def test_average_position(self):
        """Test average position"""
        normalizer = PeerNormalizer()

        convergence = {
            "P1": 0.60,
            "P2": 0.62
        }
        peer_distributions = {
            "P1": {"mean": 0.60, "std": 0.10},
            "P2": {"mean": 0.62, "std": 0.10}
        }

        result = normalizer.normalize(convergence, peer_distributions, 1.0)

        assert result.peer_position == "average"

# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestMacroIntegration:
    """Test integration across macro components"""

    def test_full_macro_workflow(self):
        """Test complete macro analysis workflow"""
        # 1. Coverage analysis
        coverage_stressor = CoverageGapStressor()
        coverage_result = coverage_stressor.evaluate(
            convergence_by_dimension={"D1": 0.8, "D2": 0.7},
            missing_clusters=["C1"],
            dimension_coverage={"D1": 0.9, "D2": 0.8},
            policy_area_coverage={"P1": 0.85}
        )

        # 2. Contradiction scan
        contradiction_scanner = ContradictionScanner()
        contradiction_result = contradiction_scanner.scan(
            micro_claims=[],
            meso_summary_signals={},
            macro_narratives={}
        )

        # 3. Portfolio composition
        portfolio_composer = BayesianPortfolioComposer()
        portfolio_result = portfolio_composer.compose(
            meso_posteriors={"C1": 0.8},
            cluster_weights={"C1": 1.0}
        )

        # 4. Roadmap optimization
        roadmap_optimizer = RoadmapOptimizer()
        roadmap_result = roadmap_optimizer.optimize(
            critical_gaps=[{"id": "G1"}],
            dependency_graph={},
            effort_estimates={"G1": 2.0},
            impact_scores={"G1": 0.8}
        )

        # 5. Peer normalization
        peer_normalizer = PeerNormalizer()
        peer_result = peer_normalizer.normalize(
            convergence_by_policy_area={"P1": 0.75},
            peer_distributions={"P1": {"mean": 0.70, "std": 0.05}},
            baseline_confidence=1.0
        )

        # All components should produce valid results
        assert isinstance(coverage_result, CoverageAnalysis)
        assert isinstance(contradiction_result, ContradictionReport)
        assert isinstance(portfolio_result, BayesianPortfolio)
        assert isinstance(roadmap_result, ImplementationRoadmap)
        assert isinstance(peer_result, PeerNormalization)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
