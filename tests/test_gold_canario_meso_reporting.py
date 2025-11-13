#!/usr/bin/env python3
"""
GOLD-CANARIO Comprehensive Tests: Meso Reporting
=================================================

Tests for all 4 meso-level analysis functions:
1. analyze_policy_dispersion - Dispersion analytics with CV, gap, Gini
2. reconcile_cross_metrics - Metric validation against macro reference
3. compose_cluster_posterior - Bayesian roll-up from micro posteriors
4. calibrate_against_peers - Peer comparison with IQR and outliers
"""

import pytest

from saaaaaa.analysis.meso_cluster_analysis import (
    analyze_policy_dispersion,
    calibrate_against_peers,
    compose_cluster_posterior,
    reconcile_cross_metrics,
)

class TestAnalyzePolicyDispersion:
    """Test analyze_policy_dispersion function"""

    def test_concentrated_dispersion(self):
        """Test concentrated policy area scores"""
        policy_scores = {
            "P1": 0.80,
            "P2": 0.82,
            "P3": 0.81,
            "P4": 0.79
        }
        peer_stats = {
            "cv_median": 0.15,
            "gap_median": 0.10
        }
        thresholds = {
            "cv_warn": 0.20,
            "cv_fail": 0.30,
            "gap_warn": 0.15,
            "gap_fail": 0.25
        }

        result, narrative = analyze_policy_dispersion(
            policy_scores, peer_stats, thresholds
        )

        assert result['class'] == "Concentrado"
        assert result['cv'] < 0.05
        assert result['penalty'] == 0.0
        assert "Concentrado" in narrative or "concentración" in narrative.lower()

    def test_dispersed_scores(self):
        """Test dispersed policy area scores"""
        policy_scores = {
            "P1": 0.3,
            "P2": 0.8,
            "P3": 0.5,
            "P4": 0.9
        }
        peer_stats = {
            "cv_median": 0.15,
            "gap_median": 0.20
        }
        thresholds = {
            "cv_warn": 0.20,
            "cv_fail": 0.30,
            "gap_warn": 0.25,
            "gap_fail": 0.40
        }

        result, narrative = analyze_policy_dispersion(
            policy_scores, peer_stats, thresholds
        )

        assert result['class'] in ["Moderado", "Disperso", "Crítico"]
        assert result['max_gap'] > 0.5
        assert result['penalty'] > 0.0
        assert "brecha" in narrative.lower() or "gap" in narrative.lower()

    def test_critical_dispersion(self):
        """Test critical dispersion scenario"""
        policy_scores = {
            "P1": 0.1,
            "P2": 0.9,
            "P3": 0.2,
            "P4": 1.0
        }
        peer_stats = {
            "cv_median": 0.10,
            "gap_median": 0.15
        }
        thresholds = {
            "cv_warn": 0.15,
            "cv_fail": 0.20,
            "gap_warn": 0.20,
            "gap_fail": 0.30
        }

        result, narrative = analyze_policy_dispersion(
            policy_scores, peer_stats, thresholds
        )

        assert result['class'] == "Crítico"
        assert result['cv'] > 0.5
        assert result['max_gap'] > 0.8
        assert result['penalty'] > 0.3
        assert "Crítico" in narrative or "crítico" in narrative.lower()

    def test_gini_calculation(self):
        """Test Gini coefficient calculation"""
        policy_scores = {
            "P1": 0.5,
            "P2": 0.5,
            "P3": 0.5
        }
        peer_stats = {}
        thresholds = {}

        result, narrative = analyze_policy_dispersion(
            policy_scores, peer_stats, thresholds
        )

        # Equal scores should have Gini near 0
        assert result['gini'] < 0.1
        assert 'gini' in result

    def test_normalization_projection(self):
        """Test normalized projection uplift"""
        policy_scores = {
            "P1": 0.2,
            "P2": 0.8,
            "P3": 0.5,
            "P4": 0.9
        }
        peer_stats = {}
        thresholds = {}

        result, narrative = analyze_policy_dispersion(
            policy_scores, peer_stats, thresholds
        )

        assert 'normalized_projection' in result
        assert 'adjusted_cv' in result['normalized_projection']
        assert 'mean_uplift' in result['normalized_projection']
        assert result['normalized_projection']['mean_uplift'] >= 0.0

    def test_empty_policy_scores(self):
        """Test with empty policy scores"""
        policy_scores = {}
        peer_stats = {}
        thresholds = {}

        result, narrative = analyze_policy_dispersion(
            policy_scores, peer_stats, thresholds
        )

        assert result['cv'] == 0.0
        assert result['max_gap'] == 0.0
        assert isinstance(narrative, str)

    def test_single_policy_score(self):
        """Test with single policy score"""
        policy_scores = {"P1": 0.7}
        peer_stats = {}
        thresholds = {}

        result, narrative = analyze_policy_dispersion(
            policy_scores, peer_stats, thresholds
        )

        assert result['cv'] == 0.0  # No variance with one value
        assert result['max_gap'] == 0.0

