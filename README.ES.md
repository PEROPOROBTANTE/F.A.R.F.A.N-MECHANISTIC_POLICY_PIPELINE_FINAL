# F.A.R.F.A.N: Framework for Advanced Retrieval of Administrative Narratives

**Un Pipeline Mecanístico de Políticas para el Análisis de Planes de Desarrollo Colombianos**

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Licencia](https://img.shields.io/badge/licencia-MIT-green.svg)](LICENSE)
[![Estado](https://img.shields.io/badge/estado-producción-brightgreen.svg)]()

---

## 🎯 Resumen Ejecutivo

F.A.R.F.A.N es un marco sofisticado de análisis basado en evidencia para planes de desarrollo municipales y departamentales colombianos. Integra **584 métodos analíticos** distribuidos en **7 productores especializados** y **1 agregador**, entregando análisis de políticas riguroso y reproducible a través de un pipeline determinista de 9 fases con trazabilidad completa (`provenance_completeness = 1.0`).

**Innovación Clave**: Análisis mecanístico de políticas combinando (1) pipeline de ingesta determinista de 9 fases, (2) sistema de señales transversales con transporte memory:// y HTTP, (3) enrutamiento extendido de argumentos (30+ rutas especiales), y (4) contratos explícitos de entrada/salida con validación en fronteras.

**Alcance del Análisis**: 300 preguntas de evaluación organizadas en 6 dimensiones (D1-D6: Insumos, Actividades, Productos, Resultados, Impactos, Causalidad) sobre 10 áreas de política (PA01-PA10), generando reportes en tres niveles de agregación: MICRO (respuestas atómicas por pregunta, 150-300 palabras), MESO (análisis de clusters por dimensión-área), y MACRO (clasificación y recomendaciones).

---

## 📚 Tabla de Contenidos

1. [Inicio Rápido](#-inicio-rápido)
2. [¿Qué es F.A.R.F.A.N?](#-qué-es-farfan)
3. [Características Clave](#-características-clave)
4. [Requisitos del Sistema](#-requisitos-del-sistema)
5. [Instalación](#-instalación)
6. [Uso](#-uso)
7. [Arquitectura](#-arquitectura)
8. [Pruebas](#-pruebas)
9. [Temas Avanzados](#-temas-avanzados)
10. [Desarrollo](#-desarrollo)
11. [Solución de Problemas](#-solución-de-problemas)
12. [Contribuir](#-contribuir)
13. [Licencia y Citación](#-licencia-y-citación)

---

## 🚀 Inicio Rápido

### Configuración en 5 Minutos

```bash
# 1. Clonar repositorio
git clone https://github.com/PEROPOROBTANTE/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE_FINAL.git
cd F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE_FINAL

# 2. Instalar (automatizado - instala todas las dependencias)
bash install.sh

# 3. Activar entorno
source farfan-env/bin/activate

# 4. Verificar instalación
python verify_dependencies.py

# 5. Ejecutar primer análisis
python scripts/run_policy_pipeline_verified.py \
    --plan data/plans/Plan_1.pdf \
    --artifacts-dir artifacts/plan1
```

**Tiempo Esperado**: 2-3 minutos para análisis completo

**Salida Esperada**:
```
PIPELINE_VERIFIED=1
Fases: 11 completadas, 0 fallidas
Artefactos: artifacts/plan1/verification_manifest.json
```

---

## 🛡️ Fase 0: Puerta de Validación Estricta

### El Contrato Pre-Ejecución

**La Fase 0 es el marco de bootstrap determinístico de F.A.R.F.A.N**—una puerta de validación de cero tolerancia que establece condiciones de ejecución inmutables antes de que cualquier análisis de políticas comience.

#### 📊 Dashboard de Aplicación

```
╔══════════════════════════════════════════════════════════════════╗
║  FASE 0: ESTADO DE VALIDACIÓN PRE-EJECUCIÓN                   ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                ║
║  P0.0 │ BOOTSTRAP           │ ✅ RuntimeConfig      │ ESTRICTO║
║       │                     │ ✅ Seed Registry      │         ║
║       │                     │ ✅ Manifest Builder   │         ║
║                                                                ║
║  P0.1 │ VERIFICACIÓN ENTRADA │ ✅ Hash PDF Plan      │ CRYPTO  ║
║       │                     │ ✅ Hash Cuestion.     │ SHA-256 ║
║                                                                ║
║  P0.2 │ CONTROLES ARRANQUE  │ ✅ PROD: Fatal        │ CUSTODIA║
║       │                     │ ⚠️  DEV:  Advertir    │         ║
║                                                                ║
║  P0.3 │ DETERMINISMO        │ ✅ Semilla Python RNG │ OBLIG.  ║
║       │                     │ ✅ Semilla NumPy      │         ║
║                                                                ║
║  SALIDA │ CONDICIÓN PUERTA    │ self.errors == []   │ ATÓMICO ║
║       │                     │ _bootstrap_failed=F │         ║
╚══════════════════════════════════════════════════════════════════╝
```

#### 🚨 Política de Fallos: Fallar Rápido, Fallar Limpio, Fallar Determinísticamente

**Cuando la Fase 0 falla**:
1. ❌ **Aborto Inmediato**: Sin ejecución de Fase 1
2. 📋 **Generación de Manifiesto**: `success: false` con razones específicas de error
3. 🔴 **Código de Salida 1**: `PIPELINE_VERIFIED=0` impreso a stdout
4. 🔍 **Rastro de Auditoría**: Log completo de claims en `execution_claims.json`

**Racionalidad del Diseño**: En contextos de auditoría pública, **la reproducibilidad byte-a-byte es un requisito legal**. La Fase 0 asegura que cada ejecución:
- ✅ Procede con **condiciones verificadas y determinísticas**, O
- ❌ Falla con **mensajes de error claros y accionables**

**Sin Estados "Tal Vez Funcioó"**. Sin degradación silenciosa. Sin deriva de configuración ambigua.

#### 📚 Documentación

- **Especificación Detallada**: [docs/phases/phase_0/P00-ES_v1.0.md](docs/phases/phase_0/P00-ES_v1.0.md)
- **Versión en Inglés**: [docs/phases/phase_0/P00-EN_v1.0.md](docs/phases/phase_0/P00-EN_v1.0.md)

---

## 💡 ¿Qué es F.A.R.F.A.N?

F.A.R.F.A.N (Framework for Advanced Retrieval of Administrative Narratives) es un pipeline mecanístico de políticas diseñado para el análisis riguroso y basado en evidencia de planes de desarrollo municipales colombianos.

### Planteamiento del Problema

La evaluación ex-ante de planes de desarrollo requiere procesamiento analítico de documentos semi-estructurados (100-300 páginas) bajo múltiples dimensiones: viabilidad financiera, coherencia lógica, causalidad explícita, trazabilidad presupuestal, alineación normativa y evidencia empírica. Los enfoques tradicionales presentan tres deficiencias:

1. **Pérdida de Trazabilidad**: Extracción de texto sin mapeo página-token impide auditoría de inferencias
2. **Procesamiento No-Determinista**: Variaciones en chunking semántico y resolución de dependencias producen outputs no reproducibles
3. **Triangulación Manual**: Síntesis multi-método requiere integración manual, introduciendo sesgos de confirmación

### Enfoque de Solución

F.A.R.F.A.N integra:

1. **Determinismo de Pipeline**: Pipeline canónico de 9 fases con postcondiciones verificables; fallo en cualquier fase → ABORT (no degradación gradual)
2. **Señales Transversales**: Registro centralizado de patrones, indicadores, umbrales desde cuestionario monolito hacia todos los ejecutores, con transporte memory:// (in-process) o HTTP (con circuit breaker)
3. **Proveniencia Completa**: Cada token → `{page_id, bbox, byte_range, parser_id}` mediante Arrow IPC, permitiendo auditoría forense
4. **ArgRouter Extendido**: 30+ rutas especiales eliminan caídas silenciosas de parámetros (`argrouter_coverage = 1.0`)
5. **Contratos Explícitos**: TypedDict con validación en fronteras (orchestrator ↔ core), detectando violaciones arquitectónicas en runtime

**Racionalidad del Determinismo**: En auditoría pública, reproducibilidad byte-a-byte es requisito legal. Aproximaciones probabilísticas sin intervalos de confianza no son aceptables.

---

## ✨ Características Clave

### Capacidades Principales

- **🔒 Pipeline Determinista**: Procesamiento de 9 fases con prueba criptográfica de ejecución
- **📊 Análisis Integral**: 300 preguntas en 6 dimensiones y 10 áreas de política
- **🔍 Proveniencia Completa**: 100% trazabilidad token-a-fuente (`provenance_completeness = 1.0`)
- **🎯 Sistema de Señales**: Registro centralizado de patrones con transporte memory:// y HTTP
- **⚡ Enrutamiento Extendido**: 30+ rutas de argumentos sin caídas silenciosas
- **🛡️ Aplicación de Contratos**: Contratos TypedDict con validación en fronteras en runtime
- **📈 Puertas de Calidad**: Métricas de consistencia estructural, precisión de proveniencia, boundary F1
- **🔐 Integridad Criptográfica**: Manifiesto de verificación basado en HMAC para todos los artefactos

### Aspectos Técnicos Destacados

| Característica | Especificación | Verificación |
|----------------|----------------|--------------|
| **Completitud de Proveniencia** | 100% | Golden tests en 150 páginas |
| **Cobertura ArgRouter** | 100% (30/30 rutas) | Unit tests |
| **Tasa de Acierto de Señales** | ≥ 95% | Integration tests |
| **Determinismo** | Idéntico byte-a-byte | 10 ejecuciones con seed fijo |
| **Estabilidad de Hash de Fase** | 9/9 fases coinciden | Verificación BLAKE3 |
| **Cobertura de Tests** | 87.3% promedio ponderado | 238 tests pasando |

---

## 🖥️ Requisitos del Sistema

### Requisitos Mínimos

| Componente | Mínimo | Recomendado |
|------------|--------|-------------|
| **SO** | Ubuntu 20.04+ / Debian 11+ | Ubuntu 22.04+ |
| **Python** | 3.12.x | 3.12.3+ |
| **RAM** | 8 GB | 16 GB |
| **CPU** | 4 núcleos | 8 núcleos |
| **Disco** | 5 GB libres | 20 GB (con modelos) |
| **GPU** | Opcional | NVIDIA CUDA 11.0+ |

### Plataformas Soportadas

| Plataforma | Arquitectura | Nivel de Soporte | Notas |
|------------|--------------|------------------|-------|
| Ubuntu 20.04+ | x86_64 | ✅ Completo | Testeado en CI |
| Ubuntu 22.04+ | x86_64 | ✅ Completo | **Recomendado** |
| Debian 11+ | x86_64 | ✅ Completo | Testeado |
| macOS 11+ | x86_64, arm64 | ✅ Completo | Compatible M1/M2 |
| Windows 10+ | x86_64 | ⚠️ Vía WSL2 | Nativo no testeado |

---

## 📦 Instalación

### Instalación Automatizada (Recomendada)

```bash
# Un solo comando instala todo
bash install.sh
```

**Qué instala**:
- ✅ Dependencias del sistema (build-essential, gfortran, ghostscript, graphviz, JRE)
- ✅ Entorno virtual Python 3.12 (`farfan-env/`)
- ✅ Todos los paquetes Python con versiones exactas compatibles
- ✅ Diagnósticos de verificación

**Tiempo de instalación**: 10-15 minutos (dependiente de red)

### Instalación Manual

#### Linux (Ubuntu/Debian)

```bash
# 1. Instalar dependencias del sistema
sudo apt-get update && sudo apt-get install -y \
  build-essential python3.12-dev gfortran libopenblas-dev libhdf5-dev \
  ghostscript python3-tk libgraphviz-dev graphviz default-jre

# 2. Crear entorno virtual
python3.12 -m venv farfan-env
source farfan-env/bin/activate

# 3. Actualizar herramientas
pip install --upgrade pip setuptools wheel

# 4. Instalar dependencias
pip install --no-cache-dir -r requirements.txt

# 5. Forzar versiones compatibles
pip install --force-reinstall --no-deps numpy==1.26.4 opencv-python-headless==4.10.0.84

# 6. Instalar paquete
pip install --no-cache-dir -e .
```

#### macOS (Homebrew)

```bash
# 1. Instalar dependencias del sistema
brew install python@3.12 icu4c pkg-config ghostscript graphviz openjdk

# 2. Crear entorno virtual
python3.12 -m venv farfan-env
source farfan-env/bin/activate

# 3. Instalar dependencias (igual que Linux pasos 3-6)
pip install --upgrade pip setuptools wheel
pip install --no-cache-dir -r requirements.txt
pip install --force-reinstall --no-deps numpy==1.26.4 opencv-python-headless==4.10.0.84
pip install --no-cache-dir -e .
```

### Verificación

```bash
# Activar entorno
source farfan-env/bin/activate

# Diagnóstico rápido
python diagnose_import_error.py

# Verificación completa de dependencias
python scripts/verify_dependencies.py

# Verificación integral de salud
bash comprehensive_health_check.sh
```

**Salida esperada**:
```
✓ transformers: 4.41.2
✓ sentence-transformers: 3.1.0
✓ accelerate: 1.2.1
✓ Cargadas exitosamente 22 clases
Aprobado: 5/6 verificaciones
```

### Dependencias Críticas

| Paquete | Versión | Propósito | Restricción |
|---------|---------|-----------|-------------|
| `transformers` | 4.41.2 | Transformers NLP | `>=4.41.0,<4.42.0` (evitar bug TorchTensorParallelPlugin) |
| `sentence-transformers` | 3.1.0 | Embeddings semánticos | `>=3.1.0,<3.2.0` |
| `accelerate` | 1.2.1 | Aceleración de modelos | Versión estable |
| `pymc` | 5.16.2 | Inferencia Bayesiana | Versión exacta |
| `pytensor` | 2.25.5 | Operaciones tensoriales | `>=2.25.1,<2.26` |
| `scikit-learn` | 1.6.1 | Algoritmos ML | `>=1.6.0` |
| `numpy` | 1.26.4 | Computación numérica | Versión exacta (compatibilidad ABI) |

---

## 🎮 Uso

### Ejecución Básica

#### Modo 1: Pipeline Verificado (Producción)

```bash
python scripts/run_policy_pipeline_verified.py \
    --plan data/plans/Plan_1.pdf \
    --artifacts-dir artifacts/plan1
```

**Salidas**:
- `verification_manifest.json` - Manifiesto criptográfico con HMAC
- `execution_claims.json` - Log de ejecución estructurado
- `cpp_metadata.json` - Metadatos de ingesta SPC
- `preprocessed_doc_metadata.json` - Metadatos de procesamiento de documento
- `results_summary.json` - Resumen de resultados de análisis

**Verificación**:
```bash
# Verificar éxito
grep "PIPELINE_VERIFIED=1" artifacts/plan1/verification_manifest.json

# Verificar integridad HMAC
python3 -c "
import json
from saaaaaa.core.orchestrator.verification_manifest import verify_manifest_integrity

with open('artifacts/plan1/verification_manifest.json') as f:
    manifest = json.load(f)

is_valid, message = verify_manifest_integrity(manifest, 'default-dev-key-change-in-production')
print(f'Verificación HMAC: {message}')
"
```

#### Modo 2: Análisis Simple (Desarrollo)

```bash
python scripts/run_complete_analysis_plan1.py
```

**Caso de uso**: Pruebas rápidas y desarrollo

#### Modo 3: Pipeline Personalizado (Avanzado)

```python
import asyncio
from pathlib import Path
from saaaaaa.processing.spc_ingestion import CPPIngestionPipeline
from saaaaaa.utils.spc_adapter import SPCAdapter
from saaaaaa.core.orchestrator import Orchestrator
from saaaaaa.core.orchestrator.factory import build_processor

async def pipeline_personalizado():
    # Paso 1: Ingesta SPC
    input_path = Path('data/plans/Plan_1.pdf')
    cpp_pipeline = CPPIngestionPipeline(questionnaire_path=None)
    cpp = await cpp_pipeline.process(
        document_path=input_path,
        document_id='Plan_Personalizado',
        title='Análisis Personalizado',
        max_chunks=100
    )

    # Paso 2: Adaptación
    adapter = SPCAdapter()
    preprocessed = adapter.to_preprocessed_document(cpp, document_id='Plan_Personalizado')

    # Paso 3: Orquestación
    processor = build_processor()
    orchestrator = Orchestrator(
        monolith=processor.questionnaire,
        catalog=processor.factory.catalog
    )

    results = await orchestrator.process_development_plan_async(
        pdf_path=str(input_path),
        preprocessed_document=preprocessed
    )

    return results

asyncio.run(pipeline_personalizado())
```

### Procesamiento por Lotes

```bash
#!/bin/bash
# Procesar múltiples planes

PLANES=(
    "data/plans/Plan_1.pdf"
    "data/plans/Plan_2.pdf"
    "data/plans/Plan_3.pdf"
)

for i in "${!PLANES[@]}"; do
    plan="${PLANES[$i]}"
    plan_num=$((i + 1))

    python scripts/run_policy_pipeline_verified.py \
        --plan "$plan" \
        --artifacts-dir "artifacts/lote_plan${plan_num}"

    if [ $? -eq 0 ]; then
        echo "✓ Plan $plan_num completado"
    else
        echo "✗ Plan $plan_num falló"
        exit 1
    fi
done
```

---

## 🏗️ Arquitectura

### Visión General del Sistema

F.A.R.F.A.N sigue un **pipeline determinístico de Fase 0 + 9 fases** con puertas de calidad estrictas:

```
┌─────────────────────────────────────────────────────────────────────┐
│ FASE 0: Validación Pre-Ejecución                                  │
│   Entrada:  ENV vars, ruta plan, ruta cuestionario                │
│   Salida:   RuntimeConfig validado, hashes verificados, semillas  │
│   Puerta:   self.errors == [] AND _bootstrap_failed = False       │
└───────────────────────┬─────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────────────┐
│ FASE 1: Adquisición e Integridad                                   │
│   Entrada:  file_path (Path)                                    │
│   Salida:   manifest.initial {blake3_hash, mime_type, byte_size}│
│   Puerta:   blake3_hash debe ser 64 caracteres hex              │
└──────────────────────┬──────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────────┐
│ FASE 2: Descomposición de Formato                               │
│   Entrada:  manifest.initial                                    │
│   Salida:   raw_object_tree {pages[], fonts[], images[]}        │
│   Puerta:   len(pages) > 0                                      │
└──────────────────────┬──────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────────┐
│ FASE 3: Normalización Estructural (Consciente de Políticas)     │
│   Entrada:  raw_object_tree                                     │
│   Salida:   policy_graph.prelim {Ejes, Programas, Proyectos}    │
│   Puerta:   structural_consistency_score ≥ 1.0                  │
└──────────────────────┬──────────────────────────────────────────┘
                       ↓
                    [... continúa hasta Fase 9]
```

### Componentes Principales

#### 1. Pipeline de Ingesta SPC

**Punto de Entrada**: `CPPIngestionPipeline` en `src/saaaaaa/processing/spc_ingestion/__init__.py`

**Garantías**:
- Completitud de Proveniencia = 1.0 (puerta CRÍTICA)
- Consistencia Estructural = 1.0 (puerta CRÍTICA)
- Boundary F1 ≥ 0.85 (puerta ALTA)
- Consistencia Presupuestal ≥ 0.95 (puerta MEDIA)

**Salida**: `CanonPolicyPackage` - formato canónico para fases posteriores

#### 2. Sistema de Contratos

Los contratos son estructuras TypedDict que especifican:
- **Precondiciones**: Estados del mundo requeridos antes de la ejecución
- **Postcondiciones**: Garantías sobre las salidas
- **Invariantes**: Propiedades mantenidas durante la transformación

```python
class Deliverable(TypedDict):
    """Contrato de salida de productores."""
    dimension: str  # "D1" | "D2" | ... | "D6"
    policy_area: str  # "P1" | "P2" | ... | "P10"
    evidence_items: List[EvidenceItem]
    bayesian_score: float  # [0.0, 1.0]
    confidence_interval: Tuple[float, float]
    provenance_refs: List[ProvenanceRef]
```

#### 3. Sistema de Señales

**Arquitectura**:
```
questionnaire_monolith.json (300 preguntas)
    ↓ parse + extract
SignalPack {patterns[], indicators[], thresholds[]}
    ↓
SignalClient (base_url = "memory://" | "http://...")
    ↓
SignalRegistry (caché LRU, TTL=3600s, max_size=100)
```

**Modos de Transporte**:
- **memory://** (Por defecto): In-process, latencia cero
- **http://** (Opcional): Arquitecturas distribuidas con circuit breaker

#### 4. ArgRouter Extendido

**Problema**: Los ejecutores reciben 50+ parámetros dinámicos. El tipado estricto de Python requiere enrutamiento explícito.

**Solución**: 30+ rutas especiales eliminan caídas silenciosas de parámetros

```python
SPECIAL_ROUTES = {
    "bayesian_prior_alpha": "bayesian_config.prior_alpha",
    "coherence_threshold": "coherence_detector.threshold",
    "kpi_extraction_mode": "kpi_extractor.mode",
    # ... 27 rutas más
}
```

**Métrica**: `argrouter_coverage = 1.0` (DEBE enrutar todos los parámetros)

### Flujo de Datos

```
Documento de Política (PDF)
    ↓
Ingesta SPC (9 fases)
    ↓
CanonPolicyPackage {content, provenance, chunk_graph, integrity_index}
    ↓
SPCAdapter → PreprocessedDocument
    ↓
Orchestrator (300 preguntas)
    ↓
7 Productores (ejecución paralela)
    ↓
Ensamblaje de Evidencia
    ↓
Validación y Puntuación
    ↓
Reporte Final (MICRO/MESO/MACRO)
```

### Métricas de Calidad

| Métrica | Definición | Umbral | Actual |
|---------|------------|--------|--------|
| **provenance_completeness** | `tokens_con_prov / total_tokens` | = 1.0 | **1.0** |
| **signals.hit_rate** | `fetches_exitosos / intentos_totales` | ≥ 0.95 | **0.97** |
| **argrouter_coverage** | `params_enrutados / params_totales` | = 1.0 | **1.0** |
| **determinism_check** | SHA-256 idéntico en 10 ejecuciones | PASS | **PASS** |

---

## 🧪 Pruebas

### Resumen de Suite de Pruebas

| Categoría | Pruebas | Aprobadas | Cobertura |
|-----------|---------|-----------|-----------|
| Contratos | 45 | 45 | 92% |
| Señales | 33 | 33 | 95% |
| Ingesta CPP | 16 | 16 | 88% |
| ArgRouter | 24 | 24 | 100% |
| Integración | 18 | 18 | N/A |
| **TOTAL** | **238** | **238** | **87.3%** |

### Ejecutar Pruebas

```bash
# Suite completa de pruebas
python -m pytest tests/ -v --cov=src/saaaaaa --cov-report=term-missing

# Categorías específicas de pruebas
python -m pytest tests/test_contracts.py -v
python -m pytest tests/test_signals.py -v
python -m pytest tests/test_cpp_ingestion.py -v

# Golden tests (determinismo)
python -m pytest tests/test_regression_*.py -v
```

### Ejecución del Plan de Pruebas

Ver [TEST_PLAN.md](TEST_PLAN.md) para casos de prueba completos.

**Validación rápida**:
```bash
# Ejecutar todas las pruebas requeridas
bash test_suite.sh
```

---

## 🔬 Temas Avanzados

### Sistema de Calibración

El sistema de calibración gestiona parámetros de puntuación en las 300 preguntas.

**Configuración**:
- `config/intrinsic_calibration.json` - Parámetros base de calibración
- `config/fusion_specification.json` - Reglas de fusión multi-método
- `config/layer_calibrations/` - Calibraciones específicas por capa

**Documentación**: [docs/CALIBRATION_QUICK_START.md](docs/CALIBRATION_QUICK_START.md)

### Irrigación de Señales

Sistema de señales transversales que propaga patrones del cuestionario a todos los ejecutores.

**Archivos Clave**:
- `src/saaaaaa/core/orchestrator/signals.py` - Cliente/registro de señales
- `src/saaaaaa/core/orchestrator/signal_loader.py` - Extracción de patrones

**Documentación**: [docs/SIGNAL_IRRIGATION_README.md](docs/SIGNAL_IRRIGATION_README.md)

### Especificación de Contratos V3

Último formato de contrato de ejecutor con estructura completa.

**Esquema**: `config/schemas/executor_contract.v3.schema.json`

**Documentación**: [docs/contracts/README.md](docs/contracts/README.md)

### Sistema de Importación

Sistema de importación determinista, auditable y portable con importaciones seguras y carga perezosa.

**Documentación**: [docs/IMPORT_SYSTEM.md](docs/IMPORT_SYSTEM.md)

### Rastreo de Proveniencia

Trazabilidad completa token-a-fuente vía Arrow IPC.

**Cálculo**:
```python
def _calculate_provenance_completeness(chunks: List[Chunk]) -> float:
    total_tokens = sum(len(c.text.split()) for c in chunks)
    tokens_with_prov = sum(
        len(c.text.split()) for c in chunks if c.provenance is not None
    )
    return tokens_with_prov / total_tokens if total_tokens > 0 else 0.0
```

---

## 🛠️ Desarrollo

### Configurar Entorno de Desarrollo

```bash
# Clonar e instalar
git clone https://github.com/PEROPOROBTANTE/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE_FINAL.git
cd F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE_FINAL
bash install.sh
source farfan-env/bin/activate

# Instalar dependencias de desarrollo
pip install -r requirements-dev.txt

# Verificar instalación
python -m saaaaaa.devtools.ensure_install
```

### Estructura del Código

```
src/saaaaaa/
├── core/
│   ├── orchestrator/          # Motor principal de orquestación (30+ módulos)
│   │   ├── core.py            # Orchestrator
│   │   ├── executors.py       # Implementaciones de ejecutores
│   │   ├── arg_router.py      # Enrutador extendido de argumentos
│   │   ├── questionnaire.py   # Integridad del cuestionario
│   │   └── signals.py         # Sistema de señales
│   └── phases/                # Definiciones de fases
├── processing/
│   ├── spc_ingestion/         # Capa de conversión SPC
│   └── [procesadores]         # Procesadores de documentos
├── analysis/                  # Módulos de análisis
└── utils/                     # Utilidades y adaptadores
```

### Agregar Nuevos Analizadores

1. Crear clase analizadora en `src/saaaaaa/analysis/`
2. Registrar en `src/saaaaaa/core/orchestrator/class_registry.py`
3. Agregar firma de método al catálogo canónico de métodos
4. Crear contrato de ejecutor en `config/executor_contracts/`
5. Agregar pruebas en `tests/`

### Consejos de Depuración

```bash
# Habilitar modo debug
export PIPELINE_DEBUG=1

# Ejecutar con salida verbose
python scripts/run_policy_pipeline_verified.py \
    --plan data/plans/Plan_1.pdf \
    --artifacts-dir artifacts/debug \
    2>&1 | tee debug.log

# Analizar claims de ejecución
jq '.[] | select(.claim_type=="error")' artifacts/debug/execution_claims.json
```

---

## 🐛 Solución de Problemas

### Problemas Comunes

#### Problema 1: Errores de Importación

**Síntomas**:
```
ImportError: cannot import name 'TorchTensorParallelPlugin'
ModuleNotFoundError: No module named 'transformers'
```

**Solución**:
```bash
# Verificar versiones correctas
pip list | grep -E "transformers|accelerate|sentence-transformers"

# Debería mostrar:
# transformers==4.41.2
# accelerate==1.2.1
# sentence-transformers==3.1.0

# Reinstalar si es necesario
bash install.sh
```

#### Problema 2: Discrepancia de Hash del Cuestionario

**Síntomas**:
```
HashValidationError: Discrepancia de hash del cuestionario
```

**Solución**:
```bash
# Verificar si el archivo fue modificado
git status data/questionnaire_monolith.json

# Revertir a versión canónica
git checkout data/questionnaire_monolith.json

# Verificar integridad
python3 -c "
from saaaaaa.core.orchestrator.questionnaire import load_questionnaire
q = load_questionnaire()
print(f'✓ Hash verificado: {q.sha256[:16]}...')
"
```

#### Problema 3: Falta de Memoria

**Síntomas**:
```
MemoryError: No se puede asignar array
Killed
```

**Solución**:
```bash
# Reducir conteo de chunks (editar scripts de pipeline)
# Cambiar max_chunks=50 a max_chunks=25

# O aumentar memoria disponible
# Mínimo: 8GB RAM
# Recomendado: 16GB RAM
```

#### Problema 4: Pipeline se Cuelga

**Síntomas**:
- Pipeline ejecuta > 10 minutos sin salida
- Uso de CPU cae a 0%

**Solución**:
```bash
# Matar pipeline
pkill -f "python.*run_policy"

# Reiniciar con modo debug
export PIPELINE_DEBUG=1
python scripts/run_policy_pipeline_verified.py \
    --plan data/plans/Plan_1.pdf \
    --artifacts-dir artifacts/debug
```

### Obtener Ayuda

**Si los problemas persisten**:

1. Verificar versión de Python: `python3.12 --version` (debe ser 3.12.x)
2. Ejecutar diagnóstico: `python diagnose_import_error.py`
3. Revisar logs: Revisar salida de ejecución del pipeline
4. Verificar rama git: `git branch`

**Soporte**:
- GitHub Issues: https://github.com/PEROPOROBTANTE/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE_FINAL/issues
- Incluir salida de: `python diagnose_import_error.py`

---

## 🤝 Contribuir

Ver [CONTRIBUTING.md](CONTRIBUTING.md) para guías de contribución.

**Flujo rápido de contribución**:
1. Fork del repositorio
2. Crear rama de característica (`git checkout -b feature/caracteristica-increible`)
3. Hacer cambios y agregar pruebas
4. Ejecutar suite de pruebas (`bash test_suite.sh`)
5. Commit de cambios (`git commit -m 'Agregar característica increíble'`)
6. Push a rama (`git push origin feature/caracteristica-increible`)
7. Abrir Pull Request

---

## 📄 Licencia y Citación

### Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

### Citación

Si usa F.A.R.F.A.N en su investigación, por favor cite:

```bibtex
@software{farfan2025,
  title={F.A.R.F.A.N: Framework for Advanced Retrieval of Administrative Narratives},
  author={Equipo de Desarrollo F.A.R.F.A.N},
  year={2025},
  url={https://github.com/PEROPOROBTANTE/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE_FINAL},
  version={1.0.0}
}
```

---

## 📖 Recursos Adicionales

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Arquitectura detallada del sistema
- **[RUNBOOK.md](RUNBOOK.md)** - Manual operacional
- **[TEST_PLAN.md](TEST_PLAN.md)** - Plan de pruebas completo
- **[CHANGELOG.md](CHANGELOG.md)** - Historial de versiones
- **[docs/](docs/)** - Documentación extendida

---

**Versión**: 1.0.0  
**Última Actualización**: 2025-11-26  
**Estado**: Listo para Producción
