# Informe de Auditoría de Agregación: Verificación y Análisis

**DEPRECATED (2025-11-17)** – Este documento se conserva únicamente como historial.
La referencia vigente para la Fase de Agregación es `docs/aggregation_phase_canonical.md`.

**Fecha:** 2025-11-17

## Resumen Ejecutivo

Este informe detalla el análisis y la verificación de los hallazgos relacionados con el sistema de agregación identificados en el informe de auditoría técnica integral con fecha de `2025-11-06`. Cada hallazgo ha sido sometido a un proceso de doble verificación para confirmar su validez, identificar la "prueba reina" en el código y proponer acciones de remediación claras y pragmáticas.

## Hallazgos Verificados

### 1. AGGREG-041: Falta de validación de columnas (Severidad: ALTA)

**Confirmación:** **Válido.**

**Análisis:**
El informe original indica que "la agregación debería fallar si faltan las columnas requeridas". El término "columnas" se interpreta como los campos de los objetos de datos de entrada, principalmente `ScoredResult`.

Actualmente, el código utiliza `dataclasses` para los modelos de datos como `ScoredResult`. Si bien esto proporciona validación de tipo en el momento de la instanciación del objeto, no hay un mecanismo de validación proactivo que se ejecute *antes* del proceso de agregación. Si los datos de entrada se construyen incorrectamente (por ejemplo, a partir de un diccionario con claves faltantes), se produciría un `TypeError` en el momento de la creación del `dataclass`, pero el sistema de agregación en sí mismo no valida la integridad de sus entradas.

**Prueba Reina (Evidencia):**
La clase `ScoredResult` se define como un `dataclass` simple, sin validación de entrada personalizada. La validación depende completamente del comportamiento predeterminado de los `dataclasses`.

*Ubicación:* `src/saaaaaa/processing/aggregation.py`
```python
@dataclass
class ScoredResult:
    """Scored result for a micro question."""
    question_global: int
    base_slot: str
    policy_area: str
    dimension: str
    score: float
    quality_level: str
    evidence: dict[str, Any]
    raw_results: dict[str, Any]
```

**Impacto:**
La falta de una validación de entrada explícita hace que el sistema de agregación sea frágil. Datos de entrada malformados pueden causar fallos en tiempo de ejecución que son difíciles de depurar, ya que el error ocurrirá en lo profundo de la lógica de agregación en lugar de en el borde del sistema, donde los datos son recibidos.

**Acción de Remediación Propuesta:**
Implementar una función de validación de "pre-vuelo" que itere sobre la lista de `ScoredResult` de entrada y verifique la presencia y el tipo de todos los campos requeridos antes de pasarlos a las clases `Aggregator`. Esta función debería generar un `ValidationError` claro y conciso si los datos no son válidos.

### 2. AGGREG-039, AGGREG-042, AGGREG-043: Falta de especificación `group_by` (Severidad: MEDIA)

**Confirmación:** **Válido.**

**Análisis:**
El informe indica que la agregación debería tener claves `group_by` explícitas. Este hallazgo es correcto en los tres archivos mencionados. La lógica de agrupación está actualmente codificada mediante filtros de comprensión de listas, lo que la hace rígida y difícil de mantener.

**Prueba Reina (Evidencia):**
La agrupación de resultados para una dimensión específica se realiza con un filtro codificado, en lugar de un mecanismo de agrupación configurable.

*Ubicación:* `src/saaaaaa/processing/aggregation.py`
```python
# Filter results for this dimension/area
dim_results = [
    r for r in scored_results
    if r.dimension == dimension_id and r.policy_area == area_id
]
```

Del mismo modo, los modelos de configuración en `aggregation_models.py` carecen de cualquier campo para especificar por qué claves agrupar.

*Ubicación:* `src/saaaaaa/utils/validation/aggregation_models.py`
```python
class DimensionAggregationConfig(BaseModel):
    """Configuration for dimension-level aggregation."""
    model_config = ConfigDict(frozen=True, extra='forbid')
    dimension_id: str = Field(..., pattern=r'^DIM\d{2}$')
    area_id: str = Field(..., pattern=r'^PA\d{2}$')
    weights: AggregationWeights | None = None
    expected_question_count: int = Field(default=5, ge=1, le=10)
```

**Impacto:**
La lógica de agrupación codificada viola el principio de Abierto/Cerrado. Si los criterios de agregación cambian (por ejemplo, si se necesita agrupar por una nueva propiedad), se requiere una modificación directa del código en múltiples lugares, lo que aumenta el riesgo de introducir errores.

**Acción de Remediación Propuesta:**
1.  Añadir un campo `group_by_keys: list[str]` a los modelos de Pydantic relevantes en `src/saaaaaa/utils/validation/aggregation_models.py`.
2.  Refactorizar los métodos `aggregate_*` en `src/saaaaaa/processing/aggregation.py` para usar una función de agrupación genérica que utilice las `group_by_keys` para agrupar los datos de forma dinámica. Esto centralizará la lógica de agrupación y la hará configurable.

### 3. AGGREG-040: Falta de definiciones de pesos (Severidad: MEDIA)

**Confirmación:** **Válido.**

**Análisis:**
El informe afirma que la agregación debería tener definiciones de pesos explícitas. Si bien `DimensionAggregator` y `ClusterAggregator` aceptan pesos opcionales, `AreaPolicyAggregator` no lo hace y, en su lugar, calcula un promedio simple de las puntuaciones de las dimensiones.

**Prueba Reina (Evidencia):**
`AreaPolicyAggregator.aggregate_area` calcula directamente el promedio de las puntuaciones, sin opción para aplicar pesos.

*Ubicación:* `src/saaaaaa/processing/aggregation.py`
```python
# Calculate average score
avg_score = sum(d.score for d in area_dim_scores) / len(area_dim_scores)
```
Esto contrasta con `DimensionAggregator`, que sí maneja pesos.

**Impacto:**
La incapacidad de ponderar las puntuaciones de las dimensiones al calcular la puntuación de un área de política limita la flexibilidad del modelo de puntuación. Ciertas dimensiones pueden ser más importantes que otras en un área de política determinada, y el modelo de agregación actual no puede reflejar esta matiz.

**Acción de Remediación Propuesta:**
1.  Modificar la firma del método `AreaPolicyAggregator.aggregate_area` para aceptar un parámetro `weights: list[float] | None = None`.
2.  Implementar una lógica para calcular un promedio ponderado si se proporcionan pesos, similar a la que ya existe en `DimensionAggregator.calculate_weighted_average`.
3.  Actualizar el modelo Pydantic `AreaAggregationConfig` en `src/saaaaaa/utils/validation/aggregation_models.py` para incluir un campo opcional `weights: AggregationWeights | None = None`.
