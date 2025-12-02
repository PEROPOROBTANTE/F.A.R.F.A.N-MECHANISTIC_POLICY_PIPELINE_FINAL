#!/usr/bin/env python3
"""Test inventory completeness - verifies all critical methods are present

DEPRECATED: Test uses hardcoded methods_inventory_raw.json path and outdated critical method patterns.
See tests/DEPRECATED_TESTS.md for details.
"""

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.obsolete

CRITICAL_METHODS = [
    "analysis.derek_beach.CDAFException._format_message",
    "analysis.derek_beach.CDAFException.to_dict",
    "analysis.derek_beach.ConfigLoader._load_config",
    "analysis.derek_beach.ConfigLoader._validate_config",
    "analysis.derek_beach.BeachEvidentialTest.classify_test",
    "analysis.derek_beach.BeachEvidentialTest.apply_test_logic",
    "core.aggregation.AreaPolicyAggregator",
    "core.aggregation.ClusterAggregator",
    "core.aggregation.DimensionAggregator",
    "core.aggregation.MacroAggregator",
    "processing.aggregation.AreaPolicyAggregator",
    "processing.aggregation.ClusterAggregator",
    "processing.aggregation.DimensionAggregator",
    "processing.aggregation.MacroAggregator",
    "core.orchestrator.executors",
    "core.orchestrator.executors_contract",
]


@pytest.fixture
def inventory():
    """Load the inventory JSON file"""
    inventory_path = Path("methods_inventory_raw.json")

    if not inventory_path.exists():
        pytest.fail(f"Inventory file not found: {inventory_path}")

    with open(inventory_path, encoding="utf-8") as f:
        return json.load(f)


def test_inventory_exists():
    """Verify inventory file exists"""
    assert Path("methods_inventory_raw.json").exists(), "Inventory file must exist"


def test_minimum_method_count(inventory):
    """Verify at least 200 methods in inventory"""
    total = inventory["metadata"]["total_methods"]
    assert total >= 200, f"Insufficient methods: {total} < 200"


def test_critical_files_present(inventory):
    """Verify methods from critical files are present"""
    methods = inventory["methods"]
    source_files = {m["source_file"] for m in methods}

    critical_files = [
        "derek_beach.py",
        "aggregation.py",
        "executors.py",
        "executors_contract.py",
    ]

    for critical_file in critical_files:
        found = any(critical_file in sf for sf in source_files)
        assert found, f"Critical file not found in inventory: {critical_file}"


def test_critical_method_patterns(inventory):
    """Verify critical method patterns are present"""
    methods = inventory["methods"]
    canonical_ids = {m["canonical_identifier"] for m in methods}

    patterns_to_check = [
        "derek_beach",
        "aggregation",
        "executors",
    ]

    for pattern in patterns_to_check:
        found = any(pattern in cid.lower() for cid in canonical_ids)
        assert found, f"No methods found matching pattern: {pattern}"


def test_all_roles_present(inventory):
    """Verify all expected roles are present"""
    stats = inventory["statistics"]["by_role"]

    expected_roles = [
        "ingest", "processor", "analyzer", "extractor",
        "score", "utility", "orchestrator", "core", "executor"
    ]

    for role in expected_roles:
        assert role in stats, f"Role not found in inventory: {role}"


def test_calibration_flags_set(inventory):
    """Verify calibration flags are properly set"""
    methods = inventory["methods"]

    calibration_count = sum(1 for m in methods if m["requiere_calibracion"])
    parametrization_count = sum(1 for m in methods if m["requiere_parametrizacion"])

    assert calibration_count > 0, "No methods flagged for calibration"
    assert parametrization_count > 0, "No methods flagged for parametrization"


def test_canonical_identifier_format(inventory):
    """Verify canonical identifiers follow module.Class.method format"""
    methods = inventory["methods"]

    for method in methods:
        cid = method["canonical_identifier"]
        parts = cid.split(".")

        assert len(parts) >= 2, f"Invalid canonical ID format: {cid}"

        if method["class_name"]:
            assert len(parts) >= 3, f"Class method must have at least 3 parts: {cid}"


def test_epistemology_tags_present(inventory):
    """Verify epistemology tags are assigned"""
    methods = inventory["methods"]

    tagged_count = sum(1 for m in methods if m["epistemology_tags"])
    total = len(methods)

    assert tagged_count > 0, "No methods have epistemology tags"

    tag_ratio = tagged_count / total
    assert tag_ratio > 0.3, f"Too few methods tagged: {tag_ratio:.2%}"


def test_derek_beach_methods_complete(inventory):
    """Verify derek_beach.py methods are complete"""
    methods = inventory["methods"]
    derek_methods = [m for m in methods if "derek_beach" in m["source_file"]]

    assert len(derek_methods) > 10, f"Too few derek_beach methods: {len(derek_methods)}"

    required_patterns = ["_format_message", "to_dict", "_load_config", "classify_test"]

    for pattern in required_patterns:
        found = any(pattern in m["method_name"] for m in derek_methods)
        assert found, f"Required derek_beach method not found: {pattern}"


def test_aggregation_classes_present(inventory):
    """Verify aggregation classes are present"""
    methods = inventory["methods"]
    aggregation_methods = [m for m in methods if "aggregation" in m["source_file"].lower()]

    assert len(aggregation_methods) > 0, "No aggregation methods found"

    required_classes = ["AreaPolicyAggregator", "ClusterAggregator", "DimensionAggregator"]

    found_classes = {m["class_name"] for m in aggregation_methods if m["class_name"]}

    for req_class in required_classes:
        assert req_class in found_classes, f"Required aggregation class not found: {req_class}"


def test_executor_methods_present(inventory):
    """Verify executor methods are present"""
    methods = inventory["methods"]
    executor_methods = [m for m in methods if "executor" in m["source_file"].lower()]

    assert len(executor_methods) > 5, f"Too few executor methods: {len(executor_methods)}"


def test_no_duplicate_canonical_ids(inventory):
    """Verify no duplicate canonical identifiers"""
    methods = inventory["methods"]
    canonical_ids = [m["canonical_identifier"] for m in methods]

    duplicates = [cid for cid in canonical_ids if canonical_ids.count(cid) > 1]

    assert len(duplicates) == 0, f"Duplicate canonical IDs found: {set(duplicates)}"


def test_layer_requirements_complete(inventory):
    """Verify LAYER_REQUIREMENTS table is complete"""
    layer_requirements = inventory["layer_requirements"]

    expected_layers = [
        "ingest", "processor", "analyzer", "extractor",
        "score", "utility", "orchestrator", "core", "executor"
    ]

    for layer in expected_layers:
        assert layer in layer_requirements, f"Layer missing from requirements: {layer}"
        assert "description" in layer_requirements[layer]
        assert "typical_patterns" in layer_requirements[layer]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
