# QUESTIONNAIRE MONOLITH - AUDIT REPORT

**Fecha**: 2025-12-02  
**Generado por**: Agente de Ingeniería Autónoma

---

## RESUMEN EJECUTIVO

⚠️ **INCONSISTENCIA DETECTADA**: Archivo duplicado en 2 ubicaciones diferentes  
⚠️ **CÓDIGO INCONSISTENTE**: Scripts usan rutas diferentes  
✅ **SCHEMA PRESENTE**: schema_version 2.0.0  
❌ **FALTA JSON SCHEMA**: No hay $schema field  

---

## UBICACIONES ENCONTRADAS

### 1. `config/json_files_ no_schemas/questionnaire_monolith.json`

**Estado**: ❌ UBICACIÓN INCORRECTA (carpeta mal nombrada)

```
Tamaño: 2,394,796 bytes (2.28 MB)
Última modificación: 2025-12-01 13:13
Schema version: 2.0.0
Top-level keys: 7
  - canonical_notation (dict)
  - blocks (dict[6 keys])
  - generated_at (str)
  - integrity (dict)
  - observability (dict)
  - schema_version: "2.0.0"
  - version (str)
```

**Problemas**:
- ❌ Carpeta "json_files_ no_schemas" contradictoria (dice "no schemas" pero tiene schema_version)
- ❌ No está bajo control de paquete (está en config/, no en src/)
- ⚠️ 3 scripts antiguos apuntan aquí

### 2. `system/config/questionnaire/questionnaire_monolith.json`

**Estado**: ✅ UBICACIÓN CORRECTA (canónica)

```
Tamaño: 2,394,796 bytes (2.28 MB)
Última modificación: 2025-12-01 13:13
Schema version: 2.0.0
Estructura: IDÉNTICA a archivo 1
```

**Ventajas**:
- ✅ Carpeta específica: `system/config/questionnaire/`
- ✅ Organización jerárquica clara
- ✅ 1 script moderno apunta aquí
- ✅ Separación de concerns

---

## CÓDIGO QUE USA EL ARCHIVO

### Scripts con ruta OLD (incorrecta):

```python
# scripts/clear_validations.py (línea 6)
MONOLITH_PATH = Path("config/json_files_ no_schemas/questionnaire_monolith.json")

# scripts/fix_monolith.py (línea 4)
MONOLITH_PATH = Path("config/json_files_ no_schemas/questionnaire_monolith.json")

# scripts/dev/debug_schema_errors.py (línea 7)
MONOLITH_PATH = Path("config/json_files_ no_schemas/questionnaire_monolith.json")
```

### Scripts con ruta NEW (correcta):

```python
# scripts/validate_phase2_architecture.py (línea 85)
monolith_path = Path("system/config/questionnaire/questionnaire_monolith.json")
```

### Configuración en paths.py:

```python
# src/farfan_pipeline/config/paths.py
QUESTIONNAIRE_FILE: Final[Path] = DATA_DIR / 'questionnaire_monolith.json'
#                                   ^^^^^^^^
#                                   ⚠️ Asume estar en DATA_DIR (no especifica system/config)
```

---

## ANÁLISIS DE SCHEMA

### Estructura del Monolith:

```json
{
  "canonical_notation": {
    "type": "...",
    "specification": "..."
  },
  "blocks": {
    "methods": [...],
    "dimensions": [...],
    "indicators": [...],
    "outcomes": [...],
    "rules": [...],
    "constraints": [...]
  },
  "generated_at": "2025-11-XX...",
  "integrity": {
    "hash": "sha256:...",
    "block_hashes": {...},
    "verified": true
  },
  "observability": {
    "trace_id": "..."
  },
  "schema_version": "2.0.0",
  "version": "..."
}
```

### Schema Metadata:

✅ **Tiene**:
- `schema_version`: "2.0.0"
- `version`: Versión del monolith
- `integrity`: Hash y verificación
- `observability`: Trazabilidad

❌ **Falta**:
- `$schema`: URL to JSON Schema definition
  - Debería ser algo como: `"$schema": "https://farfan-pipeline.org/schemas/questionnaire-monolith/v2.0.0.json"`

⚠️ **Inconsistencia**:
- Carpeta dice "no_schemas" pero archivo tiene `schema_version`

---

## PROBLEMAS IDENTIFICADOS

### 1. DUPLICACIÓN DE ARCHIVOS
- **Impacto**: Alto
- **Riesgo**: Divergencia de datos
- **Solución**: Eliminar versión antigua, usar solo system/config/

