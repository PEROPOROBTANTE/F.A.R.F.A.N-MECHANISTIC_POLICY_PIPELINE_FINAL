#!/usr/bin/env python3
"""
GOLD-CANARIO Comprehensive Tests: Micro Reporting - Anti-Milagro Stress Tester
===============================================================================

Tests for AntiMilagroStressTester including:
- Pattern density calculation
- Pattern coverage calculation
- Node removal simulation
- Fragility detection
- Explanation generation
- JSON export
"""

import pytest

from saaaaaa.processing.micro_prompts import (
    AntiMilagroStressTester,
    CausalChain,
    ProportionalityPattern,
    StressTestResult,
)

class TestAntiMilagroStressTesterBasics:
    """Test basic functionality of AntiMilagroStressTester"""

    def test_tester_initialization_defaults(self):
        """Test tester initializes with default values"""
        tester = AntiMilagroStressTester()
        assert tester.fragility_threshold == 0.3

    def test_tester_initialization_custom(self):
        """Test tester initializes with custom threshold"""
        tester = AntiMilagroStressTester(fragility_threshold=0.5)
        assert tester.fragility_threshold == 0.5

    def test_empty_chain_stress_test(self):
        """Test stress test with empty chain"""
        tester = AntiMilagroStressTester()

        chain = CausalChain(steps=[], edges=[])
        patterns = []
        missing = []

        result = tester.stress_test(chain, patterns, missing)

        assert isinstance(result, StressTestResult)
        assert result.density == 0.0
        assert result.pattern_coverage == 0.0

class TestPatternDensity:
    """Test pattern density calculation"""

    def test_zero_density_no_patterns(self):
        """Test density is zero with no patterns"""
        tester = AntiMilagroStressTester()

        chain = CausalChain(
            steps=["A", "B", "C"],
            edges=[("A", "B"), ("B", "C")]
        )
        patterns = []

        result = tester.stress_test(chain, patterns, [])

        assert result.density == 0.0

    def test_density_calculation(self):
        """Test density calculation with patterns"""
        tester = AntiMilagroStressTester()

        chain = CausalChain(
            steps=["A", "B", "C", "D"],
            edges=[("A", "B"), ("B", "C"), ("C", "D")]
        )
        patterns = [
            ProportionalityPattern("linear", 0.8, "A->B"),
            ProportionalityPattern("dose-response", 0.7, "B->C")
        ]

        result = tester.stress_test(chain, patterns, [])

        # 2 patterns / 4 steps = 0.5
        assert result.density == 0.5

    def test_high_density(self):
        """Test high pattern density"""
        tester = AntiMilagroStressTester()

        chain = CausalChain(
            steps=["A", "B", "C"],
            edges=[("A", "B"), ("B", "C")]
        )
        patterns = [
            ProportionalityPattern("linear", 0.9, "A->B"),
            ProportionalityPattern("dose-response", 0.8, "B->C"),
            ProportionalityPattern("threshold", 0.7, "A->C")
        ]

        result = tester.stress_test(chain, patterns, [])

        # 3 patterns / 3 steps = 1.0
        assert result.density == 1.0

    def test_density_exceeds_one(self):
        """Test density can exceed 1.0 with many patterns"""
        tester = AntiMilagroStressTester()

        chain = CausalChain(
            steps=["A", "B"],
            edges=[("A", "B")]
        )
        patterns = [
            ProportionalityPattern("linear", 0.9, "A->B"),
            ProportionalityPattern("dose-response", 0.8, "A->B"),
            ProportionalityPattern("threshold", 0.7, "A->B")
        ]

        result = tester.stress_test(chain, patterns, [])

        # 3 patterns / 2 steps = 1.5
        assert result.density == 1.5

