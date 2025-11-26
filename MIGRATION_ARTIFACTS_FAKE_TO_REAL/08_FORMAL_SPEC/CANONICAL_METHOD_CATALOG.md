# Canonical Method Catalog System

**Version:** 1.0.0  
**Status:** Active  
**Authority:** Directive-Compliant Universal Method Registry

---

## Executive Summary

This document defines the **Canonical Method Catalog System**, the single authoritative source for method identification, calibration tracking, and migration management in this repository.

**Key Principles:**
- ✅ **Universal Coverage** - No method can be omitted, filtered, or hidden
- ✅ **Single Source of Truth** - No conceptual splits without formal authorization
- ✅ **Machine-Readable** - Calibration requirements are mechanically decidable
- ✅ **Complete Tracking** - All calibration implementations are visible and tracked
- ✅ **Migration Path** - Transitional cases are explicitly managed

---

## System Architecture

### 1. Canonical Method Catalog

**File:** `config/canonical_method_catalog.json`

The catalog contains **complete metadata** for ALL methods in the repository:

```json
{
  "metadata": {
    "generated_at": "ISO8601 timestamp",
    "version": "1.0.0",
    "purpose": "Canonical method catalog - universal coverage per directive",
    "total_methods": 1996,
    "directive_compliance": {
      "universal_coverage": true,
      "machine_readable_flags": true,
      "no_filters_applied": true,
      "single_canonical_source": true
    }
  },
  "summary": {
    "total_methods": 1996,
    "by_layer": {...},
    "by_calibration_status": {...},
    "calibration_coverage": {...}
  },
  "methods": [...]
}
```

### 2. Method Metadata Schema

Each method includes:

```typescript
{
  // Core identification
  unique_id: string,          // SHA256 hash (first 16 chars)
  canonical_name: string,     // module.ClassName.method_name
  method_name: string,
  class_name: string | null,
  file_path: string,
  
  // Layer positionality
  layer: string,              // orchestrator, executor, analyzer, etc.
  layer_position: number,     // Position within layer (0-based)
  
  // Signature and interface
  signature: string,
  input_parameters: [...],
  return_type: string | null,
  
  // Calibration tracking (CRITICAL)
  requires_calibration: boolean,  // Machine-readable flag
  calibration_status: string,     // "centralized" | "embedded" | "none" | "unknown"
  calibration_location: string | null,  // File:line if embedded
  
  // Additional metadata
  docstring: string | null,
  decorators: [...],
  is_async: boolean,
  is_private: boolean,
  is_abstract: boolean,
  complexity: string,
  
  // Source tracking
  line_number: number,
  source_hash: string,
  last_analyzed: string
}
```

### 3. Calibration Status Taxonomy

| Status | Meaning | Count | Action Required |
|--------|---------|-------|-----------------|
| **centralized** | Uses `calibration_registry.py` | 177 | ✅ Compliant |
| **embedded** | Has inline/local parametrization | 61 | ⚠️ Migration needed |
| **none** | Does not require calibration | 1438 | ✅ Compliant |
| **unknown** | Requires investigation | 320 | ⚠️ Needs analysis |

### 4. Layer Classification

Methods are organized into layers:

- **orchestrator** (632 methods) - Core orchestration logic
- **analyzer** (601 methods) - Analysis and scoring methods
- **processor** (291 methods) - Processing and transformation
- **utility** (211 methods) - Helper and utility functions
- **unknown** (230 methods) - Needs classification
- **ingestion** (29 methods) - Document ingestion
- **executor** (2 methods) - Direct executors

---

## Calibration Tracking

### Centralized Calibration (177 methods)

**Location:** `src/saaaaaa/core/orchestrator/calibration_registry.py`

Methods with centralized calibration are **fully compliant**. They use the canonical calibration system with:
- Explicit `MethodCalibration` entries
- Context-aware modifiers
- Version tracking and hashing
- No silent defaults

**Example:**
```python
("BayesianNumericalAnalyzer", "evaluate_policy_metric"): MethodCalibration(
    score_min=0.0, score_max=1.0,
    min_evidence_snippets=6,
    max_evidence_snippets=30,
    contradiction_tolerance=0.05,
    uncertainty_penalty=0.45,
    aggregation_weight=1.5,
    sensitivity=0.98,
    requires_numeric_support=True,
    requires_temporal_support=False,
    requires_source_provenance=True,
)
```

