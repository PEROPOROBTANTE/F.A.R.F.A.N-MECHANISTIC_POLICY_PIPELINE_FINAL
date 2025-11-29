"""
Structural normalization with policy-awareness.

Segments documents into policy-aware units.
"""

from typing import Any
from saaaaaa.core.calibration.decorators import calibrated_method


class StructuralNormalizer:
    """Policy-aware structural normalizer."""

    @calibrated_method("saaaaaa.processing.spc_ingestion.structural.StructuralNormalizer.normalize")
    def normalize(self, raw_objects: dict[str, Any]) -> dict[str, Any]:
        """
        Normalize document structure with policy awareness.

        Args:
            raw_objects: Raw parsed objects

        Returns:
            Policy graph with structured sections
        """
        policy_graph = {
            "sections": [],
            "policy_units": [],
            "axes": [],
            "programs": [],
            "projects": [],
            "years": [],
            "territories": [],
        }

        # Extract sections from pages
        for page in raw_objects.get("pages", []):
            text = page.get("text", "")

            # Detect policy units
            policy_units = self._detect_policy_units(text)
            policy_graph["policy_units"].extend(policy_units)

            # Create section
            section = {
                "text": text,
                "page": page.get("page_num"),
                "title": self._extract_title(text),
                "area": None,
                "eje": None,
            }
            policy_graph["sections"].append(section)

        # Extract axes, programs, projects
        for unit in policy_graph["policy_units"]:
            if unit["type"] == "eje":
                policy_graph["axes"].append(unit["name"])
            elif unit["type"] == "programa":
                policy_graph["programs"].append(unit["name"])
            elif unit["type"] == "proyecto":
                policy_graph["projects"].append(unit["name"])

        return policy_graph

    @calibrated_method("saaaaaa.processing.spc_ingestion.structural.StructuralNormalizer._detect_policy_units")
    def _detect_policy_units(self, text: str) -> list[dict[str, Any]]:
        """Detect policy units in text."""
        units = []

        # Simple keyword-based detection
        keywords = {
            "eje": ["eje", "pilar"],
            "programa": ["programa"],
            "proyecto": ["proyecto"],
            "meta": ["meta"],
            "indicador": ["indicador"],
        }

        for unit_type, keywords_list in keywords.items():
            for keyword in keywords_list:
                if keyword.lower() in text.lower():
                    units.append({
                        "type": unit_type,
                        "name": f"{keyword.capitalize()} detected",
                    })

        return units

    @calibrated_method("saaaaaa.processing.spc_ingestion.structural.StructuralNormalizer._extract_title")
    def _extract_title(self, text: str) -> str:
        """Extract title from text."""
        # Simple: first line or first N characters
        lines = text.split("\n")
        if lines:
            return lines[0][:100]
        return ""
