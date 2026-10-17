"""
Dashboard endpoint — aggregate stats for the home screen.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.chat import ChatMessage
from app.models.paper import Paper
from app.schemas.misc import DashboardStats

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardStats)
def get_dashboard(db: Session = Depends(get_db)):
    total_papers = db.query(func.count(Paper.id)).scalar() or 0
    total_pages = db.query(func.coalesce(func.sum(Paper.total_pages), 0)).scalar() or 0
    total_chat_messages = db.query(func.count(ChatMessage.id)).scalar() or 0

    recent_uploads = db.query(Paper).order_by(Paper.created_at.desc()).limit(5).all()
    favorite_papers = db.query(Paper).filter(Paper.is_favorite.is_(True)).order_by(Paper.created_at.desc()).all()

    return DashboardStats(
        total_papers=total_papers,
        total_pages=int(total_pages),
        total_chat_messages=total_chat_messages,
        recent_uploads=recent_uploads,
        favorite_papers=favorite_papers,
    )
