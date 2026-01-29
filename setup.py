"""F.A.R.F.A.N Setup Configuration"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).resolve().parent / "README.ES.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="farfan-pipeline",
    version="1.0.0",
    description="Framework for Advanced Retrieval of Administrative Narratives - Mechanistic Policy Pipeline",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="F.A.R.F.A.N Development Team",
    python_requires=">=3.11,<3.14",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        # Core API and validation
        "fastapi>=0.109.0",
        "pydantic>=2.0.0",
        "uvicorn>=0.27.0",
        # NLP and transformers
        "transformers>=4.41.0,<4.42.0",
        "sentence-transformers>=3.1.0,<3.2.0",
        "accelerate>=1.2.0",
        "tokenizers>=0.15.0",
        # Bayesian analysis
        "pymc>=5.16.0,<5.17.0",
        "pytensor>=2.25.1,<2.26",
        "arviz>=0.17.0",
        # Machine learning
        "scikit-learn>=1.6.0",
        "numpy>=1.26.4,<2.0.0",
        "scipy>=1.11.0",
        # Graph analysis
        "networkx>=3.0",
        # NLP tools
        "spacy>=3.7.0",
        # PDF processing
        "PyPDF2>=3.0.0",
        "pdfplumber>=0.10.0",
        # Data handling
        "pandas>=2.1.0",
        "pyarrow>=14.0.0",
        # Configuration
        "python-dotenv>=1.0.0",
        # Image/table processing
        "img2table>=1.4.0",
        "opencv-contrib-python-headless>=4.8.0",
        "pillow>=10.0.0",
        "tabula-py>=2.9.0",
        # Utilities
        "requests>=2.31.0",
        "aiohttp>=3.9.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-cov>=4.1.0",
            "pytest-asyncio>=0.23.0",
            "ruff>=0.1.0",
            "mypy>=1.8.0",
            "black>=24.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "farfan-pipeline=farfan_pipeline.entrypoint.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
