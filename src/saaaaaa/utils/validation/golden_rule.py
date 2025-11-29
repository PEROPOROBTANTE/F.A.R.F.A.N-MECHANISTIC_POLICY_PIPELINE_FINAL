"""Golden Rule enforcement utilities."""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING
from saaaaaa.core.calibration.decorators import calibrated_method

if TYPE_CHECKING:
    from collections.abc import Iterable

class GoldenRuleViolation(Exception):
    """Raised when a Golden Rule assertion is violated."""

class GoldenRuleValidator:
    """Enforces the Golden Rules across orchestrated execution phases."""

    def __init__(self, questionnaire_hash: str, step_catalog: Iterable[str]) -> None:
        self._baseline_questionnaire_hash = questionnaire_hash
        self._baseline_step_signature = self._hash_sequence(step_catalog)
        self._baseline_step_catalog = list(step_catalog)
        self._state_ids: set[int] = set()
        self._predicate_signature: set[str] | None = None

    @staticmethod
    def _hash_sequence(sequence: Iterable[str]) -> str:
        canonical = "|".join(str(item) for item in sequence)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def assert_immutable_metadata(
        self,
        questionnaire_hash: str,
        step_catalog: Iterable[str]
    ) -> None:
        """Ensure canonical questionnaire and step catalog remain unchanged."""

        if self._baseline_questionnaire_hash:
            if questionnaire_hash and questionnaire_hash != self._baseline_questionnaire_hash:
                raise GoldenRuleViolation("Questionnaire metadata hash mismatch")

        if self._hash_sequence(step_catalog) != self._baseline_step_signature:
            raise GoldenRuleViolation("Execution step catalog mutated")

    @calibrated_method("saaaaaa.utils.validation.golden_rule.GoldenRuleValidator.reset_atomic_state")
    def reset_atomic_state(self) -> None:
        """Reset atomic state tracking between phases."""

        self._state_ids.clear()

    @calibrated_method("saaaaaa.utils.validation.golden_rule.GoldenRuleValidator.assert_atomic_context")
    def assert_atomic_context(self, state_obj: object) -> None:
        """Ensure copy-on-write semantics for per-step state."""

        obj_id = id(state_obj)
        if obj_id in self._state_ids:
            raise GoldenRuleViolation("State object reused across steps")

        self._state_ids.add(obj_id)

    @calibrated_method("saaaaaa.utils.validation.golden_rule.GoldenRuleValidator.assert_deterministic_dag")
    def assert_deterministic_dag(self, step_ids: list[str]) -> None:
        """Validate deterministic ordering and absence of cycles."""

        if len(step_ids) != len(set(step_ids)):
            raise GoldenRuleViolation("Duplicate step identifiers detected")

        # Validate that step_ids is a subsequence of the canonical step catalog and in the same order
        canonical = self._baseline_step_catalog
        canonical_indices = {step_id: idx for idx, step_id in enumerate(canonical)}
        try:
            indices = [canonical_indices[step_id] for step_id in step_ids]
        except KeyError as e:
            raise GoldenRuleViolation(f"Step ID '{e.args[0]}' not found in canonical step catalog")
        if indices != sorted(indices):
            raise GoldenRuleViolation("Execution chain deviates from canonical order")
    @calibrated_method("saaaaaa.utils.validation.golden_rule.GoldenRuleValidator.assert_homogeneous_treatment")
    def assert_homogeneous_treatment(self, predicate_set: Iterable[str]) -> None:
        """Ensure identical predicate set is applied across all questions."""

        fingerprint = {str(item) for item in predicate_set}

        if self._predicate_signature is None:
            self._predicate_signature = fingerprint
            return

        if fingerprint != self._predicate_signature:
            raise GoldenRuleViolation("Predicate set mismatch detected")

    @property
    @calibrated_method("saaaaaa.utils.validation.golden_rule.GoldenRuleValidator.baseline_step_catalog")
    def baseline_step_catalog(self) -> list[str]:
        """Expose the baseline step catalog for downstream validation."""

        return list(self._baseline_step_catalog)
