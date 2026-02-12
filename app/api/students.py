"""
Student API routes.

Students can:
- View and update their own profile
- Manage skills, education, experience, projects, certifications

All endpoints enforce student-only access through JWT authentication.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from starlette.requests import Request

from app.core.auth import require_student, CurrentUser
from app.middleware.rate_limiting import limiter, standard_limiter, write_limiter
from app.db.supabase import (
    get_supabase_client,
    fetch_one,
    fetch_many,
    insert_row,
    update_row,
    delete_row,
)
from app.db.queries import (
    TABLE_USER_PROFILES,
    TABLE_USER_SKILLS,
    TABLE_USER_EDUCATION,
    TABLE_USER_EXPERIENCE,
    TABLE_USER_PROJECTS,
    TABLE_USER_CERTIFICATIONS,
    STUDENT_PROFILE_COLUMNS,
    SKILL_COLUMNS,
    EDUCATION_COLUMNS,
    EXPERIENCE_COLUMNS,
    PROJECT_COLUMNS,
    CERTIFICATION_COLUMNS,
)
from app.schemas.profiles import (
    UserProfileResponse,
    UserProfileUpdate,
    UserSkillCreate,
    UserSkillUpdate,
    UserSkillResponse,
    UserEducationCreate,
    UserEducationUpdate,
    UserEducationResponse,
    UserExperienceCreate,
    UserExperienceUpdate,
    UserExperienceResponse,
    UserProjectCreate,
    UserProjectUpdate,
    UserProjectResponse,
    UserCertificationCreate,
    UserCertificationUpdate,
    UserCertificationResponse,
)

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Profile Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/me", response_model=UserProfileResponse)
@limiter.limit(standard_limiter)
async def get_my_profile(
    request: Request,
    user: Annotated[CurrentUser, Depends(require_student)]
):
    """Get the current student's profile."""
    profile = await fetch_one(
        TABLE_USER_PROFILES,
        str(user.id),
        columns=STUDENT_PROFILE_COLUMNS.replace("\n", "").replace(" ", "")
    )
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found. Please complete onboarding."
        )
    
    return profile


@router.patch("/me", response_model=UserProfileResponse)
@limiter.limit(write_limiter)
async def update_my_profile(
    request: Request,
    update_data: UserProfileUpdate,
    user: Annotated[CurrentUser, Depends(require_student)]
):
    """Update the current student's profile."""
    # Filter out None values
    update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)
    
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    updated = await update_row(TABLE_USER_PROFILES, str(user.id), update_dict)
    return updated


# ─────────────────────────────────────────────────────────────────────────────
# Skills Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/me/skills", response_model=list[UserSkillResponse])
@limiter.limit(standard_limiter)
async def get_my_skills(
    request: Request,
    user: Annotated[CurrentUser, Depends(require_student)]
):
    """Get all skills for the current student."""
    skills = await fetch_many(
        TABLE_USER_SKILLS,
        filters={"user_id": str(user.id)},
        columns=SKILL_COLUMNS.replace("\n", "").replace(" ", ""),
        order_by="created_at",
        order_desc=True
    )
    return skills


