"""
SPC to TeoriaCambio Bridge - Causal Graph Construction.

This module bridges Smart Policy Chunks (SPC) chunk graphs to causal DAG
representations for integration with TeoriaCambio (Theory of Change) analysis.
"""

from __future__ import annotations

import logging
from typing import Any

from farfan_pipeline.core.calibration.decorators import calibrated_method
from farfan_pipeline.core.parameters import ParameterLoaderV2

try:
    import networkx as nx

    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    nx = None  # type: ignore

try:
    from farfan_pipeline.processing.models import CanonPolicyPackage, ChunkGraph

    HAS_CPP_MODELS = True
except ImportError:
    HAS_CPP_MODELS = False
    CanonPolicyPackage = None  # type: ignore
    ChunkGraph = None  # type: ignore

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
        "sequential": 0.3,  # Weak temporal causality (A then B)
        "hierarchical": 0.7,  # Strong structural causality (A contains/governs B)
        "reference": 0.5,  # Medium evidential causality (A references B)
        "dependency": 0.9,  # Strong logical causality (A requires B)
    }

    def __init__(self) -> None:
        """Initialize the SPC causal bridge."""
        if not HAS_NETWORKX:
            logger.warning(
                "NetworkX not available. SPCCausalBridge will have limited functionality. "
                "Install networkx for full causal graph construction."
            )
        if not HAS_CPP_MODELS:
            logger.warning(
                "CPP models not available. build_causal_graph_from_cpp will have limited functionality."
            )

    @calibrated_method(
        "farfan_core.analysis.spc_causal_bridge.SPCCausalBridge.build_causal_graph_from_cpp"
    )
    def build_causal_graph_from_cpp(self, cpp: Any) -> Any:
        """
        Convert CanonPolicyPackage to causal DAG via chunk_graph extraction.

        This method serves as the Phase 1-2 adapter integration point, enabling
        D4/D6 executors to perform Theory of Change analysis on the rich
        semantic structure preserved in CanonPolicyPackage.

        Args:
            cpp: CanonPolicyPackage from Phase 1 ingestion

        Returns:
            NetworkX DiGraph representing causal relationships, or None if NetworkX unavailable

        Raises:
            ValueError: If cpp is invalid or missing chunk_graph
            ImportError: If required models not available
        """
        if not HAS_NETWORKX:
            logger.error("NetworkX required for causal graph construction")
            return None

        if not HAS_CPP_MODELS:
            logger.error("CPP models not available for processing")
            return None

        if not cpp:
            raise ValueError("cpp (CanonPolicyPackage) cannot be None or empty")

        if not hasattr(cpp, "chunk_graph") or not cpp.chunk_graph:
            raise ValueError(
                "CanonPolicyPackage must have a valid chunk_graph attribute. "
                "Ensure Phase 1 ingestion completed successfully."
            )

        chunk_graph = cpp.chunk_graph

        if not isinstance(chunk_graph, ChunkGraph):
            raise ValueError(
                f"Expected ChunkGraph instance, got {type(chunk_graph).__name__}"
            )

        if not chunk_graph.chunks:
            logger.warning("ChunkGraph has no chunks, returning empty causal graph")
            return nx.DiGraph()

        logger.info(
            f"Extracting causal graph from CanonPolicyPackage: "
            f"{len(chunk_graph.chunks)} chunks, {len(chunk_graph.edges)} edges"
        )

        chunk_graph_dict = self._convert_chunk_graph_to_dict(chunk_graph)

        causal_graph = self.build_causal_graph_from_spc(chunk_graph_dict)

        if causal_graph is not None:
            self._enhance_graph_with_cpp_metadata(causal_graph, cpp)

        return causal_graph

    @calibrated_method(
        "farfan_core.analysis.spc_causal_bridge.SPCCausalBridge._convert_chunk_graph_to_dict"
    )
    def _convert_chunk_graph_to_dict(self, chunk_graph: Any) -> dict:
        """
        Convert ChunkGraph object to dictionary format for SPC processing.

        Extracts nodes and edges from the ChunkGraph dataclass structure
        and converts them to the dictionary format expected by build_causal_graph_from_spc.

        Args:
            chunk_graph: ChunkGraph instance from CanonPolicyPackage

        Returns:
            Dictionary with 'nodes' and 'edges' keys containing graph structure
        """
        nodes = []
        for chunk_id, chunk in chunk_graph.chunks.items():
            node = {
                "id": chunk_id,
                "type": (
                    getattr(chunk, "resolution", "MESO").name
                    if hasattr(getattr(chunk, "resolution", None), "name")
                    else "MESO"
                ),
                "text": getattr(chunk, "text", "")[:200],
                "confidence": getattr(
                    getattr(chunk, "confidence", None), "layout", 1.0
                ),
            }

            if hasattr(chunk, "policy_area_id") and chunk.policy_area_id:
                node["policy_area_id"] = chunk.policy_area_id
            if hasattr(chunk, "dimension_id") and chunk.dimension_id:
                node["dimension_id"] = chunk.dimension_id

            nodes.append(node)

        edges = []
        for edge_tuple in chunk_graph.edges:
            if len(edge_tuple) >= 3:
                source, target, relation_type = (
                    edge_tuple[0],
                    edge_tuple[1],
                    edge_tuple[2],
                )
            elif len(edge_tuple) == 2:
                source, target = edge_tuple[0], edge_tuple[1]
                relation_type = "sequential"
            else:
                logger.warning(f"Malformed edge tuple: {edge_tuple}, skipping")
                continue

            edges.append(
                {
                    "source": source,
                    "target": target,
                    "type": self._normalize_edge_type(relation_type),
                }
            )

        logger.debug(f"Converted ChunkGraph: {len(nodes)} nodes, {len(edges)} edges")

        return {"nodes": nodes, "edges": edges}

    @calibrated_method(
        "farfan_core.analysis.spc_causal_bridge.SPCCausalBridge._normalize_edge_type"
    )
    def _normalize_edge_type(self, relation_type: str) -> str:
        """
        Normalize edge relation types to causal weights mapping.

        Args:
            relation_type: Original relation type from ChunkGraph

        Returns:
            Normalized edge type compatible with CAUSAL_WEIGHTS
        """
        relation_lower = str(relation_type).lower().strip()

        if relation_lower in self.CAUSAL_WEIGHTS:
            return relation_lower

        type_mapping = {
            "seq": "sequential",
            "sequence": "sequential",
            "hier": "hierarchical",
            "hierarchy": "hierarchical",
            "parent": "hierarchical",
            "child": "hierarchical",
            "ref": "reference",
            "cite": "reference",
            "citation": "reference",
            "dep": "dependency",
            "require": "dependency",
            "requires": "dependency",
            "prerequisite": "dependency",
        }

        return type_mapping.get(relation_lower, "sequential")

    @calibrated_method(
        "farfan_core.analysis.spc_causal_bridge.SPCCausalBridge._enhance_graph_with_cpp_metadata"
    )
    def _enhance_graph_with_cpp_metadata(self, G: Any, cpp: Any) -> None:
        """
        Enhance causal graph with CanonPolicyPackage metadata.

        Enriches nodes with quality metrics, policy manifest data, and provenance
        information from the CPP, enabling richer Theory of Change analysis.

        Args:
            G: NetworkX DiGraph to enhance
            cpp: CanonPolicyPackage with metadata
        """
        if not HAS_NETWORKX or G is None:
            return

        G.graph["schema_version"] = getattr(cpp, "schema_version", "unknown")

        if hasattr(cpp, "quality_metrics") and cpp.quality_metrics:
            qm = cpp.quality_metrics
            G.graph["quality_metrics"] = {
                "provenance_completeness": getattr(qm, "provenance_completeness", 0.0),
                "structural_consistency": getattr(qm, "structural_consistency", 0.0),
                "boundary_f1": getattr(qm, "boundary_f1", 0.0),
                "kpi_linkage_rate": getattr(qm, "kpi_linkage_rate", 0.0),
                "budget_consistency_score": getattr(
                    qm, "budget_consistency_score", 0.0
                ),
            }

        if hasattr(cpp, "policy_manifest") and cpp.policy_manifest:
            pm = cpp.policy_manifest
            G.graph["policy_manifest"] = {
                "axes": getattr(pm, "axes", []),
                "programs": getattr(pm, "programs", []),
                "projects": getattr(pm, "projects", []),
                "years": getattr(pm, "years", []),
                "territories": getattr(pm, "territories", []),
            }

        logger.debug(
            f"Enhanced causal graph with CPP metadata: {len(G.graph)} graph attributes"
        )

    @calibrated_method(
        "farfan_core.analysis.spc_causal_bridge.SPCCausalBridge.build_causal_graph_from_spc"
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
                confidence=node.get(
                    "confidence",
                    ParameterLoaderV2.get(
                        "farfan_core.analysis.spc_causal_bridge.SPCCausalBridge.build_causal_graph_from_spc",
                        "auto_param_L91_50",
                        0.0,
                    ),
                ),
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
            if (
                isinstance(source, str)
                and not source.startswith("chunk_")
                or isinstance(source, int)
            ):
                source_id = f"chunk_{source}"
            else:
                source_id = str(source)

            if (
                isinstance(target, str)
                and not target.startswith("chunk_")
                or isinstance(target, int)
            ):
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

    @calibrated_method(
        "farfan_core.analysis.spc_causal_bridge.SPCCausalBridge._compute_causal_weight"
    )
    def _compute_causal_weight(self, edge_type: str) -> float:
        """
        Map SPC edge type to causal weight.

        Args:
            edge_type: Type of edge from SPC graph

        Returns:
            Causal weight between ParameterLoaderV2.get("farfan_core.analysis.spc_causal_bridge.SPCCausalBridge._compute_causal_weight", "auto_param_L149_34", 0.0) and ParameterLoaderV2.get("farfan_core.analysis.spc_causal_bridge.SPCCausalBridge._compute_causal_weight", "auto_param_L149_42", 1.0)
        """
        return self.CAUSAL_WEIGHTS.get(
            edge_type,
            ParameterLoaderV2.get(
                "farfan_core.analysis.spc_causal_bridge.SPCCausalBridge._compute_causal_weight",
                "auto_param_L151_50",
                0.0,
            ),
        )

    @calibrated_method(
        "farfan_core.analysis.spc_causal_bridge.SPCCausalBridge._remove_cycles"
    )
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
                min_weight = float("inf")
                min_edge = None

                for u, v, direction in cycle:
                    if direction == "forward":
                        weight = G_dag[u][v].get(
                            "weight",
                            ParameterLoaderV2.get(
                                "farfan_core.analysis.spc_causal_bridge.SPCCausalBridge._remove_cycles",
                                "auto_param_L184_59",
                                0.0,
                            ),
                        )
                        if weight < min_weight:
                            min_weight = weight
                            min_edge = (u, v)

                # Remove the edge
                if min_edge:
                    logger.info(
                        f"Removing edge {min_edge} (weight={min_weight}) to break cycle"
                    )
                    G_dag.remove_edge(*min_edge)
                else:
                    # Shouldn't happen, but break to avoid infinite loop
                    logger.error("Could not find edge to remove from cycle")
                    break

            except nx.NetworkXNoCycle:
                # No more cycles
                break

        return G_dag

    @calibrated_method(
        "farfan_core.analysis.spc_causal_bridge.SPCCausalBridge.enhance_graph_with_content"
    )
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

        _ = chunks  # Future enhancement: Add content-based edges using chunks
        return G
