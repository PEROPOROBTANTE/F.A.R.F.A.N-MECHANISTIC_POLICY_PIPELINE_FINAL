# Enhanced Recommendation Engine v2.0

## Overview

The recommendation engine has been enhanced with 7 advanced features to provide actionable, measurable, and accountable recommendations for development plans. This document describes the enhancements and how to use them.

## Version History

- **v1.0**: Basic recommendation engine with simple rules
- **v2.0**: Enhanced with 7 advanced features (current version)

## The 7 Advanced Features

### 1. Template Parameterization

**Problem**: Hardcoded template strings made rules verbose and difficult to maintain.

**Solution**: Introduced `template_id` and `template_params` for cleaner, reusable templates.

```json
{
  "template": {
    "template_id": "TPL-REC-MICRO-PA01-DIM01-LB01",
    "template_params": {
      "pa_id": "PA01",
      "dim_id": "DIM01",
      "question_id": "Q001"
    },
    "problem": "La pregunta {{Q001}} de {{PAxx}}..."
  }
}
```

### 2. Rule Execution Logic

**Problem**: Rules lacked metadata about how and when they should be executed.

**Solution**: Added `execution` block with trigger conditions, approval requirements, and automation settings.

```json
{
  "execution": {
    "trigger_condition": "score < 1.65 AND pa_id = 'PA01' AND dim_id = 'DIM01'",
    "blocking": false,
    "auto_apply": false,
    "requires_approval": true,
    "approval_roles": ["Secretaría de Planeación", "Secretaría de Hacienda"]
  }
}
```

**Fields**:
- `trigger_condition`: Boolean expression defining when rule activates
- `blocking`: Whether this rule blocks other actions
- `auto_apply`: Whether recommendation is applied automatically
- `requires_approval`: Whether manual approval is required
- `approval_roles`: Roles that can approve this recommendation

### 3. Measurable Indicators

**Problem**: Vague indicators with no calculation method or data sources.

**Solution**: Added comprehensive measurement metadata.

```json
{
  "indicator": {
    "name": "PA01-DIM01 líneas base homologadas",
    "baseline": null,
    "target": 0.85,
    "unit": "proporción",
    "formula": "COUNT(compliant_items) / COUNT(total_items)",
    "acceptable_range": [0.6, 1.0],
    "baseline_measurement_date": "2024-01-01",
    "measurement_frequency": "mensual",
    "data_source": "Sistema de Seguimiento de Planes (SSP)",
    "data_source_query": "SELECT COUNT(*) FROM indicators WHERE indicator_id = 'REC-MICRO-PA01-DIM01-LB01-IND'",
    "responsible_measurement": "Oficina de Planeación Municipal",
    "escalation_if_below": 0.6
  }
}
```

**Fields**:
- `formula`: Calculation method for the indicator
- `acceptable_range`: [min, max] acceptable values
- `baseline_measurement_date`: Date of baseline measurement
- `measurement_frequency`: How often measured (diaria, semanal, mensual, etc.)
- `data_source`: Where data comes from
- `data_source_query`: SQL or API query to retrieve data
- `responsible_measurement`: Who is responsible for measurement
- `escalation_if_below`: Threshold value that triggers escalation

### 4. Unambiguous Time Horizons

**Problem**: Abstract T0/T1/T2/T3 labels with no concrete meaning.

**Solution**: Added duration in months, milestones, and dependencies.

```json
{
  "horizon": {
    "start": "T0",
    "end": "T1",
    "start_type": "plan_approval_date",
    "duration_months": 6,
    "milestones": [
      {
        "name": "Inicio de implementación",
        "offset_months": 1,
        "deliverables": ["Plan de trabajo aprobado"],
        "verification_required": true
      },
      {
        "name": "Entrega final",
        "offset_months": 6,
        "deliverables": ["Todos los productos esperados"],
        "verification_required": true
      }
    ],
    "dependencies": [],
    "critical_path": true
  }
}
```

**Fields**:
- `start_type`: What T0 represents (plan_approval_date, project_start_date, fiscal_year_start)
- `duration_months`: Duration in months from start to end
- `milestones`: Array of checkpoint objects with deliverables
- `dependencies`: IDs of rules that must complete first
- `critical_path`: Whether this is on the critical path

