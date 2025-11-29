# macro_prompts.py
"""
Macro Prompts for MACRO-Level Analysis
=======================================

This module implements 5 strategic macro-level analysis prompts:
1. Coverage & Structural Gap Stressor - Evaluates dimensional/cluster coverage
2. Inter-Level Contradiction Scan - Detects micro↔meso↔macro contradictions
3. Bayesian Portfolio Composer - Integrates posteriors into global portfolio
4. Roadmap Optimizer - Generates sequenced 0-3m / 3-6m / 6-12m roadmap
5. Peer Normalization & Confidence Scaling - Adjusts classification vs peers

Author: Integration Team
Version: 1.0.0
Python: 3.10+
"""

import logging
import statistics
from dataclasses import asdict, dataclass, field
from typing import Any

# Import runtime error fixes for defensive programming
from saaaaaa.utils.runtime_error_fixes import ensure_list_return
from saaaaaa import get_parameter_loader
from saaaaaa.core.calibration.decorators import calibrated_method

logger = logging.getLogger(__name__)

# ============================================================================
# DATA STRUCTURES FOR MACRO PROMPTS
# ============================================================================

@dataclass
class CoverageAnalysis:
    """Output from Coverage & Structural Gap Stressor"""
    coverage_index: float  # Weighted average coverage (0.0-1.0)
    degraded_confidence: float | None  # Adjusted confidence if coverage low
    predictive_uplift: dict[str, float]  # Expected improvement if gaps filled
    dimension_coverage: dict[str, float]  # D1-D6 coverage percentages
    policy_area_coverage: dict[str, float]  # P1-P10 coverage percentages
    critical_dimensions_below_threshold: list[str]  # Dimensions needing attention
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ContradictionReport:
    """Output from Inter-Level Contradiction Scan"""
    contradictions: list[dict[str, Any]]  # List of detected contradictions
    suggested_actions: list[dict[str, str]]  # Actions to resolve contradictions
    consistency_score: float  # 0.0-1.0 overall consistency
    micro_meso_alignment: float  # 0.0-1.0 micro↔meso alignment
    meso_macro_alignment: float  # 0.0-1.0 meso↔macro alignment
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class BayesianPortfolio:
    """Output from Bayesian Portfolio Composer"""
    prior_global: float  # Global prior (weighted meso average)
    penalties_applied: dict[str, float]  # Coverage, dispersion, contradiction penalties
    posterior_global: float  # Adjusted global posterior
    var_global: float  # Global variance
    confidence_interval: tuple[float, float]  # 95% CI
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ImplementationRoadmap:
    """Output from Roadmap Optimizer"""
    phases: list[dict[str, Any]]  # 0-3m, 3-6m, 6-12m phases
    total_expected_uplift: float  # Total expected improvement
    critical_path: list[str]  # Critical dependency chain
    resource_requirements: dict[str, Any]  # Estimated resources per phase
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class PeerNormalization:
    """Output from Peer Normalization & Confidence Scaling"""
    z_scores: dict[str, float]  # Z-scores by policy area
    adjusted_confidence: float  # Adjusted confidence based on peer comparison
    peer_position: str  # "above_average", "average", "below_average"
    outlier_areas: list[str]  # Policy areas >2 SD from mean
    metadata: dict[str, Any] = field(default_factory=dict)

# ============================================================================
# MACRO PROMPT 1: COVERAGE & STRUCTURAL GAP STRESSOR
# ============================================================================

