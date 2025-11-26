# F.A.R.F.A.N Quick Start: Run Complete Analysis

**Framework for Advanced Retrieval of Administrativa Narratives**

## TL;DR - Fastest Way to Test

```bash
# 1. Verify CPP ingestion works (no ML dependencies required)
python verify_cpp_ingestion.py

# 2. Install full dependencies (if not already done)
pip install -r requirements.txt

# 3. Run complete analysis  
python run_complete_analysis_plan1.py
```

## What These Scripts Do

### `verify_cpp_ingestion.py` ✓ Lightweight Test

Tests **only** the CPP ingestion pipeline:
- ✅ No ML dependencies (torch, transformers, etc.)
- ✅ Fast execution (~30 seconds)
- ✅ Verifies PDF parsing and structure extraction
- ✅ Validates output artifacts

**Use this first** to ensure basic functionality before installing heavy ML dependencies.

### `run_complete_analysis_plan1.py` ⚡ Full System

Runs the **complete** SIN_CARRETA pipeline:
- 📄 CPP Ingestion (9 phases)
- 🔄 CPP Adaptation
- ⚙️ Orchestrator Initialization
- 🚀 11-Phase Analysis Pipeline
- 📊 Results Display

**Requires** all dependencies including ML models (~2GB download).

## Step-by-Step Setup

### 1. Check Prerequisites

```bash
# Verify Python version (3.10+ required)
python3 --version

# Check if Plan_1.pdf exists
ls -lh data/plans/Plan_1.pdf
```

### 2. Install Minimal Dependencies (for verification only)

```bash
pip install pdfplumber==0.10.3 PyPDF2==3.0.1 PyMuPDF==1.23.8 pyarrow
```

### 3. Run Verification

```bash
python verify_cpp_ingestion.py
```

Expected output:
```
================================================================================
✅ CPP INGESTION SUCCESSFUL
================================================================================

  Status: OK
  CPP URI: /home/user/SAAAAAA/data/output/cpp_verify_test
  Schema Version: CPP-2025.1

  Generated files:
    - content_stream.arrow (138,658 bytes)
    - metadata.json (372 bytes)
    - provenance_map.arrow (5,338 bytes)

  Quality Metrics:
    Boundary F1: 0.950
    KPI Linkage Rate: 0.920
    Budget Consistency: 1.000
    Provenance Completeness: 1.000

✅ All checks passed!
```

### 4. Install Full Dependencies (for complete analysis)

```bash
# Core dependencies
pip install numpy pandas scikit-learn scipy networkx structlog

# ML dependencies (large downloads)
pip install spacy nltk torch transformers sentence-transformers

# Download Spanish models
python -m spacy download es_core_news_lg
python -m spacy download es_dep_news_trf
```

Or install everything at once:
```bash
pip install -r requirements.txt
```

### 5. Run Complete Analysis

```bash
python run_complete_analysis_plan1.py
```

## Troubleshooting

### "Plan_1.pdf not found"

**Solution**: Ensure the file exists at `data/plans/Plan_1.pdf`

### "No module named 'pdfplumber'"

**Solution**: Install missing dependency:
```bash
pip install pdfplumber
```

### "CPP Status: ABORT"

**Solution**: Check that pyarrow is installed:
```bash
pip install pyarrow
```

### "Dependencia faltante" errors

**Solution**: Install the missing package mentioned in the error message:
```bash
pip install <package_name>
```

## What Gets Generated

Both scripts create output in `data/output/`:

```
data/output/
├── cpp_verify_test/          # From verify_cpp_ingestion.py
│   ├── content_stream.arrow
│   ├── metadata.json
│   └── provenance_map.arrow
└── cpp_plan_1/               # From run_complete_analysis_plan1.py
    ├── content_stream.arrow
    ├── metadata.json
    └── provenance_map.arrow
```

These files are excluded from git via `.gitignore`.

## Performance Expectations

| Script | Dependencies | Time | Memory |
|--------|-------------|------|--------|
| verify_cpp_ingestion.py | Minimal | ~30s | ~500MB |
| run_complete_analysis_plan1.py | Full | ~90s | ~4-8GB |

## Next Steps

After successful execution:

1. **Review the output**: Check generated files in `data/output/`
2. **Examine the code**: Study the script structure for integration patterns
3. **Adapt for your needs**: Modify scripts for different input files
4. **Read documentation**: See `RUN_COMPLETE_ANALYSIS_README.md` for details

## Related Files

- `run_complete_analysis_plan1.py` - Main complete analysis script
- `verify_cpp_ingestion.py` - Lightweight verification script
- `RUN_COMPLETE_ANALYSIS_README.md` - Comprehensive documentation
- `OPERATIONAL_GUIDE.md` - Current operational/install guide (replaces legacy manual)
- `requirements.txt` - All Python dependencies

## Support

For issues:
1. Run `verify_cpp_ingestion.py` first to isolate problems
2. Check error messages for missing dependencies
3. Review `RUN_COMPLETE_ANALYSIS_README.md` for detailed troubleshooting
4. Ensure you have sufficient memory (8GB+ recommended)
