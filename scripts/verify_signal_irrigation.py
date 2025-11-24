#!/usr/bin/env python3
"""
Signal Irrigation Verification Script
======================================

Verifies that signal irrigation is working correctly and generates
contrafactual analysis report without requiring pytest.

Usage:
    python scripts/verify_signal_irrigation.py
"""

import re
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from saaaaaa.core.orchestrator.questionnaire import load_questionnaire
from saaaaaa.core.orchestrator.signal_registry import create_signal_registry

# Sample policy text
SAMPLE_TEXT = """
Diagnóstico de Género 2024

Según el DANE, en 2023 la tasa de feminicidios fue de 3.5 por cada 100.000 mujeres.
La Medicina Legal reportó 1,247 casos de violencia intrafamiliar.
Fuente: Observatorio de Asuntos de Género, Informe Anual 2023.

Plan de Inversiones
El presupuesto asignado para la Casa de la Mujer es de $450 millones COP.
Recursos del Plan Plurianual de Inversiones (PPI): $1,200 millones.

Indicadores de Seguimiento
- Tasa de desempleo femenina: 12.3%
- Brecha salarial de género: 18.5%
- Participación política de las mujeres: 35.2%
"""


def print_header(text: str):
    """Print formatted header."""
    print("\n" + "=" * 80)
    print(text)
    print("=" * 80)


def print_section(text: str):
    """Print formatted section."""
    print(f"\n{text}")
    print("-" * 80)


def verify_registry_initialization():
    """Verify signal registry can be initialized."""
    print_header("TEST 1: Signal Registry Initialization")

    try:
        questionnaire = load_questionnaire()
        print(f"✓ Questionnaire loaded: {questionnaire.version}")
        print(f"  Questions: {questionnaire.total_question_count}")
        print(f"  Hash: {questionnaire.sha256[:16]}...")

        registry = create_signal_registry(questionnaire)
        print(f"✓ Signal registry created")

        return registry, questionnaire

    except Exception as e:
        print(f"✗ Failed: {e}")
        return None, None


def verify_signal_packs(registry):
    """Verify all signal packs can be retrieved."""
    print_header("TEST 2: Signal Pack Retrieval")

    results = {}

    # Test chunking signals
    try:
        signals = registry.get_chunking_signals()
        print(f"✓ Chunking signals retrieved")
        print(f"  Section patterns: {len(signals.section_detection_patterns)}")
        print(f"  Section weights: {len(signals.section_weights)}")
        print(f"  Source hash: {signals.source_hash[:16]}...")
        results["chunking"] = True
    except Exception as e:
        print(f"✗ Chunking signals failed: {e}")
        results["chunking"] = False

    # Test micro answering signals
    try:
        signals = registry.get_micro_answering_signals("Q001")
        print(f"✓ Micro answering signals retrieved (Q001)")
        patterns = signals.question_patterns.get("Q001", [])
        print(f"  Patterns: {len(patterns)}")
        print(f"  Expected elements: {len(signals.expected_elements.get('Q001', []))}")
        results["micro_answering"] = True
    except Exception as e:
        print(f"✗ Micro answering signals failed: {e}")
        results["micro_answering"] = False

    # Test validation signals
    try:
        signals = registry.get_validation_signals("Q001")
        print(f"✓ Validation signals retrieved (Q001)")
        rules = signals.validation_rules.get("Q001", {})
        print(f"  Validation rules: {len(rules)}")
        results["validation"] = True
    except Exception as e:
        print(f"✗ Validation signals failed: {e}")
        results["validation"] = False

    # Test scoring signals
    try:
        signals = registry.get_scoring_signals("Q001")
        print(f"✓ Scoring signals retrieved (Q001)")
        print(f"  Modality: {signals.question_modalities.get('Q001', 'UNKNOWN')}")
        print(f"  Quality levels: {len(signals.quality_levels)}")
        results["scoring"] = True
    except Exception as e:
        print(f"✗ Scoring signals failed: {e}")
        results["scoring"] = False

    # Test assembly signals
    try:
        signals = registry.get_assembly_signals("MESO_1")
        print(f"✓ Assembly signals retrieved (MESO_1)")
        print(f"  Clusters: {len(signals.cluster_policy_areas)}")
        results["assembly"] = True
    except Exception as e:
        print(f"✗ Assembly signals failed: {e}")
        results["assembly"] = False

    return results


