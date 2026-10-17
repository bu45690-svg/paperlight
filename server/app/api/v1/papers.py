"""
Paper upload & management endpoints.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.paper import Paper, PaperStatus
from app.schemas.paper import (
    FavoriteToggle,
    PaperAnalysis,
    PaperStatusResponse,
    PaperSummary,
    PaperUploadResponse,
    ReadingProgressUpdate,
)
from app.services import vector_store
from app.services.analysis_service import process_paper
from app.services.pdf_service import InvalidPDFError, validate_pdf_bytes

router = APIRouter(prefix="/papers", tags=["Papers"])


def _get_paper_or_404(db: Session, paper_id: str) -> Paper:
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found.")
    return paper


@router.post("/upload", response_model=PaperUploadResponse, status_code=201)
async def upload_paper(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a single PDF. Validates it, stores it, then kicks off async analysis."""
    data = await file.read()

    try:
        validate_pdf_bytes(data, file.filename or "upload.pdf")
    except InvalidPDFError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    paper_id = str(uuid.uuid4())
    safe_name = f"{paper_id}.pdf"
    dest_path = settings.UPLOAD_DIR / safe_name
    dest_path.write_bytes(data)

    paper = Paper(
        id=paper_id,
        filename=safe_name,
        original_filename=file.filename or safe_name,
        file_path=str(dest_path),
        file_size_bytes=len(data),
        status=PaperStatus.UPLOADED,
    )
    db.add(paper)
    db.commit()
    db.refresh(paper)

    # Process in the background (extraction, indexing, Gemini analysis) so upload
    # returns immediately even for large multi-page PDFs.
    background_tasks.add_task(process_paper, paper.id)

    return PaperUploadResponse(
        id=paper.id,
        filename=paper.original_filename,
        status=paper.status,
        message="Upload received. Processing started in the background.",
    )


@router.post("/upload-multiple", response_model=List[PaperUploadResponse], status_code=201)
async def upload_multiple_papers(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """Upload multiple PDFs in one request."""
    responses: List[PaperUploadResponse] = []
    for file in files:
        data = await file.read()
        try:
            validate_pdf_bytes(data, file.filename or "upload.pdf")
        except InvalidPDFError as exc:
            responses.append(
                PaperUploadResponse(id="", filename=file.filename or "unknown", status=PaperStatus.FAILED, message=str(exc))
            )
            continue

        paper_id = str(uuid.uuid4())
        safe_name = f"{paper_id}.pdf"
        dest_path = settings.UPLOAD_DIR / safe_name
        dest_path.write_bytes(data)

        paper = Paper(
            id=paper_id,
            filename=safe_name,
            original_filename=file.filename or safe_name,
            file_path=str(dest_path),
            file_size_bytes=len(data),
            status=PaperStatus.UPLOADED,
        )
        db.add(paper)
        db.commit()
        db.refresh(paper)

        background_tasks.add_task(process_paper, paper.id)
        responses.append(
            PaperUploadResponse(id=paper.id, filename=paper.original_filename, status=paper.status, message="Processing started.")
        )
    return responses


@router.get("", response_model=List[PaperSummary])
def list_papers(db: Session = Depends(get_db)):
    papers = db.query(Paper).order_by(Paper.created_at.desc()).all()
    return papers


@router.get("/{paper_id}", response_model=PaperAnalysis)
def get_paper(paper_id: str, db: Session = Depends(get_db)):
    return _get_paper_or_404(db, paper_id)


@router.get("/{paper_id}/status", response_model=PaperStatusResponse)
def get_paper_status(paper_id: str, db: Session = Depends(get_db)):
    paper = _get_paper_or_404(db, paper_id)
    return PaperStatusResponse(id=paper.id, status=paper.status, error_message=paper.error_message)


@router.patch("/{paper_id}/favorite", response_model=PaperSummary)
def toggle_favorite(paper_id: str, payload: FavoriteToggle, db: Session = Depends(get_db)):
    paper = _get_paper_or_404(db, paper_id)
    paper.is_favorite = payload.is_favorite
    db.commit()
    db.refresh(paper)
    return paper


@router.patch("/{paper_id}/progress", response_model=PaperSummary)
def update_progress(paper_id: str, payload: ReadingProgressUpdate, db: Session = Depends(get_db)):
    paper = _get_paper_or_404(db, paper_id)
    paper.reading_progress_percent = max(0, min(100, payload.reading_progress_percent))
    paper.last_opened_at = datetime.utcnow()
    db.commit()
    db.refresh(paper)
    return paper


@router.post("/{paper_id}/open", response_model=PaperSummary)
def mark_opened(paper_id: str, db: Session = Depends(get_db)):
    """Records that a paper was opened, for the Recent Papers bonus feature."""
    paper = _get_paper_or_404(db, paper_id)
    paper.last_opened_at = datetime.utcnow()
    db.commit()
    db.refresh(paper)
    return paper


@router.delete("/{paper_id}", status_code=204)
def delete_paper(paper_id: str, db: Session = Depends(get_db)):
    paper = _get_paper_or_404(db, paper_id)
    Path(paper.file_path).unlink(missing_ok=True)
    vector_store.delete_index(paper.id)
    db.delete(paper)
    db.commit()
    return None
