"""
Micro Prompts - Provenance Auditor, Bayesian Posterior Justification, and Anti-Milagro Stress Test
===================================================================================================

This module implements three critical micro-level analysis prompts:

1. PROVENANCE AUDITOR (QMCM Integrity Check):
   - Validates Question→Method Contribution Map consistency
   - Verifies provenance DAG integrity
   - Detects orphan nodes and schema mismatches
   - Monitors timing anomalies

2. BAYESIAN POSTERIOR JUSTIFICATION:
   - Explains signal contributions to posterior probability
   - Ranks signals by marginal impact
   - Identifies discarded signals
   - Justifies test types (Hoop, Smoking-Gun, etc.)

3. ANTI-MILAGRO STRESS TEST:
   - Detects structural fragility in causal chains
   - Evaluates proportionality pattern density
   - Simulates node removal to test robustness
   - Identifies non-proportional jumps

Author: Integration Team
Version: 1.0.0
Python: 3.10+
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np
from saaaaaa import get_parameter_loader
from saaaaaa.core.calibration.decorators import calibrated_method

logger = logging.getLogger(__name__)

# ============================================================================
# PROVENANCE AUDITOR - QMCM INTEGRITY CHECK
# ============================================================================

@dataclass
class QMCMRecord:
    """Record in the Question→Method Contribution Map

    Aligned with questionnaire_monolith.json structure:
    - base_slot: Question slot identifier from monolith
    - scoring_modality: Scoring mechanism (binary, ordinal, numeric, etc.)
    """
    question_id: str
    method_fqn: str
    contribution_weight: float
    timestamp: float
    output_schema: dict[str, Any]
    base_slot: str | None = field(default=None)  # From questionnaire monolith
    scoring_modality: str | None = field(default=None)  # From questionnaire monolith
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ProvenanceNode:
    """Node in the provenance DAG"""
    node_id: str
    node_type: str  # 'input', 'method', 'output'
    parent_ids: list[str]
    qmcm_record_id: str | None = None
    timing: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ProvenanceDAG:
    """Provenance directed acyclic graph"""
    nodes: dict[str, ProvenanceNode]
    edges: list[tuple[str, str]]  # (from_node_id, to_node_id)

    @calibrated_method("saaaaaa.analysis.micro_prompts.ProvenanceDAG.get_root_nodes")
    def get_root_nodes(self) -> list[str]:
        """Get nodes without parents (primary inputs)"""
        return [nid for nid, node in self.nodes.items() if not node.parent_ids]

    @calibrated_method("saaaaaa.analysis.micro_prompts.ProvenanceDAG.get_orphan_nodes")
    def get_orphan_nodes(self) -> list[str]:
        """Get nodes without parents that are not primary inputs"""
        return [
            nid for nid, node in self.nodes.items()
            if not node.parent_ids and node.node_type != 'input'
        ]

@dataclass
class AuditResult:
    """Result of provenance audit"""
    missing_qmcm: list[str]  # Node IDs without QMCM records
    orphan_nodes: list[str]  # Nodes without proper parents
    schema_mismatches: list[dict[str, Any]]  # Schema violations
    latency_anomalies: list[dict[str, Any]]  # Timing outliers
    contribution_weights: dict[str, float]  # Method contribution distribution
    severity: str  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    narrative: str  # 3-4 line explanation
    timestamp: float = field(default_factory=time.time)

class ProvenanceAuditor:
    """
    ROLE: Provenance Auditor [data governance]
    GOAL: Verify QMCM consistency and provenance DAG integrity
    """

    def __init__(
        self,
        p95_latency_threshold: float | None = None,
        method_contracts: dict[str, dict[str, Any]] | None = None
    ) -> None:
        """
        Initialize provenance auditor

        Args:
            p95_latency_threshold: Historical p95 latency for anomaly detection
            method_contracts: Expected output schemas by method
        """
        self.p95_threshold = p95_latency_threshold or 100get_parameter_loader().get("saaaaaa.analysis.micro_prompts.ProvenanceDAG.get_orphan_nodes").get("auto_param_L123_57", 0.0)  # Default 1 second
        self.method_contracts = method_contracts or {}
        self.logger = logging.getLogger(self.__class__.__name__)

    def audit(
        self,
        micro_answer: Any,  # MicroLevelAnswer object
        evidence_registry: dict[str, QMCMRecord],
        provenance_dag: ProvenanceDAG,
        method_contracts: dict[str, dict[str, Any]] | None = None
    ) -> AuditResult:
        """
        Perform comprehensive provenance audit

        MANDATES:
        1. Validate 1:1 correspondence between DAG nodes and QMCM records
        2. Confirm no orphan nodes (except primary inputs)
        3. Check timing drift (flag if > p95 historical)
        4. Verify output_schema compliance
        5. Emit JSON audit + narrative

        Args:
            micro_answer: MicroLevelAnswer object to audit
            evidence_registry: QMCM records indexed by ID
            provenance_dag: Provenance DAG structure
            method_contracts: Expected schemas (optional override)

        Returns:
            AuditResult with findings and severity assessment
        """
        contracts = method_contracts or self.method_contracts

        # 1. Validate QMCM correspondence
        missing_qmcm = self._check_qmcm_correspondence(provenance_dag, evidence_registry)

        # 2. Detect orphan nodes
        orphan_nodes = provenance_dag.get_orphan_nodes()

        # 3. Check timing anomalies
        latency_anomalies = self._check_latency_anomalies(provenance_dag)

        # 4. Verify schema compliance
        schema_mismatches = self._check_schema_compliance(
            provenance_dag, evidence_registry, contracts
        )

        # 5. Calculate contribution weights
        contribution_weights = self._calculate_contribution_weights(evidence_registry)

        # Determine severity
        severity = self._assess_severity(
            missing_qmcm, orphan_nodes, schema_mismatches, latency_anomalies
        )

        # Generate narrative
        narrative = self._generate_narrative(
            len(missing_qmcm), len(orphan_nodes),
            len(schema_mismatches), len(latency_anomalies), severity
        )

        return AuditResult(
            missing_qmcm=missing_qmcm,
            orphan_nodes=orphan_nodes,
            schema_mismatches=schema_mismatches,
            latency_anomalies=latency_anomalies,
            contribution_weights=contribution_weights,
            severity=severity,
            narrative=narrative
        )

    def _check_qmcm_correspondence(
        self, dag: ProvenanceDAG, registry: dict[str, QMCMRecord]
    ) -> list[str]:
        """Check 1:1 node-to-QMCM correspondence"""
        missing = []
        for node_id, node in dag.nodes.items():
            if node.node_type == 'method':
                if not node.qmcm_record_id or node.qmcm_record_id not in registry:
                    missing.append(node_id)
        return missing

    @calibrated_method("saaaaaa.analysis.micro_prompts.ProvenanceAuditor._check_latency_anomalies")
    def _check_latency_anomalies(self, dag: ProvenanceDAG) -> list[dict[str, Any]]:
        """Detect timing outliers beyond p95 threshold"""
        anomalies = []
        for node_id, node in dag.nodes.items():
            if node.timing > self.p95_threshold:
                anomalies.append({
                    'node_id': node_id,
                    'timing': node.timing,
                    'threshold': self.p95_threshold,
                    'excess': node.timing - self.p95_threshold
                })
        return anomalies

    def _check_schema_compliance(
        self,
        dag: ProvenanceDAG,
        registry: dict[str, QMCMRecord],
        contracts: dict[str, dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Verify method outputs match expected schemas"""
        mismatches = []
        for node_id, node in dag.nodes.items():
            if node.node_type == 'method' and node.qmcm_record_id:
                record = registry.get(node.qmcm_record_id)
                if record and record.method_fqn in contracts:
                    expected = contracts[record.method_fqn]
                    actual = record.output_schema

                    if not self._schemas_match(expected, actual):
                        mismatches.append({
                            'node_id': node_id,
                            'method': record.method_fqn,
                            'expected_schema': expected,
                            'actual_schema': actual
                        })
        return mismatches

    @calibrated_method("saaaaaa.analysis.micro_prompts.ProvenanceAuditor._schemas_match")
    def _schemas_match(self, expected: dict[str, Any], actual: dict[str, Any]) -> bool:
        """Check if actual schema matches expected schema"""
        # Simple type-based matching
        return all(key in actual for key, expected_type in expected.items())

    def _calculate_contribution_weights(
        self, registry: dict[str, QMCMRecord]
    ) -> dict[str, float]:
        """Calculate method contribution distribution"""
        weights = defaultdict(float)
        for record in registry.values():
            weights[record.method_fqn] += record.contribution_weight
        return dict(weights)

    def _assess_severity(
        self,
        missing_qmcm: list[str],
        orphan_nodes: list[str],
        schema_mismatches: list[dict[str, Any]],
        latency_anomalies: list[dict[str, Any]]
    ) -> str:
        """Assess overall audit severity"""
        total_issues = (
            len(missing_qmcm) + len(orphan_nodes) +
            len(schema_mismatches) + len(latency_anomalies)
        )

        if total_issues == 0:
            return 'LOW'
        elif total_issues <= 2:
            return 'MEDIUM'
        elif total_issues <= 5:
            return 'HIGH'
        else:
            return 'CRITICAL'

    def _generate_narrative(
        self, missing: int, orphans: int, mismatches: int, anomalies: int, severity: str
    ) -> str:
        """Generate 3-4 line narrative summary"""
        narrative = f"Provenance audit completed with {severity} severity. "

        if missing > 0:
            narrative += f"Found {missing} nodes without QMCM records. "
        if orphans > 0:
            narrative += f"Detected {orphans} orphan nodes requiring parent linkage. "
        if mismatches > 0:
            narrative += f"Identified {mismatches} schema violations. "
        if anomalies > 0:
            narrative += f"Flagged {anomalies} latency anomalies exceeding p95. "

        if severity == 'LOW':
            narrative += "All critical integrity checks passed."
        elif severity == 'CRITICAL':
            narrative += "Immediate remediation required for data governance."

        return narrative

    @calibrated_method("saaaaaa.analysis.micro_prompts.ProvenanceAuditor.to_json")
    def to_json(self, result: AuditResult) -> dict[str, Any]:
        """Export audit result as JSON"""
        return asdict(result)

