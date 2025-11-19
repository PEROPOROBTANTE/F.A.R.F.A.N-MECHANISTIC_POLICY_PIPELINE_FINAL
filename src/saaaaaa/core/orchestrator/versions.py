"""
Version Tracking for Contract Enforcement

Centralized version management for all contract enforcement components.
Enables compatibility checking and rollback safety.
"""

# Pipeline version
PIPELINE_VERSION = "2.0.0"

# Calibration version (from calibration_registry.py)
CALIBRATION_VERSION = "2.0.0"  # Should match calibration_registry.CALIBRATION_VERSION

# Signal version
SIGNAL_VERSION = "1.0.0"

# Advanced module version
ADVANCED_MODULE_VERSION = "1.0.0"

# Seed registry version
SEED_VERSION = "sha256_v1"  # Should match seed_registry.SEED_VERSION

# Verification manifest version
MANIFEST_VERSION = "1.0.0"  # Should match verification_manifest.MANIFEST_VERSION

# Minimum supported versions for backward compatibility
MIN_CALIBRATION_VERSION = "2.0.0"
MIN_SIGNAL_VERSION = "1.0.0"
MIN_PIPELINE_VERSION = "2.0.0"


def check_version_compatibility(component: str, version: str, min_version: str) -> bool:
    """
    Check if a version meets minimum requirements.

    Args:
        component: Component name (for error messages)
        version: Current version string (e.g., "2.1.0")
        min_version: Minimum required version (e.g., "2.0.0")

    Returns:
        True if version >= min_version

    Raises:
        ValueError: If version is incompatible
    """
    try:
        v_parts = [int(x) for x in version.split(".")]
        min_parts = [int(x) for x in min_version.split(".")]

        # Pad to same length
        while len(v_parts) < len(min_parts):
            v_parts.append(0)
        while len(min_parts) < len(v_parts):
            min_parts.append(0)

        # Compare tuple
        if tuple(v_parts) < tuple(min_parts):
            raise ValueError(
                f"{component} version {version} is below minimum required {min_version}. "
                "Please upgrade or regenerate calibration data."
            )

        return True
    except (ValueError, AttributeError) as e:
        if "below minimum" in str(e):
            raise
        raise ValueError(
            f"Invalid version format for {component}: {version}. "
            "Expected semantic version like '1.0.0'"
        ) from e


def get_all_versions() -> dict[str, str]:
    """
    Get all component versions for manifest inclusion.

    Returns:
        Dictionary mapping component names to version strings
    """
    return {
        "pipeline": PIPELINE_VERSION,
        "calibration": CALIBRATION_VERSION,
        "signal": SIGNAL_VERSION,
        "advanced_module": ADVANCED_MODULE_VERSION,
        "seed": SEED_VERSION,
        "manifest": MANIFEST_VERSION,
    }
