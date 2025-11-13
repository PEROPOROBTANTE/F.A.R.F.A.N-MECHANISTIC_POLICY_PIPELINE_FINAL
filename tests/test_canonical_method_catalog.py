"""Tests for Canonical Method Catalog System

This test suite validates the canonical method catalog implementation
against directive requirements:

1. Universal coverage - no methods omitted
2. Machine-readable calibration flags
3. Complete calibration tracking
4. Transitional cases explicitly managed
5. Single source of truth
"""

import json
import pytest
from pathlib import Path


# Fixtures

@pytest.fixture
def repo_root():
    """Get repository root."""
    return Path(__file__).parent.parent


@pytest.fixture
def catalog_data(repo_root):
    """Load canonical method catalog."""
    catalog_path = repo_root / "config" / "canonical_method_catalog.json"
    assert catalog_path.exists(), "Canonical catalog not found"
    
    with open(catalog_path) as f:
        return json.load(f)


@pytest.fixture
def embedded_appendix(repo_root):
    """Load embedded calibration appendix."""
    appendix_path = repo_root / "config" / "embedded_calibration_appendix.json"
    if not appendix_path.exists():
        return None
    
    with open(appendix_path) as f:
        return json.load(f)


# Test Directive Compliance

class TestDirectiveCompliance:
    """Test compliance with directive requirements."""
    
    def test_universal_coverage_flag(self, catalog_data):
        """Directive requirement: Universal coverage must be declared."""
        compliance = catalog_data['metadata']['directive_compliance']
        assert compliance['universal_coverage'] is True
    
    def test_no_filters_applied_flag(self, catalog_data):
        """Directive requirement: No filters can be applied."""
        compliance = catalog_data['metadata']['directive_compliance']
        assert compliance['no_filters_applied'] is True
    
    def test_machine_readable_flags(self, catalog_data):
        """Directive requirement: Machine-readable flags must exist."""
        compliance = catalog_data['metadata']['directive_compliance']
        assert compliance['machine_readable_flags'] is True
    
    def test_single_canonical_source(self, catalog_data):
        """Directive requirement: Single source of truth."""
        compliance = catalog_data['metadata']['directive_compliance']
        assert compliance['single_canonical_source'] is True
    
    def test_catalog_not_empty(self, catalog_data):
        """Directive requirement: Catalog must enumerate ALL methods."""
        assert catalog_data['summary']['total_methods'] > 0
        # Expect at least 1000 methods in a real repository
        assert catalog_data['summary']['total_methods'] >= 1000


class TestMethodMetadata:
    """Test method metadata completeness."""
    
    def test_all_methods_have_unique_id(self, catalog_data):
        """Every method must have a unique identifier."""
        methods = catalog_data['methods']
        
        for method in methods:
            assert 'unique_id' in method
            assert method['unique_id']
            assert isinstance(method['unique_id'], str)
            assert len(method['unique_id']) == 16  # SHA256 truncated to 16
    
    def test_unique_ids_are_unique(self, catalog_data):
        """Unique IDs must actually be unique."""
        methods = catalog_data['methods']
        unique_ids = [m['unique_id'] for m in methods]
        
        assert len(unique_ids) == len(set(unique_ids))
    
    def test_all_methods_have_canonical_name(self, catalog_data):
        """Every method must have a canonical name."""
        methods = catalog_data['methods']
        
        for method in methods:
            assert 'canonical_name' in method
            assert method['canonical_name']
            # Should be in format: module.Class.method or module.function
            assert '.' in method['canonical_name']
    
    def test_all_methods_have_layer(self, catalog_data):
        """Every method must have layer positionality."""
        methods = catalog_data['methods']
        
        for method in methods:
            assert 'layer' in method
            assert method['layer']
            assert 'layer_position' in method
            assert isinstance(method['layer_position'], int)
            assert method['layer_position'] >= 0
    
    def test_all_methods_have_file_path(self, catalog_data):
        """Every method must reference its source file."""
        methods = catalog_data['methods']
        
        for method in methods:
            assert 'file_path' in method
            assert method['file_path']
            assert 'line_number' in method
            assert isinstance(method['line_number'], int)
            assert method['line_number'] > 0


