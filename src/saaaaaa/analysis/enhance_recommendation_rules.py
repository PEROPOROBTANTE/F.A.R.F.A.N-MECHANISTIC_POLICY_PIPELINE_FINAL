#!/usr/bin/env python3
"""
Script to enhance recommendation rules with 7 advanced features:
1. Template parameterization
2. Rule execution logic
3. Measurable indicators
4. Unambiguous time horizons
5. Testable verification
6. Cost tracking
7. Authority mapping
"""

import copy
import json
from pathlib import Path
from typing import Any
from saaaaaa.core.calibration.decorators import calibrated_method


def enhance_template(rule: dict[str, Any]) -> dict[str, Any]:
    """
    Feature 1: Eliminate Hardcoded Template Strings
    Replace with template_id and template_params
    """
    template = rule.get('template', {})
    rule_id = rule.get('rule_id', '')
    level = rule.get('level', '')

    # Extract parameters from template strings
    template_params = {}

    if level == 'MICRO':
        when = rule.get('when', {})
        template_params = {
            'pa_id': when.get('pa_id', 'PA01'),
            'dim_id': when.get('dim_id', 'DIM01'),
            'question_id': 'Q001'  # Would be derived from context
        }
    elif level == 'MESO':
        when = rule.get('when', {})
        template_params = {
            'cluster_id': when.get('cluster_id', 'CL01')
        }

    # Create enhanced template with ID
    enhanced_template = copy.deepcopy(template)
    enhanced_template['template_id'] = f"TPL-{rule_id}"
    enhanced_template['template_params'] = template_params

    return enhanced_template

def add_execution_logic(rule: dict[str, Any]) -> dict[str, Any]:
    """
    Feature 2: Add Rule Execution Logic
    """
    when = rule.get('when', {})
    level = rule.get('level', '')

    # Build trigger condition string
    trigger_parts = []
    if level == 'MICRO':
        pa_id = when.get('pa_id', '')
        dim_id = when.get('dim_id', '')
        score_lt = when.get('score_lt', 1.65)
        trigger_parts.append(f"score < {score_lt}")
        trigger_parts.append(f"pa_id = '{pa_id}'")
        trigger_parts.append(f"dim_id = '{dim_id}'")
    elif level == 'MESO':
        cluster_id = when.get('cluster_id', '')
        score_band = when.get('score_band', '')
        if score_band:
            trigger_parts.append(f"score_band = '{score_band}'")
        if cluster_id:
            trigger_parts.append(f"cluster_id = '{cluster_id}'")
    elif level == 'MACRO':
        macro_band = when.get('macro_band', '')
        if macro_band:
            trigger_parts.append(f"macro_band = '{macro_band}'")

    trigger_condition = " AND ".join(trigger_parts) if trigger_parts else "true"

    return {
        "trigger_condition": trigger_condition,
        "blocking": False,
        "auto_apply": False,
        "requires_approval": True,
        "approval_roles": ["Secretaría de Planeación", "Secretaría de Hacienda"]
    }

def enhance_indicator(indicator: dict[str, Any], rule_id: str, level: str) -> dict[str, Any]:
    """
    Feature 3: Make Indicators Measurable
    """
    enhanced = copy.deepcopy(indicator)

    # Add formula based on indicator type
    indicator.get('name', '')
    if 'proporción' in indicator.get('unit', ''):
        enhanced['formula'] = 'COUNT(compliant_items) / COUNT(total_items)'
        enhanced['acceptable_range'] = [0.6, 1.0]
    elif 'porcentaje' in indicator.get('unit', ''):
        enhanced['formula'] = '(achieved / target) * 100'
        enhanced['acceptable_range'] = [60.0, 100.0]
    else:
        enhanced['formula'] = 'SUM(verified_artifacts)'
        enhanced['acceptable_range'] = [indicator.get('target', 1) * 0.7, indicator.get('target', 1)]

    # Add measurement metadata
    enhanced['baseline_measurement_date'] = '2024-01-01'
    enhanced['measurement_frequency'] = 'mensual'
    enhanced['data_source'] = 'Sistema de Seguimiento de Planes (SSP)'
    enhanced['data_source_query'] = f"SELECT COUNT(*) FROM indicators WHERE indicator_id = '{rule_id}-IND'"
    enhanced['responsible_measurement'] = 'Oficina de Planeación Municipal'
    enhanced['escalation_if_below'] = enhanced['acceptable_range'][0]

    return enhanced