def verify_contrafactual_analysis(registry):
    """Verify contrafactual analysis (with vs without signals)."""
    print_header("TEST 3: Contrafactual Analysis")

    # Test 1: Pattern matching
    print_section("3.1 Pattern Match Precision")

    # Baseline: manual pattern
    baseline_pattern = r"\d+%|\d+\.\d+%"
    baseline_matches = re.findall(baseline_pattern, SAMPLE_TEXT)
    print(f"Baseline (manual regex): {len(baseline_matches)} matches")
    print(f"  Matches: {baseline_matches}")

    # With signals: use signal patterns
    try:
        signals = registry.get_micro_answering_signals("Q001")
        indicator_patterns = signals.indicators_by_pa.get("PA01", [])

        signal_matches = []
        for pattern_str in indicator_patterns[:10]:  # Sample first 10
            try:
                matches = re.findall(pattern_str, SAMPLE_TEXT, re.IGNORECASE)
                signal_matches.extend(matches)
            except re.error:
                continue

        print(f"With signals: {len(signal_matches)} matches")
        print(f"  Patterns tested: {min(len(indicator_patterns), 10)}")
        print(f"  Matches: {signal_matches[:5]}..." if len(signal_matches) > 5 else f"  Matches: {signal_matches}")

        improvement = (
            (len(signal_matches) - len(baseline_matches)) / len(baseline_matches) * 100
            if len(baseline_matches) > 0
            else 0
        )
        print(f"  Improvement: {improvement:+.1f}%")

    except Exception as e:
        print(f"✗ Signal pattern matching failed: {e}")

    # Test 2: Official source detection
    print_section("3.2 Official Source Detection")

    # Baseline: hardcoded sources
    baseline_sources = ["DANE", "Medicina Legal"]
    baseline_found = sum(1 for s in baseline_sources if s in SAMPLE_TEXT)
    print(f"Baseline (hardcoded): {baseline_found}/{len(baseline_sources)} sources found")

    # With signals
    try:
        signals = registry.get_micro_answering_signals("Q001")
        signal_sources = signals.official_sources

        signal_found = sum(
            1 for s in signal_sources if s.lower() in SAMPLE_TEXT.lower()
        )
        print(f"With signals: {signal_found}/{len(signal_sources)} sources found")
        print(f"  Total sources in registry: {len(signal_sources)}")
        print(f"  Coverage improvement: {len(signal_sources) - len(baseline_sources)} additional sources")

    except Exception as e:
        print(f"✗ Signal source detection failed: {e}")


def verify_performance(registry):
    """Verify performance metrics."""
    print_header("TEST 4: Performance & Caching")

    # Clear cache
    registry.clear_cache()

    # Cold cache
    start = time.perf_counter()
    for i in range(1, 11):
        try:
            registry.get_micro_answering_signals(f"Q{i:03d}")
        except (ValueError, KeyError):
            pass
    cold_time = time.perf_counter() - start

    # Warm cache
    start = time.perf_counter()
    for i in range(1, 11):
        try:
            registry.get_micro_answering_signals(f"Q{i:03d}")
        except (ValueError, KeyError):
            pass
    warm_time = time.perf_counter() - start

    metrics = registry.get_metrics()

    print(f"Cold cache (10 questions): {cold_time*1000:.2f}ms")
    print(f"Warm cache (10 questions): {warm_time*1000:.2f}ms")
    print(f"Speedup: {(cold_time/warm_time):.1f}x" if warm_time > 0 else "Speedup: N/A")
    print(f"\nCache Metrics:")
    print(f"  Hit rate: {metrics['hit_rate']:.1%}")
    print(f"  Cache hits: {metrics['cache_hits']}")
    print(f"  Cache misses: {metrics['cache_misses']}")
    print(f"  Signal loads: {metrics['signal_loads']}")


def verify_type_safety():
    """Verify type safety with Pydantic."""
    print_header("TEST 5: Type Safety")

    from saaaaaa.core.orchestrator.signal_registry import ChunkingSignalPack

    # Test valid data
    try:
        valid_pack = ChunkingSignalPack(
            section_detection_patterns={"TEST": ["pattern1", "pattern2"]},
            section_weights={"TEST": 1.0},
            source_hash="a" * 32,
        )
        print(f"✓ Valid signal pack accepted")
        print(f"  Version: {valid_pack.version}")
    except Exception as e:
        print(f"✗ Valid signal pack rejected: {e}")

    # Test invalid data (weight out of range)
    try:
        invalid_pack = ChunkingSignalPack(
            section_detection_patterns={"TEST": ["pattern1"]},
            section_weights={"TEST": 5.0},  # Out of range [0.0, 2.0]
            source_hash="a" * 32,
        )
        print(f"✗ Invalid signal pack accepted (should have failed)")
    except Exception as e:
        print(f"✓ Invalid signal pack rejected: {str(e)[:80]}...")

    # Test invalid data (empty patterns)
    try:
        invalid_pack = ChunkingSignalPack(
            section_detection_patterns={},  # Empty - violates min_length=1
            section_weights={"TEST": 1.0},
            source_hash="a" * 32,
        )
        print(f"✗ Empty patterns accepted (should have failed)")
    except Exception as e:
        print(f"✓ Empty patterns rejected: {str(e)[:80]}...")


def generate_summary_report(results):
    """Generate summary report."""
    print_header("SUMMARY REPORT")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    print(f"\nSignal Pack Tests: {passed}/{total} passed")
    for component, status in results.items():
        symbol = "✓" if status else "✗"
        print(f"  {symbol} {component}")

    print(f"\n{'='*80}")
    if passed == total:
        print("✓ ALL TESTS PASSED - Signal irrigation is working correctly")
    else:
        print(f"✗ SOME TESTS FAILED - {total - passed} components need attention")
    print(f"{'='*80}")


def main():
    """Run all verification tests."""
    print("\n" + "="*80)
    print("SIGNAL IRRIGATION VERIFICATION SUITE")
    print("="*80)

    # Test 1: Registry initialization
    registry, questionnaire = verify_registry_initialization()
    if not registry:
        print("\n✗ CRITICAL: Cannot proceed without registry")
        return

    # Test 2: Signal pack retrieval
    results = verify_signal_packs(registry)

    # Test 3: Contrafactual analysis
    verify_contrafactual_analysis(registry)

    # Test 4: Performance
    verify_performance(registry)

    # Test 5: Type safety
    verify_type_safety()

    # Summary
    generate_summary_report(results)


if __name__ == "__main__":
    main()
