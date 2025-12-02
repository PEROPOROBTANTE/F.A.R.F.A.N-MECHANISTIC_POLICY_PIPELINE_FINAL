"""Signal Loader Module - Extract patterns from questionnaire_monolith.json

This module implements Phase 1 of the Signal Integration Plan by extracting
REAL patterns from the questionnaire_monolith.json file and building SignalPack
objects for each of the 10 policy areas.

Key Features:
- Extracts ~2200 patterns from 300 micro_questions
- Groups patterns by policy_area_id (PA01-PA10)
- Categorizes patterns by type (TEMPORAL, INDICADOR, FUENTE_OFICIAL, etc.)
- Builds versioned SignalPack objects with fingerprints
- Computes source fingerprints using blake3/hashlib
"""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .questionnaire import CanonicalQuestionnaire

try:
    import blake3
    BLAKE3_AVAILABLE = True
except ImportError:
    BLAKE3_AVAILABLE = False

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from .signal_consumption import SignalManifest, generate_signal_manifests
from .signals import SignalPack


def compute_fingerprint(content: str | bytes) -> str:
    """
    Compute fingerprint of content using blake3 or sha256 fallback.

    Args:
        content: String or bytes to hash

    Returns:
        Hex string of hash
    """
    if isinstance(content, str):
        content = content.encode('utf-8')

    if BLAKE3_AVAILABLE:
        return blake3.blake3(content).hexdigest()
    else:
        return hashlib.sha256(content).hexdigest()


# DEPRECATED: Re-exported from factory.py for backward compatibility
# Do NOT create additional implementations - this is the single source


def extract_patterns_by_policy_area(
    monolith: dict[str, Any]
) -> dict[str, list[dict[str, Any]]]:
    """
    Extract patterns grouped by policy area.

    Args:
        monolith: Loaded questionnaire monolith data

    Returns:
        Dict mapping policy_area_id to list of patterns
    """
    questions = monolith.get('blocks', {}).get('micro_questions', [])

    patterns_by_pa = {}
    for question in questions:
        policy_area = question.get('policy_area_id', 'PA01')
        patterns = question.get('patterns', [])

        if policy_area not in patterns_by_pa:
            patterns_by_pa[policy_area] = []

        patterns_by_pa[policy_area].extend(patterns)

    logger.info(
        "patterns_extracted_by_policy_area",
        policy_areas=len(patterns_by_pa),
        total_patterns=sum(len(p) for p in patterns_by_pa.values()),
    )

    return patterns_by_pa


def categorize_patterns(
    patterns: list[dict[str, Any]]
) -> dict[str, list[str]]:
    """
    Categorize patterns by their category field.

    Args:
        patterns: List of pattern objects

    Returns:
        Dict with categorized pattern strings:
        - all_patterns: All non-TEMPORAL patterns
        - indicators: INDICADOR patterns
        - sources: FUENTE_OFICIAL patterns
        - temporal: TEMPORAL patterns
    """
    categorized = {
        'all_patterns': [],
        'indicators': [],
        'sources': [],
        'temporal': [],
        'entities': [],
    }

    for pattern_obj in patterns:
        pattern_str = pattern_obj.get('pattern', '')
        category = pattern_obj.get('category', '')

        if not pattern_str:
            continue

        # All non-temporal patterns
        if category != 'TEMPORAL':
            categorized['all_patterns'].append(pattern_str)

        # Category-specific
        if category == 'INDICADOR':
            categorized['indicators'].append(pattern_str)
        elif category == 'FUENTE_OFICIAL':
            categorized['sources'].append(pattern_str)
            # Sources are also entities
            # Extract entity names from pattern (simplified)
            parts = pattern_str.split('|')
            categorized['entities'].extend(p.strip() for p in parts if p.strip())
        elif category == 'TEMPORAL':
            categorized['temporal'].append(pattern_str)

    # Deduplicate
    for key in categorized:
        categorized[key] = list(set(categorized[key]))

    return categorized