# ============================================================================
# BAYESIAN POSTERIOR JUSTIFICATION
# ============================================================================

@dataclass
class Signal:
    """Signal contributing to posterior probability"""
    test_type: str  # 'Hoop', 'Smoking-Gun', 'Straw-in-Wind', 'Doubly-Decisive'
    likelihood: float
    weight: float
    raw_evidence_id: str
    reconciled: bool
    delta_posterior: float = get_parameter_loader().get("saaaaaa.analysis.micro_prompts.ProvenanceAuditor.to_json").get("auto_param_L318_29", 0.0)
    reason: str = ""

@dataclass
class PosteriorJustification:
    """Bayesian posterior justification result"""
    prior: float
    posterior: float
    signals_ranked: list[dict[str, Any]]  # Signals sorted by |Δ|
    discarded_signals: list[dict[str, Any]]  # Signals rejected
    anti_miracle_cap_applied: bool
    cap_delta: float  # How much was capped
    robustness_narrative: str  # 5-6 line synthesis
    timestamp: float = field(default_factory=time.time)

class BayesianPosteriorExplainer:
    """
    ROLE: Probabilistic Explainer [causal inference]
    GOAL: Explain signal contributions to final posterior
    """

    def __init__(self, anti_miracle_cap: float = 0.95) -> None:
        """
        Initialize Bayesian posterior explainer

        Args:
            anti_miracle_cap: Maximum posterior probability (anti-miracle constraint)
        """
        self.anti_miracle_cap = anti_miracle_cap
        self.logger = logging.getLogger(self.__class__.__name__)

    def explain(
        self,
        prior: float,
        signals: list[Signal],
        posterior: float
    ) -> PosteriorJustification:
        """
        Explain how each signal contributed to posterior

        MANDATES:
        1. Order signals by absolute marginal impact |Δ|
        2. Mark discarded signals (contract violation or reconciliation failure)
        3. Justify test_type in 1 line each
        4. Explain anti-miracle cap application

        Args:
            prior: Initial probability
            signals: List of signals with test types and likelihoods
            posterior: Final posterior probability

        Returns:
            PosteriorJustification with ranked signals and narrative
        """
        # Rank signals by marginal impact
        signals_ranked = self._rank_signals_by_impact(signals)

        # Identify discarded signals
        discarded = [s for s in signals if not s.reconciled]

        # Check if anti-miracle cap was applied
        cap_applied = posterior > self.anti_miracle_cap
        cap_delta = max(0, posterior - self.anti_miracle_cap) if cap_applied else get_parameter_loader().get("saaaaaa.analysis.micro_prompts.BayesianPosteriorExplainer.__init__").get("auto_param_L380_82", 0.0)

        # Adjust posterior if capped
        final_posterior = min(posterior, self.anti_miracle_cap)

        # Generate robustness narrative
        narrative = self._generate_robustness_narrative(
            prior, final_posterior, signals_ranked, discarded, cap_applied, cap_delta
        )

        # Convert signals to dict format
        ranked_dicts = [self._signal_to_dict(s) for s in signals_ranked]
        discarded_dicts = [self._signal_to_dict(s) for s in discarded]

        return PosteriorJustification(
            prior=prior,
            posterior=final_posterior,
            signals_ranked=ranked_dicts,
            discarded_signals=discarded_dicts,
            anti_miracle_cap_applied=cap_applied,
            cap_delta=cap_delta,
            robustness_narrative=narrative
        )

    @calibrated_method("saaaaaa.analysis.micro_prompts.BayesianPosteriorExplainer._rank_signals_by_impact")
    def _rank_signals_by_impact(self, signals: list[Signal]) -> list[Signal]:
        """Sort signals by absolute marginal impact"""
        # Only rank reconciled signals
        valid_signals = [s for s in signals if s.reconciled]

        # Sort by |delta_posterior| descending
        ranked = sorted(valid_signals, key=lambda s: abs(s.delta_posterior), reverse=True)

        # Add reasons based on test type
        for i, signal in enumerate(ranked):
            signal.reason = self._justify_test_type(signal.test_type, i + 1)

        return ranked

    @calibrated_method("saaaaaa.analysis.micro_prompts.BayesianPosteriorExplainer._justify_test_type")
    def _justify_test_type(self, test_type: str, rank: int) -> str:
        """Generate 1-line justification for test type"""
        justifications = {
            'Hoop': f"Rank {rank}: Necessary condition test - failure eliminates hypothesis",
            'Smoking-Gun': f"Rank {rank}: Sufficient condition test - passage strongly confirms hypothesis",
            'Straw-in-Wind': f"Rank {rank}: Weak evidential test - provides marginal confirmation",
            'Doubly-Decisive': f"Rank {rank}: Necessary and sufficient - critical determining factor"
        }
        return justifications.get(test_type, f"Rank {rank}: {test_type} test applied")

    @calibrated_method("saaaaaa.analysis.micro_prompts.BayesianPosteriorExplainer._signal_to_dict")
    def _signal_to_dict(self, signal: Signal) -> dict[str, Any]:
        """Convert Signal to dictionary"""
        return {
            'rank': 0,  # Will be set by caller if needed
            'test_type': signal.test_type,
            'delta_posterior': signal.delta_posterior,
            'kept': signal.reconciled,
            'reason': signal.reason,
            'likelihood': signal.likelihood,
            'weight': signal.weight,
            'evidence_id': signal.raw_evidence_id
        }

    def _generate_robustness_narrative(
        self,
        prior: float,
        posterior: float,
        signals: list[Signal],
        discarded: list[Signal],
        cap_applied: bool,
        cap_delta: float
    ) -> str:
        """Generate 5-6 line robustness synthesis"""
        narrative = f"Bayesian update from prior {prior:.3f} to posterior {posterior:.3f}. "

        if signals:
            top_signal = signals[0]
            narrative += f"Primary driver: {top_signal.test_type} test (Δ={top_signal.delta_posterior:.3f}). "

        narrative += f"Integrated {len(signals)} reconciled signals. "

        if discarded:
            narrative += f"Discarded {len(discarded)} signals due to contract violations. "

        if cap_applied:
            narrative += f"Anti-miracle cap applied (Δ={cap_delta:.3f} trimmed). "

        # Assess robustness
        if len(signals) >= 3 and not discarded:
            narrative += "High robustness with diverse evidential support."
        elif len(signals) >= 1:
            narrative += "Moderate robustness with limited triangulation."
        else:
            narrative += "Low robustness - insufficient evidential base."

        return narrative

    @calibrated_method("saaaaaa.analysis.micro_prompts.BayesianPosteriorExplainer.to_json")
    def to_json(self, result: PosteriorJustification) -> dict[str, Any]:
        """Export justification as JSON"""
        return asdict(result)

