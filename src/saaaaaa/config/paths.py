"""
Centralized Path Configuration for F.A.R.F.A.N
==============================================

This module provides a single source of truth for all filesystem paths
used throughout the project. This ensures:

1. Portability: Works in development and production
2. Configurability: Paths can be overridden via environment variables
3. Consistency: All modules use the same path definitions
4. Testability: Paths can be mocked for testing

Author: Python Pipeline Expert
Date: 2025-11-15

Usage:
    from saaaaaa.config.paths import DATA_DIR, OUTPUT_DIR, CACHE_DIR

    questionnaire = DATA_DIR / 'questionnaire_monolith.json'
    report = OUTPUT_DIR / 'analysis_report.json'
"""

import os
import sys
from pathlib import Path
from typing import Final

# ============================================================================
# Project Root Detection
# ============================================================================

def _detect_project_root() -> Path:
    """
    Detect project root directory reliably in both dev and production.

    Strategy:
    1. If running from installed package: Use site-packages parent
    2. If running from source: Navigate from this file to project root
    3. Fallback: Use environment variable SAAAAAA_PROJECT_ROOT
    """
    # Check environment variable first (explicit override)
    if env_root := os.getenv('SAAAAAA_PROJECT_ROOT'):
        return Path(env_root).resolve()

    # Detect from this file's location
    # src/saaaaaa/config/paths.py → project_root
    this_file = Path(__file__).resolve()

    # Navigate up: paths.py -> config -> saaaaaa -> src -> project_root
    candidate = this_file.parents[3]

    # Verify this looks like our project (has setup.py or pyproject.toml)
    if (candidate / 'setup.py').exists() or (candidate / 'pyproject.toml').exists():
        return candidate

    # Fallback: current working directory
    return Path.cwd()


# Project root (base for all other paths)
PROJECT_ROOT: Final[Path] = _detect_project_root()

# ============================================================================
# Core Directories
# ============================================================================

# Source code directory
SRC_DIR: Final[Path] = PROJECT_ROOT / 'src' / 'saaaaaa'

# Package root (for importlib.resources)
PACKAGE_ROOT: Final[Path] = SRC_DIR

# ============================================================================
# Data Directories (Configurable)
# ============================================================================

# Input data directory
DATA_DIR: Final[Path] = Path(
    os.getenv('SAAAAAA_DATA_DIR', str(PROJECT_ROOT / 'data'))
).resolve()

# Output directory for generated reports
OUTPUT_DIR: Final[Path] = Path(
    os.getenv('SAAAAAA_OUTPUT_DIR', str(PROJECT_ROOT / 'output'))
).resolve()

# Cache directory for temporary artifacts
CACHE_DIR: Final[Path] = Path(
    os.getenv('SAAAAAA_CACHE_DIR', str(PROJECT_ROOT / '.cache'))
).resolve()

# Logs directory
LOGS_DIR: Final[Path] = Path(
    os.getenv('SAAAAAA_LOGS_DIR', str(PROJECT_ROOT / 'logs'))
).resolve()

# ============================================================================
# Configuration Directories
# ============================================================================

# Configuration files directory
CONFIG_DIR: Final[Path] = SRC_DIR / 'config'

# Rules and schemas directory
RULES_DIR: Final[Path] = PROJECT_ROOT / 'config' / 'rules'
SCHEMAS_DIR: Final[Path] = PROJECT_ROOT / 'config' / 'schemas'

# ============================================================================
# Common Data Files
# ============================================================================

# Questionnaire monolith (canonical)
QUESTIONNAIRE_FILE: Final[Path] = DATA_DIR / 'questionnaire_monolith.json'

# Method catalog
METHOD_CATALOG_FILE: Final[Path] = DATA_DIR / 'metodos' / 'catalogo_metodos.json'

# ============================================================================
# Test Directories
# ============================================================================

# Test data directory (fixtures, golden files, etc.)
TEST_DATA_DIR: Final[Path] = PROJECT_ROOT / 'tests' / 'data'

# Test output directory (temporary outputs from tests)
TEST_OUTPUT_DIR: Final[Path] = PROJECT_ROOT / 'tests' / 'output'

# ============================================================================
# Utilities
# ============================================================================

