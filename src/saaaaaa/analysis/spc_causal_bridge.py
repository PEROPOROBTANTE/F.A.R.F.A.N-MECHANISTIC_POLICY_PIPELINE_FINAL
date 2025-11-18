"""
SPC to TeoriaCambio Bridge - Causal Graph Construction.

This module bridges Smart Policy Chunks (SPC) chunk graphs to causal DAG
representations for integration with TeoriaCambio (Theory of Change) analysis.
"""

from __future__ import annotations

import logging
from typing import Any

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    nx = None  # type: ignore

logger = logging.getLogger(__name__)


class SPCCausalBridge:
    """
    Converts SPC chunk graph to causal DAG for Theory of Change analysis.

    This bridge enables causal analysis by mapping semantic chunk relationships
    (sequential, hierarchical, reference, dependency) to causal weights that
    can be used by downstream causal inference methods.
    """

    # Mapping of SPC edge types to causal weights
    # Higher weight = stronger causal relationship
    CAUSAL_WEIGHTS: dict[str, float] = {
        "sequential": 0.3,     # Weak temporal causality (A then B)
        "hierarchical": 0.7,   # Strong structural causality (A contains/governs B)
        "reference": 0.5,      # Medium evidential causality (A references B)
        "dependency": 0.9,     # Strong logical causality (A requires B)
    }

    def __init__(self) -> None:
        """Initialize the SPC causal bridge."""
        if not HAS_NETWORKX:
            logger.warning(
                "NetworkX not available. SPCCausalBridge will have limited functionality. "
                "Install networkx for full causal graph construction."
            )

    def build_causal_graph_from_spc(self, chunk_graph: dict) -> Any:
        """
        Convert SPC chunk graph to causal DAG.

        Args:
            chunk_graph: Dictionary with 'nodes' and 'edges' from chunk graph

        Returns:
            NetworkX DiGraph representing causal relationships, or None if NetworkX unavailable

        Raises:
            ValueError: If chunk_graph is invalid
        """
        if not HAS_NETWORKX:
            logger.error("NetworkX required for causal graph construction")
            return None

        if not chunk_graph or not isinstance(chunk_graph, dict):
            raise ValueError("chunk_graph must be a non-empty dictionary")

        nodes = chunk_graph.get("nodes", [])
        edges = chunk_graph.get("edges", [])

        if not nodes:
            logger.warning("No nodes in chunk graph, returning empty graph")
            return nx.DiGraph()

        # Create directed graph
        G = nx.DiGraph()

        # Add nodes with attributes
        for node in nodes:
            node_id = node.get("id")
            if node_id is None:
                continue

            G.add_node(
                f"chunk_{node_id}",
                chunk_type=node.get("type", "unknown"),
                text_summary=node.get("text", "")[:100],  # First 100 chars
                confidence=node.get("confidence", 0.0),
            )

        # Add edges with causal interpretation
        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            edge_type = edge.get("type", "sequential")

            if source is None or target is None:
                continue

            # Convert to node IDs
            # Handle both string and integer IDs
            if isinstance(source, str) and not source.startswith("chunk_") or isinstance(source, int):
                source_id = f"chunk_{source}"
            else:
                source_id = str(source)

            if isinstance(target, str) and not target.startswith("chunk_") or isinstance(target, int):
                target_id = f"chunk_{target}"
            else:
                target_id = str(target)

            # Compute causal weight
            weight = self._compute_causal_weight(edge_type)

            if weight > 0:  # Only add edges with positive causal weight
                G.add_edge(
                    source_id,
                    target_id,
                    weight=weight,
                    edge_type=edge_type,
                    original_type=edge_type,
                )

        # Validate and clean graph
        if not nx.is_directed_acyclic_graph(G):
            logger.warning("Graph contains cycles, attempting to remove cycles")
            G = self._remove_cycles(G)

        logger.info(
            f"Built causal graph: {G.number_of_nodes()} nodes, "
            f"{G.number_of_edges()} edges, "
            f"is_dag={nx.is_directed_acyclic_graph(G)}"
        )

        return G

    def _compute_causal_weight(self, edge_type: str) -> float:
        """
        Map SPC edge type to causal weight.

        Args:
            edge_type: Type of edge from SPC graph

        Returns:
            Causal weight between 0.0 and 1.0
        """
        return self.CAUSAL_WEIGHTS.get(edge_type, 0.0)

    def _remove_cycles(self, G: Any) -> Any:
        """
        Remove cycles from graph to create a DAG.

        Uses a simple strategy: remove edges with lowest weight until acyclic.

        Args:
            G: NetworkX DiGraph

        Returns:
            Modified graph (DAG)
        """
        if not HAS_NETWORKX:
            return G

        # Make a copy to avoid modifying original
        G_dag = G.copy()

        # Find cycles and remove lowest-weight edges
        while not nx.is_directed_acyclic_graph(G_dag):
            try:
                # Find a cycle
                cycle = nx.find_cycle(G_dag, orientation="original")

                # Find edge in cycle with minimum weight
                min_weight = float('inf')
                min_edge = None

                for u, v, direction in cycle:
                    if direction == "forward":
                        weight = G_dag[u][v].get("weight", 0.0)
                        if weight < min_weight:
                            min_weight = weight
                            min_edge = (u, v)

                # Remove the edge
                if min_edge:
                    logger.info(f"Removing edge {min_edge} (weight={min_weight}) to break cycle")
                    G_dag.remove_edge(*min_edge)
                else:
                    # Shouldn't happen, but break to avoid infinite loop
                    logger.error("Could not find edge to remove from cycle")
                    break

            except nx.NetworkXNoCycle:
                # No more cycles
                break

        return G_dag

    def enhance_graph_with_content(self, G: Any, chunks: list) -> Any:
        """
        Enhance causal graph with content-based relationships.

        This method can add additional edges based on content similarity,
        shared entities, or other semantic relationships.

        Args:
            G: NetworkX DiGraph (causal graph)
            chunks: List of ChunkData objects

        Returns:
            Enhanced graph
        """
        if not HAS_NETWORKX or G is None:
            return G

        # Future enhancement: Add content-based edges
        # For now, just return the graph as-is
        return G
