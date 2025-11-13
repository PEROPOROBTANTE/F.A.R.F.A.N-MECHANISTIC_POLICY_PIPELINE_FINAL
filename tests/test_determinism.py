"""
Tests for Determinism Infrastructure

Validates that seed management ensures reproducible execution across
all stochastic operations.
"""

import pytest
from saaaaaa.core.orchestrator.seed_registry import (
    SeedRegistry,
    get_global_seed_registry,
    reset_global_seed_registry,
    SEED_VERSION,
)


class TestSeedRegistry:
    """Test SeedRegistry deterministic seed generation."""
    
    def test_same_inputs_produce_same_seed(self):
        """Test that identical inputs always produce identical seeds."""
        registry = SeedRegistry()
        
        seed1 = registry.get_seed("plan_2024", "exec_001", "numpy")
        seed2 = registry.get_seed("plan_2024", "exec_001", "numpy")
        
        assert seed1 == seed2
        assert isinstance(seed1, int)
        assert 0 <= seed1 < 2**32
    
    def test_different_components_produce_different_seeds(self):
        """Test that different components get different seeds."""
        registry = SeedRegistry()
        
        np_seed = registry.get_seed("plan_2024", "exec_001", "numpy")
        py_seed = registry.get_seed("plan_2024", "exec_001", "python")
        qt_seed = registry.get_seed("plan_2024", "exec_001", "quantum")
        
        # All seeds should be different
        assert np_seed != py_seed
        assert py_seed != qt_seed
        assert np_seed != qt_seed
    
    def test_different_policy_units_produce_different_seeds(self):
        """Test that different policy units get different seeds."""
        registry = SeedRegistry()
        
        seed1 = registry.get_seed("plan_2024", "exec_001", "numpy")
        seed2 = registry.get_seed("plan_2025", "exec_001", "numpy")
        
        assert seed1 != seed2
    
    def test_different_correlation_ids_produce_different_seeds(self):
        """Test that different correlation IDs get different seeds."""
        registry = SeedRegistry()
        
        seed1 = registry.get_seed("plan_2024", "exec_001", "numpy")
        seed2 = registry.get_seed("plan_2024", "exec_002", "numpy")
        
        assert seed1 != seed2
    
    def test_seed_caching_works(self):
        """Test that seeds are cached and reused."""
        registry = SeedRegistry()
        
        # First call
        seed1 = registry.get_seed("plan_2024", "exec_001", "numpy")
        audit_count_1 = len(registry.get_audit_log())
        
        # Second call (should use cache)
        seed2 = registry.get_seed("plan_2024", "exec_001", "numpy")
        audit_count_2 = len(registry.get_audit_log())
        
        assert seed1 == seed2
        assert audit_count_2 == audit_count_1  # No new audit entry
    
    def test_derive_seed_is_deterministic(self):
        """Test that derive_seed produces consistent output."""
        registry = SeedRegistry()
        
        seed1 = registry.derive_seed("test_material_123")
        seed2 = registry.derive_seed("test_material_123")
        
        assert seed1 == seed2
        assert isinstance(seed1, int)
        assert 0 <= seed1 < 2**32
    
    def test_derive_seed_different_inputs(self):
        """Test that different inputs produce different seeds."""
        registry = SeedRegistry()
        
        seed1 = registry.derive_seed("material_A")
        seed2 = registry.derive_seed("material_B")
        
        assert seed1 != seed2
    
    def test_audit_log_records_seeds(self):
        """Test that audit log records all seed generations."""
        registry = SeedRegistry()
        
        registry.get_seed("plan_2024", "exec_001", "numpy")
        registry.get_seed("plan_2024", "exec_001", "python")
        registry.get_seed("plan_2025", "exec_002", "quantum")
        
        audit_log = registry.get_audit_log()
        
        assert len(audit_log) == 3
        assert audit_log[0].policy_unit_id == "plan_2024"
        assert audit_log[0].component == "numpy"
        assert audit_log[1].component == "python"
        assert audit_log[2].policy_unit_id == "plan_2025"
        assert all(record.seed_version == SEED_VERSION for record in audit_log)
    
    def test_get_seeds_for_context(self):
        """Test getting all standard seeds for a context."""
        registry = SeedRegistry()
        
        seeds = registry.get_seeds_for_context("plan_2024", "exec_001")
        
        assert "numpy" in seeds
        assert "python" in seeds
        assert "quantum" in seeds
        assert "neuromorphic" in seeds
        assert "meta_learner" in seeds
        
        # All seeds should be different
        seed_values = list(seeds.values())
        assert len(seed_values) == len(set(seed_values))
    
    def test_clear_cache(self):
        """Test that clear_cache removes cached seeds."""
        registry = SeedRegistry()
        
        seed1 = registry.get_seed("plan_2024", "exec_001", "numpy")
        registry.clear_cache()
        
        # After clearing cache, should generate again (audit log grows)
        audit_count_before = len(registry.get_audit_log())
        seed2 = registry.get_seed("plan_2024", "exec_001", "numpy")
        audit_count_after = len(registry.get_audit_log())
        
        assert seed1 == seed2  # Same seed value
        assert audit_count_after > audit_count_before  # New audit entry
    
    def test_get_manifest_entry(self):
        """Test manifest entry generation."""
        registry = SeedRegistry()
        
        registry.get_seed("plan_2024", "exec_001", "numpy")
        registry.get_seed("plan_2024", "exec_001", "python")
        
        manifest = registry.get_manifest_entry("plan_2024", "exec_001")
        
        assert manifest["seed_version"] == SEED_VERSION
        assert manifest["seeds_generated"] == 2
        assert manifest["policy_unit_id"] == "plan_2024"
        assert manifest["correlation_id"] == "exec_001"
        assert "numpy" in manifest["seeds_by_component"]
        assert "python" in manifest["seeds_by_component"]


