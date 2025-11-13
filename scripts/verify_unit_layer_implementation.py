"""
Verify Unit Layer is actually implemented (not a stub).

This script MUST pass before proceeding to executor integration.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from saaaaaa.core.calibration import UnitLayerEvaluator, UnitLayerConfig
from saaaaaa.core.calibration.pdt_structure import PDTStructure


def test_unit_layer_not_stub():
    """Verify Unit Layer doesn't return hardcoded values."""

    # Create a complete PDT (should get high score)
    pdt1 = PDTStructure(
        full_text="test1",
        total_tokens=5000,
        blocks_found={
            "Diagnóstico": {"tokens": 500, "numbers_count": 15},
            "Parte Estratégica": {"tokens": 400, "numbers_count": 12},
            "PPI": {"tokens": 300, "numbers_count": 20},
            "Seguimiento": {"tokens": 200, "numbers_count": 10}
        },
        headers=[
            {"level": 1, "text": "1. DIAGNÓSTICO", "valid_numbering": True},
            {"level": 1, "text": "2. PARTE ESTRATÉGICA", "valid_numbering": True},
            {"level": 1, "text": "3. PPI", "valid_numbering": True}
        ],
        block_sequence=["Diagnóstico", "Parte Estratégica", "PPI", "Seguimiento"],
        sections_found={
            "Diagnóstico": {
                "present": True,
                "token_count": 500,
                "keyword_matches": 5,
                "number_count": 15,
                "sources_found": 3
            },
            "Parte Estratégica": {
                "present": True,
                "token_count": 400,
                "keyword_matches": 4,
                "number_count": 12,
                "sources_found": 0
            },
            "PPI": {
                "present": True,
                "token_count": 300,
                "keyword_matches": 3,
                "number_count": 20,
                "sources_found": 0
            },
            "Seguimiento": {
                "present": True,
                "token_count": 200,
                "keyword_matches": 2,
                "number_count": 10,
                "sources_found": 0
            }
        },
        indicator_matrix_present=True,
        indicator_rows=[
            {
                "Tipo": "PRODUCTO",
                "Línea Estratégica": "Equidad",
                "Programa": "Equidad Social",
                "Línea Base": "100",
                "Año LB": 2023,
                "Meta Cuatrienio": "150",
                "Fuente": "DANE",
                "Unidad Medida": "Personas",
                "Código MGA": "1234567"
            },
            {
                "Tipo": "RESULTADO",
                "Línea Estratégica": "Salud",
                "Programa": "Salud Pública",
                "Línea Base": "85",
                "Año LB": 2023,
                "Meta Cuatrienio": "95",
                "Fuente": "Secretaría Salud",
                "Unidad Medida": "Porcentaje",
                "Código MGA": "7654321"
            }
        ],
        ppi_matrix_present=True,
        ppi_rows=[
            {
                "Línea Estratégica": "Equidad",
                "Programa": "Equidad Social",
                "Costo Total": 1000000,
                "2024": 250000,
                "2025": 250000,
                "2026": 250000,
                "2027": 250000,
                "SGP": 600000,
                "SGR": 0,
                "Propios": 400000,
                "Otras": 0
            }
        ]
    )

    # Create a minimal PDT (will get score of 0.0 due to missing required matrices - hard gates)
    pdt2 = PDTStructure(
        full_text="test2",
        total_tokens=1000,
        blocks_found={
            "Diagnóstico": {"tokens": 150, "numbers_count": 5}
        },
        headers=[
            {"level": 1, "text": "DIAGNÓSTICO", "valid_numbering": False}
        ],
        block_sequence=["Diagnóstico"],
        sections_found={
            "Diagnóstico": {
                "present": True,
                "token_count": 150,
                "keyword_matches": 1,
                "number_count": 5,
                "sources_found": 1
            }
        },
        indicator_matrix_present=False,
        indicator_rows=[],
        ppi_matrix_present=False,
        ppi_rows=[]
    )
    
    evaluator = UnitLayerEvaluator(UnitLayerConfig())
    
    score1 = evaluator.evaluate(pdt1)
    score2 = evaluator.evaluate(pdt2)
    
    # Scores MUST be different for different PDTs
    if score1.score == score2.score:
        print(f"❌ FAIL: Unit Layer returns same score for different PDTs")
        print(f"   Score 1: {score1.score}")
        print(f"   Score 2: {score2.score}")
        print(f"   This indicates a STUB implementation!")
        return False
    
    # Score MUST NOT be exactly 0.75 (old stub value)
    if score1.score == 0.75:
        print(f"❌ FAIL: Unit Layer returns hardcoded 0.75")
        print(f"   This is the old stub value!")
        return False
    
    # Metadata MUST NOT have "stub": True
    if score1.metadata.get("stub"):
        print(f"❌ FAIL: Unit Layer metadata still shows stub=True")
        return False
    
    print(f"✅ PASS: Unit Layer is data-driven")
    print(f"   Score 1: {score1.score:.3f} (components: {score1.components})")
    print(f"   Score 2: {score2.score:.3f}")
    return True


if __name__ == "__main__":
    success = test_unit_layer_not_stub()
    sys.exit(0 if success else 1)
