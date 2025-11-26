# Architectural Violations Found by Import Linter

**Date**: 2025-11-18
**Tool**: import-linter with fixed configuration

## Status: 5 Contracts BROKEN, 3 Contracts KEPT

---

## ✅ CONTRACTS THAT PASS

1. **Analysis depends on core but not infrastructure** - KEPT
2. **Infrastructure must not pull orchestrator** - KEPT
3. **Utils stay leaf modules** - KEPT

---

## ❌ BROKEN CONTRACTS (5)

### 1. Core Orchestrator → Analysis (CRITICAL)
**Contract**: "Core orchestrator must not import analysis"
**Violation**: `saaaaaa.core.orchestrator.core` → `saaaaaa.analysis.recommendation_engine`
**Location**: `src/saaaaaa/core/orchestrator/core.py:36`

**Impact**: Core layer importing from analysis layer violates architectural boundaries

---

### 2. Core → Analysis (via Orchestrator)
**Contract**: "Core (excluding orchestrator) must not import analysis"
**Violations**:
- `saaaaaa.core.calibration.engine` → `saaaaaa.core.orchestrator.factory` (l.85)
  → `saaaaaa.core.orchestrator.core` (l.46)
  → `saaaaaa.analysis.recommendation_engine` (l.36)

- `saaaaaa.core.wiring.bootstrap` → `saaaaaa.core.orchestrator.factory` (l.25)
  → `saaaaaa.core.orchestrator.core` (l.46)
  → `saaaaaa.analysis.recommendation_engine` (l.36)

**Impact**: Core modules indirectly importing analysis through orchestrator

---

### 3. Core → Processing (via Orchestrator)
**Contract**: "Core (excluding orchestrator) must not import processing"
**Violations**:
- `saaaaaa.core.calibration.engine` → `saaaaaa.core.orchestrator.factory` (l.85)
  → `saaaaaa.core.orchestrator.core` (l.46)
  → `saaaaaa.processing.spc_ingestion` (l.1432)

- `saaaaaa.core.wiring.bootstrap` → `saaaaaa.core.orchestrator.factory` (l.25)
  → `saaaaaa.core.orchestrator.core` (l.46)
  → `saaaaaa.processing.spc_ingestion` (l.1432)

**Impact**: Core modules indirectly importing processing through orchestrator

---

### 4. Processing/Analysis → Orchestrator (via canonical_notation)
**Contract**: "Processing/Analysis cannot import orchestrator"
**Violations**:
- `saaaaaa.processing.aggregation` → `saaaaaa.core.canonical_notation` (l.114)
  → `saaaaaa.core.orchestrator.questionnaire` (l.61)

- `saaaaaa.analysis.recommendation_engine` → `saaaaaa.core.canonical_notation` (l.165)
  → `saaaaaa.core.orchestrator.questionnaire` (l.61)

- `saaaaaa.analysis.report_assembly` → `saaaaaa.core.orchestrator.factory` (l.147)

**Impact**: Analysis and processing layers importing from orchestrator

**Root Cause**: `canonical_notation.py` imports from orchestrator, causing transitive violations

---

### 5. API → Analysis/Processing/Utils
**Contract**: "API layer only calls orchestrator entry points"
**Violations**:
- `saaaaaa.api.api_server` → `saaaaaa.analysis.recommendation_engine` (l.46) - DIRECT import
- `saaaaaa.api.pipeline_connector` → analysis/processing via orchestrator.core
- `saaaaaa.api.pipeline_connector` → `saaaaaa.utils.spc_adapter` via orchestrator.core

**Impact**: API bypassing orchestrator and importing directly from other layers

---

## 📊 SUMMARY

| Layer | Violates | Count |
|-------|----------|-------|
| core.orchestrator | → analysis | 1 |
| core (via orchestrator) | → analysis, processing | 4 |
| processing, analysis | → orchestrator | 3 |
| api | → analysis, processing, utils | 3+ |

**Total Violations**: 11+ import chains breaking architectural contracts

---

## 🔧 RECOMMENDED FIXES

### Priority 1: Fix Core Orchestrator → Analysis
**File**: `src/saaaaaa/core/orchestrator/core.py:36`
**Action**: Remove direct import of `recommendation_engine`
**Options**:
- Move recommendation logic to orchestrator
- Use dependency injection
- Create interface/protocol in core

### Priority 2: Fix Canonical Notation → Orchestrator
**File**: `src/saaaaaa/core/canonical_notation.py:61`
**Action**: Break dependency on `orchestrator.questionnaire`
**Options**:
- Move shared types to `core.types`
- Use TYPE_CHECKING imports
- Refactor to eliminate circular dependency

### Priority 3: Fix API Direct Imports
**File**: `src/saaaaaa/api/api_server.py:46`
**Action**: Remove direct import of `analysis.recommendation_engine`
**Impact**: API should only import from orchestrator entry points

### Priority 4: Review All Transitive Imports
**Action**: Each violation creates a chain that breaks multiple contracts
**Solution**: Fix root causes (#1, #2, #3) to eliminate transitive violations

---

## ⚠️ IMPACT ASSESSMENT

**Current State**: Architectural boundaries are **NOT ENFORCED**

**Risk**:
- Core modules can import from any layer (via orchestrator)
- Analysis/processing can import orchestrator internals
- API bypasses orchestrator pattern
- Circular dependencies possible
- Testing and mocking becomes difficult

**Until Fixed**:
- Cannot enforce clean architecture
- Refactoring is risky
- Module coupling is high
- CI import-linter check will FAIL

---

## 📝 NOTES

- Import linter was broken (wrong contract type "forbid" → "forbidden")
- Fixed in commit: 3375895
- Now properly detecting violations
- Makefile updated to FAIL build on violations (line 53)
- These violations explain why the build was previously failing
