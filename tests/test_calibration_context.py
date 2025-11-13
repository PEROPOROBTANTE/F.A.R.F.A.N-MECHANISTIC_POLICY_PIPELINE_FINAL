"""Tests for context-aware calibration system."""

import pytest

from src.saaaaaa.core.orchestrator.calibration_registry import (
    MethodCalibration,
    resolve_calibration,
    resolve_calibration_with_context,
)
from src.saaaaaa.core.orchestrator.calibration_context import (
    CalibrationContext,
    CalibrationModifier,
    PolicyArea,
    UnitOfAnalysis,
    resolve_contextual_calibration,
    infer_context_from_question_id,
)


class TestCalibrationContext:
    """Test CalibrationContext creation and manipulation."""
    
    def test_from_question_id_valid(self):
        """Test creating context from valid question ID."""
        context = CalibrationContext.from_question_id("D1Q1")
        assert context.question_id == "D1Q1"
        assert context.dimension == 1
        assert context.question_num == 1
    
    def test_from_question_id_various_formats(self):
        """Test parsing various question ID formats."""
        test_cases = [
            ("D6Q3", 6, 3),
            ("d2q5", 2, 5),
            ("D10Q25", 10, 25),
        ]
        for qid, expected_dim, expected_q in test_cases:
            context = CalibrationContext.from_question_id(qid)
            assert context.dimension == expected_dim
            assert context.question_num == expected_q
    
    def test_from_question_id_invalid(self):
        """Test handling invalid question IDs."""
        context = CalibrationContext.from_question_id("invalid")
        assert context.question_id == "invalid"
        assert context.dimension == 0
        assert context.question_num == 0
    
    def test_with_policy_area(self):
        """Test updating policy area."""
        context = CalibrationContext.from_question_id("D1Q1")
        new_context = context.with_policy_area(PolicyArea.FISCAL)
        
        assert new_context.policy_area == PolicyArea.FISCAL
        assert context.policy_area == PolicyArea.UNKNOWN  # Original unchanged
        assert new_context.dimension == context.dimension  # Other fields preserved
    
    def test_with_unit_of_analysis(self):
        """Test updating unit of analysis."""
        context = CalibrationContext.from_question_id("D1Q1")
        new_context = context.with_unit_of_analysis(UnitOfAnalysis.BASELINE_GAP)
        
        assert new_context.unit_of_analysis == UnitOfAnalysis.BASELINE_GAP
        assert context.unit_of_analysis == UnitOfAnalysis.UNKNOWN
    
    def test_with_method_position(self):
        """Test updating method position."""
        context = CalibrationContext.from_question_id("D1Q1")
        new_context = context.with_method_position(2, 5)
        
        assert new_context.method_position == 2
        assert new_context.total_methods == 5
        assert context.method_position == 0  # Original unchanged