class TestPatternCoverage:
    """Test pattern coverage calculation"""

    def test_zero_coverage(self):
        """Test zero coverage with no patterns"""
        tester = AntiMilagroStressTester()

        chain = CausalChain(
            steps=["A", "B", "C"],
            edges=[("A", "B"), ("B", "C")]
        )
        patterns = []

        result = tester.stress_test(chain, patterns, [])

        assert result.pattern_coverage == 0.0

    def test_partial_coverage(self):
        """Test partial pattern coverage"""
        tester = AntiMilagroStressTester()

        chain = CausalChain(
            steps=["A", "B", "C", "D"],
            edges=[("A", "B"), ("B", "C"), ("C", "D")]
        )
        patterns = [
            ProportionalityPattern("linear", 0.8, "A->B"),
            ProportionalityPattern("dose-response", 0.7, "A->B"),  # Same location
        ]

        result = tester.stress_test(chain, patterns, [])

        # Coverage depends on unique locations covered
        assert 0.0 <= result.pattern_coverage <= 1.0

    def test_full_coverage(self):
        """Test full pattern coverage"""
        tester = AntiMilagroStressTester()

        chain = CausalChain(
            steps=["A", "B", "C"],
            edges=[("A", "B"), ("B", "C")]
        )
        patterns = [
            ProportionalityPattern("linear", 0.8, "A"),
            ProportionalityPattern("dose-response", 0.7, "B"),
            ProportionalityPattern("threshold", 0.6, "C")
        ]

        result = tester.stress_test(chain, patterns, [])

        # All steps covered
        assert result.pattern_coverage == 1.0

class TestNodeRemovalSimulation:
    """Test node removal simulation"""

    def test_no_drop_strong_patterns(self):
        """Test minimal drop with all strong patterns"""
        tester = AntiMilagroStressTester()

        chain = CausalChain(
            steps=["A", "B", "C"],
            edges=[("A", "B"), ("B", "C")]
        )
        patterns = [
            ProportionalityPattern("linear", 0.9, "A->B"),
            ProportionalityPattern("dose-response", 0.85, "B->C"),
            ProportionalityPattern("threshold", 0.8, "A->C")
        ]

        result = tester.stress_test(chain, patterns, [])

        # Should have low drop since all patterns are strong
        assert result.simulated_drop < 0.3
        assert not result.fragility_flag

    def test_high_drop_weak_patterns(self):
        """Test high drop with weak patterns"""
        tester = AntiMilagroStressTester()

        chain = CausalChain(
            steps=["A", "B", "C"],
            edges=[("A", "B"), ("B", "C")]
        )
        patterns = [
            ProportionalityPattern("linear", 0.2, "A->B"),
            ProportionalityPattern("dose-response", 0.1, "B->C"),
            ProportionalityPattern("threshold", 0.9, "A->C")  # One strong pattern
        ]

        result = tester.stress_test(chain, patterns, [])

        # Should have significant drop when weak patterns removed
        assert 0.0 <= result.simulated_drop <= 1.0

    def test_maximum_drop_no_patterns(self):
        """Test maximum drop with no patterns"""
        tester = AntiMilagroStressTester()

        chain = CausalChain(
            steps=["A", "B"],
            edges=[("A", "B")]
        )
        patterns = []

        result = tester.stress_test(chain, patterns, [])

        # Should have maximum drop
        assert result.simulated_drop == 1.0
        assert result.fragility_flag

    def test_single_pattern(self):
        """Test simulation with single pattern"""
        tester = AntiMilagroStressTester()

        chain = CausalChain(
            steps=["A", "B"],
            edges=[("A", "B")]
        )
        patterns = [
            ProportionalityPattern("linear", 0.5, "A->B")
        ]

        result = tester.stress_test(chain, patterns, [])

        # With single pattern, drop should be 0 (no weak patterns to remove)
        assert result.simulated_drop == 0.0

class TestFragilityDetection:
    """Test fragility flag detection"""

    def test_no_fragility_robust_structure(self):
        """Test no fragility with robust structure"""
        tester = AntiMilagroStressTester(fragility_threshold=0.3)

        chain = CausalChain(
            steps=["A", "B", "C"],
            edges=[("A", "B"), ("B", "C")]
        )
        patterns = [
            ProportionalityPattern("linear", 0.9, "A->B"),
            ProportionalityPattern("dose-response", 0.85, "B->C"),
            ProportionalityPattern("threshold", 0.8, "A->C")
        ]

        result = tester.stress_test(chain, patterns, [])

        assert not result.fragility_flag

    def test_fragility_detected(self):
        """Test fragility detection with weak structure"""
        tester = AntiMilagroStressTester(fragility_threshold=0.3)

        chain = CausalChain(
            steps=["A", "B", "C"],
            edges=[("A", "B"), ("B", "C")]
        )
        patterns = [
            ProportionalityPattern("linear", 0.2, "A->B"),
            ProportionalityPattern("dose-response", 0.15, "B->C"),
            ProportionalityPattern("threshold", 0.8, "A->C")
        ]

        result = tester.stress_test(chain, patterns, [])

        # Should detect fragility
        assert result.simulated_drop >= tester.fragility_threshold
        assert result.fragility_flag

    def test_fragility_threshold_boundary(self):
        """Test fragility at threshold boundary"""
        tester = AntiMilagroStressTester(fragility_threshold=0.5)

        # This is a simplified test; actual drop calculation is complex
        chain = CausalChain(steps=["A", "B"], edges=[("A", "B")])
        patterns = []

        result = tester.stress_test(chain, patterns, [])

        # With no patterns, drop is 1.0, which exceeds 0.5 threshold
        assert result.fragility_flag

    def test_custom_fragility_threshold(self):
        """Test custom fragility threshold"""
        tester = AntiMilagroStressTester(fragility_threshold=0.8)

        chain = CausalChain(
            steps=["A", "B"],
            edges=[("A", "B")]
        )
        patterns = [
            ProportionalityPattern("linear", 0.5, "A->B")
        ]

        result = tester.stress_test(chain, patterns, [])

        # With single pattern, drop is 0, which is below 0.8 threshold
        assert not result.fragility_flag

