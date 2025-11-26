# Run Complete Analysis - Plan_1.pdf

## Overview

The `run_complete_analysis_plan1.py` script demonstrates the complete end-to-end SIN_CARRETA system execution:

1. **CPP Ingestion**: Preprocesses Plan_1.pdf using the Canon Policy Package (CPP) pipeline
2. **CPP Adaptation**: Converts CPP format to PreprocessedDocument for orchestrator consumption
3. **Orchestrator Execution**: Runs all 11 phases of the analysis pipeline
4. **Results Display**: Shows comprehensive results from each phase

## Prerequisites

### Required Dependencies

The script requires the following Python packages to be installed:

```bash
# Core PDF processing
pip install pdfplumber==0.10.3 PyPDF2==3.0.1 PyMuPDF==1.23.8

# Data processing
pip install pyarrow pandas numpy

# Scientific computing
pip install scikit-learn scipy

# Graph processing  
pip install networkx

# Logging
pip install structlog

# NLP and ML (WARNING: Large downloads, 2GB+)
pip install spacy nltk torch transformers sentence-transformers

# Download spaCy Spanish models (required)
python -m spacy download es_core_news_lg
python -m spacy download es_dep_news_trf
```

### Quick Install (All at once)

```bash
# Install from requirements.txt (recommended)
pip install -r requirements.txt

# Or install minimal set
pip install pdfplumber==0.10.3 PyPDF2==3.0.1 PyMuPDF==1.23.8 \
    pyarrow pandas numpy scikit-learn scipy networkx structlog

# Then install ML dependencies (large, may take time)
pip install spacy nltk torch transformers sentence-transformers
python -m spacy download es_core_news_lg
python -m spacy download es_dep_news_trf
```

### Input File

The script expects `Plan_1.pdf` to exist at:
```
data/plans/Plan_1.pdf
```

This is a 940KB Development Plan document used for demonstration.

## Usage

### Basic Execution

```bash
python run_complete_analysis_plan1.py
```

### Expected Output

The script produces structured output showing progress through 4 main phases:

```
================================================================================
COMPLETE SYSTEM EXECUTION: CPP + ORCHESTRATOR FOR PLAN_1.PDF
================================================================================

📄 PHASE 1: CPP INGESTION
--------------------------------------------------------------------------------
  Input: Plan_1.pdf
  Location: /home/user/SAAAAAA/data/plans/Plan_1.pdf
  Size: 940.2 KB
  
  🔄 Initializing CPP ingestion pipeline...
  🔄 Processing document (this may take 30-60 seconds)...
  ✅ CPP Status: OK
  ✅ CPP URI: /home/user/SAAAAAA/data/output/cpp_plan_1
  ✅ Schema Version: CPP-2025.1

🔄 PHASE 2: CPP LOADING & ADAPTATION
--------------------------------------------------------------------------------
  🔄 Loading CPP from directory...
  ✅ CPP loaded successfully
  ✅ Schema: CPP-2025.1
  🔄 Converting CPP to PreprocessedDocument...
  ✅ Document ID: Plan_1
  ✅ Sentences: 78
  ✅ Tables: 0
  ✅ Raw text length: 133555 chars
  ✅ Provenance completeness: 0.00%

⚙️  PHASE 3: ORCHESTRATOR INITIALIZATION
--------------------------------------------------------------------------------
  🔄 Initializing Orchestrator...
  ✅ Orchestrator initialized
  ✅ Phases: 11
  ✅ Executors registered: 305

🚀 PHASE 4: ORCHESTRATOR EXECUTION (11 PHASES)
================================================================================

  🔄 Starting 11-phase orchestration...

================================================================================
📊 ORCHESTRATION RESULTS
================================================================================

✅ FASE 0 - Validación de Configuración
   Duration: 150ms
   Mode: sync
   Results: dict

✅ FASE 1 - Ingestión de Documento
   Duration: 2500ms
   Mode: sync
   Results: PreprocessedDocument

✅ FASE 2 - Micro Preguntas
   Duration: 45000ms
   Mode: async
   Results: 305 items

✅ FASE 3 - Scoring Micro
   Duration: 12000ms
   Mode: async
   Results: 305 items

✅ FASE 4 - Agregación Dimensiones
   Duration: 8000ms
   Mode: async
   Results: 60 keys

✅ FASE 5 - Agregación Áreas
   Duration: 5000ms
   Mode: async
   Results: 10 keys

✅ FASE 6 - Agregación Clústeres
   Duration: 3000ms
   Mode: sync
   Results: 4 keys

✅ FASE 7 - Evaluación Macro
   Duration: 4000ms
   Mode: sync
   Results: MacroScore

✅ FASE 8 - Recomendaciones
   Duration: 6000ms
   Mode: async
   Results: list

✅ FASE 9 - Ensamblado de Reporte
   Duration: 2000ms
   Mode: sync
   Results: dict

✅ FASE 10 - Formateo y Exportación
   Duration: 3000ms
   Mode: async
   Results: ExportPayload

================================================================================
📈 SUMMARY
================================================================================
  Phases completed: 11/11
  Total time: 90.7s
  Average per phase: 8247ms

  🎉 ALL PHASES COMPLETED SUCCESSFULLY!
```

