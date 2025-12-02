# QUESTIONNAIRE AUDIT - MONOLITH vs SCHEMA

**Fecha**: 2025-12-02  
**Generado por**: Agente de Ingeniería Autónoma

---

## 1️⃣ QUESTIONNAIRE_MONOLITH.JSON (Archivo de DATOS)

### 📍 Ubicaciones Encontradas:

#### Ubicación 1: ❌ INCORRECTA
```
Path: config/json_files_ no_schemas/questionnaire_monolith.json
Size: 2,394,796 bytes (2.28 MB)
Modified: 2025-12-01 13:13
```

**Problemas**:
- ❌ Carpeta mal nombrada: "json_files_ no_schemas" (contradictoria)
- ❌ Fuera de ubicación estándar
- ⚠️ 3 scripts antiguos apuntan aquí:
  - scripts/clear_validations.py
  - scripts/fix_monolith.py
  - scripts/dev/debug_schema_errors.py

#### Ubicación 2: ✅ CORRECTA
```
Path: system/config/questionnaire/questionnaire_monolith.json
Size: 2,394,796 bytes (2.28 MB)
Modified: 2025-12-01 13:13
```

**Ventajas**:
- ✅ Ubicación lógica y organizada
- ✅ Bajo system/config/questionnaire/
- ✅ 1 script moderno usa esta ruta:
  - scripts/validate_phase2_architecture.py

### 📊 Contenido del Monolith:

```json
{
  "canonical_notation": {
    "type": "...",
    "specification": "..."
  },
  "blocks": {
    "methods": [...],        // Lista de métodos disponibles
    "dimensions": [...],     // Dimensiones de análisis
    "indicators": [...],     // Indicadores medibles
    "outcomes": [...],       // Resultados esperados
    "rules": [...],          // Reglas de validación
    "constraints": [...]     // Restricciones del sistema
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
  "schema_version": "2.0.0",  // ← Versión del schema que usa
  "version": "1.0.0"          // ← Versión del monolith mismo
}
```

### ✅ Estado del Monolith:

| Aspecto | Estado | Notas |
|---------|--------|-------|
| Valid JSON | ✅ Sí | Parsea correctamente |
| Tamaño | ✅ 2.28 MB | Razonable |
| Integrity Hash | ✅ Presente | SHA-256 verificable |
| Schema Version | ✅ 2.0.0 | Declarado |
| Duplicado | ⚠️ Sí | 2 copias idénticas |
| Ubicación | ⚠️ Inconsistente | Scripts usan diferentes rutas |

---

## 2️⃣ QUESTIONNAIRE_SCHEMA.JSON (Definición del SCHEMA)

### 📍 Ubicación:

```
❌ NO EXISTE
```

### 🔍 Búsqueda Realizada:

```bash
# Buscado en:
- system/config/questionnaire/
- config/json_files_no_schemas/
- Cualquier directorio con "schema" en el nombre
- Archivos con patrón *questionnaire*schema*.json

# Resultado:
  ❌ NO se encontró archivo de schema separado
```

### 📋 ¿Qué DEBERÍA Existir?

Un archivo JSON Schema que defina la estructura válida del monolith:

```json
// system/config/questionnaire/questionnaire_schema.json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://farfan-pipeline.org/schemas/questionnaire-monolith/v2.0.0.json",
  "title": "Questionnaire Monolith Schema",
  "description": "JSON Schema for F.A.R.F.A.N questionnaire monolith structure",
  "type": "object",
  "required": [
    "canonical_notation",
    "blocks",
    "schema_version",
    "integrity"
  ],
  "properties": {
    "canonical_notation": {
      "type": "object",
      "properties": {
        "type": { "type": "string" },
        "specification": { "type": "string" }
      },
      "required": ["type", "specification"]
    },
    "blocks": {
      "type": "object",
      "properties": {
        "methods": {
          "type": "array",
          "items": { "$ref": "#/definitions/method" }
        },
        "dimensions": { "type": "array" },
        "indicators": { "type": "array" },
        "outcomes": { "type": "array" },
        "rules": { "type": "array" },
        "constraints": { "type": "array" }
      },
      "required": ["methods", "dimensions", "indicators"]
    },
    "schema_version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+$"
    },
    "integrity": {
      "type": "object",
      "properties": {
        "hash": { "type": "string" },
        "verified": { "type": "boolean" }
      },
      "required": ["hash", "verified"]
    }
  },
  "definitions": {
    "method": {
      "type": "object",
      "properties": {
        "id": { "type": "string" },
        "name": { "type": "string" },
        "category": { "type": "string" }
      },
      "required": ["id", "name"]
    }
  }
}
```

### ❌ Problemas por NO Tener Schema Separado:

1. **Sin validación automática**: No se puede verificar que el monolith cumpla la estructura
2. **Sin documentación formal**: No hay especificación de qué campos son obligatorios
3. **Sin versionado independiente**: Schema y datos no se versionan separadamente
4. **Sin herramientas de desarrollo**: IDEs no pueden autocompletar o validar
5. **Sin contrato claro**: Consumidores del monolith no saben qué esperar