class TestCalibrationModifier:
    """Test CalibrationModifier application."""
    
    def test_identity_modifier(self):
        """Test that default modifier doesn't change calibration."""
        base = MethodCalibration(
            score_min=0.0,
            score_max=1.0,
            min_evidence_snippets=3,
            max_evidence_snippets=18,
            contradiction_tolerance=0.05,
            uncertainty_penalty=0.25,
            aggregation_weight=1.0,
            sensitivity=0.85,
            requires_numeric_support=False,
            requires_temporal_support=False,
            requires_source_provenance=True,
        )
        
        modifier = CalibrationModifier()
        result = modifier.apply(base)
        
        assert result.min_evidence_snippets == base.min_evidence_snippets
        assert result.max_evidence_snippets == base.max_evidence_snippets
        assert result.contradiction_tolerance == pytest.approx(base.contradiction_tolerance)
        assert result.uncertainty_penalty == pytest.approx(base.uncertainty_penalty)
        assert result.aggregation_weight == pytest.approx(base.aggregation_weight)
        assert result.sensitivity == pytest.approx(base.sensitivity)
    
    def test_evidence_multiplier(self):
        """Test evidence snippet multipliers."""
        base = MethodCalibration(
            score_min=0.0,
            score_max=1.0,
            min_evidence_snippets=10,
            max_evidence_snippets=20,
            contradiction_tolerance=0.05,
            uncertainty_penalty=0.25,
            aggregation_weight=1.0,
            sensitivity=0.85,
            requires_numeric_support=False,
            requires_temporal_support=False,
            requires_source_provenance=True,
        )
        
        modifier = CalibrationModifier(
            min_evidence_multiplier=1.5,
            max_evidence_multiplier=1.2,
        )
        result = modifier.apply(base)
        
        assert result.min_evidence_snippets == 15  # 10 * 1.5
        assert result.max_evidence_snippets == 24  # 20 * 1.2
    
    def test_clamping(self):
        """Test that modifiers clamp values to valid ranges."""
        base = MethodCalibration(
            score_min=0.0,
            score_max=1.0,
            min_evidence_snippets=3,
            max_evidence_snippets=18,
            contradiction_tolerance=0.9,
            uncertainty_penalty=0.1,
            aggregation_weight=1.0,
            sensitivity=0.9,
            requires_numeric_support=False,
            requires_temporal_support=False,
            requires_source_provenance=True,
        )
        
        # Try to push values out of range
        modifier = CalibrationModifier(
            contradiction_tolerance_multiplier=2.0,  # Would be 1.8 > 1.0
            uncertainty_penalty_multiplier=0.1,  # Would be 0.01 < 0.0 (OK)
            sensitivity_multiplier=1.5,  # Would be 1.35 > 1.0
        )
        result = modifier.apply(base)
        
        assert result.contradiction_tolerance <= 1.0
        assert result.contradiction_tolerance >= 0.0
        assert result.sensitivity <= 1.0
        assert result.sensitivity >= 0.0


class TestContextualCalibration:
    """Test context-aware calibration resolution."""
    
    def test_no_context_returns_base(self):
        """Test that no context returns base calibration unchanged."""
        base = MethodCalibration(
            score_min=0.0,
            score_max=1.0,
            min_evidence_snippets=3,
            max_evidence_snippets=18,
            contradiction_tolerance=0.05,
            uncertainty_penalty=0.25,
            aggregation_weight=1.0,
            sensitivity=0.85,
            requires_numeric_support=False,
            requires_temporal_support=False,
            requires_source_provenance=True,
        )
        
        result = resolve_contextual_calibration(base, None)
        assert result == base
    
    def test_dimension_modifier_applied(self):
        """Test dimension-specific modifiers are applied."""
        base = MethodCalibration(
            score_min=0.0,
            score_max=1.0,
            min_evidence_snippets=10,
            max_evidence_snippets=20,
            contradiction_tolerance=0.5,
            uncertainty_penalty=0.5,
            aggregation_weight=1.0,
            sensitivity=0.5,
            requires_numeric_support=False,
            requires_temporal_support=False,
            requires_source_provenance=True,
        )
        
        # D1 has min_evidence_multiplier=1.3
        context = CalibrationContext.from_question_id("D1Q1")
        result = resolve_contextual_calibration(base, context)
        
        # Should have more evidence requirements for D1 (baseline gaps)
        assert result.min_evidence_snippets > base.min_evidence_snippets
    
    def test_policy_area_modifier_applied(self):
        """Test policy area modifiers are applied."""
        base = MethodCalibration(
            score_min=0.0,
            score_max=1.0,
            min_evidence_snippets=10,
            max_evidence_snippets=20,
            contradiction_tolerance=0.5,
            uncertainty_penalty=0.5,
            aggregation_weight=1.0,
            sensitivity=0.5,
            requires_numeric_support=False,
            requires_temporal_support=False,
            requires_source_provenance=True,
        )
        
        context = CalibrationContext.from_question_id("D1Q1")
        context = context.with_policy_area(PolicyArea.FISCAL)
        result = resolve_contextual_calibration(base, context)
        
        # Fiscal policy should increase evidence requirements and sensitivity
        assert result.min_evidence_snippets > base.min_evidence_snippets
        assert result.sensitivity > base.sensitivity
    
    def test_cumulative_modifiers(self):
        """Test that multiple modifiers are cumulative."""
        base = MethodCalibration(
            score_min=0.0,
            score_max=1.0,
            min_evidence_snippets=10,
            max_evidence_snippets=20,
            contradiction_tolerance=0.5,
            uncertainty_penalty=0.5,
            aggregation_weight=1.0,
            sensitivity=0.5,
            requires_numeric_support=False,
            requires_temporal_support=False,
            requires_source_provenance=True,
        )
        
        # Apply dimension + policy area + unit modifiers
        context = CalibrationContext.from_question_id("D9Q1")  # Financial dimension
        context = context.with_policy_area(PolicyArea.FISCAL)
        context = context.with_unit_of_analysis(UnitOfAnalysis.FINANCIAL)
        result = resolve_contextual_calibration(base, context)
        
        # Should have significantly higher requirements
        # D9, fiscal, and financial all increase evidence needs
        assert result.min_evidence_snippets > base.min_evidence_snippets * 1.5
        assert result.sensitivity > base.sensitivity


