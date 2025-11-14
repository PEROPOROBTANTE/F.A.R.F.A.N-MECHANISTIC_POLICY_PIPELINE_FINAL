# Canonical Executor Catalog

## Descripción

Este archivo JSON (`canonical_executor_catalog.json`) contiene el catálogo canónico completo de los 30 executors del sistema F.A.R.F.A.N Mechanistic Policy Pipeline, con sus secuencias de métodos, flujos de ejecución y metadata asociada.

## Ubicación

```
/home/user/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE/config/canonical_executor_catalog.json
```

## Estructura del Catálogo

### 1. Metadata

Información general del catálogo:
- **version**: 1.0.0
- **created**: 2025-11-13
- **total_executors**: 30 (D1-Q1 a D6-Q5)
- **total_questions**: 300 preguntas totales mapeadas a 30 base slots
- **dimensions**: 6 dimensiones de análisis
- **total_policy_areas**: 10 áreas de política

#### Archivos Core (files)

9 módulos principales identificados con códigos:
- **PP**: policy_processor.py (3 clases)
- **CD**: contradiction_detection.py (3 clases)
- **FV**: financiero_viabilidad_tablas.py (2 clases)
- **DB**: derek_beach.py (7 clases)
- **RA**: report_assembly.py (1 clase)
- **EP**: embedding_policy.py (2 clases)
- **A1**: Analyzer_one.py (4 clases)
- **TC**: teoria_cambio.py (2 clases)
- **SC**: semantic_chunking_policy.py (1 clase)

#### Tipos de Métodos (types)

- **E**: Extracción
- **V**: Validación
- **T**: Transformación
- **C**: Cálculo
- **O**: Orquestación
- **R**: Reporte

#### Prioridades (priority)

- **3**: ★ Crítico
- **2**: ◆ Importante
- **1**: ○ Complementario

### 2. Dimensions

6 dimensiones con sus configuraciones:

```json
{
  "D1": {
    "code": "DIM01",
    "name": "INSUMOS",
    "label": "Diagnóstico y Recursos",
    "total_executors": 5,
    "questions": ["D1-Q1", "D1-Q2", "D1-Q3", "D1-Q4", "D1-Q5"],
    "total_methods": 15
  }
}
```

**Dimensiones completas:**
- D1 (INSUMOS): Diagnóstico y Recursos - 15 métodos
- D2 (ACTIVIDADES): Diseño de Intervención - 15 métodos
- D3 (PRODUCTOS): Productos y Outputs - 14 métodos
- D4 (RESULTADOS): Resultados y Outcomes - 16 métodos
- D5 (IMPACTOS): Impactos de Largo Plazo - 15 métodos
- D6 (CAUSALIDAD): Teoría de Cambio - 17 métodos

### 3. Policy Areas

10 áreas de política (PA01-PA10) con sus nombres canónicos según el sistema colombiano de derechos humanos.

### 4. Special Features

#### Sistema Bicameral de Validación
- **Ruta 1** (D6-Q3): Detección local de contradicciones
- **Ruta 2** (D6-Q4): Inferencia estructural de mejoras

#### Validación Anti-Milagro (D6-Q2)
Patrones de validación de proporcionalidad y continuidad causal:
- enlaces_proporcionales
- sin_saltos
- no_milagros

4 métodos clave para validar coherencia causal.

#### Derek Beach Tests
4 tipos de tests evidenciales:
- **Hoop Test**: Necesario pero NO suficiente
- **Smoking Gun Test**: Suficiente pero NO necesario
- **Doubly Decisive Test**: Necesario Y suficiente
- **Straw in Wind Test**: Ni necesario ni suficiente

### 5. Executors

Array de 30 executors con la siguiente estructura:

```json
{
  "q": "D1-Q1",
  "qid": "Q001",
  "t": "¿El diagnóstico presenta datos numéricos...",
  "m": 15,
  "flow": "PP.E → SC.T → EP.C → CD.V → A1.T",
  "p": [
    {
      "f": "PP",
      "c": "IndustrialPolicyProcessor",
      "m": ["process", "_match_patterns_in_sentences", ...],
      "t": ["E", "E", ...],
      "pr": [3, 3, ...],
      "note": "Procesamiento y extracción principal"
    }
  ]
}
```

#### Campos del Executor

- **q**: Base slot (D1-Q1 a D6-Q5)
- **qid**: Question ID (Q001-Q030)
- **t**: Texto completo de la pregunta
- **m**: Número total de métodos
- **flow**: Flujo simplificado de ejecución
- **p**: Array de packages (módulos)

#### Campos de cada Package

- **f**: File code (PP, CD, FV, etc.)
- **c**: Class name
- **m**: Array de nombres de métodos
- **t**: Array de tipos de métodos (E/V/T/C/O/R)
- **pr**: Array de prioridades (1/2/3)
- **note**: Nota descriptiva del package

## Estadísticas del Catálogo

### Distribución de Métodos

- **Total de métodos**: 460 llamadas de método
- **Promedio por executor**: 15.3 métodos
- **Rango**: 14-17 métodos por executor

### Por Tipo de Método

