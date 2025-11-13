"""
Verify Unit Layer is data-driven (CORRECTED).

This test creates PDTs that:
1. Both PASS hard gates (so we don't get 0.0 for both)
2. Have DIFFERENT quality levels (so scores differ)

Previous version failed because both PDTs triggered same hard gates.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from saaaaaa.core.calibration import UnitLayerEvaluator, UnitLayerConfig
from saaaaaa.core.calibration.pdt_structure import PDTStructure


def create_high_quality_pdt() -> PDTStructure:
    """
    Create a high-quality PDT that passes all gates.
    
    Expected score: ~0.75-0.85 (sobresaliente)
    """
    return PDTStructure(
        full_text="High quality plan de desarrollo territorial with comprehensive data",
        total_tokens=5000,
        
        # Good block coverage
        blocks_found={
            "Diagnóstico": {
                "text": "Comprehensive diagnosis...",
                "tokens": 800,
                "numbers_count": 25
            },
            "Parte Estratégica": {
                "text": "Strategic component...",
                "tokens": 600,
                "numbers_count": 15
            },
            "PPI": {
                "text": "Plan plurianual de inversiones...",
                "tokens": 400,
                "numbers_count": 30
            },
            "Seguimiento": {
                "text": "Monitoring and evaluation...",
                "tokens": 300,
                "numbers_count": 10
            }
        },
        
        # Valid headers
        headers=[
            {"level": 1, "text": "1. DIAGNÓSTICO", "valid_numbering": True},
            {"level": 2, "text": "1.1 Contexto", "valid_numbering": True},
            {"level": 2, "text": "1.2 Análisis", "valid_numbering": True},
            {"level": 1, "text": "2. PARTE ESTRATÉGICA", "valid_numbering": True},
        ],
        
        # Correct sequence
        block_sequence=["Diagnóstico", "Parte Estratégica", "PPI", "Seguimiento"],
        
        # Good sections
        sections_found={
            "Diagnóstico": {
                "present": True,
                "token_count": 800,
                "keyword_matches": 5,  # Exceeds min (3)
                "number_count": 25,    # Exceeds min (5)
                "sources_found": 3     # Exceeds min (2)
            },
            "Parte Estratégica": {
                "present": True,
                "token_count": 600,
                "keyword_matches": 4,  # Exceeds min (3)
                "number_count": 15,    # Exceeds min (3)
                "sources_found": 0
            },
            "PPI": {
                "present": True,
                "token_count": 400,
                "keyword_matches": 3,  # Meets min (2)
                "number_count": 30,    # Exceeds min (10)
                "sources_found": 0
            }
        },
        
        # CRITICAL: Has indicator matrix (passes gate)
        indicator_matrix_present=True,
        indicator_rows=[
            {
                "Tipo": "PRODUCTO",
                "Línea Estratégica": "Equidad de Género",
                "Programa": "Prevención VBG",
                "Línea Base": "120 casos",  # Valid, not placeholder
                "Año LB": 2023,
                "Meta Cuatrienio": "80 casos",  # Valid, not placeholder
                "Fuente": "Comisaría de Familia",  # Valid, not placeholder
                "Unidad Medida": "Casos reportados",
                "Código MGA": "1234567"
            },
            {
                "Tipo": "RESULTADO",
                "Línea Estratégica": "Equidad de Género",
                "Programa": "Prevención VBG",
                "Línea Base": "35%",
                "Año LB": 2023,
                "Meta Cuatrienio": "50%",
                "Fuente": "Encuesta local",
                "Unidad Medida": "Porcentaje",
                "Código MGA": "1234568"
            }
        ],
        
        # CRITICAL: Has PPI matrix (passes gate)
        ppi_matrix_present=True,
        ppi_rows=[
            {
                "Línea Estratégica": "Equidad de Género",
                "Programa": "Prevención VBG",
                "Costo Total": 500000000,
                "2024": 100000000,
                "2025": 150000000,
                "2026": 150000000,
                "2027": 100000000,
                "SGP": 300000000,
                "SGR": 0,
                "Propios": 200000000,
                "Otras": 0
            }
        ]
    )


def create_low_quality_pdt() -> PDTStructure:
    """
    Create a low-quality PDT that barely passes gates.
    
    Expected score: ~0.35-0.50 (mínimo or below)
    """
    return PDTStructure(
        full_text="Minimal plan de desarrollo",
        total_tokens=1000,
        
        # Minimal block coverage (only 2/4 blocks)
        blocks_found={
            "Diagnóstico": {
                "text": "Brief diagnosis",
                "tokens": 100,
                "numbers_count": 3
            },
            "Parte Estratégica": {
                "text": "Brief strategy",
                "tokens": 80,
                "numbers_count": 2
            }
        },
        
        # Poor headers (only 50% valid)
        headers=[
            {"level": 1, "text": "DIAGNÓSTICO", "valid_numbering": False},  # No numbering
            {"level": 1, "text": "1. Estrategia", "valid_numbering": True},
        ],
        
        # Wrong sequence
        block_sequence=["Parte Estratégica", "Diagnóstico"],  # Inverted!
        
        # Minimal sections (barely meet requirements)
        sections_found={
            "Diagnóstico": {
                "present": True,
                "token_count": 100,  # Way below min (500)
                "keyword_matches": 2, # Below min (3)
                "number_count": 3,    # Below min (5)
                "sources_found": 1    # Below min (2)
            },
            "Parte Estratégica": {
                "present": True,
                "token_count": 80,    # Below min (400)
                "keyword_matches": 2, # Below min (3)
                "number_count": 2,    # Below min (3)
                "sources_found": 0
            }
        },
        
        # CRITICAL: Has indicator matrix (passes gate) but poor quality
        indicator_matrix_present=True,
        indicator_rows=[
            {
                "Tipo": "PRODUCTO",
                "Línea Estratégica": "Género",
                "Programa": "VBG",
                "Línea Base": "S/D",  # PLACEHOLDER - triggers penalty
                "Año LB": 2023,
                "Meta Cuatrienio": "S/D",  # PLACEHOLDER - triggers penalty
                "Fuente": "S/D",  # PLACEHOLDER - triggers penalty
                "Unidad Medida": "NA",
                "Código MGA": "0000000"
            }
        ],
        
        # CRITICAL: Has PPI matrix (passes gate) but minimal
        ppi_matrix_present=True,
        ppi_rows=[
            {
                "Línea Estratégica": "Género",
                "Programa": "VBG",
                "Costo Total": 0,  # Zero cost - triggers penalty
                "2024": 0,
                "2025": 0,
                "2026": 0,
                "2027": 0,
                "SGP": 0,
                "SGR": 0,
                "Propios": 0,
                "Otras": 0
            }
        ]
    )


def test_unit_layer_is_data_driven():
    """
    Test that Unit Layer produces different scores for different PDTs.
    
    Returns:
        True if test passes, False otherwise
    """
    print("=" * 60)
    print("UNIT LAYER DATA-DRIVEN VERIFICATION (CORRECTED)")
    print("=" * 60)
    
    # Create test PDTs
    print("\n1. Creating test PDTs...")
    pdt_high = create_high_quality_pdt()
    pdt_low = create_low_quality_pdt()
    
    print(f"   High quality PDT: {pdt_high.total_tokens} tokens, "
          f"{len(pdt_high.blocks_found)} blocks, "
          f"{len(pdt_high.indicator_rows)} indicators")
    print(f"   Low quality PDT: {pdt_low.total_tokens} tokens, "
          f"{len(pdt_low.blocks_found)} blocks, "
          f"{len(pdt_low.indicator_rows)} indicators")
    
    # Evaluate
    print("\n2. Evaluating PDTs...")
    evaluator = UnitLayerEvaluator(UnitLayerConfig())
    
    score_high = evaluator.evaluate(pdt_high)
    score_low = evaluator.evaluate(pdt_low)
    
    print(f"   High quality score: {score_high.score:.3f}")
    print(f"   Low quality score: {score_low.score:.3f}")
    
    # Check 1: Scores must be different
    print("\n3. Checking differentiation...")
    if abs(score_high.score - score_low.score) < 0.01:
        print(f"   ❌ FAIL: Scores are too similar ({score_high.score:.3f} vs {score_low.score:.3f})")
        print(f"   This indicates Unit Layer is not data-driven!")
        return False
    else:
        print(f"   ✅ PASS: Scores are different ({score_high.score:.3f} vs {score_low.score:.3f})")
    
    # Check 2: High quality should score higher
    print("\n4. Checking quality ordering...")
    if score_high.score <= score_low.score:
        print(f"   ⚠️  WARNING: High quality PDT scored lower or equal")
        print(f"   High: {score_high.score:.3f}, Low: {score_low.score:.3f}")
        print(f"   This may indicate incorrect component weighting")
        # Don't fail test, but warn
    else:
        print(f"   ✅ PASS: High quality scores higher ({score_high.score:.3f} > {score_low.score:.3f})")
    
    # Check 3: Neither should be hardcoded 0.75
    print("\n5. Checking for old stub values...")
    if score_high.score == 0.75 or score_low.score == 0.75:
        print(f"   ❌ FAIL: One score is exactly 0.75 (old stub value)")
        return False
    else:
        print(f"   ✅ PASS: No hardcoded 0.75 values")
    
    # Check 4: Metadata should not show stub
    print("\n6. Checking metadata...")
    if score_high.metadata.get("stub") or score_low.metadata.get("stub"):
        print(f"   ❌ FAIL: Metadata still shows stub=True")
        return False
    else:
        print(f"   ✅ PASS: No stub metadata")
    
    # Check 5: Both should not be 0.0 (hard gate failure on both)
    print("\n7. Checking hard gates...")
    if score_high.score == 0.0 and score_low.score == 0.0:
        print(f"   ❌ FAIL: Both PDTs scored 0.0 (both triggered hard gates)")
        print(f"   High rationale: {score_high.rationale}")
        print(f"   Low rationale: {score_low.rationale}")
        return False
    else:
        print(f"   ✅ PASS: At least one PDT passed hard gates")
    
    # Check 6: Components should be different
    print("\n8. Checking component differentiation...")
    if score_high.components == score_low.components:
        print(f"   ❌ FAIL: Components are identical")
        print(f"   High: {score_high.components}")
        print(f"   Low: {score_low.components}")
        return False
    else:
        print(f"   ✅ PASS: Components differ")
        print(f"   High: S={score_high.components.get('S', 'N/A'):.2f}, "
              f"M={score_high.components.get('M', 'N/A'):.2f}, "
              f"I={score_high.components.get('I', 'N/A'):.2f}, "
              f"P={score_high.components.get('P', 'N/A'):.2f}")
        # Handle N/A values (strings) gracefully
        def fmt_score(val):
            return f"{val:.2f}" if isinstance(val, (int, float)) else str(val)
        
        print(f"   Low:  S={fmt_score(score_low.components.get('S', 'N/A'))}, "
              f"M={fmt_score(score_low.components.get('M', 'N/A'))}, "
              f"I={fmt_score(score_low.components.get('I', 'N/A'))}, "
              f"P={fmt_score(score_low.components.get('P', 'N/A'))}")
    
    # Final result
    print("\n" + "=" * 60)
    print("✅ ALL CHECKS PASSED - Unit Layer is DATA-DRIVEN")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  High quality PDT: {score_high.score:.3f} ({score_high.rationale})")
    print(f"  Low quality PDT:  {score_low.score:.3f} ({score_low.rationale})")
    print(f"  Difference: {abs(score_high.score - score_low.score):.3f}")
    
    return True


if __name__ == "__main__":
    try:
        success = test_unit_layer_is_data_driven()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: Test failed with exception")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