---

## 🔗 RELACIÓN ENTRE MONOLITH Y SCHEMA

### Como DEBERÍA Ser:

```
system/config/questionnaire/
├── questionnaire_schema.json       ← Define la estructura válida
└── questionnaire_monolith.json     ← Datos que cumplen el schema
    └─> Referencia al schema con "$schema" field
```

**questionnaire_monolith.json** debería tener:
```json
{
  "$schema": "./questionnaire_schema.json",
  "schema_version": "2.0.0",
  ...resto del contenido...
}
```

### Como Está AHORA:

```
system/config/questionnaire/
└── questionnaire_monolith.json     ← Solo datos, sin schema
    ✗ NO tiene campo "$schema"
    ✓ Tiene "schema_version": "2.0.0" (pero el schema no existe)
```

---

## ⚠️ RESUMEN DE PROBLEMAS

### MONOLITH (datos):
1. ⚠️ **Duplicado**: Existe en 2 ubicaciones
2. ⚠️ **Rutas inconsistentes**: Scripts usan paths diferentes
3. ✅ **Estructura válida**: JSON bien formado
4. ✅ **Integrity verificable**: Tiene hash SHA-256
5. ❌ **Sin referencia a schema**: Falta campo `$schema`

### SCHEMA (definición):
1. ❌ **NO EXISTE**: Archivo de schema no encontrado
2. ❌ **Sin validación**: No se puede verificar estructura del monolith
3. ❌ **Sin documentación**: No hay especificación formal
4. ⚠️ **schema_version declarado**: Monolith dice "2.0.0" pero el schema no existe

---

## ✅ RECOMENDACIONES

### 1. CREAR SCHEMA (CRÍTICO)

```bash
# Crear archivo de schema
touch system/config/questionnaire/questionnaire_schema.json
```

Contenido mínimo:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://farfan-pipeline.org/schemas/questionnaire-monolith/v2.0.0.json",
  "title": "Questionnaire Monolith Schema v2.0.0",
  "type": "object",
  "required": ["canonical_notation", "blocks", "schema_version", "integrity"],
  "properties": {
    "schema_version": {
      "const": "2.0.0"
    },
    "canonical_notation": { "type": "object" },
    "blocks": { "type": "object" },
    "integrity": { "type": "object" }
  }
}
```

### 2. ACTUALIZAR MONOLITH (CRÍTICO)

Agregar al inicio de `questionnaire_monolith.json`:
```json
{
  "$schema": "./questionnaire_schema.json",
  "schema_version": "2.0.0",
  ...resto...
}
```

### 3. ELIMINAR DUPLICADO (CRÍTICO)

```bash
git rm "config/json_files_ no_schemas/questionnaire_monolith.json"
```

Mantener solo: `system/config/questionnaire/questionnaire_monolith.json`

### 4. ACTUALIZAR SCRIPTS (CRÍTICO)

Cambiar en 3 scripts:
```python
# DE:
MONOLITH_PATH = Path("config/json_files_ no_schemas/questionnaire_monolith.json")

# A:
from farfan_pipeline.config.paths import PROJECT_ROOT
MONOLITH_PATH = PROJECT_ROOT / "system/config/questionnaire/questionnaire_monolith.json"
```

### 5. VALIDACIÓN AUTOMÁTICA (RECOMENDADO)

```python
# scripts/validate_questionnaire.py
import json
import jsonschema

with open("system/config/questionnaire/questionnaire_schema.json") as f:
    schema = json.load(f)

with open("system/config/questionnaire/questionnaire_monolith.json") as f:
    monolith = json.load(f)

jsonschema.validate(monolith, schema)
print("✓ Monolith válido según schema")
```

---

## 📁 ESTRUCTURA FINAL RECOMENDADA

```
sistema/
├── src/
│   └── farfan_pipeline/
│       └── config/
│           └── paths.py → Define QUESTIONNAIRE_FILE
├── system/
│   └── config/
│       └── questionnaire/
│           ├── questionnaire_schema.json    ← CREAR (definición)
│           └── questionnaire_monolith.json  ← YA EXISTE (datos)
│               └─> Referencia a schema con "$schema"
└── scripts/
    └── *.py → Usan QUESTIONNAIRE_FILE de paths.py
```

---

## ✅ CHECKLIST DE CORRECCIÓN

- [ ] Crear `questionnaire_schema.json` con estructura JSON Schema
- [ ] Agregar campo `"$schema"` al monolith
- [ ] Eliminar duplicado en config/json_files_no_schemas/
- [ ] Actualizar 3 scripts con ruta correcta
- [ ] Actualizar paths.py con ruta canónica
- [ ] Crear script de validación automática
- [ ] Documentar en README la ubicación del monolith y schema
- [ ] Agregar validación a CI/CD

---

**Estado MONOLITH**: ⚠️ Duplicado + Sin referencia a schema  
**Estado SCHEMA**: ❌ NO EXISTE  
**Prioridad**: ALTA  
**Tiempo estimado**: 1-2 horas (crear schema + actualizar refs)

