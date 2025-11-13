"""
Tests for synthetic traffic generation.

These tests validate that the synthetic traffic generator produces valid
requests that conform to the expected structure and constraints.
"""

import unittest
from pathlib import Path

# Add project root to path
from tools.testing.generate_synthetic_traffic import (
    MODALITY_TEMPLATES,
    generate_evidence,
    generate_request,
)

class TestSyntheticTraffic(unittest.TestCase):
    """Test synthetic traffic generation."""

    def test_generate_evidence_type_a(self):
        """Test TYPE_A evidence generation."""
        evidence = generate_evidence("TYPE_A")

        self.assertIn("elements", evidence)
        self.assertIn("confidence", evidence)
        self.assertIsInstance(evidence["elements"], list)
        self.assertIsInstance(evidence["confidence"], float)
        self.assertGreaterEqual(evidence["confidence"], 0.5)
        self.assertLessEqual(evidence["confidence"], 1.0)
        self.assertGreaterEqual(len(evidence["elements"]), 1)
        self.assertLessEqual(len(evidence["elements"]), 4)

    def test_generate_evidence_type_b(self):
        """Test TYPE_B evidence generation."""
        evidence = generate_evidence("TYPE_B")

        self.assertIn("elements", evidence)
        self.assertIn("completeness", evidence)
        self.assertIsInstance(evidence["completeness"], float)
        self.assertGreaterEqual(evidence["completeness"], 0.5)
        self.assertLessEqual(evidence["completeness"], 1.0)

    def test_generate_evidence_type_e(self):
        """Test TYPE_E evidence generation."""
        evidence = generate_evidence("TYPE_E")

        self.assertIn("elements", evidence)
        self.assertIn("traceability", evidence)
        self.assertIsInstance(evidence["traceability"], bool)

    def test_generate_request_structure(self):
        """Test that generated requests have correct structure."""
        modalities = ["TYPE_A", "TYPE_B"]
        policy_areas = ["PA01", "PA02"]

        request = generate_request(modalities, policy_areas, 1)

        # Check required fields
        self.assertIn("request_id", request)
        self.assertIn("question_global", request)
        self.assertIn("base_slot", request)
        self.assertIn("policy_area", request)
        self.assertIn("dimension", request)
        self.assertIn("modality", request)
        self.assertIn("evidence", request)
        self.assertIn("metadata", request)

        # Check field types
        self.assertIsInstance(request["question_global"], int)
        self.assertIsInstance(request["base_slot"], str)
        self.assertIsInstance(request["policy_area"], str)
        self.assertIsInstance(request["dimension"], str)
        self.assertIsInstance(request["modality"], str)
        self.assertIsInstance(request["evidence"], dict)

        # Check constraints
        self.assertIn(request["modality"], modalities)
        self.assertIn(request["policy_area"], policy_areas)
        self.assertGreaterEqual(request["question_global"], 1)
        self.assertLessEqual(request["question_global"], 300)

    def test_evidence_matches_modality(self):
        """Test that evidence structure matches modality requirements."""
        for modality in MODALITY_TEMPLATES:
            evidence = generate_evidence(modality)

            # All evidence must have elements
            self.assertIn("elements", evidence)
            self.assertIsInstance(evidence["elements"], list)
            self.assertGreater(len(evidence["elements"]), 0)

            # Check modality-specific fields
            if modality == "TYPE_A":
                self.assertIn("confidence", evidence)
            elif modality == "TYPE_B":
                self.assertIn("completeness", evidence)
            elif modality == "TYPE_C":
                self.assertIn("coherence_score", evidence)
            elif modality == "TYPE_D":
                self.assertIn("pattern_matches", evidence)
            elif modality == "TYPE_E":
                self.assertIn("traceability", evidence)
            elif modality == "TYPE_F":
                self.assertIn("plausibility", evidence)

    def test_request_id_format(self):
        """Test that request IDs are formatted correctly."""
        request = generate_request(["TYPE_A"], ["PA01"], 42)

        self.assertTrue(request["request_id"].startswith("synthetic-"))
        self.assertEqual(request["request_id"], "synthetic-000042")

    def test_base_slot_format(self):
        """Test that base slot IDs are formatted correctly."""
        request = generate_request(["TYPE_A"], ["PA01"], 1)

        # Should match pattern PA##-DIM##-Q###
        base_slot = request["base_slot"]
        parts = base_slot.split("-")

        self.assertEqual(len(parts), 3)
        self.assertTrue(parts[0].startswith("PA"))
        self.assertTrue(parts[1].startswith("DIM"))
        self.assertTrue(parts[2].startswith("Q"))

if __name__ == "__main__":
    unittest.main()
