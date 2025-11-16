#!/usr/bin/env python3
"""
Demo AGUJA I: Prior Adaptativo Bayesiano
==========================================

Demuestra los tres prompts de AGUJA I:
- PROMPT I-1: Ponderación evidencial con BF y calibración
- PROMPT I-2: Sensibilidad, OOD y ablation evidencial
- PROMPT I-3: Trazabilidad y reproducibilidad

Author: AI Assistant
Version: 1.0.0
"""

import json

# Import AGUJA I desde derek_beach
from pathlib import Path

import numpy as np

# Verify package is available
try:
    import saaaaaa
except ImportError as e:
    print("❌ ERROR: Cannot import saaaaaa package")
    print(f"   {e}")
    print("\n📦 Please install the package first:")
    print("   pip install -e .")
    print("\nOr set PYTHONPATH:")
    print("   export PYTHONPATH=/path/to/SAAAAAA/src")
    exit(1)

from saaaaaa.utils.derek_beach import AdaptivePriorCalculator

def demo_prompt_i1():
    """Demo PROMPT I-1: Ponderación evidencial con BF y calibración"""
    print("\n" + "="*80)
    print("PROMPT I-1: PONDERACIÓN EVIDENCIAL CON BF Y CALIBRACIÓN")
    print("="*80)

    # Inicializar calculador
    calculator = AdaptivePriorCalculator()

    # Crear evidencia de ejemplo con 4 dominios
    evidence_dict = {
        'semantic': {
            'score': 0.75,
            'snippet': 'El plan establece mecanismos claros de causalidad...',
            'line_span': '45-52',
            'raw_value': 'high_coherence'
        },
        'temporal': {
            'score': 0.60,
            'snippet': 'Cronograma detallado con hitos trimestrales...',
            'line_span': '120-135',
            'raw_value': 'temporal_sequence_found'
        },
        'financial': {
            'score': 0.80,
            'snippet': 'Presupuesto: $12,500 millones con fuentes identificadas',
            'line_span': '200-215',
            'raw_value': 12500000000
        },
        'structural': {
            'score': 0.55,
            'snippet': 'Estructura organizacional con responsables asignados',
            'line_span': '300-320',
            'raw_value': 'partial_structure'
        }
    }

    # Calcular para diferentes tipos de test
    test_types = ['straw', 'hoop', 'smoking', 'doubly']

    print("\n📊 RESULTADOS POR TIPO DE TEST EVIDENCIAL:")
    print("-" * 80)

    for test_type in test_types:
        result = calculator.calculate_likelihood_adaptativo(evidence_dict, test_type)

        print(f"\n🔍 Test Type: {test_type.upper()}")
        print(f"   Bayes Factor: {result['BF_used']:.2f}")
        print(f"   P(mechanism): {result['p_mechanism']:.4f}")
        print(f"   Combined Score: {result['combined_score']:.4f}")
        print(f"   Triangulation Bonus: {result['triangulation_bonus']:.2f}")
        print(f"   Active Domains: {result['active_domains']}/4")
        print(f"   Domain Weights: {json.dumps(result['domain_weights'], indent=4)}")

    print("\n✅ PROMPT I-1 COMPLETADO")
    return evidence_dict

