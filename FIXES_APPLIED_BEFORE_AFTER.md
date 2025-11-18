# Critical Fixes Applied - Before/After Comparison

## Executive Summary

This document provides concrete evidence of fixes applied to address non-functional code in the canonical systems implementation. All issues raised in code review have been resolved.

---

## Issue #1: Usage Intelligence Scanner Non-Functional

### BEFORE (Broken)
```
Total methods tracked: 612
Methods with usage > 0: 22
Catalog methods with usage > 0: 0  ❌

Top "used" methods:
  super.__init__: 51 usages
  Path.resolve: 7 usages
  str.lower: 7 usages
  str.upper: 6 usages
  (all Python builtins/library methods)
```

**Problem**: Scanner only detected generic Python method calls (`super.__init__`, `str.lower`), not catalog methods.

**Root Cause**: AST visitor had no type inference - couldn't match `obj.method()` calls to catalog classes.

### AFTER (Fixed)
```
Total methods tracked: 590
Methods with usage > 0: 292
Catalog methods with usage > 0: 292  ✅

Top used catalog methods:
  ConfigLoader.get: 913 usages
  EmbeddingProtocol.encode: 22 usages
  AdvancedDAGValidator.add_node: 17 usages
  EvidenceBundle.to_dict: 11 usages
  ProcessorConfig.validate: 8 usages
  AdvancedDAGValidator.add_edge: 7 usages
  DerekBeachProducer.counterfactual_query: 7 usages
```

**Fix Applied**:
1. Enhanced `MethodCallVisitor` to track imports and class instances
2. Match method calls against catalog using multiple heuristics
3. Only track catalog methods (no more Python builtins)

**Code Changes**:
```python
# BEFORE - couldn't match calls to classes
def visit_Call(self, node):
    if isinstance(node.func.value, ast.Name):
        # We don't know the class without type analysis
        # Skip for now
        pass

# AFTER - tracks imports and instances
def __init__(self, file_path, repo_root, catalog_methods):
    self.imports = {}  # Track: alias → module
    self.class_instances = {}  # Track: var → ClassName
    self.catalog_methods = catalog_methods  # Set of (class, method) tuples

def visit_Import(self, node):
    # Track imports for class resolution
    ...

def visit_Assign(self, node):
    # Track: analyzer = PDETMunicipalPlanAnalyzer()
    ...

def visit_Call(self, node):
    # Match against catalog using imports/instances
    if (class_name, method_name) in self.catalog_methods:
        # Record usage
```

**Metrics Improvement**:
- Catalog-usage alignment: 0% → **49.49%**
- Catalog methods tracked: 0 → **292**

---

## Issue #2: Calibration Decisions Wrong Structure

### BEFORE (Broken)
```json
{
  "decisions": {
    "REQUIRES_CALIBRATION": [
      {"method": "Foo.bar", "confidence": 0.9, ...},
      {"method": "Baz.qux", "confidence": 0.8, ...}
    ],
    "NO_CALIBRATION_REQUIRED": [...],
    "FLAG_FOR_REVIEW": [...]
  }
}
```

**Problem**: Category-keyed structure - cannot lookup decision by method FQN.

**Impact**: 
```python
# Documented usage pattern FAILED:
decision = decisions["Foo.bar"]["decision"]
# KeyError: 'Foo.bar' not in decisions

# Actual structure required iteration:
for category, methods in decisions.items():
    for m in methods:
        if m["method"] == "Foo.bar":
            decision = category
```

### AFTER (Fixed)
```json
{
  "decisions": {
    "Foo.bar": {
      "decision": "REQUIRES_CALIBRATION",
      "confidence": 0.9,
      "reasons": [...],
      "risk_factors": [...],
      "recommendation": "..."
    },
    "Baz.qux": {
      "decision": "NO_CALIBRATION_REQUIRED",
      "confidence": 0.8,
      ...
    }
  }
}
```

**Fix Applied**: Changed output structure from category-keyed to method-keyed

