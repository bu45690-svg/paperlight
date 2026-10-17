"""
StudyNote model — stores generated exam notes, flashcards, MCQs, etc. per paper.
"""
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class StudyNote(Base):
    __tablename__ = "study_notes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    paper_id: Mapped[str] = mapped_column(String, ForeignKey("papers.id"), nullable=False)

    exam_notes: Mapped[str | None] = mapped_column(JSON, nullable=True)  # list[str]
    flashcards: Mapped[str | None] = mapped_column(JSON, nullable=True)  # list[{q,a}]
    bullet_notes: Mapped[str | None] = mapped_column(JSON, nullable=True)  # list[str]
    interview_questions: Mapped[str | None] = mapped_column(JSON, nullable=True)  # list[str]
    viva_questions: Mapped[str | None] = mapped_column(JSON, nullable=True)  # list[str]
    mcqs: Mapped[str | None] = mapped_column(JSON, nullable=True)  # list[{q,options,answer}]

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    paper = relationship("Paper", back_populates="study_notes")
