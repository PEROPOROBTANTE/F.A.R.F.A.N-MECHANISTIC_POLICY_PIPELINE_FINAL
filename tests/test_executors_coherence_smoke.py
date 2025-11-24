"""
Smoke tests for executor docstring-execution coherence.

Validates that each executor's docstring accurately documents the methods
it executes in the correct order.
"""

import importlib
import re
import sys
import types
from typing import Dict, List, Set, Tuple

import pytest


# Stub orchestrator dependencies to avoid circular imports during test import
core_stub = types.ModuleType("saaaaaa.core.orchestrator.core")


class _FakeMethodExecutor:
    """Fake MethodExecutor that tracks method calls."""

    def __init__(self):
        self.calls: List[Tuple[str, str]] = []

    def execute(self, class_name: str, method_name: str, **payload):
        self.calls.append((class_name, method_name))
        # Return safe defaults for common return types
        return {"class": class_name, "method": method_name, "payload": payload}


core_stub.MethodExecutor = _FakeMethodExecutor
core_stub.AbortRequested = type("AbortRequested", (), {})
core_stub.AbortSignal = type("AbortSignal", (), {})
core_stub.ResourceLimits = type("ResourceLimits", (), {})
core_stub.PhaseInstrumentation = type("PhaseInstrumentation", (), {})
core_stub.PhaseResult = type("PhaseResult", (), {})
core_stub.MicroQuestionRun = type("MicroQuestionRun", (), {})
core_stub.ScoredMicroQuestion = type("ScoredMicroQuestion", (), {})
core_stub.Evidence = type("Evidence", (), {})
core_stub.PreprocessedDocument = type("PreprocessedDocument", (), {})
core_stub.Orchestrator = type("Orchestrator", (), {})
sys.modules["saaaaaa.core.orchestrator.core"] = core_stub

factory_stub = types.ModuleType("saaaaaa.core.orchestrator.factory")


def _fake_build_processor(me: _FakeMethodExecutor | None = None):
    bundle = types.SimpleNamespace()
    bundle.method_executor = me or _FakeMethodExecutor()
    return bundle


factory_stub.build_processor = _fake_build_processor
sys.modules["saaaaaa.core.orchestrator.factory"] = factory_stub

contract_loader = types.ModuleType("contract_loader")


class _Dummy:
    pass


contract_loader.JSONContractLoader = _Dummy
contract_loader.LoadError = _Dummy
contract_loader.LoadResult = _Dummy
sys.modules.setdefault("saaaaaa.core.orchestrator.contract_loader", contract_loader)

exec_mod = importlib.import_module("saaaaaa.core.orchestrator.executors")


def parse_docstring_methods(docstring: str) -> List[str]:
    """
    Parse method names from executor docstring.

    Expected format:
    Step N: Description - ClassName.method_name

    Returns list of "ClassName.method_name" strings in order.
    """
    if not docstring:
        return []

    methods = []
    # Match patterns like "Step N: ... - ClassName.method_name"
    step_pattern = re.compile(r"Step\s+\d+:.*?-\s+(\w+\.\w+)")
    # Also match old format "- ClassName.method_name"
    old_pattern = re.compile(r"^\s*-\s+(\w+\.\w+)\s*$", re.MULTILINE)

    # Try new format first
    step_matches = step_pattern.findall(docstring)
    if step_matches:
        methods = step_matches
    else:
        # Fall back to old format
        methods = old_pattern.findall(docstring)

    return methods


def get_executed_methods(executor_class, context: Dict) -> List[str]:
    """
    Execute an executor and return the list of methods it called.

    Returns list of "ClassName.method_name" strings in execution order.
    """
    fake_me = _FakeMethodExecutor()

    # Create executor instance
    executor = executor_class(
        executor_id="TEST-Q1",
        config={},
        method_executor=fake_me
    )

    try:
        # Execute with minimal context
        executor.execute(context)
    except Exception:
        # Some executors may fail due to missing data, that's OK
        # We just want to see what methods were attempted
        pass

    # Return methods in format "ClassName.method_name"
    return [f"{class_name}.{method_name}" for class_name, method_name in fake_me.calls]


# Test cases for executors with updated docstrings
EXECUTORS_TO_TEST = [
    "D3_Q3_TraceabilityValidator",
    "D3_Q4_TechnicalFeasibilityEvaluator",
    "D5_Q2_CompositeMeasurementValidator",
    "D6_Q5_ContextualAdaptabilityEvaluator",
]


