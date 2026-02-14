"""
AI service for career intelligence features using LangChain.

Uses context engineering for curated, personalized AI responses.
"""

from uuid import UUID
from typing import Any

from app.core.llm import (
    format_profile_context,
    get_profile_analysis_chain,
    get_career_advice_chain,
    get_interview_prep_chain,
    get_skill_gap_chain,
    get_resume_suggestions_chain,
    get_company_questions_chain,
    get_answer_evaluation_chain,
)
from app.core import voice
from app.db.supabase import fetch_one, fetch_many
from app.db.queries import (
    TABLE_USER_PROFILES,
    TABLE_USER_SKILLS,
    TABLE_USER_EDUCATION,
    TABLE_USER_EXPERIENCE,
    TABLE_USER_PROJECTS,
)


async def get_user_context(user_id: UUID) -> dict[str, Any]:
    """Build full user context for AI prompts."""
    profile = await fetch_one(TABLE_USER_PROFILES, str(user_id))
    skills = await fetch_many(TABLE_USER_SKILLS, {"user_id": str(user_id)})
    education = await fetch_many(TABLE_USER_EDUCATION, {"user_id": str(user_id)})
    experience = await fetch_many(TABLE_USER_EXPERIENCE, {"user_id": str(user_id)})
    projects = await fetch_many(TABLE_USER_PROJECTS, {"user_id": str(user_id)})
    
    return {
        "profile": profile,
        "skills": skills,
        "education": education,
        "experience": experience,
        "projects": projects
    }


async def analyze_profile(user_id: UUID) -> dict:
    """Analyze user profile with LangChain context engineering."""
    context = await get_user_context(user_id)
    profile_context = format_profile_context(context)
    
    chain = get_profile_analysis_chain()
    result = await chain.ainvoke({"profile_context": profile_context})
    
    return result


async def get_career_advice(user_id: UUID, question: str) -> str:
    """Get personalized career advice with full profile context."""
    context = await get_user_context(user_id)
    profile_context = format_profile_context(context)
    
    chain = get_career_advice_chain()
    result = await chain.ainvoke({
        "profile_context": profile_context,
        "question": question
    })
    
    return result


async def generate_interview_questions(user_id: UUID, target_role: str) -> dict:
    """Generate tailored interview questions using profile context."""
    context = await get_user_context(user_id)
    profile_context = format_profile_context(context)
    
    chain = get_interview_prep_chain()
    result = await chain.ainvoke({
        "profile_context": profile_context,
        "target_role": target_role
    })
    
    return result


async def analyze_skill_gaps(user_id: UUID, target_role: str) -> dict:
    """Analyze skill gaps with context-aware recommendations."""
    context = await get_user_context(user_id)
    profile_context = format_profile_context(context)
    
    chain = get_skill_gap_chain()
    result = await chain.ainvoke({
        "profile_context": profile_context,
        "target_role": target_role
    })
    
    return result


async def generate_resume_suggestions(user_id: UUID) -> dict:
    """Generate resume improvements based on full profile context."""
    context = await get_user_context(user_id)
    profile_context = format_profile_context(context)
    
    chain = get_resume_suggestions_chain()
    result = await chain.ainvoke({"profile_context": profile_context})
    
    return result


async def generate_company_specific_questions(
    user_id: UUID,
    target_role: str,
    companies: list[str]
) -> dict:
    """Generate interview questions for specific companies."""
    context = await get_user_context(user_id)
    profile_context = format_profile_context(context)
    
    chain = get_company_questions_chain()
    
    results = {}
    for company in companies:
        result = await chain.ainvoke({
            "profile_context": profile_context,
            "company_name": company,
            "target_role": target_role
        })
        results[company] = result.get("questions", [])
        
    return results


def generate_voice_from_text(text: str, voice_id: str = "JBFqnCBsd6RMkjVDRZzb"):
    """Generate audio stream from text."""
    return voice.generate_audio(text, voice_id)
