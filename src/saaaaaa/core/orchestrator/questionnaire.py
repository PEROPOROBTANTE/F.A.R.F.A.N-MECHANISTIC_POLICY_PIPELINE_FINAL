"""
Questionnaire Integrity Module - THE ONLY module that loads questionnaire_monolith.json.

This module enforces the Questionnaire Integrity Protocol:
1. ONE PATH: questionnaire_monolith.json is the single source of truth
2. ONE HASH: SHA-256 hash must match EXPECTED_HASH or load fails
3. ONE STRUCTURE: Exactly 305 questions (300 micro + 4 meso + 1 macro)
4. ONE LOADER: load_questionnaire() is the ONLY way to load the questionnaire
5. ONE TYPE: CanonicalQuestionnaire is the ONLY valid representation

All consumers MUST use this module. Direct file access is prohibited.

Architectural Rules:
- This is THE ONLY module that may read questionnaire_monolith.json
- All other modules MUST import from this module
- No other module may use json.load() on the questionnaire file
- The questionnaire file path is immutable (no parameters)
- The expected hash is immutable (must update here for legitimate changes)

Version: 2.0.0
Status: Production - Integrity enforcement active
"""

import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final

logger = logging.getLogger(__name__)

# ============================================================================
# INTEGRITY CONSTANTS - THE THREE RULES
# ============================================================================

# RULE 1: ONE PATH - The ONLY valid questionnaire location
_REPO_ROOT = Path(__file__).resolve().parents[4]
QUESTIONNAIRE_PATH: Final[Path] = _REPO_ROOT / "data" / "questionnaire_monolith.json"

# RULE 2: ONE HASH - Expected SHA-256 hash (MUST match or load fails)
# Computed using: json.dumps(data, sort_keys=True, ensure_ascii=True, separators=(',', ':'))
# Update this constant when the questionnaire is legitimately modified
EXPECTED_HASH: Final[str] = "27f7f784583d637158cb70ee236f1a98f77c1a08366612b5ae11f3be24062658"

# RULE 3: ONE STRUCTURE - Expected question counts
EXPECTED_MICRO_QUESTION_COUNT: Final[int] = 300
EXPECTED_MESO_QUESTION_COUNT: Final[int] = 4
EXPECTED_MACRO_QUESTION_COUNT: Final[int] = 1
EXPECTED_TOTAL_QUESTION_COUNT: Final[int] = 305  # 300 + 4 + 1


# ============================================================================
# CANONICAL QUESTIONNAIRE TYPE - THE ONLY VALID REPRESENTATION
# ============================================================================

@dataclass(frozen=True)
class CanonicalQuestionnaire:
    """Immutable, validated, hash-verified questionnaire.

    This is the ONLY valid representation of questionnaire data in the system.
    All questionnaire consumers MUST accept this type, not raw dicts.

    Attributes:
        data: Immutable view of questionnaire structure
        sha256: Computed SHA-256 hash (must match EXPECTED_HASH)
        micro_questions: Immutable tuple of micro questions
        meso_questions: Immutable tuple of meso questions
        macro_question: Immutable macro question or None
        micro_question_count: Number of micro questions (must be 300)
        total_question_count: Total questions including meso + macro (must be 305)
        version: Questionnaire version string
        schema_version: Schema version string

    Invariants enforced at construction:
        - sha256 == EXPECTED_HASH
        - micro_question_count == 300
        - total_question_count == 305
        - All data structures are immutable (MappingProxyType/tuple)
        - No None values in required fields
        - No duplicate question_id or question_global values
    """

    data: MappingProxyType[str, Any]
    sha256: str
    micro_questions: tuple[MappingProxyType, ...]
    meso_questions: tuple[MappingProxyType, ...]
    macro_question: MappingProxyType | None
    micro_question_count: int
    total_question_count: int
    version: str
    schema_version: str

    def __post_init__(self) -> None:
        """Validate all invariants on construction.

        Raises:
            ValueError: If any invariant is violated
        """
        # Hash verification (RULE 2)
        if self.sha256 != EXPECTED_HASH:
            raise ValueError(
                f"QUESTIONNAIRE INTEGRITY VIOLATION: Hash mismatch!\n"
                f"Expected: {EXPECTED_HASH}\n"
                f"Got:      {self.sha256}\n"
                f"The questionnaire file has been modified. If this was intentional, "
                f"update EXPECTED_HASH in questionnaire.py"
            )

        # Count verification (RULE 3)
        if self.micro_question_count != EXPECTED_MICRO_QUESTION_COUNT:
            raise ValueError(
                f"Expected {EXPECTED_MICRO_QUESTION_COUNT} micro questions, "
                f"got {self.micro_question_count}"
            )

        if self.total_question_count != EXPECTED_TOTAL_QUESTION_COUNT:
            raise ValueError(
                f"Expected {EXPECTED_TOTAL_QUESTION_COUNT} total questions, "
                f"got {self.total_question_count}"
            )

        # Immutability verification
        if not isinstance(self.data, MappingProxyType):
            raise TypeError(
                f"data must be MappingProxyType, got {type(self.data).__name__}"
            )

        if not isinstance(self.micro_questions, tuple):
            raise TypeError(
                f"micro_questions must be tuple, got {type(self.micro_questions).__name__}"
            )

        # Validate all micro questions are immutable
        for i, q in enumerate(self.micro_questions):
            if not isinstance(q, MappingProxyType):
                raise TypeError(
                    f"micro_questions[{i}] must be MappingProxyType, "
                    f"got {type(q).__name__}"
                )

        logger.info(
            "canonical_questionnaire_validated",
            sha256=self.sha256[:16] + "...",
            micro_count=self.micro_question_count,
            total_count=self.total_question_count,
            version=self.version,
        )


