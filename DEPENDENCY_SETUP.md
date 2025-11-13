# Dependency Setup Guide

This document describes the complete setup process for SAAAAAA dependencies, including external models and specialized libraries.

## Installation Steps

### 1. Install Python Dependencies

First, install all Python packages from requirements.txt:

```bash
pip install -r requirements.txt
```

### 2. SpaCy Language Models

The system requires Spanish language models for NLP analysis, particularly for the Derek Beach CDAF framework and Financial Producer components.

#### Required SpaCy Models

Install the large Spanish model:
```bash
python -m spacy download es_core_news_lg
```

For enhanced transformer-based analysis (recommended):
```bash
python -m spacy download es_dep_news_trf
```

These models are required for:
- **CDAFFramework** (Derek Beach analysis)
- **PDETMunicipalPlanAnalyzer** (Financial analysis)
- Text analysis and semantic processing

### 3. Verify Installation

After installing dependencies, use the automated verification script:

```bash
python scripts/verify_dependencies.py
```

This script will:
- ✓ Verify all 22 classes have correct `saaaaaa.` prefix
- ✓ Check all core dependencies are installed
- ✓ Validate PDF processing libraries
- ✓ Confirm NLP dependencies
- ✓ Check SpaCy models
- ✓ Attempt to load the class registry

Alternatively, manually verify the class registry can load all modules:

```bash
python -c "
import sys
sys.path.insert(0, 'src')
from saaaaaa.core.orchestrator.class_registry import build_class_registry

try:
    registry = build_class_registry()
    print(f'✓ Successfully loaded {len(registry)} classes')
    for name in sorted(registry.keys()):
        print(f'  - {name}')
except Exception as e:
    print(f'✗ Error: {e}')
"
```

## Dependency Categories

### Core Import Architecture

All module imports now use absolute paths with the `saaaaaa.` prefix:

- **Analysis modules**: `saaaaaa.analysis.*`
  - Derek Beach CDAF (5 classes)
  - Contradiction Detection (3 classes)
  - Semantic Analyzer (4 classes)
  - Theory of Change (2 classes)
  - Financial Analysis (1 class)

- **Processing modules**: `saaaaaa.processing.*`
  - Policy Processor (3 classes)
  - Embedding Policy (3 classes)

### External Dependencies by Component

#### PDF Processing
- `PyMuPDF` (fitz) - Required for PDF document processing
- `tabula-py` - Table extraction from PDFs (Financial Producer)
- `camelot-py` - Complex table extraction
- `pdfplumber` - Alternative PDF processing

#### NLP and Text Processing
- `spacy` - Core NLP framework
- `es_core_news_lg` - Spanish language model (large)
- `es_dep_news_trf` - Spanish transformer model (optional but recommended)
- `sentencepiece` - Tokenization for transformer models (PolicyContradictionDetector)
- `tiktoken` - OpenAI tokenizer
- `transformers` - Hugging Face transformers
- `sentence-transformers` - Semantic embeddings

#### Text Matching and Validation
- `fuzzywuzzy` - Fuzzy string matching
- `python-Levenshtein` - String similarity metrics

#### Machine Learning
- `tensorflow` - Deep learning framework
- `torch` - PyTorch framework
- `scikit-learn` - Traditional ML algorithms

#### Bayesian Analysis
- `pymc` - Bayesian modeling
- `arviz` - Bayesian visualization

#### Causal Inference
- `dowhy` - Causal inference framework
- `econml` - Econometric ML

#### Graph Analysis
- `networkx` - Network/graph analysis
- `igraph` - Efficient graph algorithms
- `python-louvain` - Community detection

## Troubleshooting

### Import Errors

If you encounter import errors, verify:

1. The package is installed in development mode:
   ```bash
   pip install -e .
   ```

2. The `src/` directory is in your Python path:
   ```bash
   export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
   ```

### Missing SpaCy Models

If you see errors about missing Spanish models:
```bash
python -m spacy download es_core_news_lg
python -m spacy download es_dep_news_trf
```

### Dependency Conflicts

If you encounter version conflicts, consider creating a fresh virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Development Notes

### Class Registry Architecture

The `class_registry.py` file maps orchestrator-facing class names to their absolute import paths. All 22 analytical classes are registered with the following structure:

```python
{
    "ClassName": "saaaaaa.module.submodule.ClassName"
}
```

This ensures that:
- Classes can find each other within the project
- Import paths are consistent and explicit
- The orchestrator can dynamically load all analytical components

### Testing Class Loading

To test individual class loading:

```python
from saaaaaa.core.orchestrator.class_registry import get_class_paths
paths = get_class_paths()
print(f"Total classes configured: {len(paths)}")
```

## References

- Problem Statement: See repository issue for complete context
- Import conflicts were resolved by adding `saaaaaa.` prefix to all module paths
- External dependencies were identified during instantiation testing
