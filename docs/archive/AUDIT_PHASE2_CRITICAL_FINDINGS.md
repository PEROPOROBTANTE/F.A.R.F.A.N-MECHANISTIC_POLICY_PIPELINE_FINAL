# AUDITORÍA CRÍTICA - FLUX PHASE 2 (NORMALIZE) Y SPC QUALITY GATES
**Fecha:** 2025-11-17
**Auditor:** Claude Sonnet 4.5
**Prioridad:** 🔴 CRÍTICA - MÁXIMO ESTÁNDAR REQUERIDO

---

## CONTEXTO

**SPC (Smart Policy Chunks)** es el ÚNICO punto de entrada canónico para ingestion (Phase-One) vía `CPPIngestionPipeline` en `src/saaaaaa/processing/spc_ingestion/__init__.py`.

**FLUX** proporciona fases complementarias que procesan el output de SPC (normalize, chunk, signals, aggregate, score, report).

Esta auditoría identificó bugs críticos en:
- FLUX Phase 2 (normalize): `run_normalize()` en `src/saaaaaa/flux/phases.py`
- SPC Quality Gates: `SPCQualityGates` en `src/saaaaaa/processing/spc_ingestion/quality_gates.py`
- SPC Converter: `SmartChunkConverter` en `src/saaaaaa/processing/spc_ingestion/converter.py`

---

## RESUMEN EJECUTIVO

Se identificaron **5 BUGS CRÍTICOS** que violan los principios de máximo estándar y representan downgrades inaceptables del sistema:

1. **🔴 CRÍTICO**: FLUX `run_normalize()` ignora completamente `NormalizeConfig` (unicode_form, keep_diacritics)
2. **🔴 CRÍTICO**: Normalización Unicode NO implementada en FLUX (comentario TODO en producción)
3. **🔴 CRÍTICO**: Split simplista por `\n` en FLUX sin procesamiento lingüístico real
4. **🟡 ALTO**: SPC SmartChunkConverter puede perder embeddings si numpy no disponible
5. **🟡 MEDIO**: SPC Quality gates no validan provenance_completeness = 1.0

**NOTA**: Bug #1-3 fueron encontrados en FLUX Phase 2 (normalize), NO en SPC Phase-One que es independiente y canónico.

---

## 1. BUG CRÍTICO: run_normalize() IGNORA NormalizeConfig

### Ubicación
- **Archivo:** `src/saaaaaa/flux/phases.py`
- **Línea:** 302-414
- **Función:** `run_normalize()`

### Problema
La función recibe `cfg: NormalizeConfig` con parámetros:
- `unicode_form: Literal["NFC", "NFKC"] = "NFC"`
- `keep_diacritics: bool = True`

**PERO NINGUNO SE USA EN LA IMPLEMENTACIÓN**

### Código Actual (INCORRECTO)
```python
def run_normalize(
    cfg: NormalizeConfig,  # ← Parámetro RECIBIDO PERO IGNORADO
    ing: IngestDeliverable,
    *,
    policy_unit_id: str | None = None,
    correlation_id: str | None = None,
    envelope_metadata: dict[str, str] | None = None,
) -> PhaseOutcome:
    # ...

    # TODO: Implement actual normalization (unicode normalization, etc.)
    sentences = [s for s in ing.raw_text.split("\n") if s.strip()]
    sentence_meta: list[dict[str, Any]] = [
        {"index": i, "length": len(s)} for i, s in enumerate(sentences)
    ]
    # ...
```

### Impacto
- ❌ **Violación de contrato**: Función acepta configuración pero la ignora
- ❌ **No-determinismo**: Sin normalización Unicode, textos con diferentes encodings producen outputs diferentes
- ❌ **Pérdida de calidad**: Caracteres acentuados, ligaduras, etc. no normalizados
- ❌ **Fallo de auditoría**: TODO en producción indica funcionalidad incompleta
- ❌ **Downgrade masivo**: Split por `\n` es algoritmo de complejidad mínima, no máxima

### Evidencia de Diseño Correcto
En `configs.py` líneas 30-46:
```python
class NormalizeConfig(BaseModel):
    """Configuration for normalize phase."""

    unicode_form: Literal["NFC", "NFKC"] = "NFC"
    keep_diacritics: bool = True

    @classmethod
    def from_env(cls) -> NormalizeConfig:
        """Create config from environment variables."""
        return cls(
            unicode_form=os.getenv("FLUX_NORMALIZE_UNICODE_FORM", "NFC"),
            keep_diacritics=os.getenv("FLUX_NORMALIZE_KEEP_DIACRITICS", "true").lower() == "true",
        )
```