class TestCalibrationTracking:
    """Test calibration requirement and status tracking."""
    
    def test_all_methods_have_calibration_flag(self, catalog_data):
        """Directive requirement: Calibration must be mechanically decidable."""
        methods = catalog_data['methods']
        
        for method in methods:
            assert 'requires_calibration' in method
            assert isinstance(method['requires_calibration'], bool)
    
    def test_all_methods_have_calibration_status(self, catalog_data):
        """Directive requirement: Calibration status must be explicit."""
        methods = catalog_data['methods']
        valid_statuses = {'centralized', 'embedded', 'none', 'unknown'}
        
        for method in methods:
            assert 'calibration_status' in method
            assert method['calibration_status'] in valid_statuses
    
    def test_calibration_status_consistency(self, catalog_data):
        """Calibration flag and status must be consistent."""
        methods = catalog_data['methods']
        
        for method in methods:
            requires = method['requires_calibration']
            status = method['calibration_status']
            
            # If doesn't require calibration, status must be 'none'
            if not requires:
                assert status == 'none', (
                    f"Method {method['canonical_name']} doesn't require "
                    f"calibration but has status '{status}'"
                )
            
            # If requires calibration, status cannot be 'none'
            if requires:
                assert status != 'none', (
                    f"Method {method['canonical_name']} requires "
                    f"calibration but has status 'none'"
                )
    
    def test_centralized_calibrations_reference_registry(self, catalog_data):
        """Centralized calibrations must reference calibration_registry.py."""
        centralized = catalog_data['calibration_tracking']['centralized']
        
        for method in centralized:
            assert 'calibration_location' in method
            location = method['calibration_location']
            assert 'calibration_registry.py' in location
    
    def test_embedded_calibrations_have_location(self, catalog_data):
        """Embedded calibrations must have file:line location."""
        embedded = catalog_data['calibration_tracking']['embedded']
        
        for method in embedded:
            assert 'calibration_location' in method
            location = method['calibration_location']
            assert location
            assert ':' in location  # file:line format


class TestMigrationBacklog:
    """Test migration backlog for embedded calibrations."""
    
    def test_embedded_count_matches_appendix(self, catalog_data, embedded_appendix):
        """Directive requirement: All embedded calibrations must be tracked."""
        if embedded_appendix is None:
            # If no appendix, there should be no embedded calibrations
            embedded_count = catalog_data['summary']['by_calibration_status']['embedded']
            assert embedded_count == 0
            return
        
        catalog_embedded = catalog_data['summary']['by_calibration_status']['embedded']
        appendix_embedded = embedded_appendix['metadata']['total_embedded']
        
        assert catalog_embedded == appendix_embedded, (
            f"Embedded count mismatch: catalog={catalog_embedded}, "
            f"appendix={appendix_embedded}"
        )
    
    def test_embedded_calibrations_have_migration_metadata(self, catalog_data):
        """Embedded calibrations must have migration metadata."""
        embedded = catalog_data['calibration_tracking']['embedded']
        
        for method in embedded:
            assert 'embedded_calibration' in method
            meta = method['embedded_calibration']
            
            assert 'pattern_type' in meta
            assert 'parameter_count' in meta
            assert 'migration_priority' in meta
            assert 'migration_complexity' in meta
            
            # Priority must be valid
            assert meta['migration_priority'] in ['critical', 'high', 'medium', 'low']
            
            # Complexity must be valid
            assert meta['migration_complexity'] in ['simple', 'moderate', 'complex']
    
    def test_critical_priority_exists_in_appendix(self, embedded_appendix):
        """Critical priority items must be in appendix."""
        if embedded_appendix is None:
            pytest.skip("No embedded calibrations")
        
        critical_count = embedded_appendix['metadata']['by_priority'].get('critical', 0)
        
        if critical_count > 0:
            # Critical items should be in the embedded_calibrations list
            critical_items = [
                c for c in embedded_appendix['embedded_calibrations']
                if c['migration_priority'] == 'critical'
            ]
            assert len(critical_items) == critical_count


class TestLayerClassification:
    """Test layer classification."""
    
    def test_layer_counts_match_methods(self, catalog_data):
        """Layer counts in summary must match actual methods."""
        by_layer = catalog_data['summary']['by_layer']
        methods = catalog_data['methods']
        
        # Count methods by layer
        actual_counts = {}
        for method in methods:
            layer = method['layer']
            actual_counts[layer] = actual_counts.get(layer, 0) + 1
        
        assert by_layer == actual_counts
    
    def test_layer_values_are_valid(self, catalog_data):
        """Layer values should be from expected set."""
        valid_layers = {
            'orchestrator', 'executor', 'analyzer', 'processor',
            'ingestion', 'utility', 'validation', 'contracts', 'unknown'
        }
        
        by_layer = catalog_data['summary']['by_layer']
        
        for layer in by_layer.keys():
            assert layer in valid_layers, f"Unexpected layer: {layer}"
    
    def test_unknown_layer_percentage(self, catalog_data):
        """Unknown layer percentage should be reasonable (< 20%)."""
        by_layer = catalog_data['summary']['by_layer']
        total = sum(by_layer.values())
        unknown = by_layer.get('unknown', 0)
        
        percentage = (unknown / total) * 100
        assert percentage < 20.0, (
            f"Too many unknown layers: {unknown}/{total} = {percentage:.1f}%"
        )


