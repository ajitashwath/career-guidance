"""
SQL query constants for database operations.

All queries are parameterized to prevent SQL injection.
Organized by domain: profiles, skills, events, intelligence.
"""

# ─────────────────────────────────────────────────────────────────────────────
# Table Names
# ─────────────────────────────────────────────────────────────────────────────

TABLE_USER_PROFILES = "user_profiles"
TABLE_USER_SKILLS = "user_skills"
TABLE_USER_EDUCATION = "user_education"
TABLE_USER_EXPERIENCE = "user_experience"
TABLE_USER_PROJECTS = "user_projects"
TABLE_USER_CERTIFICATIONS = "user_certifications"
TABLE_USER_EVENTS = "user_events"
TABLE_USER_INTELLIGENCE_SNAPSHOTS = "user_intelligence_snapshots"
TABLE_UNIVERSITIES = "universities"


# ─────────────────────────────────────────────────────────────────────────────
# Profile Columns (for responses - excludes sensitive internal fields)
# ─────────────────────────────────────────────────────────────────────────────

# Student self-view (includes everything except internal scores)
STUDENT_PROFILE_COLUMNS = """
    id,
    full_name,
    email,
    phone,
    avatar_url,
    university_id,
    student_id,
    major,
    minor,
    graduation_year,
    current_year,
    gpa,
    city,
    state,
    country,
    current_skills,
    target_roles,
    target_industries,
    years_of_experience,
    preferred_job_types,
    preferred_locations,
    willing_to_relocate,
    salary_expectation_min,
    salary_expectation_max,
    linkedin_url,
    github_url,
    portfolio_url,
    resume_url,
    bio,
    onboarding_completed,
    last_active_at,
    created_at,
    updated_at
"""

# Recruiter view (public fields only - no tier/internal scores visible)
RECRUITER_PROFILE_COLUMNS = """
    id,
    full_name,
    avatar_url,
    university_id,
    major,
    minor,
    graduation_year,
    current_year,
    gpa,
    city,
    state,
    country,
    current_skills,
    target_roles,
    target_industries,
    years_of_experience,
    preferred_job_types,
    preferred_locations,
    willing_to_relocate,
    linkedin_url,
    github_url,
    portfolio_url,
    bio,
    engagement_score,
    learning_velocity_score,
    commitment_score,
    interview_readiness_score,
    professional_maturity_score,
    overall_capability_score,
    last_active_at
"""

# Admin view (all fields including internal)
ADMIN_PROFILE_COLUMNS = "*"


# ─────────────────────────────────────────────────────────────────────────────
# Skill Columns
# ─────────────────────────────────────────────────────────────────────────────

SKILL_COLUMNS = """
    id,
    user_id,
    skill_name,
    proficiency_level,
    years_of_experience,
    verified,
    verification_source,
    certificate_url,
    created_at,
    updated_at
"""


# ─────────────────────────────────────────────────────────────────────────────
# Education Columns
# ─────────────────────────────────────────────────────────────────────────────

EDUCATION_COLUMNS = """
    id,
    user_id,
    institution_name,
    degree,
    field_of_study,
    start_date,
    end_date,
    is_current,
    gpa,
    achievements,
    relevant_coursework,
    created_at
"""


# ─────────────────────────────────────────────────────────────────────────────
# Experience Columns
# ─────────────────────────────────────────────────────────────────────────────

EXPERIENCE_COLUMNS = """
    id,
    user_id,
    company_name,
    position_title,
    employment_type,
    location,
    is_remote,
    start_date,
    end_date,
    is_current,
    description,
    achievements,
    skills_used,
    created_at
"""


# ─────────────────────────────────────────────────────────────────────────────
# Project Columns
# ─────────────────────────────────────────────────────────────────────────────

PROJECT_COLUMNS = """
    id,
    user_id,
    project_name,
    description,
    role,
    start_date,
    end_date,
    is_ongoing,
    technologies_used,
    github_url,
    live_demo_url,
    achievements,
    created_at
"""


# ─────────────────────────────────────────────────────────────────────────────
# Certification Columns
# ─────────────────────────────────────────────────────────────────────────────

CERTIFICATION_COLUMNS = """
    id,
    user_id,
    certification_name,
    issuing_organization,
    issue_date,
    expiry_date,
    credential_id,
    credential_url,
    created_at
"""


# ─────────────────────────────────────────────────────────────────────────────
# Event Columns
# ─────────────────────────────────────────────────────────────────────────────

EVENT_COLUMNS = """
    id,
    user_id,
    event_type,
    event_payload,
    created_at
"""


# ─────────────────────────────────────────────────────────────────────────────
# Intelligence Snapshot Columns
# ─────────────────────────────────────────────────────────────────────────────

SNAPSHOT_COLUMNS = """
    id,
    user_id,
    engagement_score,
    learning_velocity_score,
    commitment_score,
    interview_readiness_score,
    professional_maturity_score,
    overall_capability_score,
    profile_tier,
    scoring_version,
    confidence_level,
    computed_at
"""
