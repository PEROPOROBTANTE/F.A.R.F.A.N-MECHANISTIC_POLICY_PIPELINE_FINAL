#!/usr/bin/env python3
"""
GOLD-CANARIO Comprehensive Tests: Micro Reporting - Bayesian Posterior Explainer
=================================================================================

Tests for BayesianPosteriorExplainer including:
- Signal ranking by marginal impact
- Discarded signal identification
- Test type justification
- Anti-miracle cap application
- Robustness narrative generation
- JSON export
"""

import pytest

from saaaaaa.processing.micro_prompts import (
    BayesianPosteriorExplainer,
    PosteriorJustification,
    Signal,
)

class TestBayesianPosteriorExplainerBasics:
    """Test basic functionality of BayesianPosteriorExplainer"""

    def test_explainer_initialization_defaults(self):
        """Test explainer initializes with default values"""
        explainer = BayesianPosteriorExplainer()
        assert explainer.anti_miracle_cap == 0.95

    def test_explainer_initialization_custom(self):
        """Test explainer initializes with custom cap"""
        explainer = BayesianPosteriorExplainer(anti_miracle_cap=0.90)
        assert explainer.anti_miracle_cap == 0.90

    def test_empty_signals_explanation(self):
        """Test explanation with no signals"""
        explainer = BayesianPosteriorExplainer()

        result = explainer.explain(
            prior=0.5,
            signals=[],
            posterior=0.5
        )

        assert isinstance(result, PosteriorJustification)
        assert result.prior == 0.5
        assert result.posterior == 0.5
        assert len(result.signals_ranked) == 0
        assert not result.anti_miracle_cap_applied

class TestSignalRanking:
    """Test signal ranking by marginal impact"""

    def test_single_signal_ranking(self):
        """Test ranking with single signal"""
        explainer = BayesianPosteriorExplainer()

        signal = Signal(
            test_type="Smoking-Gun",
            likelihood=0.8,
            weight=1.0,
            raw_evidence_id="E1",
            reconciled=True,
            delta_posterior=0.3
        )

        result = explainer.explain(
            prior=0.5,
            signals=[signal],
            posterior=0.8
        )

        assert len(result.signals_ranked) == 1
        assert result.signals_ranked[0]['test_type'] == "Smoking-Gun"
        assert result.signals_ranked[0]['delta_posterior'] == 0.3
        assert result.signals_ranked[0]['kept'] is True

    def test_multiple_signals_ranking_order(self):
        """Test signals are ranked by absolute marginal impact"""
        explainer = BayesianPosteriorExplainer()

        signals = [
            Signal(
                test_type="Straw-in-Wind",
                likelihood=0.6,
                weight=1.0,
                raw_evidence_id="E1",
                reconciled=True,
                delta_posterior=0.1
            ),
            Signal(
                test_type="Smoking-Gun",
                likelihood=0.9,
                weight=1.0,
                raw_evidence_id="E2",
                reconciled=True,
                delta_posterior=0.4
            ),
            Signal(
                test_type="Hoop",
                likelihood=0.7,
                weight=1.0,
                raw_evidence_id="E3",
                reconciled=True,
                delta_posterior=0.25
            )
        ]

        result = explainer.explain(
            prior=0.4,
            signals=signals,
            posterior=0.8
        )

        # Should be ranked by |delta|: 0.4, 0.25, 0.1
        assert len(result.signals_ranked) == 3
        assert result.signals_ranked[0]['delta_posterior'] == 0.4
        assert result.signals_ranked[0]['test_type'] == "Smoking-Gun"
        assert result.signals_ranked[1]['delta_posterior'] == 0.25
        assert result.signals_ranked[1]['test_type'] == "Hoop"
        assert result.signals_ranked[2]['delta_posterior'] == 0.1
        assert result.signals_ranked[2]['test_type'] == "Straw-in-Wind"

    def test_negative_delta_ranking(self):
        """Test ranking with negative deltas (should rank by absolute value)"""
        explainer = BayesianPosteriorExplainer()

        signals = [
            Signal(
                test_type="Test1",
                likelihood=0.5,
                weight=1.0,
                raw_evidence_id="E1",
                reconciled=True,
                delta_posterior=0.2
            ),
            Signal(
                test_type="Test2",
                likelihood=0.5,
                weight=1.0,
                raw_evidence_id="E2",
                reconciled=True,
                delta_posterior=-0.3  # Negative impact
            )
        ]

        result = explainer.explain(
            prior=0.6,
            signals=signals,
            posterior=0.5
        )

        # Should rank by |delta|: |-0.3| > |0.2|
        assert result.signals_ranked[0]['delta_posterior'] == -0.3
        assert result.signals_ranked[1]['delta_posterior'] == 0.2

