"""
LangChain-based LLM client with context engineering.

Supports OpenAI, Anthropic, and Google with proper context management.
"""

from functools import lru_cache
from typing import Any

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.config import get_settings


def get_llm():
    """Get configured LangChain LLM based on settings."""
    settings = get_settings()
    
    if settings.llm_provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            temperature=0.7
        )
    elif settings.llm_provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            api_key=settings.anthropic_api_key,
            model=settings.anthropic_model,
            temperature=0.7
        )
    elif settings.llm_provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            api_key=settings.google_api_key,
            model=settings.google_model,
            temperature=0.7
        )
    elif settings.llm_provider == "openrouter":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            model=settings.openrouter_model,
            temperature=0.7,
            default_headers={
                "HTTP-Referer": "https://career-intelligence.app",
                "X-Title": "Career Intelligence Platform"
            }
        )
    else:
        raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")



# ─────────────────────────────────────────────────────────────────────────────
# Prompt Templates with Context Engineering
# ─────────────────────────────────────────────────────────────────────────────

PROFILE_CONTEXT_TEMPLATE = """
## User Profile Context

**Personal Information:**
- Name: {full_name}
- Target Roles: {target_roles}
- Academic Stage: {academic_stage}
- Graduation Year: {graduation_year}
- Location: {location}

**Skills ({skill_count} total):**
{skills_formatted}

**Education ({education_count} entries):**
{education_formatted}

**Experience ({experience_count} positions):**
{experience_formatted}

**Projects ({project_count} total):**
{projects_formatted}

**Intelligence Scores:**
- Engagement: {engagement_score}/100
- Learning Velocity: {learning_velocity_score}/100
- Commitment: {commitment_score}/100
- Interview Readiness: {interview_readiness_score}/100
- Professional Maturity: {professional_maturity_score}/100
- Overall Capability: {overall_capability_score}/100
- Tier: {profile_tier}
"""


def format_profile_context(context: dict[str, Any]) -> str:
    """Format user context into structured prompt context."""
    profile = context.get("profile", {}) or {}
    skills = context.get("skills", []) or []
    education = context.get("education", []) or []
    experience = context.get("experience", []) or []
    projects = context.get("projects", []) or []
    
    # Format skills
    skills_formatted = "\n".join([
        f"  - {s.get('skill_name', 'Unknown')} (Level {s.get('proficiency_level', '?')}/5, {s.get('years_of_experience', '?')} years)"
        for s in skills[:10]
    ]) or "  - No skills listed"
    
    # Format education
    education_formatted = "\n".join([
        f"  - {e.get('degree', 'Degree')} in {e.get('field_of_study', 'Field')} from {e.get('institution_name', 'Institution')}"
        for e in education[:5]
    ]) or "  - No education listed"
    
    # Format experience
    experience_formatted = "\n".join([
        f"  - {e.get('position_title', 'Position')} at {e.get('company_name', 'Company')} ({e.get('employment_type', 'Full-time')})"
        for e in experience[:5]
    ]) or "  - No experience listed"
    
    # Format projects
    projects_formatted = "\n".join([
        f"  - {p.get('project_name', 'Project')}: {(p.get('description', '')[:100] + '...' if len(p.get('description', '')) > 100 else p.get('description', 'No description'))}"
        for p in projects[:5]
    ]) or "  - No projects listed"
    
    return PROFILE_CONTEXT_TEMPLATE.format(
        full_name=profile.get("full_name", "Unknown"),
        target_roles=", ".join(profile.get("target_roles", [])) or "Not specified",
        academic_stage=profile.get("academic_stage", "Not specified"),
        graduation_year=profile.get("graduation_year", "Not specified"),
        location=f"{profile.get('city', '')}, {profile.get('country', '')}".strip(", ") or "Not specified",
        skill_count=len(skills),
        skills_formatted=skills_formatted,
        education_count=len(education),
        education_formatted=education_formatted,
        experience_count=len(experience),
        experience_formatted=experience_formatted,
        project_count=len(projects),
        projects_formatted=projects_formatted,
        engagement_score=profile.get("engagement_score", 0),
        learning_velocity_score=profile.get("learning_velocity_score", 0),
        commitment_score=profile.get("commitment_score", 0),
        interview_readiness_score=profile.get("interview_readiness_score", 0),
        professional_maturity_score=profile.get("professional_maturity_score", 0),
        overall_capability_score=profile.get("overall_capability_score", 0),
        profile_tier=profile.get("profile_tier", "N/A")
    )


# ─────────────────────────────────────────────────────────────────────────────
# Chain Builders
# ─────────────────────────────────────────────────────────────────────────────

def build_profile_analysis_chain():
    """Build chain for profile analysis with structured output."""
    llm = get_llm()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert career advisor specializing in tech careers.
Analyze the user's profile comprehensively and provide actionable feedback.
Be specific and reference actual data from their profile.
Always respond in valid JSON format."""),
        ("human", """{profile_context}

