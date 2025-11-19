"""
Micro Prompts Integration Example
==================================

Demonstrates how to integrate the three micro prompts with the existing
bayesian_multilevel_system, evidence_registry, and report_assembly modules.
"""

import time
from pathlib import Path

# Add parent directory to path for imports
# Import micro prompts
import importlib.util

# Verify package is available
try:
    import saaaaaa
except ImportError as e:
    print("❌ ERROR: Cannot import saaaaaa package")
    print(f"   {e}")
    print("\n📦 Please install the package first:")
    print("   pip install -e .")
    print("\nNeed to debug your environment?")
    print("   python -m saaaaaa.devtools.ensure_install")
    exit(1)

from saaaaaa.processing.micro_prompts import (
    CausalChain,
    ProportionalityPattern,
    ProvenanceDAG,
    ProvenanceNode,
    QMCMRecord,
    Signal,
    create_posterior_explainer,
    create_provenance_auditor,
    create_stress_tester,
)

# Import existing system components (when available)
BAYESIAN_AVAILABLE = importlib.util.find_spec("bayesian_multilevel_system") is not None
if not BAYESIAN_AVAILABLE:
    print("Note: bayesian_multilevel_system not fully imported")

# Check for evidence_registry availability
_registry_spec = importlib.util.find_spec("saaaaaa.core.orchestrator.evidence_registry")
if _registry_spec is None:
    _registry_spec = importlib.util.find_spec("orchestrator.evidence_registry")
REGISTRY_AVAILABLE = _registry_spec is not None
if not REGISTRY_AVAILABLE:
    print("Note: evidence_registry not fully imported")

