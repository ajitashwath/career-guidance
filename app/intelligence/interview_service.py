"""
Service for managing Voice Interview sessions.
"""

import uuid
from datetime import datetime
from uuid import UUID
from typing import Optional, Dict

from app.models.interview import InterviewSession, InterviewTurn, InterviewFeedback
from app.intelligence import ai_service
from app.core import voice


# In-memory storage for active sessions (for MVP/Latency)
# In production, this should be Redis or Database
active_sessions: Dict[str, InterviewSession] = {}


async def create_session(user_id: str, target_role: str, company: str, difficulty: str) -> InterviewSession:
    """Create a new interview session and generate the first question."""
    session_id = str(uuid.uuid4())
    
    # 1. Generate Questions Plan (The KB)
    questions = []
    
    # Use existing company specific chain or general interview prep
    if company and company.lower() != "general":
        # Returns {company_name: [questions]}
        questions_data = await ai_service.generate_company_specific_questions(
            UUID(user_id), target_role, [company]
        )
        if questions_data and company in questions_data:
            questions = [q['question'] for q in questions_data[company]]
    
    if not questions:
        # Fallback or General interview prep
        prep_data = await ai_service.generate_interview_questions(UUID(user_id), target_role)
        # Combine technical and behavioral
        tech = [q['question'] for q in prep_data.get('technical_questions', [])]
        behavioral = [q['question'] for q in prep_data.get('behavioral_questions', [])]
        questions = (tech + behavioral)[:5] # Mix up to 5 questions
    
    # Create Session
    session = InterviewSession(
        id=session_id,
        user_id=str(user_id),
        target_role=target_role,
        company_name=company or "General",
        created_at=datetime.utcnow(),
        questions=questions,
        current_question_index=0,
        feedback_history=[],
        is_active=True
    )
    
    active_sessions[session_id] = session
    return session


async def get_current_turn(session_id: str) -> Optional[InterviewTurn]:
    """Get the current turn (question + audio)."""
    session = active_sessions.get(session_id)
    if not session or not session.is_active:
        return None
    
    if session.current_question_index >= len(session.questions):
        session.is_active = False
        return None
        
    current_q = session.questions[session.current_question_index]
    
    # Generate Audio (Latency critical part)
    # In a real system, we'd cache this or stream it.
    # For now, we generate generic audio.
    # We return the generator/iterator directly? No, we need to send it to client.
    # We will return None for audio_data here and handle streaming in the route
    
    return InterviewTurn(
        id=session.current_question_index,
        question=current_q,
        is_completed=False
    )

async def process_response(session_id: str, answer: str) -> Dict:
    """Process user answer, evaluate, and move to next."""
    session = active_sessions.get(session_id)
    if not session:
        raise ValueError("Session not found")
        
    # Get current question for evaluation context
    current_q = session.questions[session.current_question_index]
    
    # Evaluate (Async)
    evaluation = await ai_service.evaluate_answer(
        UUID(session.user_id),
        current_q,
        answer,
        session.target_role
    )
    
    # Store feedback
    feedback = InterviewFeedback(
        question=current_q,
        answer=answer,
        rating=evaluation.get('rating', 0),
        feedback=evaluation.get('feedback', ''),
        improved_answer=evaluation.get('improved_answer', '')
    )
    session.feedback_history.append(feedback)
    
    # Move to next question
    session.current_question_index += 1
    
    # Check if sessions ends
    is_finished = session.current_question_index >= len(session.questions)
    if is_finished:
        session.is_active = False
        
    return {
        "feedback": feedback,
        "is_finished": is_finished,
        "next_question_index": session.current_question_index
    }

async def get_session_feedback(session_id: str) -> Dict:
    session = active_sessions.get(session_id)
    if not session:
        return {}
    return {
        "history": session.feedback_history,
        "total_questions": len(session.questions)
    }