# ============================================================================
# VALIDATION FUNCTIONS (INTERNAL)
# ============================================================================

def _validate_questionnaire_structure(data: dict[str, Any]) -> None:
    """Validate questionnaire structure for required fields and types.

    Args:
        data: Questionnaire data to validate

    Raises:
        ValueError: If required fields are missing or invalid
        TypeError: If data is not a dictionary
    """
    if not isinstance(data, dict):
        raise ValueError("Questionnaire must be a dictionary")

    # Check top-level keys
    required_keys = ["version", "blocks", "schema_version"]
    missing = [k for k in required_keys if k not in data]
    if missing:
        raise ValueError(f"Questionnaire missing keys: {missing}")

    # Validate blocks structure
    blocks = data["blocks"]
    if not isinstance(blocks, dict):
        raise ValueError("blocks must be a dict")

    if "micro_questions" not in blocks:
        raise ValueError("blocks.micro_questions is required")

    micro_questions = blocks["micro_questions"]
    if not isinstance(micro_questions, list):
        raise ValueError("blocks.micro_questions must be a list")

    # Track for duplicate detection
    seen_question_ids = set()
    seen_question_globals = set()

    # Validate each question
    required_q_keys = ["question_id", "question_global", "base_slot"]

    for i, q in enumerate(micro_questions):
        if not isinstance(q, dict):
            raise ValueError(f"Question {i} must be a dict, got {type(q).__name__}")

        # Check required keys
        missing_q = [k for k in required_q_keys if k not in q]
        if missing_q:
            raise ValueError(f"Question {i} missing keys: {missing_q}")

        # Check for None values
        for key in required_q_keys:
            if q[key] is None:
                raise ValueError(f"Question {i}: {key} cannot be None")

        # Type validation
        question_id = q["question_id"]
        if not isinstance(question_id, str):
            raise ValueError(
                f"Question {i}: question_id must be string, got {type(question_id).__name__}"
            )

        question_global = q["question_global"]
        if not isinstance(question_global, int):
            raise ValueError(
                f"Question {i}: question_global must be an integer, got {type(question_global).__name__}"
            )

        base_slot = q["base_slot"]
        if not isinstance(base_slot, str):
            raise ValueError(
                f"Question {i}: base_slot must be string, got {type(base_slot).__name__}"
            )

        # Duplicate detection
        if question_id in seen_question_ids:
            raise ValueError(f"Duplicate question_id: {question_id} at index {i}")
        seen_question_ids.add(question_id)

        if question_global in seen_question_globals:
            raise ValueError(
                f"Duplicate question_global: {question_global} at index {i}"
            )
        seen_question_globals.add(question_global)

    logger.info(
        f"questionnaire_validation_passed: {len(micro_questions)} questions validated"
    )