Analyze this profile and provide:
1. Overall impression (2-3 sentences)
2. Top 3 strengths based on their actual skills/experience
3. Top 3 areas for improvement
4. Profile completeness score (0-100)
5. Prioritized action items

Respond in this exact JSON format:
{{
    "overall_impression": "...",
    "strengths": ["specific strength 1", "specific strength 2", "specific strength 3"],
    "areas_for_improvement": ["area 1", "area 2", "area 3"],
    "profile_completeness_score": 75,
    "recommended_actions": [
        {{"action": "...", "priority": "high/medium/low", "impact": "why this matters"}}
    ]
}}""")
    ])
    
    return prompt | llm | JsonOutputParser()


def build_career_advice_chain():
    """Build chain for personalized career advice."""
    llm = get_llm()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert career coach with deep knowledge of tech industry.
Provide personalized, actionable advice based on the user's specific profile.
Reference their actual skills, experience, and goals in your response.
Be encouraging but realistic."""),
        ("human", """{profile_context}

User's Question: {question}

Provide personalized advice that:
1. Directly addresses their question
2. References their specific skills/experience
3. Considers their target roles
4. Includes concrete next steps""")
    ])
    
    return prompt | llm | StrOutputParser()


def build_interview_prep_chain():
    """Build chain for generating interview questions."""
    llm = get_llm()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a senior technical interviewer at a top tech company.
Generate interview questions tailored to the candidate's background and target role.
Questions should be challenging but fair given their experience level."""),
        ("human", """{profile_context}

Target Role: {target_role}

Generate tailored interview questions that:
1. Test skills they claim to have
2. Explore their project experience
3. Assess role-specific competencies

Respond in this exact JSON format:
{{
    "technical_questions": [
        {{"question": "...", "what_to_look_for": "...", "difficulty": "easy/medium/hard", "related_skill": "..."}}
    ],
    "behavioral_questions": [
        {{"question": "...", "what_to_look_for": "...", "related_experience": "..."}}
    ],
    "role_specific_questions": [
        {{"question": "...", "why_asked": "..."}}
    ],
    "preparation_tips": ["tip 1", "tip 2", "tip 3"]
}}""")
    ])
    
    return prompt | llm | JsonOutputParser()


def build_skill_gap_chain():
    """Build chain for skill gap analysis."""
    llm = get_llm()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a career development specialist with expertise in tech skill requirements.
Analyze skill gaps by comparing current skills against industry requirements for target roles.
Be specific about what's missing and how long it takes to learn."""),
        ("human", """{profile_context}

Target Role: {target_role}

Analyze the gap between their current skills and what's needed for {target_role}.

Respond in this exact JSON format:
{{
    "target_role": "{target_role}",
    "current_match_percentage": 65,
    "transferable_skills": ["skill they have that applies"],
    "missing_critical_skills": [
        {{"skill": "...", "importance": "critical/important/nice_to_have", "learning_time": "X weeks/months", "resources": ["resource 1"]}}
    ],
    "recommended_learning_path": [
        {{"step": 1, "topic": "...", "duration": "X weeks", "reason": "..."}}
    ],
    "estimated_time_to_ready": "X months",
    "quick_wins": ["something they can do this week"]
}}""")
    ])
    
    return prompt | llm | JsonOutputParser()


def build_resume_suggestions_chain():
    """Build chain for resume improvement suggestions."""
    llm = get_llm()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a professional resume writer and ATS optimization expert.
Provide specific, actionable suggestions to improve resume impact and ATS compatibility.
Reference actual content from their profile."""),
        ("human", """{profile_context}

Analyze their profile as if reviewing a resume and suggest improvements.

Respond in this exact JSON format:
{{
    "professional_summary_suggestion": "A compelling 2-3 sentence summary they should use",
    "experience_improvements": [
        {{"position": "actual position from their profile", "current_issue": "...", "improved_version": "..."}}
    ],
    "skills_to_highlight": ["skill with reason"],
    "skills_to_add": ["missing skills they should learn"],
    "ats_optimization_tips": ["specific tip 1", "specific tip 2"],
    "formatting_suggestions": ["suggestion 1"],
    "overall_resume_rating": 75,
    "top_priority_fix": "The single most important thing to change"
}}""")
    ])
    
    return prompt | llm | JsonOutputParser()


# ─────────────────────────────────────────────────────────────────────────────
# Chain Instances (cached)
# ─────────────────────────────────────────────────────────────────────────────

@lru_cache
def get_profile_analysis_chain():
    return build_profile_analysis_chain()

@lru_cache
def get_career_advice_chain():
    return build_career_advice_chain()

@lru_cache
def get_interview_prep_chain():
    return build_interview_prep_chain()

@lru_cache
def get_skill_gap_chain():
    return build_skill_gap_chain()

@lru_cache
def get_resume_suggestions_chain():
    return build_resume_suggestions_chain()
