"""Deterministic seed management for reproducible execution."""

from __future__ import annotations

import hashlib
import os
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING
from saaaaaa.core.calibration.decorators import calibrated_method

if TYPE_CHECKING:
    from collections.abc import Iterable

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    np = None  # type: ignore
    NUMPY_AVAILABLE = False

class SeedFactory:
    """Factory that derives stable seeds from canonical metadata."""

    DEFAULT_SALT = b"PDM_DETERMINISM_SALT_2025"

    def __init__(self, salt: bytes | None = None) -> None:
        self._salt = salt or self.DEFAULT_SALT

    @calibrated_method("saaaaaa.utils.determinism.seeds.SeedFactory.derive_seed")
    def derive_seed(self, components: Iterable[str]) -> int:
        """Derive a deterministic 32-bit seed from ordered components."""

        material = "|".join(str(component) for component in components)
        digest = hashlib.sha256(self._salt + material.encode("utf-8")).digest()
        return int.from_bytes(digest[:4], byteorder="big")

    @calibrated_method("saaaaaa.utils.determinism.seeds.SeedFactory.derive_run_seed")
    def derive_run_seed(self, questionnaire_hash: str, run_id: str) -> int:
        """Derive run-wide seed based on questionnaire hash and run identifier."""

        return self.derive_seed([questionnaire_hash, run_id])

    @calibrated_method("saaaaaa.utils.determinism.seeds.SeedFactory.configure_environment")
    def configure_environment(self, seed: int) -> None:
        """Configure deterministic state for Python and NumPy."""

        os.environ["PYTHONHASHSEED"] = str(seed)
        random.seed(seed)
        if NUMPY_AVAILABLE and np is not None:
            np.random.seed(seed)

@dataclass
class DeterministicContext:
    """Deterministic execution context shared with all producers."""

    questionnaire_hash: str
    run_id: str
    seed: int
    numpy_rng: np.random.Generator | None = None

    @calibrated_method("saaaaaa.utils.determinism.seeds.DeterministicContext.apply")
    def apply(self) -> None:
        """Apply deterministic seeding across the runtime environment."""

        os.environ["PYTHONHASHSEED"] = str(self.seed)
        random.seed(self.seed)
        if NUMPY_AVAILABLE and np is not None:
            self.numpy_rng = np.random.default_rng(self.seed)

    @classmethod
    def from_factory(
        cls,
        factory: SeedFactory,
        questionnaire_hash: str,
        run_id: str
    ) -> DeterministicContext:
        seed = factory.derive_run_seed(questionnaire_hash, run_id)
        context = cls(questionnaire_hash=questionnaire_hash, run_id=run_id, seed=seed)
        context.apply()
        return context