## Output Artifacts

The script generates several output files in `data/output/cpp_plan_1/`:

- `content_stream.arrow`: Apache Arrow format file with extracted text and metadata
- `provenance_map.arrow`: Apache Arrow format file tracking text provenance  
- `metadata.json`: JSON file with CPP metadata, quality metrics, and policy manifest

These files are automatically created by the CPP ingestion pipeline and are excluded from version control via `.gitignore`.

## Architecture

### Phase 1: CPP Ingestion (9 sub-phases)

The CPP ingestion pipeline executes 9 deterministic phases:

1. Acquisition & Integrity
2. Format Decomposition  
3. Structural Normalization
4. Text Extraction & Normalization
5. OCR (conditional)
6. Tables & Budget Handling
7. Provenance Binding
8. Advanced Chunking
9. Canonical Packing

### Phase 2: CPP Adaptation

The CPPAdapter converts the Canon Policy Package into the orchestrator's PreprocessedDocument format, preserving:
- Complete provenance information
- Chunk ordering by text span
- Metadata and quality metrics
- Tables and budget data

### Phase 3: Orchestrator Initialization

Initializes the main Orchestrator with:
- 305 micro-question executors
- Policy area aggregators
- Scoring systems
- Recommendation engine

### Phase 4: 11-Phase Orchestration

Executes the complete analysis pipeline:

0. **Configuration Validation** (sync)
1. **Document Ingestion** (sync)
2. **Micro Questions** (async, ~305 questions)
3. **Scoring Micro** (async)
4. **Dimension Aggregation** (async, ~60 dimensions)
5. **Policy Area Aggregation** (async, ~10 areas)
6. **Cluster Aggregation** (sync, 4 clusters)
7. **Macro Evaluation** (sync)
8. **Recommendations** (async, MICRO/MESO/MACRO levels)
9. **Report Assembly** (sync)
10. **Format & Export** (async)

## Troubleshooting

### Common Issues

#### Missing Dependencies

**Error**: `ModuleNotFoundError: No module named 'pdfplumber'`

**Solution**: Install missing package:
```bash
pip install pdfplumber
```

#### CPP Ingestion Fails

**Error**: `CPP Status: ABORT`

**Possible causes**:
- Missing pdfplumber, PyMuPDF, or pyarrow
- Corrupted PDF file
- Insufficient memory

**Solution**: Ensure all dependencies are installed and input file is valid.

#### Orchestrator Initialization Fails

**Error**: `ERROR: Dependencia faltante. Ejecute: pip install spacy`

**Solution**: Install the missing package and required spacy models:
```bash
pip install spacy
python -m spacy download es_core_news_lg
```

#### Out of Memory

**Error**: `MemoryError` or system hangs

**Solution**: The system requires significant memory (8GB+ recommended) due to ML models. Try:
- Close other applications
- Increase swap space
- Use a machine with more RAM

### Debug Mode

To see detailed logging, set the log level:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance Notes

- **CPP Ingestion**: 30-60 seconds for a 1MB PDF
- **Orchestrator Execution**: 60-120 seconds total for all 11 phases
- **Memory Usage**: ~4-8GB peak during ML model loading
- **Disk Usage**: ~200-300MB for output artifacts per document

## System Requirements

- **Python**: 3.10 or higher (3.11/3.12 recommended)
- **RAM**: 8GB minimum, 16GB recommended
- **Disk**: 10GB for dependencies + models
- **OS**: Linux, macOS, or Windows (WSL2 recommended)

## Related Documentation

- `OPERATIONAL_GUIDE.md`: Current operational/install guide (replaces legacy manual)
- `src/saaaaaa/processing/cpp_ingestion/README.md`: CPP ingestion pipeline documentation
- `src/saaaaaa/core/orchestrator/`: Orchestrator implementation
- `ORCHESTRATION_ARCHITECTURE_ANALYSIS.md`: Orchestration architecture details

## Support

For issues or questions:
1. Check `OPERATIONAL_GUIDE.md` for detailed setup instructions
2. Review system logs for specific error messages
3. Ensure all dependencies are properly installed
4. Verify input file exists and is readable
