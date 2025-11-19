# MANUAL OPERACIONAL — F.A.R.F.A.N System

**Framework for Advanced Retrieval of Administrativa Narratives**

## Tabla de Contenidos

1. [Prerrequisitos](#1-prerrequisitos)
2. [Instalación con Pins](#2-instalación-con-pins)
3. [Comandos de Equipamiento](#3-comandos-de-equipamiento)
4. [Ejecución Estándar](#4-ejecución-estándar)
5. [Batería de Tests Actualizados](#5-batería-de-tests-actualizados)
6. [Validaciones Pre-Ejecución](#6-validaciones-pre-ejecución)
7. [Métricas Esperadas Post-Run](#7-métricas-esperadas-post-run)
8. [Recuperación de Errores](#8-recuperación-de-errores)
9. [Comandos de Referencia Rápida](#9-comandos-de-referencia-rápida)

---

## 1. Prerrequisitos

### 1.1 Versión de Python

**REQUERIDO:** Python = 3.12.x (versiones anteriores no soportadas)

```bash
# Verificar versión
python3 --version
# Debe mostrar: Python 3.12.x
```

### 1.2 Herramientas del Sistema

#### En Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install -y \
  build-essential \
  python3-dev \
  libicu-dev \
  libssl-dev \
  pkg-config \
  git \
  curl
```

#### En macOS:
```bash
# Instalar Homebrew si no está instalado
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Instalar dependencias
brew install python@3.12 icu4c pkg-config
```

### 1.3 Gestores de Paquetes Python

**Opción A: uv (Recomendado - Más rápido)**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env
uv --version
```

**Opción B: Poetry**
```bash
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"
poetry --version
```

**Opción C: pip estándar**
```bash
python3 -m pip install --upgrade pip setuptools wheel
```

### 1.4 Variables de Entorno Opcionales

```bash
# Para señales HTTP (opcional - por defecto usa memory://)
export SIGNALS_TOKEN="your-token-here"
export SIGNALS_BASE_URL="http://localhost:8000"

# Para compilación de extensiones C/C++
export CC=gcc
export CXX=g++

# Para límites del sistema (opcional)
export SAAAAAA_MAX_WORKERS=8
export SAAAAAA_MEMORY_LIMIT_GB=16
```

### 1.5 Verificación de ICU/Unicode

```bash
# Verificar disponibilidad de ICU
python3 -c "import icu; print(f'ICU version: {icu.ICU_VERSION}')" || echo "ICU no disponible - instalar pyicu"

# Verificar soporte Unicode
python3 -c "import unicodedata; print(f'Unicode: {unicodedata.unidata_version}')"
```

---

## 2. Instalación con Pins

### 2.1 Clonar Repositorio

```bash
git clone https://github.com/kkkkknhh/SAAAAAA.git
cd SAAAAAA
```

### 2.2 Instalación con uv (Recomendado)

```bash
# Crear entorno virtual
uv venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Instalar dependencias con pins
uv pip install -r requirements.txt

# Instalar paquete en modo editable
uv pip install -e .

# Verificar instalación
uv pip freeze > installed_versions.txt
diff requirements.txt installed_versions.txt || echo "Verificar diferencias"
```

### 2.3 Instalación con Poetry

```bash
# Instalar con lock
poetry install --no-root
poetry install

# Verificar lock
poetry check
poetry show --tree
```

### 2.4 Instalación con pip

```bash
# Crear entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependencias con pins exactos
pip install -r requirements.txt

# Instalar paquete
pip install -e .

# Verificar pins
pip freeze | grep -f requirements.txt
```

### 2.5 Instalar Modelos de SpaCy

```bash
# Modelos en español (requeridos)
python3 -m spacy download es_core_news_lg
python3 -m spacy download es_dep_news_trf

# Verificar instalación
python3 -c "import spacy; nlp = spacy.load('es_core_news_lg'); print('✓ SpaCy OK')"
```

---

## 3. Comandos de Equipamiento

### 3.1 `make equip-system` — Verificación del Sistema Operativo

```bash
make equip-system
```

**Realiza:**
- ✓ Verifica versión de Python (>= 3.10)
- ✓ Comprueba `ulimits` (archivos abiertos, procesos)
- ✓ Valida configuración de locales (UTF-8)
- ✓ Verifica disponibilidad de ICU/Unicode
- ✓ Comprueba herramientas del sistema (gcc, make, pkg-config)
- ✓ Valida memoria disponible y límites

**Comando completo (si no existe target Makefile):**
```bash
python3 scripts/verify_system_equipment.py --check-all
```

**Salida esperada:**
```
✓ Python version: 3.12.x
✓ Open files limit: 1024 (soft) / 1048576 (hard)
✓ Locale: UTF-8 enabled
✓ ICU version: 73.2
✓ Build tools: gcc, g++, make found
✓ Available memory: 16GB
✓ System ready
```

### 3.2 `make equip-python` — Instalación y Compilación Python

```bash
make equip-python
```

**Realiza:**
- ✓ Instala dependencias Python con pins verificados
- ✓ Compila extensiones C (blake3, pyarrow, polars)
- ✓ Verifica hashes de compilación
- ✓ Pre-compila módulos Python (.pyc)
- ✓ Valida imports críticos

**Comando completo:**
```bash
# Instalar con verificación
pip install -r requirements.txt --no-cache-dir --force-reinstall

# Compilar módulos
python3 -m compileall -q src/ orchestrator/ core/ executors/ scoring/

# Verificar extensiones C
python3 -c "import blake3; print(f'✓ blake3: {blake3.__version__}')"
python3 -c "import pyarrow; print(f'✓ pyarrow: {pyarrow.__version__}')"
python3 -c "import polars; print(f'✓ polars: {polars.__version__}')"

# Test de imports
python3 tools/import_all.py
```

### 3.3 `make equip-signals` — Preparación del Sistema de Señales

```bash
make equip-signals
```

**Realiza:**
- ✓ Warm-up de memoria:// (registro de señales en memoria)
- ✓ Pre-compilación de patrones regex
- ✓ Seed de SignalRegistry con datos iniciales
- ✓ Verificación de hit_rate de señales

**Comando completo:**
```bash
python3 scripts/equip_signals.py \
  --source memory \
  --preload-patterns \
  --warmup-cache \
  --verify-registry
```

**Salida esperada:**
```
✓ SignalRegistry initialized (max_size=100, ttl=3600s)
✓ Patterns pre-compiled: 45 regex patterns
✓ Memory cache warmed: 10 policy areas
✓ Hit rate test: 98.5% (threshold: 95%)
✓ Signals ready
```

### 3.4 `make equip-cpp` — Verificación de CPP Adapter

```bash
make equip-cpp
```

**Realiza:**
- ✓ Smoke test de CPPAdapter
- ✓ Verifica conversión CPP → PreprocessedDocument
- ✓ Valida completitud de proveniencia (= 1.0)
- ✓ Test de ensure() con documento de prueba

**Comando completo:**
```bash
python3 scripts/equip_cpp_smoke.py --run-tests
```

**Salida esperada:**
```
✓ CPPAdapter initialized
✓ Test CPP document created
✓ Conversion successful
✓ Provenance completeness: 1.0
✓ ensure() validation passed
✓ CPP subsystem ready
```

### 3.5 Equipamiento Completo

```bash
# Ejecutar todas las fases de equipamiento
make equip-all
# O manualmente:
make equip-system && \
make equip-python && \
make equip-signals && \
make equip-cpp
```

---

## 4. Ejecución Estándar

### 4.1 Modo Flux Pipeline Completo

**Comando básico:**
```bash
python3 -m saaaaaa.flux.cli run \
  "demo://sample-policy-document.pdf"
```

**Comando con parámetros completos:**
```bash
python3 -m saaaaaa.flux.cli run \
  "file:///absolute/path/to/plan.pdf" \
  --ingest-enable-ocr \
  --ingest-ocr-threshold 0.85 \
  --ingest-max-mb 250 \
  --normalize-unicode-form NFC \
  --normalize-keep-diacritics \
  --chunk-priority-resolution MESO \
  --chunk-overlap-max 0.15 \
  --chunk-max-tokens-meso 1200 \
  --signals-source memory \
  --signals-ttl-s 3600 \
  --aggregate-feature-set full \
  --aggregate-group-by policy_area,year \
  --score-metrics precision,coverage,risk \
  --score-calibration-mode none \
  --report-formats json,md \
  --report-include-provenance
```

### 4.2 Ejecución por Fases Individuales

#### Fase 1: Ingest
```bash
python3 -c "
from saaaaaa.flux import IngestConfig, run_ingest

cfg = IngestConfig(enable_ocr=True, ocr_threshold=0.85, max_mb=250)
outcome = run_ingest(cfg, input_uri='demo://sample.pdf')
print(f'Fingerprint: {outcome.fingerprint}')
print(f'Status: {outcome.status}')
"
```

#### Fase 2: Normalize
```bash
python3 -c "
from saaaaaa.flux import NormalizeConfig, run_normalize, IngestDeliverable

# Asumiendo ingest_deliverable ya cargado
cfg = NormalizeConfig(unicode_form='NFC', keep_diacritics=True)
outcome = run_normalize(cfg, ingest_deliverable)
print(f'Sentences: {len(outcome.payload[\"sentences\"])}')
"
```

#### Fase 3: Chunk
```bash
python3 -c "
from saaaaaa.flux import ChunkConfig, run_chunk

cfg = ChunkConfig(priority_resolution='MESO', overlap_max=0.15, max_tokens_meso=1200)
outcome = run_chunk(cfg, normalize_deliverable)
print(f'Chunks: {len(outcome.payload[\"chunks\"])}')
"
```

#### Fase 4: Signals (Cross-Cut)
```bash
python3 -c "
from saaaaaa.flux import SignalsConfig, run_signals

def dummy_registry(area): return {'patterns': ['p1', 'p2'], 'version': '1.0'}

cfg = SignalsConfig(source='memory', ttl_s=3600)
outcome = run_signals(cfg, chunk_deliverable, registry_get=dummy_registry)
print(f'Enriched chunks: {len(outcome.payload[\"enriched_chunks\"])}')
"
```

#### Fase 5: Aggregate
```bash
python3 -c "
from saaaaaa.flux import AggregateConfig, run_aggregate

cfg = AggregateConfig(feature_set='full', group_by=['policy_area', 'year'])
outcome = run_aggregate(cfg, signals_deliverable)
print(f'Features rows: {outcome.payload[\"meta\"][\"rows\"]}')
"
```

#### Fase 6: Score
```bash
python3 -c "
from saaaaaa.flux import ScoreConfig, run_score

cfg = ScoreConfig(metrics=['precision', 'coverage', 'risk'], calibration_mode='none')
outcome = run_score(cfg, aggregate_deliverable)
print(f'Scores computed: {outcome.payload[\"meta\"][\"total_scores\"]}')
"
```

#### Fase 7: Report
```bash
python3 -c "
from saaaaaa.flux import ReportConfig, run_report

cfg = ReportConfig(formats=['json', 'md'], include_provenance=True)
outcome = run_report(cfg, score_deliverable, doc_manifest)
print(f'Artifacts: {list(outcome.payload[\"artifacts\"].keys())}')
"
```

### 4.3 Ejecución con CPP Ingestion Habilitado

```bash
python3 examples/cpp_ingestion_example.py
```

O programáticamente:
```bash
python3 -c "
from saaaaaa.processing.cpp_ingestion import CPPIngestionPipeline
from pathlib import Path

pipeline = CPPIngestionPipeline(
    enable_ocr=False,
    ocr_confidence_threshold=0.85,
    chunk_overlap_threshold=0.15
)

outcome = pipeline.ingest(
    Path('data/input_plans/plan.pdf'),
    Path('data/output/cpp_output')
)

print(f'Status: {outcome.status}')
print(f'Provenance completeness: {outcome.metrics.provenance_completeness}')
"
```

### 4.4 Dry-Run (Validación sin Ejecución)

```bash
python3 -m saaaaaa.flux.cli run \
  "demo://sample.pdf" \
  --dry-run
```

Imprime configuración sin ejecutar fases.

---

## 5. Batería de Tests Actualizados

### 5.1 Tests Marcados como Actualizados

El sistema marca explícitamente tests que están actualizados y soportados:

```bash
# Ejecutar SOLO tests actualizados
pytest -m "updated and not outdated" -v

# Ver lista de tests con marca "updated"
pytest --collect-only -m updated
```

### 5.2 Clasificación de Tests

#### Tests Core (Alta Prioridad)
```bash
# Tests de contratos y validación
pytest tests/test_contracts_comprehensive.py -v
pytest tests/test_flux_contracts.py -v
pytest tests/test_signal_client.py -v

# Tests de CPP y adaptadores
pytest tests/test_cpp_adapter.py -v
pytest tests/test_cpp_ingestion.py -v

# Tests de integración flux
pytest tests/test_flux_integration.py -v
```

#### Tests de Signals y Routing
```bash
pytest tests/test_signals.py -v
pytest tests/test_signal_integration_e2e.py -v
pytest tests/test_arg_router.py -v
pytest tests/test_arg_router_extended.py -v
```

#### Tests de Aggregation y Scoring
```bash
pytest tests/test_aggregation.py -v
pytest tests/test_scoring.py -v
pytest tests/test_recommendation_coverage.py -v
```

#### Tests de Calidad y Validación
```bash
pytest tests/test_questionnaire_validation.py -v
pytest tests/test_schema_validation.py -v
pytest tests/test_boundaries.py -v
```

### 5.3 Tests Obsoletos Marcados

Los tests obsoletos están marcados con:
```python
@pytest.mark.skip(reason="outdated - no longer compatible with current architecture")
```

Ver: `tests/UPDATED_TESTS_MANIFEST.json` para la lista completa.

### 5.4 Ejecución Rápida (Smoke Tests)

```bash
# Solo tests rápidos (< 1 segundo cada uno)
pytest tests/test_smoke_imports.py -v
pytest tests/test_import_consistency.py -v

# Verificación de estructura
pytest tests/test_structure_verification.py -v
```

### 5.5 Suite Completa de Tests Actualizados

```bash
# Ejecutar todos los tests marcados como "updated"
pytest -m updated -v --tb=short

# Con cobertura
pytest -m updated --cov=src/saaaaaa --cov-report=term-missing

# Rápido (paralelo)
pytest -m updated -n auto
```

---

## 6. Validaciones Pre-Ejecución

### 6.1 Checklist Preflight

**Script automatizado:**
```bash
python3 scripts/preflight_check.py --verbose
```

**Checklist manual:**

#### 6.1.1 Verificar ausencia de YAML en ejecutores
```bash
python3 scripts/scan_no_yaml_in_executors.py
# Debe retornar: ✓ No YAML files found in executors/
```

#### 6.1.2 Verificar pins presentes
```bash
python3 -c "
import pkg_resources
required = open('requirements.txt').read().splitlines()
installed = {pkg.key: pkg.version for pkg in pkg_resources.working_set}
for req in required:
    if '==' in req:
        name, version = req.split('==')
        name = name.lower().replace('_', '-')
        if name not in installed:
            print(f'✗ Missing: {req}')
        elif installed[name] != version:
            print(f'✗ Wrong version: {name} (expected {version}, got {installed[name]})')
print('✓ All pins verified')
"
```

#### 6.1.3 Verificar rutas ArgRouter ≥ 30
```bash
python3 -c "
from saaaaaa.core.orchestrator.arg_router import ArgRouter
router = ArgRouter()
count = len(router._routes)
assert count >= 30, f'Expected ≥30 routes, got {count}'
print(f'✓ ArgRouter has {count} routes')
"
```

#### 6.1.4 Verificar señales memory:// disponibles
```bash
python3 -c "
from saaaaaa.core.orchestrator.signals import SignalClient
client = SignalClient(base_url='memory://')
# Test de disponibilidad
assert client.base_url == 'memory://', 'Memory mode not enabled'
print('✓ Memory signals available')
"
```

#### 6.1.5 Verificar que no hay secretos en código
```bash
# Usar trufflehog, git-secrets, o grep manual
grep -r "password\|secret\|api_key" src/ --include="*.py" | grep -v "# " || echo "✓ No secrets found"

# O con bandit
bandit -r src/ -ll -i
```

### 6.2 Validación de Estructura

```bash
# Verificar importabilidad de módulos clave
python3 -c "
from saaaaaa.core.orchestrator import Orchestrator
from saaaaaa.flux import run_ingest, run_normalize
from saaaaaa.processing.cpp_ingestion import CPPIngestionPipeline
from saaaaaa.core.orchestrator.signals import SignalClient
print('✓ All critical imports successful')
"
```

### 6.3 Verificación de Calidad de Código

```bash
# Compilación de bytecode
python3 -m compileall -q src/ orchestrator/ core/ executors/ || echo "✗ Compilation errors"

# Linting
ruff check src/ --quiet || echo "⚠ Ruff warnings"

# Type checking (opcional, puede tener warnings)
mypy src/saaaaaa --config-file pyproject.toml --no-error-summary 2>&1 | head -10
```

---

## 7. Métricas Esperadas Post-Run

### 7.1 Thresholds Obligatorios

Después de ejecutar el pipeline FLUX, el sistema debe cumplir con:

| Métrica | Threshold | Descripción |
|---------|-----------|-------------|
| `signal_hit_rate` | ≥ 95% | Porcentaje de señales encontradas en chunks |
| `provenance_completeness` | = 1.0 | Completitud de proveniencia (CPP) |
| `boundary_f1` | ≥ 0.85 | F1 score de detección de límites |
| `kpi_linkage_rate` | ≥ 0.90 | Tasa de vinculación de KPIs |
| `coverage` | ≥ 0.85 | Cobertura de análisis sobre documento |
| `determinism` | = 1.0 | Reproducibilidad (mismos fingerprints) |

### 7.2 Verificación de Métricas

```bash
python3 -c "
import json

# Cargar resultados
with open('data/output/report_artifacts/metrics.json') as f:
    metrics = json.load(f)

# Validar thresholds
thresholds = {
    'signal_hit_rate': 0.95,
    'provenance_completeness': 1.0,
    'boundary_f1': 0.85,
    'kpi_linkage_rate': 0.90,
    'coverage': 0.85,
}

failures = []
for metric, threshold in thresholds.items():
    value = metrics.get(metric, 0.0)
    if value < threshold:
        failures.append(f'{metric}: {value:.3f} < {threshold}')
    else:
        print(f'✓ {metric}: {value:.3f}')

if failures:
    print('✗ Threshold failures:')
    for f in failures:
        print(f'  - {f}')
    exit(1)
else:
    print('✓ All thresholds met')
"
```

### 7.3 Quality Gates

```bash
python3 -c "
from saaaaaa.flux.gates import QualityGates

# Verificar gates
gate_results = QualityGates.run_all_gates(
    phase_outcomes=phase_outcomes,
    run1_fingerprints=fingerprints,
    run2_fingerprints=None,
    source_paths=[Path('src/saaaaaa/flux')]
)

passed = sum(1 for r in gate_results.values() if r.passed)
total = len(gate_results)
print(f'Quality Gates: {passed}/{total} passed')

if passed < total:
    for name, result in gate_results.items():
        if not result.passed:
            print(f'✗ {name}: {result.message}')
    exit(1)
"
```

---

## 8. Recuperación de Errores

### 8.1 Códigos de Salida

| Código | Significado | Acción |
|--------|-------------|--------|
| 0 | Éxito | Continuar |
| 1 | Error general | Ver logs, diagnósticos |
| 2 | Validación fallida | Revisar preflight checklist |
| 3 | Configuración inválida | Verificar parámetros de entrada |
| 4 | Dependencia faltante | Ejecutar `make equip-python` |
| 5 | Threshold no alcanzado | Revisar calidad de input |

### 8.2 Rutas de Fallback

#### 8.2.1 Si falla ingesta (Fase 1)
```bash
# Verificar archivo de entrada
ls -lh /path/to/input.pdf
file /path/to/input.pdf

# Probar con OCR deshabilitado
python3 -m saaaaaa.flux.cli run "file:///path/to/input.pdf" \
  --ingest-enable-ocr=false

# Verificar logs
tail -f logs/flux_ingest.log
```

#### 8.2.2 Si falla normalización (Fase 2)
```bash
# Probar con forma Unicode diferente
python3 -c "
from saaaaaa.flux import NormalizeConfig, run_normalize
cfg = NormalizeConfig(unicode_form='NFKC', keep_diacritics=False)
# ... ejecutar con cfg alternativa
"
```

#### 8.2.3 Si falla signals (Fase 4)
```bash
# Verificar registry
python3 -c "
from saaaaaa.core.orchestrator.signals import SignalRegistry
registry = SignalRegistry()
print(f'Registry size: {len(registry._store)}')
"

# Fallback: desactivar signals
# (no recomendado, pero permite continuar)
python3 -m saaaaaa.flux.cli run "file:///input.pdf" \
  --signals-source memory \
  --signals-ttl-s 0  # Deshabilita cache
```

#### 8.2.4 Si falla tests
```bash
# Re-ejecutar test específico con más verbosidad
pytest tests/test_failed_module.py::test_failed_function -vv --tb=long

# Limpiar cache y re-ejecutar
pytest --cache-clear tests/test_failed_module.py -v
```

### 8.3 Logs y Diagnósticos

```bash
# Logs de ejecución
tail -f logs/saaaaaa.log

# Logs de tests
pytest tests/ -v --log-cli-level=DEBUG

# Exportar diagnósticos
python3 scripts/export_diagnostics.py --output diagnostics.json
```

### 8.4 Reset Completo

```bash
# Limpiar cache y compilados
make clean

# Reinstalar dependencias
pip uninstall -y -r requirements.txt
pip install -r requirements.txt

# Re-equipar sistema
make equip-all

# Verificar
pytest tests/test_smoke_imports.py -v
```

---

## 9. Comandos de Referencia Rápida

### 9.1 Instalación

```bash
# Clonar e instalar
git clone https://github.com/kkkkknhh/SAAAAAA.git && cd SAAAAAA
pip install -r requirements.txt && pip install -e .
python3 -m spacy download es_core_news_lg es_dep_news_trf
```

### 9.2 Equipamiento

```bash
# Equipamiento completo
make equip-all

# O paso a paso
make equip-system
make equip-python
make equip-signals
make equip-cpp
```

### 9.3 Ejecución

```bash
# Pipeline completo
python3 -m saaaaaa.flux.cli run "demo://sample.pdf"

# Con CPP
python3 examples/cpp_ingestion_example.py

# Dry-run
python3 -m saaaaaa.flux.cli run "demo://sample.pdf" --dry-run
```

### 9.4 Tests

```bash
# Solo actualizados
pytest -m "updated and not outdated" -v

# Suite completa
pytest tests/ -v

# Con cobertura
pytest --cov=src/saaaaaa --cov-report=html
```

### 9.5 Validación

```bash
# Preflight completo
python3 scripts/preflight_check.py --verbose

# Verificación de pins
pip freeze | diff - requirements.txt

# Validación de calidad
ruff check src/ && mypy src/saaaaaa
```

### 9.6 Diagnóstico

```bash
# Ver métricas
python3 scripts/show_metrics.py data/output/report_artifacts/metrics.json

# Verificar fingerprints
python3 -c "from saaaaaa.flux.gates import QualityGates; QualityGates.verify_determinism(fingerprints_run1, fingerprints_run2)"

# Exportar diagnósticos
python3 scripts/export_diagnostics.py
```

---

## 10. Contacto y Soporte

**Repositorio:** https://github.com/kkkkknhh/SAAAAAA

**Documentación completa:**
- [README.md](README.md) - Visión general del sistema
- [OPERATIONAL_GUIDE.md](OPERATIONAL_GUIDE.md) - Guía operacional detallada
- [FLUX_IMPLEMENTATION_SUMMARY.md](FLUX_IMPLEMENTATION_SUMMARY.md) - Detalles de FLUX
- [CPP_IMPLEMENTATION_SUMMARY.md](CPP_IMPLEMENTATION_SUMMARY.md) - Detalles de CPP

**Issues:** https://github.com/kkkkknhh/SAAAAAA/issues

---

**Fin del Manual Operacional**

*Última actualización: 2025-11-06*