class CoverageGapStressor:
    """
    ROLE: Structural Integrity Auditor [systems design]
    GOAL: Evaluar si la ausencia de clusters o dimensiones erosiona la validez del score macro.

    INPUTS:
    - convergence_by_dimension
    - missing_clusters
    - dimension_coverage: {D1..D6: % preguntas respondidas}
    - policy_area_coverage: {P#: %}

    MANDATES:
    - Calcular coverage_index (media ponderada)
    - Si dimension_coverage < τ en alguna dimensión crítica (D3, D6) → degradar global_confidence
    - Simular impacto si se completara el cluster faltante (predictive uplift)

    OUTPUT:
    JSON {coverage_index, degraded_confidence, predictive_uplift}
    """

    def __init__(
        self,
        critical_dimensions: list[str] | None = None,
        dimension_weights: dict[str, float] | None = None,
        coverage_threshold: float = 0.70
    ) -> None:
        """
        Initialize Coverage Gap Stressor

        Args:
            critical_dimensions: List of critical dimensions (default: D3, D6)
            dimension_weights: Weights for each dimension (default: equal)
            coverage_threshold: Minimum acceptable coverage (default: 0.70)
        """
        self.critical_dimensions = critical_dimensions or ["D3", "D6"]
        self.dimension_weights = dimension_weights or {
            f"D{i}": 1.0/6.0 for i in range(1, 7)
        }
        self.coverage_threshold = coverage_threshold
        logger.info(f"CoverageGapStressor initialized with threshold={coverage_threshold}")

    def evaluate(
        self,
        convergence_by_dimension: dict[str, float],
        missing_clusters: list[str],
        dimension_coverage: dict[str, float],
        policy_area_coverage: dict[str, float],
        baseline_confidence: float = 1.0
    ) -> CoverageAnalysis:
        """
        Evaluate coverage and structural gaps

        Args:
            convergence_by_dimension: Convergence scores by dimension
            missing_clusters: List of missing cluster names
            dimension_coverage: Coverage percentage by dimension
            policy_area_coverage: Coverage percentage by policy area
            baseline_confidence: Starting confidence level (0.0-1.0)

        Returns:
            CoverageAnalysis with complete gap assessment
        """
        # Calculate weighted coverage index
        coverage_index = self._calculate_coverage_index(dimension_coverage)

        # Check critical dimensions
        critical_below_threshold = self._identify_critical_gaps(dimension_coverage)

        # Degrade confidence if critical gaps exist
        degraded_confidence = self._degrade_confidence(
            baseline_confidence,
            critical_below_threshold,
            coverage_index
        )

        # Simulate predictive uplift
        predictive_uplift = self._simulate_uplift(
            missing_clusters,
            dimension_coverage,
            convergence_by_dimension
        )

        return CoverageAnalysis(
            coverage_index=coverage_index,
            degraded_confidence=degraded_confidence,
            predictive_uplift=predictive_uplift,
            dimension_coverage=dimension_coverage,
            policy_area_coverage=policy_area_coverage,
            critical_dimensions_below_threshold=critical_below_threshold,
            metadata={
                "missing_clusters": missing_clusters,
                "threshold_used": self.coverage_threshold,
                "critical_dimensions": self.critical_dimensions
            }
        )

    def _calculate_coverage_index(
        self,
        dimension_coverage: dict[str, float]
    ) -> float:
        """Calculate weighted average coverage index"""
        total_weight = 0.0
        weighted_sum = 0.0

        for dim, coverage in dimension_coverage.items():
            weight = self.dimension_weights.get(dim, 0.0)
            weighted_sum += coverage * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        return weighted_sum / total_weight

    def _identify_critical_gaps(
        self,
        dimension_coverage: dict[str, float]
    ) -> list[str]:
        """Identify critical dimensions below threshold"""
        critical_gaps = []

        for dim in self.critical_dimensions:
            if dim in dimension_coverage:
                if dimension_coverage[dim] < self.coverage_threshold:
                    critical_gaps.append(dim)

        return critical_gaps

    def _degrade_confidence(
        self,
        baseline_confidence: float,
        critical_gaps: list[str],
        coverage_index: float
    ) -> float:
        """Degrade confidence based on structural gaps"""
        degraded = baseline_confidence

        # Penalty for each critical gap
        for _ in critical_gaps:
            degraded *= 0.85  # 15% penalty per critical gap

        # Additional penalty if overall coverage is low
        if coverage_index < self.coverage_threshold:
            gap_severity = (self.coverage_threshold - coverage_index) / self.coverage_threshold
            degraded *= (1.0 - gap_severity * 0.3)  # Up to 30% additional penalty

        return max(0.0, min(1.0, degraded))

    def _simulate_uplift(
        self,
        missing_clusters: list[str],
        dimension_coverage: dict[str, float],
        convergence_by_dimension: dict[str, float]
    ) -> dict[str, float]:
        """Simulate impact if missing clusters were completed"""
        uplift = {}

        # Estimate uplift for each missing cluster
        for cluster in missing_clusters:
            # Assume cluster completion would improve coverage by 10-20%
            estimated_improvement = 0.15
            uplift[cluster] = estimated_improvement

        # Estimate dimension-level uplift
        for dim, coverage in dimension_coverage.items():
            if coverage < 1.0:
                gap = 1.0 - coverage
                convergence = convergence_by_dimension.get(dim, 0.5)
                # Higher convergence suggests more potential uplift
                potential_uplift = gap * convergence * 0.7
                uplift[f"{dim}_completion"] = potential_uplift

        return uplift

# ============================================================================
# MACRO PROMPT 2: INTER-LEVEL CONTRADICTION SCAN
# ============================================================================

