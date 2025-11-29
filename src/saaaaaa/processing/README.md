# SPC (Smart Policy Chunks) Ingestion - Canonical Phase-One

Canonical phase-one of the policy analysis pipeline: deterministic ingestion and smart chunking of Development Plans (Planes de Desarrollo) with comprehensive analysis.

**Status**: This is the official phase-one entry point for the single deterministic flux from ingestion to reporting.

## Overview

The CPP Ingestion System transforms heterogeneous Development Plans (PDF, DOCX, HTML, XLSX/CSV) into structured Canon Policy Packages with:

- **Multi-resolution chunks** (micro/meso/macro) with policy awareness
- **Complete provenance tracking** with byte-level precision
- **Arrow IPC serialization** for efficient data handling
- **Quality gates** with ABORT-on-failure semantics
- **Deterministic processing** with reproducible outputs

## Architecture

### Pipeline Phases

1. **Acquisition & Integrity** - Binary reading, MIME detection, BLAKE3 hashing
2. **Format Decomposition** - Extract object tree from PDF/DOCX/HTML
3. **Structural Normalization** - Policy-aware segmentation (Ejes, Programas, Proyectos)
4. **Text Extraction & Normalization** - Unicode NFC, stable offsets
5. **OCR** (conditional) - Leptonica preprocessing, Surya-OCR/PaddleOCR
6. **Tables & Budget Handling** - Table extraction, KPI/budget classification
7. **Provenance Binding** - Complete token-to-source mapping
8. **Advanced Chunking** - Multi-resolution with 8 mechanisms
9. **Canonical Packing** - Arrow IPC serialization, Merkle root

### Advanced Chunking Mechanisms

1. **Semantic cohesion with policy conditioning** - Drift detection at PolicyUnit boundaries
2. **Multi-resolution** - Micro (200-400 tokens), Meso (800-1200), Macro (section)
3. **Graph-aware** - Chunk relationships with typed edges
4. **KPI/Budget-anchored** - Structured data chunks with evidence windows
5. **Temporal windows** - Period-based faceting
6. **Territoriality** - Geographic faceting with no mixing
7. **Normative expansion** - Law/article reference linking
8. **Redundancy guard** - Overlap control <δ%

## Usage

### Basic Ingestion

```python
from pathlib import Path
from saaaaaa.processing.cpp_ingestion import CPPIngestionPipeline

# Initialize pipeline
pipeline = CPPIngestionPipeline(
    enable_ocr=True,
    ocr_confidence_threshold=0.85,
    chunk_overlap_threshold=0.15,
)

# Ingest document
outcome = pipeline.ingest(
    input_path=Path("plan_desarrollo.pdf"),
    output_dir=Path("output/cpp"),
)

# Check result
if outcome.status == "OK":
    print(f"CPP created: {outcome.cpp_uri}")
    print(f"Metrics: {outcome.metrics}")
else:
    print(f"ABORT: {outcome.diagnostics}")
```

### Working with Chunks

```python
from saaaaaa.processing.cpp_ingestion import ChunkGraph, ChunkResolution

# Load chunk graph from CPP
chunk_graph = ChunkGraph()

# Query micro chunks
micro_chunks = [
    c for c in chunk_graph.chunks.values()
    if c.resolution == ChunkResolution.MICRO
]

# Query chunks by policy facet
education_chunks = [
    c for c in chunk_graph.chunks.values()
    if c.policy_facets.programa == "Educación"
]

# Traverse relationships
for chunk_id in chunk_graph.chunks:
    neighbors = chunk_graph.get_neighbors(chunk_id, EdgeType.PRECEDES)
    print(f"Chunk {chunk_id} precedes: {neighbors}")
```

### Quality Validation

```python
from saaaaaa.processing.cpp_ingestion import QualityGates

gates = QualityGates()
result = gates.validate(cpp)

if result["passed"]:
    print("All quality gates passed")
else:
    print(f"Failures: {result['failures']}")
```

## Data Models

### Chunk Structure

```python
@dataclass
class Chunk:
    id: str
    bytes_hash: str
    text_span: TextSpan
    resolution: ChunkResolution
    text: str
    
    # Facets
    policy_facets: PolicyFacet  # area, eje, programa, proyecto, ODS
    time_facets: TimeFacet      # from_year, to_year, period, vigencia
    geo_facets: GeoFacet        # level, code, municipio, departamento
    
    # Structured data
    kpi: Optional[KPIData]
    budget: Optional[BudgetData]
    
    # Context
    entities: List[Entity]
    norm_refs: List[NormRef]
    context: ChunkContext
    provenance: Provenance
    confidence: Confidence
```

### ChunkGraph