class TestReconcileCrossMetrics:
    """Test reconcile_cross_metrics function"""

    def test_perfect_reconciliation(self):
        """Test metrics that perfectly match macro reference"""
        aggregated = [
            {
                "metric_id": "M1",
                "value": 100.0,
                "unit": "USD",
                "period": "2024-Q1",
                "entity": "Entity1"
            }
        ]
        macro_json = {
            "metrics": {
                "M1": {
                    "unit": "USD",
                    "period": "2024-Q1",
                    "entities": ["Entity1"],
                    "range": (0.0, 200.0)
                }
            },
            "unit_crosswalk": {}
        }

        result = reconcile_cross_metrics(aggregated, macro_json)

        assert len(result['violations']) == 0
        assert result['reconciled_confidence'] == 1.0
        assert len(result['metrics_validated']) == 1

    def test_unit_mismatch(self):
        """Test unit mismatch detection"""
        aggregated = [
            {
                "metric_id": "M1",
                "value": 100.0,
                "unit": "EUR",
                "period": "2024-Q1",
                "entity": "Entity1"
            }
        ]
        macro_json = {
            "metrics": {
                "M1": {
                    "unit": "USD",
                    "period": "2024-Q1",
                    "entities": ["Entity1"],
                    "range": (0.0, 200.0)
                }
            },
            "unit_crosswalk": {}  # No conversion available
        }

        result = reconcile_cross_metrics(aggregated, macro_json)

        assert len(result['violations']) > 0
        assert any(v['unit_mismatch'] for v in result['violations'])
        assert result['reconciled_confidence'] < 1.0

    def test_unit_conversion(self):
        """Test successful unit conversion"""
        aggregated = [
            {
                "metric_id": "M1",
                "value": 100.0,
                "unit": "EUR",
                "period": "2024-Q1",
                "entity": "Entity1"
            }
        ]
        macro_json = {
            "metrics": {
                "M1": {
                    "unit": "USD",
                    "period": "2024-Q1",
                    "entities": ["Entity1"],
                    "range": (0.0, 200.0)
                }
            },
            "unit_crosswalk": {
                "EUR": {"USD": 1.1}  # 1 EUR = 1.1 USD
            }
        }

        result = reconcile_cross_metrics(aggregated, macro_json)

        # Should convert successfully
        assert len(result['violations']) == 0
        assert result['metrics_validated'][0]['value'] == 110.0
        assert result['metrics_validated'][0]['unit'] == "USD"

    def test_stale_period(self):
        """Test stale period detection"""
        aggregated = [
            {
                "metric_id": "M1",
                "value": 100.0,
                "unit": "USD",
                "period": "2023-Q1",
                "entity": "Entity1"
            }
        ]
        macro_json = {
            "metrics": {
                "M1": {
                    "unit": "USD",
                    "period": "2024-Q1",
                    "entities": ["Entity1"],
                    "range": (0.0, 200.0)
                }
            },
            "unit_crosswalk": {}
        }

        result = reconcile_cross_metrics(aggregated, macro_json)

        assert len(result['violations']) > 0
        assert any(v['stale_period'] for v in result['violations'])

    def test_entity_misalignment(self):
        """Test entity misalignment detection"""
        aggregated = [
            {
                "metric_id": "M1",
                "value": 100.0,
                "unit": "USD",
                "period": "2024-Q1",
                "entity": "WrongEntity"
            }
        ]
        macro_json = {
            "metrics": {
                "M1": {
                    "unit": "USD",
                    "period": "2024-Q1",
                    "entities": ["Entity1", "Entity2"],
                    "range": (0.0, 200.0)
                }
            },
            "unit_crosswalk": {}
        }

        result = reconcile_cross_metrics(aggregated, macro_json)

        assert len(result['violations']) > 0
        assert any(v['entity_misalignment'] for v in result['violations'])

    def test_out_of_range(self):
        """Test out of range detection"""
        aggregated = [
            {
                "metric_id": "M1",
                "value": 300.0,  # Above range
                "unit": "USD",
                "period": "2024-Q1",
                "entity": "Entity1"
            }
        ]
        macro_json = {
            "metrics": {
                "M1": {
                    "unit": "USD",
                    "period": "2024-Q1",
                    "entities": ["Entity1"],
                    "range": (0.0, 200.0)
                }
            },
            "unit_crosswalk": {}
        }

        result = reconcile_cross_metrics(aggregated, macro_json)

        assert len(result['violations']) > 0
        assert any(v['out_of_range'] for v in result['violations'])

    def test_multiple_metrics_mixed_violations(self):
        """Test multiple metrics with mixed violations"""
        aggregated = [
            {
                "metric_id": "M1",
                "value": 100.0,
                "unit": "USD",
                "period": "2024-Q1",
                "entity": "Entity1"
            },
            {
                "metric_id": "M2",
                "value": 50.0,
                "unit": "EUR",
                "period": "2023-Q1",
                "entity": "WrongEntity"
            }
        ]
        macro_json = {
            "metrics": {
                "M1": {
                    "unit": "USD",
                    "period": "2024-Q1",
                    "entities": ["Entity1"],
                    "range": (0.0, 200.0)
                },
                "M2": {
                    "unit": "USD",
                    "period": "2024-Q1",
                    "entities": ["Entity2"],
                    "range": (0.0, 100.0)
                }
            },
            "unit_crosswalk": {}
        }

        result = reconcile_cross_metrics(aggregated, macro_json)

        assert len(result['metrics_validated']) == 2
        # M1 should be clean, M2 should have violations
        assert result['reconciled_confidence'] < 1.0

