"""
Tests for calibration-parametrization harmonization.

This test suite validates that the calibration and parametrization systems
are properly integrated and consistent with each other.
"""
import pytest
from pathlib import Path

from src.saaaaaa.core.calibration import (
    BaseLayerEvaluator,
    UnitLayerEvaluator,
    CalibrationOrchestrator,
    ContextualLayerEvaluator,
    CompatibilityRegistry,
    LayerScore,
    LayerID,
    DEFAULT_CALIBRATION_CONFIG,
)


class TestBaseLayerIntegration:
    """Tests for BASE layer integration with intrinsic calibration"""

    def test_base_evaluator_loads_calibration_data(self):
        """Verify BASE layer loads real calibration scores"""
        # Check if calibration file exists
        calibration_path = Path("config/intrinsic_calibration.json")
        if not calibration_path.exists():
            pytest.skip("intrinsic_calibration.json not found")

        evaluator = BaseLayerEvaluator(calibration_path)

        # Should have loaded some calibrations
        assert len(evaluator.calibrations) > 0, \
            "BaseLayerEvaluator should load calibrations from file"

    def test_base_evaluator_returns_layer_score(self):
        """Verify BASE evaluator returns LayerScore (not raw float)"""
        calibration_path = Path("config/intrinsic_calibration.json")
        if not calibration_path.exists():
            pytest.skip("intrinsic_calibration.json not found")

        evaluator = BaseLayerEvaluator(calibration_path)

        # Get a method from calibrations
        if evaluator.calibrations:
            method_id = list(evaluator.calibrations.keys())[0]
            result = evaluator.evaluate(method_id)

            assert isinstance(result, LayerScore), \
                "BaseLayerEvaluator.evaluate() must return LayerScore"
            assert result.layer == LayerID.BASE
            assert 0.0 <= result.score <= 1.0

    def test_base_evaluator_aggregates_components_correctly(self):
        """Verify BASE score is correct aggregation of b_theory, b_impl, b_deploy"""
        calibration_path = Path("config/intrinsic_calibration.json")
        if not calibration_path.exists():
            pytest.skip("intrinsic_calibration.json not found")

        evaluator = BaseLayerEvaluator(calibration_path)

        if evaluator.calibrations:
            method_id = list(evaluator.calibrations.keys())[0]
            result = evaluator.evaluate(method_id)

            # Extract components
            b_theory = result.components["b_theory"]
            b_impl = result.components["b_impl"]
            b_deploy = result.components["b_deploy"]

            # Verify aggregation: 0.4*theory + 0.4*impl + 0.2*deploy
            expected = 0.4 * b_theory + 0.4 * b_impl + 0.2 * b_deploy
            assert abs(result.score - expected) < 1e-6, \
                f"BASE score should be 0.4*{b_theory} + 0.4*{b_impl} + 0.2*{b_deploy}"


class TestOrchestratorIntegration:
    """Tests for orchestrator integration"""

    def test_orchestrator_uses_base_evaluator(self):
        """Verify orchestrator no longer uses hardcoded BASE stub"""
        calibration_path = Path("config/intrinsic_calibration.json")
        if not calibration_path.exists():
            pytest.skip("intrinsic_calibration.json not found")

        orch = CalibrationOrchestrator(
            intrinsic_calibration_path=calibration_path
        )

        # Should have base_evaluator
        assert hasattr(orch, "base_evaluator"), \
            "Orchestrator should have base_evaluator attribute"
        assert orch.base_evaluator is not None, \
            "base_evaluator should be initialized"

    def test_orchestrator_without_calibration_file_uses_penalty(self):
        """Verify orchestrator handles missing calibration file gracefully"""
        orch = CalibrationOrchestrator(
            intrinsic_calibration_path="nonexistent.json"
        )

        # Should not crash, but base_evaluator should be None
        assert orch.base_evaluator is None