- **Extracción (E)**: 155 métodos (33.7%)
- **Validación (V)**: 150 métodos (32.6%)
- **Cálculo (C)**: 70 métodos (15.2%)
- **Transformación (T)**: 50 métodos (10.9%)
- **Reporte (R)**: 35 métodos (7.6%)
- **Orquestación (O)**: 0 métodos (0.0%)

### Por Dimensión

- D1: 75 métodos totales (5 executors)
- D2: 75 métodos totales (5 executors)
- D3: 70 métodos totales (5 executors)
- D4: 80 métodos totales (5 executors)
- D5: 75 métodos totales (5 executors)
- D6: 85 métodos totales (5 executors)

## Patrones de Flujo por Dimensión

Cada dimensión tiene un patrón característico de flujo:

1. **D1 (INSUMOS)**: `PP.E → SC.T → EP.C → CD.V → A1.T`
   - Extracción → Segmentación → Embeddings → Validación → Análisis

2. **D2 (ACTIVIDADES)**: `PP.E → SC.T → A1.T → CD.V → TC.V`
   - Extracción → Segmentación → Análisis → Validación → Teoría

3. **D3 (PRODUCTOS)**: `PP.E → EP.C → FV.T → CD.V → RA.R`
   - Extracción → Cálculo → Viabilidad → Validación → Reporte

4. **D4 (RESULTADOS)**: `PP.E → TC.T → DB.C → CD.V → RA.R`
   - Extracción → Teoría → Beach Tests → Validación → Reporte

5. **D5 (IMPACTOS)**: `PP.E → TC.T → DB.C → EP.C → RA.R`
   - Extracción → Teoría → Causal → Bayesiano → Reporte

6. **D6 (CAUSALIDAD)**: `TC.T → DB.C → CD.V → FV.C → RA.R`
   - Teoría → Beach Tests → Validación → DAG → Reporte

## Uso del Catálogo

### Lectura en Python

```python
import json

with open('config/canonical_executor_catalog.json', 'r', encoding='utf-8') as f:
    catalog = json.load(f)

# Acceder a metadata
print(f"Version: {catalog['metadata']['version']}")
print(f"Total executors: {catalog['metadata']['total_executors']}")

# Obtener un executor específico
d1q1 = [e for e in catalog['executors'] if e['q'] == 'D1-Q1'][0]
print(f"D1-Q1 tiene {d1q1['m']} métodos")

# Iterar por dimensiones
for dim_key, dim_info in catalog['dimensions'].items():
    print(f"{dim_key}: {dim_info['name']} - {dim_info['total_methods']} métodos")

# Acceder a special features
bicameral = catalog['special_features']['bicameral_system']
print(f"Bicameral: {bicameral['description']}")
```

### Consultas Comunes

#### 1. Obtener todos los executors de una dimensión

```python
d6_executors = [e for e in catalog['executors'] if e['q'].startswith('D6')]
```

#### 2. Contar métodos por tipo en un executor

```python
from collections import Counter

executor = catalog['executors'][0]
type_counts = Counter()
for pkg in executor['p']:
    type_counts.update(pkg['t'])
```

#### 3. Listar métodos críticos (prioridad 3)

```python
critical_methods = []
for executor in catalog['executors']:
    for pkg in executor['p']:
        for method, priority in zip(pkg['m'], pkg['pr']):
            if priority == 3:
                critical_methods.append(f"{pkg['f']}.{pkg['c']}.{method}")
```

## Validación

El catálogo ha sido validado con las siguientes comprobaciones:

- ✅ 30 executors definidos (D1-Q1 a D6-Q5)
- ✅ Cada dimensión tiene exactamente 5 executors
- ✅ Todos los executors tienen secuencias de métodos
- ✅ Todos los executors están vinculados a preguntas Q001-Q030
- ✅ Patrones de flujo definidos para cada dimensión
- ✅ Tipos y prioridades asignados a cada método
- ✅ Special features documentados
- ✅ Policy areas integradas desde notación canónica

## Changelog

### v1.0.0 (2025-11-13)
- Creación inicial del catálogo canónico
- 30 executors con secuencias completas
- 9 archivos core identificados
- 3 special features documentados
- 460 métodos catalogados

## Notas Técnicas

1. **Determinismo**: Las secuencias de métodos están ordenadas para garantizar ejecución determinista.

2. **Prioridades**: Los métodos de prioridad 3 (críticos) son esenciales para la correcta ejecución del pipeline.

3. **Validación Anti-Milagro**: D6-Q2 es el executor clave para prevenir saltos causales ilógicos.

4. **Sistema Bicameral**: D6-Q3 y D6-Q4 trabajan en conjunto para detectar y corregir contradicciones.

5. **Derek Beach Tests**: Implementados en D4, D5 y D6 para validación de evidencia causal.

## Referencias

- Documentación del sistema: README.md
- Questionnaire monolith: data/questionnaire_monolith.json
- Archivos core: src/saaaaaa/processing/ y src/saaaaaa/analysis/
- Policy areas: config/canonical_ontologies/policy_areas_and_dimensions.json

## Contacto

Para preguntas o actualizaciones sobre este catálogo, consultar la documentación principal del proyecto F.A.R.F.A.N.