def example_1_provenance_audit():
    """
    Example 1: Provenance Audit on a micro-level answer

    Shows how to validate QMCM integrity and provenance DAG
    for a single question's analysis pipeline.
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: Provenance Audit (QMCM Integrity Check)")
    print("="*70)

    # Create provenance auditor with 500ms latency threshold
    auditor = create_provenance_auditor(p95_latency=500.0)

    # Simulate QMCM records for a question
    qmcm_records = {
        'qmcm_001': QMCMRecord(
            question_id='P1-D1-Q1',
            method_fqn='financiero_viabilidad_tablas.PDETMunicipalPlanAnalyzer.analyze_financial_feasibility',
            contribution_weight=0.4,
            timestamp=time.time(),
            output_schema={
                'feasibility_score': 'float',
                'budget_allocation': 'dict',
                'gaps': 'list'
            }
        ),
        'qmcm_002': QMCMRecord(
            question_id='P1-D1-Q1',
            method_fqn='embedding_policy.BayesianEvidenceScorer.compute_evidence_score',
            contribution_weight=0.3,
            timestamp=time.time(),
            output_schema={
                'posterior': 'float',
                'confidence': 'float'
            }
        ),
        'qmcm_003': QMCMRecord(
            question_id='P1-D1-Q1',
            method_fqn='derek_beach.BeachEvidentialTest.apply_test_logic',
            contribution_weight=0.3,
            timestamp=time.time(),
            output_schema={
                'test_result': 'bool',
                'strength': 'float'
            }
        )
    }

    # Build provenance DAG
    nodes = {
        'input_doc': ProvenanceNode(
            node_id='input_doc',
            node_type='input',
            parent_ids=[],
            timing=0.0
        ),
        'financial_analysis': ProvenanceNode(
            node_id='financial_analysis',
            node_type='method',
            parent_ids=['input_doc'],
            qmcm_record_id='qmcm_001',
            timing=250.0
        ),
        'bayesian_score': ProvenanceNode(
            node_id='bayesian_score',
            node_type='method',
            parent_ids=['financial_analysis'],
            qmcm_record_id='qmcm_002',
            timing=120.0
        ),
        'beach_test': ProvenanceNode(
            node_id='beach_test',
            node_type='method',
            parent_ids=['financial_analysis'],
            qmcm_record_id='qmcm_003',
            timing=180.0
        ),
        'final_output': ProvenanceNode(
            node_id='final_output',
            node_type='output',
            parent_ids=['bayesian_score', 'beach_test'],
            timing=50.0
        )
    }

    edges = [
        ('input_doc', 'financial_analysis'),
        ('financial_analysis', 'bayesian_score'),
        ('financial_analysis', 'beach_test'),
        ('bayesian_score', 'final_output'),
        ('beach_test', 'final_output')
    ]

    dag = ProvenanceDAG(nodes=nodes, edges=edges)

    # Define method contracts (expected schemas)
    contracts = {
        'financiero_viabilidad_tablas.PDETMunicipalPlanAnalyzer.analyze_financial_feasibility': {
            'feasibility_score': 'float',
            'budget_allocation': 'dict',
            'gaps': 'list'
        },
        'embedding_policy.BayesianEvidenceScorer.compute_evidence_score': {
            'posterior': 'float',
            'confidence': 'float'
        },
        'derek_beach.BeachEvidentialTest.apply_test_logic': {
            'test_result': 'bool',
            'strength': 'float'
        }
    }

    # Perform audit
    result = auditor.audit(
        micro_answer=None,  # Would be actual MicroLevelAnswer
        evidence_registry=qmcm_records,
        provenance_dag=dag,
        method_contracts=contracts
    )

    # Display results
    print(f"\n✓ Audit Severity: {result.severity}")
    print(f"✓ Missing QMCM: {len(result.missing_qmcm)}")
    print(f"✓ Orphan Nodes: {len(result.orphan_nodes)}")
    print(f"✓ Schema Mismatches: {len(result.schema_mismatches)}")
    print(f"✓ Latency Anomalies: {len(result.latency_anomalies)}")
    print("\n✓ Contribution Weights:")
    for method, weight in result.contribution_weights.items():
        short_name = method.split('.')[-1]
        print(f"  - {short_name}: {weight:.2f}")
    print(f"\n✓ Narrative: {result.narrative}")

    # Export to JSON
    audit_json = auditor.to_json(result)
    print(f"\n✓ JSON export keys: {list(audit_json.keys())}")

    return result

def example_2_bayesian_posterior_justification():
    """
    Example 2: Bayesian Posterior Justification

    Shows how to explain how different signals contributed to
    the final posterior probability for a question.
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: Bayesian Posterior Justification")
    print("="*70)

    # Create explainer with anti-miracle cap at 0.95
    explainer = create_posterior_explainer(anti_miracle_cap=0.95)

    # Simulate signals from different analysis methods
    signals = [
        Signal(
            test_type='Hoop',
            likelihood=0.8,
            weight=0.3,
            raw_evidence_id='evidence_bayesian_001',
            reconciled=True,
            delta_posterior=0.12,
            reason=""  # Will be auto-generated by explainer
        ),
        Signal(
            test_type='Smoking-Gun',
            likelihood=0.95,
            weight=0.4,
            raw_evidence_id='evidence_beach_002',
            reconciled=True,
            delta_posterior=0.28,
            reason=""  # Will be auto-generated by explainer
        ),
        Signal(
            test_type='Straw-in-Wind',
            likelihood=0.65,
            weight=0.2,
            raw_evidence_id='evidence_pattern_003',
            reconciled=True,
            delta_posterior=0.05,
            reason=""  # Will be auto-generated by explainer
        ),
        Signal(
            test_type='Doubly-Decisive',
            likelihood=0.85,
            weight=0.1,
            raw_evidence_id='evidence_financial_004',
            reconciled=False,  # Failed reconciliation
            delta_posterior=0.18,
            reason="Contract violation: missing required field"
        )
    ]

    # Explain posterior
    prior = 0.35
    posterior = 0.80

    result = explainer.explain(
        prior=prior,
        signals=signals,
        posterior=posterior
    )

    # Display results
    print(f"\n✓ Prior Probability: {result.prior:.3f}")
    print(f"✓ Posterior Probability: {result.posterior:.3f}")
    print(f"✓ Change: {result.posterior - result.prior:+.3f}")

    print("\n✓ Signals Ranked by Impact:")
    for i, signal in enumerate(result.signals_ranked[:5], 1):
        print(f"  {i}. {signal['test_type']} (Δ={signal['delta_posterior']:.3f})")
        print(f"     {signal['reason']}")

    print(f"\n✓ Discarded Signals: {len(result.discarded_signals)}")
    for signal in result.discarded_signals:
        print(f"  - {signal['test_type']}: {signal['reason']}")

    print(f"\n✓ Anti-Miracle Cap Applied: {result.anti_miracle_cap_applied}")
    if result.anti_miracle_cap_applied:
        print(f"  Cap Delta: {result.cap_delta:.3f}")

    print("\n✓ Robustness Narrative:")
    print(f"  {result.robustness_narrative}")

    # Export to JSON
    justification_json = explainer.to_json(result)
    print(f"\n✓ JSON export contains {len(justification_json['signals_ranked'])} ranked signals")

    return result

