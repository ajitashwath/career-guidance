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
)

router = APIRouter()


class CareerAdviceRequest(BaseModel):
    question: str = Field(..., min_length=10, max_length=500)


class InterviewPrepRequest(BaseModel):
    target_role: str = Field(..., min_length=2, max_length=100)


class SkillGapRequest(BaseModel):
    target_role: str = Field(..., min_length=2, max_length=100)


@router.get("/profile-analysis")
async def get_profile_analysis(
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
async def get_ai_career_advice(
    request: CareerAdviceRequest,
    user: Annotated[CurrentUser, Depends(require_student)]
):
    """Get personalized career advice based on your question."""
    try:
        advice = await get_career_advice(user.id, request.question)
        return {"question": request.question, "advice": advice}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI advice failed: {str(e)}"
        )


@router.post("/interview-prep")
async def get_interview_prep(
    request: InterviewPrepRequest,
    user: Annotated[CurrentUser, Depends(require_student)]
):
    """Generate tailored interview questions for a target role."""
    try:
        return await generate_interview_questions(user.id, request.target_role)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Interview prep failed: {str(e)}"
        )


@router.post("/skill-gaps")
async def get_skill_gap_analysis(
    request: SkillGapRequest,
    user: Annotated[CurrentUser, Depends(require_student)]
):
    """Analyze skill gaps for a target role."""
    try:
        return await analyze_skill_gaps(user.id, request.target_role)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Skill gap analysis failed: {str(e)}"
        )


@router.get("/resume-suggestions")
async def get_resume_improvement_suggestions(
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