class TestConfigConsistency:
    """Tests for configuration consistency"""

    def test_unit_layer_weights_sum_to_one(self):
        """Verify Unit layer component weights sum to 1.0"""
        config = DEFAULT_CALIBRATION_CONFIG

        total = (config.unit_layer.w_S + config.unit_layer.w_M +
                config.unit_layer.w_I + config.unit_layer.w_P)

        assert abs(total - 1.0) < 1e-6, \
            f"Unit layer weights must sum to 1.0, got {total}"

    def test_meta_layer_weights_sum_to_one(self):
        """Verify Meta layer component weights sum to 1.0"""
        config = DEFAULT_CALIBRATION_CONFIG

        total = (config.meta_layer.w_transparency +
                config.meta_layer.w_governance +
                config.meta_layer.w_cost)

        assert abs(total - 1.0) < 1e-6, \
            f"Meta layer weights must sum to 1.0, got {total}"

    def test_choquet_weights_normalized(self):
        """Verify Choquet weights (linear + interaction) sum to 1.0"""
        config = DEFAULT_CALIBRATION_CONFIG

        linear_sum = sum(config.choquet.linear_weights.values())
        interaction_sum = sum(config.choquet.interaction_weights.values())
        total = linear_sum + interaction_sum

        assert abs(total - 1.0) < 1e-6, \
            f"Choquet normalization: linear + interaction must = 1.0, got {total}"


class TestAntiUniversality:
    """Tests for anti-universality constraint enforcement"""

    def test_compatibility_registry_validates_anti_universality(self):
        """Verify compatibility registry enforces anti-universality"""
        compat_path = Path("data/method_compatibility.json")
        if not compat_path.exists():
            pytest.skip("method_compatibility.json not found")

        registry = CompatibilityRegistry(compat_path)

        # validate_anti_universality should not raise for valid data
        try:
            results = registry.validate_anti_universality(threshold=0.9)
            assert isinstance(results, dict)
            # All methods should be compliant
            assert all(results.values()), \
                "All methods in registry should satisfy anti-universality"
        except ValueError as e:
            pytest.fail(f"Anti-universality validation failed: {e}")


class TestDataStructureImmutability:
    """Tests for frozen dataclass immutability"""

    def test_layer_score_is_immutable(self):
        """Verify LayerScore cannot be modified after creation"""
        score = LayerScore(
            layer=LayerID.BASE,
            score=0.8,
            rationale="test"
        )

        # Attempting to modify should raise
        with pytest.raises(FrozenInstanceError):
            score.score = 0.9

    def test_context_tuple_validates_canonical_notation(self):
        """Verify ContextTuple enforces canonical notation"""
        from src.saaaaaa.core.calibration import ContextTuple

        # Valid canonical notation should work
        ctx = ContextTuple(
            question_id="Q001",
            dimension="DIM01",
            policy_area="PA01",
            unit_quality=0.75
        )
        assert ctx.dimension == "DIM01"

        # Invalid notation should raise
        with pytest.raises(ValueError):
            ContextTuple(
                question_id="Q001",
                dimension="D1",  # Should be DIM01
                policy_area="PA01",
                unit_quality=0.75
            )


class TestContextualLayerEvaluator:
    """Tests for contextual layer evaluator enhancements"""

    def test_contextual_evaluator_has_layer_score_methods(self):
        """Verify ContextualLayerEvaluator has new LayerScore-based methods"""
        compat_path = Path("data/method_compatibility.json")
        if not compat_path.exists():
            pytest.skip("method_compatibility.json not found")

        registry = CompatibilityRegistry(compat_path)
        evaluator = ContextualLayerEvaluator(registry)

        # Should have new methods
        assert hasattr(evaluator, "evaluate_question_layer")
        assert hasattr(evaluator, "evaluate_dimension_layer")
        assert hasattr(evaluator, "evaluate_policy_layer")

    def test_contextual_evaluator_backward_compatibility(self):
        """Verify old methods still work (backward compatibility)"""
        compat_path = Path("data/method_compatibility.json")
        if not compat_path.exists():
            pytest.skip("method_compatibility.json not found")

        registry = CompatibilityRegistry(compat_path)
        evaluator = ContextualLayerEvaluator(registry)

        # Old methods should still return float
        if registry.mappings:
            method_id = list(registry.mappings.keys())[0]
            mapping = registry.mappings[method_id]

            if mapping.questions:
                question_id = list(mapping.questions.keys())[0]
                score = evaluator.evaluate_question(method_id, question_id)
                assert isinstance(score, float)


# Add more test classes as needed for:
# - CongruenceLayerEvaluator
# - ChainLayerEvaluator
# - MetaLayerEvaluator
# - End-to-end calibration workflow