class TestComposeClusterPosterior:
    """Test compose_cluster_posterior function"""

    def test_simple_composition(self):
        """Test simple posterior composition"""
        micro_posteriors = [0.7, 0.8, 0.75]

        result, narrative = compose_cluster_posterior(micro_posteriors)

        assert 'prior_meso' in result
        assert 'posterior_meso' in result
        assert 'uncertainty_index' in result
        assert 0.0 <= result['prior_meso'] <= 1.0
        assert 0.0 <= result['posterior_meso'] <= 1.0
        assert "prior meso" in narrative.lower()

    def test_weighted_composition(self):
        """Test weighted posterior composition"""
        micro_posteriors = [0.5, 0.8, 0.9]
        weights = [1.0, 2.0, 1.0]  # Middle value weighted more

        result, narrative = compose_cluster_posterior(
            micro_posteriors, weighting_trace=weights
        )

        # Weighted mean should favor 0.8
        assert result['prior_meso'] > 0.65
        assert result['prior_meso'] < 0.75

    def test_penalty_application(self):
        """Test reconciliation penalty application"""
        micro_posteriors = [0.8, 0.85, 0.82]
        penalties = {
            "dispersion_penalty": 0.1,
            "coverage_penalty": 0.05,
            "reconciliation_penalty": 0.08
        }

        result, narrative = compose_cluster_posterior(
            micro_posteriors, reconciliation_penalties=penalties
        )

        assert result['posterior_meso'] < result['prior_meso']
        assert result['penalties']['dispersion_penalty'] == 0.1
        assert result['penalties']['coverage_penalty'] == 0.05
        assert result['penalties']['reconciliation_penalty'] == 0.08
        assert "penalizaciones" in narrative.lower()

    def test_high_variance_posteriors(self):
        """Test with high variance in posteriors"""
        micro_posteriors = [0.1, 0.9, 0.2, 0.8]

        result, narrative = compose_cluster_posterior(micro_posteriors)

        assert result['uncertainty_index'] > 0.2
        assert "incertidumbre" in narrative.lower()

    def test_uniform_posteriors(self):
        """Test with uniform posteriors (low variance)"""
        micro_posteriors = [0.7, 0.7, 0.7, 0.7]

        result, narrative = compose_cluster_posterior(micro_posteriors)

        assert result['uncertainty_index'] < 0.01
        assert result['prior_meso'] == 0.7

    def test_empty_posteriors_raises_error(self):
        """Test that empty posteriors raise ValueError"""
        with pytest.raises(ValueError, match="cannot be empty"):
            compose_cluster_posterior([])

    def test_weight_mismatch_raises_error(self):
        """Test that mismatched weights raise ValueError"""
        with pytest.raises(ValueError, match="must match"):
            compose_cluster_posterior([0.7, 0.8], weighting_trace=[1.0])

    def test_negative_weights_raise_error(self):
        """Test that negative weights raise ValueError"""
        with pytest.raises(ValueError, match="non-negative"):
            compose_cluster_posterior([0.7, 0.8], weighting_trace=[-1.0, 1.0])

    def test_extreme_penalties(self):
        """Test with extreme penalties"""
        micro_posteriors = [0.9, 0.85]
        penalties = {
            "dispersion_penalty": 0.5,
            "coverage_penalty": 0.4,
            "reconciliation_penalty": 0.3
        }

        result, narrative = compose_cluster_posterior(
            micro_posteriors, reconciliation_penalties=penalties
        )

        # Posterior should be significantly lower than prior
        assert result['posterior_meso'] < result['prior_meso'] * 0.5