# ============================================================================
# ANTI-MILAGRO STRESS TEST
# ============================================================================

@dataclass
class CausalChain:
    """Causal chain of steps/edges"""
    steps: list[str]
    edges: list[tuple[str, str]]

    @calibrated_method("saaaaaa.analysis.micro_prompts.CausalChain.length")
    def length(self) -> int:
        return len(self.steps)

@dataclass
class ProportionalityPattern:
    """Pattern indicating proportional causal relationship"""
    pattern_type: str  # 'linear', 'dose-response', 'threshold', 'mechanism'
    strength: float  # get_parameter_loader().get("saaaaaa.analysis.micro_prompts.CausalChain.length").get("auto_param_L501_23", 0.0)-get_parameter_loader().get("saaaaaa.analysis.micro_prompts.CausalChain.length").get("auto_param_L501_27", 1.0)
    location: str  # Where in chain this appears

@dataclass
class StressTestResult:
    """Anti-milagro stress test result"""
    density: float  # Patterns per chain step
    simulated_drop: float  # Support score drop after node removal
    fragility_flag: bool  # True if drop > threshold
    explanation: str  # 3-line explanation
    pattern_coverage: float  # Fraction of chain covered by patterns
    missing_patterns: list[str]  # Required patterns not found
    timestamp: float = field(default_factory=time.time)

