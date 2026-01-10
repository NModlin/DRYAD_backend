# app/utils/pdf_extractor.py
"""
Optional PDF text extraction utilities using PyMuPDF (pymupdf).
This module is safe to import even if pymupdf is not installed.
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except Exception as e:  # ImportError and others (platform issues)
    PYMUPDF_AVAILABLE = False
    _IMPORT_ERR = e


def is_available() -> bool:
    """Return True if PyMuPDF is available."""
    return PYMUPDF_AVAILABLE


def extract_text_from_pdf_bytes(data: bytes, max_pages: Optional[int] = None) -> str:
    """Extract text from a PDF given as bytes.

    Args:
        data: The raw bytes of the PDF file.
        max_pages: Optional limit on number of pages to parse.

    Returns:
        A string with concatenated text of the parsed pages. Empty string if extraction fails.
    """
    if not PYMUPDF_AVAILABLE:
        logger.warning("pymupdf not installed; returning placeholder for PDF text extraction")
        return ""

    try:
        text_parts: list[str] = []
        with fitz.open(stream=data, filetype="pdf") as doc:
            total = len(doc)
            pages_to_read = total if max_pages is None else min(max_pages, total)
            for i in range(pages_to_read):
                page = doc.load_page(i)
                # 'text' gets plain text. Alternatives: 'blocks', 'json', etc.
                text_parts.append(page.get_text("text"))
        return "\n\n".join(part.strip() for part in text_parts if part)
    except Exception as e:
        logger.error(f"Failed to extract PDF text: {e}")
        return ""

