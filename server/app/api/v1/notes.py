"""
Study notes generation endpoints — exam notes, flashcards, bullet notes, Q&A, MCQs.
"""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException
from pathlib import Path
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.note import StudyNote
from app.models.paper import Paper, PaperStatus
from app.schemas.note import StudyNotesResponse
from app.services import gemini_service, pdf_service

router = APIRouter(prefix="/notes", tags=["Study Notes"])


@router.post("/{paper_id}/generate", response_model=StudyNotesResponse)
async def generate_notes(paper_id: str, db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found.")
    if paper.status != PaperStatus.READY:
        raise HTTPException(status_code=409, detail=f"Paper is not ready yet (status: {paper.status}).")

    # Re-extract text (cheap, avoids storing the full raw text in the DB).
    extracted = await asyncio.to_thread(pdf_service.extract_text, Path(paper.file_path))

    try:
        result = await asyncio.to_thread(gemini_service.generate_study_notes, extracted.full_text)
    except gemini_service.GeminiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    existing = db.query(StudyNote).filter(StudyNote.paper_id == paper_id).first()
    if existing:
        note = existing
    else:
        note = StudyNote(paper_id=paper_id)
        db.add(note)

    note.exam_notes = result.get("exam_notes", [])
    note.flashcards = result.get("flashcards", [])
    note.bullet_notes = result.get("bullet_notes", [])
    note.interview_questions = result.get("interview_questions", [])
    note.viva_questions = result.get("viva_questions", [])
    note.mcqs = result.get("mcqs", [])

    db.commit()
    db.refresh(note)
    return note


@router.get("/{paper_id}", response_model=StudyNotesResponse)
def get_notes(paper_id: str, db: Session = Depends(get_db)):
    note = db.query(StudyNote).filter(StudyNote.paper_id == paper_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Study notes not yet generated for this paper.")
    return note
