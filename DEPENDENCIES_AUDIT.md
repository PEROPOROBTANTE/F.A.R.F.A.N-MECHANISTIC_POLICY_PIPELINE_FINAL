# DEPENDENCIES AUDIT

**Generated**: 2025-11-06  
**Status**: Comprehensive dependency management system established  
**Python Version**: 3.10-3.12 compatible  

## Overview

This document provides a complete audit of all dependencies in the SAAAAAA project, including their roles, versions, usage patterns, and security considerations.

## Table of Contents

1. [Dependency Classification](#dependency-classification)
2. [Package Inventory](#package-inventory)
3. [Installation Profiles](#installation-profiles)
4. [Verification Procedures](#verification-procedures)
5. [Adding New Dependencies](#adding-new-dependencies)
6. [Known Issues & Risks](#known-issues--risks)
7. [CI/CD Gates](#cicd-gates)

---

## Dependency Classification

Dependencies are classified into four categories:

### 1. Core Runtime (`core_runtime`)
Critical packages required for production execution. These packages MUST be available for the system to function.

### 2. Optional Runtime (`optional_runtime`)
Packages that enhance functionality but are not critical for core operation.

### 3. Development/Testing (`dev_test`)
Packages required for development, testing, and code quality assurance.

### 4. Documentation (`docs`)
Packages required for building documentation.

---

## Package Inventory

### Core Runtime Dependencies

| Package | Version | Role | Used In | Justification | Risks |
|---------|---------|------|---------|---------------|-------|
| **numpy** | 2.2.1 | Data processing | Core analysis modules | Fundamental numerical computing | None - stable API |
| **pandas** | 2.2.3 | Data processing | Data ingestion, analysis | Tabular data manipulation | Breaking changes in major versions |
| **polars** | 1.19.0 | Data processing | High-performance analytics | Fast DataFrame operations | API evolving, pin exact version |
| **pyarrow** | 19.0.0 | Data serialization | Polars backend, data I/O | Efficient columnar format | Must match polars compatibility |
| **scipy** | 1.15.1 | Scientific computing | Statistical analysis | Advanced mathematical functions | Generally stable |
| **scikit-learn** | 1.6.1 | Machine learning | ML models, clustering | Standard ML algorithms | Breaking changes in major versions |
| **transformers** | 4.48.3 | NLP/ML | Text embeddings, models | Hugging Face model hub | Frequent updates, test before upgrade |
| **sentence-transformers** | 3.3.1 | NLP embeddings | Semantic similarity | Sentence/document embeddings | Depends on transformers version |
| **spacy** | 3.8.3 | NLP | Text processing | Industrial-strength NLP | Model compatibility critical |
| **networkx** | 3.4.2 | Graph analysis | Network/graph operations | Graph algorithms | Stable API |
| **pdfplumber** | 0.11.4 | PDF parsing | Document ingestion | Text extraction from PDFs | Active development |
| **PyPDF2** | 3.0.1 | PDF processing | PDF manipulation | PDF reading/writing | Maintenance mode, consider alternatives |
| **PyMuPDF** | 1.25.2 | PDF rendering | Advanced PDF operations | Fast PDF rendering (fitz) | Frequent updates |
| **python-docx** | 1.1.2 | DOCX processing | Document ingestion | Word document parsing | Stable |
| **flask** | 3.0.3 | Web framework | API server | HTTP server | Stable, well-tested |
| **fastapi** | 0.115.6 | Web framework | Modern API | Async API framework | Breaking changes in minor versions |
| **httpx** | 0.28.1 | HTTP client | External API calls | Async HTTP client | Stable |
| **uvicorn** | 0.34.0 | ASGI server | FastAPI runtime | Production server | Stable |
| **sse-starlette** | 2.2.1 | Server-sent events | Real-time updates | SSE support for FastAPI | Niche, low activity |
| **werkzeug** | 3.0.6 | WSGI utilities | Flask dependency | HTTP utilities | Breaking changes in major versions |
| **pydantic** | 2.10.6 | Data validation | Data models, validation | Schema validation | v2 has breaking changes from v1 |
| **pyyaml** | 6.0.2 | YAML parsing | Configuration | Config file parsing | Security fixes important |
| **jsonschema** | 4.23.0 | JSON validation | Schema validation | JSON schema enforcement | Stable |
| **blake3** | 0.4.1 | Hashing | Data integrity | Fast cryptographic hashing | Stable, use exact pin |
| **structlog** | 24.4.0 | Logging | System logging | Structured logging | Stable |
| **tenacity** | 9.0.0 | Retry logic | Error handling | Retry decorators | Stable |
| **typer** | 0.15.1 | CLI framework | Command-line interface | Modern CLI building | Stable |
| **python-dotenv** | 1.0.1 | Environment vars | Configuration | .env file loading | Stable |
| **typing-extensions** | 4.12.2 | Type hints | Type checking | Backported type features | Essential for Python <3.11 |

**Note**: `tensorflow` and `torch` are omitted from core due to:
- **tensorflow**: Requires Python <3.12 or version >=2.16
- **torch**: Platform-specific installation (CUDA vs CPU)
- **pymc**: Complex dependency tree, install separately if needed

### Optional Runtime Dependencies

| Package | Version | Role | Used In | Justification | Risks |
|---------|---------|------|---------|---------------|-------|
| **flask-cors** | 6.0.0 | CORS support | API server | Cross-origin requests | Stable |
| **flask-socketio** | 5.4.1 | WebSocket | Real-time comms | WebSocket support for Flask | Breaking changes possible |
| **python-socketio** | 5.14.1 | WebSocket | Real-time comms | SocketIO protocol | Must match flask-socketio |
| **gevent** | 24.11.1 | Async I/O | WebSocket backend | Green threads | Breaking changes in major versions |
| **gevent-websocket** | 0.10.1 | WebSocket | gevent integration | WebSocket for gevent | Low maintenance |
| **pyjwt** | 2.10.1 | JWT tokens | Authentication | Token generation/validation | Security updates critical |
| **igraph** | 0.11.8 | Graph analysis | Advanced graph ops | Fast graph algorithms | Stable but complex install |
| **python-louvain** | 0.16 | Community detection | Graph clustering | Louvain algorithm | Low maintenance |
| **pydot** | 3.0.4 | Graph visualization | Graph rendering | DOT graph visualization | Requires Graphviz |
| **tabula-py** | 2.10.0 | PDF tables | Table extraction | Extract tables from PDFs | Requires Java |
| **camelot-py** | 0.11.0 | PDF tables | Advanced table parsing | High-quality table extraction | Complex dependencies |
| **nltk** | 3.9.1 | NLP | Text processing | Classical NLP algorithms | Data downloads required |
| **sentencepiece** | 0.2.0 | Tokenization | Model tokenization | Subword tokenization | Stable |
| **tiktoken** | 0.8.0 | Tokenization | OpenAI tokenization | Token counting | OpenAI-specific |
| **fuzzywuzzy** | 0.18.0 | String matching | Fuzzy string matching | Approximate matching | Low maintenance |
| **python-Levenshtein** | 0.26.1 | String distance | String similarity | Fast edit distance | Stable |
| **langdetect** | 1.0.9 | Language detection | Text language ID | Detect text language | Low maintenance |
| **redis** | 5.2.1 | Caching | Cache layer | Redis client | Stable |
| **sqlalchemy** | 2.0.37 | ORM | Database access | Database abstraction | Breaking changes in major versions |
| **gunicorn** | 23.0.0 | WSGI server | Production server | Production WSGI server | Stable |
| **prometheus-client** | 0.21.1 | Metrics | Monitoring | Prometheus metrics | Stable |
| **psutil** | 6.1.1 | System info | Resource monitoring | System utilities | Stable |
| **opentelemetry-api** | 1.29.0 | Observability | Tracing | OpenTelemetry API | Stable |
| **opentelemetry-sdk** | 1.29.0 | Observability | Tracing | OpenTelemetry SDK | Must match API version |
| **opentelemetry-instrumentation-fastapi** | 0.50b0 | Observability | FastAPI tracing | Auto-instrumentation | Beta, pin exact version |
| **beautifulsoup4** | 4.12.3 | HTML parsing | Web scraping | HTML/XML parsing | Stable |

### Development & Testing Dependencies

| Package | Version | Role | Used In | Justification | Risks |
|---------|---------|------|---------|---------------|-------|
| **pytest** | 8.3.4 | Testing | Test suite | Standard test framework | Stable |
| **pytest-cov** | 6.0.0 | Coverage | Test coverage | Code coverage reports | Stable |
| **pytest-asyncio** | 0.25.2 | Async testing | Async tests | Async test support | Stable |
| **hypothesis** | 6.124.3 | Property testing | Property tests | Generative testing | Frequent updates, generally compatible |
| **schemathesis** | 3.38.4 | API testing | API contract tests | OpenAPI testing | Active development |
| **black** | 24.10.0 | Code formatting | Code style | Opinionated formatter | Breaking changes rare |
| **ruff** | 0.9.1 | Linting | Code quality | Fast Python linter | Rapid development, pin version |
| **flake8** | 7.1.1 | Linting | Code quality | Style checker | Stable |
| **mypy** | 1.14.1 | Type checking | Static analysis | Type checker | Breaking changes in minor versions |
| **pyright** | 1.1.395 | Type checking | Static analysis | Microsoft type checker | Frequent updates |
| **bandit** | 1.8.0 | Security | Security scanning | Security linter | Stable |
| **import-linter** | 2.2 | Architecture | Layer validation | Import contract enforcement | Stable |

### Documentation Dependencies

| Package | Version | Role | Used In | Justification | Risks |
|---------|---------|------|---------|---------------|-------|
| **sphinx** | 8.1.3 | Documentation | Doc generation | Documentation generator | Stable |
| **sphinx-rtd-theme** | 3.0.2 | Documentation | Theme | ReadTheDocs theme | Stable |
| **myst-parser** | 4.0.0 | Documentation | Markdown support | Markdown parser for Sphinx | Stable |

---

## Installation Profiles

### Profile 1: Core Runtime Only
For production deployments with minimal dependencies.

```bash
pip install -r requirements-core.txt
```

**Use case**: Production servers, minimal Docker images

### Profile 2: Core + Optional
For full-featured deployments.

```bash
pip install -r requirements-core.txt -r requirements-optional.txt
```

**Use case**: Production with all features enabled

### Profile 3: Development
For development work with testing and code quality tools.

```bash
pip install -r requirements-dev.txt
# Includes requirements-core.txt automatically
```

**Use case**: Local development, CI/CD pipelines

### Profile 4: All Dependencies
Complete installation including documentation tools.

```bash
pip install -r requirements-all.txt
```

**Use case**: Complete development environment

### Profile 5: Constrained Installation
Use constraints file to prevent dependency conflicts.

```bash
pip install -c constraints-new.txt -r requirements-core.txt
```

**Use case**: Reproducible builds, debugging version conflicts

---

## Verification Procedures

### 1. Verify Importability

Check that all critical packages can be imported:

```bash
python3 scripts/verify_importability.py
```

**Expected output**: All critical packages should import successfully with versions displayed.

### 2. Audit Dependencies

Scan codebase for all imports and detect missing packages:

```bash
python3 scripts/audit_dependencies.py
```

**Expected output**: JSON report with classification and missing package list.

### 3. Compare Freeze with Lock

Verify that installed packages match expected versions:

```bash
# Generate current freeze
pip freeze > freeze-current.txt

# Compare with expected
diff freeze-current.txt constraints-new.txt
```

**Expected output**: No differences for pinned packages.

### 4. Check for Security Vulnerabilities

```bash
pip install pip-audit  # If not already installed
pip-audit
```

**Expected output**: No known vulnerabilities.

---

## Adding New Dependencies

**CRITICAL**: Follow this procedure EXACTLY when adding new dependencies.

### Checklist for New Dependency

- [ ] 1. **Justification**: Document why the dependency is needed
- [ ] 2. **Alternatives**: Consider if functionality can be implemented internally
- [ ] 3. **Classification**: Determine role (core/optional/dev/docs)
- [ ] 4. **Version Research**: Find minimum compatible version
- [ ] 5. **Security Check**: Run `pip-audit` or check GitHub Security Advisory Database
- [ ] 6. **License Check**: Verify license compatibility (prefer permissive licenses)
- [ ] 7. **Maintenance Check**: Verify package is actively maintained
- [ ] 8. **Size Check**: Check package size and transitive dependencies
- [ ] 9. **Python Compatibility**: Verify support for Python 3.10-3.12
- [ ] 10. **Test Installation**: Install in clean venv and test
- [ ] 11. **Update Scripts**: Add to `generate_dependency_files.py`
- [ ] 12. **Regenerate Files**: Run `python3 scripts/generate_dependency_files.py`
- [ ] 13. **Test Importability**: Run `python3 scripts/verify_importability.py`
- [ ] 14. **Update Documentation**: Add entry to this document
- [ ] 15. **Commit**: Create commit with clear message

### Example Workflow

```bash
# 1. Research package
pip show <package-name>
pip search <package-name>

# 2. Check security
gh api /advisories --jq '.[] | select(.cve.package.name=="<package-name>")'

# 3. Test in isolation
python3 -m venv test-env
source test-env/bin/activate
pip install <package-name>==<version>
python3 -c "import <package-name>; print(<package-name>.__version__)"
deactivate
rm -rf test-env

# 4. Add to generator script
# Edit scripts/generate_dependency_files.py
# Add package to appropriate dictionary (CORE_DEPENDENCIES, etc.)

# 5. Regenerate files
python3 scripts/generate_dependency_files.py

# 6. Verify
python3 scripts/verify_importability.py

# 7. Update this document
# Add row to appropriate table above

# 8. Test
pip install -r requirements-core.txt  # or appropriate file
pytest tests/

# 9. Commit
git add requirements-*.txt constraints-new.txt scripts/generate_dependency_files.py DEPENDENCIES_AUDIT.md
git commit -m "deps: Add <package-name> <version> for <purpose>"
```

---

## Known Issues & Risks

### 1. TensorFlow Compatibility

**Issue**: TensorFlow 2.15.0 does not support Python 3.12  
**Impact**: High - affects ML functionality  
**Mitigation**: 
- Use Python 3.10 or 3.11 for TensorFlow workloads
- Or upgrade to TensorFlow >=2.16 when stable
- Consider PyTorch as alternative

**Resolution**: Install separately based on Python version:
```bash
# Python 3.10-3.11
pip install tensorflow==2.15.0

# Python 3.12
pip install tensorflow>=2.16.0
```

### 2. PyTorch Platform-Specific Installation

**Issue**: PyTorch has different builds for CPU vs GPU  
**Impact**: Medium - affects performance  
**Mitigation**: Install from PyTorch's index with platform selection

**Resolution**:
```bash
# CPU only
pip install torch==2.8.0+cpu -f https://download.pytorch.org/whl/torch_stable.html

# CUDA 11.8
pip install torch==2.8.0+cu118 -f https://download.pytorch.org/whl/torch_stable.html

# CUDA 12.1
pip install torch==2.8.0+cu121 -f https://download.pytorch.org/whl/torch_stable.html
```

### 3. PyMC Complex Dependencies

**Issue**: PyMC has strict version requirements for pytensor, arviz, etc.  
**Impact**: Medium - optional bayesian analysis  
**Mitigation**: Install separately after core dependencies

**Resolution**:
```bash
pip install pymc==5.10.3 arviz==0.17.0 pytensor==2.18.6
```

### 4. Pydantic v2 Breaking Changes

**Issue**: Pydantic v2 has breaking changes from v1  
**Impact**: High if code uses v1 API  
**Mitigation**: Use exact pin, test thoroughly before upgrading

**Action Required**: Audit all pydantic usage if upgrading from v1

### 5. Polars API Evolution

**Issue**: Polars API is evolving rapidly  
**Impact**: Medium - API changes may break code  
**Mitigation**: Exact version pin, test before upgrading

**Recommendation**: Pin exact version and upgrade cautiously

### 6. gevent-websocket Maintenance

**Issue**: gevent-websocket is low maintenance  
**Impact**: Low - optional feature  
**Mitigation**: Consider alternative WebSocket libraries

**Future**: Evaluate migrating to modern async WebSocket libraries

---

## CI/CD Gates

### Gate 1: Missing Import Detection

**Purpose**: Fail CI if any imports are missing  
**Implementation**: `.github/workflows/ci.yml`

```yaml
- name: Check for missing imports
  run: |
    python3 scripts/audit_dependencies.py
    if [ $? -ne 0 ]; then
      echo "❌ Missing dependencies detected!"
      exit 1
    fi
```

### Gate 2: Freeze vs Lock Comparison

**Purpose**: Fail CI if installed packages don't match lock file  
**Implementation**: `.github/workflows/ci.yml`

```yaml
- name: Verify dependency lock
  run: |
    pip freeze > freeze-ci.txt
    python3 scripts/compare_freeze_lock.py freeze-ci.txt constraints-new.txt
```

### Gate 3: Open Range Detection

**Purpose**: Fail CI if core dependencies use open ranges (>=, ~=)  
**Implementation**: `.github/workflows/ci.yml`

```yaml
- name: Check for open version ranges
  run: |
    if grep -E ">=|~=|\*" requirements-core.txt; then
      echo "❌ Open version ranges detected in core dependencies!"
      exit 1
    fi
```

### Gate 4: Security Vulnerability Scan

**Purpose**: Warn on known vulnerabilities  
**Implementation**: `.github/workflows/ci.yml`

```yaml
- name: Security audit
  run: |
    pip install pip-audit
    pip-audit || echo "⚠️  Security vulnerabilities detected"
```

---

## Makefile Targets

### `make deps:verify`

Verify all dependencies are correctly installed and importable.

```bash
make deps:verify
```

**Actions**:
1. Run importability verification
2. Check for missing dependencies
3. Compare freeze with constraints
4. Display summary

### `make deps:lock`

Generate lock file from currently installed packages.

```bash
make deps:lock
```

**Actions**:
1. Run `pip freeze > constraints-frozen.txt`
2. Display diff with current constraints
3. Prompt to update constraints file

### `make deps:audit`

Run full dependency audit.

```bash
make deps:audit
```

**Actions**:
1. Scan all Python files for imports
2. Classify dependencies by role
3. Detect missing packages
4. Generate audit report JSON
5. Display summary

### `make deps:clean`

Clean dependency-related artifacts.

```bash
make deps:clean
```

**Actions**:
1. Remove `__pycache__` directories
2. Remove `*.pyc` files
3. Remove dependency audit reports

---

## Reproducible Build Procedure

### Step 1: Clean Environment

```bash
python3 -m venv venv-clean
source venv-clean/bin/activate
pip install --upgrade pip setuptools wheel
```

### Step 2: Install Dependencies

```bash
pip install -c constraints-new.txt -r requirements-core.txt
```

### Step 3: Verify Installation

```bash
python3 scripts/verify_importability.py
```

### Step 4: Freeze and Compare

```bash
pip freeze > freeze-test.txt
diff freeze-test.txt constraints-new.txt
```

### Step 5: Test Application

```bash
pytest tests/ -v
python3 -m saaaaaa.core.orchestrator --help
```

---

## Maintenance Schedule

### Weekly
- [ ] Check for security advisories: `pip-audit`
- [ ] Review dependency updates on GitHub

### Monthly
- [ ] Review new versions of critical packages
- [ ] Test compatibility with new versions
- [ ] Update documentation with new findings

### Quarterly
- [ ] Major version upgrade evaluation
- [ ] Full dependency audit refresh
- [ ] Performance benchmarking
- [ ] License compliance review

---

## Contact & Support

For dependency-related questions:
1. Check this document first
2. Review existing issues: `github.com/kkkkknhh/SAAAAAA/issues`
3. Create new issue with `dependencies` label

---

**Document Version**: 1.0.0  
**Last Updated**: 2025-11-06  
**Next Review**: 2025-12-06