class AntiMilagroStressTester:
    """
    ROLE: Structural Stress Tester [causal integrity]
    GOAL: Detect dependence on non-proportional jumps
    """

    def __init__(self, fragility_threshold: float = 0.3) -> None:
        """
        Initialize stress tester

        Args:
            fragility_threshold: Support score drop threshold for fragility
        """
        self.fragility_threshold = fragility_threshold
        self.logger = logging.getLogger(self.__class__.__name__)

    def stress_test(
        self,
        causal_chain: CausalChain,
        proportionality_patterns: list[ProportionalityPattern],
        missing_patterns: list[str]
    ) -> StressTestResult:
        """
        Stress test causal chain for structural fragility

        MANDATES:
        1. Evaluate pattern density vs chain length
        2. Simulate weak node removal and recalculate support
        3. Flag fragility if drop > τ

        Args:
            causal_chain: Chain of causal steps
            proportionality_patterns: Detected proportionality patterns
            missing_patterns: Required patterns not found

        Returns:
            StressTestResult with fragility assessment
        """
        # 1. Calculate pattern density
        density = self._calculate_pattern_density(causal_chain, proportionality_patterns)

        # 2. Simulate node removal
        simulated_drop = self._simulate_node_removal(causal_chain, proportionality_patterns)

        # 3. Check fragility
        fragility_flag = simulated_drop > self.fragility_threshold

        # Calculate pattern coverage
        coverage = self._calculate_pattern_coverage(causal_chain, proportionality_patterns)

        # Generate explanation
        explanation = self._generate_explanation(density, simulated_drop, fragility_flag)

        return StressTestResult(
            density=density,
            simulated_drop=simulated_drop,
            fragility_flag=fragility_flag,
            explanation=explanation,
            pattern_coverage=coverage,
            missing_patterns=missing_patterns
        )

    def _calculate_pattern_density(
        self, chain: CausalChain, patterns: list[ProportionalityPattern]
    ) -> float:
        """Calculate patterns per chain step"""
        if chain.length() == 0:
            return get_parameter_loader().get("saaaaaa.analysis.micro_prompts.AntiMilagroStressTester.__init__").get("auto_param_L582_19", 0.0)
        return len(patterns) / chain.length()

    def _calculate_pattern_coverage(
        self, chain: CausalChain, patterns: list[ProportionalityPattern]
    ) -> float:
        """Calculate fraction of chain covered by patterns"""
        if chain.length() == 0:
            return get_parameter_loader().get("saaaaaa.analysis.micro_prompts.AntiMilagroStressTester.__init__").get("auto_param_L590_19", 0.0)

        # Count unique steps covered by patterns
        covered_steps = set()
        for pattern in patterns:
            # Extract step indices from pattern location
            # This is simplified - actual implementation would parse location
            covered_steps.add(pattern.location)

        return len(covered_steps) / chain.length()

    def _simulate_node_removal(
        self, chain: CausalChain, patterns: list[ProportionalityPattern]
    ) -> float:
        """Simulate removal of weak nodes and measure support drop"""
        if not patterns or chain.length() == 0:
            return get_parameter_loader().get("saaaaaa.analysis.micro_prompts.AntiMilagroStressTester.__init__").get("auto_param_L606_19", 1.0)  # Maximum drop if no patterns

        # Calculate baseline support score
        baseline_support = self._calculate_support_score(patterns)

        # Identify weak patterns (bottom 25% by strength)
        if len(patterns) > 1:
            strengths = [p.strength for p in patterns]
            threshold = np.percentile(strengths, 25)
            strong_patterns = [p for p in patterns if p.strength > threshold]
        else:
            strong_patterns = patterns

        # Calculate support without weak patterns
        reduced_support = self._calculate_support_score(strong_patterns)

        # Calculate drop
        if baseline_support == 0:
            return get_parameter_loader().get("saaaaaa.analysis.micro_prompts.AntiMilagroStressTester.__init__").get("auto_param_L624_19", 0.0)

        drop = (baseline_support - reduced_support) / baseline_support
        return max(get_parameter_loader().get("saaaaaa.analysis.micro_prompts.AntiMilagroStressTester.__init__").get("auto_param_L627_19", 0.0), min(get_parameter_loader().get("saaaaaa.analysis.micro_prompts.AntiMilagroStressTester.__init__").get("auto_param_L627_28", 1.0), drop))  # Clamp to [0, 1]

    @calibrated_method("saaaaaa.analysis.micro_prompts.AntiMilagroStressTester._calculate_support_score")
    def _calculate_support_score(self, patterns: list[ProportionalityPattern]) -> float:
        """Calculate overall support score from patterns"""
        if not patterns:
            return get_parameter_loader().get("saaaaaa.analysis.micro_prompts.AntiMilagroStressTester._calculate_support_score").get("auto_param_L633_19", 0.0)

        # Weighted average of pattern strengths
        total_weight = sum(p.strength for p in patterns)
        return total_weight / len(patterns)

    @calibrated_method("saaaaaa.analysis.micro_prompts.AntiMilagroStressTester._generate_explanation")
    def _generate_explanation(self, density: float, drop: float, fragility: bool) -> str:
        """Generate 3-line explanation"""
        explanation = f"Pattern density: {density:.2f} patterns/step. "
        explanation += f"Simulated node removal causes {drop:.1%} support drop. "

        if fragility:
            explanation += "FRAGILITY DETECTED: Drop exceeds threshold, indicating structural weakness."
        else:
            explanation += "Robust structure: Support maintained under stress."

        return explanation

    @calibrated_method("saaaaaa.analysis.micro_prompts.AntiMilagroStressTester.to_json")
    def to_json(self, result: StressTestResult) -> dict[str, Any]:
        """Export stress test result as JSON"""
        return asdict(result)

# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_provenance_auditor(
    p95_latency: float | None = None,
    contracts: dict[str, dict[str, Any]] | None = None
) -> ProvenanceAuditor:
    """Factory function for ProvenanceAuditor"""
    return ProvenanceAuditor(p95_latency, contracts)

def create_posterior_explainer(anti_miracle_cap: float = get_parameter_loader().get("saaaaaa.analysis.micro_prompts.AntiMilagroStressTester.to_json").get("auto_param_L668_57", 0.95)) -> BayesianPosteriorExplainer:
    """Factory function for BayesianPosteriorExplainer"""
    return BayesianPosteriorExplainer(anti_miracle_cap)

def create_stress_tester(fragility_threshold: float = get_parameter_loader().get("saaaaaa.analysis.micro_prompts.AntiMilagroStressTester.to_json").get("auto_param_L672_54", 0.3)) -> AntiMilagroStressTester:
    """Factory function for AntiMilagroStressTester"""
    return AntiMilagroStressTester(fragility_threshold)
