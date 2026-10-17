"""
Export endpoints — download summary / study notes / flashcards as PDF.
"""
from __future__ import annotations

import asyncio
import re

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.note import StudyNote
from app.models.paper import Paper
from app.services import export_service

router = APIRouter(prefix="/export", tags=["Export"])


def _safe_filename(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", name)[:80]


@router.get("/{paper_id}/summary")
async def export_summary(paper_id: str, db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found.")

    pdf_bytes = await asyncio.to_thread(export_service.generate_summary_pdf, paper)
    filename = f"{_safe_filename(paper.title or paper.original_filename)}_summary.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{paper_id}/study-notes")
async def export_study_notes(paper_id: str, db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found.")
    notes = db.query(StudyNote).filter(StudyNote.paper_id == paper_id).first()
    if not notes:
        raise HTTPException(status_code=404, detail="Study notes have not been generated yet.")

    pdf_bytes = await asyncio.to_thread(export_service.generate_study_notes_pdf, paper, notes)
    filename = f"{_safe_filename(paper.title or paper.original_filename)}_study_notes.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{paper_id}/flashcards")
async def export_flashcards(paper_id: str, db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found.")
    notes = db.query(StudyNote).filter(StudyNote.paper_id == paper_id).first()
    if not notes:
        raise HTTPException(status_code=404, detail="Study notes have not been generated yet.")

    pdf_bytes = await asyncio.to_thread(export_service.generate_flashcards_pdf, paper, notes)
    filename = f"{_safe_filename(paper.title or paper.original_filename)}_flashcards.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
