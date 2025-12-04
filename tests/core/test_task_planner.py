import json
from pathlib import Path
from typing import Any

import pytest

from farfan_pipeline.core.orchestrator.task_planner import (
    EXPECTED_TASKS_PER_CHUNK,
    ExecutableTask,
    MicroQuestionContext,
    _construct_task,
    _validate_cross_task,
    _validate_schema,
    extract_expected_elements,
    extract_signal_requirements,
    sort_micro_question_contexts,
)


class TestValidateSchema:
    def test_validate_schema_with_matching_elements(self):
        question = {
            "question_id": "Q001",
            "expected_elements": [
                {"type": "fuentes_oficiales", "minimum": 2},
                {"type": "indicadores_cuantitativos", "minimum": 3},
            ],
        }
        chunk = {
            "id": "chunk_001",
            "expected_elements": [
                {"type": "fuentes_oficiales", "minimum": 2},
                {"type": "indicadores_cuantitativos", "minimum": 3},
            ],
        }

        _validate_schema(question, chunk)

    def test_validate_schema_fails_on_mismatch(self):
        question = {
            "question_id": "Q001",
            "expected_elements": [
                {"type": "fuentes_oficiales", "minimum": 2},
                {"type": "indicadores_cuantitativos", "minimum": 3},
            ],
        }
        chunk = {
            "id": "chunk_001",
            "expected_elements": [
                {"type": "fuentes_oficiales", "minimum": 3},
                {"type": "series_temporales", "minimum": 2},
            ],
        }

        with pytest.raises(ValueError) as exc_info:
            _validate_schema(question, chunk)

        assert "Schema mismatch" in str(exc_info.value)
        assert "fuentes_oficiales" in str(exc_info.value)
        assert "Question schema:" in str(exc_info.value)
        assert "Chunk schema:" in str(exc_info.value)


class TestConstructTask:
    def test_construct_task_generates_correct_id(self):
        question = {
            "question_id": "D1-Q1",
            "question_global": 1,
            "policy_area_id": "PA01",
            "dimension_id": "DIM01",
            "base_slot": "D1-Q1",
            "cluster_id": "CL01",
            "expected_elements": [{"type": "fuentes_oficiales", "minimum": 2}],
            "signal_requirements": {"signal1": 0.3},
        }
        chunk = {"id": "chunk_001", "expected_elements": []}
        patterns = [{"type": "pattern1"}]
        signals = {"signal1": 0.5}
        generated_ids: set[str] = set()

        task = _construct_task(question, chunk, patterns, signals, generated_ids)

        assert task.task_id == "MQC-001_PA01"
        assert task.question_id == "D1-Q1"
        assert task.question_global == 1
        assert task.policy_area_id == "PA01"
        assert task.dimension_id == "DIM01"
        assert task.chunk_id == "chunk_001"
        assert task.patterns == patterns
        assert task.signals == signals
        assert task.expected_elements == question["expected_elements"]
        assert task.metadata["base_slot"] == "D1-Q1"
        assert task.metadata["cluster_id"] == "CL01"
        assert "MQC-001_PA01" in generated_ids
        assert task.context is not None
        assert isinstance(task.context, MicroQuestionContext)
        assert task.context.base_slot == "D1-Q1"
        assert task.context.cluster_id == "CL01"

    def test_construct_task_rejects_duplicate_id(self):
        question = {
            "question_id": "D1-Q1",
            "question_global": 1,
            "policy_area_id": "PA01",
            "dimension_id": "DIM01",
            "expected_elements": [],
        }
        chunk = {"id": "chunk_001", "expected_elements": []}
        patterns = []
        signals = {}
        generated_ids = {"MQC-001_PA01"}

        with pytest.raises(ValueError) as exc_info:
            _construct_task(question, chunk, patterns, signals, generated_ids)

        assert "Duplicate task_id detected: MQC-001_PA01" in str(exc_info.value)

    def test_construct_task_timestamp_format(self):
        question = {
            "question_id": "D1-Q1",
            "question_global": 15,
            "policy_area_id": "PA05",
            "dimension_id": "DIM02",
            "expected_elements": [],
        }
        chunk = {"id": "chunk_002", "expected_elements": []}
        generated_ids: set[str] = set()

        task = _construct_task(question, chunk, [], {}, generated_ids)

        assert "T" in task.creation_timestamp
        assert task.creation_timestamp.endswith("Z") or "." in task.creation_timestamp


