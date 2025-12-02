"""
Core type definitions shared across layers.

This module contains types that need to be referenced by both core and analysis
layers without creating circular dependencies.
"""
from enum import Enum


class CategoriaCausal(Enum):
    """
    Jerarquía axiomática de categorías causales en una teoría de cambio.
    El orden numérico impone la secuencia lógica obligatoria.

    Originally from farfan_core.analysis.teoria_cambio, moved here to break
    architectural dependency (core should not import from analysis).
    """

    INSUMOS = 1
    ACTIVIDADES = 2
    PRODUCTOS = 3
    RESULTADOS = 4
    CAUSALIDAD = 5
