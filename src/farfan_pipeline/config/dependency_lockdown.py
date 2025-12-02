"""
Dependency Lockdown

Explicit allowlist of third-party modules permitted in F.A.R.F.A.N pipeline.

This is the SINGLE SOURCE OF TRUTH for:
- Which third-party packages are allowed to be imported.
- Which dynamic imports (if any) are whitelisted.

Maximum hardness interpretation:
- If a module is not in ALLOWED_THIRD_PARTY_MODULES, it MUST NOT be imported.
- If this file is missing or ALLOWED_THIRD_PARTY_MODULES is empty, policy_builder MUST fail hard.
- No silent fallback to requirements.txt is permitted.
"""

from typing import FrozenSet

# Third-party modules explicitly allowed for import
# These MUST correspond to packages in requirements.txt but are explicitly vetted
ALLOWED_THIRD_PARTY_MODULES: FrozenSet[str] = frozenset(
    {
        # Core data science
        "numpy",
        "np",
        "pandas",
        "pd",
        "scipy",
        "sklearn",
        "scikit-learn",
        "scikit_learn",
        # Deep learning
        "torch",
        "pytorch",
        "tensorflow",
        "tf",
        "keras",
        "tf_keras",
        # NLP / Transformers
        "transformers",
        "sentence_transformers",
        "sentencepiece",
        "tokenizers",
        # Vector DB / RAG
        "chromadb",
        "chroma",
        "faiss",
        # LLM integrations
        "langchain",
        "langchain_core",
        "langchain_community",
        "openai",
        "anthropic",
        # Web frameworks
        "pydantic",
        "pydantic_core",
        "fastapi",
        "uvicorn",
        "starlette",
        # Testing
        "pytest",
        "hypothesis",
        "mock",
        # Utilities
        "click",
        "tqdm",
        "requests",
        "httpx",
        "aiohttp",
        "psutil",
        "pypdf",
        "pypdf2",
        "pdfplumber",
        "reportlab",
        # Data formats
        "yaml",
        "pyyaml",
        "toml",
        "tomli",
        "msgpack",
        # Serialization
        "orjson",
        "ujson",
        # Async
        "asyncio",
        "aiofiles",
        # Environment
        "dotenv",
        "python-dotenv",
        "python_dotenv",
        # Logging / Observability
        "loguru",
        "structlog",
        # Type checking (dev)
        "typing_extensions",
        "mypy",
        "mypy_extensions",
        # Linting (dev)
        "ruff",
        "black",
        "isort",
        # Documentation (dev)
        "sphinx",
        "mkdocs",
        # Packaging
        "setuptools",
        "wheel",
        "pip",
        "pipdeptree",
        # Deprecated warnings for migration
        "deprecated",
        "warnings",
    }
)

# Dynamic imports explicitly allowed (optional, default empty)
# These are module names that can be imported via importlib.import_module()
ALLOWED_DYNAMIC_IMPORTS: FrozenSet[str] = frozenset(
    {
        # Add dynamic imports here if needed
        # Example: "farfan_core.plugins.optional_module"
    }
)