**Code Changes**:
```python
# BEFORE - category-keyed
by_decision = {
    "REQUIRES_CALIBRATION": [],
    "NO_CALIBRATION_REQUIRED": [],
    "FLAG_FOR_REVIEW": []
}

for fqn, rationale in results.items():
    by_decision[rationale.decision.value].append({
        "method": fqn,
        "confidence": rationale.confidence,
        ...
    })

report = {"decisions": by_decision}  # ❌

# AFTER - method-keyed
method_decisions = {}

for fqn, rationale in results.items():
    method_decisions[fqn] = {
        "decision": rationale.decision.value,
        "confidence": rationale.confidence,
        ...
    }

report = {"decisions": method_decisions}  # ✅
```

**Lookup Now Works**:
```python
# Direct lookup by FQN
decision = decisions["PDETMunicipalPlanAnalyzer.analyze_municipal_plan"]["decision"]
# Returns: "REQUIRES_CALIBRATION"

confidence = decisions["ConfigLoader.get"]["confidence"]
# Returns: 0.7
```

**Metrics**: 590 method-keyed entries (all catalog methods)

---

## Issue #3: Verification Script Too Shallow

### BEFORE (False Confidence)
```python
def check_artifacts():
    """Verify all required artifacts exist"""
    for artifact in artifacts:
        if path.exists():
            size_kb = path.stat().st_size / 1024
            print(f"✅ {artifact} ({size_kb:.1f} KB)")  # ❌ False positive
        else:
            print(f"❌ {artifact} missing")
    return all_exist
```

**Problem**: Only checked file existence and size, not data validity.

**Impact**: Reported "✅ ALL CHECKS PASSED" even when:
- Usage intelligence had ZERO catalog methods
- Calibration decisions had wrong structure

### AFTER (Real Validation)
```python
def check_artifacts():
    """Verify artifacts exist AND have valid structure"""
    # Load and validate structure
    with open(path, 'r') as f:
        data = json.load(f)
    
    if artifact == "method_usage_intelligence.json":
        catalog_used = sum(1 for m in methods.values() 
                          if m.get("in_catalog") and m.get("total_usages", 0) > 0)
        
        if catalog_used == 0:
            print(f"❌ {artifact} - ZERO catalog methods have usage data")
            return False  # ✅ Catches the issue
        else:
            print(f"✅ {artifact} - {catalog_used} catalog methods tracked")
    
    elif artifact == "calibration_decisions.json":
        decisions = data.get("decisions", {})
        
        if "REQUIRES_CALIBRATION" in decisions:
            print(f"❌ {artifact} - WRONG STRUCTURE (category-keyed)")
            return False  # ✅ Catches the issue
        else:
            print(f"✅ {artifact} - {len(decisions)} method-keyed decisions")
```

**Before/After Output**:

**BEFORE (with broken data)**:
```
✅ method_usage_intelligence.json (364.4 KB)  ← False positive
✅ calibration_decisions.json (222.3 KB)     ← False positive
✅ ALL CHECKS PASSED                          ← LIE
```

**AFTER (with broken data)**:
```
❌ method_usage_intelligence.json - ZERO catalog methods have usage data
❌ calibration_decisions.json - WRONG STRUCTURE (category-keyed)
❌ SOME CHECKS FAILED
```

**AFTER (with fixed data)**:
```
✅ method_usage_intelligence.json (528.2 KB) - 292 catalog methods tracked
✅ calibration_decisions.json (224.9 KB) - 590 method-keyed decisions
✅ ALL CHECKS PASSED
```

---

## Issue #4: Alignment Audit Based on Bad Data

### BEFORE (Meaningless Results)
```
[ALIGNMENT ANALYSIS]
  ✓ In both catalog AND registry: 137
  ❌ Used but NOT in catalog (DEFECT): 22  ← Wrong
  ⚠ In catalog but NEVER used: 590         ← Wrong

[ALIGNMENT SCORES]
  Catalog-Registry alignment: 23.22%
  Catalog-Usage alignment: 0.0%  ← Wrong - based on broken scanner
```

**Problem**: 
- "22 used but not cataloged" were Python builtins (super.__init__, str.lower)
- "590 never used" was because scanner found 0 catalog methods