class TestDiscardedSignals:
    """Test identification of discarded signals"""

    def test_all_signals_reconciled(self):
        """Test when all signals are reconciled"""
        explainer = BayesianPosteriorExplainer()

        signals = [
            Signal(
                test_type="Smoking-Gun",
                likelihood=0.8,
                weight=1.0,
                raw_evidence_id="E1",
                reconciled=True,
                delta_posterior=0.3
            )
        ]

        result = explainer.explain(
            prior=0.5,
            signals=signals,
            posterior=0.8
        )

        assert len(result.discarded_signals) == 0

    def test_some_signals_discarded(self):
        """Test identification of discarded signals"""
        explainer = BayesianPosteriorExplainer()

        signals = [
            Signal(
                test_type="Smoking-Gun",
                likelihood=0.8,
                weight=1.0,
                raw_evidence_id="E1",
                reconciled=True,
                delta_posterior=0.3
            ),
            Signal(
                test_type="Hoop",
                likelihood=0.7,
                weight=1.0,
                raw_evidence_id="E2",
                reconciled=False,  # Discarded
                delta_posterior=0.2
            ),
            Signal(
                test_type="Straw-in-Wind",
                likelihood=0.6,
                weight=1.0,
                raw_evidence_id="E3",
                reconciled=False,  # Discarded
                delta_posterior=0.1
            )
        ]

        result = explainer.explain(
            prior=0.5,
            signals=signals,
            posterior=0.8
        )

        assert len(result.discarded_signals) == 2
        assert result.discarded_signals[0]['kept'] is False
        assert result.discarded_signals[1]['kept'] is False

    def test_discarded_signals_not_in_ranked(self):
        """Test discarded signals are not in ranked list"""
        explainer = BayesianPosteriorExplainer()

        signals = [
            Signal(
                test_type="Smoking-Gun",
                likelihood=0.8,
                weight=1.0,
                raw_evidence_id="E1",
                reconciled=True,
                delta_posterior=0.3
            ),
            Signal(
                test_type="Hoop",
                likelihood=0.7,
                weight=1.0,
                raw_evidence_id="E2",
                reconciled=False,
                delta_posterior=0.4  # Higher delta but discarded
            )
        ]

        result = explainer.explain(
            prior=0.5,
            signals=signals,
            posterior=0.8
        )

        # Only reconciled signal should be in ranked list
        assert len(result.signals_ranked) == 1
        assert result.signals_ranked[0]['evidence_id'] == "E1"

