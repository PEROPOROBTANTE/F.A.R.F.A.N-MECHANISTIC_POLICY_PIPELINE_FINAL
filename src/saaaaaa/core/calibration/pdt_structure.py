"""
PDT (Plan de Desarrollo Territorial) structure definition.

This module defines the data structure that represents a parsed PDT.
The PDT is the INPUT to the Unit Layer evaluation.

The structure is populated by a separate PDT parser (not shown here),
which extracts:
- Text content and tokens
- Block structure (Diagnóstico, Estratégica, PPI, Seguimiento)
- Section analysis (keywords, numbers, sources)
- Indicator matrix (if present)
- PPI matrix (if present)
"""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PDTStructure:
    """
    Extracted structure of a PDT.
    
    This is populated by the PDT parser and consumed by UnitLayerEvaluator.
    
    Attributes:
        full_text: Complete text of the PDT
        total_tokens: Total word/token count
        blocks_found: Detected structural blocks
        headers: List of headers with numbering validation
        block_sequence: Actual order of blocks (for checking sequence)
        sections_found: Analysis of mandatory sections
        indicator_matrix_present: Whether indicator table was found
        indicator_rows: Parsed indicator table rows
        ppi_matrix_present: Whether PPI table was found
        ppi_rows: Parsed PPI table rows
    """
    # Raw content
    full_text: str
    total_tokens: int
    
    # Block detection (for S - Structural compliance)
    blocks_found: dict[str, dict[str, Any]] = field(default_factory=dict)
    # Example: {
    #     "Diagnóstico": {"text": "...", "tokens": 1500, "numbers_count": 25},
    #     "Parte Estratégica": {"text": "...", "tokens": 1200, "numbers_count": 15},
    # }
    
    headers: list[dict[str, Any]] = field(default_factory=list)
    # Example: [
    #     {"level": 1, "text": "1. DIAGNÓSTICO", "valid_numbering": True},
    #     {"level": 2, "text": "1.1 Contexto", "valid_numbering": True},
    # ]
    
    block_sequence: list[str] = field(default_factory=list)
    # Example: ["Diagnóstico", "Parte Estratégica", "PPI", "Seguimiento"]
    
    # Section analysis (for M - Mandatory sections)
    sections_found: dict[str, dict[str, Any]] = field(default_factory=dict)
    # Example: {
    #     "Diagnóstico": {
    #         "present": True,
    #         "token_count": 1500,
    #         "keyword_matches": 5,  # e.g., "brecha", "DANE", "línea base"
    #         "number_count": 25,
    #         "sources_found": 3,  # e.g., "DANE", "Medicina Legal"
    #     }
    # }
    
    # Indicator matrix (for I - Indicator quality)
    indicator_matrix_present: bool = False
    indicator_rows: list[dict[str, Any]] = field(default_factory=list)
    # Example: [
    #     {
    #         "Tipo": "PRODUCTO",
    #         "Línea Estratégica": "Equidad de Género",
    #         "Programa": "Prevención de VBG",
    #         "Línea Base": "120 casos",
    #         "Año LB": 2023,
    #         "Meta Cuatrienio": "80 casos",
    #         "Fuente": "Comisaría de Familia",
    #         "Unidad Medida": "Casos reportados",
    #         "Código MGA": "1234567"
    #     }
    # ]
    
    # PPI matrix (for P - PPI completeness)
    ppi_matrix_present: bool = False
    ppi_rows: list[dict[str, Any]] = field(default_factory=list)
    # Example: [
    #     {
    #         "Línea Estratégica": "Equidad de Género",
    #         "Programa": "Prevención de VBG",
    #         "Costo Total": 500000000,
    #         "2024": 100000000,
    #         "2025": 150000000,
    #         "2026": 150000000,
    #         "2027": 100000000,
    #         "SGP": 300000000,
    #         "SGR": 0,
    #         "Propios": 200000000,
    #         "Otras": 0
    #     }
    # ]
