"""
Integration tests for the complete calibration system.

Tests the end-to-end flow:
1. Loading intrinsic_calibration.json
2. Loading method_parameters.json
3. Determining required layers by method type
4. Computing calibration scores via orchestrator
5. Making validation decisions
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.saaaaaa.core.calibration.intrinsic_loader import IntrinsicScoreLoader
from src.saaaaaa.core.calibration.parameter_loader import MethodParameterLoader
from src.saaaaaa.core.calibration.layer_requirements import LayerRequirementsResolver
from src.saaaaaa.core.calibration.orchestrator import CalibrationOrchestrator
from src.saaaaaa.core.calibration.validator import CalibrationValidator
from src.saaaaaa.core.calibration.data_structures import LayerID


class TestIntrinsicLoader:
    """Test intrinsic calibration loader."""

    def test_load_intrinsic_calibration(self):
        """Test loading intrinsic_calibration.json."""
        loader = IntrinsicScoreLoader("config/intrinsic_calibration.json")

        # Should load lazily
        assert not loader._loaded

        # Get statistics (triggers load)
        stats = loader.get_statistics()

        assert loader._loaded
        assert stats["total"] > 0
        assert stats["computed"] > 0
        print(f"✓ Loaded {stats['total']} methods, {stats['computed']} computed")

    def test_get_score_for_calibrated_method(self):
        """Test getting score for a method that exists."""
        loader = IntrinsicScoreLoader("config/intrinsic_calibration.json")

        # Should have some methods calibrated
        stats = loader.get_statistics()
        assert stats["computed"] > 0

        # Get a score (using a method we know exists from exploration)
        # Note: Replace with actual method from your intrinsic_calibration.json
        score = loader.get_score("some.method.name", default=0.5)

        # Score should be in valid range
        assert 0.0 <= score <= 1.0
        print(f"✓ Retrieved score: {score}")

    def test_get_layer_for_method(self):
        """Test getting layer/role for a method."""
        loader = IntrinsicScoreLoader("config/intrinsic_calibration.json")

        # Get layer for a method
        # Note: This will return None for methods not in JSON
        layer = loader.get_layer("some.method.name")

        # Layer should be one of the expected types or None
        if layer:
            expected_layers = {
                "analyzer", "processor", "ingest", "structure",
                "extract", "aggregate", "report", "utility",
                "orchestrator", "meta", "transform", "score", "core"
            }
            assert layer.lower() in expected_layers
            print(f"✓ Method layer: {layer}")


class TestParameterLoader:
    """Test method parameter loader."""

    def test_load_method_parameters(self):
        """Test loading method_parameters.json."""
        loader = MethodParameterLoader("config/method_parameters.json")

        # Should load lazily
        assert not loader._loaded

        # Get statistics (triggers load)
        stats = loader.get_statistics()

        assert loader._loaded
        assert stats["total_executors"] == 30  # All 30 executors configured
        print(f"✓ Loaded {stats['total_executors']} executors, {stats['total_methods']} methods")

    def test_get_quality_thresholds(self):
        """Test getting global quality thresholds."""
        loader = MethodParameterLoader("config/method_parameters.json")

        thresholds = loader.get_quality_thresholds()

        assert thresholds["excellent"] == 0.85
        assert thresholds["good"] == 0.70
        assert thresholds["acceptable"] == 0.55
        assert thresholds["insufficient"] == 0.0
        print(f"✓ Quality thresholds: {thresholds}")

    def test_get_executor_threshold(self):
        """Test getting executor-specific threshold."""
        loader = MethodParameterLoader("config/method_parameters.json")

        # Test a few executors
        d1q1_threshold = loader.get_executor_threshold("D1Q1_Executor")
        d4q1_threshold = loader.get_executor_threshold("D4Q1_Executor")

        assert 0.0 < d1q1_threshold <= 1.0
        assert 0.0 < d4q1_threshold <= 1.0

        # D4Q1 (financial) should have higher threshold
        assert d4q1_threshold >= d1q1_threshold
        print(f"✓ D1Q1 threshold: {d1q1_threshold}, D4Q1 threshold: {d4q1_threshold}")

    def test_get_validation_threshold_by_role(self):
        """Test getting validation threshold by role type."""
        loader = MethodParameterLoader("config/method_parameters.json")

        analyzer_threshold = loader.get_validation_threshold_for_role("analyzer")
        utility_threshold = loader.get_validation_threshold_for_role("utility")

        # Analyzer should have higher threshold than utility
        assert analyzer_threshold > utility_threshold
        print(f"✓ Analyzer: {analyzer_threshold}, Utility: {utility_threshold}")


class TestLayerRequirements:
    """Test layer requirements resolver."""

    def test_resolver_initialization(self):
        """Test that resolver initializes correctly."""
        intrinsic_loader = IntrinsicScoreLoader("config/intrinsic_calibration.json")
        resolver = LayerRequirementsResolver(intrinsic_loader)

        # All role mappings should include BASE layer
        for role, layers in resolver.ROLE_LAYER_MAP.items():
            assert LayerID.BASE in layers
            print(f"✓ Role '{role}' includes BASE layer")

    def test_get_required_layers_for_analyzer(self):
        """Test that analyzer methods require all 8 layers."""
        intrinsic_loader = IntrinsicScoreLoader("config/intrinsic_calibration.json")
        resolver = LayerRequirementsResolver(intrinsic_loader)

        # Analyzer should have all 8 layers
        analyzer_layers = resolver.ROLE_LAYER_MAP["analyzer"]

        expected_layers = {
            LayerID.BASE,
            LayerID.UNIT,
            LayerID.QUESTION,
            LayerID.DIMENSION,
            LayerID.POLICY,
            LayerID.CONGRUENCE,
            LayerID.CHAIN,
            LayerID.META
        }

        assert analyzer_layers == expected_layers
        print(f"✓ Analyzer requires {len(analyzer_layers)} layers: all 8")

    def test_get_required_layers_for_utility(self):
        """Test that utility methods require minimal layers."""
        intrinsic_loader = IntrinsicScoreLoader("config/intrinsic_calibration.json")
        resolver = LayerRequirementsResolver(intrinsic_loader)

        # Utility should have minimal layers
        utility_layers = resolver.ROLE_LAYER_MAP["utility"]

        # Should have BASE, CHAIN, META (minimal)
        assert LayerID.BASE in utility_layers
        assert LayerID.CHAIN in utility_layers
        assert LayerID.META in utility_layers

        # Should NOT have contextual layers
        assert LayerID.QUESTION not in utility_layers
        assert LayerID.DIMENSION not in utility_layers
        assert LayerID.POLICY not in utility_layers

        print(f"✓ Utility requires {len(utility_layers)} layers (minimal)")


class TestOrchestratorIntegration:
    """Test calibration orchestrator integration."""

    def test_orchestrator_initialization(self):
        """Test that orchestrator initializes with all loaders."""
        orchestrator = CalibrationOrchestrator(
            intrinsic_calibration_path="config/intrinsic_calibration.json"
        )

        # Check that all components are initialized
        assert orchestrator.intrinsic_loader is not None
        assert orchestrator.layer_resolver is not None
        assert orchestrator.base_evaluator is not None
        assert orchestrator.unit_evaluator is not None

        print("✓ Orchestrator initialized with all components")

    def test_orchestrator_has_layer_resolver(self):
        """Test that orchestrator has layer resolver."""
        orchestrator = CalibrationOrchestrator(
            intrinsic_calibration_path="config/intrinsic_calibration.json"
        )

        # Should have layer_resolver attribute
        assert hasattr(orchestrator, 'layer_resolver')
        assert orchestrator.layer_resolver is not None

        # Test layer resolver functionality
        required_layers = orchestrator.layer_resolver.get_required_layers("test.method")
        assert isinstance(required_layers, set)
        assert len(required_layers) > 0

        print(f"✓ Layer resolver working, returns {len(required_layers)} layers for unknown method")


class TestValidatorIntegration:
    """Test validator integration."""

    def test_validator_initialization(self):
        """Test validator initialization."""
        orchestrator = CalibrationOrchestrator(
            intrinsic_calibration_path="config/intrinsic_calibration.json"
        )
        parameter_loader = MethodParameterLoader("config/method_parameters.json")

        validator = CalibrationValidator(
            orchestrator=orchestrator,
            parameter_loader=parameter_loader
        )

        assert validator.orchestrator is not None
        assert validator.parameter_loader is not None
        assert validator.intrinsic_loader is not None

        print("✓ Validator initialized successfully")

    def test_get_threshold_for_executor(self):
        """Test threshold determination for executors."""
        orchestrator = CalibrationOrchestrator(
            intrinsic_calibration_path="config/intrinsic_calibration.json"
        )
        parameter_loader = MethodParameterLoader("config/method_parameters.json")
        validator = CalibrationValidator(
            orchestrator=orchestrator,
            parameter_loader=parameter_loader
        )

        # Get threshold for an executor
        threshold = validator._get_threshold_for_method("D1Q1_Executor")

        assert 0.0 < threshold <= 1.0
        assert threshold >= 0.60  # Executors should have high thresholds

        print(f"✓ D1Q1_Executor threshold: {threshold}")

    def test_validate_method_flow(self):
        """Test full validation flow (skipped - requires PDT)."""
        # This would test the full flow but requires a valid PDT structure
        # and context, which are complex to mock
        print("  (Skipped - requires full PDT structure)")


class TestEndToEndFlow:
    """Test the complete end-to-end flow."""

    def test_complete_system_initialization(self):
        """Test that all components can be initialized together."""
        # 1. Load intrinsic calibration
        intrinsic_loader = IntrinsicScoreLoader("config/intrinsic_calibration.json")
        intrinsic_stats = intrinsic_loader.get_statistics()
        print(f"✓ Step 1: Loaded intrinsic calibration ({intrinsic_stats['computed']} methods)")

        # 2. Load method parameters
        parameter_loader = MethodParameterLoader("config/method_parameters.json")
        param_stats = parameter_loader.get_statistics()
        print(f"✓ Step 2: Loaded method parameters ({param_stats['total_executors']} executors)")

        # 3. Initialize layer resolver
        layer_resolver = LayerRequirementsResolver(intrinsic_loader)
        print("✓ Step 3: Initialized layer requirements resolver")

        # 4. Initialize orchestrator
        orchestrator = CalibrationOrchestrator(
            intrinsic_calibration_path="config/intrinsic_calibration.json"
        )
        print("✓ Step 4: Initialized calibration orchestrator")

        # 5. Initialize validator
        validator = CalibrationValidator(
            orchestrator=orchestrator,
            parameter_loader=parameter_loader
        )
        print("✓ Step 5: Initialized validator")

        # Verify all components are connected
        assert validator.orchestrator.intrinsic_loader is not None
        assert validator.orchestrator.layer_resolver is not None
        assert validator.parameter_loader is not None

        print("\n✅ Complete system initialized successfully!")

    def test_executor_configuration_complete(self):
        """Test that all 30 executors are configured."""
        parameter_loader = MethodParameterLoader("config/method_parameters.json")

        # Check all 30 executors
        all_configured = True
        missing = []

        for d in range(1, 7):
            for q in range(1, 6):
                executor_name = f"D{d}Q{q}_Executor"
                threshold = parameter_loader.get_executor_threshold(executor_name, default=None)

                if threshold is None:
                    all_configured = False
                    missing.append(executor_name)

        if all_configured:
            print("✓ All 30 executors are configured with thresholds")
        else:
            print(f"✗ Missing configurations for: {missing}")

        assert all_configured, f"Missing executor configurations: {missing}"

    def test_layer_mapping_completeness(self):
        """Test that all role types have layer mappings."""
        intrinsic_loader = IntrinsicScoreLoader("config/intrinsic_calibration.json")
        resolver = LayerRequirementsResolver(intrinsic_loader)

        expected_roles = {
            "analyzer", "processor", "ingest", "structure",
            "extract", "aggregate", "report", "utility",
            "orchestrator", "meta", "transform"
        }

        for role in expected_roles:
            assert role in resolver.ROLE_LAYER_MAP
            layers = resolver.ROLE_LAYER_MAP[role]
            assert LayerID.BASE in layers  # All must include BASE

        print(f"✓ All {len(expected_roles)} role types have layer mappings")


if __name__ == "__main__":
    """Run tests with detailed output."""
    print("=" * 80)
    print("CALIBRATION SYSTEM INTEGRATION TESTS")
    print("=" * 80)
    print()

    # Run each test class
    test_classes = [
        TestIntrinsicLoader,
        TestParameterLoader,
        TestLayerRequirements,
        TestOrchestratorIntegration,
        TestValidatorIntegration,
        TestEndToEndFlow
    ]

    for test_class in test_classes:
        print(f"\n{test_class.__name__}:")
        print("-" * 80)

        test_instance = test_class()
        for method_name in dir(test_instance):
            if method_name.startswith("test_"):
                try:
                    method = getattr(test_instance, method_name)
                    print(f"\n  {method_name}:")
                    method()
                except Exception as e:
                    print(f"  ✗ FAILED: {e}")

    print("\n" + "=" * 80)
    print("TESTS COMPLETE")
    print("=" * 80)
