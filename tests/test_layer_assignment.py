"""
Test suite for layer assignment system.

VERIFICATION CONDITIONS:
1. All methods must have layer mappings
2. All executors must have exactly 8 layers
3. JSON contains ONLY metadata (no numeric scores outside weights)
4. Sum of weights per executor must equal 1.0

FAILURE CONDITIONS:
- If <30 executors identified: ABORT with 'layer assignment corrupted'
- If any score appears in JSON (outside weights): ABORT with 'layer assignment corrupted'

DEPRECATED: Test assumes outdated canonic_inventorry_methods_layers.json structure.
See tests/DEPRECATED_TESTS.md for details.
"""

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.obsolete

REPO_ROOT = Path(__file__).parent.parent
CONFIG_FILE = REPO_ROOT / "config" / "canonic_inventorry_methods_layers.json"
EXECUTORS_FILE = (
    REPO_ROOT / "src" / "farfan_pipeline" / "core" / "orchestrator" / "executors.py"
)


class TestLayerAssignment:

    @pytest.fixture
    def inventory_data(self):
        """Load the canonical inventory JSON."""
        if not CONFIG_FILE.exists():
            pytest.fail(f"Config file not found: {CONFIG_FILE}")

        with open(CONFIG_FILE) as f:
            return json.load(f)

    def test_minimum_executor_count(self, inventory_data):
        """Verify at least 30 executors are identified."""
        method_count = len(inventory_data["methods"])
        assert (
            method_count >= 30
        ), f"layer assignment corrupted: Found {method_count} executors, expected 30"

    def test_all_methods_have_layer_mappings(self, inventory_data):
        """Verify every method has layer mappings."""
        for method_id, method_data in inventory_data["methods"].items():
            assert (
                "layers" in method_data
            ), f"layer assignment corrupted: Method {method_id} missing 'layers'"
            assert isinstance(
                method_data["layers"], list
            ), f"layer assignment corrupted: Method {method_id} 'layers' is not a list"
            assert (
                len(method_data["layers"]) > 0
            ), f"layer assignment corrupted: Method {method_id} has empty 'layers'"

    def test_all_executors_have_8_layers(self, inventory_data):
        """Verify all executors have exactly 8 layers."""
        for method_id, method_data in inventory_data["methods"].items():
            if method_data.get("role") == "executor":
                layer_count = len(method_data["layers"])
                assert layer_count == 8, (
                    f"layer assignment corrupted: Executor {method_id} has "
                    f"{layer_count} layers, expected 8"
                )

    def test_no_numeric_scores_in_json(self, inventory_data):
        """Verify JSON contains only metadata, not numeric scores."""

        def check_for_scores(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key

                    if key in ["weights", "interaction_weights"]:
                        continue

                    if key in ["version", "total_executors"]:
                        continue

                    if isinstance(value, int | float) and key not in [
                        "version",
                        "total_executors",
                    ]:
                        if current_path.endswith(("weights", "interaction_weights")):
                            continue
                        pytest.fail(
                            f"layer assignment corrupted: Found numeric score in JSON "
                            f"at {current_path}={value}"
                        )

                    check_for_scores(value, current_path)

            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_for_scores(item, f"{path}[{i}]")

        check_for_scores(inventory_data)

    def test_weights_sum_to_one(self, inventory_data):
        """Verify sum of weights per executor equals 1.0."""
        for method_id, method_data in inventory_data["methods"].items():
            weights = method_data.get("weights", {})
            interaction_weights = method_data.get("interaction_weights", {})

            total = sum(weights.values()) + sum(interaction_weights.values())

            assert abs(total - 1.0) < 0.01, (
                f"layer assignment corrupted: Weights for {method_id} "
                f"sum to {total:.4f}, expected 1.0"
            )

    def test_required_metadata_fields(self, inventory_data):
        """Verify all methods have required metadata fields."""
        required_fields = ["method_id", "role", "layers", "weights", "aggregator_type"]

        for method_id, method_data in inventory_data["methods"].items():
            for field in required_fields:
                assert field in method_data, (
                    f"layer assignment corrupted: Method {method_id} missing "
                    f"required field '{field}'"
                )

    def test_layer_names_are_valid(self, inventory_data):
        """Verify all layer names match the canonical set."""
        valid_layers = {"@b", "@chain", "@q", "@d", "@p", "@C", "@u", "@m"}

        for method_id, method_data in inventory_data["methods"].items():
            layers = set(method_data["layers"])
            invalid = layers - valid_layers

            assert not invalid, (
                f"layer assignment corrupted: Method {method_id} has invalid "
                f"layers: {invalid}"
            )

    def test_weights_match_layers(self, inventory_data):
        """Verify weights dict keys match assigned layers."""
        for method_id, method_data in inventory_data["methods"].items():
            layers = set(method_data["layers"])
            weight_keys = set(method_data["weights"].keys())

            assert weight_keys == layers, (
                f"layer assignment corrupted: Method {method_id} weight keys "
                f"{weight_keys} don't match layers {layers}"
            )

    def test_executor_pattern_matching(self):
        """Verify executor pattern D[1-6]Q[1-5] is correctly identified."""
        import re

        with open(EXECUTORS_FILE) as f:
            content = f.read()

        pattern = re.compile(r"class (D([1-6])_Q([1-5])_\w+)\(")
        matches = pattern.findall(content)

        assert len(matches) >= 30, (
            f"layer assignment corrupted: Found {len(matches)} executor classes, "
            f"expected 30"
        )

        for _class_name, dim, question in matches:
            assert dim in "123456", f"Invalid dimension: {dim}"
            assert question in "12345", f"Invalid question: {question}"

    def test_aggregator_type_is_choquet(self, inventory_data):
        """Verify all executors use Choquet aggregator."""
        for method_id, method_data in inventory_data["methods"].items():
            if method_data.get("role") == "executor":
                assert method_data["aggregator_type"] == "choquet", (
                    f"layer assignment corrupted: Executor {method_id} has "
                    f"aggregator_type '{method_data['aggregator_type']}', expected 'choquet'"
                )

    def test_interaction_weights_are_valid(self, inventory_data):
        """Verify interaction weights reference valid layer pairs."""
        for method_id, method_data in inventory_data["methods"].items():
            layers = set(method_data["layers"])

            for pair_key in method_data.get("interaction_weights", {}):
                if "," not in pair_key:
                    pytest.fail(
                        f"layer assignment corrupted: Invalid interaction weight key "
                        f"'{pair_key}' in {method_id}"
                    )

                l1, l2 = pair_key.split(",")
                assert l1 in layers, (
                    f"layer assignment corrupted: Interaction weight {pair_key} in "
                    f"{method_id} references layer {l1} not in assigned layers"
                )
                assert l2 in layers, (
                    f"layer assignment corrupted: Interaction weight {pair_key} in "
                    f"{method_id} references layer {l2} not in assigned layers"
                )

    def test_dimension_and_question_metadata(self, inventory_data):
        """Verify executors have dimension and question metadata."""
        for method_id, method_data in inventory_data["methods"].items():
            if method_data.get("role") == "executor":
                assert (
                    "dimension" in method_data
                ), f"layer assignment corrupted: Executor {method_id} missing 'dimension'"
                assert (
                    "question" in method_data
                ), f"layer assignment corrupted: Executor {method_id} missing 'question'"

                dim = method_data["dimension"]
                question = method_data["question"]

                assert (
                    dim.startswith("D") and dim[1:].isdigit()
                ), f"layer assignment corrupted: Invalid dimension '{dim}' in {method_id}"
                assert (
                    question.startswith("Q") and question[1:].isdigit()
                ), f"layer assignment corrupted: Invalid question '{question}' in {method_id}"


class TestLayerRequirements:
    """Test the LAYER_REQUIREMENTS table definition."""

    def test_layer_requirements_completeness(self):
        """Verify LAYER_REQUIREMENTS covers all specified roles."""
        from farfan_pipeline.core.calibration.layer_assignment import LAYER_REQUIREMENTS

        expected_roles = [
            "ingest",
            "processor",
            "analyzer",
            "score",
            "executor",
            "utility",
            "orchestrator",
            "core",
            "extractor",
        ]

        for role in expected_roles:
            assert (
                role in LAYER_REQUIREMENTS
            ), f"layer assignment corrupted: Role '{role}' missing from LAYER_REQUIREMENTS"

    def test_ingest_layers(self):
        """Verify ingest role has correct layers."""
        from farfan_pipeline.core.calibration.layer_assignment import LAYER_REQUIREMENTS

        expected = ["@b", "@chain", "@u", "@m"]
        assert LAYER_REQUIREMENTS["ingest"] == expected

    def test_processor_layers(self):
        """Verify processor role has correct layers."""
        from farfan_pipeline.core.calibration.layer_assignment import LAYER_REQUIREMENTS

        expected = ["@b", "@chain", "@u", "@m"]
        assert LAYER_REQUIREMENTS["processor"] == expected

    def test_analyzer_layers(self):
        """Verify analyzer role has correct layers."""
        from farfan_pipeline.core.calibration.layer_assignment import LAYER_REQUIREMENTS

        expected = ["@b", "@chain", "@q", "@d", "@p", "@C", "@u", "@m"]
        assert LAYER_REQUIREMENTS["analyzer"] == expected

    def test_score_layers(self):
        """Verify score role has all 8 layers."""
        from farfan_pipeline.core.calibration.layer_assignment import LAYER_REQUIREMENTS

        expected = ["@b", "@chain", "@q", "@d", "@p", "@C", "@u", "@m"]
        assert LAYER_REQUIREMENTS["score"] == expected

    def test_executor_layers(self):
        """Verify executor role has all 8 layers."""
        from farfan_pipeline.core.calibration.layer_assignment import LAYER_REQUIREMENTS

        expected = ["@b", "@chain", "@q", "@d", "@p", "@C", "@u", "@m"]
        assert LAYER_REQUIREMENTS["executor"] == expected

    def test_utility_layers(self):
        """Verify utility role has correct layers."""
        from farfan_pipeline.core.calibration.layer_assignment import LAYER_REQUIREMENTS

        expected = ["@b", "@chain", "@m"]
        assert LAYER_REQUIREMENTS["utility"] == expected

    def test_orchestrator_layers(self):
        """Verify orchestrator role has correct layers."""
        from farfan_pipeline.core.calibration.layer_assignment import LAYER_REQUIREMENTS

        expected = ["@b", "@chain", "@m"]
        assert LAYER_REQUIREMENTS["orchestrator"] == expected

    def test_core_layers(self):
        """Verify core role has all 8 layers."""
        from farfan_pipeline.core.calibration.layer_assignment import LAYER_REQUIREMENTS

        expected = ["@b", "@chain", "@q", "@d", "@p", "@C", "@u", "@m"]
        assert LAYER_REQUIREMENTS["core"] == expected

    def test_extractor_layers(self):
        """Verify extractor role has correct layers."""
        from farfan_pipeline.core.calibration.layer_assignment import LAYER_REQUIREMENTS

        expected = ["@b", "@chain", "@u", "@m"]
        assert LAYER_REQUIREMENTS["extractor"] == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