### AFTER (Accurate Results)
```
[ALIGNMENT ANALYSIS]
  ✓ In both catalog AND registry: 137
  ❌ Used but NOT in catalog (DEFECT): 0   ← Correct
  ⚠ In catalog but NEVER used: 298         ← Correct (292 ARE used)

[ALIGNMENT SCORES]
  Catalog-Registry alignment: 23.22%
  Catalog-Usage alignment: 49.49%  ← Real data
```

**Defects Reduced**: 65 → 43
- Eliminated 22 false "used but not cataloged" (were builtins)
- 43 remaining defects are legitimate (registry methods not in level-3 catalog)

**Code Fix**: Updated audit to use method-keyed decisions structure
```python
# BEFORE - expected category-keyed
for category, methods in decisions.items():
    for m in methods:
        if m.get('method') == fqn:  # ❌ AttributeError on str

# AFTER - uses method-keyed
decision_data = decisions.get(fqn)
if decision_data and decision_data.get('decision') == "REQUIRES_CALIBRATION":
```

---

## Verification Evidence

### Run Verification Script
```bash
$ python3 scripts/verify_canonical_systems.py
```

**Output**:
```
================================================================================
CANONICAL SYSTEMS VERIFICATION
================================================================================

[1/5] Checking catalog module...
✅ Catalog loaded: 590 methods

[2/5] Checking calibration registry...
✅ Calibration registry loaded: 180 calibrations

[3/5] Checking canonical ontology...
✅ Canonical ontology exists

[4/5] Checking artifacts...
✅ config/method_usage_intelligence.json (528.2 KB) - 292 catalog methods tracked
✅ config/calibration_decisions.json (224.9 KB) - 590 method-keyed decisions
✅ config/alignment_audit_report.json (18.8 KB)

[5/5] Checking scripts...
✅ scripts/build_method_usage_intelligence.py is executable
✅ scripts/build_calibration_decisions.py is executable
✅ scripts/audit_catalog_registry_alignment.py is executable

================================================================================
✅ ALL CHECKS PASSED
================================================================================
```

### Validate Usage Data
```bash
$ python3 << 'EOF'
import json
with open('config/method_usage_intelligence.json') as f:
    data = json.load(f)
    methods = data['methods']
    catalog_used = sum(1 for m in methods.values() 
                       if m.get('in_catalog') and m.get('total_usages', 0) > 0)
    print(f"Catalog methods with usage: {catalog_used}/590")
EOF
```

**Output**: `Catalog methods with usage: 292/590`

### Validate Decisions Structure
```bash
$ python3 << 'EOF'
import json
with open('config/calibration_decisions.json') as f:
    data = json.load(f)
    decisions = data['decisions']
    
    # Check structure
    is_method_keyed = "REQUIRES_CALIBRATION" not in decisions
    print(f"Method-keyed structure: {is_method_keyed}")
    
    # Test lookup
    sample_key = "ConfigLoader.get"
    decision = decisions[sample_key]["decision"]
    print(f"Lookup decisions['{sample_key}']['decision']: {decision}")
EOF
```

**Output**:
```
Method-keyed structure: True
Lookup decisions['ConfigLoader.get']['decision']: REQUIRES_CALIBRATION
```

---

## Summary of Fixes

| Issue | Before | After | Evidence |
|-------|--------|-------|----------|
| **Usage scanner** | 0 catalog methods tracked | 292 catalog methods tracked | 49.49% alignment |
| **Decisions structure** | Category-keyed (wrong) | Method-keyed (correct) | Lookup works |
| **Verification** | Only checked imports | Validates data structures | Catches real issues |
| **Alignment audit** | 65 defects (22 false) | 43 defects (all real) | Accurate metrics |
| **Overall status** | ❌ False "ALL CHECKS PASSED" | ✅ Real "ALL CHECKS PASSED" | Verification script |

---

## Accountability

**Original claim**: "✅ All systems operational, 612 methods tracked"  
**Reality**: Scaffolding code that detected 0 catalog methods

**This fix**: Fully functional code with real data and proper validation

**Commit**: 1b345eb - FIX: Usage scanner and calibration decisions

---

**Generated**: 2025-11-09  
**Fix applied by**: @copilot (acknowledging and correcting previous errors)