**La configuración EXISTE y está bien diseñada, pero NO SE USA.**

---

## 2. BUG CRÍTICO: Normalización Unicode NO Implementada

### Problema
El comentario `# TODO: Implement actual normalization (unicode normalization, etc.)` en línea 345 indica que la funcionalidad FUNDAMENTAL no está implementada.

### Qué Debería Hacer
Según el README (línea 31):
> Unicode NFC normalization | ✅ | ICU-compatible via Rust

La normalización Unicode debería:
1. Aplicar NFC o NFKC según configuración
2. Normalizar espacios en blanco (múltiples espacios → uno, tabs → espacios)
3. Normalizar caracteres combinados (é puede ser U+00E9 o U+0065+U+0301)
4. Preservar o eliminar diacríticos según `keep_diacritics`
5. Garantizar output determinista byte-a-byte

### Código Esperado (Alto Estándar)
```python
import unicodedata
import re

# Normalización Unicode
normalized_text = unicodedata.normalize(cfg.unicode_form, ing.raw_text)

# Normalización de espacios
normalized_text = re.sub(r'\s+', ' ', normalized_text)  # Múltiples espacios → uno
normalized_text = re.sub(r'\t', ' ', normalized_text)  # Tabs → espacios
normalized_text = re.sub(r' \n ', '\n', normalized_text)  # Limpiar alrededor de \n

# Eliminar diacríticos si configurado
if not cfg.keep_diacritics:
    # NFD descompone é → e + ́ (acento)
    nfd = unicodedata.normalize('NFD', normalized_text)
    # Filtrar caracteres de combinación (categoría Mn)
    normalized_text = ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')
    # Volver a componer
    normalized_text = unicodedata.normalize('NFC', normalized_text)

# Segmentación de oraciones (NO split simplista)
# Opción 1: Usar spaCy
import spacy
nlp = spacy.load("es_core_news_sm")
doc = nlp(normalized_text)
sentences = [sent.text for sent in doc.sents]

# Opción 2: Usar regex sofisticado (fallback)
import re
# Pattern que respeta abreviaturas, decimales, etc.
sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', normalized_text)
```

### Impacto
- ❌ **Irreproducibilidad**: Diferentes encodings → diferentes outputs
- ❌ **Pérdida de calidad lingüística**: Split por `\n` rompe oraciones reales
- ❌ **Violación de especificación**: README promete NFC, código no lo hace

---

## 3. BUG CRÍTICO: Split Simplista por `\n`

### Código Actual
```python
sentences = [s for s in ing.raw_text.split("\n") if s.strip()]
```

### Problemas
1. **Asume que `\n` = límite de oración**
   - ❌ Falso: PDFs pueden tener `\n` por wrapping de línea, no fin de oración
   - ❌ Ejemplo: "El presupuesto\npara 2024 es..." → se divide incorrectamente

2. **No respeta puntuación real**
   - ❌ "Hola. Mundo" en misma línea → UNA oración (incorrecto)
   - ❌ "Objetivo: aumentar..." → se corta (incorrecto)

3. **No maneja casos especiales**
   - ❌ Abreviaturas: "Sr. Juan" → se corta en "Sr." (incorrecto)
   - ❌ Listas numeradas: "1. Primero\n2. Segundo" → cortes incorrectos

4. **Violación del principio de máxima complejidad**
   - Usuario exigió: "NO ENFRENTES LA COMPLEJIDAD POR EL CAMINO FÁCIL"
   - Split por `\n` es literalmente el camino más fácil y menos correcto

### Solución de Alto Estándar
```python
# Usar spaCy para segmentación real
import spacy
nlp = spacy.load("es_core_news_lg")  # Modelo grande para máxima precisión

# Procesar con pipeline completo
doc = nlp(normalized_text)

# Extraer oraciones con metadata rica
sentences = []
sentence_meta = []

for i, sent in enumerate(doc.sents):
    sentences.append(sent.text)

    sentence_meta.append({
        "index": i,
        "length": len(sent.text),
        "char_start": sent.start_char,
        "char_end": sent.end_char,
        "token_count": len(sent),
        "has_verb": any(token.pos_ == "VERB" for token in sent),
        "entities": [ent.text for ent in sent.ents],
        "root_lemma": sent.root.lemma_,
    })
```

---

## 4. BUG ALTO: SmartChunkConverter Pérdida de Embeddings

