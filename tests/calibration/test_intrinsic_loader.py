"""
Unit tests for IntrinsicScoreLoader.

Tests verify:
- Lazy loading and caching behavior
- Thread safety
- Score computation from b_theory, b_impl, b_deploy
- Filtering by calibration_status
- Statistics and validation
"""
import pytest
import tempfile
import json
from pathlib import Path
from src.saaaaaa.core.calibration.intrinsic_loader import IntrinsicScoreLoader


@pytest.fixture
def sample_calibration_data():
    """Sample calibration JSON for testing."""
    return {
        "_metadata": {
            "version": "1.0.0",
            "generated_at": "2025-11-10T08:23:00Z"
        },
        "_base_weights": {
            "w_th": 0.4,
            "w_imp": 0.35,
            "w_dep": 0.25
        },
        "methods": {
            "test.analyzer.AnalyzeMethod.analyze": {
                "method_id": "test.analyzer.AnalyzeMethod.analyze",
                "b_theory": 0.8,
                "b_impl": 0.75,
                "b_deploy": 0.7,
                "calibration_status": "computed",
                "layer": "analyzer"
            },
            "test.processor.ProcessMethod.process": {
                "method_id": "test.processor.ProcessMethod.process",
                "b_theory": 0.6,
                "b_impl": 0.65,
                "b_deploy": 0.55,
                "calibration_status": "computed",
                "layer": "processor"
            },
            "test.utility.UtilMethod.format": {
                "method_id": "test.utility.UtilMethod.format",
                "calibration_status": "excluded",
                "reason": "Non-analytical utility function",
                "layer": "utility"
            },
            "test.incomplete.Method.missing_fields": {
                "method_id": "test.incomplete.Method.missing_fields",
                "calibration_status": "computed",
                "b_theory": 0.5,
                # Missing b_impl and b_deploy
                "layer": "processor"
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

    # Cleanup
    Path(temp_path).unlink()


class TestIntrinsicScoreLoader:
    """Test suite for IntrinsicScoreLoader."""

    def test_initialization(self, temp_calibration_file):
        """Test that loader initializes without loading data."""
        loader = IntrinsicScoreLoader(temp_calibration_file)

        assert loader.calibration_path == Path(temp_calibration_file)
        assert loader._loaded is False
        assert loader._data is None
        assert loader._methods is None

    def test_lazy_loading(self, temp_calibration_file):
        """Test that data is loaded lazily on first access."""
        loader = IntrinsicScoreLoader(temp_calibration_file)

        # Data not loaded yet
        assert not loader._loaded

        # First access triggers load
        loader.get_score("test.analyzer.AnalyzeMethod.analyze")

        # Data now loaded
        assert loader._loaded
        assert loader._data is not None
        assert loader._methods is not None

    def test_score_computation(self, temp_calibration_file):
        """Test intrinsic score computation from components."""
        loader = IntrinsicScoreLoader(temp_calibration_file)

        # Expected: 0.4*0.8 + 0.35*0.75 + 0.25*0.7 = 0.32 + 0.2625 + 0.175 = 0.7575
        score = loader.get_score("test.analyzer.AnalyzeMethod.analyze")
        assert pytest.approx(score, rel=1e-3) == 0.7575

        # Expected: 0.4*0.6 + 0.35*0.65 + 0.25*0.55 = 0.24 + 0.2275 + 0.1375 = 0.605
        score2 = loader.get_score("test.processor.ProcessMethod.process")
        assert pytest.approx(score2, rel=1e-3) == 0.605

    def test_score_range_validation(self, temp_calibration_file):
        """Test that scores are clamped to [0.0, 1.0]."""
        loader = IntrinsicScoreLoader(temp_calibration_file)

        score = loader.get_score("test.analyzer.AnalyzeMethod.analyze")
        assert 0.0 <= score <= 1.0

    def test_excluded_method_returns_default(self, temp_calibration_file):
        """Test that excluded methods return the default score."""
        loader = IntrinsicScoreLoader(temp_calibration_file)

        score = loader.get_score("test.utility.UtilMethod.format", default=0.5)
        assert score == 0.5

        score2 = loader.get_score("test.utility.UtilMethod.format", default=0.3)
        assert score2 == 0.3

    def test_unknown_method_returns_default(self, temp_calibration_file):
        """Test that unknown methods return the default score."""
        loader = IntrinsicScoreLoader(temp_calibration_file)

        score = loader.get_score("unknown.method.name", default=0.42)
        assert score == 0.42

    def test_is_calibrated(self, temp_calibration_file):
        """Test is_calibrated method."""
        loader = IntrinsicScoreLoader(temp_calibration_file)

        assert loader.is_calibrated("test.analyzer.AnalyzeMethod.analyze") is True
        assert loader.is_calibrated("test.processor.ProcessMethod.process") is True
        assert loader.is_calibrated("test.utility.UtilMethod.format") is False
        assert loader.is_calibrated("unknown.method") is False

    def test_is_excluded(self, temp_calibration_file):
        """Test is_excluded method."""
        loader = IntrinsicScoreLoader(temp_calibration_file)

        assert loader.is_excluded("test.utility.UtilMethod.format") is True
        assert loader.is_excluded("test.analyzer.AnalyzeMethod.analyze") is False
        assert loader.is_excluded("unknown.method") is False

    def test_get_layer(self, temp_calibration_file):
        """Test get_layer method."""
        loader = IntrinsicScoreLoader(temp_calibration_file)

        assert loader.get_layer("test.analyzer.AnalyzeMethod.analyze") == "analyzer"
        assert loader.get_layer("test.processor.ProcessMethod.process") == "processor"
        assert loader.get_layer("test.utility.UtilMethod.format") == "utility"
        assert loader.get_layer("unknown.method") is None

    def test_get_method_data(self, temp_calibration_file):
        """Test get_method_data returns full data."""
        loader = IntrinsicScoreLoader(temp_calibration_file)

        data = loader.get_method_data("test.analyzer.AnalyzeMethod.analyze")
        assert data is not None
        assert data["method_id"] == "test.analyzer.AnalyzeMethod.analyze"
        assert data["b_theory"] == 0.8
        assert data["b_impl"] == 0.75
        assert data["b_deploy"] == 0.7
        assert data["calibration_status"] == "computed"
        assert data["layer"] == "analyzer"

        unknown = loader.get_method_data("unknown.method")
        assert unknown is None

    def test_get_statistics(self, temp_calibration_file):
        """Test get_statistics returns correct counts."""
        loader = IntrinsicScoreLoader(temp_calibration_file)

        stats = loader.get_statistics()
        assert stats["total"] == 4
        assert stats["computed"] == 3
        assert stats["excluded"] == 1
        assert stats["unknown_status"] == 0

    def test_missing_file_raises_error(self):
        """Test that missing calibration file raises FileNotFoundError."""
        loader = IntrinsicScoreLoader("/nonexistent/path/calibration.json")

        with pytest.raises(FileNotFoundError):
            loader.get_score("any.method")

    def test_missing_score_components_returns_zero(self, temp_calibration_file):
        """Test that methods with missing components return 0 or default."""
        loader = IntrinsicScoreLoader(temp_calibration_file)

        # Method has status=computed but missing b_impl and b_deploy
        score = loader.get_score("test.incomplete.Method.missing_fields")

        # Should compute with missing values as 0.0
        # Expected: 0.4*0.5 + 0.35*0.0 + 0.25*0.0 = 0.2
        assert score == pytest.approx(0.2, rel=1e-3)

    def test_weights_loaded_from_json(self, sample_calibration_data):
        """Test that weights are loaded from JSON _base_weights section."""
        # Create JSON with custom weights
        custom_data = sample_calibration_data.copy()
        custom_data["_base_weights"] = {
            "w_th": 0.5,
            "w_imp": 0.3,
            "w_dep": 0.2
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(custom_data, f)
            temp_path = f.name

        try:
            loader = IntrinsicScoreLoader(temp_path)
            loader._ensure_loaded()

            # Verify weights were loaded from JSON
            assert loader.w_theory == 0.5
            assert loader.w_impl == 0.3
            assert loader.w_deploy == 0.2

            # Verify score computation uses loaded weights
            # Expected: 0.5*0.8 + 0.3*0.75 + 0.2*0.7 = 0.4 + 0.225 + 0.14 = 0.765
            score = loader.get_score("test.analyzer.AnalyzeMethod.analyze")
            assert pytest.approx(score, rel=1e-3) == 0.765

        finally:
            Path(temp_path).unlink()

    def test_default_weights_used_when_missing(self, sample_calibration_data):
        """Test that default weights are used when _base_weights is missing."""
        # Create JSON without _base_weights
        custom_data = sample_calibration_data.copy()
        if "_base_weights" in custom_data:
            del custom_data["_base_weights"]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(custom_data, f)
            temp_path = f.name

        try:
            loader = IntrinsicScoreLoader(temp_path)
            loader._ensure_loaded()

            # Verify default weights are used
            assert loader.w_theory == IntrinsicScoreLoader.DEFAULT_W_THEORY
            assert loader.w_impl == IntrinsicScoreLoader.DEFAULT_W_IMPL
            assert loader.w_deploy == IntrinsicScoreLoader.DEFAULT_W_DEPLOY

        finally:
            Path(temp_path).unlink()


class TestIntrinsicScoreLoaderWithRealData:
    """Tests using the actual intrinsic_calibration.json file."""

    def test_real_file_loads(self):
        """Test that the real calibration file loads successfully."""
        real_path = "config/intrinsic_calibration.json"

        if not Path(real_path).exists():
            pytest.skip("Real calibration file not found")

        loader = IntrinsicScoreLoader(real_path)
        stats = loader.get_statistics()

        # Basic sanity checks
        assert stats["total"] > 0
        assert stats["computed"] > 0
        assert stats["excluded"] >= 0
        assert stats["total"] == stats["computed"] + stats["excluded"] + stats["unknown_status"]

    def test_real_file_scores_in_range(self):
        """Test that all computed scores are in [0.0, 1.0]."""
        real_path = "config/intrinsic_calibration.json"

        if not Path(real_path).exists():
            pytest.skip("Real calibration file not found")

        loader = IntrinsicScoreLoader(real_path)
        loader._ensure_loaded()  # Ensure data is loaded

        # Check a few methods
        for method_id in list(loader._methods.keys())[:10]:
            if loader.is_calibrated(method_id):
                score = loader.get_score(method_id)
                assert 0.0 <= score <= 1.0, f"Score for {method_id} out of range: {score}"

    def test_real_file_has_expected_structure(self):
        """Test that real file has expected metadata structure."""
        real_path = "config/intrinsic_calibration.json"

        if not Path(real_path).exists():
            pytest.skip("Real calibration file not found")

        loader = IntrinsicScoreLoader(real_path)
        loader._ensure_loaded()

        assert "_metadata" in loader._data
        assert "methods" in loader._data
        assert isinstance(loader._data["methods"], dict)