@router.post("/me/skills", response_model=UserSkillResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(write_limiter)
async def add_skill(
    request: Request,
    skill: UserSkillCreate,
    user: Annotated[CurrentUser, Depends(require_student)]
):
    """Add a new skill to the current student's profile."""
    skill_data = skill.model_dump()
    skill_data["user_id"] = str(user.id)
    
    created = await insert_row(TABLE_USER_SKILLS, skill_data)
    return created


@router.patch("/me/skills/{skill_id}", response_model=UserSkillResponse)
@limiter.limit(write_limiter)
async def update_skill(
    request: Request,
    skill_id: UUID,
    update_data: UserSkillUpdate,
    user: Annotated[CurrentUser, Depends(require_student)]
):
    """Update a specific skill."""
    # Verify ownership
    existing = await fetch_one(TABLE_USER_SKILLS, str(skill_id))
    if not existing or existing.get("user_id") != str(user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )
    
    update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    updated = await update_row(TABLE_USER_SKILLS, str(skill_id), update_dict)
    return updated


@router.delete("/me/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(write_limiter)
async def delete_skill(
    request: Request,
    skill_id: UUID,
    user: Annotated[CurrentUser, Depends(require_student)]
):
    """Delete a specific skill."""
    existing = await fetch_one(TABLE_USER_SKILLS, str(skill_id))
    if not existing or existing.get("user_id") != str(user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )
    
    await delete_row(TABLE_USER_SKILLS, str(skill_id))


# ─────────────────────────────────────────────────────────────────────────────
# Education Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/me/education", response_model=list[UserEducationResponse])
@limiter.limit(standard_limiter)
async def get_my_education(
    request: Request,
    user: Annotated[CurrentUser, Depends(require_student)]
):
    """Get all education entries for the current student."""
    education = await fetch_many(
        TABLE_USER_EDUCATION,
        filters={"user_id": str(user.id)},
        columns=EDUCATION_COLUMNS.replace("\n", "").replace(" ", ""),
        order_by="start_date",
        order_desc=True
    )
    return education


@router.post("/me/education", response_model=UserEducationResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(write_limiter)
async def add_education(
    request: Request,
    education: UserEducationCreate,
    user: Annotated[CurrentUser, Depends(require_student)]
):
    """Add a new education entry."""
    edu_data = education.model_dump()
    edu_data["user_id"] = str(user.id)
    
    # Convert dates to strings
    if edu_data.get("start_date"):
        edu_data["start_date"] = edu_data["start_date"].isoformat()
    if edu_data.get("end_date"):
        edu_data["end_date"] = edu_data["end_date"].isoformat()
    
    created = await insert_row(TABLE_USER_EDUCATION, edu_data)
    return created


@router.patch("/me/education/{education_id}", response_model=UserEducationResponse)
@limiter.limit(write_limiter)
async def update_education(
    request: Request,
    education_id: UUID,
    update_data: UserEducationUpdate,
    user: Annotated[CurrentUser, Depends(require_student)]
):
    """Update a specific education entry."""
    existing = await fetch_one(TABLE_USER_EDUCATION, str(education_id))
    if not existing or existing.get("user_id") != str(user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Education entry not found"
        )
    
    update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)
    
    # Convert dates
    if "start_date" in update_dict and update_dict["start_date"]:
        update_dict["start_date"] = update_dict["start_date"].isoformat()
    if "end_date" in update_dict and update_dict["end_date"]:
        update_dict["end_date"] = update_dict["end_date"].isoformat()
    
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    updated = await update_row(TABLE_USER_EDUCATION, str(education_id), update_dict)
    return updated


@router.delete("/me/education/{education_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(write_limiter)
async def delete_education(
    request: Request,
    education_id: UUID,
    user: Annotated[CurrentUser, Depends(require_student)]
):
    """Delete a specific education entry."""
    existing = await fetch_one(TABLE_USER_EDUCATION, str(education_id))
    if not existing or existing.get("user_id") != str(user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Education entry not found"
        )
    
    await delete_row(TABLE_USER_EDUCATION, str(education_id))


# ─────────────────────────────────────────────────────────────────────────────
# Experience Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/me/experience", response_model=list[UserExperienceResponse])
@limiter.limit(standard_limiter)
async def get_my_experience(
    request: Request,
    user: Annotated[CurrentUser, Depends(require_student)]
):
    """Get all work experience for the current student."""
    experience = await fetch_many(
        TABLE_USER_EXPERIENCE,
        filters={"user_id": str(user.id)},
        columns=EXPERIENCE_COLUMNS.replace("\n", "").replace(" ", ""),
        order_by="start_date",
        order_desc=True
    )
    return experience


@router.post("/me/experience", response_model=UserExperienceResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(write_limiter)
async def add_experience(
    request: Request,
    experience: UserExperienceCreate,
    user: Annotated[CurrentUser, Depends(require_student)]
):
    """Add a new work experience entry."""
    exp_data = experience.model_dump()
    exp_data["user_id"] = str(user.id)
    
    # Convert dates
    exp_data["start_date"] = exp_data["start_date"].isoformat()
    if exp_data.get("end_date"):
        exp_data["end_date"] = exp_data["end_date"].isoformat()
    
    created = await insert_row(TABLE_USER_EXPERIENCE, exp_data)
    return created


@router.patch("/me/experience/{experience_id}", response_model=UserExperienceResponse)
@limiter.limit(write_limiter)
async def update_experience(
    request: Request,
    experience_id: UUID,
    update_data: UserExperienceUpdate,
    user: Annotated[CurrentUser, Depends(require_student)]
):
    """Update a specific work experience entry."""
    existing = await fetch_one(TABLE_USER_EXPERIENCE, str(experience_id))
    if not existing or existing.get("user_id") != str(user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experience entry not found"
        )
    
    update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)
    
    # Convert dates
    if "start_date" in update_dict and update_dict["start_date"]:
        update_dict["start_date"] = update_dict["start_date"].isoformat()
    if "end_date" in update_dict and update_dict["end_date"]:
        update_dict["end_date"] = update_dict["end_date"].isoformat()
    
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    updated = await update_row(TABLE_USER_EXPERIENCE, str(experience_id), update_dict)
    return updated


@router.delete("/me/experience/{experience_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(write_limiter)
async def delete_experience(
    request: Request,
    experience_id: UUID,
    user: Annotated[CurrentUser, Depends(require_student)]
):
    """Delete a specific work experience entry."""
    existing = await fetch_one(TABLE_USER_EXPERIENCE, str(experience_id))
    if not existing or existing.get("user_id") != str(user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experience entry not found"
        )
    
    await delete_row(TABLE_USER_EXPERIENCE, str(experience_id))


# ─────────────────────────────────────────────────────────────────────────────
# Projects Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/me/projects", response_model=list[UserProjectResponse])
@limiter.limit(standard_limiter)
async def get_my_projects(
    request: Request,
    user: Annotated[CurrentUser, Depends(require_student)]
):
    """Get all projects for the current student."""
    projects = await fetch_many(
        TABLE_USER_PROJECTS,
        filters={"user_id": str(user.id)},
        columns=PROJECT_COLUMNS.replace("\n", "").replace(" ", ""),
        order_by="created_at",
        order_desc=True
    )
    return projects


@router.post("/me/projects", response_model=UserProjectResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(write_limiter)
async def add_project(
    request: Request,
    project: UserProjectCreate,
    user: Annotated[CurrentUser, Depends(require_student)]
):
    """Add a new project."""
    proj_data = project.model_dump()
    proj_data["user_id"] = str(user.id)
    
    # Convert dates
    if proj_data.get("start_date"):
        proj_data["start_date"] = proj_data["start_date"].isoformat()
    if proj_data.get("end_date"):
        proj_data["end_date"] = proj_data["end_date"].isoformat()
    
    created = await insert_row(TABLE_USER_PROJECTS, proj_data)
    return created


@router.patch("/me/projects/{project_id}", response_model=UserProjectResponse)
@limiter.limit(write_limiter)
async def update_project(
    request: Request,
    project_id: UUID,
    update_data: UserProjectUpdate,
    user: Annotated[CurrentUser, Depends(require_student)]
):
    """Update a specific project."""
    existing = await fetch_one(TABLE_USER_PROJECTS, str(project_id))
    if not existing or existing.get("user_id") != str(user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)
    
    if "start_date" in update_dict and update_dict["start_date"]:
        update_dict["start_date"] = update_dict["start_date"].isoformat()
    if "end_date" in update_dict and update_dict["end_date"]:
        update_dict["end_date"] = update_dict["end_date"].isoformat()
    
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    updated = await update_row(TABLE_USER_PROJECTS, str(project_id), update_dict)
    return updated


@router.delete("/me/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(write_limiter)
async def delete_project(
    request: Request,
    project_id: UUID,
    user: Annotated[CurrentUser, Depends(require_student)]
):
    """Delete a specific project."""
    existing = await fetch_one(TABLE_USER_PROJECTS, str(project_id))
    if not existing or existing.get("user_id") != str(user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    await delete_row(TABLE_USER_PROJECTS, str(project_id))


# ─────────────────────────────────────────────────────────────────────────────
# Certifications Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/me/certifications", response_model=list[UserCertificationResponse])
@limiter.limit(standard_limiter)
async def get_my_certifications(
    request: Request,
    user: Annotated[CurrentUser, Depends(require_student)]
):
    """Get all certifications for the current student."""
    certs = await fetch_many(
        TABLE_USER_CERTIFICATIONS,
        filters={"user_id": str(user.id)},
        columns=CERTIFICATION_COLUMNS.replace("\n", "").replace(" ", ""),
        order_by="issue_date",
        order_desc=True
    )
    return certs


@router.post("/me/certifications", response_model=UserCertificationResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(write_limiter)
async def add_certification(
    request: Request,
    certification: UserCertificationCreate,
    user: Annotated[CurrentUser, Depends(require_student)]
):
    """Add a new certification."""
    cert_data = certification.model_dump()
    cert_data["user_id"] = str(user.id)
    
    if cert_data.get("issue_date"):
        cert_data["issue_date"] = cert_data["issue_date"].isoformat()
    if cert_data.get("expiry_date"):
        cert_data["expiry_date"] = cert_data["expiry_date"].isoformat()
    
    created = await insert_row(TABLE_USER_CERTIFICATIONS, cert_data)
    return created


@router.patch("/me/certifications/{certification_id}", response_model=UserCertificationResponse)
@limiter.limit(write_limiter)
async def update_certification(
    request: Request,
    certification_id: UUID,
    update_data: UserCertificationUpdate,
    user: Annotated[CurrentUser, Depends(require_student)]
):
    """Update a specific certification."""
    existing = await fetch_one(TABLE_USER_CERTIFICATIONS, str(certification_id))
    if not existing or existing.get("user_id") != str(user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certification not found"
        )
    
    update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)
    
    if "issue_date" in update_dict and update_dict["issue_date"]:
        update_dict["issue_date"] = update_dict["issue_date"].isoformat()
    if "expiry_date" in update_dict and update_dict["expiry_date"]:
        update_dict["expiry_date"] = update_dict["expiry_date"].isoformat()
    
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    updated = await update_row(TABLE_USER_CERTIFICATIONS, str(certification_id), update_dict)
    return updated


@router.delete("/me/certifications/{certification_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(write_limiter)
async def delete_certification(
    request: Request,
    certification_id: UUID,
    user: Annotated[CurrentUser, Depends(require_student)]
):
    """Delete a specific certification."""
    existing = await fetch_one(TABLE_USER_CERTIFICATIONS, str(certification_id))
    if not existing or existing.get("user_id") != str(user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certification not found"
        )
    
    await delete_row(TABLE_USER_CERTIFICATIONS, str(certification_id))
