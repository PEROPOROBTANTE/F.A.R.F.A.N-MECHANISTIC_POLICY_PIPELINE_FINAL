# Canonical Systems Engineering: Documentation

## Overview

This document defines the **canonical, authoritative** ontology and systems architecture for the policy analysis pipeline. Any deviation from these definitions is a **DEFECT**.

---

## 1. Policy Areas (PAs) - CLOSED ONTOLOGY

**Source of Truth**: `data/questionnaire_monolith.json`

The Policy Areas represent a **closed, canonical ontology** derived from the questionnaire monolith. No additions, merges, renaming, clustering, "improvements," or extrapolations are permitted.

### Canonical Policy Areas

| ID | Questions | Status |
|----|-----------|--------|
| PA01 | 30 | Canonical |
| PA02 | 30 | Canonical |
| PA03 | 30 | Canonical |
| PA04 | 30 | Canonical |
| PA05 | 30 | Canonical |
| PA06 | 30 | Canonical |
| PA07 | 30 | Canonical |
| PA08 | 30 | Canonical |
| PA09 | 30 | Canonical |
| PA10 | 30 | Canonical |

**Total**: 10 Policy Areas, 300 questions

**Artifact**: `config/canonical_ontologies/policy_areas_and_dimensions.json`

### Policy Area Rules

1. **Closed Set**: These 10 PAs are the complete universe. No PA11, no custom areas.
2. **Immutable**: Names and semantics are fixed. No renaming PA01 to "Education" or similar.
3. **No Clustering**: Do not group PAs into meta-categories unless explicitly defined in the source.
4. **Validation**: All code referencing policy areas must use PA01-PA10 identifiers.

---

## 2. Dimensions of Analysis (DoA)

**Source of Truth**: `data/questionnaire_monolith.json`

There are **exactly six** Dimensions of Analysis. Their names, semantics, and usage are those defined in the questionnaire monolith. No synonyms, parallel taxonomies, or restructuring allowed.

### Canonical Dimensions

| ID | Questions | Status |
|----|-----------|--------|
| DIM01 | 50 | Canonical |
| DIM02 | 50 | Canonical |
| DIM03 | 50 | Canonical |
| DIM04 | 50 | Canonical |
| DIM05 | 50 | Canonical |
| DIM06 | 50 | Canonical |

**Total**: 6 Dimensions, 300 questions

**Artifact**: `config/canonical_ontologies/policy_areas_and_dimensions.json`

### Dimension Rules

1. **Exactly Six**: Not 5, not 7. Six dimensions, no more, no less.
2. **Canonical Names**: Use DIM01-DIM06. No "Dimension of Financial Viability" or similar verbose aliases.
3. **Convergence**: All documentation and code must converge on this single canonical set.
4. **No Parallel Taxonomies**: No alternative dimension systems alongside these.

---

## 3. F.A.R.F.A.N Framework

**Scope**: Colombian municipal Development Plans **ONLY**

F.A.R.F.A.N is a **specialized framework** exclusively for analyzing Colombian municipal Development Plans. It is:
- **Not** a generic unit of analysis
- **Not** a meta-framework
- **Not** portable by default to other domains

### Framework Rules

1. **Domain-Specific**: Use only for Colombian municipal plans.
2. **Spec Violations**: Any use outside this domain must be explicitly justified and documented.
3. **No Generalization**: Do not attempt to make F.A.R.F.A.N "generic" without explicit requirements.

---

## 4. Lexical Discipline

**Canonical Spelling**: CALIBRATION

**Prohibited**: CALLIBRATION

### Enforcement

All occurrences must use the correct spelling:
- Python code (variables, functions, classes, comments, docstrings)
- JSON configurations
- YAML files
- Markdown documentation

**Audit Status**: ✅ Clean (no misspellings found in codebase)

---

## 5. Method Canonicalization

### Canonical Method Catalog

**Source**: `config/rules/METODOS/complete_canonical_catalog.json`  
**Python Module**: `src/saaaaaa/core/orchestrator/complete_canonical_catalog.py`

**Version**: 3.0.0  
**Methods**: 590 canonical methods across 53 classes

### Catalog Rules

1. **Single Source of Truth**: The JSON catalog is authoritative.
2. **Canonical Identifiers**: Use exact class name + method name from catalog.
3. **No Local Variants**: Where local usage conflicts with catalog, **local usage is WRONG**.
4. **Alias Normalization**: All aliases, misspellings, or variants must be normalized to canonical forms.

### Usage

```python
from saaaaaa.core.orchestrator.complete_canonical_catalog import (
    CATALOG,
    get_canonical_method,
    validate_method_is_canonical
)

# Get a method
method = get_canonical_method("PDETMunicipalPlanAnalyzer", "analyze_municipal_plan")

# Validate a method reference
validate_method_is_canonical("SomeClass", "some_method")  # Raises if not canonical
```

---

## 6. Registry-Catalog Integrity

### Calibration Registry

**File**: `src/saaaaaa/core/orchestrator/calibration_registry.py`

**Methods**: 180 calibrated methods

### Alignment Requirements

1. **One-to-One Mapping**: Every catalogued method should have a corresponding registry entry (or explicit absence).
2. **No Orphans**: No registry method should be missing from the catalog.
3. **Audit Trail**: Use `scripts/audit_catalog_registry_alignment.py` to verify alignment.

### Current Status

**Alignment Score**: 23.22% (137/590 methods aligned)

**Defects**: 65 total
- 43 methods in registry but not in catalog
- 22 methods used but not in catalog

**Action Required**: Resolve defects by either:
1. Adding missing methods to catalog
2. Removing invalid entries from registry
3. Updating codebase to use canonical methods

---

## 7. Usage Intelligence

### Method Usage Scanner