class TestSummaryConsistency:
    """Test summary statistics consistency."""
    
    def test_total_methods_consistency(self, catalog_data):
        """Total in metadata must match actual method count."""
        metadata_total = catalog_data['metadata']['total_methods']
        summary_total = catalog_data['summary']['total_methods']
        actual_total = len(catalog_data['methods'])
        
        assert metadata_total == summary_total == actual_total
    
    def test_calibration_status_counts(self, catalog_data):
        """Calibration status counts must sum to total."""
        by_status = catalog_data['summary']['by_calibration_status']
        total_methods = catalog_data['summary']['total_methods']
        
        status_sum = sum(by_status.values())
        assert status_sum == total_methods
    
    def test_layer_counts_sum(self, catalog_data):
        """Layer counts must sum to total."""
        by_layer = catalog_data['summary']['by_layer']
        total_methods = catalog_data['summary']['total_methods']
        
        layer_sum = sum(by_layer.values())
        assert layer_sum == total_methods


class TestCalibrationCoverage:
    """Test calibration coverage metrics."""
    
    def test_requires_calibration_count(self, catalog_data):
        """Requires calibration count must match actual."""
        coverage = catalog_data['summary']['calibration_coverage']
        methods = catalog_data['methods']
        
        actual_requires = len([m for m in methods if m['requires_calibration']])
        
        assert coverage['requires_calibration'] == actual_requires
    
    def test_centralized_count(self, catalog_data):
        """Centralized count must match."""
        coverage = catalog_data['summary']['calibration_coverage']
        by_status = catalog_data['summary']['by_calibration_status']
        
        assert coverage['centralized'] == by_status['centralized']
    
    def test_migration_needed_calculation(self, catalog_data):
        """Migration needed should be embedded + unknown."""
        coverage = catalog_data['summary']['calibration_coverage']
        
        expected_migration = (
            coverage['embedded'] + coverage['unknown']
        )
        
        assert coverage['migration_needed'] == expected_migration


# Integration Tests

class TestIntegrationWithCalibrationRegistry:
    """Test integration with calibration_registry.py."""
    
    def test_centralized_methods_exist_in_registry(self, catalog_data, repo_root):
        """Centralized calibrations should exist in calibration_registry.py."""
        registry_path = repo_root / "src" / "saaaaaa" / "core" / "orchestrator" / "calibration_registry.py"
        
        if not registry_path.exists():
            pytest.skip("calibration_registry.py not found")
        
        with open(registry_path) as f:
            registry_content = f.read()
        
        centralized = catalog_data['calibration_tracking']['centralized']
        
        # Sample check - not all methods (too slow)
        sample_size = min(10, len(centralized))
        for method in centralized[:sample_size]:
            if method.get('class_name'):
                # Look for key pattern
                key_pattern = f'("{method["class_name"]}", "{method["method_name"]}")'
                assert key_pattern in registry_content, (
                    f"Method {method['canonical_name']} not found in registry"
                )


# Property-based tests

class TestMethodProperties:
    """Test properties that should hold for all methods."""
    
    def test_all_methods_have_source_hash(self, catalog_data):
        """All methods should have source hash for tracking changes."""
        methods = catalog_data['methods']
        
        for method in methods:
            assert 'source_hash' in method
            assert method['source_hash']
    
    def test_all_methods_have_timestamp(self, catalog_data):
        """All methods should have last_analyzed timestamp."""
        methods = catalog_data['methods']
        
        for method in methods:
            assert 'last_analyzed' in method
            assert method['last_analyzed']
            # Should be ISO format
            assert 'T' in method['last_analyzed']
    
    def test_signature_format(self, catalog_data):
        """Method signatures should be well-formed."""
        methods = catalog_data['methods']
        
        for method in methods:
            assert 'signature' in method
            sig = method['signature']
            # Should contain method name and parentheses
            assert method['method_name'] in sig
            assert '(' in sig
