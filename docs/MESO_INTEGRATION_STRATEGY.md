# 🎯 ESTRATEGIA DE INTEGRACIÓN MESO

## ANÁLISIS DE ESTADO ACTUAL

### Archivos Existentes (INMUTABLES - NO RECREAR)

**1. cuestionario_FIXED.json** (~25K líneas)
```
Top-level: metadata, dimensiones, puntos_decalogo, preguntas_base, 
           common_failure_patterns, scoring_system, causal_glossary
- 300 preguntas con IDs: P#-D#-Q# (ej: P1-D1-Q1)
- 10 puntos del Decálogo (P1-P10)
- 6 dimensiones (D1-D6)
- Indicadores empíricos por punto
- Umbrales por dimensión
- Patrones de verificación
```

**2. rubric_scoring_FIXED.json** (~11K líneas)
```
Top-level: metadata, scoring_modalities, aggregation_levels, score_bands,
           dimensions, questions, thematic_points, validation_rules
- TYPE_A through TYPE_F modalities
- 4 aggregation levels (Question→Dimension→Point→Global)
- Score bands (EXCELENTE, BUENO, SATISFACTORIO, INSUFICIENTE, DEFICIENTE)
```

### Agregación Actual (4 niveles)

```
Level 1: Question Score (0-3 points)
    ↓
Level 2: Dimension Score (0-100%, 5 questions → 1 dimension)
    ↓
Level 3: Point Score (0-100%, 6 dimensions → 1 thematic point)
    ↓
Level 4: Global Score (0-100%, 10 points → overall)
```

---

## 🔧 INSERCIÓN DE MESO (SIN PERTURBACIÓN)

### Nueva Agregación (5 niveles)

```
Level 1: Question Score (MICRO) - 0-3 points
    ↓
Level 2: Dimension Score - 0-100%
    ↓
Level 3: Point Score (Policy Area) - 0-100%
    ↓ ⭐ NUEVO: MESO CLUSTER LAYER
Level 3.5: Cluster Score (MESO) - 0-100%
    ↓
Level 4: Global Score (MACRO) - 0-100%
```

### MESO = 4 Clusters Inmutables

```
CL01 (Seguridad y Paz): PA02, PA03, PA07
CL02 (Grupos Poblacionales): PA01, PA05, PA06  
CL03 (Territorio-Ambiente): PA04, PA08
CL04 (Derechos Sociales & Crisis): PA09, PA10
```

**Mapeo PA (Policy Area) ↔ P# (Punto Decálogo):**
- PA01 = P1 (Mujeres e igualdad)
- PA02 = P2 (Violencia y conflicto)
- PA03 = P3 (Ambiente y desastres)
- PA04 = P4 (Tierras y territorios)
- PA05 = P5 (Niñez y familia)
- PA06 = P6 (Personas privadas libertad)
- PA07 = P7 (Líderes DD.HH.)
- PA08 = P8 (Migración)
- PA09 = P9 (Víctimas y paz)
- PA10 = P10 (DESC)

---

## 📝 MODIFICACIONES PRECISAS

### 1. Extender cuestionario_FIXED.json

**Agregar a `metadata`:**
```json
"metadata": {
  // ... existing fields ...
  "meso_enabled": true,
  "clusters": [
    {
      "cluster_id": "CL01",
      "name": "Seguridad y Paz",
      "rationale": "Seguridad humana, protección de la vida y paz territorial",
      "policy_area_ids": ["PA02", "PA03", "PA07"],
      "legacy_point_ids": ["P2", "P3", "P7"]
    },
    // ... CL02, CL03, CL04
  ],
  "policy_area_mapping": {
    "PA01": "P1", "PA02": "P2", "PA03": "P3", "PA04": "P4", "PA05": "P5",
    "PA06": "P6", "PA07": "P7", "PA08": "P8", "PA09": "P9", "PA10": "P10"
  }
}
```

**Ubicación:** Insertar después de línea ~20 en metadata section