### 2. RUTAS INCONSISTENTES EN SCRIPTS
- **Impacto**: Alto
- **Riesgo**: Scripts fallan en producción
- **Solución**: Actualizar 3 scripts a ruta nueva

### 3. PATHS.PY AMBIGUO
- **Impacto**: Medio
- **Riesgo**: Confusión sobre ubicación canónica
- **Solución**: Definir ruta absoluta explícita

### 4. FALTA $SCHEMA
- **Impacto**: Bajo
- **Riesgo**: No hay validación automática
- **Solución**: Agregar campo $schema con URL a definición

### 5. CARPETA MAL NOMBRADA
- **Impacto**: Bajo
- **Riesgo**: Confusión conceptual
- **Solución**: Renombrar o eliminar config/json_files_no_schemas/

---

## RECOMENDACIONES

### 1. UBICACIÓN CANÓNICA (CRÍTICO)

**Establecer ruta única**:
```
system/config/questionnaire/questionnaire_monolith.json
```

**Razones**:
- ✅ Organización clara
- ✅ Separada de código fuente
- ✅ Fácil de versionar
- ✅ No confunde con código Python

### 2. ACTUALIZAR PATHS.PY (CRÍTICO)

```python
# src/farfan_pipeline/config/paths.py
QUESTIONNAIRE_FILE: Final[Path] = (
    PROJECT_ROOT / "system" / "config" / "questionnaire" / "questionnaire_monolith.json"
)
```

### 3. ACTUALIZAR SCRIPTS (CRÍTICO)

Cambiar en 3 archivos:
- scripts/clear_validations.py
- scripts/fix_monolith.py
- scripts/dev/debug_schema_errors.py

De:
```python
MONOLITH_PATH = Path("config/json_files_ no_schemas/questionnaire_monolith.json")
```

A:
```python
from farfan_pipeline.config.paths import QUESTIONNAIRE_FILE
MONOLITH_PATH = QUESTIONNAIRE_FILE
```

### 4. AGREGAR $SCHEMA (RECOMENDADO)

Agregar al JSON:
```json
{
  "$schema": "https://farfan-pipeline.org/schemas/questionnaire-monolith/v2.0.0.json",
  "schema_version": "2.0.0",
  ...
}
```

### 5. ELIMINAR DUPLICADO (RECOMENDADO)

```bash
git rm config/json_files_no_schemas/questionnaire_monolith.json
```

### 6. PACKAGE DATA (OPCIONAL)

Si quieres incluir el monolith en el paquete pip:

```toml
# pyproject.toml
[tool.setuptools.package-data]
farfan_pipeline = [
    "../../system/config/questionnaire/*.json"
]
```

---

## PLAN DE ACCIÓN

### Fase 1: Corrección Inmediata
- [x] Auditar ubicaciones
- [ ] Actualizar paths.py con ruta canónica
- [ ] Actualizar 3 scripts antiguos
- [ ] Eliminar archivo duplicado

### Fase 2: Mejora de Schema
- [ ] Crear JSON Schema formal
- [ ] Agregar campo $schema al monolith
- [ ] Configurar validación automática

### Fase 3: Documentación
- [ ] Documentar ubicación canónica en README
- [ ] Agregar guía de actualización del monolith
- [ ] Establecer proceso de versionado

---

## ESTRUCTURA RECOMENDADA FINAL

```
proyecto/
├── src/
│   └── farfan_pipeline/
│       ├── config/
│       │   └── paths.py  → Apunta a system/config/questionnaire/
│       └── ...
├── system/
│   └── config/
│       ├── questionnaire/
│       │   ├── questionnaire_monolith.json  ← ÚNICO archivo
│       │   └── schema.json  ← JSON Schema definition
│       └── calibration/
│           └── ...
├── scripts/
│   └── *.py  → Usan QUESTIONNAIRE_FILE de paths.py
└── pyproject.toml
```

---

## VERIFICACIÓN POST-CORRECCIÓN

```bash
# 1. Verificar ruta canónica
python3 -c "from farfan_pipeline.config.paths import QUESTIONNAIRE_FILE; print(QUESTIONNAIRE_FILE)"

# 2. Verificar archivo existe
test -f system/config/questionnaire/questionnaire_monolith.json && echo "✓ OK"

# 3. Verificar JSON válido
python3 -c "import json; json.load(open('system/config/questionnaire/questionnaire_monolith.json'))" && echo "✓ Valid JSON"

# 4. Verificar no hay duplicados
find . -name "questionnaire_monolith.json" | wc -l  # Debe ser 1
```

---

**Estado**: ⚠️ REQUIERE CORRECCIÓN  
**Prioridad**: ALTA (inconsistencia en rutas)  
**Tiempo estimado**: 30 minutos