### Embedded Calibration (61 methods)

**Status:** Transitional Anomalies - Explicitly Tracked  
**Document:** `config/embedded_calibration_appendix.md`  
**Machine-Readable:** `config/embedded_calibration_appendix.json`

Methods with embedded calibration have **local parametrization** that must be migrated to the centralized system.

**Migration Priority Breakdown:**
- **Critical:** 3 methods (executors, scoring methods)
- **High:** 10 methods (analyzers with many parameters)
- **Medium:** 20 methods (other analyzers and processors)
- **Low:** 28 methods (utilities and simple cases)

**Detected Patterns:**
- `explicit_parameters` - Named threshold/weight variables
- `config_dict` - Configuration dictionaries
- `magic_numbers` - Numeric literals in calculations

**Example Critical Case:**
```python
# src.saaaaaa.analysis.scoring.scoring.score_type_a
def score_type_a(self, evidence):
    threshold = 0.7  # ⚠️ EMBEDDED - should be in calibration_registry
    min_snippets = 3  # ⚠️ EMBEDDED
    weight = 1.2  # ⚠️ EMBEDDED
    # ...
```

### Unknown Status (320 methods)

Methods marked as "unknown" **require investigation** to determine:
1. Whether they truly need calibration
2. If calibration is hidden elsewhere
3. If they should be reclassified as "none"

---

## Compliance Requirements

### 1. Universal Coverage

**Requirement:** Every method in the repository must be in the catalog.

**Enforcement:**
```bash
python3 scripts/build_canonical_method_catalog.py
```

This scans ALL Python files without filters or exceptions.

### 2. Machine-Readable Calibration Flags

**Requirement:** Calibration requirements must be mechanically decidable.

**Implementation:**
- `requires_calibration` boolean flag on every method
- Based on method name patterns, layer, and explicit registry presence
- No subjective "simplicity" judgments

**Decision Algorithm:**
```python
def requires_calibration(method):
    # 1. In calibration registry → YES
    if in_calibration_registry(method):
        return True
    
    # 2. Name indicates calibration need
    calibration_indicators = [
        "score", "compute", "evaluate", "analyze",
        "aggregate", "weight", "threshold"
    ]
    if any(ind in method.name.lower() for ind in calibration_indicators):
        return True
    
    # 3. In executor or analyzer layer
    if method.layer in ["executor", "analyzer"]:
        return True
    
    return False
```

### 3. Complete Calibration Tracking

**Requirement:** All calibration implementations must be visible.

**Status Tracking:**
- **Centralized:** Tracked in `calibration_registry.py`
- **Embedded:** Tracked in `embedded_calibration_appendix.json`
- **Unknown:** Listed for investigation
- **None:** Explicitly marked as not requiring calibration

### 4. Migration Backlog

**Requirement:** Transitional cases must be explicitly managed.

**Backlog:** `config/embedded_calibration_appendix.md`

Each entry includes:
- File path and line number
- Parametrization pattern
- Migration priority
- Migration complexity
- Parameter list

**Migration Process:**
1. Review appendix
2. Prioritize critical/high items
3. Extract parameters to `MethodCalibration` objects
4. Add to `calibration_registry.py`
5. Remove embedded parameters
6. Update catalog status to "centralized"
7. Re-run detection to verify

---

## Tools and Scripts

### Build Canonical Catalog

```bash
python3 scripts/build_canonical_method_catalog.py
```

Scans entire repository and generates `config/canonical_method_catalog.json`.

**Output:**
- Complete method inventory
- Layer classification
- Calibration requirement flags
- Calibration status determination

### Detect Embedded Calibrations

```bash
python3 scripts/detect_embedded_calibrations.py
```

Analyzes methods marked as "unknown" to find embedded calibrations.

**Output:**
- `config/embedded_calibration_appendix.json` (machine-readable)
- `config/embedded_calibration_appendix.md` (human-readable)

**Detection Patterns:**
- Variable patterns: `threshold|min|max|weight|penalty = <number>`
- Config dictionaries: `config = {...}`
- Magic numbers: Multiple numeric literals in code

### Validate Catalog

```bash
python3 scripts/validate_canonical_catalog.py
```

Validates catalog compliance with directive requirements.

