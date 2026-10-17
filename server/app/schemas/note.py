from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class Flashcard(BaseModel):
    question: str
    answer: str


class MCQ(BaseModel):
    question: str
    options: List[str]
    correct_answer_index: int
    explanation: Optional[str] = None


class StudyNotesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    paper_id: str
    exam_notes: Optional[List[str]] = None
    flashcards: Optional[List[Flashcard]] = None
    bullet_notes: Optional[List[str]] = None
    interview_questions: Optional[List[str]] = None
    viva_questions: Optional[List[str]] = None
    mcqs: Optional[List[MCQ]] = None