class TestInferContext:
    """Test context inference from question ID."""
    
    def test_infer_dimension_1_baseline_gap(self):
        """Test D1 infers baseline gap unit."""
        context = infer_context_from_question_id("D1Q1")
        assert context.dimension == 1
        assert context.unit_of_analysis == UnitOfAnalysis.BASELINE_GAP
    
    def test_infer_dimension_2_indicator(self):
        """Test D2 infers indicator unit."""
        context = infer_context_from_question_id("D2Q3")
        assert context.dimension == 2
        assert context.unit_of_analysis == UnitOfAnalysis.INDICATOR
    
    def test_infer_dimension_9_financial(self):
        """Test D9 infers financial unit."""
        context = infer_context_from_question_id("D9Q1")
        assert context.dimension == 9
        assert context.unit_of_analysis == UnitOfAnalysis.FINANCIAL


class TestIntegrationWithRegistry:
    """Test integration with calibration registry."""
    
    def test_resolve_calibration_backward_compatible(self):
        """Test that resolve_calibration still works without context."""
        # BayesianEvidenceScorer.compute_evidence_score exists in registry
        calib = resolve_calibration("BayesianEvidenceScorer", "compute_evidence_score")
        assert calib is not None
        assert isinstance(calib, MethodCalibration)
    
    def test_resolve_with_context_returns_different(self):
        """Test that context changes calibration."""
        base = resolve_calibration("BayesianEvidenceScorer", "compute_evidence_score")
        assert base is not None
        
        # Resolve with fiscal policy context
        contextual = resolve_calibration_with_context(
            "BayesianEvidenceScorer",
            "compute_evidence_score",
            question_id="D9Q1",
            policy_area="fiscal",
        )
        assert contextual is not None
        
        # Should be different due to D9 + fiscal modifiers
        assert (
            contextual.min_evidence_snippets != base.min_evidence_snippets
            or contextual.sensitivity != base.sensitivity
        )
    
    def test_resolve_with_context_different_questions(self):
        """Test that same method gets different calibration for different questions."""
        # D1Q1 (baseline gap)
        d1_calib = resolve_calibration_with_context(
            "BayesianEvidenceScorer",
            "compute_evidence_score",
            question_id="D1Q1",
        )
        
        # D6Q3 (logical framework)
        d6_calib = resolve_calibration_with_context(
            "BayesianEvidenceScorer",
            "compute_evidence_score",
            question_id="D6Q3",
        )
        
        assert d1_calib is not None
        assert d6_calib is not None
        
        # Should have different characteristics
        # D6 has lower contradiction tolerance (stricter)
        assert d6_calib.contradiction_tolerance < d1_calib.contradiction_tolerance
    
    def test_method_position_affects_calibration(self):
        """Test that method position in sequence affects calibration."""
        # First method in sequence
        first = resolve_calibration_with_context(
            "BayesianEvidenceScorer",
            "compute_evidence_score",
            question_id="D1Q1",
            method_position=0,
            total_methods=5,
        )
        
        # Last method in sequence
        last = resolve_calibration_with_context(
            "BayesianEvidenceScorer",
            "compute_evidence_score",
            question_id="D1Q1",
            method_position=4,
            total_methods=5,
        )
        
        assert first is not None
        assert last is not None
        
        # Early methods should have higher evidence needs
        assert first.min_evidence_snippets >= last.min_evidence_snippets
        # Late methods should have higher aggregation weight (synthesis)
        assert last.aggregation_weight > first.aggregation_weight


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