**Script**: `scripts/build_method_usage_intelligence.py`  
**Output**: `config/method_usage_intelligence.json`

### Tracked Metrics

For every method:
- **Usage Count**: Total references across repository
- **Usage Locations**: File, line, context
- **Pipelines**: Processes/pipelines using this method
- **Execution Topology**: Solo, Sequential, Parallel, Interconnected
- **Parameterization Locus**:
  - In-script (hardcoded parameters)
  - In YAML (🚩 RED FLAG - should migrate to registry)
  - In calibration_registry.py (preferred)

### Current Statistics

- **Total Tracked**: 612 methods
- **In Catalog**: 590
- **Not in Catalog** (DEFECT): 22
- **In Registry**: 137
- **Never Used**: 590

---

## 8. Auto-Calibration Decision System

### Calibration Classifier

**Script**: `scripts/build_calibration_decisions.py`  
**Output**: `config/calibration_decisions.json`

### Decision Categories

1. **REQUIRES_CALIBRATION**: Method must have calibration entry
2. **NO_CALIBRATION_REQUIRED**: Simple utility, no calibration needed
3. **FLAG_FOR_REVIEW**: Inconclusive, needs human review

### Decision Criteria

Methods require calibration if they:
- Have CRITICAL or HIGH priority
- Have HIGH complexity
- Are used in critical paths
- Have numeric_support or temporal_support requirements
- Are called frequently (>10 usages)
- Have configurable parameters
- Perform scoring, evaluation, or analysis

Methods don't need calibration if they:
- Have LOW priority and LOW complexity
- Are simple utilities (__init__, getters, formatters)
- Have zero configurable parameters
- Are never used in scoring/evidence logic

### Current Decisions

- **REQUIRES_CALIBRATION**: 235 methods (39.8%)
- **NO_CALIBRATION_REQUIRED**: 254 methods (43.1%)
- **FLAG_FOR_REVIEW**: 101 methods (17.1%)

---

## 9. Execution Standard

All transformations must be:

1. **Repository-Wide**: Apply consistently across entire codebase
2. **Consistent**: No exceptions, no partial cleanups
3. **Idempotent**: Can be run multiple times safely
4. **Machine-Verifiable**: Output must be checkable programmatically
5. **Explicit**: Defects marked explicitly, not as "uncertainty"

### Anti-Patterns (Prohibited)

❌ Partial cleanups  
❌ Undocumented exceptions  
❌ Speculative additions  
❌ Naming drift  
❌ Conceptual freelancing  
❌ "I thought this sounded better"  
❌ Fuzzy guidance without executable rules

---

## 10. Auditing & Verification

### Alignment Audit

**Script**: `scripts/audit_catalog_registry_alignment.py`

Run to verify catalog-registry-usage alignment:

```bash
python scripts/audit_catalog_registry_alignment.py
```

### Expected Output

- Inventory counts
- Alignment analysis
- Defect report
- Warning report
- Alignment scores
- Pass/Fail status

### Success Criteria

- **Zero Defects**: No methods in registry missing from catalog
- **Zero Defects**: No used methods missing from catalog
- **Alignment Score** > 80%: High catalog-registry alignment

---

## 11. Maintenance Workflows

### Adding a New Method

1. Add to canonical catalog JSON
2. Regenerate Python catalog module
3. Run usage intelligence scanner
4. Run calibration decision classifier
5. Add calibration entry if required
6. Run alignment audit
7. Verify no defects

### Modifying a Method

1. Update canonical catalog JSON
2. Update calibration registry if applicable
3. Regenerate all derived artifacts
4. Run alignment audit

### Deprecating a Method

1. Mark in catalog as deprecated
2. Remove from calibration registry
3. Update usage intelligence
4. Verify no active usages
5. Remove from catalog

---

## 12. Artifact Manifest

| Artifact | Type | Description |
|----------|------|-------------|
| `config/canonical_ontologies/policy_areas_and_dimensions.json` | Data | Canonical PA & DoA definitions |
| `config/rules/METODOS/complete_canonical_catalog.json` | Data | Canonical method universe (590 methods) |
| `src/saaaaaa/core/orchestrator/complete_canonical_catalog.py` | Code | Programmatic catalog access |
| `src/saaaaaa/core/orchestrator/calibration_registry.py` | Code | Method calibration metadata (180 methods) |
| `config/method_usage_intelligence.json` | Data | Usage metrics & topology (612 methods tracked) |
| `config/calibration_decisions.json` | Data | Auto-calibration decisions |
| `config/alignment_audit_report.json` | Data | Catalog-registry-usage alignment audit |
| `scripts/build_method_usage_intelligence.py` | Tool | Usage intelligence scanner |
| `scripts/build_calibration_decisions.py` | Tool | Auto-calibration classifier |
| `scripts/audit_catalog_registry_alignment.py` | Tool | Alignment auditor |

---

## 13. References

- **Questionnaire Monolith**: `data/questionnaire_monolith.json`
- **Method Catalog**: `config/rules/METODOS/complete_canonical_catalog.json`
- **Calibration Registry**: `src/saaaaaa/core/orchestrator/calibration_registry.py`

---

## Status Summary

✅ **Canonical PA Ontology**: Defined (10 PAs)  
✅ **Canonical DoA Ontology**: Defined (6 dimensions)  
✅ **Lexical Discipline**: Clean (no misspellings)  
✅ **Method Catalog**: Created (590 methods)  
✅ **Usage Intelligence**: Operational (612 methods tracked)  
✅ **Auto-Calibration**: Operational (3 decision categories)  
❌ **Alignment Integrity**: FAIL (65 defects)  
⚠️ **F.A.R.F.A.N Scope**: Validated but not enforced in code

**Next**: Resolve 65 alignment defects to achieve PASS status.