class TestTypeJustification:
    """Test test type justification generation"""

    def test_hoop_test_justification(self):
        """Test justification for Hoop test"""
        explainer = BayesianPosteriorExplainer()

        signal = Signal(
            test_type="Hoop",
            likelihood=0.7,
            weight=1.0,
            raw_evidence_id="E1",
            reconciled=True,
            delta_posterior=0.3
        )

        result = explainer.explain(
            prior=0.5,
            signals=[signal],
            posterior=0.8
        )

        reason = result.signals_ranked[0]['reason']
        assert "Hoop" in reason or "Necessary" in reason
        assert "Rank 1" in reason

    def test_smoking_gun_justification(self):
        """Test justification for Smoking-Gun test"""
        explainer = BayesianPosteriorExplainer()

        signal = Signal(
            test_type="Smoking-Gun",
            likelihood=0.9,
            weight=1.0,
            raw_evidence_id="E1",
            reconciled=True,
            delta_posterior=0.4
        )

        result = explainer.explain(
            prior=0.5,
            signals=[signal],
            posterior=0.9
        )

        reason = result.signals_ranked[0]['reason']
        assert "Smoking-Gun" in reason or "Sufficient" in reason

    def test_doubly_decisive_justification(self):
        """Test justification for Doubly-Decisive test"""
        explainer = BayesianPosteriorExplainer()

        signal = Signal(
            test_type="Doubly-Decisive",
            likelihood=0.95,
            weight=1.0,
            raw_evidence_id="E1",
            reconciled=True,
            delta_posterior=0.45
        )

        result = explainer.explain(
            prior=0.5,
            signals=[signal],
            posterior=0.95
        )

        reason = result.signals_ranked[0]['reason']
        assert "Doubly-Decisive" in reason or "necessary and sufficient" in reason.lower()

    def test_straw_in_wind_justification(self):
        """Test justification for Straw-in-Wind test"""
        explainer = BayesianPosteriorExplainer()

        signal = Signal(
            test_type="Straw-in-Wind",
            likelihood=0.6,
            weight=1.0,
            raw_evidence_id="E1",
            reconciled=True,
            delta_posterior=0.1
        )

        result = explainer.explain(
            prior=0.5,
            signals=[signal],
            posterior=0.6
        )

        reason = result.signals_ranked[0]['reason']
        assert "Straw-in-Wind" in reason or "Weak" in reason or "marginal" in reason.lower()

class TestAntiMiracleCap:
    """Test anti-miracle cap application"""

    def test_no_cap_applied_below_threshold(self):
        """Test no cap when posterior below threshold"""
        explainer = BayesianPosteriorExplainer(anti_miracle_cap=0.95)

        signal = Signal(
            test_type="Smoking-Gun",
            likelihood=0.8,
            weight=1.0,
            raw_evidence_id="E1",
            reconciled=True,
            delta_posterior=0.3
        )

        result = explainer.explain(
            prior=0.5,
            signals=[signal],
            posterior=0.8  # Below cap
        )

        assert not result.anti_miracle_cap_applied
        assert result.cap_delta == 0.0
        assert result.posterior == 0.8

    def test_cap_applied_above_threshold(self):
        """Test cap applied when posterior exceeds threshold"""
        explainer = BayesianPosteriorExplainer(anti_miracle_cap=0.95)

        signal = Signal(
            test_type="Smoking-Gun",
            likelihood=0.9,
            weight=1.0,
            raw_evidence_id="E1",
            reconciled=True,
            delta_posterior=0.5
        )

        result = explainer.explain(
            prior=0.5,
            signals=[signal],
            posterior=0.98  # Above cap
        )

        assert result.anti_miracle_cap_applied
        assert result.cap_delta == 0.03  # 0.98 - 0.95
        assert result.posterior == 0.95  # Capped

    def test_cap_at_boundary(self):
        """Test behavior at exact cap boundary"""
        explainer = BayesianPosteriorExplainer(anti_miracle_cap=0.95)

        signal = Signal(
            test_type="Smoking-Gun",
            likelihood=0.85,
            weight=1.0,
            raw_evidence_id="E1",
            reconciled=True,
            delta_posterior=0.45
        )

        result = explainer.explain(
            prior=0.5,
            signals=[signal],
            posterior=0.95  # Exactly at cap
        )

        # At boundary, cap should not be applied (> not >=)
        assert not result.anti_miracle_cap_applied
        assert result.posterior == 0.95

    def test_custom_cap_value(self):
        """Test with custom cap value"""
        explainer = BayesianPosteriorExplainer(anti_miracle_cap=0.90)

        signal = Signal(
            test_type="Smoking-Gun",
            likelihood=0.85,
            weight=1.0,
            raw_evidence_id="E1",
            reconciled=True,
            delta_posterior=0.45
        )

        result = explainer.explain(
            prior=0.5,
            signals=[signal],
            posterior=0.93  # Above custom cap
        )

        assert result.anti_miracle_cap_applied
        assert result.cap_delta == 0.03
        assert result.posterior == 0.90

