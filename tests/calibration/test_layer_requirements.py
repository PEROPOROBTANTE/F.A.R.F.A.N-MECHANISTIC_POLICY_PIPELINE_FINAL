"""
Unit tests for LayerRequirementsResolver.

Tests verify:
- Correct mapping of roles to required layers
- Conservative fallback for unknown roles
- Layer skipping logic
- Always includes @b (BASE) for every method
"""
import pytest
import tempfile
import json
from pathlib import Path
from src.saaaaaa.core.calibration.intrinsic_loader import IntrinsicScoreLoader
from src.saaaaaa.core.calibration.layer_requirements import LayerRequirementsResolver
from src.saaaaaa.core.calibration.data_structures import LayerID


@pytest.fixture
def sample_calibration_data():
    """Sample calibration JSON for testing."""
    return {
        "_metadata": {"version": "1.0.0"},
        "methods": {
            "test.Analyzer.analyze": {
                "method_id": "test.Analyzer.analyze",
                "calibration_status": "computed",
                "b_theory": 0.8, "b_impl": 0.75, "b_deploy": 0.7,
                "layer": "analyzer"
            },
            "test.Processor.process": {
                "method_id": "test.Processor.process",
                "calibration_status": "computed",
                "b_theory": 0.6, "b_impl": 0.65, "b_deploy": 0.6,
                "layer": "processor"
            },
            "test.Ingest.load": {
                "method_id": "test.Ingest.load",
                "calibration_status": "computed",
                "b_theory": 0.5, "b_impl": 0.6, "b_deploy": 0.55,
                "layer": "ingest"
            },
            "test.Aggregate.combine": {
                "method_id": "test.Aggregate.combine",
                "calibration_status": "computed",
                "b_theory": 0.7, "b_impl": 0.7, "b_deploy": 0.65,
                "layer": "aggregate"
            },
            "test.Report.generate": {
                "method_id": "test.Report.generate",
                "calibration_status": "computed",
                "b_theory": 0.6, "b_impl": 0.6, "b_deploy": 0.6,
                "layer": "report"
            },
            "test.Util.format": {
                "method_id": "test.Util.format",
                "calibration_status": "computed",
                "b_theory": 0.5, "b_impl": 0.5, "b_deploy": 0.5,
                "layer": "utility"
            },
            "test.Unknown.mystery": {
                "method_id": "test.Unknown.mystery",
                "calibration_status": "computed",
                "b_theory": 0.5, "b_impl": 0.5, "b_deploy": 0.5,
                "layer": "unknown_role"
            },
            "test.NoLayer.method": {
                "method_id": "test.NoLayer.method",
                "calibration_status": "computed",
                "b_theory": 0.5, "b_impl": 0.5, "b_deploy": 0.5
            }
        }
    }