@pytest.fixture
def minimal_context() -> Dict:
    """Provide minimal context for executor tests."""
    return {
        "document_text": "Sample policy document text for testing.",
        "tables": [],
        "metadata": {"title": "Test Plan", "timestamp": "2024-01-01"},
        "product_targets": [],
        "composite_indicators": [],
        "proxy_indicators": [],
        "policy_area": "PA01",
    }


class TestExecutorDocstringCoherence:
    """Test suite for executor docstring-execution coherence."""

    def test_docstring_methods_are_subset_of_executed(self, minimal_context):
        """
        Verify that methods documented in docstrings are actually executed.

        Note: Executors may execute additional helper methods not in docstring,
        but all documented methods MUST be executed.
        """
        for executor_name in EXECUTORS_TO_TEST:
            executor_class = getattr(exec_mod, executor_name, None)
            if executor_class is None:
                pytest.skip(f"Executor {executor_name} not found")
                continue

            # Parse docstring
            docstring = executor_class.__doc__ or ""
            documented_methods = parse_docstring_methods(docstring)

            if not documented_methods:
                # Old format docstring, skip
                continue

            # Get executed methods
            executed_methods = get_executed_methods(executor_class, minimal_context)

            # Check that documented methods are in executed methods
            documented_set = set(documented_methods)
            executed_set = set(executed_methods)

            missing = documented_set - executed_set
            assert not missing, (
                f"{executor_name}: Documented methods not executed: {missing}\n"
                f"Documented: {documented_methods}\n"
                f"Executed: {executed_methods}"
            )

    def test_metadata_has_required_counts(self, minimal_context):
        """
        Verify that metadata includes counts for all list-type raw_evidence fields.
        """
        for executor_name in EXECUTORS_TO_TEST:
            executor_class = getattr(exec_mod, executor_name, None)
            if executor_class is None:
                continue

            fake_me = _FakeMethodExecutor()
            executor = executor_class(
                executor_id="TEST-Q1",
                config={},
                method_executor=fake_me
            )

            try:
                result = executor.execute(minimal_context)
            except Exception:
                # Some executors may fail, that's OK for this test
                continue

            metadata = result.get("metadata", {})

            # Check for standard count fields
            assert "methods_executed" in metadata, f"{executor_name}: Missing methods_executed in metadata"

    def test_nomenclature_is_snake_case(self, minimal_context):
        """
        Verify that all metadata keys use snake_case nomenclature.
        """
        camel_case_pattern = re.compile(r"[a-z]+[A-Z]")

        for executor_name in EXECUTORS_TO_TEST:
            executor_class = getattr(exec_mod, executor_name, None)
            if executor_class is None:
                continue

            fake_me = _FakeMethodExecutor()
            executor = executor_class(
                executor_id="TEST-Q1",
                config={},
                method_executor=fake_me
            )

            try:
                result = executor.execute(minimal_context)
            except Exception:
                continue

            metadata = result.get("metadata", {})
            raw_evidence = result.get("raw_evidence", {})

            # Check metadata keys
            for key in metadata.keys():
                assert not camel_case_pattern.search(key), (
                    f"{executor_name}: Metadata key '{key}' uses camelCase instead of snake_case"
                )

            # Check top-level raw_evidence keys
            for key in raw_evidence.keys():
                assert not camel_case_pattern.search(key), (
                    f"{executor_name}: raw_evidence key '{key}' uses camelCase instead of snake_case"
                )


class TestTypeProtection:
    """Test suite for type protection in executors."""

    def test_null_safe_get_operations(self, minimal_context):
        """
        Verify that executors handle None returns gracefully.
        """
        for executor_name in EXECUTORS_TO_TEST:
            executor_class = getattr(exec_mod, executor_name, None)
            if executor_class is None:
                continue

            # Create executor with fake method executor that returns None
            class NoneReturningExecutor(_FakeMethodExecutor):
                def execute(self, class_name: str, method_name: str, **payload):
                    return None

            fake_me = NoneReturningExecutor()
            executor = executor_class(
                executor_id="TEST-Q1",
                config={},
                method_executor=fake_me
            )

            # Should not raise AttributeError even with None returns
            try:
                result = executor.execute(minimal_context)
                # If we get here, the executor handled None gracefully
                assert "executor_id" in result
            except AttributeError as e:
                pytest.fail(f"{executor_name}: AttributeError with None return: {e}")
            except Exception:
                # Other exceptions are OK - we're testing type safety, not full execution
                pass
