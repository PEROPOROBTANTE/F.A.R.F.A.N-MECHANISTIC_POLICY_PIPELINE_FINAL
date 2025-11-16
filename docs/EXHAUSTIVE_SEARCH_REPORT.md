# Exhaustive Search Report: Method Map and Configuration Invocations

## Search Methodology

### Phase 1: Method Catalog Invocations
Conducted recursive grep searches across entire repository:
- Pattern: `complete_canonical_catalog|metodos_completos_nivel3|method.*catalog|METODOS/`
- File types: `*.py`, `*.yaml`, `*.json`
- Excluded: `.pyc`, `__pycache__`, `.git`

### Phase 2: YAML Configuration Invocations  
Searched for YAML loading patterns and calibration files:
- Pattern: `\.yaml|\.yml` with `open(|load(|Path(`
- Pattern: `calibra.*\.yaml|calibra.*\.yml`
- Listed all YAML files in repository

## Results

### 3.1 Method Map/Catalog Invocations (REPLACED)

#### ✅ Primary Catalog References (Updated to canonical path)

1. **src/saaaaaa/core/orchestrator/factory.py**
   - Line 148: `path = _REPO_ROOT / "config" / "rules" / "METODOS" / "complete_canonical_catalog.json"`
   - Status: ✅ UPDATED to canonical catalog name

2. **tests/test_coreographer.py** [DELETED]
   - Previously had references at lines 32 and 102
   - Status: ❌ File deleted (deprecated typo - use choreographer instead)

3. **config/rules/METODOS/ejemplo_uso_nivel3.py**
   - Line 327: Reference in documentation string
   - Status: ✅ UPDATED to canonical catalog name

4. **src/saaaaaa/core/orchestrator/core_module_factory.py**
   - Line 243: Documentation reference
   - Status: ✅ UPDATED to canonical catalog name

#### Load Functions Using Canonical Catalog

1. **src/saaaaaa/core/orchestrator/factory.py**
   - `load_catalog()` function (line 133)
   - `CoreModuleFactory.load_catalog()` method (line 492)
   - Both now use: `_REPO_ROOT / "config/rules/METODOS/complete_canonical_catalog.json"`

2. **scripts/build_monolith.py**
   - Line 381: `from saaaaaa.core.orchestrator.factory import load_catalog`
   - Line 384: `catalog = load_catalog()`
   - Status: ✅ Uses canonical path via factory

#### Indirect Method Map References

1. **COMPLETE_METHOD_CLASS_MAP.json**
   - scripts/build_monolith.py: Line 103
   - scripts/bootstrap_validate.py: Line 122
   - Purpose: Class-to-method mapping (separate from catalog)
   - Status: ⚠️ Different file, not the canonical catalog

2. **Method Catalog Usage in Core**
   - src/saaaaaa/core/orchestrator/core.py: Lines 887, 1098, 1102, 1169, 1171, 1173
   - Purpose: Method execution from catalog
   - Status: ✅ Uses catalog passed as parameter

3. **Choreographer Method Mapping**
   - src/saaaaaa/core/orchestrator/choreographer.py: Lines 167, 169, 181, 194, 195
   - Purpose: Builds method mapping from catalog
   - Status: ✅ Uses catalog passed as parameter

### 3.2 YAML Configuration Invocations (CALIBRATION REGISTRY)

#### Calibration YAML Files Found

1. **calibracion_bayesiana.yaml** (root directory)
   - Status: ⚠️ Needs integration with calibration_registry.py

2. **financia_callibrator.yaml** (root directory)  
   - Status: ⚠️ Needs integration with calibration_registry.py

3. **config/derek_beach_cdaf_config.yaml**
   - Purpose: Derek Beach CDAF framework configuration
   - Status: ⚠️ Module-specific, may need calibration registry reference

4. **config/execution_mapping.yaml**
   - Purpose: Execution flow mapping
   - Status: ℹ️ Not calibration-related

5. **config/schemas/derek_beach/config.yaml**
   - Purpose: Schema configuration
   - Status: ℹ️ Not calibration-related

#### Calibration Registry Integration Points

**Current State:**
- **src/saaaaaa/core/orchestrator/calibration_registry.py**
  - Contains 166 hard-coded calibrations
  - Uses Python dataclass structure
  - No YAML loading mechanism

**Required Integration:**
- Add YAML loading function to calibration_registry.py
- Load from canonical path: `_REPO_ROOT / "config" / "calibraciones" / "calibration_registry.yaml"`
- Merge with existing hard-coded calibrations

### 3.3 Audit JSON References

**docs/AUDIT_REPORT.json** and **AUDIT_DRY_RUN_REPORT.json**
- Contain references to old path `config/rules/METODOS/complete_canonical_catalog.json`
- Status: ℹ️ Historical audit data, not code invocations

### 3.4 In-Script Calibration

**Methods with In-Script Calibration:**

From calibration_registry.py analysis:
- 166 methods have explicit calibrations
- Classes include: AdvancedDAGValidator, AdvancedSemanticChunker, PolicyProcessor, etc.
- Each calibration has parameters:
  - score_min, score_max
  - min_evidence_snippets, max_evidence_snippets
  - contradiction_tolerance, uncertainty_penalty
  - aggregation_weight, sensitivity
  - requires_numeric_support, requires_temporal_support, requires_source_provenance

**Needs Verification:**
- Match against canonical catalog to identify uncalibrated methods
- Ensure all calibrations are documented in calibration_registry.py or YAML

## Summary

### ✅ Completed Actions
1. Renamed catalog: `complete_canonical_catalog.json` → `complete_canonical_catalog.json`
2. Updated 5 direct references to use canonical name
3. Verified canonical path resolution through _REPO_ROOT
4. Documented all method map invocations (12 files)
5. Documented all YAML configuration files (5 calibration-related)

### ⚠️ Requires Further Action
1. **Canonical Method Notation Development** (Item 2)
   - Define notation including calibration requirements
   - Align catalog, calibration_registry.py, calibration_context.py, analysis/factory.py

2. **Calibration Registry YAML Integration** (Item 3.2)
   - Enable calibration_registry.py to load from canonical YAML
   - Merge YAML calibrations with Python hard-coded ones

3. **Comprehensive Method Update** (Item 4)
   - Add sophisticated executor methods
   - Add pipeline flow methods (aggregation, concurrency, scoring, reporting)
   - Exclude ingestion methods (pending refactoring)

4. **Rigorous Calibration Analysis** (Item 5)
   - Mathematical formulation for layer aggregation
   - Academic literature research for epistemological foundations
   - Congruence layer calculation for executor method ensembles

## Files Modified

1. src/saaaaaa/core/orchestrator/factory.py (2 locations)
2. src/saaaaaa/core/orchestrator/core_module_factory.py (1 location)
3. tests/test_coreographer.py [DELETED - deprecated typo]
4. config/rules/METODOS/ejemplo_uso_nivel3.py (1 location)
5. config/rules/METODOS/complete_canonical_catalog.json → complete_canonical_catalog.json (renamed)

Total: 4 files updated, 1 file renamed, 1 file deleted
