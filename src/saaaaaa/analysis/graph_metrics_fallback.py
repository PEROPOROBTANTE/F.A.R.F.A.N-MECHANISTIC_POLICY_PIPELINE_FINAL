"""
Graph metrics computation with NetworkX fallback handling.

This module provides graph metrics computation with graceful degradation
when NetworkX is unavailable. It integrates with the runtime configuration
system to emit proper observability signals.
"""

import logging
from typing import Any, Optional

from saaaaaa.core.runtime_config import RuntimeConfig, get_runtime_config
from saaaaaa.core.contracts.runtime_contracts import (
    GraphMetricsInfo,
    FallbackCategory,
)
from saaaaaa.core.observability.structured_logging import log_fallback
from saaaaaa.core.observability.metrics import increment_graph_metrics_skipped

logger = logging.getLogger(__name__)


def check_networkx_available() -> bool:
    """
    Check if NetworkX is available for graph metrics computation.
    
    Returns:
        True if NetworkX is available, False otherwise
    """
    try:
        import networkx
        return True
    except ImportError:
        return False


def compute_graph_metrics_with_fallback(
    graph_data: Any,
    runtime_config: Optional[RuntimeConfig] = None,
    document_id: Optional[str] = None,
) -> tuple[dict[str, Any], GraphMetricsInfo]:
    """
    Compute graph metrics with NetworkX fallback handling.
    
    Args:
        graph_data: Graph data structure (e.g., edge list, adjacency matrix)
        runtime_config: Optional runtime configuration (uses global if None)
        document_id: Optional document identifier for logging
        
    Returns:
        Tuple of (metrics_dict, GraphMetricsInfo manifest)
        
    Example:
        >>> metrics, info = compute_graph_metrics_with_fallback(edge_list)
        >>> if info.computed:
        ...     print(f"Centrality: {metrics['centrality']}")
        ... else:
        ...     print(f"Skipped: {info.reason}")
    """
    if runtime_config is None:
        runtime_config = get_runtime_config()
    
    networkx_available = check_networkx_available()
    
    if networkx_available:
        try:
            import networkx as nx
            
            # Convert graph_data to NetworkX graph
            # This is a placeholder - actual implementation depends on graph_data format
            if isinstance(graph_data, list):
                # Assume edge list format: [(source, target), ...]
                G = nx.Graph()
                G.add_edges_from(graph_data)
            elif isinstance(graph_data, dict):
                # Assume adjacency dict format
                G = nx.from_dict_of_lists(graph_data)
            else:
                raise ValueError(f"Unsupported graph_data type: {type(graph_data)}")
            
            # Compute graph metrics
            metrics = {
                'num_nodes': G.number_of_nodes(),
                'num_edges': G.number_of_edges(),
                'density': nx.density(G),
                'avg_clustering': nx.average_clustering(G) if G.number_of_nodes() > 0 else 0.0,
                'num_components': nx.number_connected_components(G),
            }
            
            # Compute centrality if graph is not too large
            if G.number_of_nodes() < 1000:
                metrics['degree_centrality'] = nx.degree_centrality(G)
                metrics['betweenness_centrality'] = nx.betweenness_centrality(G)
            
            logger.info(f"Graph metrics computed: {metrics['num_nodes']} nodes, {metrics['num_edges']} edges")
            
            graph_info = GraphMetricsInfo(
                computed=True,
                networkx_available=True,
                reason=None
            )
            
            return metrics, graph_info
            
        except Exception as e:
            # NetworkX available but computation failed
            logger.error(f"Graph metrics computation failed: {e}")
            
            reason = f"NetworkX computation error: {str(e)}"
            graph_info = GraphMetricsInfo(
                computed=False,
                networkx_available=True,
                reason=reason
            )
            
            # Emit structured log and metrics (Category B: Quality degradation)
            log_fallback(
                component='graph_metrics',
                subsystem='analysis',
                fallback_category=FallbackCategory.B,
                fallback_mode='computation_error',
                reason=reason,
                runtime_mode=runtime_config.mode,
                document_id=document_id,
            )
            
            increment_graph_metrics_skipped(
                reason='computation_error',
                runtime_mode=runtime_config.mode,
            )
            
            # Return empty metrics
            return {}, graph_info
    
    else:
        # NetworkX not available - graceful degradation
        reason = "NetworkX not available - graph metrics skipped"
        logger.warning(reason)
        
        graph_info = GraphMetricsInfo(
            computed=False,
            networkx_available=False,
            reason=reason
        )
        
        # Emit structured log and metrics (Category B: Quality degradation)
        log_fallback(
            component='graph_metrics',
            subsystem='analysis',
            fallback_category=FallbackCategory.B,
            fallback_mode='networkx_unavailable',
            reason=reason,
            runtime_mode=runtime_config.mode,
            document_id=document_id,
        )
        
        increment_graph_metrics_skipped(
            reason='networkx_unavailable',
            runtime_mode=runtime_config.mode,
        )
        
        # Return empty metrics
        return {}, graph_info


def compute_basic_graph_stats(graph_data: Any) -> dict[str, Any]:
    """
    Compute basic graph statistics without NetworkX.
    
    This is a lightweight fallback that computes basic stats
    without requiring NetworkX.
    
    Args:
        graph_data: Graph data (edge list or adjacency dict)
        
    Returns:
        Dictionary with basic graph statistics
    """
    if isinstance(graph_data, list):
        # Edge list format
        nodes = set()
        for edge in graph_data:
            if len(edge) >= 2:
                nodes.add(edge[0])
                nodes.add(edge[1])
        
        return {
            'num_nodes': len(nodes),
            'num_edges': len(graph_data),
            'method': 'basic_stats_no_networkx'
        }
    
    elif isinstance(graph_data, dict):
        # Adjacency dict format
        num_edges = sum(len(neighbors) for neighbors in graph_data.values())
        
        return {
            'num_nodes': len(graph_data),
            'num_edges': num_edges // 2,  # Undirected graph
            'method': 'basic_stats_no_networkx'
        }
    
    else:
        return {
            'num_nodes': 0,
            'num_edges': 0,
            'method': 'unknown_format'
        }
