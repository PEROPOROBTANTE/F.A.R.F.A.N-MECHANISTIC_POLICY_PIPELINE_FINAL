"""Compatibility shim for choreographer dispatcher helpers.

NOTE: This shim redirects to the ChoreographerDispatcher class in the real
implementation at src/saaaaaa/core/orchestrator/choreographer.py.

New code should import directly from saaaaaa.core.orchestrator.choreographer.
"""
from saaaaaa.core.orchestrator.choreographer import (  # noqa: F401
    ChoreographerDispatcher,
)

__all__ = ["ChoreographerDispatcher"]
