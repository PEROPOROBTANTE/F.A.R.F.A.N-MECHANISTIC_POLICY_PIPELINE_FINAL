# P01-ES v2.0: Contrato de Ejecución Estricta para la Ingestión SPC (Fase 1)

## 1. Resumen Ejecutivo

Este documento especifica la arquitectura y los contratos inmutables del **Nodo Canónico N1 (Fase 1)** del pipeline F.A.R.F.A.N. El nodo N1 ha sido refactorizado para operar bajo un **Contrato de Ejecución Estricta (Peso: 10000)**, garantizando cero ambigüedad y determinismo total.

**Misión Crítica**: Transformar un `CanonicalInput` en un `CanonPolicyPackage` (CPP) que contenga **EXACTAMENTE 60 Smart Policy Chunks (SPC)**, distribuidos en una matriz perfecta de 10 Áreas de Política × 6 Dimensiones. Cualquier desviación resulta en la terminación inmediata del pipeline.

## 2. Especificación del Contrato (Full Contract)

### 2.1. Matriz PA×DIM (60 Chunks)

El sistema debe producir una cobertura completa de la siguiente matriz:

| Dimensiones (6) | PA01 | PA02 | PA03 | PA04 | PA05 | PA06 | PA07 | PA08 | PA09 | PA10 |
|---|---|---|---|---|---|---|---|---|---|---|
| **DIM01** (Insumos) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **DIM02** (Actividades) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **DIM03** (Productos) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **DIM04** (Resultados) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **DIM05** (Impactos) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **DIM06** (Causalidad) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

**Total**: 60 Chunks Obligatorios.

### 2.2. Arquitectura de 16 Subfases

El procesamiento sigue una secuencia estricta de 16 subfases (SP0-SP15):

1.  **SP0 - Language Detection**: Validación de idioma (ES).
2.  **SP1 - Advanced Preprocessing**: Normalización Unicode NFC.
3.  **SP2 - Structural Analysis**: Descomposición jerárquica.
4.  **SP3 - Knowledge Graph**: Construcción de grafo base.
5.  **SP4 - PA×DIM Segmentation** [CRÍTICO]: Generación de la matriz de 60 chunks.
6.  **SP5 - Causal Chain Extraction**: Identificación de cadenas causales.
7.  **SP6 - Causal Integration**: Fusión de grafos causales.
8.  **SP7 - Argumentative Analysis**: Extracción de argumentos.
9.  **SP8 - Temporal Analysis**: Marcadores temporales.
10. **SP9 - Discourse Analysis**: Modos discursivos.
11. **SP10 - Strategic Integration**: Fusión estratégica.
12. **SP11 - Smart Chunk Generation** [CRÍTICO]: Creación de objetos SmartChunk.
13. **SP12 - Inter-Chunk Enrichment**: Irrigación de señales.
14. **SP13 - Integrity Validation** [CRÍTICO]: Verificación de invariantes.
15. **SP14 - Deduplication**: Limpieza final.
16. **SP15 - Strategic Ranking**: Ordenamiento final.

## 3. Visualización del Sistema (Dashboard ATROZ)

### 3.1. Flujo de Control (Execution Trace)

El siguiente diagrama muestra la secuencia de ejecución estricta y los puntos de fallo crítico.

![Control Flow](images/control_flow.png)

### 3.2. Especificación de la Matriz PA×DIM

Visualización de la estructura de datos obligatoria de 60 celdas.

![PAxDIM Grid](images/padim_grid.png)

### 3.3. Estados de Ejecución

Transiciones de estado permitidas durante la ejecución del contrato.

![State Transition](images/state_transition.png)

### 3.4. Vinculación de Contratos

Relación entre los contratos de entrada, ejecución y salida.

![Contract Linkage](images/contract_linkage.png)

## 4. Invariantes y Manejo de Fallos

El sistema opera bajo una política de **"Fallo Ruidoso" (Loud Failure)**. No existe recuperación parcial.

```python
class Phase1FatalError(Exception):
    """Error fatal irrecuperable en Fase 1."""
    pass
```

**Invariantes Verificados:**
1.  `chunk_count == 60`
2.  `subphases_executed == 16`
3.  `pa_dim_coverage == "COMPLETE"`
4.  `execution_trace` completo y verificado criptográficamente.

## 5. Gestión de Cambios

- **v2.0**: Refactorización completa a Contrato de Ejecución Estricta (16 subfases, 60 chunks).
- **v1.0**: Versión legacy (deprecada).