### 5. Testable Verification

**Problem**: Simple string arrays made verification subjective and untestable.

**Solution**: Structured artifacts with validation queries.

```json
{
  "verification": [
    {
      "id": "VER-REC-MICRO-PA01-DIM01-LB01-001",
      "type": "DOCUMENT",
      "artifact": "Ficha técnica de línea base sobre brechas de género...",
      "format": "PDF",
      "required_sections": ["Objetivo", "Alcance", "Resultados"],
      "approval_required": true,
      "approver": "Secretaría de Planeación",
      "due_date": "T1",
      "automated_check": false
    },
    {
      "id": "VER-REC-MICRO-PA01-DIM01-LB01-002",
      "type": "SYSTEM_STATE",
      "artifact": "Repositorio del Observatorio de Género municipal con metadatos aprobados",
      "format": "DATABASE_QUERY",
      "approval_required": true,
      "approver": "Secretaría de Planeación",
      "due_date": "T1",
      "validation_query": "SELECT COUNT(*) FROM artifacts WHERE artifact_id = 'VER-REC-MICRO-PA01-DIM01-LB01-002'",
      "pass_condition": "COUNT(*) >= 1",
      "automated_check": true
    }
  ]
}
```

**Fields**:
- `id`: Unique verification artifact ID
- `type`: DOCUMENT or SYSTEM_STATE
- `artifact`: Description of what needs to be verified
- `format`: Expected format (PDF, DATABASE_QUERY, etc.)
- `required_sections`: Required sections for documents
- `approval_required`: Whether approval is needed
- `approver`: Who approves
- `due_date`: When artifact is due
- `validation_query`: SQL query to validate system state (for SYSTEM_STATE type)
- `pass_condition`: Condition that must be true
- `automated_check`: Whether verification can be automated

### 6. Cost Tracking Integration

**Problem**: No budget information for planning and resource allocation.

**Solution**: Comprehensive budget block with breakdown and funding sources.

```json
{
  "budget": {
    "estimated_cost_cop": 45000000,
    "cost_breakdown": {
      "personal": 24750000,
      "consultancy": 13500000,
      "technology": 6750000
    },
    "funding_sources": [
      {
        "source": "SGP - Sistema General de Participaciones",
        "amount": 27000000,
        "confirmed": false
      },
      {
        "source": "Recursos Propios",
        "amount": 18000000,
        "confirmed": false
      }
    ],
    "fiscal_year": 2025
  }
}
```

**Fields**:
- `estimated_cost_cop`: Total estimated cost in Colombian Pesos
- `cost_breakdown`: Breakdown by category (personal, consultancy, technology)
- `funding_sources`: Array of funding sources with amounts and confirmation status
- `fiscal_year`: Fiscal year for the budget

### 7. Authority Mapping for Accountability

**Problem**: Unclear who has legal authority and how escalation works.

**Solution**: Legal mandates, approval chains, and escalation paths.

```json
{
  "responsible": {
    "entity": "Secretaría de la Mujer Municipal",
    "role": "lidera la política pública de género",
    "partners": ["Secretaría de Planeación", "Secretaría de Hacienda"],
    "legal_mandate": "Ley 1257 de 2008 - Normas para la prevención de violencias contra la mujer",
    "approval_chain": [
      {
        "level": 1,
        "role": "Director/Coordinador de Programa",
        "decision": "Aprueba plan de trabajo"
      },
      {
        "level": 2,
        "role": "Secretario/a de la entidad responsable",
        "decision": "Aprueba presupuesto y recursos"
      },
      {
        "level": 3,
        "role": "Secretaría de Planeación",
        "decision": "Valida coherencia con PDM"
      },
      {
        "level": 4,
        "role": "Alcalde Municipal",
        "decision": "Aprobación final (si aplica)"
      }
    ],
    "escalation_path": {
      "threshold_days_delay": 15,
      "escalate_to": "Secretaría de Planeación",
      "final_escalation": "Despacho del Alcalde",
      "consequences": ["Revisión presupuestal", "Reasignación de responsables"]
    }
  }
}
```