### Ubicación
- **Archivo:** `src/saaaaaa/processing/spc_ingestion/converter.py`
- **Línea:** 489-494

### Código
```python
# Add embeddings if available (as lists for JSON serialization)
if hasattr(sc, 'semantic_embedding') and sc.semantic_embedding is not None:
    try:
        import numpy as np
        chunk_data['semantic_embedding'] = sc.semantic_embedding.tolist()
    except Exception:
        pass  # Skip if conversion fails ← 🔴 SILENT FAILURE
```

### Problema
- **Silent failure**: Si numpy falla o tolist() falla, se pierde el embedding SIN ADVERTENCIA
- **Violación de provenance**: Embeddings son parte crítica de SPC rich data
- **No hay logging**: Fallo silencioso imposibilita debug

### Fix de Alto Estándar
```python
# Add embeddings if available (as lists for JSON serialization)
if hasattr(sc, 'semantic_embedding') and sc.semantic_embedding is not None:
    try:
        import numpy as np
        if not isinstance(sc.semantic_embedding, np.ndarray):
            self.logger.warning(
                f"Chunk {sc.chunk_id}: semantic_embedding is not np.ndarray, got {type(sc.semantic_embedding)}"
            )
        else:
            chunk_data['semantic_embedding'] = sc.semantic_embedding.tolist()
            chunk_data['embedding_dim'] = sc.semantic_embedding.shape[0]
    except ImportError as e:
        self.logger.error(f"Chunk {sc.chunk_id}: Failed to import numpy: {e}")
        raise RuntimeError("NumPy is required for embedding preservation") from e
    except Exception as e:
        self.logger.error(f"Chunk {sc.chunk_id}: Failed to convert embedding: {e}")
        raise RuntimeError(f"Embedding conversion failed: {e}") from e
```

**Racionalidad**: Si embeddings no se pueden preservar, el sistema DEBE fallar (fail-fast), no continuar con datos degradados.

---

## 5. BUG MEDIO: Quality Gates No Validan provenance_completeness = 1.0

### Ubicación
- **Archivo:** `src/saaaaaa/processing/spc_ingestion/quality_gates.py`
- **Líneas:** 62-111

### Problema
La clase `SPCQualityGates` valida:
- ✅ Chunk count (MIN_CHUNKS = 5, MAX_CHUNKS = 200)
- ✅ Chunk length (50-5000 chars)
- ✅ Strategic score (>= 0.3)
- ✅ Quality score (>= 0.5)

Pero **NO** valida:
- ❌ `provenance_completeness = 1.0` (requerido por README)
- ❌ `structural_consistency >= 1.0` (requerido por FASE 3)
- ❌ Embeddings presentes y dimensión correcta
- ❌ Causal chains no vacías para chunks DIAGNOSTICO

### Fix de Alto Estándar
```python
class SPCQualityGates:
    # Agregar thresholds
    MIN_PROVENANCE_COMPLETENESS = 1.0  # 100% required
    MIN_STRUCTURAL_CONSISTENCY = 1.0
    MIN_EMBEDDING_DIM = 384

    def validate_quality_metrics(self, quality_metrics: QualityMetrics) -> Dict[str, Any]:
        """
        Validate quality metrics from CanonPolicyPackage.

        Enforces strict thresholds per README specifications.
        """
        failures = []

        # CRITICAL: Provenance completeness must be 100%
        if quality_metrics.provenance_completeness < self.MIN_PROVENANCE_COMPLETENESS:
            failures.append(
                f"Provenance completeness below threshold: "
                f"{quality_metrics.provenance_completeness:.2%} < {self.MIN_PROVENANCE_COMPLETENESS:.0%}"
            )

        # CRITICAL: Structural consistency must be perfect
        if quality_metrics.structural_consistency < self.MIN_STRUCTURAL_CONSISTENCY:
            failures.append(
                f"Structural consistency below threshold: "
                f"{quality_metrics.structural_consistency:.2%} < {self.MIN_STRUCTURAL_CONSISTENCY:.0%}"
            )

        # Check boundary F1
        if quality_metrics.boundary_f1 < 0.85:
            failures.append(f"Boundary F1 too low: {quality_metrics.boundary_f1:.2f} < 0.85")

        # Check budget consistency
        if quality_metrics.budget_consistency_score < 0.95:
            failures.append(
                f"Budget consistency too low: {quality_metrics.budget_consistency_score:.2f} < 0.95"
            )

        return {
            "passed": len(failures) == 0,
            "failures": failures,
        }
```

