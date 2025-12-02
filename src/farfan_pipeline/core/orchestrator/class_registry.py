"""Dynamic class registry for orchestrator method execution."""
from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

class ClassRegistryError(RuntimeError):
    """Raised when one or more classes cannot be loaded."""

# Map of orchestrator-facing class names to their import paths.
_CLASS_PATHS: Mapping[str, str] = {
    "IndustrialPolicyProcessor": "farfan_core.processing.policy_processor.IndustrialPolicyProcessor",
    "PolicyTextProcessor": "farfan_core.processing.policy_processor.PolicyTextProcessor",
    "BayesianEvidenceScorer": "farfan_core.processing.policy_processor.BayesianEvidenceScorer",
    "PolicyContradictionDetector": "farfan_core.analysis.contradiction_deteccion.PolicyContradictionDetector",
    "TemporalLogicVerifier": "farfan_core.analysis.contradiction_deteccion.TemporalLogicVerifier",
    "BayesianConfidenceCalculator": "farfan_core.analysis.contradiction_deteccion.BayesianConfidenceCalculator",
    "PDETMunicipalPlanAnalyzer": "farfan_core.analysis.financiero_viabilidad_tablas.PDETMunicipalPlanAnalyzer",
    "CDAFFramework": "farfan_core.analysis.derek_beach.CDAFFramework",
    "CausalExtractor": "farfan_core.analysis.derek_beach.CausalExtractor",
    "OperationalizationAuditor": "farfan_core.analysis.derek_beach.OperationalizationAuditor",
    "FinancialAuditor": "farfan_core.analysis.derek_beach.FinancialAuditor",
    "BayesianMechanismInference": "farfan_core.analysis.derek_beach.BayesianMechanismInference",
    "BayesianNumericalAnalyzer": "farfan_core.processing.embedding_policy.BayesianNumericalAnalyzer",
    "PolicyAnalysisEmbedder": "farfan_core.processing.embedding_policy.PolicyAnalysisEmbedder",
    "AdvancedSemanticChunker": "farfan_core.processing.embedding_policy.AdvancedSemanticChunker",
    # SemanticChunker is an alias maintained for backwards compatibility.
    "SemanticChunker": "farfan_core.processing.embedding_policy.AdvancedSemanticChunker",
    "SemanticAnalyzer": "farfan_core.analysis.Analyzer_one.SemanticAnalyzer",
    "PerformanceAnalyzer": "farfan_core.analysis.Analyzer_one.PerformanceAnalyzer",
    "TextMiningEngine": "farfan_core.analysis.Analyzer_one.TextMiningEngine",
    "MunicipalOntology": "farfan_core.analysis.Analyzer_one.MunicipalOntology",
    "TeoriaCambio": "farfan_core.analysis.teoria_cambio.TeoriaCambio",
    "AdvancedDAGValidator": "farfan_core.analysis.teoria_cambio.AdvancedDAGValidator",
    "D1_Q1_QuantitativeBaselineExtractor": "farfan_core.core.orchestrator.executors.D1_Q1_QuantitativeBaselineExtractor",
    "D1_Q2_ProblemDimensioningAnalyzer": "farfan_core.core.orchestrator.executors.D1_Q2_ProblemDimensioningAnalyzer",
    "SemanticProcessor": "farfan_core.processing.semantic_chunking_policy.SemanticProcessor",
    "BayesianCounterfactualAuditor": "farfan_core.analysis.derek_beach.BayesianCounterfactualAuditor",
}

def build_class_registry() -> dict[str, type[object]]:
    """Return a mapping of class names to loaded types, validating availability.

    Classes that depend on optional dependencies (e.g., torch) are skipped
    gracefully if those dependencies are not available.
    """
    resolved: dict[str, type[object]] = {}
    missing: dict[str, str] = {}
    skipped_optional: dict[str, str] = {}

    for name, path in _CLASS_PATHS.items():
        module_name, _, class_name = path.rpartition(".")
        if not module_name:
            missing[name] = path
            continue
        try:
            module = import_module(module_name)
        except ImportError as exc:
            exc_str = str(exc)
            # Check if this is an optional dependency error
            optional_deps = [
                "torch", "tensorflow", "pyarrow", "camelot",
                "sentence_transformers", "transformers", "spacy",
                "pymc", "arviz", "dowhy", "econml"
            ]
            if any(opt_dep in exc_str for opt_dep in optional_deps):
                # Mark as skipped optional rather than missing
                skipped_optional[name] = f"{path} (optional dependency: {exc})"
            else:
                missing[name] = f"{path} (import error: {exc})"
            continue
        try:
            attr = getattr(module, class_name)
        except AttributeError:
            missing[name] = f"{path} (attribute missing)"
        else:
            if not isinstance(attr, type):
                missing[name] = f"{path} (attribute is not a class: {type(attr).__name__})"
            else:
                resolved[name] = attr

    # Log skipped optional dependencies
    if skipped_optional:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(
            f"Skipped {len(skipped_optional)} optional classes due to missing dependencies: "
            f"{', '.join(skipped_optional.keys())}"
        )

    if missing:
        formatted = ", ".join(f"{name}: {reason}" for name, reason in missing.items())
        raise ClassRegistryError(f"Failed to load orchestrator classes: {formatted}")
    return resolved

def get_class_paths() -> Mapping[str, str]:
    """Expose the raw class path mapping for diagnostics."""
    return _CLASS_PATHS
