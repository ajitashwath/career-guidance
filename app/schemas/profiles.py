"""
Pydantic schemas for user profiles and related entities.

Schemas are organized as:
- Create: Input for creating new entries
- Update: Partial input for updates
- Response: Output returned to clients
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr, HttpUrl


# User Profile Schemas
class UserProfileBase(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=20)
    avatar_url: Optional[str] = None
    
    # Academic
    university_id: Optional[UUID] = None
    student_id: Optional[str] = Field(default=None, max_length=50)
    major: str = Field(..., min_length=1, max_length=100)
    minor: Optional[str] = Field(default=None, max_length=100)
    graduation_year: int = Field(..., ge=2000, le=2050)
    current_year: Optional[int] = Field(default=None, ge=1, le=8)
    gpa: Optional[Decimal] = Field(default=None, ge=0, le=4.0)
    
    # Location
    city: Optional[str] = Field(default=None, max_length=100)
    state: Optional[str] = Field(default=None, max_length=100)
    country: str = Field(..., max_length=100)
    
    # Career
    current_skills: list[str] = Field(default_factory=list)
    target_roles: list[str] = Field(default_factory=list)
    target_industries: list[str] = Field(default_factory=list)
    years_of_experience: int = Field(default=0, ge=0)
    
    # Job Preferences
    preferred_job_types: list[str] = Field(default_factory=list)
    preferred_locations: list[str] = Field(default_factory=list)
    willing_to_relocate: bool = False
    salary_expectation_min: Optional[int] = Field(default=None, ge=0)
    salary_expectation_max: Optional[int] = Field(default=None, ge=0)
    
    # Links
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    resume_url: Optional[str] = None
    
    bio: Optional[str] = Field(default=None, max_length=2000)


class UserProfileCreate(UserProfileBase):
    pass

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=20)
    avatar_url: Optional[str] = None
    
    university_id: Optional[UUID] = None
    student_id: Optional[str] = Field(default=None, max_length=50)
    major: Optional[str] = Field(default=None, min_length=1, max_length=100)
    minor: Optional[str] = None
    graduation_year: Optional[int] = Field(default=None, ge=2000, le=2050)
    current_year: Optional[int] = Field(default=None, ge=1, le=8)
    gpa: Optional[Decimal] = Field(default=None, ge=0, le=4.0)
    
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    
    current_skills: Optional[list[str]] = None
    target_roles: Optional[list[str]] = None
    target_industries: Optional[list[str]] = None
    years_of_experience: Optional[int] = Field(default=None, ge=0)
    
    preferred_job_types: Optional[list[str]] = None
    preferred_locations: Optional[list[str]] = None
    willing_to_relocate: Optional[bool] = None
    salary_expectation_min: Optional[int] = Field(default=None, ge=0)
    salary_expectation_max: Optional[int] = Field(default=None, ge=0)
    
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    resume_url: Optional[str] = None
    bio: Optional[str] = None
    
    onboarding_completed: Optional[bool] = None


class UserProfileResponse(UserProfileBase):
    id: UUID
    onboarding_completed: bool
    last_active_at: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RecruiterProfileView(BaseModel):
    """
    Excludes:
    - Email, phone (PII)
    - Salary expectations
    - Resume URL (require explicit share)
    - Internal tier information
    
    Includes intelligence scores for filtering.
    """
    id: UUID
    full_name: str
    avatar_url: Optional[str]
    
    # Academic
    university_id: Optional[UUID]
    major: str
    minor: Optional[str]
    graduation_year: int
    current_year: Optional[int]
    gpa: Optional[Decimal]
    
    # Location
    city: Optional[str]
    state: Optional[str]
    country: str
    
    # Career
    current_skills: list[str]
    target_roles: list[str]
    target_industries: list[str]
    years_of_experience: int
    
    # Preferences (public)
    preferred_job_types: list[str]
    preferred_locations: list[str]
    willing_to_relocate: bool
    
    # Links (public)
    linkedin_url: Optional[str]
    github_url: Optional[str]
    portfolio_url: Optional[str]
    
    bio: Optional[str]
    
    # Intelligence scores (visible to recruiters)
    engagement_score: int
    learning_velocity_score: int
    commitment_score: int
    interview_readiness_score: int
    professional_maturity_score: int
    overall_capability_score: int
    
    last_active_at: datetime
    
    class Config:
        from_attributes = True


# Skill Schemas
class UserSkillCreate(BaseModel):
    skill_name: str = Field(..., min_length=1, max_length=100)
    proficiency_level: int = Field(..., ge=1, le=5, description="1=Beginner, 5=Expert")
    years_of_experience: Optional[Decimal] = Field(default=None, ge=0, le=50)
    certificate_url: Optional[str] = None


class UserSkillUpdate(BaseModel):
    proficiency_level: Optional[int] = Field(default=None, ge=1, le=5)
    years_of_experience: Optional[Decimal] = Field(default=None, ge=0, le=50)
    certificate_url: Optional[str] = None


class UserSkillResponse(BaseModel):
    id: UUID
    user_id: UUID
    skill_name: str
    proficiency_level: int
    years_of_experience: Optional[Decimal]
    verified: bool
    verification_source: Optional[str]
    certificate_url: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Education Schemas
class UserEducationCreate(BaseModel):
    institution_name: str = Field(..., min_length=1, max_length=255)
    degree: str = Field(..., min_length=1, max_length=100)
    field_of_study: str = Field(..., min_length=1, max_length=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: bool = False
    gpa: Optional[Decimal] = Field(default=None, ge=0, le=4.0)
    achievements: list[str] = Field(default_factory=list)
    relevant_coursework: list[str] = Field(default_factory=list)


class UserEducationUpdate(BaseModel):
    institution_name: Optional[str] = Field(default=None, max_length=255)
    degree: Optional[str] = Field(default=None, max_length=100)
    field_of_study: Optional[str] = Field(default=None, max_length=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: Optional[bool] = None
    gpa: Optional[Decimal] = Field(default=None, ge=0, le=4.0)
    achievements: Optional[list[str]] = None
    relevant_coursework: Optional[list[str]] = None


class UserEducationResponse(BaseModel):
    id: UUID
    user_id: UUID
    institution_name: str
    degree: str
    field_of_study: str
    start_date: Optional[date]
    end_date: Optional[date]
    is_current: bool
    gpa: Optional[Decimal]
    achievements: list[str]
    relevant_coursework: list[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Experience Schemas
class UserExperienceCreate(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=255)
    position_title: str = Field(..., min_length=1, max_length=100)
    employment_type: Optional[str] = Field(default=None, max_length=50)
    location: Optional[str] = Field(default=None, max_length=100)
    is_remote: bool = False
    start_date: date
    end_date: Optional[date] = None
    is_current: bool = False
    description: Optional[str] = Field(default=None, max_length=2000)
    achievements: list[str] = Field(default_factory=list)
    skills_used: list[str] = Field(default_factory=list)


class UserExperienceUpdate(BaseModel):
    company_name: Optional[str] = Field(default=None, max_length=255)
    position_title: Optional[str] = Field(default=None, max_length=100)
    employment_type: Optional[str] = None
    location: Optional[str] = None
    is_remote: Optional[bool] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: Optional[bool] = None
    description: Optional[str] = None
    achievements: Optional[list[str]] = None
    skills_used: Optional[list[str]] = None


class UserExperienceResponse(BaseModel):
    id: UUID
    user_id: UUID
    company_name: str
    position_title: str
    employment_type: Optional[str]
    location: Optional[str]
    is_remote: bool
    start_date: date
    end_date: Optional[date]
    is_current: bool
    description: Optional[str]
    achievements: list[str]
    skills_used: list[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Project Schemas
class UserProjectCreate(BaseModel):
    project_name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1, max_length=2000)
    role: Optional[str] = Field(default=None, max_length=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_ongoing: bool = False
    technologies_used: list[str] = Field(default_factory=list)
    github_url: Optional[str] = None
    live_demo_url: Optional[str] = None
    achievements: list[str] = Field(default_factory=list)


class UserProjectUpdate(BaseModel):
    project_name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    role: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_ongoing: Optional[bool] = None
    technologies_used: Optional[list[str]] = None
    github_url: Optional[str] = None
    live_demo_url: Optional[str] = None
    achievements: Optional[list[str]] = None


class UserProjectResponse(BaseModel):
    id: UUID
    user_id: UUID
    project_name: str
    description: str
    role: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    is_ongoing: bool
    technologies_used: list[str]
    github_url: Optional[str]
    live_demo_url: Optional[str]
    achievements: list[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Certification Schemas
class UserCertificationCreate(BaseModel):
    certification_name: str = Field(..., min_length=1, max_length=255)
    issuing_organization: str = Field(..., min_length=1, max_length=255)
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    credential_id: Optional[str] = Field(default=None, max_length=100)
    credential_url: Optional[str] = None

class UserCertificationUpdate(BaseModel):
    certification_name: Optional[str] = Field(default=None, max_length=255)
    issuing_organization: Optional[str] = Field(default=None, max_length=255)
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    credential_id: Optional[str] = None
    credential_url: Optional[str] = None

class UserCertificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    certification_name: str
    issuing_organization: str
    issue_date: Optional[date]
    expiry_date: Optional[date]
    credential_id: Optional[str]
    credential_url: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