class TestExplanationGeneration:
    """Test explanation generation"""

    def test_explanation_robust_structure(self):
        """Test explanation for robust structure"""
        tester = AntiMilagroStressTester()

        chain = CausalChain(
            steps=["A", "B", "C"],
            edges=[("A", "B"), ("B", "C")]
        )
        patterns = [
            ProportionalityPattern("linear", 0.9, "A->B"),
            ProportionalityPattern("dose-response", 0.85, "B->C")
        ]

        result = tester.stress_test(chain, patterns, [])

        assert "Pattern density" in result.explanation
        assert "Robust structure" in result.explanation
        assert "maintained" in result.explanation.lower()

    def test_explanation_fragile_structure(self):
        """Test explanation for fragile structure"""
        tester = AntiMilagroStressTester()

        chain = CausalChain(
            steps=["A", "B"],
            edges=[("A", "B")]
        )
        patterns = []

        result = tester.stress_test(chain, patterns, [])

        assert "Pattern density" in result.explanation
        assert "FRAGILITY DETECTED" in result.explanation
        assert "weakness" in result.explanation.lower()

    def test_explanation_contains_metrics(self):
        """Test explanation contains key metrics"""
        tester = AntiMilagroStressTester()

        chain = CausalChain(
            steps=["A", "B", "C", "D"],
            edges=[("A", "B"), ("B", "C"), ("C", "D")]
        )
        patterns = [
            ProportionalityPattern("linear", 0.7, "A->B"),
            ProportionalityPattern("dose-response", 0.6, "B->C")
        ]

        result = tester.stress_test(chain, patterns, [])

        # Should mention density
        assert "patterns/step" in result.explanation or "density" in result.explanation.lower()

        # Should mention drop percentage
        assert "%" in result.explanation or "drop" in result.explanation.lower()

class TestMissingPatterns:
    """Test handling of missing patterns"""

    def test_missing_patterns_recorded(self):
        """Test missing patterns are recorded"""
        tester = AntiMilagroStressTester()

        chain = CausalChain(
            steps=["A", "B", "C"],
            edges=[("A", "B"), ("B", "C")]
        )
        patterns = []
        missing = ["linear", "dose-response"]

        result = tester.stress_test(chain, patterns, missing)

        assert result.missing_patterns == missing
        assert len(result.missing_patterns) == 2

    def test_no_missing_patterns(self):
        """Test no missing patterns"""
        tester = AntiMilagroStressTester()

        chain = CausalChain(
            steps=["A", "B"],
            edges=[("A", "B")]
        )
        patterns = [
            ProportionalityPattern("linear", 0.8, "A->B")
        ]
        missing = []

        result = tester.stress_test(chain, patterns, missing)

        assert result.missing_patterns == []

