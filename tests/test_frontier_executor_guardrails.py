"""Tests for FrontierExecutorOrchestrator guardrails."""

import pytest

from saaaaaa.core.orchestrator.executors import FrontierExecutorOrchestrator


def test_normalize_question_id_variations() -> None:
    """normalize_question_id should support legacy formats."""
    orchestrator = FrontierExecutorOrchestrator()
    assert orchestrator.normalize_question_id("D1-Q1") == "D1Q1"
    assert orchestrator.normalize_question_id("d6_q5") == "D6Q5"
    assert orchestrator.normalize_question_id("  D4  Q3 ") == "D4Q3"


def test_executor_coverage_guard_detects_missing_executor() -> None:
    """_verify_executor_coverage should fail when an executor is missing."""
    orchestrator = FrontierExecutorOrchestrator()
    orchestrator.executors.pop("D1Q1")

    with pytest.raises(RuntimeError):
        orchestrator._verify_executor_coverage()