def extract_thresholds(patterns: list[dict[str, Any]]) -> dict[str, float]:
    """
    Extract threshold values from pattern confidence_weight fields.

    Args:
        patterns: List of pattern objects

    Returns:
        Dict with threshold values
    """
    confidence_weights = [
        p.get('confidence_weight', 0.85)
        for p in patterns
        if 'confidence_weight' in p
    ]

    if confidence_weights:
        min_confidence = min(confidence_weights)
        max_confidence = max(confidence_weights)
        avg_confidence = sum(confidence_weights) / len(confidence_weights)
    else:
        min_confidence = 0.85
        max_confidence = 0.85
        avg_confidence = 0.85

    return {
        'min_confidence': round(min_confidence, 2),
        'max_confidence': round(max_confidence, 2),
        'avg_confidence': round(avg_confidence, 2),
        'min_evidence': 0.70,  # Derived from scoring requirements
    }


def get_git_sha() -> str:
    """
    Get current git commit SHA (short form).

    Returns:
        Short SHA or 'unknown' if not in git repo
    """
    try:
        import subprocess
        result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            check=False, capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass

    return 'unknown'


def build_signal_pack_from_monolith(
    policy_area: str,
    monolith: dict[str, Any] | None = None,
    *,
    questionnaire: CanonicalQuestionnaire | None = None,
) -> SignalPack:
    """
    Build SignalPack for a specific policy area from questionnaire monolith.

    This extracts REAL patterns from the questionnaire_monolith.json file and
    constructs a versioned SignalPack with proper categorization.

    Args:
        policy_area: Policy area code (PA01-PA10)
        monolith: DEPRECATED - Optional pre-loaded monolith data (use questionnaire parameter instead)
        questionnaire: Optional CanonicalQuestionnaire instance (recommended, loads from canonical if None)

    Returns:
        SignalPack object with extracted patterns

    Example:
        >>> from farfan_core.core.orchestrator.questionnaire import load_questionnaire
        >>> canonical = load_questionnaire()
        >>> pack = build_signal_pack_from_monolith("PA01", questionnaire=canonical)
        >>> print(f"Patterns: {len(pack.patterns)}")
        >>> print(f"Indicators: {len(pack.indicators)}")
    """
    # Import here to avoid circular dependency
    from .questionnaire import load_questionnaire

    # Handle legacy monolith parameter
    if monolith is not None:
        import warnings
        warnings.warn(
            "build_signal_pack_from_monolith: 'monolith' parameter is DEPRECATED. "
            "Use 'questionnaire' parameter with CanonicalQuestionnaire instead.",
            DeprecationWarning,
            stacklevel=2
        )
        # Use legacy monolith if provided
        monolith_data = monolith
    elif questionnaire is not None:
        # Use canonical questionnaire (preferred)
        monolith_data = dict(questionnaire.data)
    else:
        # Load from canonical loader
        canonical = load_questionnaire()
        monolith_data = dict(canonical.data)

    # Extract patterns by policy area
    patterns_by_pa = extract_patterns_by_policy_area(monolith_data)

    if policy_area not in patterns_by_pa:
        logger.warning(
            "policy_area_not_found",
            policy_area=policy_area,
            available=list(patterns_by_pa.keys()),
        )
        # Return empty signal pack
        return SignalPack(
            version="1.0.0",
            policy_area="fiscal",  # Default PolicyArea type
            patterns=[],
            indicators=[],
            regex=[],
            entities=[],
            thresholds={},
        )

    # Get patterns for this policy area
    raw_patterns = patterns_by_pa[policy_area]

    # Categorize patterns
    categorized = categorize_patterns(raw_patterns)

    # Extract thresholds
    thresholds = extract_thresholds(raw_patterns)

    # Compute source fingerprint
    monolith_str = json.dumps(monolith_data, sort_keys=True)
    source_fingerprint = compute_fingerprint(monolith_str)

    # Build version string (must be semantic X.Y.Z format)
    git_sha = get_git_sha()
    # Use 1.0.0 as base version (git sha stored in metadata)
    version = "1.0.0"

    # Regex patterns are all patterns (for now)
    regex_patterns = categorized['all_patterns'][:100]  # Limit for performance

    # Map policy area to PolicyArea type (using fiscal as default)
    # The SignalPack PolicyArea type is limited, so we use fiscal as a placeholder
    policy_area_type = "fiscal"

    # Build SignalPack
    signal_pack = SignalPack(
        version=version,
        policy_area=policy_area_type,
        patterns=categorized['all_patterns'][:200],  # Limit for performance
        indicators=categorized['indicators'][:50],
        regex=regex_patterns,
        entities=categorized['entities'][:100],
        thresholds=thresholds,
        ttl_s=86400,  # 24 hours
        source_fingerprint=source_fingerprint[:32],  # Truncate for readability
        metadata={
            'original_policy_area': policy_area,
            'total_raw_patterns': len(raw_patterns),
            'categorized_counts': {
                key: len(val) for key, val in categorized.items()
            },
            'git_sha': git_sha,
        }
    )

    logger.info(
        "signal_pack_built",
        policy_area=policy_area,
        version=version,
        patterns=len(signal_pack.patterns),
        indicators=len(signal_pack.indicators),
        entities=len(signal_pack.entities),
    )

    return signal_pack