def _compute_hash(data: dict[str, Any]) -> str:
    """Compute deterministic SHA-256 hash of questionnaire data.

    Args:
        data: Questionnaire data dictionary

    Returns:
        Hexadecimal SHA-256 hash string
    """
    canonical_json = json.dumps(
        data,
        sort_keys=True,
        ensure_ascii=True,
        separators=(',', ':'),
    )
    return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()


# ============================================================================
# THE SINGLE LOADER - RULE 4: ONE LOADER
# ============================================================================

def load_questionnaire() -> CanonicalQuestionnaire:
    """Load and validate questionnaire with full integrity checking.

    This is the ONLY function that loads questionnaire_monolith.json.
    It enforces all three rules:
    - ONE PATH: Always loads from QUESTIONNAIRE_PATH (no parameters)
    - ONE HASH: Verifies SHA-256 matches EXPECTED_HASH
    - ONE STRUCTURE: Validates 305 questions (300 micro + 4 meso + 1 macro)

    Returns:
        CanonicalQuestionnaire with validated, immutable data

    Raises:
        FileNotFoundError: If questionnaire file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
        ValueError: If structure/hash validation fails
        TypeError: If data types are incorrect

    Example:
        >>> questionnaire = load_questionnaire()
        >>> print(questionnaire.sha256[:16])
        27f7f784583d6371
        >>> print(questionnaire.micro_question_count)
        300
    """
    # RULE 1: ONE PATH - No parameter, always use QUESTIONNAIRE_PATH
    path = QUESTIONNAIRE_PATH

    if not path.exists():
        raise FileNotFoundError(
            f"Questionnaire file not found: {path}\n"
            f"Expected location: {QUESTIONNAIRE_PATH}"
        )

    logger.info(f"Loading questionnaire from {path}")

    # Read file content
    content = path.read_text(encoding='utf-8')

    # Parse JSON
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Invalid JSON in questionnaire file: {e.msg}",
            e.doc,
            e.pos
        ) from e

    if not isinstance(data, dict):
        raise TypeError(
            "questionnaire_monolith.json must contain a JSON object at the top level"
        )

    # RULE 3: Validate structure (raises on failure)
    _validate_questionnaire_structure(data)

    # RULE 2: Compute and verify hash
    sha256 = _compute_hash(data)

    # Extract blocks
    blocks = data['blocks']
    micro_questions = blocks['micro_questions']
    meso_questions = blocks.get('meso_questions', [])
    macro_question = blocks.get('macro_question')

    # Convert to immutable structures
    micro_immutable = tuple(MappingProxyType(q) for q in micro_questions)
    meso_immutable = tuple(MappingProxyType(q) for q in meso_questions)
    macro_immutable = MappingProxyType(macro_question) if macro_question else None

    # Count total questions
    total_count = len(micro_questions) + len(meso_questions)
    if macro_question:
        total_count += 1

    # Construct CanonicalQuestionnaire (validates invariants in __post_init__)
    return CanonicalQuestionnaire(
        data=MappingProxyType(data),
        sha256=sha256,
        micro_questions=micro_immutable,
        meso_questions=meso_immutable,
        macro_question=macro_immutable,
        micro_question_count=len(micro_questions),
        total_question_count=total_count,
        version=data.get('version', 'unknown'),
        schema_version=data.get('schema_version', 'unknown'),
    )


# ============================================================================
# PUBLIC API
# ============================================================================

__all__ = [
    # THE ONLY LOADER
    'load_questionnaire',
    # THE ONLY TYPE
    'CanonicalQuestionnaire',
    # INTEGRITY CONSTANTS
    'EXPECTED_HASH',
    'EXPECTED_MICRO_QUESTION_COUNT',
    'EXPECTED_MESO_QUESTION_COUNT',
    'EXPECTED_MACRO_QUESTION_COUNT',
    'EXPECTED_TOTAL_QUESTION_COUNT',
    'QUESTIONNAIRE_PATH',
    # INTERNAL (for backward compatibility only - prefer not to use directly)
    '_validate_questionnaire_structure',
    '_compute_hash',
]