class TestValidateCrossTask:
    def test_cross_task_validation_with_canonical_questionnaire(self):
        questionnaire_path = Path(
            "system/config/questionnaire/questionnaire_monolith.json"
        )

        if not questionnaire_path.exists():
            pytest.skip("Canonical questionnaire not found")

        with open(questionnaire_path) as f:
            data = json.load(f)

        blocks = data.get("blocks", {})
        micro_questions = blocks.get("micro_questions", [])

        if not micro_questions:
            pytest.skip("No micro_questions found in questionnaire")

        plan: list[ExecutableTask] = []
        generated_ids: set[str] = set()

        chunk_map: dict[str, dict[str, Any]] = {}
        for i in range(60):
            chunk_id = f"chunk_{i:03d}"
            chunk_map[chunk_id] = {"id": chunk_id, "expected_elements": []}

        for idx, question in enumerate(micro_questions[:300]):
            chunk_id = f"chunk_{(idx // 5):03d}"

            task = ExecutableTask(
                task_id=f"MQC-{question.get('question_global', idx+1):03d}_{question.get('policy_area_id', 'PA01')}",
                question_id=question.get("question_id", f"Q{idx+1}"),
                question_global=question.get("question_global", idx + 1),
                policy_area_id=question.get("policy_area_id", "PA01"),
                dimension_id=question.get("dimension_id", "DIM01"),
                chunk_id=chunk_id,
                patterns=[],
                signals={},
                creation_timestamp="2024-01-01T00:00:00Z",
                expected_elements=[],
            )
            plan.append(task)
            generated_ids.add(task.task_id)

        _validate_cross_task(plan)

        chunk_usage: dict[str, int] = {}
        for task in plan:
            chunk_usage[task.chunk_id] = chunk_usage.get(task.chunk_id, 0) + 1

        for chunk_id in chunk_map:
            if chunk_id in chunk_usage:
                assert (
                    chunk_usage[chunk_id] == EXPECTED_TASKS_PER_CHUNK
                ), f"Chunk {chunk_id} should be used exactly {EXPECTED_TASKS_PER_CHUNK} times, got {chunk_usage[chunk_id]}"

    def test_cross_task_validation_warns_on_deviations(self, caplog):
        plan = [
            ExecutableTask(
                task_id=f"MQC-{i:03d}_PA01",
                question_id=f"Q{i}",
                question_global=i,
                policy_area_id="PA01",
                dimension_id="DIM01",
                chunk_id="chunk_001",
                patterns=[],
                signals={},
                creation_timestamp="2024-01-01T00:00:00Z",
            )
            for i in range(1, 4)
        ]

        with caplog.at_level("WARNING"):
            _validate_cross_task(plan)

        assert any(
            "Chunk usage deviation" in record.message for record in caplog.records
        )
        assert any(
            "chunk_001 used 3 times (expected 5)" in record.message
            for record in caplog.records
        )

    def test_cross_task_validation_policy_area_warning(self, caplog):
        plan = [
            ExecutableTask(
                task_id=f"MQC-{i:03d}_PA01",
                question_id=f"Q{i}",
                question_global=i,
                policy_area_id="PA01",
                dimension_id="DIM01",
                chunk_id=f"chunk_{i:03d}",
                patterns=[],
                signals={},
                creation_timestamp="2024-01-01T00:00:00Z",
            )
            for i in range(1, 11)
        ]

        with caplog.at_level("WARNING"):
            _validate_cross_task(plan)

        assert any(
            "Policy area usage deviation" in record.message for record in caplog.records
        )
        assert any(
            "PA01 used 10 times (expected 30)" in record.message
            for record in caplog.records
        )


class TestExecutableTask:
    def test_executable_task_creation(self):
        signal_value = 0.8
        task = ExecutableTask(
            task_id="MQC-001_PA01",
            question_id="D1-Q1",
            question_global=1,
            policy_area_id="PA01",
            dimension_id="DIM01",
            chunk_id="chunk_001",
            patterns=[{"type": "pattern1"}],
            signals={"signal1": signal_value},
            creation_timestamp="2024-01-01T00:00:00Z",
            expected_elements=[{"type": "test", "minimum": 1}],
            metadata={"key": "value"},
        )

        assert task.task_id == "MQC-001_PA01"
        assert task.question_global == 1
        assert task.policy_area_id == "PA01"
        assert len(task.patterns) == 1
        assert task.signals["signal1"] == signal_value
        assert len(task.expected_elements) == 1
        assert task.metadata["key"] == "value"