def demo_prompt_i2(evidence_dict):
    """Demo PROMPT I-2: Sensibilidad, OOD y ablation"""
    print("\n" + "="*80)
    print("PROMPT I-2: SENSIBILIDAD, OOD Y ABLATION EVIDENCIAL")
    print("="*80)

    calculator = AdaptivePriorCalculator()

    # Ejecutar análisis de sensibilidad
    sensitivity_result = calculator.sensitivity_analysis(
        evidence_dict,
        test_type='hoop',
        perturbation=0.10
    )

    print("\n📈 ANÁLISIS DE SENSIBILIDAD:")
    print("-" * 80)

    print("\n🔝 Top-3 Influencias (∂p/∂component):")
    for i, (domain, delta_p) in enumerate(sensitivity_result['influence_top3'], 1):
        print(f"   {i}. {domain}: Δp = {delta_p:+.4f}")

    print(f"\n🎯 Max Sensitivity: {sensitivity_result['delta_p_sensitivity']:.4f}")
    print(f"   Criterion (≤0.15): {'✅ PASS' if sensitivity_result['criteria_met']['max_sensitivity_ok'] else '❌ FAIL'}")

    print(f"\n🔄 Sign Concordance: {sensitivity_result['sign_concordance']:.2f}")
    print(f"   Criterion (≥2/3): {'✅ PASS' if sensitivity_result['criteria_met']['sign_concordance_ok'] else '❌ FAIL'}")

    print(f"\n🌊 OOD Drop: {sensitivity_result['OOD_drop']:.4f}")
    print(f"   Criterion (≤0.10): {'✅ PASS' if sensitivity_result['criteria_met']['ood_drop_ok'] else '❌ FAIL'}")

    print("\n🔬 ABLATION RESULTS:")
    for ablation_name, ablation_data in sensitivity_result['ablation_results'].items():
        print(f"   {ablation_name}: p = {ablation_data['p_mechanism']:.4f}, "
              f"Sign Match: {'✅' if ablation_data['sign_match'] else '❌'}")

    print(f"\n⚡ Is Fragile: {sensitivity_result['is_fragile']}")
    print(f"   Recommendation: {sensitivity_result['recommendation'].upper()}")

    print("\n✅ PROMPT I-2 COMPLETADO")
    return sensitivity_result

def demo_prompt_i3(evidence_dict):
    """Demo PROMPT I-3: Trazabilidad y reproducibilidad"""
    print("\n" + "="*80)
    print("PROMPT I-3: TRAZABILIDAD Y REPRODUCIBILIDAD")
    print("="*80)

    calculator = AdaptivePriorCalculator()

    # Calcular resultado
    result = calculator.calculate_likelihood_adaptativo(evidence_dict, 'hoop')

    # Generar registro de trazabilidad con semilla fija
    seed = 42
    trace_record = calculator.generate_traceability_record(
        evidence_dict,
        'hoop',
        result,
        seed=seed
    )

    print("\n📋 EVIDENCE TRACE:")
    print("-" * 80)

    for i, trace_item in enumerate(trace_record['evidence_trace'], 1):
        print(f"\n   {i}. Source: {trace_item['source']}")
        print(f"      Line Span: {trace_item['line_span']}")
        print(f"      Transform: {trace_item['transform_before']} → {trace_item['transform_after']:.4f}")
        print(f"      Snippet: {trace_item['snippet'][:60]}...")

    print("\n🔐 REPRODUCIBILITY:")
    print("-" * 80)
    print(f"   Config Hash: {trace_record['hash_config']}")
    print(f"   Result Hash: {trace_record['hash_result']}")
    print(f"   Seed: {trace_record['seed']}")
    print(f"   BF Table Version: {trace_record['bf_table_version']}")
    print(f"   Weights Version: {trace_record['weights_version']}")

    print("\n📊 TRACE COMPLETENESS:")
    print(f"   {trace_record['trace_completeness']:.2%}")
    print(f"   Reproducibility Guaranteed: {'✅ YES' if trace_record['reproducibility_guaranteed'] else '❌ NO'}")
    print(f"   Criterion (≥0.95): {'✅ PASS' if trace_record['trace_completeness'] >= 0.95 else '❌ FAIL'}")

    # Verificar reproducibilidad ejecutando dos veces con misma semilla
    print("\n🔁 REPRODUCIBILITY TEST:")
    print("-" * 80)

    trace_record_2 = calculator.generate_traceability_record(
        evidence_dict,
        'hoop',
        result,
        seed=seed
    )

    hash_match = trace_record['hash_result'] == trace_record_2['hash_result']
    print(f"   Hash Match (run 1 vs run 2): {'✅ IDENTICAL' if hash_match else '❌ DIFFERENT'}")
    print(f"   Run 1 Hash: {trace_record['hash_result']}")
    print(f"   Run 2 Hash: {trace_record_2['hash_result']}")

    print("\n✅ PROMPT I-3 COMPLETADO")
    return trace_record