```python
@dataclass
class ChunkGraph:
    chunks: Dict[str, Chunk]
    edges: List[Tuple[str, str, EdgeType]]
    
    # Edge types:
    # - PRECEDES: Sequential relationship
    # - CONTAINS: Hierarchical relationship
    # - REFERS_TO: Cross-reference
    # - DEFINED_BY: Definition relationship
    # - JUSTIFIES_BUDGET: Budget justification
    # - SATISFIES_INDICATOR: KPI satisfaction
```

### Canon Policy Package

```python
@dataclass
class CanonPolicyPackage:
    schema_version: str
    policy_manifest: PolicyManifest
    chunk_graph: ChunkGraph
    content_stream: pa.Table        # Arrow IPC
    provenance_map: ProvenanceMap   # Arrow IPC
    integrity_index: IntegrityIndex  # Merkle root
    quality_metrics: QualityMetrics
```

## Quality Gates

The system enforces these invariants:

- `provenance_completeness = 1.0` - Every token must have provenance
- `structural_consistency = 1.0` - Structure must be coherent
- `kpi_linkage_rate ≥ 0.80` - KPIs must be linked to programs
- `budget_consistency_score ≥ 0.95` - Budget rows must balance
- `boundary_f1 ≥ 0.85` - Chunk boundaries must be accurate
- `chunk_overlap ≤ 0.15` - Maximum overlap between chunks

**Failure of any gate triggers ABORT.**

## Output Format

The CPP is saved as a directory with:

```
output/cpp/
├── metadata.json          # Schema, manifest, metrics
├── content_stream.arrow   # Text content with offsets
├── provenance_map.arrow   # Token-to-source mapping
├── chunk_graph.json       # Chunks and relationships
└── integrity.json         # Merkle root and hashes
```

### IngestionOutcome

```json
{
  "status": "OK",
  "cpp_uri": "output/cpp",
  "policy_manifest": {
    "axes": 3,
    "programs": 10,
    "years": [2024, 2025, 2026, 2027, 2028],
    "territories": ["Bogotá", "Medellín"]
  },
  "metrics": {
    "boundary_f1": 0.95,
    "kpi_linkage_rate": 0.92,
    "budget_consistency_score": 1.0
  },
  "fingerprints": {
    "pipeline": "CPP-2025.1",
    "tools": {...}
  }
}
```

## Rust Performance Core

Critical operations implemented in Rust:

- BLAKE3 hashing (keyed and unkeyed)
- Unicode NFC/NFD normalization
- Merkle root computation
- Grapheme segmentation

```python
# Import Rust functions (after building with maturin)
from cpp_ingestion import (
    hash_blake3,
    hash_blake3_keyed,
    normalize_unicode_nfc,
    compute_merkle_root,
)
```

## Building Rust Extension

```bash
# Install maturin
pip install maturin

# Build Rust extension
cd cpp_ingestion
maturin develop --release

# Or build wheel
maturin build --release
```

## Testing

```bash
# Run all tests
pytest tests/test_cpp_ingestion.py -v

# Run specific test class
pytest tests/test_cpp_ingestion.py::TestPipeline -v

# Run with coverage
pytest tests/test_cpp_ingestion.py --cov=saaaaaa.processing.cpp_ingestion
```

## Golden Tests

The system includes golden tests to ensure deterministic processing:

```python
# Re-ingestion should produce identical hashes
outcome1 = pipeline.ingest(document, output_dir1)
outcome2 = pipeline.ingest(document, output_dir2)

assert outcome1.fingerprints == outcome2.fingerprints
```

## Dependencies

### Python
- pyarrow >= 14.0
- polars >= 0.20
- pydantic >= 2.0

### Rust (for extension building)
- blake3 = 1.5
- pyo3 = 0.21
- arrow = 52.0
- petgraph = 0.6
- unicode-normalization = 0.1

## Observability

Event logs are emitted in JSONL format:

```json
{"phase": "Acquisition & Integrity", "input_hash": "...", "output_hash": "...", "metrics": {...}}
{"phase": "Format Decomposition", "object_count": 45, "wall_time": 0.234}
{"phase": "Advanced Chunking", "chunks_created": 234, "edges_created": 567}
```

## Security

- **Sandboxed parsers** - Isolated execution
- **WORM storage** - CPP is write-once
- **No PII in logs** - Only hashes and offsets
- **Optional encryption** - Attested key management

## References

- [Development Plans (Planes de Desarrollo)](https://colaboracion.dnp.gov.co/)
- [Arrow IPC Format](https://arrow.apache.org/docs/format/Columnar.html)
- [BLAKE3](https://github.com/BLAKE3-team/BLAKE3)
- [Unicode Normalization](https://unicode.org/reports/tr15/)

## License

Part of SAAAAAA Strategic Policy Analysis System.
