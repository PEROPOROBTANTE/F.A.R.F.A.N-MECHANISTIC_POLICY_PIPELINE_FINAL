import pytest
from farfan_pipeline.core.orchestrator.chunk_router import ChunkRouter, ChunkRoute
from farfan_pipeline.core.types import ChunkData, Provenance


@pytest.fixture
def chunk_router():
    return ChunkRouter()


def test_routing_contract_execution_map(chunk_router):
    """
    Verifies that the ChunkRouter generates a deterministic ExecutionMap
    that correctly assigns chunks to their primary executors.
    """
    # Create test chunks
    chunks = [
        ChunkData(
            id=101,
            text="Diagnostic analysis of gap...",
            chunk_type="diagnostic",
            sentences=[1, 2],
            tables=[],
            start_pos=0,
            end_pos=100,
            confidence=0.95,
            policy_area_id="PA05",
            dimension_id="DIM01",
        ),
        ChunkData(
            id=102,
            text="Activity implementation details...",
            chunk_type="activity",
            sentences=[3, 4],
            tables=[],
            start_pos=101,
            end_pos=200,
            confidence=0.92,
            policy_area_id="PA05",
            dimension_id="DIM02",
        ),
        ChunkData(
            id=103,
            text="Unknown type chunk...",
            chunk_type="unknown_type",
            sentences=[5],
            tables=[],
            start_pos=201,
            end_pos=300,
            confidence=0.5,
        ),
    ]

    # Generate Execution Map
    execution_map = chunk_router.generate_execution_map(chunks)

    # Assertions
    assert len(execution_map) == 3

    # Check Chunk 101 (Diagnostic) -> Should go to D1Q1 (first in diagnostic list)
    route_101 = execution_map[101]
    assert route_101.chunk_id == 101
    assert route_101.chunk_type == "diagnostic"
    assert route_101.executor_class == "D1Q1"
    assert route_101.skip_reason is None

    # Check Chunk 102 (Activity) -> Should go to D2Q1 (first in activity list)
    route_102 = execution_map[102]
    assert route_102.chunk_id == 102
    assert route_102.chunk_type == "activity"
    assert route_102.executor_class == "D2Q1"
    assert route_102.skip_reason is None

    # Check Chunk 103 (Unknown) -> Should have no executor and a skip reason
    route_103 = execution_map[103]
    assert route_103.chunk_id == 103
    assert route_103.executor_class == ""
    assert "No executor mapping" in route_103.skip_reason


def test_routing_determinism(chunk_router):
    """
    Verifies that the ExecutionMap generation is deterministic regardless of input order.
    """
    chunk1 = ChunkData(
        id=1,
        text="A",
        chunk_type="diagnostic",
        sentences=[],
        tables=[],
        start_pos=0,
        end_pos=1,
        confidence=1.0,
    )
    chunk2 = ChunkData(
        id=2,
        text="B",
        chunk_type="activity",
        sentences=[],
        tables=[],
        start_pos=0,
        end_pos=1,
        confidence=1.0,
    )

    # Order 1
    map1 = chunk_router.generate_execution_map([chunk1, chunk2])

    # Order 2
    map2 = chunk_router.generate_execution_map([chunk2, chunk1])

    # Keys should be identical
    assert list(map1.keys()) == list(map2.keys())

    # Values should be identical
    assert map1[1] == map2[1]
    assert map1[2] == map2[2]
