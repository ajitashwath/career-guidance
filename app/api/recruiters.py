"""
Recruiter API routes.

Recruiters can:
- Search and filter candidate profiles
- View intelligence summaries
- View activity timelines (sanitized, no raw events)

All endpoints enforce recruiter role access.
"""

from datetime import datetime, timezone, timedelta
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from starlette.requests import Request
from pydantic import BaseModel

from app.middleware.rate_limiting import limiter, standard_limiter, recruiter_read_limiter

from app.core.auth import require_recruiter, CurrentUser
from app.db.supabase import get_supabase_client, fetch_one, fetch_many
from app.db.queries import (
    TABLE_USER_PROFILES,
    TABLE_USER_INTELLIGENCE_SNAPSHOTS,
    RECRUITER_PROFILE_COLUMNS,
)
from app.schemas.profiles import RecruiterProfileView
from app.schemas.intelligence import IntelligenceSummary, IntelligenceTimeline

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Response Models
# ─────────────────────────────────────────────────────────────────────────────

class CandidateSearchResponse(BaseModel):
    """Paginated candidate search results."""
    candidates: list[RecruiterProfileView]
    total_count: int
    page: int
    page_size: int
    has_more: bool


class CandidateTimeline(BaseModel):
    """Sanitized activity timeline for recruiters."""
    user_id: UUID
    activities: list[dict]  # Sanitized activity summaries
    total_events: int
    date_range_start: datetime
    date_range_end: datetime


# ─────────────────────────────────────────────────────────────────────────────
# Candidate Search
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/candidates", response_model=CandidateSearchResponse)
@limiter.limit(recruiter_read_limiter)
async def search_candidates(
    request: Request,
    user: Annotated[CurrentUser, Depends(require_recruiter)],
    # Score filters
    min_capability_score: Optional[int] = Query(default=None, ge=0, le=100),
    max_capability_score: Optional[int] = Query(default=None, ge=0, le=100),
    tier: Optional[int] = Query(default=None, ge=1, le=3),
    # Skill filters
    skills: Optional[list[str]] = Query(default=None),
    # Role filters
    target_roles: Optional[list[str]] = Query(default=None),
    # Academic filters
    graduation_year_min: Optional[int] = Query(default=None),
    graduation_year_max: Optional[int] = Query(default=None),
    major: Optional[str] = Query(default=None),
    # Location filters
    willing_to_relocate: Optional[bool] = Query(default=None),
    country: Optional[str] = Query(default=None),
    # Pagination
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    # Sorting
    sort_by: str = Query(default="overall_capability_score"),
    sort_desc: bool = Query(default=True),
):
    """
    Search and filter candidate profiles.
    
    Returns sanitized profiles with intelligence scores.
    Raw events and private data are never exposed.
    """
    client = get_supabase_client()
    columns = RECRUITER_PROFILE_COLUMNS.replace("\n", "").replace(" ", "")
    
    # Build query
    query = client.table(TABLE_USER_PROFILES).select(columns, count="exact")
    
    # Only include completed profiles
    query = query.eq("onboarding_completed", True)
    
    # Apply score filters
    if min_capability_score is not None:
        query = query.gte("overall_capability_score", min_capability_score)
    if max_capability_score is not None:
        query = query.lte("overall_capability_score", max_capability_score)
    if tier is not None:
        query = query.eq("profile_tier", tier)
    
    # Apply skill filter (contains any)
    if skills:
        # Supabase array overlap filter
        query = query.overlaps("current_skills", skills)
    
    # Apply role filter
    if target_roles:
        query = query.overlaps("target_roles", target_roles)
    
    # Apply academic filters
    if graduation_year_min is not None:
        query = query.gte("graduation_year", graduation_year_min)
    if graduation_year_max is not None:
        query = query.lte("graduation_year", graduation_year_max)
    if major:
        query = query.ilike("major", f"%{major}%")
    
    # Apply location filters
    if willing_to_relocate is not None:
        query = query.eq("willing_to_relocate", willing_to_relocate)
    if country:
        query = query.ilike("country", f"%{country}%")
    
    # Apply sorting
    valid_sort_fields = [
        "overall_capability_score",
        "engagement_score",
        "learning_velocity_score",
        "commitment_score",
        "interview_readiness_score",
        "professional_maturity_score",
        "graduation_year",
        "last_active_at",
    ]
    if sort_by not in valid_sort_fields:
        sort_by = "overall_capability_score"
    
    query = query.order(sort_by, desc=sort_desc)
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.range(offset, offset + page_size - 1)
    
    # Execute
    response = query.execute()
    
    total_count = response.count or 0
    has_more = (offset + len(response.data)) < total_count
    
    return CandidateSearchResponse(
        candidates=response.data,
        total_count=total_count,
        page=page,
        page_size=page_size,
        has_more=has_more
    )