def ensure_directories_exist() -> None:
    """
    Create all required directories if they don't exist.

    This should be called at application startup to ensure the
    filesystem is properly initialized.
    """
    required_dirs = [
        DATA_DIR,
        OUTPUT_DIR,
        CACHE_DIR,
        LOGS_DIR,
        TEST_OUTPUT_DIR,
    ]

    for dir_path in required_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)


def get_output_path(plan_name: str, suffix: str = '') -> Path:
    """
    Get output path for a specific plan analysis.

    Args:
        plan_name: Name of the plan (e.g., "cpp_plan_1")
        suffix: Optional suffix for the output file

    Returns:
        Path to output file

    Example:
        >>> output_path = get_output_path("cpp_plan_1", "micro_analysis.json")
        >>> # Returns: output/cpp_plan_1/micro_analysis.json
    """
    plan_dir = OUTPUT_DIR / plan_name
    plan_dir.mkdir(parents=True, exist_ok=True)

    if suffix:
        return plan_dir / suffix
    return plan_dir


def get_cache_path(namespace: str, key: str) -> Path:
    """
    Get cache path for a specific namespace and key.

    Args:
        namespace: Cache namespace (e.g., "embeddings", "chunks")
        key: Cache key (will be sanitized)

    Returns:
        Path to cache file

    Example:
        >>> cache_path = get_cache_path("embeddings", "plan_123_chunk_5")
        >>> # Returns: .cache/embeddings/plan_123_chunk_5
    """
    namespace_dir = CACHE_DIR / namespace
    namespace_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize key (remove dangerous characters)
    safe_key = key.replace('/', '_').replace('\\', '_').replace('..', '_')

    return namespace_dir / safe_key


def validate_paths() -> bool:
    """
    Validate that all critical paths exist and are accessible.

    Returns:
        True if all paths are valid, False otherwise
    """
    issues = []

    # Check PROJECT_ROOT
    if not PROJECT_ROOT.exists():
        issues.append(f"PROJECT_ROOT does not exist: {PROJECT_ROOT}")

    # Check SRC_DIR
    if not SRC_DIR.exists():
        issues.append(f"SRC_DIR does not exist: {SRC_DIR}")

    # Check critical data files
    if not QUESTIONNAIRE_FILE.exists():
        issues.append(f"Questionnaire file not found: {QUESTIONNAIRE_FILE}")

    if issues:
        print("⚠️  Path validation issues:", file=sys.stderr)
        for issue in issues:
            print(f"   - {issue}", file=sys.stderr)
        return False

    return True


# ============================================================================
# Initialization
# ============================================================================

# Ensure directories exist on import (safe, idempotent)
ensure_directories_exist()

# ============================================================================
# Compatibility Shims (DEPRECATED - for migration period)
# ============================================================================

# These provide backward compatibility during migration
# TODO: Remove these after migration is complete

def proj_root() -> Path:
    """DEPRECATED: Use PROJECT_ROOT instead."""
    import warnings
    warnings.warn(
        "proj_root() is deprecated. Use PROJECT_ROOT constant instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return PROJECT_ROOT


def reports_dir() -> Path:
    """DEPRECATED: Use OUTPUT_DIR instead."""
    import warnings
    warnings.warn(
        "reports_dir() is deprecated. Use OUTPUT_DIR constant instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return OUTPUT_DIR


# ============================================================================
# Debug Information
# ============================================================================

if __name__ == "__main__":
    """Print path configuration for debugging."""
    print("=" * 80)
    print("F.A.R.F.A.N Path Configuration")
    print("=" * 80)
    print()
    print(f"PROJECT_ROOT:     {PROJECT_ROOT}")
    print(f"SRC_DIR:          {SRC_DIR}")
    print(f"DATA_DIR:         {DATA_DIR}")
    print(f"OUTPUT_DIR:       {OUTPUT_DIR}")
    print(f"CACHE_DIR:        {CACHE_DIR}")
    print(f"LOGS_DIR:         {LOGS_DIR}")
    print()
    print(f"QUESTIONNAIRE:    {QUESTIONNAIRE_FILE}")
    print(f"  Exists: {QUESTIONNAIRE_FILE.exists()}")
    print()
    print("Validation:", "✅ PASS" if validate_paths() else "❌ FAIL")
    print()
