#!/usr/bin/env python3
"""
Concurrency Integration Demo - How to use WorkerPool in the Orchestrator.

This demo shows how to integrate the new concurrency.WorkerPool with the
existing orchestrator for deterministic parallel execution of micro questions.

Key features demonstrated:
1. Deterministic task execution
2. Controlled max_workers
3. Exponential backoff and retries
4. Per-task instrumentation and logging
5. Graceful abort of pending tasks
6. No race conditions
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType

from saaaaaa.concurrency.concurrency import WorkerPool, WorkerPoolConfig
from schemas.preprocessed_document import DocumentIndexesV1, PreprocessedDocument, StructuredTextV1

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass(frozen=True, slots=True)
class Evidence:
    """Mock evidence result."""

    modality: str
    elements: tuple[str, ...]

def process_micro_question(
    question_num: int,
    _doc: PreprocessedDocument,
    _base_slot: str
) -> Evidence:
    """
    Mock function to process a single micro question.

    In real orchestrator, this would delegate to:
    - Choreographer.process_micro_question()
    - Execute DAG of methods
    - Extract evidence

    Args:
        question_num: Question number (1-300)
        doc: Preprocessed document
        base_slot: Base slot (e.g., "D1-Q1")

    Returns:
        Evidence extracted from question
    """
    # Simulate processing time
    time.sleep(0.01)

    # Simulate some questions failing occasionally
    if question_num % 50 == 0:
        raise ValueError(f"Question {question_num} encountered an error")

    # Return mock evidence
    return Evidence(
        modality="TYPE_A",
        elements=(f"evidence_{question_num}_1", f"evidence_{question_num}_2"),
    )

def orchestrator_with_workerpool_demo():
    """
    Demonstrate how to use WorkerPool in the orchestrator.

    This replaces the ThreadPoolExecutor usage with WorkerPool for:
    - Better control over concurrency
    - Deterministic execution
    - Detailed instrumentation
    - Retry and backoff logic
    - Abortability
    """
    logger.info("=" * 70)
    logger.info("ORCHESTRATOR WITH WORKERPOOL DEMO")
    logger.info("=" * 70)

    # Create preprocessed document (mock payload using the shared DTO)
    doc = PreprocessedDocument(
        document_id="doc_1",
        full_text="mock text",
        sentences=("mock text",),
        language="es",
        structured_text=StructuredTextV1(full_text="mock text"),
        sentence_metadata=(),
        tables=(),
        indexes=DocumentIndexesV1(),
        metadata=MappingProxyType({"source": "demo"}),
        ingested_at=datetime.utcnow(),
    )

    # Configure WorkerPool
    config = WorkerPoolConfig(
        max_workers=50,           # Same as before
        task_timeout_seconds=180, # 3 minutes per task
        max_retries=3,            # Retry failed tasks up to 3 times
        backoff_base_seconds=1.0, # Start with 1s backoff
        backoff_max_seconds=60.0, # Cap backoff at 60s
        enable_instrumentation=True  # Enable detailed logging
    )

    logger.info("Creating WorkerPool with config:")
    logger.info(f"  - max_workers: {config.max_workers}")
    logger.info(f"  - max_retries: {config.max_retries}")
    logger.info(f"  - task_timeout: {config.task_timeout_seconds}s")
    logger.info("")

    # Create WorkerPool
    with WorkerPool(config) as pool:
        start_time = time.time()

        # Submit all 300 micro questions
        logger.info("Submitting 300 micro questions to WorkerPool...")
        task_ids = []

        for q_num in range(1, 301):
            # Map to base slot (same as before)
            base_idx = (q_num - 1) % 30
            base_slot = f"D{base_idx//5+1}-Q{base_idx%5+1}"

            # Submit task to pool
            task_id = pool.submit_task(
                task_name=f"Q{q_num:03d}_{base_slot}",
                task_fn=process_micro_question,
                args=(q_num, doc, base_slot)
            )
            task_ids.append((task_id, q_num, base_slot))

        logger.info(f"Submitted {len(task_ids)} tasks")
        logger.info("")

        # Wait for all tasks to complete
        logger.info("Waiting for all tasks to complete...")
        results = pool.wait_for_all(timeout=600.0)  # 10 minute timeout

        elapsed = time.time() - start_time

        # Process results
        logger.info("")
        logger.info("=" * 70)
        logger.info("RESULTS SUMMARY")
        logger.info("=" * 70)

        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        logger.info(f"Total tasks: {len(results)}")
        logger.info(f"Successful: {len(successful)}")
        logger.info(f"Failed: {len(failed)}")
        logger.info(f"Success rate: {len(successful)/len(results)*100:.1f}%")
        logger.info(f"Total time: {elapsed:.2f}s")
        logger.info("")

        # Get detailed metrics
        summary = pool.get_summary_metrics()
        logger.info("DETAILED METRICS:")
        logger.info(f"  - Completed: {summary['completed']}")
        logger.info(f"  - Failed: {summary['failed']}")
        logger.info(f"  - Cancelled: {summary['cancelled']}")
        logger.info(f"  - Average execution time: {summary['avg_execution_time_ms']:.2f}ms")
        logger.info(f"  - Total retries used: {summary['total_retries']}")
        logger.info("")

        # Show sample of failed tasks
        if failed:
            logger.info("SAMPLE OF FAILED TASKS:")
            for result in failed[:5]:
                logger.info(f"  - {result.task_name}: {result.error}")
            if len(failed) > 5:
                logger.info(f"  ... and {len(failed) - 5} more")
            logger.info("")

        # Return results in orchestrator format
        processed_results = []
        for result in successful:
            # Extract question number from task_id mapping
            q_num = next(
                (q for tid, q, _ in task_ids if tid == result.task_id),
                None
            )
            if q_num:
                processed_results.append((q_num, result.result))

        logger.info("=" * 70)
        logger.info("DEMO COMPLETED SUCCESSFULLY")
        logger.info("=" * 70)

        return {
            'results': processed_results,
            'time': elapsed,
            'metrics': summary
        }

def orchestrator_with_abort_demo():
    """
    Demonstrate abort functionality.

    Shows how to cancel pending tasks if something goes wrong.
    """
    logger.info("=" * 70)
    logger.info("ABORT FUNCTIONALITY DEMO")
    logger.info("=" * 70)

    doc = PreprocessedDocument("doc_1", "mock text")

    config = WorkerPoolConfig(
        max_workers=5,  # Low number to queue up tasks
        task_timeout_seconds=180,
        max_retries=1,
        enable_instrumentation=True
    )

    with WorkerPool(config) as pool:
        # Submit 50 tasks (but only 5 can run at once)
        logger.info("Submitting 50 tasks (max_workers=5)...")
        for q_num in range(1, 51):
            pool.submit_task(
                task_name=f"Q{q_num:03d}",
                task_fn=process_micro_question,
                args=(q_num, doc, "D1-Q1")
            )

        # Let a few start
        time.sleep(0.2)

        # Abort remaining tasks
        logger.info("Aborting pending tasks...")
        cancelled = pool.abort_pending_tasks()
        logger.info(f"Cancelled {cancelled} tasks")

        # Get summary
        summary = pool.get_summary_metrics()
        logger.info("")
        logger.info("FINAL STATE:")
        logger.info(f"  - Completed: {summary['completed']}")
        logger.info(f"  - Failed: {summary['failed']}")
        logger.info(f"  - Cancelled: {summary['cancelled']}")
        logger.info("")

        logger.info("=" * 70)
        logger.info("ABORT DEMO COMPLETED")
        logger.info("=" * 70)

def main():
    """Run all demos."""
    # Demo 1: Normal execution with WorkerPool
    logger.info("")
    result = orchestrator_with_workerpool_demo()
    logger.info(f"Processed {len(result['results'])} questions successfully")
    logger.info("")

    # Demo 2: Abort functionality
    logger.info("")
    orchestrator_with_abort_demo()
    logger.info("")

if __name__ == "__main__":
    main()
