from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class InterviewSessionCreate(BaseModel):
    user_id: UUID
    target_role: str
    company_name: Optional[str] = "General"
    difficulty: Optional[str] = "Medium"

class InterviewResponse(BaseModel):
    session_id: str
    answer: str

class InterviewFeedback(BaseModel):
    question: str
    answer: str
    rating: int  # 1-10
    feedback: str
    improved_answer: str

class InterviewTurn(BaseModel):
    id: int
    question: str
    audio_data: Optional[str] = None  # Base64 encoded audio
    previous_feedback: Optional[InterviewFeedback] = None
    is_completed: bool = False

class InterviewSession(BaseModel):
    id: str
    user_id: str
    target_role: str
    company_name: str
    created_at: datetime
    questions: List[str]  # The plan
    current_question_index: int
    feedback_history: List[InterviewFeedback] = []
    is_active: bool = True