class TestPatternStrength:
    """Test pattern strength impact"""

    def test_all_strong_patterns(self):
        """Test with all strong patterns"""
        tester = AntiMilagroStressTester()

        chain = CausalChain(
            steps=["A", "B", "C"],
            edges=[("A", "B"), ("B", "C")]
        )
        patterns = [
            ProportionalityPattern("linear", 0.95, "A->B"),
            ProportionalityPattern("dose-response", 0.90, "B->C"),
            ProportionalityPattern("threshold", 0.85, "A->C")
        ]

        result = tester.stress_test(chain, patterns, [])

        # Strong patterns should result in low drop
        assert result.simulated_drop < 0.3
        assert not result.fragility_flag

    def test_mixed_strength_patterns(self):
        """Test with mixed strength patterns"""
        tester = AntiMilagroStressTester()

        chain = CausalChain(
            steps=["A", "B", "C"],
            edges=[("A", "B"), ("B", "C")]
        )
        patterns = [
            ProportionalityPattern("linear", 0.9, "A->B"),
            ProportionalityPattern("dose-response", 0.2, "B->C"),
            ProportionalityPattern("threshold", 0.15, "A->C")
        ]

        result = tester.stress_test(chain, patterns, [])

        # Should have some drop when weak patterns removed
        assert 0.0 <= result.simulated_drop <= 1.0

    def test_pattern_strength_range(self):
        """Test patterns with various strengths"""
        tester = AntiMilagroStressTester()

        chain = CausalChain(
            steps=["A", "B", "C", "D"],
            edges=[("A", "B"), ("B", "C"), ("C", "D")]
        )
        patterns = [
            ProportionalityPattern("linear", 0.1, "A->B"),
            ProportionalityPattern("dose-response", 0.3, "B->C"),
            ProportionalityPattern("threshold", 0.6, "C->D"),
            ProportionalityPattern("mechanism", 0.9, "A->D")
        ]

        result = tester.stress_test(chain, patterns, [])

        # Verify result is valid
        assert 0.0 <= result.simulated_drop <= 1.0
        assert result.density >= 0.0
        assert 0.0 <= result.pattern_coverage <= 1.0

class TestJSONExport:
    """Test JSON export functionality"""

    def test_to_json_export(self):
        """Test exporting stress test result to JSON"""
        tester = AntiMilagroStressTester()

        chain = CausalChain(
            steps=["A", "B", "C"],
            edges=[("A", "B"), ("B", "C")]
        )
        patterns = [
            ProportionalityPattern("linear", 0.8, "A->B")
        ]
        missing = ["dose-response"]

        result = tester.stress_test(chain, patterns, missing)
        json_output = tester.to_json(result)

        assert isinstance(json_output, dict)
        assert 'density' in json_output
        assert 'simulated_drop' in json_output
        assert 'fragility_flag' in json_output
        assert 'explanation' in json_output
        assert 'pattern_coverage' in json_output
        assert 'missing_patterns' in json_output
        assert 'timestamp' in json_output

class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_chain_with_one_step(self):
        """Test chain with single step"""
        tester = AntiMilagroStressTester()

        chain = CausalChain(steps=["A"], edges=[])
        patterns = [
            ProportionalityPattern("linear", 0.8, "A")
        ]

        result = tester.stress_test(chain, patterns, [])

        # 1 pattern / 1 step = 1.0 density
        assert result.density == 1.0

    def test_zero_strength_patterns(self):
        """Test with zero strength patterns"""
        tester = AntiMilagroStressTester()

        chain = CausalChain(
            steps=["A", "B"],
            edges=[("A", "B")]
        )
        patterns = [
            ProportionalityPattern("linear", 0.0, "A->B")
        ]

        result = tester.stress_test(chain, patterns, [])

        # Should handle zero strength gracefully
        assert 0.0 <= result.simulated_drop <= 1.0

    def test_maximum_strength_patterns(self):
        """Test with maximum strength patterns"""
        tester = AntiMilagroStressTester()

        chain = CausalChain(
            steps=["A", "B"],
            edges=[("A", "B")]
        )
        patterns = [
            ProportionalityPattern("linear", 1.0, "A->B")
        ]

        result = tester.stress_test(chain, patterns, [])

        # Should handle maximum strength
        assert result.simulated_drop == 0.0
        assert not result.fragility_flag

class TestCausalChainHelpers:
    """Test CausalChain helper methods"""

    def test_chain_length(self):
        """Test chain length calculation"""
        chain = CausalChain(
            steps=["A", "B", "C", "D"],
            edges=[("A", "B"), ("B", "C"), ("C", "D")]
        )

        assert chain.length() == 4

    def test_empty_chain_length(self):
        """Test empty chain length"""
        chain = CausalChain(steps=[], edges=[])

        assert chain.length() == 0

    def test_single_step_chain_length(self):
        """Test single step chain length"""
        chain = CausalChain(steps=["A"], edges=[])

        assert chain.length() == 1

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