class TestMicroQuestionContext:
    def test_context_is_frozen(self):
        context = MicroQuestionContext(
            task_id="MQC-001_PA01",
            question_id="D1-Q1",
            question_global=1,
            policy_area_id="PA01",
            dimension_id="DIM01",
            chunk_id="chunk_001",
            base_slot="D1-Q1",
            cluster_id="CL01",
            patterns=[{"type": "pattern1"}],
            signals={"signal1": 0.5},
            expected_elements=[{"type": "test", "minimum": 1}],
            signal_requirements={"signal1": 0.3},
            creation_timestamp="2024-01-01T00:00:00Z",
        )

        assert context.task_id == "MQC-001_PA01"
        assert context.question_global == 1
        assert isinstance(context.patterns, tuple)
        assert isinstance(context.expected_elements, tuple)

        with pytest.raises(AttributeError):
            context.task_id = "new_id"

    def test_extract_expected_elements(self):
        context = MicroQuestionContext(
            task_id="MQC-001_PA01",
            question_id="D1-Q1",
            question_global=1,
            policy_area_id="PA01",
            dimension_id="DIM01",
            chunk_id="chunk_001",
            base_slot="D1-Q1",
            cluster_id="CL01",
            patterns=[],
            signals={},
            expected_elements=[{"type": "test", "minimum": 1}, {"type": "test2"}],
            signal_requirements={},
            creation_timestamp="2024-01-01T00:00:00Z",
        )

        elements = extract_expected_elements(context)
        assert isinstance(elements, list)
        assert len(elements) == 2
        assert elements[0]["type"] == "test"

    def test_extract_signal_requirements(self):
        context = MicroQuestionContext(
            task_id="MQC-001_PA01",
            question_id="D1-Q1",
            question_global=1,
            policy_area_id="PA01",
            dimension_id="DIM01",
            chunk_id="chunk_001",
            base_slot="D1-Q1",
            cluster_id="CL01",
            patterns=[],
            signals={},
            expected_elements=[],
            signal_requirements={"signal1": 0.5, "signal2": 0.7},
            creation_timestamp="2024-01-01T00:00:00Z",
        )

        requirements = extract_signal_requirements(context)
        assert isinstance(requirements, dict)
        assert requirements["signal1"] == 0.5
        assert requirements["signal2"] == 0.7

    def test_sort_micro_question_contexts(self):
        contexts = [
            MicroQuestionContext(
                task_id="MQC-002_PA02",
                question_id="D1-Q2",
                question_global=2,
                policy_area_id="PA02",
                dimension_id="DIM01",
                chunk_id="chunk_002",
                base_slot="D1-Q2",
                cluster_id="CL01",
                patterns=[],
                signals={},
                expected_elements=[],
                signal_requirements={},
                creation_timestamp="2024-01-01T00:00:00Z",
            ),
            MicroQuestionContext(
                task_id="MQC-051_PA01",
                question_id="D2-Q1",
                question_global=51,
                policy_area_id="PA01",
                dimension_id="DIM02",
                chunk_id="chunk_010",
                base_slot="D2-Q1",
                cluster_id="CL01",
                patterns=[],
                signals={},
                expected_elements=[],
                signal_requirements={},
                creation_timestamp="2024-01-01T00:00:00Z",
            ),
            MicroQuestionContext(
                task_id="MQC-001_PA01",
                question_id="D1-Q1",
                question_global=1,
                policy_area_id="PA01",
                dimension_id="DIM01",
                chunk_id="chunk_001",
                base_slot="D1-Q1",
                cluster_id="CL01",
                patterns=[],
                signals={},
                expected_elements=[],
                signal_requirements={},
                creation_timestamp="2024-01-01T00:00:00Z",
            ),
        ]

        sorted_contexts = sort_micro_question_contexts(contexts)
        assert sorted_contexts[0].question_global == 1
        assert sorted_contexts[1].question_global == 2
        assert sorted_contexts[2].question_global == 51
        assert sorted_contexts[0].dimension_id == "DIM01"
        assert sorted_contexts[2].dimension_id == "DIM02"
