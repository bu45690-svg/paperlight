"""
PDF processing service.

Responsible for validating uploaded PDFs and extracting per-page text using pypdf.
Kept dependency-light (no heavy OCR) since papers are expected to be text-based PDFs.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import List

from pypdf import PdfReader

from app.core.config import settings


class InvalidPDFError(Exception):
    pass


@dataclass
class PageText:
    page_number: int  # 1-indexed
    text: str


@dataclass
class ExtractedDocument:
    total_pages: int
    pages: List[PageText]
    full_text: str
    char_count: int


def validate_pdf_bytes(data: bytes, filename: str) -> None:
    """Raise InvalidPDFError if the upload isn't an acceptable PDF."""
    if not filename.lower().endswith(".pdf"):
        raise InvalidPDFError("Only .pdf files are supported.")

    if len(data) == 0:
        raise InvalidPDFError("Uploaded file is empty.")

    if len(data) > settings.max_upload_size_bytes:
        raise InvalidPDFError(
            f"File exceeds the maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
        )

    if not data.startswith(b"%PDF-"):
        raise InvalidPDFError("File does not appear to be a valid PDF (bad header).")


def extract_text(file_path: Path) -> ExtractedDocument:
    """Extract text from every page of a PDF file on disk."""
    try:
        reader = PdfReader(str(file_path))
    except Exception as exc:  # pragma: no cover - defensive
        raise InvalidPDFError(f"Failed to parse PDF: {exc}") from exc

    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception as exc:
            raise InvalidPDFError("PDF is encrypted and could not be decrypted.") from exc

    pages: List[PageText] = []
    full_text_parts: List[str] = []

    for i, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        pages.append(PageText(page_number=i, text=text))
        full_text_parts.append(text)

    full_text = "\n".join(full_text_parts)

    return ExtractedDocument(
        total_pages=len(reader.pages),
        pages=pages,
        full_text=full_text,
        char_count=len(full_text),
    )


def count_references(full_text: str) -> int:
    """Best-effort heuristic count of reference entries in a paper's References section."""
    import re

    lower = full_text.lower()
    idx = lower.rfind("references")
    if idx == -1:
        idx = lower.rfind("bibliography")
    if idx == -1:
        return 0

    tail = full_text[idx:]
    # Count patterns like "[1]", "[12]" or leading "1." numbered entries at line starts.
    bracket_matches = re.findall(r"\[\d{1,3}\]", tail)
    if bracket_matches:
        return len(set(bracket_matches))

    numbered_matches = re.findall(r"(?m)^\s*\d{1,3}[.)]\s+\S", tail)
    return len(numbered_matches)
