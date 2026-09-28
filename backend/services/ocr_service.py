"""
Text extraction from uploaded documents.

- Native/digital PDFs: PyMuPDF (fitz) pulls embedded text directly —
  fast, no OCR needed.
- Scanned PDFs / images: rasterize pages (PyMuPDF) then run Tesseract OCR
  on each page image. Falls back to this path automatically if a PDF page
  has no extractable text layer (i.e. it's a scan).
"""
from __future__ import annotations

import io
import logging
from pathlib import Path

import fitz  # PyMuPDF
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)

MIN_CHARS_PER_PAGE_TO_SKIP_OCR = 20  # below this, assume the page is a scan


def extract_text(file_path: str | Path) -> str:
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix in (".png", ".jpg", ".jpeg", ".tiff", ".bmp"):
        return _ocr_image(path)

    if suffix == ".pdf":
        return _extract_pdf(path)

    raise ValueError(f"Unsupported file type: {suffix}")


def _ocr_image(path: Path) -> str:
    image = Image.open(path)
    text = pytesseract.image_to_string(image)
    return text.strip()


def _extract_pdf(path: Path) -> str:
    doc = fitz.open(path)
    pages_text: list[str] = []

    for page_num, page in enumerate(doc):
        native_text = page.get_text().strip()

        if len(native_text) >= MIN_CHARS_PER_PAGE_TO_SKIP_OCR:
            pages_text.append(native_text)
            continue

        # Likely a scanned page with no text layer — rasterize + OCR it.
        logger.info("Page %d has no text layer, falling back to OCR", page_num)
        pix = page.get_pixmap(dpi=300)
        image = Image.open(io.BytesIO(pix.tobytes("png")))
        pages_text.append(pytesseract.image_to_string(image).strip())

    doc.close()
    return "\n\n".join(pages_text).strip()


def clean_text(raw_text: str) -> str:
    """Light cleanup before chunking: collapse excess whitespace/blank lines."""
    lines = [line.strip() for line in raw_text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)


def chunk_text(text: str, *, target_tokens: int = 400) -> list[str]:
    """
    Rough token-count chunking (per ARCHITECTURE.md: ~300-500 tokens/chunk).
    Uses a ~4-chars-per-token heuristic to avoid pulling in a tokenizer
    dependency just for chunk sizing — good enough for MVP RAG granularity.
    """
    target_chars = target_tokens * 4
    words = text.split(" ")
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for word in words:
        current.append(word)
        current_len += len(word) + 1
        if current_len >= target_chars:
            chunks.append(" ".join(current))
            current = []
            current_len = 0

    if current:
        chunks.append(" ".join(current))

    return chunks