class TestCalibrateAgainstPeers:
    """Test calibrate_against_peers function"""

    def test_all_within_iqr(self):
        """Test all scores within inter-quartile range"""
        policy_scores = {
            "P1": 0.55,
            "P2": 0.60,
            "P3": 0.58
        }
        peer_context = {
            "P1": {"median": 0.55, "p25": 0.50, "p75": 0.60},
            "P2": {"median": 0.60, "p25": 0.55, "p75": 0.65},
            "P3": {"median": 0.58, "p25": 0.53, "p75": 0.63}
        }

        result, narrative = calibrate_against_peers(policy_scores, peer_context)

        assert all(pos == "within" for pos in result['area_positions'].values())
        assert all(not is_outlier for is_outlier in result['outliers'].values())
        assert "dentro" in narrative.lower() or "within" in narrative.lower()

    def test_above_peer_performance(self):
        """Test scores above peer ranges"""
        policy_scores = {
            "P1": 0.85,
            "P2": 0.90
        }
        peer_context = {
            "P1": {"median": 0.60, "p25": 0.50, "p75": 0.70},
            "P2": {"median": 0.65, "p25": 0.55, "p75": 0.75}
        }

        result, narrative = calibrate_against_peers(policy_scores, peer_context)

        assert all(pos == "above" for pos in result['area_positions'].values())
        assert "por encima" in narrative.lower() or "above" in narrative.lower()

    def test_below_peer_performance(self):
        """Test scores below peer ranges"""
        policy_scores = {
            "P1": 0.30,
            "P2": 0.35
        }
        peer_context = {
            "P1": {"median": 0.60, "p25": 0.50, "p75": 0.70},
            "P2": {"median": 0.65, "p25": 0.55, "p75": 0.75}
        }

        result, narrative = calibrate_against_peers(policy_scores, peer_context)

        assert all(pos == "below" for pos in result['area_positions'].values())
        assert "por debajo" in narrative.lower() or "below" in narrative.lower()

    def test_outlier_detection(self):
        """Test Tukey outlier detection"""
        policy_scores = {
            "P1": 0.95  # Way above IQR
        }
        peer_context = {
            "P1": {"median": 0.50, "p25": 0.45, "p75": 0.55}
        }

        result, narrative = calibrate_against_peers(policy_scores, peer_context)

        assert result['outliers']['P1'] is True
        assert "outliers" in narrative.lower()

    def test_mixed_performance(self):
        """Test mixed performance across areas"""
        policy_scores = {
            "P1": 0.85,  # Above
            "P2": 0.60,  # Within
            "P3": 0.35   # Below
        }
        peer_context = {
            "P1": {"median": 0.60, "p25": 0.50, "p75": 0.70},
            "P2": {"median": 0.60, "p25": 0.55, "p75": 0.65},
            "P3": {"median": 0.60, "p25": 0.50, "p75": 0.70}
        }

        result, narrative = calibrate_against_peers(policy_scores, peer_context)

        assert result['area_positions']['P1'] == "above"
        assert result['area_positions']['P2'] == "within"
        assert result['area_positions']['P3'] == "below"
        assert "heterogéneo" in narrative.lower()

    def test_missing_peer_context(self):
        """Test handling of missing peer context"""
        policy_scores = {
            "P1": 0.70,
            "P2": 0.65
        }
        peer_context = {
            "P1": {"median": 0.60, "p25": 0.50, "p75": 0.70}
            # P2 missing
        }

        result, narrative = calibrate_against_peers(policy_scores, peer_context)

        # Should handle gracefully
        assert 'P1' in result['area_positions']
        assert 'P2' in result['area_positions']

    def test_empty_policy_scores(self):
        """Test with empty policy scores"""
        policy_scores = {}
        peer_context = {}

        result, narrative = calibrate_against_peers(policy_scores, peer_context)

        assert result['area_positions'] == {}
        assert result['outliers'] == {}
        assert isinstance(narrative, str)

