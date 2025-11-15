"""Questionnaire provider access with runtime boundary enforcement."""
from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from saaaaaa.core.orchestrator.contract_loader import QuestionnaireProvider

from saaaaaa.core.orchestrator import get_questionnaire_provider as _core_get_provider

ALLOWED_PACKAGES = {"orchestrator", "saaaaaa", "scripts", "build_monolith", "__main__"}

def _resolve_root_package(frame_globals: dict[str, Any]) -> str:
    """Return the root package for the caller represented by *frame_globals*."""
    package = frame_globals.get("__package__")
    if package:
        return package.split(".", 1)[0]
    module_name = frame_globals.get("__name__", "")
    if module_name:
        return module_name.split(".", 1)[0]
    return ""

def _enforce_boundary() -> None:
    """Ensure only orchestrator package consumers reach the provider."""
    frame = inspect.currentframe()
    if frame is None:
        return
    frame = frame.f_back  # Skip the enforcement helper itself
    orchestrator_intermediate = False
    while frame is not None:
        root = _resolve_root_package(frame.f_globals)
        if root and root not in ALLOWED_PACKAGES:
            if not orchestrator_intermediate:
                raise RuntimeError(
                    "Questionnaire provider access restricted to orchestrator package"
                )
            return
        if root in ALLOWED_PACKAGES:
            module_name = frame.f_globals.get("__name__", "")
            if not module_name.startswith("orchestrator.provider"):
                orchestrator_intermediate = True
        frame = frame.f_back

def get_questionnaire_provider() -> QuestionnaireProvider:
    """Return the shared questionnaire provider if boundary checks pass."""
    _enforce_boundary()
    return _core_get_provider()

def get_questionnaire_payload(*, force_reload: bool = False) -> Any:  # noqa: ANN401
    """Retrieve questionnaire payload while honouring boundary restrictions."""
    provider = get_questionnaire_provider()
    return provider.load(force_reload=force_reload)
