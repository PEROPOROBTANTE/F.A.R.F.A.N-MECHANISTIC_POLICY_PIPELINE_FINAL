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
    "IndustrialPolicyProcessor": "saaaaaa.processing.policy_processor.IndustrialPolicyProcessor",
    "PolicyTextProcessor": "saaaaaa.processing.policy_processor.PolicyTextProcessor",
    "BayesianEvidenceScorer": "saaaaaa.processing.policy_processor.BayesianEvidenceScorer",
    "PolicyContradictionDetector": "saaaaaa.analysis.contradiction_deteccion.PolicyContradictionDetector",
    "TemporalLogicVerifier": "saaaaaa.analysis.contradiction_deteccion.TemporalLogicVerifier",
    "BayesianConfidenceCalculator": "saaaaaa.analysis.contradiction_deteccion.BayesianConfidenceCalculator",
    "PDETMunicipalPlanAnalyzer": "saaaaaa.analysis.financiero_viabilidad_tablas.PDETMunicipalPlanAnalyzer",
    "CDAFFramework": "saaaaaa.analysis.derek_beach.CDAFFramework",
    "CausalExtractor": "saaaaaa.analysis.derek_beach.CausalExtractor",
    "OperationalizationAuditor": "saaaaaa.analysis.derek_beach.OperationalizationAuditor",
    "FinancialAuditor": "saaaaaa.analysis.derek_beach.FinancialAuditor",
    "BayesianMechanismInference": "saaaaaa.analysis.derek_beach.BayesianMechanismInference",
    "BayesianNumericalAnalyzer": "saaaaaa.processing.embedding_policy.BayesianNumericalAnalyzer",
    "PolicyAnalysisEmbedder": "saaaaaa.processing.embedding_policy.PolicyAnalysisEmbedder",
    "AdvancedSemanticChunker": "saaaaaa.processing.embedding_policy.AdvancedSemanticChunker",
    # SemanticChunker is an alias maintained for backwards compatibility.
    "SemanticChunker": "saaaaaa.processing.embedding_policy.AdvancedSemanticChunker",
    "SemanticAnalyzer": "saaaaaa.analysis.Analyzer_one.SemanticAnalyzer",
    "PerformanceAnalyzer": "saaaaaa.analysis.Analyzer_one.PerformanceAnalyzer",
    "TextMiningEngine": "saaaaaa.analysis.Analyzer_one.TextMiningEngine",
    "MunicipalOntology": "saaaaaa.analysis.Analyzer_one.MunicipalOntology",
    "TeoriaCambio": "saaaaaa.analysis.teoria_cambio.TeoriaCambio",
    "AdvancedDAGValidator": "saaaaaa.analysis.teoria_cambio.AdvancedDAGValidator",
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
