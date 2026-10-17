from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class ChatQuestionRequest(BaseModel):
    question: str


class ChatAnswerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    question: str
    answer: str
    page_numbers: Optional[List[int]] = None
    citations: Optional[List[str]] = None
    confidence_score: float
    created_at: datetime


class ChatHistoryItem(ChatAnswerResponse):
    paper_id: str
    paper_title: Optional[str] = None
