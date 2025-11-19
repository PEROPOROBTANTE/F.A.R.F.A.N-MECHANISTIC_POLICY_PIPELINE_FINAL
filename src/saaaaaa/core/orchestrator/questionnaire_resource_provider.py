"""Questionnaire Resource Provider - Single Source of Truth for Patterns.

This module extracts and provides all patterns, validations, and resources from
the questionnaire monolith. It serves as the UNIQUE SOURCE for pattern data,
eliminating duplication across module classes.

Target Metrics:
- 2,207+ total patterns extracted
- 34 temporal patterns
- 157 indicator patterns
- 19 source patterns
- 6+ validation types

Design Principles:
- Single source of truth for all patterns
- No pattern duplication in individual classes
- Lazy extraction with caching
- Category-based pattern retrieval
- Full traceability and observability

QUESTIONNAIRE INTEGRITY:
- Accepts CanonicalQuestionnaire for type safety
- Falls back to dict for backward compatibility (with warning)
- All data access assumes immutable structures
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

import structlog

if TYPE_CHECKING:
    from pathlib import Path

    from .questionnaire import CanonicalQuestionnaire

logger = structlog.get_logger(__name__)


PatternCategory = Literal[
    "TEMPORAL",
    "INDICADOR",
    "FUENTE",
    "FUENTE_OFICIAL",
    "GENERAL",
    "TERRITORIAL",
    "UNIDAD_MEDIDA",
    "coherence",
    "cross_reference",
    "cross_cluster_integration",
    "narrative_coherence",
    "long_term_vision",
]


@dataclass(frozen=True)
class Pattern:
    """
    Immutable pattern extracted from questionnaire.

    Attributes:
        id: Unique pattern identifier
        category: Pattern category/type
        pattern: Regex pattern or description
        confidence_weight: Weight for scoring (0.0-1.0)
        match_type: Type of matching (REGEX, TEXT, etc.)
        flags: Regex flags (i, m, s, etc.)
        question_id: Source question ID
        metadata: Additional metadata
    """

    id: str
    category: str
    pattern: str
    confidence_weight: float = 1.0
    match_type: str = "REGEX"
    flags: str = "i"
    question_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def compile_regex(self) -> re.Pattern[str] | None:
        """
        Compile pattern as regex if match_type is REGEX.

        Returns:
            Compiled regex pattern or None if not regex type
        """
        if self.match_type != "REGEX":
            return None

        # Convert flags string to re flags
        flags_int = 0
        if "i" in self.flags.lower():
            flags_int |= re.IGNORECASE
        if "m" in self.flags.lower():
            flags_int |= re.MULTILINE
        if "s" in self.flags.lower():
            flags_int |= re.DOTALL

        try:
            return re.compile(self.pattern, flags_int)
        except re.error as e:
            logger.warning(
                "pattern_compile_error",
                pattern_id=self.id,
                error=str(e),
            )
            return None


@dataclass(frozen=True)
class ValidationSpec:
    """
    Validation specification from questionnaire.

    Attributes:
        type: Validation type name
        required: Whether validation is required
        minimum: Minimum count/value if applicable
        question_id: Source question ID
    """

    type: str
    required: bool = False
    minimum: int = 0
    question_id: str = ""


class QuestionnaireResourceProvider:
    """
    Provider for questionnaire-derived patterns and validations.

    This is the SINGLE SOURCE OF TRUTH for all patterns extracted from
    the questionnaire monolith. All module classes MUST use this provider
    instead of duplicating patterns.

    Usage (preferred):
        from saaaaaa.core.orchestrator.questionnaire import load_questionnaire
        questionnaire = load_questionnaire()
        provider = QuestionnaireResourceProvider(questionnaire)
        temporal_patterns = provider.get_temporal_patterns()

    Usage (legacy):
        provider = QuestionnaireResourceProvider.from_file("data/questionnaire_monolith.json")
    """

    def __init__(self, questionnaire_data: CanonicalQuestionnaire | dict[str, Any]) -> None:
        """
        Initialize provider with questionnaire data.

        Args:
            questionnaire_data: CanonicalQuestionnaire (preferred) or dict (legacy)
        """
        # Import here to avoid circular dependency
        from .questionnaire import CanonicalQuestionnaire

        if isinstance(questionnaire_data, CanonicalQuestionnaire):
            # Type-safe path: extract immutable data
            self._data = dict(questionnaire_data.data)  # Convert to mutable for internal use
            self._canonical = questionnaire_data
            logger.info(
                "questionnaire_resource_provider_initialized",
                source="canonical",
                sha256=questionnaire_data.sha256[:16] + "...",
                version=questionnaire_data.version,
                schema_version=questionnaire_data.schema_version,
            )
        elif isinstance(questionnaire_data, dict):
            # Legacy path: accept dict but warn
            import warnings
            warnings.warn(
                "QuestionnaireResourceProvider should receive CanonicalQuestionnaire, "
                "not dict. Use load_questionnaire() from factory module.",
                DeprecationWarning,
                stacklevel=2
            )
            self._data = questionnaire_data
            self._canonical = None
            logger.warning(
                "questionnaire_resource_provider_initialized",
                source="dict_legacy",
                version=questionnaire_data.get("version", "unknown"),
                schema_version=questionnaire_data.get("schema_version", "unknown"),
            )
        else:
            raise TypeError(
                f"questionnaire_data must be CanonicalQuestionnaire or dict, "
                f"got {type(questionnaire_data).__name__}"
            )

        self._patterns_cache: dict[str, list[Pattern]] | None = None
        self._all_patterns_cache: list[Pattern] | None = None
        self._question_area_cache: dict[str, str] | None = None
        self._validations_cache: list[ValidationSpec] | None = None

    @classmethod
    def from_file(cls, path: str | Path) -> QuestionnaireResourceProvider:
        """
        Load provider from questionnaire monolith file.

        This method now uses the canonical loader for integrity checking.

        Args:
            path: Path to questionnaire_monolith.json

        Returns:
            QuestionnaireResourceProvider instance
        """
        from .questionnaire import load_questionnaire

        logger.warning(
            "from_file: path parameter is ignored by canonical loader. "
            "Questionnaire always loads from canonical path.",
            provided_path=str(path)
        )

        logger.info("loading_questionnaire_via_canonical_loader")

        # Use canonical loader for integrity checking (no path parameter)
        canonical = load_questionnaire()

        return cls(canonical)

    def extract_all_patterns(self) -> list[Pattern]:
        """
        Extract all patterns from questionnaire.

        This method extracts patterns from:
        - Micro questions (300 questions × ~7 patterns = ~2100)
        - Meso questions (cluster-level patterns)
        - Macro question (holistic patterns)

        Returns:
            List of all patterns (target: 2,207+)
        """
        if self._all_patterns_cache is not None:
            return list(self._all_patterns_cache)

        all_patterns: list[Pattern] = []
        blocks = self._data.get("blocks", {})

        # Extract from micro questions
        micro_questions = blocks.get("micro_questions", [])
        for question in micro_questions:
            q_id = question.get("question_id", "UNKNOWN")
            patterns = question.get("patterns", [])

            for p in patterns:
                pattern = Pattern(
                    id=p.get("id", f"{q_id}-{len(all_patterns)}"),
                    category=p.get("category", "GENERAL"),
                    pattern=p.get("pattern", ""),
                    confidence_weight=p.get("confidence_weight", 1.0),
                    match_type=p.get("match_type", "REGEX"),
                    flags=p.get("flags", "i"),
                    question_id=q_id,
                )
                all_patterns.append(pattern)

        # Extract from meso questions
        meso_questions = blocks.get("meso_questions", [])
        for question in meso_questions:
            cluster_id = question.get("cluster_id", "UNKNOWN")
            patterns = question.get("patterns", [])

            for p in patterns:
                pattern = Pattern(
                    id=f"MESO-{cluster_id}-{len(all_patterns)}",
                    category=p.get("type", "GENERAL"),
                    pattern=p.get("description", ""),
                    confidence_weight=1.0,
                    match_type="TEXT",
                    question_id=cluster_id,
                    metadata={"source": "meso"},
                )
                all_patterns.append(pattern)

        # Extract from macro question
        macro_question = blocks.get("macro_question", {})
        patterns = macro_question.get("patterns", [])
        for p in patterns:
            pattern = Pattern(
                id=f"MACRO-{len(all_patterns)}",
                category=p.get("type", "GENERAL"),
                pattern=p.get("description", ""),
                confidence_weight=1.0,
                match_type="TEXT",
                question_id="MACRO_1",
                metadata={"source": "macro", "priority": p.get("priority", 999)},
            )
            all_patterns.append(pattern)

        logger.info(
            "patterns_extracted",
            total_count=len(all_patterns),
            micro_count=len([p for p in all_patterns if not p.metadata.get("source")]),
            meso_count=len([p for p in all_patterns if p.metadata.get("source") == "meso"]),
            macro_count=len([p for p in all_patterns if p.metadata.get("source") == "macro"]),
        )

        # Cache by category for fast lookup
        self._patterns_cache = defaultdict(list)
        for p in all_patterns:
            self._patterns_cache[p.category].append(p)

        self._all_patterns_cache = all_patterns

        return list(self._all_patterns_cache)

    def get_temporal_patterns(self) -> list[Pattern]:
        """
        Get all temporal patterns (target: 34).

        Temporal patterns match time references, baselines, years, etc.

        Returns:
            List of TEMPORAL category patterns
        """
        if self._patterns_cache is None:
            self.extract_all_patterns()

        patterns = self._patterns_cache.get("TEMPORAL", [])

        logger.debug("temporal_patterns_retrieved", count=len(patterns))
        return patterns

    def get_indicator_patterns(self) -> list[Pattern]:
        """
        Get all indicator patterns (target: 157).

        Indicator patterns match KPIs, metrics, measurements, etc.

        Returns:
            List of INDICADOR category patterns
        """
        if self._patterns_cache is None:
            self.extract_all_patterns()

        patterns = self._patterns_cache.get("INDICADOR", [])

        logger.debug("indicator_patterns_retrieved", count=len(patterns))
        return patterns

    def get_source_patterns(self) -> list[Pattern]:
        """
        Get all source/citation patterns (target: 19).

        Source patterns match references to official sources, citations, etc.

        Returns:
            List of FUENTE_OFICIAL category patterns
        """
        if self._patterns_cache is None:
            self.extract_all_patterns()

        # FUENTE_OFICIAL is the actual category in the data
        patterns = self._patterns_cache.get("FUENTE_OFICIAL", [])

        logger.debug("source_patterns_retrieved", count=len(patterns))
        return patterns

    def get_territorial_patterns(self) -> list[Pattern]:
        """
        Get all territorial patterns (71).

        Returns:
            List of TERRITORIAL category patterns
        """
        if self._patterns_cache is None:
            self.extract_all_patterns()

        patterns = self._patterns_cache.get("TERRITORIAL", [])

        logger.debug("territorial_patterns_retrieved", count=len(patterns))
        return patterns

    def compile_patterns_for_category(self, category: PatternCategory) -> list[re.Pattern[str]]:
        """
        Compile all patterns for a category into regex objects.

        Args:
            category: Pattern category to compile

        Returns:
            List of compiled regex patterns
        """
        if self._patterns_cache is None:
            self.extract_all_patterns()

        patterns = self._patterns_cache.get(category, [])
        compiled = []

        for p in patterns:
            regex = p.compile_regex()
            if regex is not None:
                compiled.append(regex)

        logger.debug(
            "patterns_compiled",
            category=category,
            total=len(patterns),
            compiled=len(compiled),
        )

        return compiled

    def extract_all_validations(self) -> list[ValidationSpec]:
        """
        Extract all validation specifications from questionnaire.

        Validations come from:
        - validations: list of validation names
        - expected_elements: structured requirements

        Returns:
            List of validation specifications (target: 6+ types)
        """
        if self._validations_cache is not None:
            return self._validations_cache

        validations: list[ValidationSpec] = []
        validation_types = set()
        blocks = self._data.get("blocks", {})

        micro_questions = blocks.get("micro_questions", [])
        for question in micro_questions:
            q_id = question.get("question_id", "UNKNOWN")

            # Extract from validations list
            val_list = question.get("validations", [])
            for val in val_list:
                if isinstance(val, str):
                    validations.append(
                        ValidationSpec(type=val, required=True, question_id=q_id)
                    )
                    validation_types.add(val)

            # Extract from expected_elements
            expected = question.get("expected_elements", [])
            for elem in expected:
                if isinstance(elem, dict):
                    elem_type = elem.get("type", "UNKNOWN")
                    validations.append(
                        ValidationSpec(
                            type=elem_type,
                            required=elem.get("required", False),
                            minimum=elem.get("minimum", 0),
                            question_id=q_id,
                        )
                    )
                    validation_types.add(elem_type)

        self._validations_cache = validations

        logger.info(
            "validations_extracted",
            total_count=len(validations),
            unique_types=len(validation_types),
            types=sorted(validation_types)[:10],  # Log first 10
        )

        return validations

    def get_patterns_by_question(self, question_id: str) -> list[Pattern]:
        """
        Get all patterns associated with a specific question.

        Args:
            question_id: Question identifier (e.g., "Q001")

        Returns:
            List of patterns for that question
        """
        if self._patterns_cache is None:
            self.extract_all_patterns()

        all_patterns = self.extract_all_patterns()
        return [p for p in all_patterns if p.question_id == question_id]

    def get_policy_area_for_question(self, question_id: str) -> str:
        """
        Get the policy area for a given question ID.

        This method uses the provider's already-loaded data, avoiding file I/O.

        Args:
            question_id: Question identifier (e.g., "Q001")

        Returns:
            Policy area code (e.g., "PA01") or "PA01" as default
        """
        blocks = self._data.get("blocks", {})
        micro_questions = blocks.get("micro_questions", [])

        for question in micro_questions:
            if question.get("question_id") == question_id:
                return question.get("policy_area_id", "PA01")

        # Default fallback
        logger.warning(
            "question_not_found_in_provider",
            question_id=question_id,
            fallback="PA01"
        )
        return "PA01"

    def _ensure_question_area_cache(self) -> None:
        """Build cache mapping question IDs to policy areas."""
        if self._question_area_cache is not None:
            return

        cache: dict[str, str] = {}
        blocks = self._data.get("blocks", {})
        micro_questions = blocks.get("micro_questions", [])

        for question in micro_questions:
            q_id = question.get("question_id")
            if not q_id:
                continue
            cache[q_id] = question.get("policy_area_id", "PA01")

        self._question_area_cache = cache

    def get_patterns_for_area(
        self,
        policy_area_id: str,
        limit: int | None = None,
    ) -> list[str]:
        """
        Get pattern strings associated with a policy area.

        Args:
            policy_area_id: Canonical policy area ID (PA01-PA10)
            limit: Optional max number of patterns to return

        Returns:
            List of pattern strings (may be empty if area not found)
        """
        all_patterns = self.extract_all_patterns()
        self._ensure_question_area_cache()

        if not self._question_area_cache:
            return []

        matches: list[str] = []
        remaining = limit if limit is not None else None

        for pattern in all_patterns:
            question_id = pattern.question_id or ""
            area_id = self._question_area_cache.get(question_id)
            if area_id != policy_area_id:
                continue

            matches.append(pattern.pattern)
            if remaining is not None:
                remaining -= 1
                if remaining <= 0:
                    break

        logger.debug(
            "patterns_for_area_retrieved",
            policy_area_id=policy_area_id,
            count=len(matches),
            limit=limit,
        )
        return matches

    def get_pattern_statistics(self) -> dict[str, Any]:
        """
        Get statistics about extracted patterns.

        Returns:
            Dict with pattern counts by category and totals
        """
        if self._patterns_cache is None:
            self.extract_all_patterns()

        stats = {
            "total_patterns": sum(len(patterns) for patterns in self._patterns_cache.values()),
            "categories": {
                category: len(patterns)
                for category, patterns in self._patterns_cache.items()
            },
            "temporal_count": len(self._patterns_cache.get("TEMPORAL", [])),
            "indicator_count": len(self._patterns_cache.get("INDICADOR", [])),
            "source_count": len(self._patterns_cache.get("FUENTE_OFICIAL", [])),
            "validation_count": len(self._validations_cache) if self._validations_cache else 0,
        }

        return stats

    def verify_target_counts(self) -> dict[str, bool]:
        """
        Verify that pattern extraction meets target counts.

        Returns:
            Dict with boolean flags for each target
        """
        stats = self.get_pattern_statistics()

        return {
            "total_patterns_ok": stats["total_patterns"] >= 2200,  # Target: 2207
            "temporal_patterns_ok": stats["temporal_count"] == 34,
            "indicator_patterns_ok": stats["indicator_count"] == 157,
            "source_patterns_ok": stats["source_count"] >= 19,
            "validation_types_ok": stats["validation_count"] >= 6,
        }
