#!/usr/bin/env python3
"""
Generate comprehensive dependency files for SAAAAAA project.

Generates:
- requirements-core.txt: Core runtime dependencies with exact pins
- requirements-dev.txt: Development and testing dependencies
- requirements-optional.txt: Optional runtime dependencies
- requirements-constraints.txt: Full constraint file with all transitive deps
- Updated pyproject.toml with proper dependency groups
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Set


def load_audit_report(project_root: Path) -> Dict:
    """Load the dependency audit report."""
    report_file = project_root / "dependency_audit_report.json"
    if not report_file.exists():
        print("Error: dependency_audit_report.json not found. Run audit_dependencies.py first.")
        sys.exit(1)
    
    with open(report_file, 'r') as f:
        return json.load(f)


def get_current_versions(requirements_file: Path) -> Dict[str, str]:
    """Extract package versions from existing requirements.txt."""
    versions = {}
    
    if not requirements_file.exists():
        return versions
    
    with open(requirements_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if '==' in line:
                pkg, ver = line.split('==', 1)
                versions[pkg.lower().strip()] = ver.strip()
    
    return versions


# Core runtime dependencies with known compatibility for Python 3.10-3.12
CORE_DEPENDENCIES = {
    # Web frameworks
    "flask": "3.0.3",
    "fastapi": "0.115.6",
    "uvicorn": "0.34.0",
    "httpx": "0.28.1",
    "sse-starlette": "2.2.1",
    "werkzeug": "3.0.6",
    
    # Configuration
    "pyyaml": "6.0.2",
    "python-dotenv": "1.0.1",
    "typer": "0.15.1",
    
    # Data processing - Core
    "numpy": "2.2.1",
    "scipy": "1.15.1",
    "pandas": "2.2.3",
    "polars": "1.19.0",
    "pyarrow": "19.0.0",
    
    # Machine Learning - note: tensorflow and torch need special handling for Python 3.12
    "scikit-learn": "1.6.1",
    # tensorflow is omitted - needs Python <3.12 or version >=2.16
    # torch is omitted - needs to be installed separately based on platform
    
    # NLP
    "transformers": "4.48.3",
    "sentence-transformers": "3.3.1",
    "spacy": "3.8.3",
    
    # Graph Analysis
    "networkx": "3.4.2",
    
    # Bayesian Analysis - note: pymc has strict version requirements
    # pymc omitted for now - complex dependencies
    
    # PDF Processing
    "pdfplumber": "0.11.4",
    "PyPDF2": "3.0.1",
    "PyMuPDF": "1.25.2",
    "python-docx": "1.1.2",
    
    # Data Validation
    "jsonschema": "4.23.0",
    "pydantic": "2.10.6",
    
    # Monitoring & Logging
    "structlog": "24.4.0",
    "tenacity": "9.0.0",
    
    # Security & Hashing
    "blake3": "0.4.1",
    
    # Type hints
    "typing-extensions": "4.12.2",
}

OPTIONAL_DEPENDENCIES = {
    # WebSocket Support
    "flask-cors": "6.0.0",
    "flask-socketio": "5.4.1",
    "python-socketio": "5.14.1",
    "gevent": "24.11.1",
    "gevent-websocket": "0.10.1",
    
    # Authentication
    "pyjwt": "2.10.1",
    
    # Advanced graph analysis
    "igraph": "0.11.8",
    "python-louvain": "0.16",
    "pydot": "3.0.4",
    
    # Causal inference - complex dependencies
    # "dowhy": "0.11.1",
    # "econml": "0.15.1",
    
    # Additional PDF
    "tabula-py": "2.10.0",
    "camelot-py": "0.11.0",
    
    # NLP Additional
    "nltk": "3.9.1",
    "sentencepiece": "0.2.0",
    "tiktoken": "0.8.0",
    "fuzzywuzzy": "0.18.0",
    "python-Levenshtein": "0.26.1",
    "langdetect": "1.0.9",
    
    # Database
    "redis": "5.2.1",
    "sqlalchemy": "2.0.37",
    
    # Production Server
    "gunicorn": "23.0.0",
    
    # Monitoring Advanced
    "prometheus-client": "0.21.1",
    "psutil": "6.1.1",
    "opentelemetry-api": "1.29.0",
    "opentelemetry-sdk": "1.29.0",
    # Note: opentelemetry-instrumentation-fastapi is beta - use with caution
    # Consider moving to dev/test if stability is an issue
    "opentelemetry-instrumentation-fastapi": "0.50b0",
    
    # HTML parsing
    "beautifulsoup4": "4.12.3",
}

DEV_DEPENDENCIES = {
    # Testing
    "pytest": "8.3.4",
    "pytest-cov": "6.0.0",
    "pytest-asyncio": "0.25.2",
    "hypothesis": "6.124.3",
    "schemathesis": "3.38.4",
    
    # Code Quality
    "black": "24.10.0",
    "ruff": "0.9.1",
    "flake8": "7.1.1",
    "mypy": "1.14.1",
    "pyright": "1.1.395",
    
    # Security
    "bandit": "1.8.0",
    
    # Tools
    "import-linter": "2.2",
}

DOCS_DEPENDENCIES = {
    "sphinx": "8.1.3",
    "sphinx-rtd-theme": "3.0.2",
    "myst-parser": "4.0.0",
}


def generate_core_requirements(output_file: Path, versions: Dict[str, str]):
    """Generate requirements-core.txt with exact pins."""
    print(f"Generating {output_file}...")
    
    with open(output_file, 'w') as f:
        f.write("# Core Runtime Dependencies - Exact Pins\n")
        f.write("# Generated by scripts/generate_dependency_files.py\n")
        f.write("# DO NOT EDIT MANUALLY - Update versions in the generator script\n\n")
        f.write("# This file contains ONLY critical runtime dependencies\n")
        f.write("# with exact version pins for reproducibility\n\n")
        
        for pkg, version in sorted(CORE_DEPENDENCIES.items()):
            f.write(f"{pkg}=={version}\n")
        
        f.write("\n# Notes:\n")
        f.write("# - tensorflow requires Python <3.12 or version >=2.16\n")
        f.write("# - torch should be installed separately based on platform\n")
        f.write("# - pymc has complex dependencies - install separately if needed\n")


def generate_optional_requirements(output_file: Path, versions: Dict[str, str]):
    """Generate requirements-optional.txt."""
    print(f"Generating {output_file}...")
    
    with open(output_file, 'w') as f:
        f.write("# Optional Runtime Dependencies - Exact Pins\n")
        f.write("# Generated by scripts/generate_dependency_files.py\n")
        f.write("# Install with: pip install -r requirements-optional.txt\n\n")
        
        for pkg, version in sorted(OPTIONAL_DEPENDENCIES.items()):
            f.write(f"{pkg}=={version}\n")


def generate_dev_requirements(output_file: Path, versions: Dict[str, str]):
    """Generate requirements-dev.txt."""
    print(f"Generating {output_file}...")
    
    with open(output_file, 'w') as f:
        f.write("# Development & Testing Dependencies - Exact Pins\n")
        f.write("# Generated by scripts/generate_dependency_files.py\n")
        f.write("# Install with: pip install -r requirements-dev.txt\n\n")
        f.write("# Include core dependencies\n")
        f.write("-r requirements-core.txt\n\n")
        
        for pkg, version in sorted(DEV_DEPENDENCIES.items()):
            f.write(f"{pkg}=={version}\n")


def generate_docs_requirements(output_file: Path, versions: Dict[str, str]):
    """Generate requirements-docs.txt."""
    print(f"Generating {output_file}...")
    
    with open(output_file, 'w') as f:
        f.write("# Documentation Dependencies - Exact Pins\n")
        f.write("# Generated by scripts/generate_dependency_files.py\n")
        f.write("# Install with: pip install -r requirements-docs.txt\n\n")
        
        for pkg, version in sorted(DOCS_DEPENDENCIES.items()):
            f.write(f"{pkg}=={version}\n")


def generate_all_requirements(output_file: Path, versions: Dict[str, str]):
    """Generate requirements-all.txt combining all dependencies."""
    print(f"Generating {output_file}...")
    
    with open(output_file, 'w') as f:
        f.write("# All Dependencies - For Complete Installation\n")
        f.write("# Generated by scripts/generate_dependency_files.py\n")
        f.write("# Install with: pip install -r requirements-all.txt\n\n")
        
        f.write("# Core Runtime\n")
        f.write("-r requirements-core.txt\n\n")
        
        f.write("# Optional Runtime\n")
        f.write("-r requirements-optional.txt\n\n")
        
        f.write("# Development\n")
        for pkg, version in sorted(DEV_DEPENDENCIES.items()):
            f.write(f"{pkg}=={version}\n")
        f.write("\n")
        
        f.write("# Documentation\n")
        for pkg, version in sorted(DOCS_DEPENDENCIES.items()):
            f.write(f"{pkg}=={version}\n")


def generate_constraints_file(output_file: Path):
    """Generate constraints.txt file."""
    print(f"Generating {output_file}...")
    
    with open(output_file, 'w') as f:
        f.write("# Constraints file - Exact version pins for ALL dependencies\n")
        f.write("# Generated by scripts/generate_dependency_files.py\n")
        f.write("# Use with: pip install -c constraints.txt -r requirements.txt\n\n")
        f.write("# This file prevents dependency conflicts by pinning all versions\n")
        f.write("# including transitive dependencies.\n\n")
        f.write("# To regenerate transitive dependencies:\n")
        f.write("# 1. Install all requirements in a clean venv\n")
        f.write("# 2. Run: pip freeze > constraints-full.txt\n")
        f.write("# 3. Review and merge into this file\n\n")
        
        # Combine all dependencies
        all_deps = {}
        all_deps.update(CORE_DEPENDENCIES)
        all_deps.update(OPTIONAL_DEPENDENCIES)
        all_deps.update(DEV_DEPENDENCIES)
        all_deps.update(DOCS_DEPENDENCIES)
        
        for pkg, version in sorted(all_deps.items()):
            f.write(f"{pkg}=={version}\n")


def main():
    """Main entry point."""
    project_root = Path(__file__).parent.parent
    
    # Load existing versions from requirements.txt
    existing_versions = get_current_versions(project_root / "requirements.txt")
    
    # Generate all requirement files
    generate_core_requirements(project_root / "requirements-core.txt", existing_versions)
    generate_optional_requirements(project_root / "requirements-optional.txt", existing_versions)
    generate_dev_requirements(project_root / "requirements-dev.txt", existing_versions)
    generate_docs_requirements(project_root / "requirements-docs.txt", existing_versions)
    generate_all_requirements(project_root / "requirements-all.txt", existing_versions)
    generate_constraints_file(project_root / "constraints-new.txt")
    
    print("\n" + "="*80)
    print("Dependency files generated successfully!")
    print("="*80)
    print("\nGenerated files:")
    print("  - requirements-core.txt: Core runtime dependencies")
    print("  - requirements-optional.txt: Optional runtime dependencies")
    print("  - requirements-dev.txt: Development dependencies (includes core)")
    print("  - requirements-docs.txt: Documentation dependencies")
    print("  - requirements-all.txt: All dependencies combined")
    print("  - constraints-new.txt: Version constraints for all packages")
    print("\nNext steps:")
    print("  1. Review the generated files")
    print("  2. Test installation: pip install -r requirements-core.txt")
    print("  3. Run verification: make deps:verify")
    print("  4. Replace old files if everything works")


if __name__ == "__main__":
    main()
