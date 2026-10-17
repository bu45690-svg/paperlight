"""
ChatMessage model — stores the RAG Q&A history per paper.
"""
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    paper_id: Mapped[str] = mapped_column(String, ForeignKey("papers.id"), nullable=False)

    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)

    page_numbers: Mapped[list | None] = mapped_column(JSON, nullable=True)  # list[int]
    citations: Mapped[list | None] = mapped_column(JSON, nullable=True)  # list[str] (source snippets)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)  # 0-1

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    paper = relationship("Paper", back_populates="chat_messages")
