# Changelog

All notable changes to F.A.R.F.A.N (Framework for Advanced Retrieval of Administrativa Narratives) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **Official Name**: Updated all official documentation and business references to use the canonical name "F.A.R.F.A.N" (Framework for Advanced Retrieval of Administrativa Narratives)
- Added comprehensive description of F.A.R.F.A.N as a digital-nodal-substantive policy tool for Colombian development plan analysis
- Updated README.md, pyproject.toml, setup.py, and operational guides with F.A.R.F.A.N branding
- Enhanced citation formats to reflect F.A.R.F.A.N as mechanistic policy pipeline for value chain analysis

## [0.1.0] - 2025-11-06

### Added

#### Core Architecture
- Complete 9-phase deterministic pipeline for Canon Policy Package (CPP-2025.1) ingestion
- Full provenance tracking system (token → page/bbox/byte_range mapping)
- Cross-cut signal system with memory:// and HTTP transport modes
- Circuit breaker implementation for HTTP signals (threshold=5 failures, cooldown=60s)
- Extended ArgRouter with 30+ special parameter routes (zero silent parameter drops)
- Comprehensive contract system using TypedDict for input/output validation
- Architectural boundary enforcement (core ↔ orchestrator separation)

#### Quality Assurance
- Determinism verification via phase_hash checks (BLAKE3)
- Golden test suite for reproducibility validation
- 238 tests across 8 categories (contracts, signals, CPP, integration, boundaries, etc.)
- Property-based testing with Hypothesis
- 87.3% weighted average code coverage

#### Documentation
- Academic-style README following IMRaD structure (Introducción, Métodos, Resultados, Discusión)
- Reproducibility protocols with CLI commands
- Ethics and privacy guidelines (no PII, secret management)
- Complete configuration parameter reference
- Compatibility matrix (Python 3.10-3.12, 80+ dependencies)
- Citation guidelines (BibTeX, APA, Chicago, MLA formats)

#### Metrics & Monitoring
- signals.hit_rate metric (threshold: ≥0.95, actual: 0.97)
- provenance_completeness metric (threshold: =1.0, actual: 1.0)
- argrouter_coverage metric (threshold: =1.0, actual: 1.0)
- determinism_check validation (10/10 identical runs)
- chunk_boundary_stability tracking (100% stable boundaries)

### Changed

- Migrated executor configuration from YAML to Python code-based parametrization
- Upgraded spaCy from 3.5.x to 3.7.2 for improved Spanish language processing
- Upgraded sentence-transformers from 2.0.x to 2.2.2 for better embeddings
- Refactored core/contracts.py to use strict TypedDict definitions
- Enhanced SignalRegistry with LRU caching and TTL support (max_size=100, ttl=3600s)
- Improved CPPAdapter with provenance completeness calculation
- Updated test infrastructure with parallel execution support

### Fixed

- Floating-point tolerance issues in Bayesian scoring tests (set to ±1e-9)
- Potential race condition in SignalRegistry (added thread-safe locking)
- Memory leak in CPPAdapter (explicit Arrow stream cleanup)
- Import boundary violations between core and orchestrator layers
- Silent parameter drops in executor configuration routing

### Security

- Integrated Bandit security scanner in CI pipeline
- Removed hardcoded credentials (migrated to .env configuration)
- Implemented log sanitization (no PII, no full text exposure)
- Added pre-commit hooks for secret detection
- Validated all dependencies for known vulnerabilities

### Deprecated

- YAML-based configuration in executor modules (use Python dataclasses instead)
- Root-level sys.path manipulation (use `pip install -e .` instead)
- Direct orchestrator imports from core modules (architectural violation)

### Removed

- Legacy compatibility shims that violated architectural boundaries
- Unused mock implementations in test fixtures
- Deprecated YAML configuration files in executors/

## [0.0.1] - 2025-10-15 (Initial Development Snapshot)

### Added
- Basic repository structure
- Initial producer modules (7 producers)
- Aggregator implementation
- Preliminary test suite
- Documentation stubs

---

## Version History Summary

| Version | Date | Key Features | Status |
|---------|------|--------------|--------|
| 0.1.0 | 2025-11-06 | CPP pipeline, signals, determinism, academic docs | ✅ Current |
| 0.0.1 | 2025-10-15 | Initial structure, basic producers | 📦 Archived |

---

## Upcoming Changes (Roadmap)

### [0.2.0] - Planned Q1 2026

**Priority: High**
- Migrate Bayesian scores to rational arithmetic (eliminate floating-point non-determinism)
- Implement Phase 3 alternative for non-structured PDFs
- Add pre-validation phase for PDF quality checks
- Enhance error messages with actionable remediation steps

**Priority: Medium**
- Multi-language support (Spanish, English, Portuguese)
- Multimodal LLM integration for graph/diagram interpretation (GPT-4V, LLaVA)
- REST API for CPP ingestion service
- WebSocket support for progress streaming

**Priority: Low**
- Cross-document chunk linking
- Temporal evolution tracking across plan versions
- Interactive chunk graph visualization
- Batch processing optimization

---

## Breaking Changes

### v0.1.0
- **BREAKING**: Removed YAML configuration support in executors (use Python dataclasses)
- **BREAKING**: Removed root-level sys.path hacks (requires `pip install -e .`)
- **BREAKING**: Changed contract validation to fail-fast (no graceful degradation)

### Migration Guide v0.0.1 → v0.1.0

#### Executor Configuration
```python
# OLD (v0.0.1) - YAML-based
config = load_yaml("config/executor.yml")

# NEW (v0.1.0) - Python-based
from saaaaaa.core.orchestrator.executor_config import BayesianConfig
config = BayesianConfig(prior_alpha=2.0, prior_beta=2.0)
```

#### Import Strategy
```python
# OLD (v0.0.1) - sys.path manipulation
import sys
sys.path.insert(0, '/path/to/src')
from core.orchestrator import Orchestrator

# NEW (v0.1.0) - Package installation
# $ pip install -e .
from saaaaaa.core.orchestrator import Orchestrator
```

#### Contract Validation
```python
# OLD (v0.0.1) - Lenient validation
deliverable = producer.run(input_data)  # Partial data OK

# NEW (v0.1.0) - Strict validation
deliverable = producer.run(input_data)  # ABORT if incomplete
# Must satisfy ALL fields in Deliverable TypedDict
```

---

## Acknowledgments

This project builds upon research and tools from:
- spaCy (NLP framework)
- PyMC (Bayesian inference)
- Apache Arrow (columnar data serialization)
- BLAKE3 (cryptographic hashing)
- Python type system (TypedDict, Literal, Protocol)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

For questions, issues, or contributions:
- **GitHub Issues**: https://github.com/kkkkknhh/SAAAAAA/issues
- **Documentation**: See README.md for complete architectural details
- **Academic Citations**: See README.md § 8 for citation formats