@pytest.fixture
def temp_calibration_file(sample_calibration_data):
    """Create a temporary calibration JSON file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_calibration_data, f)
        temp_path = f.name

    yield temp_path
    Path(temp_path).unlink()


@pytest.fixture
def resolver(temp_calibration_file):
    """Create a LayerRequirementsResolver with test data."""
    loader = IntrinsicScoreLoader(temp_calibration_file)
    return LayerRequirementsResolver(loader)


class TestLayerRequirementsResolver:
    """Test suite for LayerRequirementsResolver."""

    def test_initialization(self, resolver):
        """Test that resolver initializes correctly."""
        assert resolver.intrinsic_loader is not None

    def test_analyzer_requires_all_layers(self, resolver):
        """Test that analyzer methods require all 8 layers."""
        layers = resolver.get_required_layers("test.Analyzer.analyze")

        assert len(layers) == 8
        assert LayerID.BASE in layers
        assert LayerID.UNIT in layers
        assert LayerID.QUESTION in layers
        assert LayerID.DIMENSION in layers
        assert LayerID.POLICY in layers
        assert LayerID.CONGRUENCE in layers
        assert LayerID.CHAIN in layers
        assert LayerID.META in layers

    def test_processor_requires_core_plus_unit_meta(self, resolver):
        """Test that processor methods require @b, @u, @chain, @m."""
        layers = resolver.get_required_layers("test.Processor.process")

        assert LayerID.BASE in layers
        assert LayerID.UNIT in layers
        assert LayerID.CHAIN in layers
        assert LayerID.META in layers

        # Should NOT require contextual or congruence
        assert LayerID.QUESTION not in layers
        assert LayerID.DIMENSION not in layers
        assert LayerID.POLICY not in layers
        assert LayerID.CONGRUENCE not in layers

    def test_ingest_requires_core_plus_unit_meta(self, resolver):
        """Test that ingest methods require @b, @u, @chain, @m."""
        layers = resolver.get_required_layers("test.Ingest.load")

        assert LayerID.BASE in layers
        assert LayerID.UNIT in layers
        assert LayerID.CHAIN in layers
        assert LayerID.META in layers

        assert len(layers) == 4

    def test_aggregate_requires_contextual_layers(self, resolver):
        """Test that aggregate methods require contextual layers."""
        layers = resolver.get_required_layers("test.Aggregate.combine")

        assert LayerID.BASE in layers
        assert LayerID.CHAIN in layers
        assert LayerID.DIMENSION in layers
        assert LayerID.POLICY in layers
        assert LayerID.CONGRUENCE in layers
        assert LayerID.META in layers

        # Should NOT require @u or @q
        assert LayerID.UNIT not in layers
        assert LayerID.QUESTION not in layers

    def test_report_requires_minimal_layers(self, resolver):
        """Test that report methods require minimal layers."""
        layers = resolver.get_required_layers("test.Report.generate")

        assert LayerID.BASE in layers
        assert LayerID.CHAIN in layers
        assert LayerID.CONGRUENCE in layers
        assert LayerID.META in layers

        assert len(layers) == 4

    def test_utility_requires_minimal_layers(self, resolver):
        """Test that utility methods require minimal layers."""
        layers = resolver.get_required_layers("test.Util.format")

        assert LayerID.BASE in layers
        assert LayerID.CHAIN in layers
        assert LayerID.META in layers

        # Should NOT require analytical layers
        assert LayerID.UNIT not in layers
        assert LayerID.QUESTION not in layers
        assert LayerID.DIMENSION not in layers
        assert LayerID.POLICY not in layers
        assert LayerID.CONGRUENCE not in layers

    def test_unknown_role_uses_conservative_fallback(self, resolver):
        """Test that unknown roles get all 8 layers (conservative)."""
        layers = resolver.get_required_layers("test.Unknown.mystery")

        # Should default to all layers
        assert len(layers) == 8
        assert LayerID.BASE in layers
        assert LayerID.UNIT in layers
        assert LayerID.QUESTION in layers
        assert LayerID.DIMENSION in layers
        assert LayerID.POLICY in layers
        assert LayerID.CONGRUENCE in layers
        assert LayerID.CHAIN in layers
        assert LayerID.META in layers

    def test_missing_layer_field_uses_conservative_fallback(self, resolver):
        """Test that methods without 'layer' field get all 8 layers."""
        layers = resolver.get_required_layers("test.NoLayer.method")

        # Should default to all layers
        assert len(layers) == 8

    def test_nonexistent_method_uses_conservative_fallback(self, resolver):
        """Test that nonexistent methods get all 8 layers."""
        layers = resolver.get_required_layers("completely.unknown.method")

        # Should default to all layers
        assert len(layers) == 8

    def test_all_mappings_include_base(self, resolver):
        """Test that BASE layer is always included."""
        # Test all predefined roles
        for role in ["analyzer", "processor", "ingest", "aggregate", "report", "utility"]:
            layers = resolver.ROLE_LAYER_MAP[role]
            assert LayerID.BASE in layers, f"Role '{role}' must include BASE layer"

    def test_should_skip_layer_for_utility(self, resolver):
        """Test layer skipping for utility methods."""
        method = "test.Util.format"

        # Should NOT skip minimal layers
        assert resolver.should_skip_layer(method, LayerID.BASE) is False
        assert resolver.should_skip_layer(method, LayerID.CHAIN) is False
        assert resolver.should_skip_layer(method, LayerID.META) is False

        # SHOULD skip analytical layers
        assert resolver.should_skip_layer(method, LayerID.UNIT) is True
        assert resolver.should_skip_layer(method, LayerID.QUESTION) is True
        assert resolver.should_skip_layer(method, LayerID.DIMENSION) is True
        assert resolver.should_skip_layer(method, LayerID.POLICY) is True
        assert resolver.should_skip_layer(method, LayerID.CONGRUENCE) is True

    def test_should_skip_layer_for_analyzer(self, resolver):
        """Test that analyzer methods don't skip any layers."""
        method = "test.Analyzer.analyze"

        # Analyzer should NOT skip any layer
        assert resolver.should_skip_layer(method, LayerID.BASE) is False
        assert resolver.should_skip_layer(method, LayerID.UNIT) is False
        assert resolver.should_skip_layer(method, LayerID.QUESTION) is False
        assert resolver.should_skip_layer(method, LayerID.DIMENSION) is False
        assert resolver.should_skip_layer(method, LayerID.POLICY) is False
        assert resolver.should_skip_layer(method, LayerID.CONGRUENCE) is False
        assert resolver.should_skip_layer(method, LayerID.CHAIN) is False
        assert resolver.should_skip_layer(method, LayerID.META) is False

    def test_should_skip_layer_string_input(self, resolver):
        """Test that should_skip_layer works with string layer IDs."""
        method = "test.Util.format"

        # Should work with strings
        assert resolver.should_skip_layer(method, "b") is False
        assert resolver.should_skip_layer(method, "u") is True
        assert resolver.should_skip_layer(method, "q") is True
        assert resolver.should_skip_layer(method, "chain") is False

    def test_get_layer_summary(self, resolver):
        """Test get_layer_summary returns readable summary."""
        summary = resolver.get_layer_summary("test.Analyzer.analyze")
        assert "analyzer" in summary.lower()
        assert "8 layers" in summary

        summary2 = resolver.get_layer_summary("test.Util.format")
        assert "utility" in summary2.lower()
        assert "3 layers" in summary2

    def test_get_skipped_layers(self, resolver):
        """Test get_skipped_layers returns correct set."""
        skipped = resolver.get_skipped_layers("test.Util.format")

        assert LayerID.UNIT in skipped
        assert LayerID.QUESTION in skipped
        assert LayerID.DIMENSION in skipped
        assert LayerID.POLICY in skipped
        assert LayerID.CONGRUENCE in skipped

        assert LayerID.BASE not in skipped
        assert LayerID.CHAIN not in skipped
        assert LayerID.META not in skipped

    def test_validation_all_roles_include_base(self):
        """Test that initialization fails if any role doesn't include BASE."""
        # This is tested at the class level, but let's verify
        for role, layers in LayerRequirementsResolver.ROLE_LAYER_MAP.items():
            assert LayerID.BASE in layers, f"Role {role} missing BASE layer"


class TestLayerRequirementsWithRealData:
    """Tests using the actual intrinsic_calibration.json file."""

    def test_real_data_loads(self):
        """Test that resolver works with real calibration file."""
        real_path = "config/intrinsic_calibration.json"

        if not Path(real_path).exists():
            pytest.skip("Real calibration file not found")

        loader = IntrinsicScoreLoader(real_path)
        resolver = LayerRequirementsResolver(loader)

        # Get a few real methods
        stats = loader.get_statistics()
        assert stats["computed"] > 0

    def test_real_data_always_includes_base(self):
        """Test that all real methods always get BASE layer."""
        real_path = "config/intrinsic_calibration.json"

        if not Path(real_path).exists():
            pytest.skip("Real calibration file not found")

        loader = IntrinsicScoreLoader(real_path)
        resolver = LayerRequirementsResolver(loader)

        # Check a few methods
        loader._ensure_loaded()
        for method_id in list(loader._methods.keys())[:20]:
            layers = resolver.get_required_layers(method_id)
            assert LayerID.BASE in layers, f"Method {method_id} missing BASE layer"