# ─────────────────────────────────────────────────────────────────────────────
# Individual Candidate Views
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/candidates/{candidate_id}", response_model=RecruiterProfileView)
@limiter.limit(standard_limiter)
async def get_candidate_profile(
    request: Request,
    candidate_id: UUID,
    user: Annotated[CurrentUser, Depends(require_recruiter)]
):
    """
    Get a specific candidate's profile (sanitized).
    
    Excludes:
    - Email, phone (require explicit share)
    - Salary expectations
    - Internal tier labels
    """
    columns = RECRUITER_PROFILE_COLUMNS.replace("\n", "").replace(" ", "")
    profile = await fetch_one(
        TABLE_USER_PROFILES,
        str(candidate_id),
        columns=columns
    )
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )
    
    return profile


@router.get("/candidates/{candidate_id}/summary", response_model=IntelligenceSummary)
@limiter.limit(standard_limiter)
async def get_candidate_intelligence_summary(
    request: Request,
    candidate_id: UUID,
    user: Annotated[CurrentUser, Depends(require_recruiter)]
):
    """
    Get intelligence summary for a candidate.
    
    Provides score overview without detailed breakdown.
    """
    # Get latest snapshot
    client = get_supabase_client()
    response = (
        client.table(TABLE_USER_INTELLIGENCE_SNAPSHOTS)
        .select("*")
        .eq("user_id", str(candidate_id))
        .order("computed_at", desc=True)
        .limit(1)
        .execute()
    )
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No intelligence data available for this candidate"
        )
    
    snapshot = response.data[0]
    
    return IntelligenceSummary(
        engagement_score=snapshot["engagement_score"],
        learning_velocity_score=snapshot["learning_velocity_score"],
        commitment_score=snapshot["commitment_score"],
        interview_readiness_score=snapshot["interview_readiness_score"],
        professional_maturity_score=snapshot["professional_maturity_score"],
        overall_capability_score=snapshot["overall_capability_score"],
        profile_tier=snapshot["profile_tier"],
        confidence_level=float(snapshot["confidence_level"]),
        last_computed=snapshot["computed_at"]
    )


@router.get("/candidates/{candidate_id}/timeline", response_model=CandidateTimeline)
@limiter.limit(standard_limiter)
async def get_candidate_timeline(
    request: Request,
    candidate_id: UUID,
    user: Annotated[CurrentUser, Depends(require_recruiter)],
    days: int = Query(default=30, ge=1, le=90)
):
    """
    Get sanitized activity timeline for a candidate.
    
    Returns activity summaries grouped by type.
    Raw event payloads are NOT exposed to protect privacy.
    """
    from app.db.queries import TABLE_USER_EVENTS
    
    client = get_supabase_client()
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Fetch events (only type and timestamp, NO payload)
    response = (
        client.table(TABLE_USER_EVENTS)
        .select("event_type, created_at")
        .eq("user_id", str(candidate_id))
        .gte("created_at", cutoff.isoformat())
        .order("created_at", desc=True)
        .execute()
    )
    
    # Aggregate into daily summaries
    activities = []
    if response.data:
        # Group by date
        daily_events: dict[str, dict[str, int]] = {}
        for event in response.data:
            date_str = event["created_at"][:10]  # YYYY-MM-DD
            event_type = event["event_type"]
            
            if date_str not in daily_events:
                daily_events[date_str] = {}
            
            if event_type not in daily_events[date_str]:
                daily_events[date_str][event_type] = 0
            daily_events[date_str][event_type] += 1
        
        # Format as activity list
        for date_str, type_counts in sorted(daily_events.items(), reverse=True):
            activities.append({
                "date": date_str,
                "event_counts": type_counts,
                "total_events": sum(type_counts.values())
            })
    
    return CandidateTimeline(
        user_id=candidate_id,
        activities=activities,
        total_events=len(response.data) if response.data else 0,
        date_range_start=cutoff,
        date_range_end=datetime.now(timezone.utc)
    )
