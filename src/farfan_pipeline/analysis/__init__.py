"""Analysis modules for semantic and structural analysis.

This module exposes production-ready utilities and meso-level analytics functions
for policy analysis workflows.

Production-Ready Utilities:
---------------------------
- :func:`compute_graph_metrics_with_fallback`: Compute graph metrics with NetworkX
  fallback handling and observability integration
- :func:`compute_basic_graph_stats`: Compute basic graph statistics without NetworkX
- :func:`check_networkx_available`: Check if NetworkX is available for graph computation
- :class:`RetryHandler`: Robust retry mechanism for transient dependency failures
- :class:`SPCCausalBridge`: Convert SPC chunk graphs to causal DAG representations

Meso-Level Analytics:
---------------------
- :func:`analyze_policy_dispersion`: Evaluate intra-cluster dispersion with CV, gap
  analysis, and light penalty framework
- :func:`reconcile_cross_metrics`: Validate heterogeneous metric feeds against
  authoritative macro reference with governance flags
- :func:`compose_cluster_posterior`: Aggregate micro posteriors using Bayesian-style
  roll-up with reconciliation penalties
- :func:`calibrate_against_peers`: Situate cluster against peer group using
  inter-quartile comparisons and Tukey-style outlier detection

Experimental Components:
-----------------------
The following classes are under active development and should be considered
experimental. They are not exposed in the public API but remain available
for research and development purposes:

- :class:`BayesianMultilevelSystem`: Multi-level Bayesian analysis framework
  (from bayesian_multilevel_system.py)
- :class:`ContradictionDetector`: Transformer-based contradiction detection
  (from contradiction_deteccion.py)
- :class:`DerekBeachCausalFramework`: Process tracing causal analysis
  (from derek_beach.py)
- :class:`TeoriaCambio`: Theory of change validation framework
  (from teoria_cambio.py)

These experimental components may have unstable APIs, incomplete documentation,
or require additional dependencies not enforced by the core system.
"""

from farfan_pipeline.analysis.graph_metrics_fallback import (
    check_networkx_available,
    compute_basic_graph_stats,
    compute_graph_metrics_with_fallback,
)
from farfan_pipeline.analysis.meso_cluster_analysis import (
    analyze_policy_dispersion,
    calibrate_against_peers,
    compose_cluster_posterior,
    reconcile_cross_metrics,
)
from farfan_pipeline.analysis.retry_handler import RetryHandler
from farfan_pipeline.analysis.spc_causal_bridge import SPCCausalBridge

__all__ = [
    "compute_graph_metrics_with_fallback",
    "compute_basic_graph_stats",
    "check_networkx_available",
    "RetryHandler",
    "SPCCausalBridge",
    "analyze_policy_dispersion",
    "reconcile_cross_metrics",
    "compose_cluster_posterior",
    "calibrate_against_peers",
]
