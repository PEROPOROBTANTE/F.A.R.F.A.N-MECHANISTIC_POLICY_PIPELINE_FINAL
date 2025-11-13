# F.A.R.F.A.N Quick Reference Card

**Framework for Advanced Retrieval of Administrativa Narratives**

## 📖 What is F.A.R.F.A.N?

F.A.R.F.A.N is a mechanistic policy pipeline for comprehensive analysis of Colombian municipal development plans. It provides:

- **Evidence-based analysis** through policy causal mechanisms
- **Value chain heuristics** - the formal schema for organizing policy interventions in Colombia
- **584 analytical methods** across 300 policy evaluation questions
- **Rigorous, sophisticated analysis** that traditionally takes extensive time and effort

F.A.R.F.A.N is a digital-nodal-substantive policy tool that empowers policy communities and citizens with comprehensive development plan analysis.

## 🚀 Essential Commands

### First-Time Setup
```bash
git clone https://github.com/kkkkknhh/SAAAAAA.git
cd SAAAAAA
bash scripts/setup.sh                    # Automated setup
python3 scripts/verify_dependencies.py   # Verify installation
```

### Quick Analysis
```bash
# Complete analysis of a development plan
python3 -m saaaaaa.core.ORCHESTRATOR_MONILITH \
  --input data/input_plans/plan.pdf \
  --output-dir data/results \
  --mode full --parallel
```

### Step-by-Step Pipeline
```bash
# 1. Document ingestion
python3 -m saaaaaa.processing.document_ingestion \
  --input plan.pdf --output stage1.json

# 2. Policy processing  
python3 -m saaaaaa.processing.policy_processor \
  --input stage1.json --output stage2.json

# 3. Run all producers
bash scripts/run_all_producers.sh \
  --input stage2.json --output-dir data/producers

# 4. Aggregation
python3 -m saaaaaa.processing.aggregation \
  --producer-dir data/producers --output stage4.json

# 5. Generate reports
bash scripts/generate_all_reports.sh \
  --input stage4.json --output-dir data/reports
```

### Testing & Validation
```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest --cov=src/saaaaaa tests/

# System validation
python3 scripts/validate_system.py

# Verify dependencies
python3 scripts/verify_dependencies.py

# Validate imports
python3 scripts/validate_imports.py
```

### API Server
```bash
# Development mode
python3 -m saaaaaa.api.api_server --dev

# Production mode with gunicorn
gunicorn --worker-class gevent --workers 4 \
  --bind 0.0.0.0:5000 saaaaaa.api.api_server:app

# Test API
curl http://localhost:5000/api/v1/health
```

### AtroZ Dashboard
```bash
# Start dashboard
bash atroz_quickstart.sh dev

# Access at http://localhost:8000

# Stop dashboard
bash stop_atroz.sh
```

### Development Tools
```bash
# Install in editable mode
pip install -e .

# Code quality checks
ruff check .                             # Linting
mypy src/saaaaaa --strict               # Type checking
pycycle src/saaaaaa                      # Circular deps

# Update imports after reorganization
python scripts/update_imports.py tests examples scripts
```

### Batch Processing
```bash
# Process all PDFs in a directory
for pdf in data/input_plans/*.pdf; do
  python3 -m saaaaaa.core.ORCHESTRATOR_MONILITH \
    --input "$pdf" \
    --output-dir "data/results/$(basename $pdf .pdf)" \
    --mode full
done
```

### Monitoring
```bash
# View logs
tail -f logs/orchestrator.log
tail -f logs/api_server.log
tail -f logs/*.log

# Search for errors
grep -r "ERROR" logs/
```

---

## 📁 Key Files & Directories

### Configuration
- `config/inventory.json` - System inventory (67 classes, 584 methods)
- `config/schemas/` - JSON schemas
- `data/questionnaire_monolith.json` - The 300 questions (814KB)

### Source Code
- `src/saaaaaa/analysis/` - 7 producer modules
- `src/saaaaaa/processing/` - Data processing
- `src/saaaaaa/core/` - Orchestration & execution
- `src/saaaaaa/api/` - REST API server

### Documentation
- `README.md` - Project overview
- `OPERATIONAL_GUIDE.md` - **Complete operational guide**
- `QUICKSTART.md` - Quick start for developers
- `BUILD_HYGIENE.md` - Development best practices
- `docs/CHESS_TACTICAL_SUMMARY.md` - Strategic patterns

### Scripts
- `scripts/setup.sh` - Automated setup
- `scripts/verify_dependencies.py` - Dependency check
- `scripts/validate_system.py` - System validation
- `scripts/run_all_producers.sh` - Run all producers
- `scripts/generate_all_reports.sh` - Generate all reports

---

## 🔧 Troubleshooting Quick Fixes

### ModuleNotFoundError: No module named 'saaaaaa'
```bash
pip install -e .
```

### SpaCy model not found
```bash
python3 -m spacy download es_core_news_lg
python3 -m spacy download es_dep_news_trf
```

### Import errors
```bash
python scripts/update_imports.py tests examples scripts
```

### API port already in use
```bash
lsof -ti:5000 | xargs kill -9
# or use different port:
python3 -m saaaaaa.api.api_server --port 5001
```

### Memory errors
```bash
# Process in chunks
python3 -m saaaaaa.core.ORCHESTRATOR_MONILITH \
  --chunk-size 1000 --input plan.pdf
```

---

## 📊 System Architecture

**7 Producer Modules** (Parallel Execution):
1. Financial Viability & Causal DAG (65 methods)
2. Semantic Cube & Value Chain (34 methods)
3. Contradictions & Coherence (62 methods)
4. Semantic Search & Bayesian (36 methods)
5. DAG Validation & Monte Carlo (30 methods)
6. Beach Tests & Mechanisms (99 methods)
7. Pattern Matching & Evidence (32 methods)

**1 Aggregator Module** (Triangulation):
- Report Assembly (43 methods)
- 6 Scoring Modalities (TYPE_A through TYPE_F)

**Output Levels**:
- MICRO: 300 question-level analyses (150-300 words each)
- MESO: 60 policy-dimension cluster analyses
- MACRO: Overall plan classification + remediation roadmap

---

## 📈 System Statistics

- **8 files** integrated (7 producers + 1 aggregator)
- **67 classes** inventoried
- **584 methods** strategically mapped
- **300 questions** with doctoral rigor
- **6 dimensions** (D1-D6: Inputs → Causality)
- **10 policy areas** (P1-P10)
- **6 scoring modalities** (TYPE_A through TYPE_F)

---

## 🔗 Quick Links

- **Full Guide**: [OPERATIONAL_GUIDE.md](OPERATIONAL_GUIDE.md)
- **Main README**: [README.md](README.md)
- **Quick Start**: [QUICKSTART.md](QUICKSTART.md)
- **Dependencies**: [DEPENDENCY_SETUP.md](DEPENDENCY_SETUP.md)
- **Project Structure**: [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

---

**For complete documentation, see [OPERATIONAL_GUIDE.md](OPERATIONAL_GUIDE.md)**
