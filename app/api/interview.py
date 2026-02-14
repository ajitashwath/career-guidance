"""
API endpoints for Voice Interview.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Optional
import base64

from app.models.interview import (
    InterviewSessionCreate,
    InterviewResponse,
    InterviewSession,
    InterviewTurn,
    InterviewFeedback
)
from app.intelligence import interview_service
from app.core.voice import generate_audio

router = APIRouter()


@router.post("/start", response_model=InterviewSession)
async def start_interview(session_data: InterviewSessionCreate):
    """Start a new voice interview session."""
    try:
        session = await interview_service.create_session(
            session_data.user_id,
            session_data.target_role,
            session_data.company_name,
            session_data.difficulty
        )
        return session
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/next", response_model=InterviewTurn)
async def get_next_question(session_id: str):
    """Get the next question with audio."""
    turn = await interview_service.get_current_turn(session_id)
    if not turn:
        raise HTTPException(status_code=404, detail="No active question or session finished.")
    
    # Generate Audio
    try:
        audio_stream = generate_audio(turn.question)
        # Convert stream to bytes then base64
        audio_bytes = b"".join(audio_stream)
        turn.audio_data = base64.b64encode(audio_bytes).decode('utf-8')
    except Exception as e:
        print(f"Voice generation failed: {e}")
        # Continue without audio if voice fails
        pass

    return turn


@router.post("/response", response_model=dict)
async def submit_response(response_data: InterviewResponse):
    """Submit user response and get evaluation."""
    try:
        result = await interview_service.process_response(
            response_data.session_id,
            response_data.answer
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/feedback", response_model=dict)
async def get_feedback(session_id: str):
    """Get full session feedback."""
    return await interview_service.get_session_feedback(session_id)
