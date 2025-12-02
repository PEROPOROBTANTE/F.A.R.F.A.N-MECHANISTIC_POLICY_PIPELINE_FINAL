"""
Chunk Router for SPC Exploitation.

Routes semantic chunks to appropriate executors based on chunk type,
enabling targeted execution and reducing redundant processing.
"""

# Routing table version identifier
ROUTING_TABLE_VERSION = "v1"

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .core import ChunkData


@dataclass
class ChunkRoute:
    """Routing decision for a single chunk."""
    chunk_id: int
    chunk_type: str
    executor_class: str
    methods: list[tuple[str, str]]  # [(class_name, method_name), ...]
    skip_reason: str | None = None


class ChunkRouter:
    """
    Routes chunks to appropriate executors based on semantic type.

    This enables chunk-aware execution, where different chunk types
    are processed by the most relevant executors, avoiding unnecessary
    full-document processing.
    """

    # TYPE-TO-EXECUTOR MAPPING
    # Maps chunk types to executor base slots (e.g., "D1Q1", "D2Q3")
    ROUTING_TABLE: dict[str, list[str]] = {
        "diagnostic": ["D1Q1", "D1Q2", "D1Q5"],  # Baseline/gap analysis executors
        "activity": ["D2Q1", "D2Q2", "D2Q3", "D2Q4", "D2Q5"],  # Activity/intervention executors
        "indicator": ["D3Q1", "D3Q2", "D4Q1", "D5Q1"],  # Metric/indicator executors
        "resource": ["D1Q3", "D2Q4", "D5Q5"],  # Financial/resource executors
        "temporal": ["D1Q5", "D3Q4", "D5Q4"],  # Timeline/temporal executors
        "entity": ["D2Q3", "D3Q3"],  # Responsibility/entity executors
    }

    # METHODS THAT MUST SEE FULL GRAPH
    # These methods require access to the complete chunk graph
    GRAPH_METHODS: set[str] = {
        "TeoriaCambio.construir_grafo_causal",
        "CausalExtractor.extract_causal_hierarchy",
        "AdvancedDAGValidator.calculate_acyclicity_pvalue",
        "CrossReferenceValidator.validate_internal_consistency",
    }

    def route_chunk(self, chunk: ChunkData) -> ChunkRoute:
        """
        Determine executor routing for a chunk.

        Args:
            chunk: ChunkData to route

        Returns:
            ChunkRoute with executor assignment and method list
        """
        executor_classes = self.ROUTING_TABLE.get(chunk.chunk_type, [])

        if not executor_classes:
            return ChunkRoute(
                chunk_id=chunk.id,
                chunk_type=chunk.chunk_type,
                executor_class="",
                methods=[],
                skip_reason=f"No executor mapping for chunk type '{chunk.chunk_type}'"
            )

        # Get primary executor for this chunk type
        primary_executor = executor_classes[0]

        # Get method subset for this chunk type
        # Note: Actual method filtering would require loading executor configs
        # For now, we return empty list and let execute_chunk filter
        methods: list[tuple[str, str]] = []

        return ChunkRoute(
            chunk_id=chunk.id,
            chunk_type=chunk.chunk_type,
            executor_class=primary_executor,
            methods=methods,
        )

    def should_use_full_graph(self, method_name: str, class_name: str = "") -> bool:
        """
        Check if a method requires access to the full chunk graph.

        Args:
            method_name: Name of the method
            class_name: Optional class name

        Returns:
            True if method needs full graph access
        """
        full_name = f"{class_name}.{method_name}" if class_name else method_name
        return full_name in self.GRAPH_METHODS or method_name in self.GRAPH_METHODS

    def get_relevant_executors(self, chunk_type: str) -> list[str]:
        """
        Get list of executors relevant to a chunk type.

        Args:
            chunk_type: Type of chunk

        Returns:
            List of executor base slots
        """
        return self.ROUTING_TABLE.get(chunk_type, [])

    def generate_execution_map(self, chunks: list[ChunkData]) -> dict[int, ChunkRoute]:
        """
        Generate a deterministic execution map for a list of chunks.

        This map serves as the binding contract for the Orchestrator,
        dictating exactly which executor processes which chunk.

        Args:
            chunks: List of ChunkData objects

        Returns:
            Dictionary mapping chunk_id to ChunkRoute
        """
        execution_map = {}
        # Sort chunks by ID to ensure deterministic processing order if relevant,
        # though the output dict key order is insertion-ordered in modern Python.
        # We process them in order to be safe.
        sorted_chunks = sorted(chunks, key=lambda c: c.id)

        for chunk in sorted_chunks:
            route = self.route_chunk(chunk)
            execution_map[chunk.id] = route

        return execution_map
