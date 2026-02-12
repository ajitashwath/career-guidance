"""
AI API routes for LLM-powered features.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.auth import require_student, CurrentUser
from app.intelligence.ai_service import (
    analyze_profile,
    get_career_advice,
    generate_interview_questions,
    analyze_skill_gaps,
    generate_resume_suggestions,
    generate_company_specific_questions,
    generate_voice_from_text,
)
from fastapi.responses import StreamingResponse
from starlette.requests import Request

# Security Imports
from app.middleware.rate_limiting import limiter, llm_limiter
from app.security.llm_security import sanitize_llm_input

router = APIRouter()


class CareerAdviceRequest(BaseModel):
    question: str = Field(..., min_length=10, max_length=500)


class InterviewPrepRequest(BaseModel):
    target_role: str = Field(..., min_length=2, max_length=100)


class SkillGapRequest(BaseModel):
    target_role: str = Field(..., min_length=2, max_length=100)


@router.get("/profile-analysis")
@limiter.limit(llm_limiter)
async def get_profile_analysis(
    request: Request,
    user: Annotated[CurrentUser, Depends(require_student)]
):
    """Get AI analysis of your profile with actionable feedback."""
    try:
        return await analyze_profile(user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI analysis failed: {str(e)}"
        )


@router.post("/career-advice")
@limiter.limit(llm_limiter)
async def get_ai_career_advice(
    request: Request,
    body: CareerAdviceRequest,
    user: Annotated[CurrentUser, Depends(require_student)]
):
    """Get personalized career advice based on your question."""
    try:
        # Sanitize input
        safe_question = sanitize_llm_input(body.question)
        
        advice = await get_career_advice(user.id, safe_question)
        return {"question": body.question, "advice": advice}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI advice failed: {str(e)}"
        )


@router.post("/interview-prep")
@limiter.limit(llm_limiter)
async def get_interview_prep(
    request: Request,
    body: InterviewPrepRequest,
    user: Annotated[CurrentUser, Depends(require_student)]
):
    """Generate tailored interview questions for a target role."""
    try:
        safe_role = sanitize_llm_input(body.target_role)
        return await generate_interview_questions(user.id, safe_role)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Interview prep failed: {str(e)}"
        )


@router.post("/skill-gaps")
@limiter.limit(llm_limiter)
async def get_skill_gap_analysis(
    request: Request,
    body: SkillGapRequest,
    user: Annotated[CurrentUser, Depends(require_student)]
):
    """Analyze skill gaps for a target role."""
    try:
        safe_role = sanitize_llm_input(body.target_role)
        return await analyze_skill_gaps(user.id, safe_role)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Skill gap analysis failed: {str(e)}"
        )


@router.get("/resume-suggestions")
@limiter.limit(llm_limiter)
async def get_resume_improvement_suggestions(
    request: Request,
    user: Annotated[CurrentUser, Depends(require_student)]
):
    """Get AI-powered resume improvement suggestions."""
    try:
        return await generate_resume_suggestions(user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resume suggestions failed: {str(e)}"
        )


class CompanyInterviewRequest(BaseModel):
    target_role: str = Field(..., min_length=2, max_length=100)
    companies: list[str] = Field(
        default=["Google", "Amazon", "Microsoft", "Meta"],
        min_length=1,
        max_length=5
    )


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)
    voice_id: str = Field(default="JBFqnCBsd6RMkjVDRZzb")


@router.post("/interview-prep/companies")
@limiter.limit(llm_limiter)
async def get_company_interview_prep(
    request: Request,
    body: CompanyInterviewRequest,
    user: Annotated[CurrentUser, Depends(require_student)]
):
    """Generate interview questions tailored to specific companies."""
    try:
        safe_role = sanitize_llm_input(body.target_role)
        # Note: companies list is enum-like/controlled by pydantic, less risk but good to be safe if they were free-text
        
        return await generate_company_specific_questions(
            user.id,
            safe_role,
            body.companies
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Company interview prep failed: {str(e)}"
        )


@router.post("/audio/tts")
@limiter.limit(llm_limiter)
async def generate_speech(
    request: Request,
    body: TTSRequest,
    user: Annotated[CurrentUser, Depends(require_student)]
):
    """Generate audio from text using ElevenLabs."""
    try:
        safe_text = sanitize_llm_input(body.text)
        audio_stream = generate_voice_from_text(safe_text, body.voice_id)
        return StreamingResponse(audio_stream, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"TTS generation failed: {str(e)}"
        )
