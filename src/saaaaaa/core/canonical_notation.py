"""
Canonical Notation System - Single Source of Truth

This module provides access to the canonical notation system defined in
questionnaire_monolith.json. All dimension and policy area references should
use this module instead of hardcoding values.

Architecture:
- Dimensions (D1-D6) with codes, names, and labels
- Policy Areas (PA01-PA10) with names and legacy IDs
- Lazy loading from questionnaire_monolith.json via factory
- Type-safe access with enums

Version: 1.0.0
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DimensionInfo:
    """Dimension metadata from canonical notation."""

    code: str  # e.g., "DIM01"
    name: str  # e.g., "INSUMOS"
    label: str  # e.g., "Diagnóstico y Recursos"


@dataclass(frozen=True)
class PolicyAreaInfo:
    """Policy area metadata from canonical notation."""

    code: str  # e.g., "PA01"
    name: str  # e.g., "Derechos de las mujeres e igualdad de género"
    legacy_id: str  # e.g., "P1"


@lru_cache(maxsize=1)
def _load_canonical_notation() -> dict[str, Any]:
    """
    Load canonical notation from questionnaire_monolith.json via factory.

    Cached to avoid repeated file I/O.

    Returns:
        Canonical notation dictionary

    Raises:
        ImportError: If orchestrator factory is not available
        KeyError: If canonical_notation section is missing
    """
    try:
        from saaaaaa.core.orchestrator.questionnaire import load_questionnaire
    except ImportError as e:
        raise ImportError(
            "Cannot import questionnaire module. "
            "Ensure saaaaaa.core.orchestrator is available."
        ) from e

    canonical = load_questionnaire()
    data = dict(canonical.data)

    if "canonical_notation" not in data:
        raise KeyError("canonical_notation section missing from questionnaire")

    return data["canonical_notation"]


def get_dimension_info(dimension_key: str) -> DimensionInfo:
    """
    Get dimension information from canonical notation.

    Args:
        dimension_key: Dimension key (e.g., "D1", "D2", etc.)

    Returns:
        DimensionInfo object with code, name, and label

    Raises:
        KeyError: If dimension not found
    """
    notation = _load_canonical_notation()

    if "dimensions" not in notation:
        raise KeyError("dimensions section missing from canonical_notation")

    dims = notation["dimensions"]
    if dimension_key not in dims:
        raise KeyError(f"Dimension {dimension_key} not found in canonical notation")

    dim = dims[dimension_key]
    return DimensionInfo(
        code=dim["code"],
        name=dim["name"],
        label=dim["label"]
    )


def get_policy_area_info(policy_area_key: str) -> PolicyAreaInfo:
    """
    Get policy area information from canonical notation.

    Args:
        policy_area_key: Policy area key (e.g., "PA01", "PA02", etc.)

    Returns:
        PolicyAreaInfo object with code, name, and legacy_id

    Raises:
        KeyError: If policy area not found
    """
    notation = _load_canonical_notation()

    if "policy_areas" not in notation:
        raise KeyError("policy_areas section missing from canonical_notation")

    areas = notation["policy_areas"]
    if policy_area_key not in areas:
        raise KeyError(f"Policy area {policy_area_key} not found in canonical notation")

    area = areas[policy_area_key]
    return PolicyAreaInfo(
        code=policy_area_key,
        name=area["name"],
        legacy_id=area["legacy_id"]
    )


def get_all_dimensions() -> dict[str, DimensionInfo]:
    """
    Get all dimensions from canonical notation.

    Returns:
        Dictionary mapping dimension keys to DimensionInfo objects
    """
    notation = _load_canonical_notation()

    if "dimensions" not in notation:
        raise KeyError("dimensions section missing from canonical_notation")

    dims = notation["dimensions"]
    return {
        key: DimensionInfo(
            code=info["code"],
            name=info["name"],
            label=info["label"]
        )
        for key, info in dims.items()
    }


def get_all_policy_areas() -> dict[str, PolicyAreaInfo]:
    """
    Get all policy areas from canonical notation.

    Returns:
        Dictionary mapping policy area codes to PolicyAreaInfo objects
    """
    notation = _load_canonical_notation()

    if "policy_areas" not in notation:
        raise KeyError("policy_areas section missing from canonical_notation")

    areas = notation["policy_areas"]
    return {
        code: PolicyAreaInfo(
            code=code,
            name=info["name"],
            legacy_id=info["legacy_id"]
        )
        for code, info in areas.items()
    }


# Convenience enums built from canonical notation
class CanonicalDimension(Enum):
    """Analytical dimensions from canonical notation (lazy-loaded)."""

    @classmethod
    def from_canonical(cls, key: str) -> str:
        """Get dimension label from canonical notation."""
        return get_dimension_info(key).label

    @property
    def code(self) -> str:
        """Get dimension code."""
        return get_dimension_info(self.name).code

    @property
    def label(self) -> str:
        """Get dimension label."""
        return get_dimension_info(self.name).label

    # Enum values (keys match questionnaire)
    D1 = "D1"
    D2 = "D2"
    D3 = "D3"
    D4 = "D4"
    D5 = "D5"
    D6 = "D6"


class CanonicalPolicyArea(Enum):
    """Policy areas from canonical notation (lazy-loaded)."""

    @classmethod
    def from_canonical(cls, code: str) -> str:
        """Get policy area name from canonical notation."""
        return get_policy_area_info(code).name

    @property
    def name_long(self) -> str:
        """Get full policy area name."""
        return get_policy_area_info(self.value).name

    @property
    def legacy_id(self) -> str:
        """Get legacy policy area ID (P1-P10)."""
        return get_policy_area_info(self.value).legacy_id

    # Enum values (codes from questionnaire)
    PA01 = "PA01"
    PA02 = "PA02"
    PA03 = "PA03"
    PA04 = "PA04"
    PA05 = "PA05"
    PA06 = "PA06"
    PA07 = "PA07"
    PA08 = "PA08"
    PA09 = "PA09"
    PA10 = "PA10"