def enhance_horizon(horizon: dict[str, str], rule_id: str) -> dict[str, Any]:
    """
    Feature 4: Define Unambiguous Time Horizons
    """
    # Map T0, T1, T2, T3 to actual durations
    duration_map = {
        'T0': 0,
        'T1': 6,   # 6 months
        'T2': 12,  # 12 months
        'T3': 24   # 24 months
    }

    start = horizon.get('start', 'T0')
    end = horizon.get('end', 'T1')

    duration_months = duration_map.get(end, 6) - duration_map.get(start, 0)

    # Create milestones
    milestones = []
    if duration_months >= 6:
        milestones.append({
            "name": "Inicio de implementación",
            "offset_months": 1,
            "deliverables": ["Plan de trabajo aprobado"],
            "verification_required": True
        })
    if duration_months >= 12:
        milestones.append({
            "name": "Revisión intermedia",
            "offset_months": duration_months // 2,
            "deliverables": ["Informe de avance"],
            "verification_required": True
        })
    milestones.append({
        "name": "Entrega final",
        "offset_months": duration_months,
        "deliverables": ["Todos los productos esperados"],
        "verification_required": True
    })

    return {
        "start": start,
        "end": end,
        "start_type": "plan_approval_date",
        "duration_months": duration_months,
        "milestones": milestones,
        "dependencies": [],
        "critical_path": duration_months <= 6
    }

def enhance_verification(verification: list[str], rule_id: str) -> list[dict[str, Any]]:
    """
    Feature 5: Make Verification Testable
    """
    enhanced_verifications = []

    for idx, artifact_text in enumerate(verification, 1):
        # Determine artifact type
        artifact_type = "DOCUMENT"
        if any(word in artifact_text.lower() for word in ['sistema', 'repositorio', 'registro', 'base de datos']):
            artifact_type = "SYSTEM_STATE"

        # Create structured verification
        ver_obj = {
            "id": f"VER-{rule_id}-{idx:03d}",
            "type": artifact_type,
            "artifact": artifact_text,
            "format": "PDF" if artifact_type == "DOCUMENT" else "DATABASE_QUERY",
            "required_sections": ["Objetivo", "Alcance", "Resultados"] if artifact_type == "DOCUMENT" else [],
            "approval_required": True,
            "approver": "Secretaría de Planeación",
            "due_date": "T1",
            "automated_check": artifact_type == "SYSTEM_STATE"
        }

        # Add validation for system states
        if artifact_type == "SYSTEM_STATE":
            ver_obj["validation_query"] = f"SELECT COUNT(*) FROM artifacts WHERE artifact_id = '{ver_obj['id']}'"
            ver_obj["pass_condition"] = "COUNT(*) >= 1"

        enhanced_verifications.append(ver_obj)

    return enhanced_verifications

def add_budget(rule: dict[str, Any]) -> dict[str, Any]:
    """
    Feature 6: Integrate Cost Tracking
    """
    level = rule.get('level', '')

    # Estimate costs based on level and complexity
    if level == 'MICRO':
        base_cost = 45_000_000  # COP
    elif level == 'MESO':
        base_cost = 150_000_000
    elif level == 'MACRO':
        base_cost = 500_000_000
    else:
        base_cost = 50_000_000

    # Cost breakdown
    personal_cost = int(base_cost * 0.55)
    consultancy_cost = int(base_cost * 0.30)
    technology_cost = int(base_cost * 0.15)

    return {
        "estimated_cost_cop": base_cost,
        "cost_breakdown": {
            "personal": personal_cost,
            "consultancy": consultancy_cost,
            "technology": technology_cost
        },
        "funding_sources": [
            {
                "source": "SGP - Sistema General de Participaciones",
                "amount": int(base_cost * 0.60),
                "confirmed": False
            },
            {
                "source": "Recursos Propios",
                "amount": int(base_cost * 0.40),
                "confirmed": False
            }
        ],
        "fiscal_year": 2025
    }