class TestRobustnessNarrative:
    """Test robustness narrative generation"""

    def test_narrative_high_robustness(self):
        """Test narrative for high robustness scenario"""
        explainer = BayesianPosteriorExplainer()

        signals = [
            Signal(
                test_type="Smoking-Gun",
                likelihood=0.8,
                weight=1.0,
                raw_evidence_id="E1",
                reconciled=True,
                delta_posterior=0.2
            ),
            Signal(
                test_type="Hoop",
                likelihood=0.7,
                weight=1.0,
                raw_evidence_id="E2",
                reconciled=True,
                delta_posterior=0.15
            ),
            Signal(
                test_type="Straw-in-Wind",
                likelihood=0.6,
                weight=1.0,
                raw_evidence_id="E3",
                reconciled=True,
                delta_posterior=0.1
            )
        ]

        result = explainer.explain(
            prior=0.5,
            signals=signals,
            posterior=0.8
        )

        narrative = result.robustness_narrative
        assert "High robustness" in narrative
        assert "diverse" in narrative.lower()

    def test_narrative_with_discarded_signals(self):
        """Test narrative mentions discarded signals"""
        explainer = BayesianPosteriorExplainer()

        signals = [
            Signal(
                test_type="Smoking-Gun",
                likelihood=0.8,
                weight=1.0,
                raw_evidence_id="E1",
                reconciled=True,
                delta_posterior=0.3
            ),
            Signal(
                test_type="Hoop",
                likelihood=0.7,
                weight=1.0,
                raw_evidence_id="E2",
                reconciled=False,
                delta_posterior=0.2
            )
        ]

        result = explainer.explain(
            prior=0.5,
            signals=signals,
            posterior=0.8
        )

        narrative = result.robustness_narrative
        assert "Discarded" in narrative
        assert "violation" in narrative.lower()

    def test_narrative_with_cap_applied(self):
        """Test narrative mentions anti-miracle cap"""
        explainer = BayesianPosteriorExplainer(anti_miracle_cap=0.90)

        signal = Signal(
            test_type="Smoking-Gun",
            likelihood=0.9,
            weight=1.0,
            raw_evidence_id="E1",
            reconciled=True,
            delta_posterior=0.45
        )

        result = explainer.explain(
            prior=0.5,
            signals=[signal],
            posterior=0.95
        )

        narrative = result.robustness_narrative
        assert "Anti-miracle cap" in narrative
        assert "trimmed" in narrative.lower()

    def test_narrative_low_robustness(self):
        """Test narrative for low robustness scenario"""
        explainer = BayesianPosteriorExplainer()

        # No reconciled signals
        signals = [
            Signal(
                test_type="Smoking-Gun",
                likelihood=0.8,
                weight=1.0,
                raw_evidence_id="E1",
                reconciled=False,
                delta_posterior=0.3
            )
        ]

        result = explainer.explain(
            prior=0.5,
            signals=signals,
            posterior=0.5
        )

        narrative = result.robustness_narrative
        assert "Low robustness" in narrative
        assert "insufficient" in narrative.lower()

    def test_narrative_moderate_robustness(self):
        """Test narrative for moderate robustness scenario"""
        explainer = BayesianPosteriorExplainer()

        signals = [
            Signal(
                test_type="Smoking-Gun",
                likelihood=0.8,
                weight=1.0,
                raw_evidence_id="E1",
                reconciled=True,
                delta_posterior=0.3
            )
        ]

        result = explainer.explain(
            prior=0.5,
            signals=signals,
            posterior=0.8
        )

        narrative = result.robustness_narrative
        assert "Moderate robustness" in narrative
        assert "limited" in narrative.lower()

    def test_narrative_mentions_primary_driver(self):
        """Test narrative mentions primary driving signal"""
        explainer = BayesianPosteriorExplainer()

        signals = [
            Signal(
                test_type="Smoking-Gun",
                likelihood=0.9,
                weight=1.0,
                raw_evidence_id="E1",
                reconciled=True,
                delta_posterior=0.4
            ),
            Signal(
                test_type="Straw-in-Wind",
                likelihood=0.6,
                weight=1.0,
                raw_evidence_id="E2",
                reconciled=True,
                delta_posterior=0.05
            )
        ]

        result = explainer.explain(
            prior=0.5,
            signals=signals,
            posterior=0.9
        )

        narrative = result.robustness_narrative
        assert "Primary driver" in narrative
        assert "Smoking-Gun" in narrative

