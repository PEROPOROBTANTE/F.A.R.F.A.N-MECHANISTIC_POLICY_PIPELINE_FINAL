# SPC/CPP Migration Guide

## Overview

This guide explains the terminology migration from **CPP (Canon Policy Package)** to **SPC (Smart Policy Chunks)** and how to use the compatibility layer.

## Quick Summary

- **SPC (Smart Policy Chunks)** is the new preferred terminology
- **CPP (Canon Policy Package)** is the legacy terminology (still supported)
- Both terminologies work interchangeably through aliases
- No breaking changes - existing code continues to work

## What Changed

### New Terminology

| Legacy (CPP) | New (SPC) | Status |
|-------------|----------|---------|
| CPPAdapter | SPCAdapter | Alias (same class) |
| CPPAdapterError | SPCAdapterError | Alias (same exception) |
| CPPDeliverable | SPCDeliverable | Both available |
| PortCPPAdapter | PortSPCAdapter | Both available |
| adapt_cpp_to_orchestrator | adapt_spc_to_orchestrator | Both available |

## Usage Examples

### Using SPC Terminology (Recommended for New Code)

```python
from saaaaaa.utils.spc_adapter import SPCAdapter, adapt_spc_to_orchestrator
from saaaaaa.processing.cpp_ingestion.models import CanonPolicyPackage
from saaaaaa.core.wiring.contracts import SPCDeliverable
from saaaaaa.core.ports import PortSPCAdapter

# Create adapter
adapter = SPCAdapter()

# Convert SPC to PreprocessedDocument
doc = adapter.to_preprocessed_document(spc_package, document_id="mydoc")

# Or use convenience function
doc = adapt_spc_to_orchestrator(spc_package, document_id="mydoc")
```

### Using CPP Terminology (Legacy, Still Supported)

```python
from saaaaaa.utils.cpp_adapter import CPPAdapter, adapt_cpp_to_orchestrator
from saaaaaa.processing.cpp_ingestion.models import CanonPolicyPackage
from saaaaaa.core.wiring.contracts import CPPDeliverable
from saaaaaa.core.ports import PortCPPAdapter

# Create adapter (same implementation as SPCAdapter)
adapter = CPPAdapter()

# Convert CPP to PreprocessedDocument
doc = adapter.to_preprocessed_document(cpp_package, document_id="mydoc")

# Or use convenience function
doc = adapt_cpp_to_orchestrator(cpp_package, document_id="mydoc")
```

## Model Structure

The models are located in `src/saaaaaa/processing/cpp_ingestion/models.py` and work with both terminologies:

```python
from saaaaaa.processing.cpp_ingestion.models import (
    CanonPolicyPackage,      # Main container (works with both SPC and CPP)
    Chunk,                    # Individual chunk with metadata
    ChunkGraph,              # Graph of chunks
    ChunkResolution,         # MICRO, MESO, MACRO enum
    PolicyManifest,          # Policy metadata
    QualityMetrics,          # Quality scores
    IntegrityIndex,          # Hash-based integrity
    BudgetInfo,              # Budget data
    KPIInfo,                 # KPI information
)
```

### Required Fields (Verified)

All these fields are verified to exist and work correctly:

**CanonPolicyPackage:**
- `schema_version: str`
- `chunk_graph: ChunkGraph`
- `policy_manifest: PolicyManifest`
- `quality_metrics: QualityMetrics`
- `integrity_index: IntegrityIndex`
- `provenance_map: ProvenanceMap`
- `metadata: dict[str, Any]`

**Chunk:**
- `id: str`
- `text: str`
- `resolution: ChunkResolution`
- `text_span: TextSpan`
- `bytes_hash: str`
- `policy_facets: PolicyFacet`
- `time_facets: TimeFacet`
- `geo_facets: GeoFacet`
- `confidence: Confidence`
- `budget: Optional[BudgetInfo]`
- `kpi: Optional[KPIInfo]`
- `provenance: Optional[dict[str, Any]]`
- `entities: list[EntityInfo]`

## Testing

Both adapters share the same implementation and tests:

```bash
# Test SPC adapter (new tests)
pytest tests/test_spc_adapter.py

# Test CPP adapter (existing tests)
pytest tests/test_cpp_adapter.py

# Test both together
pytest tests/test_spc_adapter.py tests/test_cpp_adapter.py
```

All 32 tests pass (14 CPP + 18 SPC).

## Migration Strategy

### For New Code

Use SPC terminology:
```python
from saaaaaa.utils.spc_adapter import SPCAdapter
```

### For Existing Code

No changes needed - CPP terminology continues to work:
```python
from saaaaaa.utils.cpp_adapter import CPPAdapter
```

### Gradual Migration

You can migrate gradually:

1. **Phase 1**: Keep using CPPAdapter (no rush)
2. **Phase 2**: Start using SPCAdapter in new modules
3. **Phase 3**: Optionally update old modules when convenient

Both work identically since `SPCAdapter is CPPAdapter` (same class).

## Contracts and Ports

### Wiring Contracts

Both contracts are available in `src/saaaaaa/core/wiring/contracts.py`:

```python
from saaaaaa.core.wiring.contracts import CPPDeliverable, SPCDeliverable

# Both have identical fields:
# - chunk_graph: dict[str, Any]
# - policy_manifest: dict[str, Any]
# - provenance_completeness: float
# - schema_version: str
```

### Port Protocols

Both ports are available in `src/saaaaaa/core/ports.py`:

```python
from saaaaaa.core.ports import PortCPPAdapter, PortSPCAdapter

# Both define the same interface:
# - to_preprocessed(cpp/spc, document_id) -> PreprocessedDocument
```

## Backward Compatibility

The implementation maintains **100% backward compatibility**:

- ✅ Existing imports continue to work
- ✅ No breaking changes to APIs
- ✅ No changes to model structure
- ✅ All existing tests pass
- ✅ SPC and CPP names are interchangeable

## Implementation Details

### Alias Implementation

```python
# In src/saaaaaa/utils/spc_adapter.py
from saaaaaa.utils.cpp_adapter import CPPAdapter, CPPAdapterError

# Simple aliases - no code duplication
SPCAdapter = CPPAdapter
SPCAdapterError = CPPAdapterError
```

This means:
- Same implementation
- Same memory footprint
- Same performance
- Same behavior
- Just different names for the same class

### Why This Approach?

1. **Zero overhead**: Aliases have no runtime cost
2. **Single source of truth**: One implementation, multiple names
3. **Easy maintenance**: Update one file, both names work
4. **Safe migration**: Can't break existing code
5. **Gradual adoption**: Teams can migrate at their own pace

## Related Documentation

- [SPC Implementation Complete](./SPC_IMPLEMENTATION_COMPLETE.md) - Full implementation history
- [SPC Ingestion Audit](./SPC_INGESTION_AUDIT.md) - Method overlap analysis
- [Canonical Flux](./CANONICAL_FLUX.md) - Pipeline architecture

## Support

For questions or issues:
1. Check test files: `tests/test_spc_adapter.py` and `tests/test_cpp_adapter.py`
2. Review source code: `src/saaaaaa/utils/spc_adapter.py`
3. Consult model definitions: `src/saaaaaa/processing/cpp_ingestion/models.py`

---

**Last Updated**: 2025-11-10  
**Status**: Production Ready ✅  
**Compatibility**: 100% Backward Compatible