class TestGlobalSeedRegistry:
    """Test global seed registry singleton."""
    
    def test_get_global_registry(self):
        """Test getting global registry instance."""
        reset_global_seed_registry()
        
        registry1 = get_global_seed_registry()
        registry2 = get_global_seed_registry()
        
        assert registry1 is registry2  # Same instance
    
    def test_reset_global_registry(self):
        """Test resetting global registry."""
        reset_global_seed_registry()
        
        registry1 = get_global_seed_registry()
        registry1.get_seed("plan_2024", "exec_001", "numpy")
        
        reset_global_seed_registry()
        
        registry2 = get_global_seed_registry()
        assert registry2 is not registry1  # New instance
        assert len(registry2.get_audit_log()) == 0  # Empty audit log


class TestDeterminismAcrossRuns:
    """Test that same seeds produce identical results across runs."""
    
    def test_same_seed_different_registries(self):
        """Test that different registry instances produce same seeds."""
        registry1 = SeedRegistry()
        registry2 = SeedRegistry()
        
        seed1 = registry1.get_seed("plan_2024", "exec_001", "numpy")
        seed2 = registry2.get_seed("plan_2024", "exec_001", "numpy")
        
        assert seed1 == seed2
    
    def test_reproducible_numpy_random(self):
        """Test that NumPy RNG with same seed produces same output."""
        try:
            import numpy as np
        except ImportError:
            pytest.skip("NumPy not available")
        
        registry = SeedRegistry()
        seed = registry.get_seed("plan_2024", "exec_001", "numpy")
        
        # First run
        rng1 = np.random.default_rng(seed)
        values1 = rng1.random(10)
        
        # Second run with same seed
        rng2 = np.random.default_rng(seed)
        values2 = rng2.random(10)
        
        assert np.allclose(values1, values2)
    
    def test_reproducible_python_random(self):
        """Test that Python random with same seed produces same output."""
        import random
        
        registry = SeedRegistry()
        seed = registry.get_seed("plan_2024", "exec_001", "python")
        
        # First run
        random.seed(seed)
        values1 = [random.random() for _ in range(10)]
        
        # Second run with same seed
        random.seed(seed)
        values2 = [random.random() for _ in range(10)]
        
        assert values1 == values2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
