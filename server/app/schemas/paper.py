"""
Pydantic schemas for Paper request/response bodies.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from app.models.paper import PaperStatus


class PaperUploadResponse(BaseModel):
    id: str
    filename: str
    status: PaperStatus
    message: str


class PaperSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    original_filename: str
    title: Optional[str] = None
    status: PaperStatus
    total_pages: int
    is_favorite: bool
    reading_progress_percent: int
    created_at: datetime


class PaperAnalysis(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    original_filename: str
    title: Optional[str] = None
    status: PaperStatus
    error_message: Optional[str] = None
    total_pages: int
    executive_summary: Optional[str] = None
    abstract_summary: Optional[str] = None
    key_contributions: Optional[List[str]] = None
    methodology: Optional[str] = None
    results: Optional[str] = None
    limitations: Optional[str] = None
    future_work: Optional[str] = None
    keywords: Optional[List[str]] = None
    important_equations: Optional[List[str]] = None
    important_figures: Optional[List[str]] = None
    references_count: int
    is_favorite: bool
    reading_progress_percent: int
    created_at: datetime
    updated_at: datetime


class PaperStatusResponse(BaseModel):
    id: str
    status: PaperStatus
    error_message: Optional[str] = None


class ReadingProgressUpdate(BaseModel):
    reading_progress_percent: int


class FavoriteToggle(BaseModel):
    is_favorite: bool