def build_all_signal_packs(
    monolith: dict[str, Any] | None = None,
    *,
    questionnaire: CanonicalQuestionnaire | None = None,
) -> dict[str, SignalPack]:
    """
    Build SignalPacks for all policy areas.

    Args:
        monolith: DEPRECATED - Optional pre-loaded monolith data (use questionnaire parameter instead)
        questionnaire: Optional CanonicalQuestionnaire instance (recommended, loads from canonical if None)

    Returns:
        Dict mapping policy_area_id to SignalPack

    Example:
        >>> from farfan_core.core.orchestrator.questionnaire import load_questionnaire
        >>> canonical = load_questionnaire()
        >>> packs = build_all_signal_packs(questionnaire=canonical)
        >>> print(f"Built {len(packs)} signal packs")
    """
    # Import here to avoid circular dependency
    from .questionnaire import load_questionnaire

    # Handle legacy monolith parameter and ensure questionnaire is loaded only once
    if monolith is not None:
        import warnings
        warnings.warn(
            "build_all_signal_packs: 'monolith' parameter is DEPRECATED. "
            "Use 'questionnaire' parameter with CanonicalQuestionnaire instead.",
            DeprecationWarning,
            stacklevel=2
        )
    elif questionnaire is None:
        # Load questionnaire once to avoid redundant I/O in loop
        questionnaire = load_questionnaire()

    policy_areas = [f"PA{i:02d}" for i in range(1, 11)]

    signal_packs = {}
    for pa in policy_areas:
        signal_packs[pa] = build_signal_pack_from_monolith(
            pa, monolith=monolith, questionnaire=questionnaire
        )

    logger.info(
        "all_signal_packs_built",
        count=len(signal_packs),
        policy_areas=list(signal_packs.keys()),
    )

    return signal_packs


def build_signal_manifests(
    monolith: dict[str, Any] | None = None,
    *,
    questionnaire: CanonicalQuestionnaire | None = None,
) -> dict[str, SignalManifest]:
    """
    Build signal manifests with Merkle roots for verification.

    Args:
        monolith: DEPRECATED - Optional pre-loaded monolith data (use questionnaire parameter instead)
        questionnaire: Optional CanonicalQuestionnaire instance (recommended, loads from canonical if None)

    Returns:
        Dict mapping policy_area_id to SignalManifest

    Example:
        >>> from farfan_core.core.orchestrator.questionnaire import load_questionnaire
        >>> canonical = load_questionnaire()
        >>> manifests = build_signal_manifests(questionnaire=canonical)
        >>> print(f"Built {len(manifests)} manifests")
    """
    # Import here to avoid circular dependency
    from .questionnaire import QUESTIONNAIRE_PATH, load_questionnaire

    # Handle legacy monolith parameter
    if monolith is not None:
        import warnings
        warnings.warn(
            "build_signal_manifests: 'monolith' parameter is DEPRECATED. "
            "Use 'questionnaire' parameter with CanonicalQuestionnaire instead.",
            DeprecationWarning,
            stacklevel=2
        )
        monolith_data = monolith
    elif questionnaire is not None:
        # Use canonical questionnaire (preferred)
        monolith_data = dict(questionnaire.data)
    else:
        # Load from canonical loader
        canonical = load_questionnaire()
        monolith_data = dict(canonical.data)

    # Always use canonical path
    monolith_path = QUESTIONNAIRE_PATH
    manifests = generate_signal_manifests(monolith_data, monolith_path)

    logger.info(
        "signal_manifests_built",
        count=len(manifests),
        policy_areas=list(manifests.keys()),
    )

    return manifests
