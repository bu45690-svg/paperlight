"""
Paper model — represents an uploaded research paper and all AI-derived analysis.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, Integer, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class PaperStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    EXTRACTING = "extracting"
    ANALYZING = "analyzing"
    INDEXING = "indexing"
    READY = "ready"
    FAILED = "failed"


class Paper(Base):
    __tablename__ = "papers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    original_filename: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0)

    status: Mapped[PaperStatus] = mapped_column(Enum(PaperStatus), default=PaperStatus.UPLOADED)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    total_pages: Mapped[int] = mapped_column(Integer, default=0)
    raw_text_char_count: Mapped[int] = mapped_column(Integer, default=0)

    # --- Analysis fields (populated by Gemini) ---
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    executive_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    abstract_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_contributions: Mapped[str | None] = mapped_column(JSON, nullable=True)  # list[str]
    methodology: Mapped[str | None] = mapped_column(Text, nullable=True)
    results: Mapped[str | None] = mapped_column(Text, nullable=True)
    limitations: Mapped[str | None] = mapped_column(Text, nullable=True)
    future_work: Mapped[str | None] = mapped_column(Text, nullable=True)
    keywords: Mapped[str | None] = mapped_column(JSON, nullable=True)  # list[str]
    important_equations: Mapped[str | None] = mapped_column(JSON, nullable=True)  # list[str]
    important_figures: Mapped[str | None] = mapped_column(JSON, nullable=True)  # list[str] titles
    references_count: Mapped[int] = mapped_column(Integer, default=0)

    # --- Vector index reference ---
    faiss_index_path: Mapped[str | None] = mapped_column(String, nullable=True)

    # --- Bonus features ---
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    reading_progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    last_opened_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    chat_messages = relationship("ChatMessage", back_populates="paper", cascade="all, delete-orphan")
    study_notes = relationship("StudyNote", back_populates="paper", cascade="all, delete-orphan")