class TestJSONExport:
    """Test JSON export functionality"""

    def test_to_json_export(self):
        """Test exporting justification to JSON"""
        explainer = BayesianPosteriorExplainer()

        signal = Signal(
            test_type="Smoking-Gun",
            likelihood=0.8,
            weight=1.0,
            raw_evidence_id="E1",
            reconciled=True,
            delta_posterior=0.3
        )

        result = explainer.explain(
            prior=0.5,
            signals=[signal],
            posterior=0.8
        )

        json_output = explainer.to_json(result)

        assert isinstance(json_output, dict)
        assert 'prior' in json_output
        assert 'posterior' in json_output
        assert 'signals_ranked' in json_output
        assert 'discarded_signals' in json_output
        assert 'anti_miracle_cap_applied' in json_output
        assert 'cap_delta' in json_output
        assert 'robustness_narrative' in json_output
        assert 'timestamp' in json_output

class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_zero_prior(self):
        """Test with zero prior"""
        explainer = BayesianPosteriorExplainer()

        signal = Signal(
            test_type="Smoking-Gun",
            likelihood=0.8,
            weight=1.0,
            raw_evidence_id="E1",
            reconciled=True,
            delta_posterior=0.5
        )

        result = explainer.explain(
            prior=0.0,
            signals=[signal],
            posterior=0.5
        )

        assert result.prior == 0.0
        assert result.posterior == 0.5

    def test_one_posterior(self):
        """Test with posterior of 1.0"""
        explainer = BayesianPosteriorExplainer(anti_miracle_cap=0.99)

        signal = Signal(
            test_type="Doubly-Decisive",
            likelihood=1.0,
            weight=1.0,
            raw_evidence_id="E1",
            reconciled=True,
            delta_posterior=0.5
        )

        result = explainer.explain(
            prior=0.5,
            signals=[signal],
            posterior=1.0
        )

        assert result.anti_miracle_cap_applied
        assert result.posterior == 0.99

    def test_all_signals_zero_delta(self):
        """Test with all signals having zero delta"""
        explainer = BayesianPosteriorExplainer()

        signals = [
            Signal(
                test_type="Straw-in-Wind",
                likelihood=0.5,
                weight=1.0,
                raw_evidence_id="E1",
                reconciled=True,
                delta_posterior=0.0
            ),
            Signal(
                test_type="Straw-in-Wind",
                likelihood=0.5,
                weight=1.0,
                raw_evidence_id="E2",
                reconciled=True,
                delta_posterior=0.0
            )
        ]

        result = explainer.explain(
            prior=0.5,
            signals=signals,
            posterior=0.5
        )

        assert len(result.signals_ranked) == 2
        assert result.posterior == 0.5

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
