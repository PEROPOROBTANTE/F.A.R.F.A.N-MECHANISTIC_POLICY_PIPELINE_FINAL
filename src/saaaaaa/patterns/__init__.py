"""
FARFAN Mechanistic Policy Pipeline - Patterns Module
=====================================================

Design patterns for robust distributed systems including:
- Saga pattern for compensating transactions
- Event tracking for observability

Author: FARFAN Team
Date: 2025-11-13
Version: 1.0.0
"""

from .event_tracking import (
    Event,
    EventCategory,
    EventLevel,
    EventSpan,
    EventTracker,
    get_global_tracker,
    record_event,
    span,
)
from .saga import (
    SagaEvent,
    SagaOrchestrator,
    SagaStatus,
    SagaStep,
    SagaStepStatus,
    compensate_api_call,
    compensate_database_insert,
    compensate_file_write,
)

__all__ = [
    # Event Tracking
    "Event",
    "EventCategory",
    "EventLevel",
    "EventSpan",
    "EventTracker",
    "get_global_tracker",
    "record_event",
    "span",
    # Saga Pattern
    "SagaEvent",
    "SagaOrchestrator",
    "SagaStatus",
    "SagaStep",
    "SagaStepStatus",
    "compensate_api_call",
    "compensate_database_insert",
    "compensate_file_write",
]
