"""
Factory Layer for Processing Module I/O Operations

This module provides centralized I/O operations for the processing package,
implementing a clean separation between I/O and business logic following
the Ports and Adapters (Hexagonal Architecture) pattern.

All file I/O for the processing package should be handled through this factory.
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Any
from saaaaaa.core.calibration.decorators import calibrated_method

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

logger = logging.getLogger(__name__)

# ============================================================================
# FILE I/O OPERATIONS
# ============================================================================

def load_json(file_path: str | Path) -> dict[str, Any]:
    """
    Load JSON data from file.

    Args:
        file_path: Path to JSON file

    Returns:
        Dict containing the loaded JSON data

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    logger.info(f"Loaded JSON from {file_path}")
    return data

def save_json(data: dict[str, Any], file_path: str | Path, indent: int = 2) -> None:
    """
    Save data to JSON file with formatted output.

    Args:
        data: Dictionary to save
        file_path: Path to output JSON file
        indent: Indentation level for formatting
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)

    logger.info(f"Saved JSON to {file_path}")

def read_text_file(file_path: str | Path, encodings: list = None) -> str:
    """
    Read text file with automatic encoding detection.

    Args:
        file_path: Path to text file
        encodings: List of encodings to try (default: utf-8, latin-1, cp1252)

    Returns:
        String content of the file

    Raises:
        FileNotFoundError: If file doesn't exist
        UnicodeDecodeError: If file cannot be decoded with any encoding
    """
    if encodings is None:
        encodings = ["utf-8", "latin-1", "cp1252"]

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    last_error = None
    for encoding in encodings:
        try:
            with open(file_path, encoding=encoding) as f:
                content = f.read()
            logger.debug(f"Successfully read {file_path} with {encoding}")
            return content
        except (UnicodeDecodeError, UnicodeError) as e:
            last_error = e
            continue

    raise UnicodeDecodeError(
        "utf-8", b"", 0, 0,
        f"Could not decode {file_path} with any of: {encodings}. Last error: {last_error}"
    )

def write_text_file(content: str, file_path: str | Path) -> None:
    """
    Write text content to file with UTF-8 encoding.

    Args:
        content: Text content to write
        file_path: Path to output file
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(f"Written {len(content)} characters to {file_path}")

def calculate_file_hash(file_path: str | Path) -> str:
    """
    Calculate SHA-256 hash of a file for traceability.

    Args:
        file_path: Path to file

    Returns:
        Hexadecimal string representation of the file's SHA-256 hash
    """
    file_path = Path(file_path)
    sha256_hash = hashlib.sha256()

    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)

    return sha256_hash.hexdigest()

# ============================================================================
# PDF OPERATIONS
# ============================================================================

def extract_pdf_text_all_pages(file_path: str | Path) -> str:
    """
    Extract all text from a PDF file.

    Args:
        file_path: Path to PDF file

    Returns:
        Concatenated text from all pages

    Raises:
        ImportError: If pdfplumber is not installed
        FileNotFoundError: If file doesn't exist
    """
    if pdfplumber is None:
        raise ImportError("pdfplumber is required for PDF operations. Install with: pip install pdfplumber")

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    all_text = []

    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            try:
                text = page.extract_text() or ""
                if text.strip():
                    all_text.append(f"\n--- Página {page_num} ---\n")
                    all_text.append(text)
            except Exception as e:
                logger.warning(f"Error extracting page {page_num}: {e}")
                continue

    result = "\n".join(all_text)
    logger.info(f"Extracted {len(result)} characters from {file_path}")
    return result

def extract_pdf_text_single_page(file_path: str | Path, page_num: int, total_pages: int = None) -> str:
    """
    Extract text from a single page of a PDF.

    Args:
        file_path: Path to PDF file
        page_num: Page number to extract (1-indexed)
        total_pages: Total number of pages (optional, for validation)

    Returns:
        Text content of the specified page

    Raises:
        ImportError: If pdfplumber is not installed
        FileNotFoundError: If file doesn't exist
        ValueError: If page number is out of range
    """
    if pdfplumber is None:
        raise ImportError("pdfplumber is required for PDF operations. Install with: pip install pdfplumber")

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    with pdfplumber.open(file_path) as pdf:
        if total_pages and (page_num < 1 or page_num > total_pages):
            raise ValueError(f"Page {page_num} out of range (1-{total_pages})")

        if page_num < 1 or page_num > len(pdf.pages):
            raise ValueError(f"Page {page_num} out of range (1-{len(pdf.pages)})")

        text = pdf.pages[page_num - 1].extract_text() or ""
        return text

def get_pdf_page_count(file_path: str | Path) -> int:
    """
    Get the number of pages in a PDF file.

    Args:
        file_path: Path to PDF file

    Returns:
        Number of pages in the PDF

    Raises:
        ImportError: If pdfplumber is not installed
        FileNotFoundError: If file doesn't exist
    """
    if pdfplumber is None:
        raise ImportError("pdfplumber is required for PDF operations. Install with: pip install pdfplumber")

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    with pdfplumber.open(file_path) as pdf:
        return len(pdf.pages)