---

## MATRIZ DE PRIORIDADES PARA FIXES

| Bug | Severidad | Impacto | Esfuerzo | Prioridad |
|-----|-----------|---------|----------|-----------|
| 1. run_normalize() ignora config | 🔴 CRÍTICO | MUY ALTO | 4 horas | P0 |
| 2. Unicode normalization no implementada | 🔴 CRÍTICO | MUY ALTO | 6 horas | P0 |
| 3. Split simplista por \n | 🔴 CRÍTICO | ALTO | 8 horas | P0 |
| 4. SmartChunkConverter silent fail | 🟡 ALTO | MEDIO | 2 horas | P1 |
| 5. Quality gates incompletos | 🟡 MEDIO | MEDIO | 3 horas | P1 |

**Tiempo total estimado**: 23 horas (3 días)

---

## PLAN DE ACCIÓN INMEDIATO

### Día 1: Fixes Críticos de Normalización
1. **Implementar normalización Unicode completa** (6h)
   - NFC/NFKC según config
   - Normalización de espacios
   - Eliminación opcional de diacríticos
   - Tests unitarios con casos edge

2. **Implementar segmentación de oraciones con spaCy** (4h)
   - Cargar modelo es_core_news_lg
   - Extraer oraciones reales
   - Metadata rica por oración
   - Tests con PDFs reales

3. **Integrar config en run_normalize()** (2h)
   - Leer cfg.unicode_form
   - Leer cfg.keep_diacritics
   - Validar precondiciones
   - Logging detallado

### Día 2: Fixes de Data Integrity
4. **Fix SmartChunkConverter fail-fast** (2h)
   - Eliminar try-except silencioso
   - Logging de errores
   - Validación de embeddings
   - Tests de failure cases

5. **Extender Quality Gates** (3h)
   - Validar provenance_completeness = 1.0
   - Validar structural_consistency
   - Validar embeddings
   - Tests exhaustivos

### Día 3: Validación y Documentación
6. **Tests de integración** (4h)
   - Pipeline completo con documento real
   - Validar determinismo (10 runs)
   - Validar quality metrics
   - Comparar con baseline

7. **Documentación y PR** (2h)
   - Actualizar README
   - Changelog detallado
   - Migration guide
   - PR con evidencia de fixes

---

## VALIDACIÓN DE MÁXIMO ESTÁNDAR

Para cada fix, validar:

✅ **No downgrades**: Funcionalidad nueva >= funcionalidad anterior
✅ **Complejidad apropiada**: Algoritmos SOTA, no shortcuts
✅ **Determinismo**: Mismo input → mismo output byte-a-byte
✅ **Trazabilidad**: Logging completo, provenance 100%
✅ **Fail-fast**: Errores fallan inmediatamente, no se propagan
✅ **Configurabilidad**: Todos los parámetros expuestos en config
✅ **Tests**: Cobertura >= 95%, edge cases incluidos

---

## REFERENCIAS

- README.md: SPC Phase-One como punto de entrada canónico
- CANONICAL_FLUX.md: Arquitectura determinista del pipeline
- src/saaaaaa/processing/spc_ingestion/__init__.py: CPPIngestionPipeline (ÚNICO punto de entrada)
- src/saaaaaa/flux/configs.py líneas 30-46: NormalizeConfig bien diseñada
- src/saaaaaa/flux/phases.py: FLUX Phase 2 (normalize) - tenía TODO en producción (AHORA CORREGIDO)
- src/saaaaaa/processing/spc_ingestion/quality_gates.py: SPCQualityGates (AHORA EXTENDIDO)
- src/saaaaaa/processing/spc_ingestion/converter.py: SmartChunkConverter (AHORA CON FAIL-FAST)

---

**Conclusión**: Sistema tiene arquitectura clara con SPC como Phase-One canónico. FLUX proporciona fases complementarias. Los bugs críticos en FLUX Phase 2 (normalize) y SPC quality gates han sido CORREGIDOS implementando máximo estándar:

✅ **FLUX run_normalize()**: Unicode NFC/NFKC + spaCy sentence segmentation + metadata rica
✅ **SPC SmartChunkConverter**: Fail-fast en pérdida de embeddings (no silent failures)
✅ **SPC SPCQualityGates**: Validación de provenance_completeness = 1.0 y structural_consistency = 1.0

**Estado**: TODOS LOS BUGS CRÍTICOS CORREGIDOS - Sistema ahora opera en MÁXIMO ESTÁNDAR.