**Checks:**
- All methods have unique IDs
- No duplicate canonical names
- All calibration statuses are valid
- Methods requiring calibration have status != "none"
- Embedded calibrations are documented

---

## Integration with Existing Systems

### Calibration Registry

**File:** `src/saaaaaa/core/orchestrator/calibration_registry.py`

The canonical catalog **references** the calibration registry as the source of truth for centralized calibrations.

**Relationship:**
- Catalog identifies which methods use the registry
- Registry contains the actual calibration parameters
- Both are versioned and hashed for reproducibility

### Executor System

**File:** `src/saaaaaa/core/orchestrator/executors.py`

Executors are the primary consumers of calibrations.

**Integration:**
- Catalog lists all executor methods
- Each executor method's calibration status is tracked
- Migration priority for executor calibrations is CRITICAL

### Layer Coexistence Model

The catalog's layer classification aligns with the Layer Coexistence and Influence model.

**Layers:**
- Orchestrator (layer 0)
- Executor (layer 1)
- Analyzer (layer 2)
- Processor (layer 3)
- Utility (layer 4)

---

## Maintenance and Updates

### Regular Updates

Run catalog build weekly or when significant code changes occur:

```bash
# Update catalog
python3 scripts/build_canonical_method_catalog.py

# Detect new embedded calibrations
python3 scripts/detect_embedded_calibrations.py

# Validate compliance
python3 scripts/validate_canonical_catalog.py
```

### Adding New Methods

When adding new methods:

1. **Determine calibration requirement**
   - Does it score, evaluate, or aggregate?
   - Is it in executor/analyzer layer?

2. **If calibration required:**
   - Add to `calibration_registry.py` immediately
   - Do NOT use embedded parameters

3. **Update catalog:**
   - Run `build_canonical_method_catalog.py`
   - Verify new method appears with status "centralized"

### Migrating Embedded Calibrations

For each embedded calibration:

1. **Extract parameters** from code
2. **Create `MethodCalibration` entry** in `calibration_registry.py`
3. **Update method code** to use `resolve_calibration()`
4. **Remove embedded parameters**
5. **Test** to ensure behavior unchanged
6. **Re-run catalog build** to update status

---

## Compliance Verification

### Automated Checks

```bash
# Check catalog completeness
python3 scripts/validate_canonical_catalog.py --check-completeness

# Check calibration coverage
python3 scripts/validate_canonical_catalog.py --check-calibration

# Check migration backlog
python3 scripts/validate_canonical_catalog.py --check-backlog
```

### Manual Review

Quarterly review:
1. Check migration backlog progress
2. Verify no new embedded calibrations introduced
3. Ensure "unknown" status count is decreasing
4. Validate layer classifications are accurate

---

## Prohibited Actions

**DO NOT:**
- Filter or omit methods from catalog
- Create separate "executor-only" or "subset" catalogs
- Introduce conceptual splits without formal authorization
- Use undocumented heuristics for calibration requirements
- Add new embedded calibrations (use `calibration_registry.py`)
- Remove methods from migration backlog without completing migration

**MUST:**
- Include ALL methods in canonical catalog
- Use machine-readable flags for all decisions
- Track ALL calibration implementations
- Document ALL transitional cases
- Maintain single source of truth

---

## Success Metrics

**Current Status:**

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Total methods tracked | 1996 | All methods | ✅ |
| Centralized calibrations | 177 | All requiring calib | 🔄 |
| Embedded calibrations | 61 | 0 | ⚠️ Migration needed |
| Unknown status | 320 | < 50 | 🔄 Investigation needed |
| Migration backlog | 61 | 0 | ⚠️ In progress |

**Goals:**
- ✅ Universal coverage achieved (1996 methods)
- 🔄 Migrate all 61 embedded calibrations
- 🔄 Investigate 320 unknown status methods
- 🔄 Achieve < 5% unknown rate
- ✅ Zero new embedded calibrations

---

## References

- **Directive:** Problem statement (universal coverage, no filters, machine-readable)
- **Calibration System:** `CALIBRATION_SYSTEM.md`
- **Layer Model:** `CANONICAL_SYSTEMS_ENGINEERING.md`
- **Registry Alignment:** `CATALOG_REGISTRY_ALIGNMENT_POLICY.md`

---

**Last Updated:** 2025-11-09  
**Owner:** Canonical Systems Engineering  
**Review Cycle:** Quarterly