class TestEdgeCases:
    """Test edge cases across all meso functions"""

    def test_dispersion_single_high_value(self):
        """Test dispersion with outlier single high value"""
        policy_scores = {
            "P1": 0.5,
            "P2": 0.5,
            "P3": 1.0  # Outlier
        }

        result, _ = analyze_policy_dispersion(policy_scores, {}, {})

        assert result['max_gap'] == 0.5
        assert result['gini'] > 0.1

    def test_compose_all_zero_posteriors(self):
        """Test composition with all zero posteriors"""
        micro_posteriors = [0.0, 0.0, 0.0]

        result, _ = compose_cluster_posterior(micro_posteriors)

        assert result['prior_meso'] == 0.0
        assert result['posterior_meso'] == 0.0

    def test_compose_all_one_posteriors(self):
        """Test composition with all one posteriors"""
        micro_posteriors = [1.0, 1.0, 1.0]

        result, _ = compose_cluster_posterior(micro_posteriors)

        assert result['prior_meso'] == 1.0
        assert result['posterior_meso'] == 1.0

    def test_reconcile_no_macro_reference(self):
        """Test reconciliation with no macro reference"""
        aggregated = [
            {
                "metric_id": "M1",
                "value": 100.0,
                "unit": "USD",
                "period": "2024-Q1",
                "entity": "Entity1"
            }
        ]
        macro_json = {}  # No reference

        result = reconcile_cross_metrics(aggregated, macro_json)

        # Should not crash, should validate metrics
        assert len(result['metrics_validated']) == 1

class TestNarrativeQuality:
    """Test narrative quality and content"""

    def test_dispersion_narrative_structure(self):
        """Test dispersion narrative has expected structure"""
        policy_scores = {"P1": 0.5, "P2": 0.6, "P3": 0.7}

        _, narrative = analyze_policy_dispersion(policy_scores, {}, {})

        lines = narrative.split('\n')
        # Should have multiple lines
        assert len(lines) >= 4
        assert len(narrative) > 100

    def test_composition_narrative_mentions_key_concepts(self):
        """Test composition narrative mentions key concepts"""
        micro_posteriors = [0.7, 0.8]

        _, narrative = compose_cluster_posterior(micro_posteriors)

        assert "prior" in narrative.lower()
        assert "posterior" in narrative.lower()
        assert any(word in narrative.lower() for word in ["media", "average", "ponderada"])

    def test_peer_calibration_narrative_comprehensive(self):
        """Test peer calibration narrative is comprehensive"""
        policy_scores = {"P1": 0.7, "P2": 0.8}
        peer_context = {
            "P1": {"median": 0.6, "p25": 0.5, "p75": 0.7},
            "P2": {"median": 0.6, "p25": 0.5, "p75": 0.7}
        }

        _, narrative = calibrate_against_peers(policy_scores, peer_context)

        # Should mention IQR, outliers, and positioning
        assert len(narrative) > 200
        assert any(word in narrative.lower() for word in ["iqr", "cuartil", "quartile"])

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
