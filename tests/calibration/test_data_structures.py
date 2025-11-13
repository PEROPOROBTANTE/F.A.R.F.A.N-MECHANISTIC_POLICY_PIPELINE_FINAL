"""
Unit tests for calibration data structures.

Validates:
- Score range enforcement [0.0, 1.0]
- Canonical notation validation
- Anti-universality checking
- Serialization (to_dict)
"""
import pytest

from src.saaaaaa.core.calibration import (
    LayerID,
    LayerScore,
    ContextTuple,
    CompatibilityMapping,
    InteractionTerm,
    CalibrationResult,
    CalibrationSubject,
)


class TestLayerScore:
    """Test LayerScore validation."""
    
    def test_valid_score(self):
        """Valid score should be accepted."""
        score = LayerScore(
            layer=LayerID.UNIT,
            score=0.75,
            rationale="Test"
        )
        assert score.score == 0.75
    
    def test_score_too_high(self):
        """Score > 1.0 should raise ValueError."""
        with pytest.raises(ValueError, match="out of range"):
            LayerScore(
                layer=LayerID.UNIT,
                score=1.5,
                rationale="Invalid"
            )
    
    def test_score_too_low(self):
        """Score < 0.0 should raise ValueError."""
        with pytest.raises(ValueError, match="out of range"):
            LayerScore(
                layer=LayerID.UNIT,
                score=-0.1,
                rationale="Invalid"
            )
    
    def test_boundary_values(self):
        """Boundary values 0.0 and 1.0 should be valid."""
        score_zero = LayerScore(layer=LayerID.UNIT, score=0.0)
        score_one = LayerScore(layer=LayerID.UNIT, score=1.0)
        assert score_zero.score == 0.0
        assert score_one.score == 1.0


class TestContextTuple:
    """Test ContextTuple validation."""
    
    def test_valid_context(self):
        """Valid canonical notation should be accepted."""
        ctx = ContextTuple(
            question_id="Q001",
            dimension="DIM01",
            policy_area="PA01",
            unit_quality=0.75
        )
        assert ctx.dimension == "DIM01"
        assert ctx.policy_area == "PA01"
    
    def test_invalid_dimension_notation(self):
        """Non-canonical dimension should raise ValueError."""
        with pytest.raises(ValueError, match="canonical code"):
            ContextTuple(
                question_id="Q001",
                dimension="D1",  # Should be DIM01
                policy_area="PA01",
                unit_quality=0.75
            )
    
    def test_invalid_policy_notation(self):
        """Non-canonical policy should raise ValueError."""
        with pytest.raises(ValueError, match="canonical code"):
            ContextTuple(
                question_id="Q001",
                dimension="DIM01",
                policy_area="P1",  # Should be PA01
                unit_quality=0.75
            )


class TestCompatibilityMapping:
    """Test compatibility mapping and anti-universality."""
    
    def test_get_score_declared(self):
        """Should return declared score."""
        mapping = CompatibilityMapping(
            method_id="test_method",
            questions={"Q001": 1.0},
            dimensions={"DIM01": 0.7},
            policies={"PA01": 0.3}
        )
        
        assert mapping.get_question_score("Q001") == 1.0
        assert mapping.get_dimension_score("DIM01") == 0.7
        assert mapping.get_policy_score("PA01") == 0.3
    
    def test_get_score_undeclared(self):
        """Should return penalty (0.1) for undeclared."""
        mapping = CompatibilityMapping(
            method_id="test_method",
            questions={},
            dimensions={},
            policies={}
        )
        
        assert mapping.get_question_score("Q999") == 0.1
        assert mapping.get_dimension_score("DIM99") == 0.1
        assert mapping.get_policy_score("PA99") == 0.1
    
    def test_anti_universality_compliant(self):
        """Should pass if NOT universal."""
        mapping = CompatibilityMapping(
            method_id="test_method",
            questions={"Q001": 1.0, "Q002": 0.7, "Q003": 0.3},
            dimensions={"DIM01": 1.0, "DIM02": 0.7},
            policies={"PA01": 1.0, "PA02": 0.3}
        )
        
        # Average: Q=0.67, D=0.85, P=0.65 → NOT universal
        assert mapping.check_anti_universality(threshold=0.9)
    
    def test_anti_universality_violation(self):
        """Should fail if universal."""
        mapping = CompatibilityMapping(
            method_id="universal_method",
            questions={"Q001": 1.0, "Q002": 1.0, "Q003": 1.0},
            dimensions={"DIM01": 1.0, "DIM02": 1.0},
            policies={"PA01": 1.0, "PA02": 1.0}
        )
        
        # Average: Q=1.0, D=1.0, P=1.0 → UNIVERSAL (violation)
        assert not mapping.check_anti_universality(threshold=0.9)


class TestInteractionTerm:
    """Test interaction term computation."""
    
    def test_compute_weakest_link(self):
        """Should use min() for weakest link."""
        term = InteractionTerm(
            layer_1=LayerID.UNIT,
            layer_2=LayerID.CHAIN,
            weight=0.15,
            rationale="Test"
        )
        
        scores = {
            LayerID.UNIT: 0.8,
            LayerID.CHAIN: 0.6
        }
        
        # 0.15 * min(0.8, 0.6) = 0.15 * 0.6 = 0.09
        contribution = term.compute(scores)
        assert abs(contribution - 0.09) < 1e-6
    
    def test_compute_missing_layer(self):
        """Should use 0.0 for missing layer."""
        term = InteractionTerm(
            layer_1=LayerID.UNIT,
            layer_2=LayerID.CHAIN,
            weight=0.15,
            rationale="Test"
        )
        
        scores = {
            LayerID.UNIT: 0.8
            # CHAIN missing
        }
        
        # 0.15 * min(0.8, 0.0) = 0.0
        contribution = term.compute(scores)
        assert contribution == 0.0


class TestCalibrationResult:
    """Test calibration result validation."""
    
    def test_valid_result(self):
        """Valid result should be accepted."""
        subject = CalibrationSubject(
            method_id="test",
            method_version="v1.0",
            graph_config="abc123",
            subgraph_id="test_graph",
            context=ContextTuple(
                question_id="Q001",
                dimension="DIM01",
                policy_area="PA01",
                unit_quality=0.75
            )
        )
        
        result = CalibrationResult(
            subject=subject,
            layer_scores={
                LayerID.UNIT: LayerScore(layer=LayerID.UNIT, score=0.75)
            },
            linear_contribution=0.65,
            interaction_contribution=0.15,
            final_score=0.80
        )
        
        assert result.final_score == 0.80
    
    def test_invalid_sum(self):
        """Should raise if linear + interaction ≠ final."""
        subject = CalibrationSubject(
            method_id="test",
            method_version="v1.0",
            graph_config="abc",
            subgraph_id="test",
            context=ContextTuple(
                question_id="Q001",
                dimension="DIM01",
                policy_area="PA01",
                unit_quality=0.75
            )
        )
        
        with pytest.raises(ValueError, match="Final score.*!="):
            CalibrationResult(
                subject=subject,
                layer_scores={},
                linear_contribution=0.65,
                interaction_contribution=0.15,
                final_score=0.99  # Doesn't match sum
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