### 2. Extender rubric_scoring_FIXED.json

**Agregar nuevo nivel en `aggregation_levels`:**
```json
"aggregation_levels": {
  "level_1": { /* existing */ },
  "level_2": { /* existing */ },
  "level_3": { /* existing */ },
  "level_3_5_meso": {
    "name": "Cluster Score (MESO)",
    "range": [0.0, 100.0],
    "unit": "percentage",
    "precision": 1,
    "formula": "weighted_average(point_scores_in_cluster)",
    "description": "Aggregate of policy areas into subsystem clusters"
  },
  "level_4": { /* existing */ }
}
```

**Agregar sección `meso_clusters`:**
```json
"meso_clusters": {
  "CL01": {
    "cluster_id": "CL01",
    "name": "Seguridad y Paz",
    "policy_area_ids": ["PA02", "PA03", "PA07"],
    "weights": {"PA02": 0.40, "PA03": 0.35, "PA07": 0.25},
    "imbalance_threshold": 30.0,
    "aggregation_method": "weighted_average"
  },
  "CL02": {
    "cluster_id": "CL02",
    "name": "Grupos Poblacionales",
    "policy_area_ids": ["PA01", "PA05", "PA06"],
    "weights": {"PA01": 0.40, "PA05": 0.35, "PA06": 0.25},
    "imbalance_threshold": 30.0,
    "aggregation_method": "weighted_average"
  },
  "CL03": {
    "cluster_id": "CL03",
    "name": "Territorio-Ambiente",
    "policy_area_ids": ["PA04", "PA08"],
    "weights": {"PA04": 0.55, "PA08": 0.45},
    "imbalance_threshold": 25.0,
    "aggregation_method": "weighted_average"
  },
  "CL04": {
    "cluster_id": "CL04",
    "name": "Derechos Sociales & Crisis",
    "policy_area_ids": ["PA09", "PA10"],
    "weights": {"PA09": 0.50, "PA10": 0.50},
    "imbalance_threshold": 25.0,
    "aggregation_method": "weighted_average"
  }
}
```

**Actualizar level_4 formula:**
```json
"level_4": {
  "name": "Global Score",
  "range": [0.0, 100.0],
  "unit": "percentage",
  "precision": 1,
  "formula": "weighted_average(cluster_scores)",  // CHANGED
  "cluster_weights": {
    "CL01": 0.30,
    "CL02": 0.25,
    "CL03": 0.25,
    "CL04": 0.20
  },
  "exclude_na": true,
  "description": "Aggregate of MESO clusters to macro score"
}
```

---

## 🔄 INTEGRACIÓN EN CÓDIGO

### Choreographer.py

**Nuevos métodos a agregar (NO modificar existentes):**

```python
def aggregate_questions_to_policy_area(
    self, 
    question_results: Dict[str, float],
    policy_area_id: str,
    dimension_weights: Dict[str, float]
) -> Dict[str, Any]:
    """Q→PA aggregation"""
    pass

def aggregate_policy_areas_to_cluster(
    self,
    policy_area_scores: Dict[str, float],
    cluster_id: str,
    weights: Dict[str, float],
    imbalance_threshold: float
) -> Dict[str, Any]:
    """PA→CL aggregation with imbalance detection"""
    pass

def calculate_cluster_imbalance(
    self,
    policy_area_scores: Dict[str, float]
) -> Dict[str, float]:
    """Calculate range, std_dev, Gini for imbalance detection"""
    pass
```

### Orchestrator.py

**Modificar `_generate_meso_clusters()` para:**
1. Leer cluster definitions desde cuestionario metadata
2. Agregar PA scores usando rubric weights
3. Calcular métricas de desbalance
4. Retornar MesoLevelCluster con imbalance flags

**NO modificar:**
- _execute_opening()
- _execute_middle_game()
- Existing CHESS strategy logic

---

## ⚠️ REGLAS DE NO-PERTURBACIÓN