def enhance_responsible(responsible: dict[str, Any]) -> dict[str, Any]:
    """
    Feature 7: Map Authority for Accountability
    """
    enhanced = copy.deepcopy(responsible)

    # Add legal mandate
    entity = responsible.get('entity', '')
    if 'Mujer' in entity:
        legal_mandate = "Ley 1257 de 2008 - Normas para la prevención de violencias contra la mujer"
    elif 'Planeación' in entity:
        legal_mandate = "Ley 152 de 1994 - Ley Orgánica del Plan de Desarrollo"
    elif 'Hacienda' in entity:
        legal_mandate = "Ley 819 de 2003 - Responsabilidad Fiscal"
    else:
        legal_mandate = "Estatuto Orgánico Municipal"

    enhanced['legal_mandate'] = legal_mandate

    # Add approval chain
    enhanced['approval_chain'] = [
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
    ]

    # Add escalation path
    enhanced['escalation_path'] = {
        "threshold_days_delay": 15,
        "escalate_to": "Secretaría de Planeación",
        "final_escalation": "Despacho del Alcalde",
        "consequences": ["Revisión presupuestal", "Reasignación de responsables"]
    }

    return enhanced

def enhance_rule(rule: dict[str, Any]) -> dict[str, Any]:
    """Enhance a single rule with all 7 features"""
    enhanced_rule = copy.deepcopy(rule)

    # 1. Template parameterization
    enhanced_rule['template'] = enhance_template(rule)

    # 2. Execution logic
    enhanced_rule['execution'] = add_execution_logic(rule)

    # 3. Measurable indicators
    if 'indicator' in enhanced_rule['template']:
        enhanced_rule['template']['indicator'] = enhance_indicator(
            enhanced_rule['template']['indicator'],
            rule.get('rule_id', ''),
            rule.get('level', '')
        )

    # 4. Unambiguous time horizons
    if 'horizon' in enhanced_rule['template']:
        enhanced_rule['template']['horizon'] = enhance_horizon(
            enhanced_rule['template']['horizon'],
            rule.get('rule_id', '')
        )

    # 5. Testable verification
    if 'verification' in enhanced_rule['template']:
        enhanced_rule['template']['verification'] = enhance_verification(
            enhanced_rule['template']['verification'],
            rule.get('rule_id', '')
        )

    # 6. Budget tracking
    enhanced_rule['budget'] = add_budget(rule)

    # 7. Authority mapping
    if 'responsible' in enhanced_rule['template']:
        enhanced_rule['template']['responsible'] = enhance_responsible(
            enhanced_rule['template']['responsible']
        )

    return enhanced_rule

def main() -> None:
    """Main enhancement process"""
    # Delegate to factory for I/O operations
    from .factory import load_json, save_json

    # Load existing rules
    rules_path = Path('config/recommendation_rules.json')
    rules_data = load_json(rules_path)

    print(f"Loaded {len(rules_data['rules'])} rules from {rules_path}")

    # Enhance all rules
    enhanced_rules = []
    for i, rule in enumerate(rules_data['rules'], 1):
        try:
            enhanced = enhance_rule(rule)
            enhanced_rules.append(enhanced)
            if i % 10 == 0:
                print(f"Enhanced {i}/{len(rules_data['rules'])} rules...")
        except Exception as e:
            print(f"Error enhancing rule {rule.get('rule_id', 'UNKNOWN')}: {e}")
            enhanced_rules.append(rule)  # Keep original if enhancement fails

    # Create enhanced data structure
    enhanced_data = {
        'version': '2.0',  # Increment version
        'enhanced_features': [
            'template_parameterization',
            'execution_logic',
            'measurable_indicators',
            'unambiguous_time_horizons',
            'testable_verification',
            'cost_tracking',
            'authority_mapping'
        ],
        'rules': enhanced_rules
    }

    # Save enhanced rules
    output_path = Path('config/recommendation_rules_enhanced.json')
    save_json(enhanced_data, output_path)

    print(f"\nEnhanced {len(enhanced_rules)} rules saved to {output_path}")
    print(f"Original file preserved at {rules_path}")

    # Show sample enhanced rule
    if enhanced_rules:
        print("\n=== Sample Enhanced Rule ===")
        print(json.dumps(enhanced_rules[0], indent=2, ensure_ascii=False)[:2000])
        print("...")

# Note: Main entry point removed to maintain I/O boundary separation.
# For usage examples, see examples/ directory.
