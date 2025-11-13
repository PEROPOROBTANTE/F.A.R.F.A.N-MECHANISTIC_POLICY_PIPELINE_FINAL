"""Compatibility shim exposing orchestrator facilities from the refactored package.

IMPORTANT: This is a COMPATIBILITY LAYER for backward compatibility only.
The real orchestrator implementation is in src/saaaaaa/core/orchestrator/.

All orchestration-related code is consolidated in ONE location:
    src/saaaaaa/core/orchestrator/

This directory (orchestrator/) contains only thin compatibility shims that
redirect imports to the real implementation. See PROJECT_STRUCTURE.md for details.

New code should import directly from saaaaaa.core.orchestrator, not from this
compatibility layer.
"""
from __future__ import annotations

import contextlib
import sys
from importlib import import_module
from pathlib import Path
from typing import Any

# Add src to path for development environments
_SRC_PATH = Path(__file__).resolve().parent.parent / "src"
if _SRC_PATH.exists():  # pragma: no cover - executed at import time
    src_str = str(_SRC_PATH)
# Import from unified orchestrator package (if available) or fall back to submodules
try:
    from saaaaaa.core.orchestrator import (
        AbortRequested,
        AbortSignal,
        Evidence,
        EvidenceRecord,
        EvidenceRegistry,
        JSONContractLoader,
        LoadError,
        LoadResult,
        MethodExecutor,
        MicroQuestionRun,
        Orchestrator,
        PhaseInstrumentation,
        PhaseResult,
        PreprocessedDocument,
        ProvenanceDAG,
        ProvenanceNode,
        ResourceLimits,
        ScoredMicroQuestion,
        get_global_registry,
        get_questionnaire_payload,
        get_questionnaire_provider,
    )
except ImportError:
    # Fall back to granular imports
    from saaaaaa.core.orchestrator.contract_loader import (
        JSONContractLoader,
        LoadError,
        LoadResult,
    )
    from saaaaaa.core.orchestrator.core import (
        AbortRequested,
        AbortSignal,
        Evidence,
        MethodExecutor,
        MicroQuestionRun,
        Orchestrator,
        PhaseInstrumentation,
        PhaseResult,
        PreprocessedDocument,
        ResourceLimits,
        ScoredMicroQuestion,
    )
    from saaaaaa.core.orchestrator.evidence_registry import (
        EvidenceRecord,
        EvidenceRegistry,
        ProvenanceDAG,
        ProvenanceNode,
        get_global_registry,
    )

    from .provider import get_questionnaire_payload, get_questionnaire_provider

from .factory import build_processor  # noqa: E402

# Import submodules for backwards compatibility (lazy loading to avoid dependency issues)
core = import_module("saaaaaa.core.orchestrator.core")
# Note: executors module requires numpy and other heavy dependencies
# Import it lazily only when needed via __getattr__
_executors = None

__all__ = [
    "AbortRequested",
    "AbortSignal",
    "Evidence",
    "EvidenceRecord",
    "EvidenceRegistry",
    "JSONContractLoader",
    "LoadError",
    "LoadResult",
    "MethodExecutor",
    "MicroQuestionRun",
    "Orchestrator",
    "PhaseInstrumentation",
    "PhaseResult",
    "PreprocessedDocument",
    "ProvenanceDAG",
    "ProvenanceNode",
    "ResourceLimits",
    "ScoredMicroQuestion",
    "build_processor",
    "core",
    "executors",
    "get_global_registry",
    "get_questionnaire_payload",
    "get_questionnaire_provider",
]

# Register submodule aliases for backwards compatibility (lazy loading)
_SUBMODULE_ALIASES: dict[str, str] = {
    "orchestrator.arg_router": "saaaaaa.core.orchestrator.arg_router",
    "orchestrator.class_registry": "saaaaaa.core.orchestrator.class_registry",
    "orchestrator.contract_loader": "saaaaaa.core.orchestrator.contract_loader",
    "orchestrator.core": "saaaaaa.core.orchestrator.core",
    "orchestrator.evidence_registry": "saaaaaa.core.orchestrator.evidence_registry",
    # "orchestrator.executors": "saaaaaa.core.orchestrator.executors",  # Lazy load via __getattr__
    "orchestrator.factory": "saaaaaa.core.orchestrator.factory",
}

for alias, target in _SUBMODULE_ALIASES.items():
    if alias not in sys.modules:
        with contextlib.suppress(ImportError):
            # Skip modules that have missing dependencies
            sys.modules[alias] = import_module(target)

def __getattr__(name: str) -> Any:  # noqa: ANN401  # pragma: no cover - delegation helper
    """Delegate unknown attributes to the core module or lazily load executors."""
    global _executors

    # Lazily import executors module only when accessed
    if name == "executors":
        if _executors is None:
            _executors = import_module("saaaaaa.core.orchestrator.executors")
        return _executors

    return getattr(core, name)