**Fields**:
- `legal_mandate`: Legal basis for responsibility
- `approval_chain`: Multi-level approval process
- `escalation_path`: What happens when delays occur

## Usage

### Basic Usage

```python
from recommendation_engine import load_recommendation_engine

# Initialize with enhanced rules
engine = load_recommendation_engine(
    rules_path="config/recommendation_rules_enhanced.json",
    schema_path="rules/recommendation_rules_enhanced.schema.json"
)

# Generate recommendations
micro_scores = {'PA01-DIM01': 1.2, 'PA02-DIM03': 1.8}
cluster_data = {'CL01': {'score': 72.0, 'variance': 0.25, 'weak_pa': 'PA02'}}
macro_data = {
    'macro_band': 'SATISFACTORIO',
    'clusters_below_target': ['CL02'],
    'variance_alert': 'MODERADA',
    'priority_micro_gaps': ['PA01-DIM05']
}

all_recs = engine.generate_all_recommendations(
    micro_scores=micro_scores,
    cluster_data=cluster_data,
    macro_data=macro_data
)
```

### Accessing Enhanced Fields

```python
# Get first MICRO recommendation
rec = all_recs['MICRO'].recommendations[0]

# Access execution logic
print(f"Trigger: {rec.execution['trigger_condition']}")
print(f"Requires approval: {rec.execution['requires_approval']}")

# Access budget
print(f"Cost: ${rec.budget['estimated_cost_cop']:,} COP")
print(f"Breakdown: {rec.budget['cost_breakdown']}")

# Access measurable indicator
print(f"Formula: {rec.indicator['formula']}")
print(f"Data source: {rec.indicator['data_source']}")

# Access time horizons
print(f"Duration: {rec.horizon['duration_months']} months")
print(f"Milestones: {len(rec.horizon['milestones'])}")

# Access structured verification
for ver in rec.verification:
    if isinstance(ver, dict):
        print(f"Artifact: {ver['id']} ({ver['type']})")
        if ver['automated_check']:
            print(f"  Query: {ver['validation_query']}")

# Access authority mapping
print(f"Legal mandate: {rec.responsible['legal_mandate']}")
print(f"Approval levels: {len(rec.responsible['approval_chain'])}")
```

### Orchestrator Integration

The orchestrator automatically uses enhanced rules if available, with fallback to v1.0:

```python
# In orchestrator.py
self.recommendation_engine = RecommendationEngine(
    rules_path="config/recommendation_rules_enhanced.json",  # Try v2.0 first
    schema_path="rules/recommendation_rules_enhanced.schema.json"
)
```

If enhanced rules are not available, it falls back to:

```python
self.recommendation_engine = RecommendationEngine(
    rules_path="config/recommendation_rules.json",  # Fall back to v1.0
    schema_path="rules/recommendation_rules.schema.json"
)
```

## Testing

Run the comprehensive test suite:

```bash
python3 test_enhanced_recommendations.py
```

This validates:
- All 7 enhanced features
- MICRO, MESO, and MACRO recommendations
- Orchestrator integration
- Export functionality (JSON, Markdown)

## Files

- `config/recommendation_rules_enhanced.json`: Enhanced rules (v2.0)
- `rules/recommendation_rules_enhanced.schema.json`: Enhanced schema
- `recommendation_engine.py`: Updated engine with backward compatibility
- `enhance_recommendation_rules.py`: Script to enhance existing rules
- `test_enhanced_recommendations.py`: Comprehensive test suite

## Backward Compatibility

The enhanced engine is fully backward compatible with v1.0 rules. The `Recommendation` dataclass has optional enhanced fields that are `None` when not present, ensuring existing code continues to work.

## Statistics

- **Total Rules**: 119
- **MICRO Rules**: 60 (PA01-PA10, DIM01-DIM06)
- **MESO Rules**: 54 (CL01-CL04 with variance patterns)
- **MACRO Rules**: 5 (strategic recommendations)

## Next Steps

1. **Integration Testing**: Test with real plan data from orchestrator
2. **Budget Validation**: Refine cost estimates based on actual project data
3. **Query Implementation**: Implement actual database queries for verification
4. **Approval Workflow**: Integrate with existing approval systems
5. **Monitoring Dashboard**: Create dashboard to track indicator measurements