### ✅ PERMITIDO:
- Agregar nuevas secciones a metadata
- Agregar nuevos niveles de agregación
- Agregar nuevos métodos a clases existentes
- Extender dataclasses con nuevos campos opcionales

### ❌ PROHIBIDO:
- Cambiar IDs de preguntas existentes (P#-D#-Q#)
- Modificar fórmulas de niveles 1-3
- Cambiar scoring modalities (TYPE_A-F)
- Alterar estructura de preguntas_base
- Renombrar campos existentes

---

## 📊 VALIDACIÓN

### Schema Validation

1. Validate cuestionario_FIXED.json contra questionnaire.schema.json
2. Validate rubric_scoring_FIXED.json contra rubric_scoring.schema.json
3. Verificar:
   - Todos los P# en clusters existen en puntos_decalogo
   - Suma de weights en cada cluster = 1.0
   - No hay P# huérfanos (todos mapeados a un cluster)

### Integration Tests

1. Cargar ambos JSONs sin errores
2. Extraer metadata de clusters
3. Ejecutar agregación Q→PA→CL→Macro
4. Verificar idempotencia (mismo input = mismo output)
5. Verificar detección de desbalances

---

## 🚀 SECUENCIA DE EJECUCIÓN

1. ✅ **Crear schemas** (questionnaire.schema.json, rubric_scoring.schema.json)
2. ✅ **Crear schema_validator.py**
3. ✅ **Crear docs/taxonomia_meso.md**
4. ⏭️ **Extender cuestionario_FIXED.json** (agregar clusters a metadata)
5. ⏭️ **Extender rubric_scoring_FIXED.json** (agregar meso_clusters y level_3_5)
6. ⏭️ **Validar con schemas**
7. ⏭️ **Actualizar Orchestrator** (_define_clusters, _generate_meso_clusters)
8. ⏭️ **Actualizar Choreographer** (agregar métodos de agregación MESO)
9. ⏭️ **Actualizar ReportAssembler** (consumir clusters desde metadata)
10. ⏭️ **Tests de integración**
11. ⏭️ **Generar trace.json** con checksums y provenance

---

## 📍 PUNTOS DE INVOCACIÓN

### Startup (Orchestrator.__init__)
```python
# Validate schemas
from schema_validator import SchemaValidator
validator = SchemaValidator()
q_report, r_report = validator.validate_all(
    "cuestionario_FIXED.json",
    "rubric_scoring_FIXED.json"
)
if not (q_report.is_valid and r_report.is_valid):
    raise ValueError("Schema validation failed")
```

### Cluster Definition (Orchestrator._define_clusters)
```python
# Load from metadata instead of hardcoding
clusters_metadata = self.questionnaire["metadata"]["clusters"]
self.clusters = [
    ClusterDefinition(
        cluster_id=c["cluster_id"],
        cluster_name=c["name"],
        description=c["rationale"],
        policy_areas=c["policy_area_ids"],
        dimensions=["D1","D2","D3","D4","D5","D6"],
        question_ids=self._get_questions_for_cluster(c["policy_area_ids"])
    )
    for c in clusters_metadata
]
```

### MESO Aggregation (Orchestrator._generate_meso_clusters)
```python
# Get cluster config from rubric
cluster_config = self.rubric["meso_clusters"][cluster_id]

# Aggregate PA scores with weights
pa_scores = {pa_id: self._get_pa_score(pa_id) for pa_id in cluster_config["policy_areas"]}
weighted_score = sum(
    pa_scores[pa_id] * cluster_config["weights"][pa_id]
    for pa_id in pa_scores.keys()
)

# Calculate imbalance
imbalance_metrics = self._calculate_imbalance(pa_scores)
is_high_imbalance = imbalance_metrics["range"] >= cluster_config["imbalance_threshold"]
```

---

**STATUS:** Ready for precise implementation  
**NEXT:** Apply exact modifications to cuestionario_FIXED.json and rubric_scoring_FIXED.json
