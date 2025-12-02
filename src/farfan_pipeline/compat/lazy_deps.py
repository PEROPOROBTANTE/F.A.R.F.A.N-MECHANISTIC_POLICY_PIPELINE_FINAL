"""
Lazy Loading for Heavy Dependencies

This module provides lazy-loaded imports for heavy optional dependencies
to reduce import-time overhead and improve startup performance.

Heavy dependencies include:
- polars: Fast DataFrame library (50-200ms import time)
- pyarrow: Arrow format support (50-150ms import time)
- torch: Deep learning framework (500-1500ms import time)
- tensorflow: Machine learning framework (1000-3000ms import time)
- transformers: NLP models (200-500ms import time)
- spacy: NLP processing (200-400ms import time)

Usage:
    from farfan_core.compat.lazy_deps import get_polars, get_pyarrow

    def process_dataframe(data):
        pl = get_polars()  # Lazy-loaded on first call
        return pl.DataFrame(data)
"""

from __future__ import annotations

from typing import Any

from .safe_imports import lazy_import


def get_polars() -> Any:
    """
    Lazy-load polars library.

    Returns
    -------
    module
        The polars module

    Raises
    ------
    ImportErrorDetailed
        If polars is not installed

    Examples
    --------
    >>> pl = get_polars()
    >>> df = pl.DataFrame({"a": [1, 2, 3]})
    """
    return lazy_import(
        "polars",
        hint="Install with: pip install polars\n"
             "Or install analytics extra: pip install farfan_core[analytics]"
    )


def get_pyarrow() -> Any:
    """
    Lazy-load pyarrow library.

    Returns
    -------
    module
        The pyarrow module

    Raises
    ------
    ImportErrorDetailed
        If pyarrow is not installed

    Examples
    --------
    >>> pa = get_pyarrow()
    >>> table = pa.table({"a": [1, 2, 3]})
    """
    return lazy_import(
        "pyarrow",
        hint="Install with: pip install pyarrow\n"
             "This is a core dependency for Arrow format support."
    )


def get_torch() -> Any:
    """
    Lazy-load torch library.

    Returns
    -------
    module
        The torch module

    Raises
    ------
    ImportErrorDetailed
        If torch is not installed

    Examples
    --------
    >>> torch = get_torch()
    >>> tensor = torch.tensor([1, 2, 3])
    """
    return lazy_import(
        "torch",
        hint="Install with: pip install torch\n"
             "Or install ml extra: pip install farfan_core[ml]"
    )


def get_tensorflow() -> Any:
    """
    Lazy-load tensorflow library.

    Returns
    -------
    module
        The tensorflow module

    Raises
    ------
    ImportErrorDetailed
        If tensorflow is not installed

    Examples
    --------
    >>> tf = get_tensorflow()
    >>> tensor = tf.constant([1, 2, 3])
    """
    return lazy_import(
        "tensorflow",
        hint="Install with: pip install tensorflow\n"
             "Or install ml extra: pip install farfan_core[ml]"
    )


def get_transformers() -> Any:
    """
    Lazy-load transformers library.

    Returns
    -------
    module
        The transformers module

    Raises
    ------
    ImportErrorDetailed
        If transformers is not installed

    Examples
    --------
    >>> transformers = get_transformers()
    >>> model = transformers.AutoModel.from_pretrained("bert-base-uncased")
    """
    return lazy_import(
        "transformers",
        hint="Install with: pip install transformers\n"
             "Or install nlp extra: pip install farfan_core[nlp]"
    )


def get_spacy() -> Any:
    """
    Lazy-load spacy library.

    Returns
    -------
    module
        The spacy module

    Raises
    ------
    ImportErrorDetailed
        If spacy is not installed

    Examples
    --------
    >>> spacy = get_spacy()
    >>> nlp = spacy.load("es_core_news_sm")
    """
    return lazy_import(
        "spacy",
        hint="Install with: pip install spacy\n"
             "Then download language model: python -m spacy download es_core_news_sm\n"
             "Or install nlp extra: pip install farfan_core[nlp]"
    )


def get_pandas() -> Any:
    """
    Lazy-load pandas library.

    This is typically a required dependency but we lazy-load it
    to reduce import-time overhead.

    Returns
    -------
    module
        The pandas module

    Raises
    ------
    ImportErrorDetailed
        If pandas is not installed

    Examples
    --------
    >>> pd = get_pandas()
    >>> df = pd.DataFrame({"a": [1, 2, 3]})
    """
    return lazy_import(
        "pandas",
        hint="Install with: pip install pandas\n"
             "This is a core dependency."
    )


def get_numpy() -> Any:
    """
    Lazy-load numpy library.

    This is typically a required dependency but we lazy-load it
    to reduce import-time overhead in modules that don't always need it.

    Returns
    -------
    module
        The numpy module

    Raises
    ------
    ImportErrorDetailed
        If numpy is not installed

    Examples
    --------
    >>> np = get_numpy()
    >>> array = np.array([1, 2, 3])
    """
    return lazy_import(
        "numpy",
        hint="Install with: pip install numpy\n"
             "This is a core dependency."
    )


# Convenience mapping for programmatic access
LAZY_DEPS = {
    "polars": get_polars,
    "pyarrow": get_pyarrow,
    "torch": get_torch,
    "tensorflow": get_tensorflow,
    "transformers": get_transformers,
    "spacy": get_spacy,
    "pandas": get_pandas,
    "numpy": get_numpy,
}


def get_lazy_dep(name: str) -> Any:
    """
    Get a lazy-loaded dependency by name.

    Parameters
    ----------
    name : str
        Name of the dependency (e.g., "polars", "torch")

    Returns
    -------
    module
        The requested module

    Raises
    ------
    KeyError
        If the dependency name is not recognized
    ImportErrorDetailed
        If the dependency is not installed

    Examples
    --------
    >>> polars = get_lazy_dep("polars")
    >>> torch = get_lazy_dep("torch")
    """
    if name not in LAZY_DEPS:
        raise KeyError(
            f"Unknown lazy dependency: {name}. "
            f"Available: {', '.join(LAZY_DEPS.keys())}"
        )

    return LAZY_DEPS[name]()


__all__ = [
    "get_polars",
    "get_pyarrow",
    "get_torch",
    "get_tensorflow",
    "get_transformers",
    "get_spacy",
    "get_pandas",
    "get_numpy",
    "get_lazy_dep",
    "LAZY_DEPS",
]
