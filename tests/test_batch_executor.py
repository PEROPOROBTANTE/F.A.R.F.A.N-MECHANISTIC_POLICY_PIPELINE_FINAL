"""Tests for batch executor infrastructure."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from farfan_pipeline.core.orchestrator.batch_executor import (
    COMPLEXITY_BATCH_SIZE_MAP,
    EXECUTOR_COMPLEXITY_MAP,
    AggregatedBatchResults,
    BatchExecutor,
    BatchExecutorConfig,
    BatchResult,
    BatchStatus,
    ExecutorComplexity,
)
from farfan_pipeline.core.types import PreprocessedDocument


@pytest.fixture
def batch_config():
    """Create batch executor configuration."""
    return BatchExecutorConfig(
        default_batch_size=10,
        max_batch_size=50,
        min_batch_size=2,
        enable_streaming=True,
        error_threshold=0.5,
        max_retries=2,
        enable_instrumentation=False,
    )


@pytest.fixture
def mock_method_executor():
    """Create mock method executor."""
    executor = MagicMock()
    executor.signal_registry = MagicMock()
    return executor


@pytest.fixture
def sample_document():
    """Create sample preprocessed document."""
    return PreprocessedDocument(
        document_id="test_doc_001",
        raw_text="Sample document text for testing batch processing.",
        sentences=["Sample document text for testing batch processing."],
        tables=[],
        metadata={"source": "test"},
        source_path=Path("/tmp/test.pdf"),
    )


@pytest.fixture
def sample_question_context():
    """Create sample question context."""
    return {
        "question_id": "D1-Q1",
        "question_global": 1,
        "base_slot": "D1-Q1",
        "dimension_id": "DIM01",
        "policy_area_id": "PA01",
        "cluster_id": "CLU01",
        "scoring_modality": "quantitative",
        "expected_elements": ["baseline", "metrics"],
    }


class MockExecutor:
    """Mock executor for testing."""

    def __init__(
        self,
        method_executor,
        signal_registry,
        config,
        questionnaire_provider,
        calibration_orchestrator,
    ):
        self.method_executor = method_executor
        self.signal_registry = signal_registry
        self.config = config
        self.questionnaire_provider = questionnaire_provider
        self.calibration_orchestrator = calibration_orchestrator
        self.call_count = 0

    def execute(self, document, method_executor, question_context):
        """Mock execute method."""
        self.call_count += 1
        return {
            "evidence": {"baseline": "test_value"},
            "metadata": {"executed": True},
            "call_count": self.call_count,
        }


class FailingExecutor:
    """Mock executor that fails."""

    def __init__(
        self,
        method_executor,
        signal_registry,
        config,
        questionnaire_provider,
        calibration_orchestrator,
    ):
        self.method_executor = method_executor
        self.signal_registry = signal_registry

    def execute(self, document, method_executor, question_context):
        """Mock execute that always fails."""
        raise ValueError("Intentional test failure")


class PartialFailExecutor:
    """Mock executor that fails every other call."""

    def __init__(
        self,
        method_executor,
        signal_registry,
        config,
        questionnaire_provider,
        calibration_orchestrator,
    ):
        self.method_executor = method_executor
        self.call_count = 0

    def execute(self, document, method_executor, question_context):
        """Mock execute that fails every other call."""
        self.call_count += 1
        if self.call_count % 2 == 0:
            raise ValueError(f"Intentional failure on call {self.call_count}")
        return {"evidence": {"data": f"success_{self.call_count}"}}


class TestBatchExecutorConfig:
    """Test batch executor configuration."""

    def test_valid_config(self):
        """Test valid configuration."""
        config = BatchExecutorConfig(
            default_batch_size=10,
            max_batch_size=100,
            min_batch_size=1,
            error_threshold=0.3,
        )
        assert config.default_batch_size == 10
        assert config.max_batch_size == 100
        assert config.min_batch_size == 1
        assert config.error_threshold == 0.3

    def test_invalid_batch_sizes(self):
        """Test invalid batch size configuration."""
        with pytest.raises(ValueError, match="Invalid batch size configuration"):
            BatchExecutorConfig(
                default_batch_size=5,
                max_batch_size=3,
                min_batch_size=1,
            )

    def test_invalid_error_threshold(self):
        """Test invalid error threshold."""
        with pytest.raises(ValueError, match="error_threshold must be in"):
            BatchExecutorConfig(error_threshold=1.5)

    def test_default_values(self):
        """Test default configuration values."""
        config = BatchExecutorConfig()
        assert config.default_batch_size == 10
        assert config.max_batch_size == 100
        assert config.min_batch_size == 1
        assert config.error_threshold == 0.5
        assert config.max_retries == 2
        assert config.enable_streaming is True


class TestComplexityMapping:
    """Test executor complexity mapping."""

    def test_complexity_map_coverage(self):
        """Test that all major executors have complexity mappings."""
        assert "D1-Q1" in EXECUTOR_COMPLEXITY_MAP
        assert "D3-Q2" in EXECUTOR_COMPLEXITY_MAP
        assert "D5-Q2" in EXECUTOR_COMPLEXITY_MAP

    def test_complexity_batch_size_map(self):
        """Test complexity to batch size mapping."""
        assert COMPLEXITY_BATCH_SIZE_MAP[ExecutorComplexity.SIMPLE] == 50
        assert COMPLEXITY_BATCH_SIZE_MAP[ExecutorComplexity.MODERATE] == 20
        assert COMPLEXITY_BATCH_SIZE_MAP[ExecutorComplexity.COMPLEX] == 10
        assert COMPLEXITY_BATCH_SIZE_MAP[ExecutorComplexity.VERY_COMPLEX] == 5

    def test_very_complex_executors(self):
        """Test that intensive executors are marked as very complex."""
        very_complex = [
            slot
            for slot, complexity in EXECUTOR_COMPLEXITY_MAP.items()
            if complexity == ExecutorComplexity.VERY_COMPLEX
        ]
        assert "D2-Q2" in very_complex
        assert "D3-Q2" in very_complex
        assert "D3-Q3" in very_complex


class TestBatchExecutorBasics:
    """Test basic batch executor functionality."""

    def test_initialization(self, batch_config, mock_method_executor):
        """Test batch executor initialization."""
        executor = BatchExecutor(
            config=batch_config,
            method_executor=mock_method_executor,
        )
        assert executor.config == batch_config
        assert executor.method_executor == mock_method_executor
        assert executor._batch_counter == 0

    def test_get_batch_size_for_executor(self, batch_config, mock_method_executor):
        """Test batch size determination based on complexity."""
        executor = BatchExecutor(
            config=batch_config, method_executor=mock_method_executor
        )

        batch_size_moderate = executor.get_batch_size_for_executor("D1-Q1")
        assert batch_size_moderate == 20

        batch_size_complex = executor.get_batch_size_for_executor("D3-Q2")
        assert batch_size_complex == 5

        batch_size_unknown = executor.get_batch_size_for_executor("UNKNOWN")
        assert batch_size_unknown == 20

    def test_batch_size_clamping(self, mock_method_executor):
        """Test that batch sizes respect min/max constraints."""
        config = BatchExecutorConfig(
            default_batch_size=10, max_batch_size=15, min_batch_size=8
        )
        executor = BatchExecutor(config=config, method_executor=mock_method_executor)

        batch_size = executor.get_batch_size_for_executor("D1-Q1")
        assert 8 <= batch_size <= 15

    def test_create_batches(self, batch_config, mock_method_executor):
        """Test batch creation from items."""
        executor = BatchExecutor(
            config=batch_config, method_executor=mock_method_executor
        )

        items = list(range(25))
        batches = executor._create_batches(items, batch_size=10)

        assert len(batches) == 3
        assert batches[0] == (0, list(range(0, 10)))
        assert batches[1] == (1, list(range(10, 20)))
        assert batches[2] == (2, list(range(20, 25)))

    def test_create_batches_exact_fit(self, batch_config, mock_method_executor):
        """Test batch creation with exact fit."""
        executor = BatchExecutor(
            config=batch_config, method_executor=mock_method_executor
        )

        items = list(range(20))
        batches = executor._create_batches(items, batch_size=10)

        assert len(batches) == 2
        assert all(len(batch[1]) == 10 for batch in batches)

    def test_create_batches_single_batch(self, batch_config, mock_method_executor):
        """Test batch creation with items fitting in single batch."""
        executor = BatchExecutor(
            config=batch_config, method_executor=mock_method_executor
        )

        items = list(range(5))
        batches = executor._create_batches(items, batch_size=10)

        assert len(batches) == 1
        assert batches[0] == (0, items)


class TestBatchExecution:
    """Test batch execution."""

    @pytest.mark.asyncio
    async def test_execute_single_batch_success(
        self,
        batch_config,
        mock_method_executor,
        sample_document,
        sample_question_context,
    ):
        """Test successful execution of a single batch."""
        executor = BatchExecutor(
            config=batch_config, method_executor=mock_method_executor
        )
        mock_executor_instance = MockExecutor(
            mock_method_executor, None, batch_config, None, None
        )

        batch_items = [1, 2, 3]
        result = await executor._execute_single_batch(
            "test_batch_001",
            0,
            batch_items,
            mock_executor_instance,
            sample_document,
            sample_question_context,
        )

        assert result.batch_id == "test_batch_001"
        assert result.batch_index == 0
        assert result.status == BatchStatus.COMPLETED
        assert result.metrics["successful_items"] == 3
        assert result.metrics["failed_items"] == 0
        assert len(result.results) == 3
        assert all(r is not None for r in result.results)

    @pytest.mark.asyncio
    async def test_execute_single_batch_all_failures(
        self,
        batch_config,
        mock_method_executor,
        sample_document,
        sample_question_context,
    ):
        """Test batch execution with all failures."""
        executor = BatchExecutor(
            config=batch_config, method_executor=mock_method_executor
        )
        mock_executor_instance = FailingExecutor(
            mock_method_executor, None, batch_config, None, None
        )

        batch_items = [1, 2, 3]
        result = await executor._execute_single_batch(
            "test_batch_002",
            0,
            batch_items,
            mock_executor_instance,
            sample_document,
            sample_question_context,
        )

        assert result.status == BatchStatus.FAILED
        assert result.metrics["successful_items"] == 0
        assert result.metrics["failed_items"] == 3
        assert len(result.errors) == 3
        assert all(r is None for r in result.results)

    @pytest.mark.asyncio
    async def test_execute_single_batch_partial_success(
        self, mock_method_executor, sample_document, sample_question_context
    ):
        """Test batch execution with partial success."""
        config = BatchExecutorConfig(error_threshold=0.6, enable_instrumentation=False)
        executor = BatchExecutor(config=config, method_executor=mock_method_executor)
        mock_executor_instance = PartialFailExecutor(
            mock_method_executor, None, config, None, None
        )

        batch_items = [1, 2, 3, 4]
        result = await executor._execute_single_batch(
            "test_batch_003",
            0,
            batch_items,
            mock_executor_instance,
            sample_document,
            sample_question_context,
        )

        assert result.status == BatchStatus.PARTIAL_SUCCESS
        assert result.metrics["successful_items"] == 2
        assert result.metrics["failed_items"] == 2
        assert len(result.get_successful_results()) == 2
        assert len(result.get_failed_items()) == 2

    @pytest.mark.asyncio
    async def test_execute_batch_with_retry_success_first_try(
        self,
        batch_config,
        mock_method_executor,
        sample_document,
        sample_question_context,
    ):
        """Test batch retry logic with success on first try."""
        executor = BatchExecutor(
            config=batch_config, method_executor=mock_method_executor
        )
        mock_executor_instance = MockExecutor(
            mock_method_executor, None, batch_config, None, None
        )

        batch_items = [1, 2]
        result = await executor._execute_batch_with_retry(
            "test_batch_004",
            0,
            batch_items,
            mock_executor_instance,
            sample_document,
            sample_question_context,
        )

        assert result.status == BatchStatus.COMPLETED
        assert result.metrics["retries_used"] == 0

    @pytest.mark.asyncio
    async def test_execute_batch_with_retry_exhausted(
        self, mock_method_executor, sample_document, sample_question_context
    ):
        """Test batch retry logic with retries exhausted."""
        config = BatchExecutorConfig(max_retries=1, enable_instrumentation=False)
        executor = BatchExecutor(config=config, method_executor=mock_method_executor)
        mock_executor_instance = FailingExecutor(
            mock_method_executor, None, config, None, None
        )

        batch_items = [1, 2]
        result = await executor._execute_batch_with_retry(
            "test_batch_005",
            0,
            batch_items,
            mock_executor_instance,
            sample_document,
            sample_question_context,
        )

        assert result.status == BatchStatus.FAILED
        assert result.metrics["retries_used"] == 1


class TestStreamingBatchExecution:
    """Test streaming batch execution."""

    @pytest.mark.asyncio
    async def test_execute_batches_streaming(
        self,
        batch_config,
        mock_method_executor,
        sample_document,
        sample_question_context,
    ):
        """Test streaming batch execution."""
        executor = BatchExecutor(
            config=batch_config, method_executor=mock_method_executor
        )

        items = list(range(25))
        batch_results = []

        async for batch_result in executor.execute_batches(
            items, MockExecutor, sample_document, sample_question_context, batch_size=10
        ):
            batch_results.append(batch_result)

        assert len(batch_results) == 3
        assert batch_results[0].batch_index == 0
        assert batch_results[1].batch_index == 1
        assert batch_results[2].batch_index == 2
        assert all(br.status == BatchStatus.COMPLETED for br in batch_results)

    @pytest.mark.asyncio
    async def test_execute_batches_with_base_slot(
        self,
        batch_config,
        mock_method_executor,
        sample_document,
        sample_question_context,
    ):
        """Test batch execution with base slot for complexity-based sizing."""
        executor = BatchExecutor(
            config=batch_config, method_executor=mock_method_executor
        )

        items = list(range(30))
        batch_results = []

        async for batch_result in executor.execute_batches(
            items,
            MockExecutor,
            sample_document,
            sample_question_context,
            base_slot="D3-Q2",
        ):
            batch_results.append(batch_result)

        assert len(batch_results) == 6

    @pytest.mark.asyncio
    async def test_execute_batches_empty_items(
        self,
        batch_config,
        mock_method_executor,
        sample_document,
        sample_question_context,
    ):
        """Test batch execution with empty items list."""
        executor = BatchExecutor(
            config=batch_config, method_executor=mock_method_executor
        )

        batch_results = []
        async for batch_result in executor.execute_batches(
            [], MockExecutor, sample_document, sample_question_context
        ):
            batch_results.append(batch_result)

        assert len(batch_results) == 0


class TestParallelBatchExecution:
    """Test parallel batch execution."""

    @pytest.mark.asyncio
    async def test_execute_batches_parallel(
        self,
        batch_config,
        mock_method_executor,
        sample_document,
        sample_question_context,
    ):
        """Test parallel batch execution."""
        executor = BatchExecutor(
            config=batch_config, method_executor=mock_method_executor
        )

        items = list(range(40))
        batch_results = await executor.execute_batches_parallel(
            items,
            MockExecutor,
            sample_document,
            sample_question_context,
            batch_size=10,
            max_concurrent_batches=2,
        )

        assert len(batch_results) == 4
        assert all(br.status == BatchStatus.COMPLETED for br in batch_results)
        assert sum(br.metrics["successful_items"] for br in batch_results) == 40

    @pytest.mark.asyncio
    async def test_execute_batches_parallel_with_failures(
        self,
        batch_config,
        mock_method_executor,
        sample_document,
        sample_question_context,
    ):
        """Test parallel batch execution with some failures."""
        executor = BatchExecutor(
            config=batch_config, method_executor=mock_method_executor
        )

        items = list(range(20))
        batch_results = await executor.execute_batches_parallel(
            items,
            PartialFailExecutor,
            sample_document,
            sample_question_context,
            batch_size=10,
            max_concurrent_batches=2,
        )

        assert len(batch_results) == 2
        successful_total = sum(br.metrics["successful_items"] for br in batch_results)
        failed_total = sum(br.metrics["failed_items"] for br in batch_results)
        assert successful_total == 10
        assert failed_total == 10


class TestBatchAggregation:
    """Test batch result aggregation."""

    @pytest.mark.asyncio
    async def test_aggregate_batch_results(self, batch_config, mock_method_executor):
        """Test aggregation of batch results."""
        executor = BatchExecutor(
            config=batch_config, method_executor=mock_method_executor
        )

        batch_results = [
            BatchResult(
                batch_id="batch_001",
                batch_index=0,
                items=[1, 2, 3],
                results=[{"a": 1}, {"a": 2}, {"a": 3}],
                status=BatchStatus.COMPLETED,
                metrics={
                    "batch_id": "batch_001",
                    "batch_index": 0,
                    "batch_size": 3,
                    "status": BatchStatus.COMPLETED,
                    "start_time": 0.0,
                    "end_time": 1.0,
                    "execution_time_ms": 1000.0,
                    "successful_items": 3,
                    "failed_items": 0,
                    "retries_used": 0,
                    "error_messages": [],
                },
            ),
            BatchResult(
                batch_id="batch_002",
                batch_index=1,
                items=[4, 5],
                results=[{"a": 4}, None],
                status=BatchStatus.PARTIAL_SUCCESS,
                metrics={
                    "batch_id": "batch_002",
                    "batch_index": 1,
                    "batch_size": 2,
                    "status": BatchStatus.PARTIAL_SUCCESS,
                    "start_time": 1.0,
                    "end_time": 2.0,
                    "execution_time_ms": 1000.0,
                    "successful_items": 1,
                    "failed_items": 1,
                    "retries_used": 1,
                    "error_messages": ["error"],
                },
                errors=[{"error": "test"}],
            ),
        ]

        aggregated = await executor.aggregate_batch_results(batch_results)

        assert aggregated.total_batches == 2
        assert aggregated.total_items == 5
        assert aggregated.successful_items == 4
        assert aggregated.failed_items == 1
        assert len(aggregated.results) == 4
        assert len(aggregated.errors) == 1
        assert aggregated.success_rate() == 0.8

    @pytest.mark.asyncio
    async def test_aggregate_empty_results(self, batch_config, mock_method_executor):
        """Test aggregation with no results."""
        executor = BatchExecutor(
            config=batch_config, method_executor=mock_method_executor
        )

        aggregated = await executor.aggregate_batch_results([])

        assert aggregated.total_batches == 0
        assert aggregated.total_items == 0
        assert aggregated.success_rate() == 0.0

    @pytest.mark.asyncio
    async def test_stream_aggregate_batches(
        self,
        batch_config,
        mock_method_executor,
        sample_document,
        sample_question_context,
    ):
        """Test streaming aggregation of batch results."""
        executor = BatchExecutor(
            config=batch_config, method_executor=mock_method_executor
        )

        items = list(range(15))

        def accumulator_fn(acc, result):
            """Accumulate call counts."""
            call_count = result.get("call_count", 0)
            if "total_calls" not in acc:
                acc["total_calls"] = 0
            acc["total_calls"] += call_count
            return acc

        batch_stream = executor.execute_batches(
            items, MockExecutor, sample_document, sample_question_context, batch_size=5
        )

        final = await executor.stream_aggregate_batches(batch_stream, accumulator_fn)

        assert final is not None
        assert "total_calls" in final


class TestBatchResultHelpers:
    """Test BatchResult helper methods."""

    def test_is_successful(self):
        """Test is_successful helper."""
        result = BatchResult(
            batch_id="test",
            batch_index=0,
            items=[1, 2],
            results=[{"a": 1}, {"a": 2}],
            status=BatchStatus.COMPLETED,
            metrics={
                "batch_id": "test",
                "batch_index": 0,
                "batch_size": 2,
                "status": BatchStatus.COMPLETED,
                "start_time": 0.0,
                "end_time": 1.0,
                "execution_time_ms": 1000.0,
                "successful_items": 2,
                "failed_items": 0,
                "retries_used": 0,
                "error_messages": [],
            },
        )
        assert result.is_successful() is True

    def test_has_partial_success(self):
        """Test has_partial_success helper."""
        result = BatchResult(
            batch_id="test",
            batch_index=0,
            items=[1, 2],
            results=[{"a": 1}, None],
            status=BatchStatus.PARTIAL_SUCCESS,
            metrics={
                "batch_id": "test",
                "batch_index": 0,
                "batch_size": 2,
                "status": BatchStatus.PARTIAL_SUCCESS,
                "start_time": 0.0,
                "end_time": 1.0,
                "execution_time_ms": 1000.0,
                "successful_items": 1,
                "failed_items": 1,
                "retries_used": 0,
                "error_messages": ["error"],
            },
        )
        assert result.has_partial_success() is True

    def test_get_successful_results(self):
        """Test get_successful_results helper."""
        result = BatchResult(
            batch_id="test",
            batch_index=0,
            items=[1, 2, 3],
            results=[{"a": 1}, None, {"a": 3}],
            status=BatchStatus.PARTIAL_SUCCESS,
            metrics={
                "batch_id": "test",
                "batch_index": 0,
                "batch_size": 3,
                "status": BatchStatus.PARTIAL_SUCCESS,
                "start_time": 0.0,
                "end_time": 1.0,
                "execution_time_ms": 1000.0,
                "successful_items": 2,
                "failed_items": 1,
                "retries_used": 0,
                "error_messages": ["error"],
            },
        )
        successful = result.get_successful_results()
        assert len(successful) == 2
        assert successful[0] == (1, {"a": 1})
        assert successful[1] == (3, {"a": 3})

    def test_get_failed_items(self):
        """Test get_failed_items helper."""
        result = BatchResult(
            batch_id="test",
            batch_index=0,
            items=[1, 2, 3],
            results=[{"a": 1}, None, {"a": 3}],
            status=BatchStatus.PARTIAL_SUCCESS,
            metrics={
                "batch_id": "test",
                "batch_index": 0,
                "batch_size": 3,
                "status": BatchStatus.PARTIAL_SUCCESS,
                "start_time": 0.0,
                "end_time": 1.0,
                "execution_time_ms": 1000.0,
                "successful_items": 2,
                "failed_items": 1,
                "retries_used": 0,
                "error_messages": ["error"],
            },
        )
        failed = result.get_failed_items()
        assert len(failed) == 1
        assert failed[0] == 2


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_execute_batches_single_item(
        self,
        batch_config,
        mock_method_executor,
        sample_document,
        sample_question_context,
    ):
        """Test batch execution with single item."""
        executor = BatchExecutor(
            config=batch_config, method_executor=mock_method_executor
        )

        items = [1]
        batch_results = []

        async for batch_result in executor.execute_batches(
            items, MockExecutor, sample_document, sample_question_context, batch_size=10
        ):
            batch_results.append(batch_result)

        assert len(batch_results) == 1
        assert batch_results[0].metrics["batch_size"] == 1

    @pytest.mark.asyncio
    async def test_batch_counter_increments(
        self,
        batch_config,
        mock_method_executor,
        sample_document,
        sample_question_context,
    ):
        """Test that batch counter increments properly."""
        executor = BatchExecutor(
            config=batch_config, method_executor=mock_method_executor
        )

        items = list(range(15))
        batch_results = []

        async for batch_result in executor.execute_batches(
            items, MockExecutor, sample_document, sample_question_context, batch_size=5
        ):
            batch_results.append(batch_result)

        assert executor._batch_counter == 3
        assert batch_results[0].batch_id == "batch_000001"
        assert batch_results[1].batch_id == "batch_000002"
        assert batch_results[2].batch_id == "batch_000003"

    def test_aggregated_results_success_rate_zero_items(self):
        """Test success rate calculation with zero items."""
        aggregated = AggregatedBatchResults(
            total_batches=0,
            total_items=0,
            successful_items=0,
            failed_items=0,
            results=[],
            errors=[],
            execution_time_ms=0.0,
            batch_metrics=[],
        )
        assert aggregated.success_rate() == 0.0
