"""
Orchestrates the full pipeline for a newly uploaded paper:
  extract text -> build FAISS index -> run Gemini analysis -> persist results.

Designed to run in a background task so the upload endpoint returns immediately.
"""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.paper import Paper, PaperStatus
from app.services import gemini_service, pdf_service, vector_store

logger = logging.getLogger(__name__)


def process_paper(paper_id: str) -> None:
    """Runs synchronously inside a background thread (see api/v1/papers.py)."""
    db: Session = SessionLocal()
    try:
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            logger.error("process_paper: paper %s not found", paper_id)
            return

        try:
            _run_pipeline(db, paper)
        except Exception as exc:  # noqa: BLE001 - persist any failure to the DB
            logger.exception("Paper processing failed for %s", paper_id)
            paper.status = PaperStatus.FAILED
            paper.error_message = str(exc)
            db.commit()
    finally:
        db.close()


def _run_pipeline(db: Session, paper: Paper) -> None:
    from pathlib import Path

    # --- 1. Extract text ---
    paper.status = PaperStatus.EXTRACTING
    db.commit()

    extracted = pdf_service.extract_text(Path(paper.file_path))
    paper.total_pages = extracted.total_pages
    paper.raw_text_char_count = extracted.char_count
    paper.references_count = pdf_service.count_references(extracted.full_text)
    db.commit()

    if extracted.char_count < 50:
        raise ValueError("No readable text extracted — the PDF may be a scanned image without OCR.")

    # --- 2. Build vector index (for RAG chat + search) ---
    paper.status = PaperStatus.INDEXING
    db.commit()

    index_path = vector_store.build_index(paper.id, extracted.pages)
    paper.faiss_index_path = index_path
    db.commit()

    # --- 3. Run Gemini structured analysis ---
    paper.status = PaperStatus.ANALYZING
    db.commit()

    analysis = gemini_service.analyze_paper(extracted.full_text)

    paper.title = analysis.get("title") or paper.original_filename
    paper.executive_summary = analysis.get("executive_summary", "")
    paper.abstract_summary = analysis.get("abstract_summary", "")
    paper.key_contributions = analysis.get("key_contributions", [])
    paper.methodology = analysis.get("methodology", "")
    paper.results = analysis.get("results", "")
    paper.limitations = analysis.get("limitations", "")
    paper.future_work = analysis.get("future_work", "")
    paper.keywords = analysis.get("keywords", [])
    paper.important_equations = analysis.get("important_equations", [])
    paper.important_figures = analysis.get("important_figures", [])

    paper.status = PaperStatus.READY
    db.commit()