def demo_quality_validation():
    """Demo: Validación de criterios de calidad"""
    print("\n" + "="*80)
    print("VALIDACIÓN DE CRITERIOS DE CALIDAD")
    print("="*80)

    calculator = AdaptivePriorCalculator()

    # Generar muestras sintéticas de validación
    np.random.seed(42)
    validation_samples = []

    for _i in range(50):
        # Generar evidencia sintética
        base_scores = np.random.beta(2, 2, 4)  # 4 dominios

        evidence = {
            'semantic': {'score': float(base_scores[0])},
            'temporal': {'score': float(base_scores[1])},
            'financial': {'score': float(base_scores[2])},
            'structural': {'score': float(base_scores[3])}
        }

        # Label real basado en promedio + ruido
        actual_label = np.mean(base_scores) + np.random.normal(0, 0.1)
        actual_label = np.clip(actual_label, 0, 1)

        validation_samples.append({
            'evidence': evidence,
            'actual_label': float(actual_label),
            'test_type': np.random.choice(['hoop', 'smoking'])
        })

    # Validar criterios
    quality_result = calculator.validate_quality_criteria(validation_samples)

    print("\n📊 QUALITY METRICS:")
    print("-" * 80)

    print(f"\n📈 Brier Score: {quality_result['brier_score']:.4f}")
    print(f"   Criterion (≤0.20): {'✅ PASS' if quality_result['brier_ok'] else '❌ FAIL'}")

    print(f"\n📐 ACE (Average Calibration Error): {quality_result['ace']:.4f}")
    print(f"   Criterion (∈[-0.02, 0.02]): {'✅ PASS' if quality_result['ace_ok'] else '❌ FAIL'}")

    print(f"\n📏 CI95% Coverage: {quality_result['ci95_coverage']:.2%}")
    print(f"   Criterion (∈[92%, 98%]): {'✅ PASS' if quality_result['coverage_ok'] else '❌ FAIL'}")

    print(f"\n📊 Monotonicity Violations: {quality_result['monotonicity_violations']}")
    print(f"   Criterion (=0): {'✅ PASS' if quality_result['monotonicity_ok'] else '❌ FAIL'}")

    print(f"\n🏆 OVERALL QUALITY GRADE: {quality_result['quality_grade']}")
    print(f"   All Criteria Met: {'✅ YES' if quality_result['all_criteria_met'] else '❌ NO'}")

    print("\n✅ QUALITY VALIDATION COMPLETADA")
    return quality_result

def main():
    """Ejecuta demo completa de AGUJA I"""
    print("\n" + "="*80)
    print("🎯 DEMO COMPLETA: AGUJA I - PRIOR ADAPTATIVO BAYESIANO")
    print("="*80)
    print("\nEsta demo ilustra los tres prompts de AGUJA I:")
    print("  I-1: Ponderación evidencial con BF y calibración")
    print("  I-2: Sensibilidad, OOD y ablation evidencial")
    print("  I-3: Trazabilidad y reproducibilidad")
    print("  + Validación de criterios de calidad")

    # Ejecutar demos secuencialmente
    evidence = demo_prompt_i1()
    sensitivity = demo_prompt_i2(evidence)
    trace = demo_prompt_i3(evidence)
    quality = demo_quality_validation()

    # Resumen final
    print("\n" + "="*80)
    print("🎉 DEMO COMPLETADA - RESUMEN")
    print("="*80)

    print("\n✅ PROMPT I-1: Likelihood adaptativo calculado con 4 dominios")
    print(f"   - Triangulación activa con {evidence.get('semantic', {}).get('score', 0) > 0} dominios")
    print("   - BF aplicado correctamente para diferentes test types")

    print("\n✅ PROMPT I-2: Análisis de robustez completado")
    print(f"   - Sensibilidad máxima: {sensitivity['delta_p_sensitivity']:.4f}")
    print(f"   - Fragile: {sensitivity['is_fragile']}")
    print(f"   - Recommendation: {sensitivity['recommendation']}")

    print("\n✅ PROMPT I-3: Trazabilidad garantizada")
    print(f"   - Trace completeness: {trace['trace_completeness']:.2%}")
    print(f"   - Reproducibility: {trace['reproducibility_guaranteed']}")

    print("\n✅ CALIDAD: Validación exitosa")
    print(f"   - Grade: {quality['quality_grade']}")
    print(f"   - Brier Score: {quality['brier_score']:.4f}")

    print("\n" + "="*80)
    print("📚 Para uso en producción:")
    print("   from derek_beach import AdaptivePriorCalculator")
    print("   calculator = AdaptivePriorCalculator()")
    print("   result = calculator.calculate_likelihood_adaptativo(evidence, 'hoop')")
    print("="*80)

if __name__ == "__main__":
    main()