def example_3_anti_milagro_stress_test():
    """
    Example 3: Anti-Milagro Stress Test

    Shows how to test structural fragility of causal chains
    by simulating node removal and checking for non-proportional jumps.
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: Anti-Milagro Stress Test")
    print("="*70)

    # Create stress tester with 30% fragility threshold
    tester = create_stress_tester(fragility_threshold=0.3)

    # Define causal chain for a Theory of Change
    chain = CausalChain(
        steps=[
            'Budget_Allocation',
            'Resource_Acquisition',
            'Activity_Implementation',
            'Output_Delivery',
            'Outcome_Achievement',
            'Impact_Realization'
        ],
        edges=[
            ('Budget_Allocation', 'Resource_Acquisition'),
            ('Resource_Acquisition', 'Activity_Implementation'),
            ('Activity_Implementation', 'Output_Delivery'),
            ('Output_Delivery', 'Outcome_Achievement'),
            ('Outcome_Achievement', 'Impact_Realization')
        ]
    )

    # Define proportionality patterns found in evidence
    patterns = [
        ProportionalityPattern(
            pattern_type='linear',
            strength=0.85,
            location='Budget_Allocation'
        ),
        ProportionalityPattern(
            pattern_type='dose-response',
            strength=0.75,
            location='Resource_Acquisition'
        ),
        ProportionalityPattern(
            pattern_type='mechanism',
            strength=0.80,
            location='Activity_Implementation'
        ),
        ProportionalityPattern(
            pattern_type='threshold',
            strength=0.65,
            location='Output_Delivery'
        ),
        # Note: missing patterns for Outcome and Impact steps
    ]

    # Missing required patterns
    missing = [
        'dose-response for Outcome_Achievement',
        'mechanism for Impact_Realization'
    ]

    # Run stress test
    result = tester.stress_test(
        causal_chain=chain,
        proportionality_patterns=patterns,
        missing_patterns=missing
    )

    # Display results
    print(f"\n✓ Causal Chain Length: {chain.length()} steps")
    print(f"✓ Patterns Found: {len(patterns)}")
    print(f"✓ Pattern Density: {result.density:.2f} patterns/step")
    print(f"✓ Pattern Coverage: {result.pattern_coverage:.1%}")

    print("\n✓ Stress Test Results:")
    print(f"  - Simulated Support Drop: {result.simulated_drop:.1%}")
    print(f"  - Fragility Flag: {'⚠️  FRAGILE' if result.fragility_flag else '✓ ROBUST'}")

    print(f"\n✓ Missing Patterns ({len(result.missing_patterns)}):")
    for pattern in result.missing_patterns:
        print(f"  - {pattern}")

    print("\n✓ Explanation:")
    print(f"  {result.explanation}")

    # Export to JSON
    stress_json = tester.to_json(result)
    print(f"\n✓ JSON export keys: {list(stress_json.keys())}")

    return result

def example_4_integrated_workflow():
    """
    Example 4: Integrated Workflow

    Shows how to use all three micro prompts together in a
    complete quality assurance workflow for a micro-level answer.
    """
    print("\n" + "="*70)
    print("EXAMPLE 4: Integrated Quality Assurance Workflow")
    print("="*70)

    # Step 1: Provenance Audit
    print("\nStep 1: Running Provenance Audit...")
    audit_result = example_1_provenance_audit()

    if audit_result.severity in ['HIGH', 'CRITICAL']:
        print(f"\n⚠️  ALERT: Provenance audit severity is {audit_result.severity}")
        print("  Recommend investigating before proceeding.")

    # Step 2: Bayesian Justification
    print("\n" + "-"*70)
    print("Step 2: Running Bayesian Posterior Justification...")
    posterior_result = example_2_bayesian_posterior_justification()

    if len(posterior_result.discarded_signals) > 0:
        print(f"\n⚠️  WARNING: {len(posterior_result.discarded_signals)} signals discarded")
        print("  Review reconciliation failures.")

    # Step 3: Stress Test
    print("\n" + "-"*70)
    print("Step 3: Running Anti-Milagro Stress Test...")
    stress_result = example_3_anti_milagro_stress_test()

    if stress_result.fragility_flag:
        print(f"\n⚠️  FRAGILITY DETECTED: Support drop = {stress_result.simulated_drop:.1%}")
        print("  Causal chain may depend on non-proportional jumps.")

    # Summary
    print("\n" + "="*70)
    print("QUALITY ASSURANCE SUMMARY")
    print("="*70)

    # Calculate overall QA score
    qa_scores = {
        'provenance': 1.0 if audit_result.severity == 'LOW' else 0.5,
        'posterior': 1.0 if posterior_result.posterior > 0.7 else 0.5,
        'stress': 0.0 if stress_result.fragility_flag else 1.0
    }

    overall_qa = sum(qa_scores.values()) / len(qa_scores)

    print(f"\n✓ Provenance Quality: {'PASS' if qa_scores['provenance'] == 1.0 else 'WARN'}")
    print(f"✓ Posterior Robustness: {'PASS' if qa_scores['posterior'] == 1.0 else 'WARN'}")
    print(f"✓ Structural Integrity: {'PASS' if qa_scores['stress'] == 1.0 else 'WARN'}")
    print(f"\n✓ Overall QA Score: {overall_qa:.1%}")

    if overall_qa >= 0.8:
        print("\n✅ QUALITY ASSURANCE: PASSED")
    else:
        print("\n⚠️  QUALITY ASSURANCE: NEEDS ATTENTION")

    return {
        'audit': audit_result,
        'posterior': posterior_result,
        'stress': stress_result,
        'qa_score': overall_qa
    }

if __name__ == '__main__':
    print("\n" + "="*70)
    print("MICRO PROMPTS INTEGRATION EXAMPLES")
    print("="*70)
    print("\nDemonstrating the three micro prompts:")
    print("1. Provenance Auditor (QMCM Integrity Check)")
    print("2. Bayesian Posterior Justification")
    print("3. Anti-Milagro Stress Test")
    print("4. Integrated Quality Assurance Workflow")

    # Run individual examples
    example_1_provenance_audit()
    example_2_bayesian_posterior_justification()
    example_3_anti_milagro_stress_test()

    # Run integrated workflow
    results = example_4_integrated_workflow()

    print("\n" + "="*70)
    print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
    print("="*70)
    print(f"\nFinal QA Score: {results['qa_score']:.1%}")