class ContradictionScanner:
    """
    ROLE: Consistency Inspector [data governance]
    GOAL: Detectar contradicciones micro↔meso↔macro.

    INPUTS:
    - micro_claims (extraído de MicroLevelAnswer.evidence)
    - meso_summary_signals
    - macro_narratives (borrador)

    MANDATES:
    - Alinear claims por entidad/tema/dimensión
    - Marcar contradicción si macro afirma X y ≥k micro niegan X con posterior ≥ θ
    - Sugerir corrección: "rephrase / downgrade confidence / request re-execution"

    OUTPUT:
    JSON {contradictions[], suggested_actions}
    """

    def __init__(
        self,
        contradiction_threshold: int = 3,
        posterior_threshold: float = 0.7
    ) -> None:
        """
        Initialize Contradiction Scanner

        Args:
            contradiction_threshold: Min number of micro claims to flag contradiction
            posterior_threshold: Min posterior confidence to consider claim valid
        """
        self.k = contradiction_threshold
        self.theta = posterior_threshold
        logger.info(f"ContradictionScanner initialized (k={self.k}, θ={self.theta})")

    def scan(
        self,
        micro_claims: list[dict[str, Any]],
        meso_summary_signals: dict[str, Any],
        macro_narratives: dict[str, Any]
    ) -> ContradictionReport:
        """
        Scan for contradictions across levels

        Args:
            micro_claims: List of micro-level claims with evidence
            meso_summary_signals: Meso-level summary signals
            macro_narratives: Macro-level narrative statements

        Returns:
            ContradictionReport with detected issues and suggested actions
        """
        # Align claims by entity/theme/dimension
        aligned_claims = self._align_claims(micro_claims, meso_summary_signals, macro_narratives)

        # Detect contradictions (defensive: ensure returns list)
        contradictions = ensure_list_return(self._detect_contradictions(aligned_claims))

        # Generate suggested actions
        suggested_actions = self._generate_actions(contradictions)

        # Calculate consistency scores
        consistency_score = self._calculate_consistency(contradictions, len(micro_claims))
        micro_meso_alignment = self._calculate_alignment(micro_claims, meso_summary_signals)
        meso_macro_alignment = self._calculate_alignment(
            [meso_summary_signals],
            macro_narratives
        )

        return ContradictionReport(
            contradictions=contradictions,
            suggested_actions=suggested_actions,
            consistency_score=consistency_score,
            micro_meso_alignment=micro_meso_alignment,
            meso_macro_alignment=meso_macro_alignment,
            metadata={
                "total_micro_claims": len(micro_claims),
                "contradiction_threshold": self.k,
                "posterior_threshold": self.theta
            }
        )

    def _align_claims(
        self,
        micro_claims: list[dict[str, Any]],
        meso_summary_signals: dict[str, Any],
        macro_narratives: dict[str, Any]
    ) -> dict[str, dict[str, list[Any]]]:
        """Align claims by entity/theme/dimension"""
        aligned = {
            "micro": {},
            "meso": {},
            "macro": {}
        }

        # Group micro claims by dimension
        for claim in micro_claims:
            dimension = claim.get("dimension", "unknown")
            if dimension not in aligned["micro"]:
                aligned["micro"][dimension] = []
            aligned["micro"][dimension].append(claim)

        # Group meso signals by dimension
        for key, value in meso_summary_signals.items():
            if key.startswith("D") and len(key) == 2:
                aligned["meso"][key] = value

        # Group macro narratives
        aligned["macro"] = macro_narratives

        return aligned

    def _detect_contradictions(
        self,
        aligned_claims: dict[str, dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Detect contradictions across levels"""
        contradictions = []

        # Check each dimension/theme
        for dimension in aligned_claims.get("micro", {}):
            micro_claims = aligned_claims["micro"].get(dimension, [])
            aligned_claims["meso"].get(dimension, {})
            macro_narrative = aligned_claims["macro"].get(dimension, {})

            # Count claims that contradict macro narrative
            contradicting_claims = []
            for claim in micro_claims:
                if self._is_contradictory(claim, macro_narrative):
                    posterior = claim.get("posterior", 0.0)
                    if posterior >= self.theta:
                        contradicting_claims.append(claim)

            # Flag if threshold exceeded
            if len(contradicting_claims) >= self.k:
                contradictions.append({
                    "dimension": dimension,
                    "type": "micro_macro_contradiction",
                    "contradicting_claims": len(contradicting_claims),
                    "threshold": self.k,
                    "details": contradicting_claims[:5]  # Sample
                })

        return contradictions

    def _is_contradictory(
        self,
        claim: dict[str, Any],
        narrative: dict[str, Any]
    ) -> bool:
        """Check if claim contradicts narrative"""
        # Simple heuristic: if claim score is low but narrative is positive
        claim_score = claim.get("score", 0.0)
        narrative_score = narrative.get("score", 0.5)

        # Contradiction if scores differ significantly
        return abs(claim_score - narrative_score) > 0.4

    def _generate_actions(
        self,
        contradictions: list[dict[str, Any]]
    ) -> list[dict[str, str]]:
        """Generate suggested actions to resolve contradictions"""
        actions = []

        for contradiction in contradictions:
            dimension = contradiction.get("dimension", "unknown")
            count = contradiction.get("contradicting_claims", 0)

            if count >= self.k * 2:
                actions.append({
                    "dimension": dimension,
                    "action": "request_re_execution",
                    "reason": f"{count} micro claims contradict macro narrative"
                })
            elif count >= self.k:
                actions.append({
                    "dimension": dimension,
                    "action": "downgrade_confidence",
                    "reason": f"{count} micro claims suggest lower confidence"
                })
            else:
                actions.append({
                    "dimension": dimension,
                    "action": "rephrase_narrative",
                    "reason": "Minor inconsistencies detected"
                })

        return actions

    def _calculate_consistency(
        self,
        contradictions: list[dict[str, Any]],
        total_claims: int
    ) -> float:
        """Calculate overall consistency score"""
        if total_claims == 0:
            return 1.0

        total_contradictions = sum(
            c.get("contradicting_claims", 0) for c in contradictions
        )

        consistency = 1.0 - (total_contradictions / max(total_claims, 1))
        return max(0.0, min(1.0, consistency))

    def _calculate_alignment(
        self,
        level1_data: Any,
        level2_data: Any
    ) -> float:
        """Calculate alignment between two levels"""
        # Simplified alignment calculation
        # In production, would use semantic similarity, score correlation, etc.
        return 0.85  # Placeholder

# ============================================================================
# MACRO PROMPT 3: BAYESIAN PORTFOLIO COMPOSER
# ============================================================================

class BayesianPortfolioComposer:
    """
    ROLE: Global Bayesian Integrator [causal inference]
    GOAL: Integrar todas las posteriors (micro y meso) en una cartera causal global.

    INPUTS:
    - meso_posteriors
    - weighting_trace (cluster_weights)
    - macro_reconciliation_penalties

    MANDATES:
    - Calcular prior_global (media ponderada meso)
    - Aplicar penalties jerárquicos (coverage, dispersion estructural, contradictions)
    - Recalcular posterior_global y varianza

    OUTPUT:
    JSON {prior_global, penalties_applied, posterior_global, var_global}
    """

    def __init__(
        self,
        default_variance: float = 0.05
    ) -> None:
        """
        Initialize Bayesian Portfolio Composer

        Args:
            default_variance: Default variance for uncertain estimates
        """
        self.default_variance = default_variance
        logger.info("BayesianPortfolioComposer initialized")

    def compose(
        self,
        meso_posteriors: dict[str, float],
        cluster_weights: dict[str, float],
        reconciliation_penalties: dict[str, float] | None = None
    ) -> BayesianPortfolio:
        """
        Compose global Bayesian portfolio from meso posteriors

        Args:
            meso_posteriors: Posterior probabilities by cluster/dimension
            cluster_weights: Weights for each cluster
            reconciliation_penalties: Optional penalties (coverage, dispersion, contradictions)

        Returns:
            BayesianPortfolio with integrated global estimate
        """
        # Calculate weighted prior
        prior_global = self._calculate_weighted_prior(meso_posteriors, cluster_weights)

        # Apply hierarchical penalties
        penalties = reconciliation_penalties or {}
        penalties_applied = self._apply_penalties(prior_global, penalties)

        # Calculate posterior and variance
        posterior_global = self._calculate_posterior(prior_global, penalties_applied)
        var_global = self._calculate_variance(meso_posteriors, cluster_weights, penalties_applied)

        # Calculate 95% confidence interval
        ci = self._calculate_confidence_interval(posterior_global, var_global)

        return BayesianPortfolio(
            prior_global=prior_global,
            penalties_applied=penalties_applied,
            posterior_global=posterior_global,
            var_global=var_global,
            confidence_interval=ci,
            metadata={
                "num_clusters": len(meso_posteriors),
                "total_weight": sum(cluster_weights.values())
            }
        )

    def _calculate_weighted_prior(
        self,
        meso_posteriors: dict[str, float],
        cluster_weights: dict[str, float]
    ) -> float:
        """Calculate weighted prior from meso posteriors"""
        total_weight = sum(cluster_weights.values())
        if total_weight == 0:
            return 0.5  # Neutral prior

        weighted_sum = 0.0
        for cluster, posterior in meso_posteriors.items():
            weight = cluster_weights.get(cluster, 0.0)
            weighted_sum += posterior * weight

        return weighted_sum / total_weight

    def _apply_penalties(
        self,
        prior: float,
        penalties: dict[str, float]
    ) -> dict[str, float]:
        """Apply hierarchical penalties"""
        applied = {}

        # Coverage penalty
        coverage_penalty = penalties.get("coverage", 0.0)
        applied["coverage"] = coverage_penalty

        # Structural dispersion penalty
        dispersion_penalty = penalties.get("dispersion", 0.0)
        applied["dispersion"] = dispersion_penalty

        # Contradiction penalty
        contradiction_penalty = penalties.get("contradictions", 0.0)
        applied["contradictions"] = contradiction_penalty

        return applied

    def _calculate_posterior(
        self,
        prior: float,
        penalties: dict[str, float]
    ) -> float:
        """Calculate posterior after applying penalties"""
        posterior = prior

        # Apply each penalty multiplicatively
        for _penalty_name, penalty_value in penalties.items():
            posterior *= (1.0 - penalty_value)

        return max(0.0, min(1.0, posterior))

    def _calculate_variance(
        self,
        meso_posteriors: dict[str, float],
        cluster_weights: dict[str, float],
        penalties: dict[str, float]
    ) -> float:
        """Calculate global variance"""
        if len(meso_posteriors) < 2:
            return self.default_variance

        # Calculate weighted variance
        mean = self._calculate_weighted_prior(meso_posteriors, cluster_weights)
        total_weight = sum(cluster_weights.values())

        if total_weight == 0:
            return self.default_variance

        weighted_sq_diff = 0.0
        for cluster, posterior in meso_posteriors.items():
            weight = cluster_weights.get(cluster, 0.0)
            sq_diff = (posterior - mean) ** 2
            weighted_sq_diff += weight * sq_diff

        variance = weighted_sq_diff / total_weight

        # Increase variance based on penalties
        penalty_factor = 1.0 + sum(penalties.values())
        adjusted_variance = variance * penalty_factor

        return adjusted_variance

    def _calculate_confidence_interval(
        self,
        posterior: float,
        variance: float,
        confidence: float = 0.95
    ) -> tuple[float, float]:
        """Calculate confidence interval (assumes normal distribution)"""
        # For 95% CI, z-score ≈ 1.96
        z_score = 1.96
        margin = z_score * (variance ** 0.5)

        lower = max(0.0, posterior - margin)
        upper = min(1.0, posterior + margin)

        return (lower, upper)

# ============================================================================
# MACRO PROMPT 4: ROADMAP OPTIMIZER
# ============================================================================

class RoadmapOptimizer:
    """
    ROLE: Execution Strategist [operations design]
    GOAL: Generar roadmap secuenciado 0–3m / 3–6m / 6–12m priorizando impacto/costo.

    INPUTS:
    - critical_gaps (list)
    - dependency_graph (gaps con prerequisitos)
    - effort_estimates
    - impact_scores

    MANDATES:
    - Ordenar por ratio impact/effort y dependencias
    - Asignar ventana temporal mínima sin colisión de prerequisitos
    - Estimar uplift esperado por tramo

    OUTPUT:
    JSON roadmap {phase, actions[], expected_uplift}
    """

    def __init__(self) -> None:
        """Initialize Roadmap Optimizer"""
        logger.info("RoadmapOptimizer initialized")

    def optimize(
        self,
        critical_gaps: list[dict[str, Any]],
        dependency_graph: dict[str, list[str]],
        effort_estimates: dict[str, float],
        impact_scores: dict[str, float]
    ) -> ImplementationRoadmap:
        """
        Generate optimized implementation roadmap

        Args:
            critical_gaps: List of gaps to address
            dependency_graph: Gap ID -> list of prerequisite gap IDs
            effort_estimates: Gap ID -> effort estimate (person-months)
            impact_scores: Gap ID -> expected impact (get_parameter_loader().get("saaaaaa.analysis.macro_prompts.RoadmapOptimizer.__init__").get("auto_param_L702_54", 0.0)-get_parameter_loader().get("saaaaaa.analysis.macro_prompts.RoadmapOptimizer.__init__").get("auto_param_L702_58", 1.0))

        Returns:
            ImplementationRoadmap with phased action plan
        """
        # Calculate impact/effort ratios
        prioritized_gaps = self._prioritize_gaps(
            critical_gaps,
            effort_estimates,
            impact_scores
        )

        # Assign to time windows respecting dependencies
        phases = self._assign_phases(
            prioritized_gaps,
            dependency_graph,
            effort_estimates
        )

        # Calculate expected uplift per phase
        total_uplift = self._calculate_total_uplift(phases, impact_scores)

        # Identify critical path
        critical_path = self._identify_critical_path(dependency_graph, impact_scores)

        # Estimate resource requirements
        resources = self._estimate_resources(phases, effort_estimates)

        return ImplementationRoadmap(
            phases=phases,
            total_expected_uplift=total_uplift,
            critical_path=critical_path,
            resource_requirements=resources,
            metadata={
                "total_gaps": len(critical_gaps),
                "total_effort": sum(effort_estimates.values())
            }
        )

    def _prioritize_gaps(
        self,
        gaps: list[dict[str, Any]],
        effort_estimates: dict[str, float],
        impact_scores: dict[str, float]
    ) -> list[dict[str, Any]]:
        """Prioritize gaps by impact/effort ratio"""
        prioritized = []

        for gap in gaps:
            gap_id = gap.get("id", "unknown")
            effort = effort_estimates.get(gap_id, get_parameter_loader().get("saaaaaa.analysis.macro_prompts.RoadmapOptimizer.__init__").get("auto_param_L752_50", 1.0))
            impact = impact_scores.get(gap_id, get_parameter_loader().get("saaaaaa.analysis.macro_prompts.RoadmapOptimizer.__init__").get("auto_param_L753_47", 0.5))

            # Calculate ratio (avoid division by zero)
            ratio = impact / max(effort, get_parameter_loader().get("saaaaaa.analysis.macro_prompts.RoadmapOptimizer.__init__").get("auto_param_L756_41", 0.1))

            prioritized.append({
                **gap,
                "priority_ratio": ratio,
                "effort": effort,
                "impact": impact
            })

        # Sort by priority ratio (descending)
        prioritized.sort(key=lambda x: x["priority_ratio"], reverse=True)

        return prioritized

    def _assign_phases(
        self,
        prioritized_gaps: list[dict[str, Any]],
        dependency_graph: dict[str, list[str]],
        effort_estimates: dict[str, float]
    ) -> list[dict[str, Any]]:
        """Assign gaps to time phases respecting dependencies"""
        phases = [
            {"name": "0-3m", "actions": [], "effort": get_parameter_loader().get("saaaaaa.analysis.macro_prompts.RoadmapOptimizer.__init__").get("auto_param_L778_54", 0.0), "max_effort": 9.0},
            {"name": "3-6m", "actions": [], "effort": get_parameter_loader().get("saaaaaa.analysis.macro_prompts.RoadmapOptimizer.__init__").get("auto_param_L779_54", 0.0), "max_effort": 9.0},
            {"name": "6-12m", "actions": [], "effort": get_parameter_loader().get("saaaaaa.analysis.macro_prompts.RoadmapOptimizer.__init__").get("auto_param_L780_55", 0.0), "max_effort": 18.0}
        ]

        assigned = set()
        gap_dict = {gap.get("id"): gap for gap in prioritized_gaps}

        # Process gaps, but assign dependencies first
        def assign_gap_recursive(gap_id: str, visited: set) -> None:
            """Recursively assign gap and its dependencies"""
            if gap_id in assigned or gap_id in visited:
                return

            visited.add(gap_id)

            # First assign dependencies
            dependencies = dependency_graph.get(gap_id, [])
            for dep_id in dependencies:
                if dep_id in gap_dict:
                    assign_gap_recursive(dep_id, visited)

            # Now assign this gap
            if gap_id not in assigned and gap_id in gap_dict:
                gap = gap_dict[gap_id]
                effort = gap.get("effort", get_parameter_loader().get("saaaaaa.analysis.macro_prompts.RoadmapOptimizer.__init__").get("auto_param_L803_43", 1.0))

                # Find earliest phase where all dependencies are satisfied
                earliest_phase = self._get_earliest_phase(dependencies, assigned, phases)

                # Assign to earliest phase with capacity
                for i in range(earliest_phase, len(phases)):
                    if phases[i]["effort"] + effort <= phases[i]["max_effort"]:
                        phases[i]["actions"].append(gap)
                        phases[i]["effort"] += effort
                        assigned.add(gap_id)
                        break

        # Assign gaps in priority order, but respecting dependencies
        for gap in prioritized_gaps:
            gap_id = gap.get("id", "unknown")
            assign_gap_recursive(gap_id, set())

        return phases

    def _get_earliest_phase(
        self,
        dependencies: list[str],
        assigned: set,
        phases: list[dict[str, Any]]
    ) -> int:
        """Get earliest phase where all dependencies are satisfied"""
        if not dependencies:
            return 0

        max_dep_phase = -1
        for dep_id in dependencies:
            # Find which phase the dependency is in
            dep_found = False
            for i, phase in enumerate(phases):
                for action in phase["actions"]:
                    if action.get("id") == dep_id:
                        max_dep_phase = max(max_dep_phase, i)
                        dep_found = True
                        break
                if dep_found:
                    break

        # Return phase after latest dependency (or 0 if no dependencies found yet)
        return min(max_dep_phase + 1, len(phases) - 1) if max_dep_phase >= 0 else 0

    def _calculate_total_uplift(
        self,
        phases: list[dict[str, Any]],
        impact_scores: dict[str, float]
    ) -> float:
        """Calculate total expected uplift across all phases"""
        total = get_parameter_loader().get("saaaaaa.analysis.macro_prompts.RoadmapOptimizer.__init__").get("total", 0.0) # Refactored

        for phase in phases:
            for action in phase["actions"]:
                gap_id = action.get("id", "unknown")
                impact = impact_scores.get(gap_id, get_parameter_loader().get("saaaaaa.analysis.macro_prompts.RoadmapOptimizer.__init__").get("auto_param_L860_51", 0.0))
                total += impact

        return total

    def _identify_critical_path(
        self,
        dependency_graph: dict[str, list[str]],
        impact_scores: dict[str, float]
    ) -> list[str]:
        """Identify critical dependency chain"""
        # Find the path with highest total impact
        # Simple heuristic: find longest chain with high-impact nodes

        # Find nodes with no dependents (endpoints)
        has_dependents = set()
        for deps in dependency_graph.values():
            has_dependents.update(deps)

        endpoints = [
            gap_id for gap_id in dependency_graph
            if gap_id not in has_dependents
        ]

        # For each endpoint, trace back to find highest-impact path
        best_path = []
        best_impact = get_parameter_loader().get("saaaaaa.analysis.macro_prompts.RoadmapOptimizer.__init__").get("best_impact", 0.0) # Refactored

        for endpoint in endpoints:
            path = self._trace_path(endpoint, dependency_graph)
            path_impact = sum(impact_scores.get(gap_id, get_parameter_loader().get("saaaaaa.analysis.macro_prompts.RoadmapOptimizer.__init__").get("auto_param_L890_56", 0.0)) for gap_id in path)

            if path_impact > best_impact:
                best_impact = path_impact
                best_path = path

        return best_path

    def _trace_path(
        self,
        gap_id: str,
        dependency_graph: dict[str, list[str]]
    ) -> list[str]:
        """Trace dependency path from gap to root"""
        path = [gap_id]
        dependencies = dependency_graph.get(gap_id, [])

        if dependencies:
            # Follow first dependency (simplified)
            dep_path = self._trace_path(dependencies[0], dependency_graph)
            path = dep_path + path

        return path

    def _estimate_resources(
        self,
        phases: list[dict[str, Any]],
        effort_estimates: dict[str, float]
    ) -> dict[str, Any]:
        """Estimate resource requirements per phase"""
        resources = {}

        for phase in phases:
            phase_name = phase["name"]
            total_effort = phase["effort"]
            num_actions = len(phase["actions"])

            # Estimate team size (assuming 3 months per person-month per phase)
            phase_months = {"0-3m": 3, "3-6m": 3, "6-12m": 6}
            months = phase_months.get(phase_name, 3)
            team_size = max(1, int(total_effort / months))

            resources[phase_name] = {
                "total_effort_months": total_effort,
                "recommended_team_size": team_size,
                "num_actions": num_actions
            }

        return resources

# ============================================================================
# MACRO PROMPT 5: PEER NORMALIZATION & CONFIDENCE SCALING
# ============================================================================

class PeerNormalizer:
    """
    ROLE: Macro Peer Evaluator [evaluation design]
    GOAL: Ajustar clasificación macro considerando comparativos regionales.

    INPUTS:
    - convergence_by_policy_area
    - peer_distributions: {policy_area -> {mean, std}}
    - baseline_confidence

    MANDATES:
    - Calcular z-scores
    - Penalizar si >k áreas están < -get_parameter_loader().get("saaaaaa.analysis.macro_prompts.RoadmapOptimizer.__init__").get("auto_param_L956_37", 1.0) z
    - Aumentar confianza si todas dentro ±get_parameter_loader().get("saaaaaa.analysis.macro_prompts.RoadmapOptimizer.__init__").get("auto_param_L957_42", 0.5) z y dispersión baja

    OUTPUT:
    JSON {z_scores, adjusted_confidence}
    """

    def __init__(
        self,
        penalty_threshold: int = 3,
        outlier_z_threshold: float = 2.0
    ) -> None:
        """
        Initialize Peer Normalizer

        Args:
            penalty_threshold: Number of low-performing areas to trigger penalty
            outlier_z_threshold: Z-score threshold for outlier identification
        """
        self.k = penalty_threshold
        self.outlier_z = outlier_z_threshold
        logger.info(f"PeerNormalizer initialized (k={self.k}, z_outlier={self.outlier_z})")

    def normalize(
        self,
        convergence_by_policy_area: dict[str, float],
        peer_distributions: dict[str, dict[str, float]],
        baseline_confidence: float
    ) -> PeerNormalization:
        """
        Normalize scores against peer distributions

        Args:
            convergence_by_policy_area: Scores by policy area
            peer_distributions: Mean and std dev for each policy area
            baseline_confidence: Starting confidence level

        Returns:
            PeerNormalization with adjusted confidence
        """
        # Calculate z-scores
        z_scores = self._calculate_z_scores(
            convergence_by_policy_area,
            peer_distributions
        )

        # Identify outliers
        outlier_areas = self._identify_outliers(z_scores)

        # Count low-performing areas
        low_performers = [
            area for area, z in z_scores.items()
            if z < -get_parameter_loader().get("saaaaaa.analysis.macro_prompts.RoadmapOptimizer.__init__").get("auto_param_L1008_20", 1.0)
        ]

        # Adjust confidence
        adjusted_confidence = self._adjust_confidence(
            baseline_confidence,
            z_scores,
            low_performers
        )

        # Determine peer position
        peer_position = self._determine_position(z_scores)

        return PeerNormalization(
            z_scores=z_scores,
            adjusted_confidence=adjusted_confidence,
            peer_position=peer_position,
            outlier_areas=outlier_areas,
            metadata={
                "num_policy_areas": len(convergence_by_policy_area),
                "low_performers": len(low_performers),
                "penalty_threshold": self.k
            }
        )

    def _calculate_z_scores(
        self,
        convergence: dict[str, float],
        peer_distributions: dict[str, dict[str, float]]
    ) -> dict[str, float]:
        """Calculate z-scores for each policy area"""
        z_scores = {}

        for area, score in convergence.items():
            if area in peer_distributions:
                peer = peer_distributions[area]
                mean = peer.get("mean", get_parameter_loader().get("saaaaaa.analysis.macro_prompts.RoadmapOptimizer.__init__").get("auto_param_L1044_40", 0.5))
                std = peer.get("std", get_parameter_loader().get("saaaaaa.analysis.macro_prompts.RoadmapOptimizer.__init__").get("auto_param_L1045_38", 0.1))

                # Calculate z-score
                z = (score - mean) / std if std > 0 else get_parameter_loader().get("saaaaaa.analysis.macro_prompts.RoadmapOptimizer.__init__").get("auto_param_L1048_57", 0.0)

                z_scores[area] = z

        return z_scores

    def _identify_outliers(
        self,
        z_scores: dict[str, float]
    ) -> list[str]:
        """Identify outlier policy areas"""
        outliers = []

        for area, z in z_scores.items():
            if abs(z) > self.outlier_z:
                outliers.append(area)

        return outliers

    def _adjust_confidence(
        self,
        baseline: float,
        z_scores: dict[str, float],
        low_performers: list[str]
    ) -> float:
        """Adjust confidence based on peer comparison"""
        adjusted = baseline

        # Penalize if too many low performers
        if len(low_performers) > self.k:
            penalty = get_parameter_loader().get("saaaaaa.analysis.macro_prompts.RoadmapOptimizer.__init__").get("auto_param_L1078_22", 0.1) * (len(low_performers) - self.k)
            adjusted *= (get_parameter_loader().get("saaaaaa.analysis.macro_prompts.RoadmapOptimizer.__init__").get("auto_param_L1079_25", 1.0) - min(penalty, get_parameter_loader().get("saaaaaa.analysis.macro_prompts.RoadmapOptimizer.__init__").get("auto_param_L1079_44", 0.5)))

        # Check if all within ±get_parameter_loader().get("saaaaaa.analysis.macro_prompts.RoadmapOptimizer.__init__").get("auto_param_L1081_31", 0.5) z (tight distribution)
        all_tight = all(abs(z) <= get_parameter_loader().get("saaaaaa.analysis.macro_prompts.RoadmapOptimizer.__init__").get("auto_param_L1082_34", 0.5) for z in z_scores.values())

        if all_tight and len(z_scores) > 0:
            # Increase confidence for consistent performance
            adjusted *= 1.1

        return max(get_parameter_loader().get("saaaaaa.analysis.macro_prompts.RoadmapOptimizer.__init__").get("auto_param_L1088_19", 0.0), min(get_parameter_loader().get("saaaaaa.analysis.macro_prompts.RoadmapOptimizer.__init__").get("auto_param_L1088_28", 1.0), adjusted))

    def _determine_position(
        self,
        z_scores: dict[str, float]
    ) -> str:
        """Determine overall peer position"""
        if not z_scores:
            return "average"

        avg_z = statistics.mean(z_scores.values())

        if avg_z > get_parameter_loader().get("saaaaaa.analysis.macro_prompts.RoadmapOptimizer.__init__").get("auto_param_L1100_19", 0.5):
            return "above_average"
        elif avg_z < -get_parameter_loader().get("saaaaaa.analysis.macro_prompts.RoadmapOptimizer.__init__").get("auto_param_L1102_22", 0.5):
            return "below_average"
        else:
            return "average"

# ============================================================================
# MACRO PROMPTS FACADE
# ============================================================================

class MacroPromptsOrchestrator:
    """
    Orchestrator for all 5 macro-level analysis prompts

    Provides unified interface to execute all macro analyses
    """

    def __init__(self) -> None:
        """Initialize all macro prompt components"""
        self.coverage_stressor = CoverageGapStressor()
        self.contradiction_scanner = ContradictionScanner()
        self.portfolio_composer = BayesianPortfolioComposer()
        self.roadmap_optimizer = RoadmapOptimizer()
        self.peer_normalizer = PeerNormalizer()

        logger.info("MacroPromptsOrchestrator initialized with all 5 components")

    def execute_all(
        self,
        macro_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Execute all 5 macro analyses

        Args:
            macro_data: Complete macro-level data including:
                - convergence_by_dimension
                - convergence_by_policy_area
                - missing_clusters
                - dimension_coverage
                - policy_area_coverage
                - micro_claims
                - meso_summary_signals
                - macro_narratives
                - meso_posteriors
                - cluster_weights
                - critical_gaps
                - dependency_graph
                - effort_estimates
                - impact_scores
                - peer_distributions
                - baseline_confidence

        Returns:
            Dict with results from all 5 analyses
        """
        results = {}

        # 1. Coverage & Structural Gap Analysis
        coverage_analysis = self.coverage_stressor.evaluate(
            convergence_by_dimension=macro_data.get("convergence_by_dimension", {}),
            missing_clusters=macro_data.get("missing_clusters", []),
            dimension_coverage=macro_data.get("dimension_coverage", {}),
            policy_area_coverage=macro_data.get("policy_area_coverage", {}),
            baseline_confidence=macro_data.get("baseline_confidence", get_parameter_loader().get("saaaaaa.analysis.macro_prompts.MacroPromptsOrchestrator.__init__").get("auto_param_L1165_70", 1.0))
        )
        results["coverage_analysis"] = asdict(coverage_analysis)

        # 2. Inter-Level Contradiction Scan
        contradiction_report = self.contradiction_scanner.scan(
            micro_claims=macro_data.get("micro_claims", []),
            meso_summary_signals=macro_data.get("meso_summary_signals", {}),
            macro_narratives=macro_data.get("macro_narratives", {})
        )
        results["contradiction_report"] = asdict(contradiction_report)

        # 3. Bayesian Portfolio Composition
        bayesian_portfolio = self.portfolio_composer.compose(
            meso_posteriors=macro_data.get("meso_posteriors", {}),
            cluster_weights=macro_data.get("cluster_weights", {}),
            reconciliation_penalties=macro_data.get("reconciliation_penalties")
        )
        results["bayesian_portfolio"] = asdict(bayesian_portfolio)

        # 4. Roadmap Optimization
        implementation_roadmap = self.roadmap_optimizer.optimize(
            critical_gaps=macro_data.get("critical_gaps", []),
            dependency_graph=macro_data.get("dependency_graph", {}),
            effort_estimates=macro_data.get("effort_estimates", {}),
            impact_scores=macro_data.get("impact_scores", {})
        )
        results["implementation_roadmap"] = asdict(implementation_roadmap)

        # 5. Peer Normalization
        peer_normalization = self.peer_normalizer.normalize(
            convergence_by_policy_area=macro_data.get("convergence_by_policy_area", {}),
            peer_distributions=macro_data.get("peer_distributions", {}),
            baseline_confidence=macro_data.get("baseline_confidence", get_parameter_loader().get("saaaaaa.analysis.macro_prompts.MacroPromptsOrchestrator.__init__").get("auto_param_L1198_70", 1.0))
        )
        results["peer_normalization"] = asdict(peer_normalization)

        logger.info("Completed all 5 macro analyses")
        return results
