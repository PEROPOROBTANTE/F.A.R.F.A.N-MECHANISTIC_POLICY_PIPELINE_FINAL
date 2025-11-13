# Visual Architecture: Enhanced Recommendation Engine Integration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATOR (orchestrator.py)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Initialization (lines 7238-7254):                                          │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ try:                                                                  │  │
│  │   RecommendationEngine(                                              │  │
│  │     rules_path="config/recommendation_rules_enhanced.json",  [v2.0] │  │
│  │     schema_path="rules/recommendation_rules_enhanced.schema.json"   │  │
│  │   )                                                                   │  │
│  │ except:                                                               │  │
│  │   RecommendationEngine(                                              │  │
│  │     rules_path="config/recommendation_rules.json",           [v1.0] │  │
│  │     schema_path="rules/recommendation_rules.schema.json"            │  │
│  │   )                                                                   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  FASE 8: _generate_recommendations (lines 8007-8165):                       │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ 1. Extract MICRO scores from scored_results                         │  │
│  │    → PA-DIM combinations with averaged scores                       │  │
│  │                                                                       │  │
│  │ 2. Extract MESO cluster data                                         │  │
│  │    → Cluster scores, variance, weak PA identification               │  │
│  │                                                                       │  │
│  │ 3. Extract MACRO data                                                │  │
│  │    → Macro band, clusters below target, variance alerts             │  │
│  │                                                                       │  │
│  │ 4. Call: recommendation_engine.generate_all_recommendations()       │  │
│  │                                                                       │  │
│  │ 5. Convert RecommendationSet objects to dictionaries                │  │
│  │                                                                       │  │
│  │ 6. Return: {MICRO: {...}, MESO: {...}, MACRO: {...}}               │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└──────────────────────────┬───────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                  RECOMMENDATION ENGINE (recommendation_engine.py)            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Enhanced Recommendation Dataclass (v2.0):                                  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ @dataclass                                                            │  │
│  │ class Recommendation:                                                 │  │
│  │   # Core fields (v1.0)                                               │  │
│  │   rule_id, level, problem, intervention                              │  │
│  │   indicator, responsible, horizon, verification                      │  │
│  │                                                                       │  │
│  │   # Enhanced fields (v2.0) - OPTIONAL for backward compatibility    │  │
│  │   execution: Optional[Dict]      # Feature 2                         │  │
│  │   budget: Optional[Dict]          # Feature 6                         │  │
│  │   template_id: Optional[str]      # Feature 1                         │  │
│  │   template_params: Optional[Dict] # Feature 1                         │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  generate_all_recommendations():                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                   │  │
│  │ │ MICRO       │  │ MESO        │  │ MACRO       │                   │  │
│  │ │ 60 rules    │  │ 54 rules    │  │ 5 rules     │                   │  │
│  │ │ PA-DIM      │  │ Clusters    │  │ Strategic   │                   │  │
│  │ └─────────────┘  └─────────────┘  └─────────────┘                   │  │
│  │       │                │                │                             │  │
│  │       ├────────────────┴────────────────┤                             │  │
│  │       │  Each creates Recommendation    │                             │  │
│  │       │  objects with 7 enhanced        │                             │  │
│  │       │  features when available        │                             │  │
│  │       └──────────────┬──────────────────┘                             │  │
│  │                      ▼                                                 │  │
│  │            {'MICRO': RecommendationSet,                               │  │
│  │             'MESO': RecommendationSet,                                │  │
│  │             'MACRO': RecommendationSet}                               │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└──────────────────────────┬───────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ENHANCED RULES v2.0 (119 rules total)                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Each rule now includes 7 ADVANCED FEATURES:                                │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ 1. TEMPLATE PARAMETERIZATION                                       │    │
│  │    ✓ template_id: "TPL-REC-MICRO-PA01-DIM01-LB01"                 │    │
│  │    ✓ template_params: {pa_id, dim_id, question_id}                │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ 2. RULE EXECUTION LOGIC                                            │    │
│  │    ✓ trigger_condition: "score < 1.65 AND pa_id = 'PA01'..."     │    │
│  │    ✓ blocking: false                                               │    │
│  │    ✓ auto_apply: false                                             │    │
│  │    ✓ requires_approval: true                                       │    │
│  │    ✓ approval_roles: ["Secretaría de Planeación", ...]           │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ 3. MEASURABLE INDICATORS                                           │    │
│  │    ✓ formula: "COUNT(compliant_items) / COUNT(total_items)"       │    │
│  │    ✓ acceptable_range: [0.6, 1.0]                                  │    │
│  │    ✓ baseline_measurement_date: "2024-01-01"                       │    │
│  │    ✓ measurement_frequency: "mensual"                              │    │
│  │    ✓ data_source: "Sistema de Seguimiento de Planes (SSP)"        │    │
│  │    ✓ data_source_query: "SELECT COUNT(*) FROM..."                 │    │
│  │    ✓ responsible_measurement: "Oficina de Planeación Municipal"   │    │
│  │    ✓ escalation_if_below: 0.6                                      │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ 4. UNAMBIGUOUS TIME HORIZONS                                       │    │
│  │    ✓ start_type: "plan_approval_date"                             │    │
│  │    ✓ duration_months: 6                                            │    │
│  │    ✓ milestones: [{name, offset_months, deliverables}, ...]       │    │
│  │    ✓ dependencies: []                                              │    │
│  │    ✓ critical_path: true                                           │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ 5. TESTABLE VERIFICATION                                           │    │
│  │    ✓ Structured artifacts with:                                    │    │
│  │      - id: "VER-REC-MICRO-PA01-DIM01-LB01-001"                    │    │
│  │      - type: "DOCUMENT" or "SYSTEM_STATE"                         │    │
│  │      - format: "PDF" or "DATABASE_QUERY"                          │    │
│  │      - validation_query: "SELECT COUNT(*) FROM..."               │    │
│  │      - pass_condition: "COUNT(*) >= 1"                            │    │
│  │      - automated_check: true/false                                │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ 6. COST TRACKING INTEGRATION                                       │    │
│  │    ✓ estimated_cost_cop: 45,000,000                               │    │
│  │    ✓ cost_breakdown: {personal, consultancy, technology}          │    │
│  │    ✓ funding_sources: [{source, amount, confirmed}, ...]          │    │
│  │    ✓ fiscal_year: 2025                                             │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ 7. AUTHORITY MAPPING                                               │    │
│  │    ✓ legal_mandate: "Ley 1257 de 2008..."                         │    │
│  │    ✓ approval_chain: [{level, role, decision}, ...]  (4 levels)   │    │
│  │    ✓ escalation_path:                                              │    │
│  │      - threshold_days_delay: 15                                    │    │
│  │      - escalate_to: "Secretaría de Planeación"                    │    │
│  │      - final_escalation: "Despacho del Alcalde"                   │    │
│  │      - consequences: ["Revisión presupuestal", ...]               │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Rules validated against enhanced schema:                                   │
│  rules/recommendation_rules_enhanced.schema.json (15KB, 326 lines)          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘


TESTING & VALIDATION:
═════════════════════

┌──────────────────────────────────────────────────────────────────────────┐
│ test_enhanced_recommendations.py                                         │
├──────────────────────────────────────────────────────────────────────────┤
│ ✓ Tests all 7 enhanced features                                          │
│ ✓ Tests MICRO, MESO, MACRO levels                                        │
│ ✓ Tests export functionality (JSON, Markdown)                            │
│ ✓ 100% feature coverage                                                  │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│ test_orchestrator_integration.py                                         │
├──────────────────────────────────────────────────────────────────────────┤
│ ✓ Verifies orchestrator loads v2.0 rules                                 │
│ ✓ Tests fallback to v1.0 if needed                                       │
│ ✓ Simulates FASE 8 response                                              │
│ ✓ Validates end-to-end integration                                       │
└──────────────────────────────────────────────────────────────────────────┘


DELIVERABLES:
═════════════

Files Created:
  ✓ config/recommendation_rules_enhanced.json       (756KB, 22,155 lines)
  ✓ rules/recommendation_rules_enhanced.schema.json (15KB, 326 lines)
  ✓ enhance_recommendation_rules.py                 (13KB, 387 lines)
  ✓ test_enhanced_recommendations.py                (8.7KB, 258 lines)
  ✓ test_orchestrator_integration.py                (5.5KB, 143 lines)
  ✓ ENHANCED_RECOMMENDATION_ENGINE_README.md        (12KB, 497 lines)
  ✓ IMPLEMENTATION_SUMMARY.md                       (11KB, 352 lines)

Files Modified:
  ✓ recommendation_engine.py (enhanced Recommendation dataclass)
  ✓ orchestrator.py (v2.0 with v1.0 fallback)


STATISTICS:
═══════════

Rules Enhanced:        119 total
  - MICRO rules:       60 (PA01-PA10, DIM01-DIM06)
  - MESO rules:        54 (CL01-CL04 variance patterns)
  - MACRO rules:       5 (strategic recommendations)

Size Growth:           v1.0 (194KB) → v2.0 (756KB) = 3.9x
Lines Added:           ~24,000
Test Coverage:         100% of enhanced features
Backward Compatible:   ✓ Yes (automatic fallback)
```
