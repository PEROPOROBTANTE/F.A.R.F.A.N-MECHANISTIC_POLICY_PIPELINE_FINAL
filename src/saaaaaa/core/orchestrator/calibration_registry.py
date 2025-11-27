"""Calibration Registry Module.

This module provides base calibration resolution for orchestrator methods.
It defines the MethodCalibration dataclass and functions to resolve calibration
parameters for methods, with optional context-aware adjustments.

Design Principles:
- Base calibration is context-independent
- Reads from config/intrinsic_calibration.json
- Provides fallback defaults for uncalibrated methods
- Supports context-aware resolution via calibration_context module
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..calibration.intrinsic_loader import IntrinsicScoreLoader

logger = logging.getLogger(__name__)

# Canonical repository root
# Path hierarchy: calibration_registry.py -> orchestrator -> core -> saaaaaa -> src -> REPO_ROOT
_REPO_ROOT = Path(__file__).resolve().parents[4]
_CALIBRATION_FILE = _REPO_ROOT / "config" / "intrinsic_calibration.json"


from .calibration_types import MethodCalibration


# Cache for loaded calibration data
_calibration_cache: dict[str, Any] | None = None


def _load_calibration_data() -> dict[str, Any]:
    """Load calibration data from config file.

    Returns:
        Dictionary containing calibration data
    """
    global _calibration_cache

    if _calibration_cache is not None:
        return _calibration_cache

    if not _CALIBRATION_FILE.exists():
        logger.warning(f"Calibration file not found: {_CALIBRATION_FILE}")
        _calibration_cache = {}
        return _calibration_cache

    try:
        with open(_CALIBRATION_FILE, encoding='utf-8') as f:
            data = json.load(f)
            _calibration_cache = data
            logger.info(f"Loaded calibration data from {_CALIBRATION_FILE}")
            return data
    except Exception as e:
        logger.error(f"Failed to load calibration data: {e}")
        _calibration_cache = {}
        return _calibration_cache


def _get_default_calibration() -> MethodCalibration:
    """Get default calibration for uncalibrated methods.

    Returns:
        Default MethodCalibration with conservative parameters
    """
    return MethodCalibration(
        score_min=0.0,
        score_max=1.0,
        min_evidence_snippets=3,
        max_evidence_snippets=15,
        contradiction_tolerance=0.1,
        uncertainty_penalty=0.3,
        aggregation_weight=1.0,
        sensitivity=0.75,
        requires_numeric_support=False,
        requires_temporal_support=False,
        requires_source_provenance=True,
    )


def resolve_calibration(class_name: str, method_name: str) -> MethodCalibration:
    """Resolve base calibration for a method.

    This function looks up calibration parameters from the intrinsic calibration
    file. If no calibration is found, it returns conservative defaults.

    Args:
        class_name: Name of the class (e.g., "SemanticAnalyzer")
        method_name: Name of the method (e.g., "extract_entities")

    Returns:
        MethodCalibration with parameters for this method
    """
    data = _load_calibration_data()

    # Try to find calibration for this specific method
    method_key = f"{class_name}.{method_name}"

    # Check if calibration exists for this method
    if method_key in data:
        method_data = data[method_key]
        try:
            return MethodCalibration(
                score_min=method_data.get("score_min", 0.0),
                score_max=method_data.get("score_max", 1.0),
                min_evidence_snippets=method_data.get("min_evidence_snippets", 3),
                max_evidence_snippets=method_data.get("max_evidence_snippets", 15),
                contradiction_tolerance=method_data.get("contradiction_tolerance", 0.1),
                uncertainty_penalty=method_data.get("uncertainty_penalty", 0.3),
                aggregation_weight=method_data.get("aggregation_weight", 1.0),
                sensitivity=method_data.get("sensitivity", 0.75),
                requires_numeric_support=method_data.get("requires_numeric_support", False),
                requires_temporal_support=method_data.get("requires_temporal_support", False),
                requires_source_provenance=method_data.get("requires_source_provenance", True),
            )
        except (KeyError, ValueError) as e:
            logger.warning(f"Invalid calibration for {method_key}: {e}. Using defaults.")
            return _get_default_calibration()

    # No specific calibration found, use defaults
    logger.debug(f"No calibration found for {method_key}, using defaults")
    return _get_default_calibration()


def resolve_calibration_with_context(
    class_name: str,
    method_name: str,
    question_id: str | None = None,
    **kwargs: Any
) -> MethodCalibration:
    """Resolve calibration with context-aware adjustments.

    This function first resolves base calibration, then applies context-specific
    modifiers based on the question ID and other context information.

    Args:
        class_name: Name of the class
        method_name: Name of the method
        question_id: Question ID for context inference (e.g., "D1Q1")
        **kwargs: Additional context parameters (policy_area, unit_of_analysis, etc.)

    Returns:
        MethodCalibration with context-aware adjustments applied
    """
    # Get base calibration
    base_calibration = resolve_calibration(class_name, method_name)

    # If no question_id provided, return base calibration
    if question_id is None:
        return base_calibration

    # Import context module to avoid circular dependency
    try:
        from .calibration_context import (
            CalibrationContext,
            resolve_contextual_calibration,
        )

        # Create context from question ID
        context = CalibrationContext.from_question_id(question_id)

        # Apply any additional context from kwargs
        if "policy_area" in kwargs:
            context = context.with_policy_area(kwargs["policy_area"])
        if "unit_of_analysis" in kwargs:
            context = context.with_unit_of_analysis(kwargs["unit_of_analysis"])
        if "method_position" in kwargs and "total_methods" in kwargs:
            context = context.with_method_position(
                kwargs["method_position"],
                kwargs["total_methods"]
            )

        # Apply contextual adjustments
        return resolve_contextual_calibration(base_calibration, context)

    except ImportError as e:
        logger.warning(f"Context module not available: {e}. Using base calibration.")
        return base_calibration


def get_calibration_manifest_data(
    calibration_path: str | Path = "config/intrinsic_calibration.json",
    method_ids: list[str] | None = None,
) -> dict[str, Any]:
    """
    Return canonical calibration manifest data for verification.

    Args:
        calibration_path: Path to intrinsic calibration JSON.
        method_ids: Optional method identifiers to include in detail.

    Returns:
        Dictionary with version, hash, statistics, and optional per-method data.
    """
    loader = IntrinsicScoreLoader(calibration_path)
    return loader.get_manifest_snapshot(method_ids)


__all__ = [
    "MethodCalibration",
    "resolve_calibration",
    "resolve_calibration_with_context",
    "get_calibration_manifest_data",
]
