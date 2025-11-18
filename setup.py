"""
Setup configuration for F.A.R.F.A.N package.

F.A.R.F.A.N (Framework for Advanced Retrieval of Administrativa Narratives) is a 
mechanistic policy pipeline for comprehensive analysis of Colombian municipal development 
plans. It integrates 584 analytical methods across 300 policy evaluation questions using 
a chess-based orchestration strategy with 7 producer modules and 1 aggregator.

F.A.R.F.A.N is a digital-nodal-substantive policy tool that provides evidence-based, 
rigorous analysis of development plans through the lens of policy causal mechanisms 
and value chain heuristics.

Installation:
    pip install -e .

Usage:
    python3 -m saaaaaa.core.orchestrator --input plan.pdf --mode full

For more information, see README.md and OPERATIONAL_GUIDE.md
"""

from pathlib import Path

from setuptools import find_packages, setup

# Read long description from README
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    with open(readme_file, encoding="utf-8") as f:
        long_description = f.read()

# Use flexible dependency ranges instead of strict pins from requirements.txt
# requirements.txt is for development/production pinning, not for package metadata
install_requires = [
    "numpy>=1.26.0,<2.0",
    "pandas>=2.2.0",
    "scipy>=1.14.0",
    "scikit-learn>=1.5.0", # Lowered from 1.6.0 to be compatible with econml<1.6
    "pyarrow>=19.0.0",
    "polars>=1.19.0",
    "networkx>=3.4.0",
    "pydantic>=2.10.0",
    "flask>=3.0.0",
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.34.0",
    "httpx>=0.28.0",
    "pyyaml>=6.0.2",
    "jsonschema>=4.23.0",
    "langdetect>=1.0.9",
    "blake3>=0.4.1",
    "tenacity>=9.0.0",
    "sse-starlette>=2.2.0",
    "structlog>=24.4.0",
    "opentelemetry-api>=1.29.0",
    "opentelemetry-sdk>=1.29.0",
    "huggingface-hub>=0.20.0,<1.0.0",
    "transformers>=4.41.0,<4.54.0",
    "sentence-transformers>=3.1.0,<3.2.0",
    "spacy>=3.8.0",
    "nltk>=3.9.0",
    "pdfplumber>=0.11.0",
    "PyPDF2>=3.0.0",
    "PyMuPDF>=1.25.0",
    "typer>=0.15.0",
    "ftfy>=6.0.0",  # Robust text encoding repair (mojibake fixing)
]

setup(
    name="saaaaaa",
    version="0.1.0",
    description="Strategic Policy Analysis System - Doctoral-level integration of 584 methods across 300 questions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="SAAAAAA Development Team",
    url="https://github.com/kkkkknhh/SAAAAAA",
    project_urls={
        "Bug Tracker": "https://github.com/kkkkknhh/SAAAAAA/issues",
        "Documentation": "https://github.com/kkkkknhh/SAAAAAA#readme",
        "Source Code": "https://github.com/kkkkknhh/SAAAAAA",
    },
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires="~=3.12.0",
    install_requires=install_requires,
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-cov>=4.1.0",
            "black>=24.3.0",
            "flake8>=7.0.0",
            "mypy>=1.0.0",
            "ruff>=0.1.0",
            "hypothesis>=6.92.2",
        ],
        "docs": [
            "sphinx>=7.0.0",
            "sphinx-rtd-theme>=1.3.0",
        ],
        "ml": [
            "torch>=2.0.0",
            "tensorflow>=2.16.0",
            "tf-keras>=2.16.0",  # Required for transformers compatibility with TensorFlow 2.16+
        ],
        "bayesian": [
            "pytensor>=2.25.1,<2.26",
            "pymc==5.16.2",
            "arviz>=0.20.0",
        ],
        "all": [
            "torch>=2.0.0",
            "tensorflow>=2.16.0",
            "tf-keras>=2.16.0",  # Required for transformers compatibility with TensorFlow 2.16+
            "pytensor>=2.25.1,<2.26",
            "pymc==5.16.2",
            "arviz>=0.20.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "saaaaaa=saaaaaa.core.orchestrator:main",
            "saaaaaa-api=saaaaaa.api.api_server:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
    ],
    keywords=[
        "policy analysis",
        "bayesian inference",
        "causal inference",
        "natural language processing",
        "machine learning",
        "municipal planning",
        "development plans",
        "evidential reasoning",
        "theory of change",
        "semantic analysis",
    ],
    include_package_data=True,
    zip_safe=False,
)
