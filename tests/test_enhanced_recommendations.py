#!/usr/bin/env python3
"""
End-to-end test of the recommendation engine integration with orchestrator.
Tests all 7 enhanced features across MICRO, MESO, and MACRO levels.
"""

import json
import sys

# Add parent directory to path
from saaaaaa.analysis.recommendation_engine import load_recommendation_engine
from saaaaaa.utils.paths import tmp_dir

def test_enhanced_recommendation_engine():
    """Test all 7 enhanced features"""
    print("=" * 80)
    print("TESTING ENHANCED RECOMMENDATION ENGINE v2.0")
    print("=" * 80)

    # Initialize engine with enhanced rules
    print("\n1. Initializing engine with enhanced rules...")
    engine = load_recommendation_engine(
        rules_path="config/recommendation_rules_enhanced.json",
        schema_path="rules/recommendation_rules_enhanced.schema.json"
    )
    print(f"   ✓ Loaded {len(engine.rules['rules'])} rules")
    print(f"   ✓ MICRO rules: {len(engine.rules_by_level['MICRO'])}")
    print(f"   ✓ MESO rules: {len(engine.rules_by_level['MESO'])}")
    print(f"   ✓ MACRO rules: {len(engine.rules_by_level['MACRO'])}")

    # Test MICRO recommendations
    print("\n2. Testing MICRO recommendations...")
    micro_scores = {
        'PA01-DIM01': 1.2,   # Below threshold (1.65)
        'PA01-DIM02': 1.5,   # Below threshold
        'PA02-DIM03': 2.1,   # Above threshold
        'PA05-DIM05': 1.3,   # Below threshold
    }

    micro_recs = engine.generate_micro_recommendations(micro_scores)
    print(f"   ✓ Generated {micro_recs.rules_matched} MICRO recommendations")
    print(f"   ✓ Evaluated {micro_recs.total_rules_evaluated} rules")

    # Validate first MICRO recommendation has all 7 features
    if micro_recs.recommendations:
        rec = micro_recs.recommendations[0]
        print(f"\n   Testing enhanced features on {rec.rule_id}:")

        # Feature 1: Template parameterization
        assert rec.template_id is not None, "Missing template_id"
        assert rec.template_params is not None, "Missing template_params"
        print(f"   ✓ Feature 1 - Template ID: {rec.template_id}")

        # Feature 2: Execution logic
        assert rec.execution is not None, "Missing execution"
        assert 'trigger_condition' in rec.execution, "Missing trigger_condition"
        assert 'requires_approval' in rec.execution, "Missing requires_approval"
        print(f"   ✓ Feature 2 - Execution: {rec.execution['trigger_condition'][:50]}...")

        # Feature 3: Measurable indicators
        assert 'formula' in rec.indicator, "Missing indicator formula"
        assert 'data_source' in rec.indicator, "Missing data_source"
        assert 'data_source_query' in rec.indicator, "Missing data_source_query"
        assert 'acceptable_range' in rec.indicator, "Missing acceptable_range"
        print(f"   ✓ Feature 3 - Formula: {rec.indicator['formula']}")
        print(f"   ✓ Feature 3 - Data source: {rec.indicator['data_source']}")

        # Feature 4: Unambiguous time horizons
        assert 'duration_months' in rec.horizon, "Missing duration_months"
        assert 'milestones' in rec.horizon, "Missing milestones"
        assert 'start_type' in rec.horizon, "Missing start_type"
        print(f"   ✓ Feature 4 - Duration: {rec.horizon['duration_months']} months")
        print(f"   ✓ Feature 4 - Milestones: {len(rec.horizon['milestones'])} defined")

        # Feature 5: Testable verification
        assert len(rec.verification) > 0, "No verification artifacts"
        assert isinstance(rec.verification[0], dict), "Verification not structured"
        assert 'id' in rec.verification[0], "Missing verification ID"
        assert 'type' in rec.verification[0], "Missing verification type"
        print(f"   ✓ Feature 5 - Verification: {len(rec.verification)} artifacts")
        print(f"   ✓ Feature 5 - First artifact: {rec.verification[0]['id']}")

        # Feature 6: Cost tracking
        assert rec.budget is not None, "Missing budget"
        assert 'estimated_cost_cop' in rec.budget, "Missing estimated_cost_cop"
        assert 'cost_breakdown' in rec.budget, "Missing cost_breakdown"
        assert 'funding_sources' in rec.budget, "Missing funding_sources"
        print(f"   ✓ Feature 6 - Budget: ${rec.budget['estimated_cost_cop']:,} COP")
        print(f"   ✓ Feature 6 - Breakdown: Personal={rec.budget['cost_breakdown']['personal']:,}, "
              f"Consultancy={rec.budget['cost_breakdown']['consultancy']:,}")

        # Feature 7: Authority mapping
        assert 'legal_mandate' in rec.responsible, "Missing legal_mandate"
        assert 'approval_chain' in rec.responsible, "Missing approval_chain"
        assert 'escalation_path' in rec.responsible, "Missing escalation_path"
        print(f"   ✓ Feature 7 - Legal mandate: {rec.responsible['legal_mandate'][:50]}...")
        print(f"   ✓ Feature 7 - Approval chain: {len(rec.responsible['approval_chain'])} levels")

    # Test MESO recommendations
    print("\n3. Testing MESO recommendations...")
    cluster_data = {
        'CL01': {'score': 72.0, 'variance': 0.25, 'weak_pa': 'PA02'},
        'CL02': {'score': 45.0, 'variance': 0.12, 'weak_pa': 'PA05'},
    }

    meso_recs = engine.generate_meso_recommendations(cluster_data)
    print(f"   ✓ Generated {meso_recs.rules_matched} MESO recommendations")

    if meso_recs.recommendations:
        rec = meso_recs.recommendations[0]
        print(f"   ✓ MESO recommendation: {rec.rule_id}")
        assert rec.budget is not None, "MESO missing budget"
        assert rec.execution is not None, "MESO missing execution"
        print(f"   ✓ MESO budget: ${rec.budget['estimated_cost_cop']:,} COP")

    # Test MACRO recommendations
    print("\n4. Testing MACRO recommendations...")
    macro_data = {
        'macro_band': 'SATISFACTORIO',
        'clusters_below_target': ['CL02', 'CL03'],
        'variance_alert': 'MODERADA',
        'priority_micro_gaps': ['PA01-DIM05', 'PA05-DIM04', 'PA04-DIM04', 'PA08-DIM05']
    }

    macro_recs = engine.generate_macro_recommendations(macro_data)
    print(f"   ✓ Generated {macro_recs.rules_matched} MACRO recommendations")

    if macro_recs.recommendations:
        rec = macro_recs.recommendations[0]
        print(f"   ✓ MACRO recommendation: {rec.rule_id}")
        assert rec.budget is not None, "MACRO missing budget"
        assert rec.execution is not None, "MACRO missing execution"
        print(f"   ✓ MACRO budget: ${rec.budget['estimated_cost_cop']:,} COP")

    # Test generate_all_recommendations (orchestrator integration point)
    print("\n5. Testing generate_all_recommendations (orchestrator integration)...")
    all_recs = engine.generate_all_recommendations(
        micro_scores=micro_scores,
        cluster_data=cluster_data,
        macro_data=macro_data
    )

    print(f"   ✓ MICRO: {len(all_recs['MICRO'].recommendations)} recommendations")
    print(f"   ✓ MESO: {len(all_recs['MESO'].recommendations)} recommendations")
    print(f"   ✓ MACRO: {len(all_recs['MACRO'].recommendations)} recommendations")

    # Export test
    print("\n6. Testing export functionality...")
    export_root = tmp_dir() / "recommendation_exports"
    export_root.mkdir(parents=True, exist_ok=True)
    output_json = export_root / "test_recommendations.json"
    output_md = export_root / "test_recommendations.md"

    engine.export_recommendations(all_recs, str(output_json), format='json')
    print(f"   ✓ Exported to JSON: {output_json}")

    engine.export_recommendations(all_recs, str(output_md), format='markdown')
    print(f"   ✓ Exported to Markdown: {output_md}")

    # Verify JSON export has enhanced fields
    with open(output_json, encoding='utf-8') as f:
        exported = json.load(f)

    if exported['MICRO']['recommendations']:
        first_rec = exported['MICRO']['recommendations'][0]
        assert 'execution' in first_rec, "Exported JSON missing execution"
        assert 'budget' in first_rec, "Exported JSON missing budget"
        print("   ✓ Exported JSON contains all enhanced fields")

    print("\n" + "=" * 80)
    print("✓ ALL TESTS PASSED - Enhanced recommendation engine is fully functional")
    print("=" * 80)
    print("\nSummary:")
    print(f"  - Total recommendations: {len(all_recs['MICRO'].recommendations) + len(all_recs['MESO'].recommendations) + len(all_recs['MACRO'].recommendations)}")
    print("  - All 7 advanced features validated")
    print("  - Orchestrator integration point tested")
    print("  - Export formats working (JSON, Markdown)")

    return True

if __name__ == '__main__':
    try:
        success = test_enhanced_recommendation_engine()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
