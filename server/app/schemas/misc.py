from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.paper import PaperSummary


class SearchQuery(BaseModel):
    query: str
    top_k: int = 5


class SearchResultItem(BaseModel):
    paper_id: str
    paper_title: Optional[str]
    page_number: Optional[int]
    snippet: str
    score: float


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResultItem]


class DashboardStats(BaseModel):
    total_papers: int
    total_pages: int
    total_chat_messages: int
    recent_uploads: List[PaperSummary]
    favorite_papers: List[PaperSummary]
