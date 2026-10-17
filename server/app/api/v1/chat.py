"""
RAG chat endpoints — ask grounded questions about a specific paper.
"""
from __future__ import annotations

import asyncio
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.chat import ChatMessage
from app.models.paper import Paper, PaperStatus
from app.schemas.chat import ChatAnswerResponse, ChatHistoryItem, ChatQuestionRequest
from app.services import gemini_service, vector_store

router = APIRouter(prefix="/chat", tags=["Chat (RAG)"])


@router.post("/{paper_id}/ask", response_model=ChatAnswerResponse)
async def ask_question(paper_id: str, payload: ChatQuestionRequest, db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found.")
    if paper.status != PaperStatus.READY:
        raise HTTPException(status_code=409, detail=f"Paper is not ready yet (status: {paper.status}).")

    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question must not be empty.")

    # Retrieve relevant chunks (CPU-bound embedding search) off the event loop.
    retrieved = await asyncio.to_thread(vector_store.search_index, paper_id, payload.question)
    excerpts = [(chunk.text, chunk.page_number) for chunk, _score in retrieved]

    try:
        result = await asyncio.to_thread(gemini_service.answer_question, payload.question, excerpts)
    except gemini_service.GeminiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    message = ChatMessage(
        paper_id=paper_id,
        question=payload.question,
        answer=result["answer"],
        page_numbers=result.get("page_numbers", []),
        citations=result.get("citations", []),
        confidence_score=result.get("confidence_score", 0.0),
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


@router.get("/{paper_id}/history", response_model=List[ChatAnswerResponse])
def get_chat_history(paper_id: str, db: Session = Depends(get_db)):
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.paper_id == paper_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )


@router.get("/history/all", response_model=List[ChatHistoryItem])
def get_all_chat_history(db: Session = Depends(get_db)):
    """All chat history across papers, for the Dashboard + 'Download Chat' bonus feature."""
    messages = db.query(ChatMessage).order_by(ChatMessage.created_at.desc()).all()
    results = []
    for m in messages:
        results.append(
            ChatHistoryItem(
                id=m.id,
                paper_id=m.paper_id,
                paper_title=m.paper.title if m.paper else None,
                question=m.question,
                answer=m.answer,
                page_numbers=m.page_numbers,
                citations=m.citations,
                confidence_score=m.confidence_score,
                created_at=m.created_at,
            )
        )
    return results
