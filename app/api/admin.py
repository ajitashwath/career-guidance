"""
Admin API routes.

Admins can:
- Force score recomputation
- View raw event streams
- Debug scoring logic
- Toggle scoring versions

All endpoints require admin role.
"""

from datetime import datetime, timezone
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from starlette.requests import Request
from pydantic import BaseModel

from app.middleware.rate_limiting import limiter, admin_limiter, standard_limiter

from app.core.auth import require_admin, CurrentUser
from app.core.config import get_settings
from app.db.supabase import get_supabase_client, fetch_many
from app.db.queries import TABLE_USER_EVENTS, TABLE_USER_INTELLIGENCE_SNAPSHOTS
from app.intelligence.scoring import full_score_recomputation, get_score_debug_info
from app.workers.recompute_scores import batch_recompute_scores
from app.schemas.events import EventResponse
from app.schemas.intelligence import ScoreDebugInfo, IntelligenceSnapshot

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Response Models
# ─────────────────────────────────────────────────────────────────────────────

class RecomputeResult(BaseModel):
    """Result of score recomputation."""
    user_id: UUID
    success: bool
    overall_capability_score: Optional[int] = None
    profile_tier: Optional[int] = None
    message: str


class BatchRecomputeResult(BaseModel):
    """Result of batch recomputation."""
    total: int
    success: int
    failed: int
    failures: list[dict]


class ScoringVersionInfo(BaseModel):
    """Current scoring version configuration."""
    current_version: str
    event_window_days: int
    decay_half_life_days: int
    weights: dict[str, float]


class EventStreamResponse(BaseModel):
    """Raw event stream for admin viewing."""
    user_id: UUID
    events: list[EventResponse]
    total_count: int


# ─────────────────────────────────────────────────────────────────────────────
# Score Recomputation
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/users/{user_id}/recompute", response_model=RecomputeResult)
@limiter.limit(admin_limiter)
async def force_recompute_scores(
    request: Request,
    user_id: UUID,
    user: Annotated[CurrentUser, Depends(require_admin)]
):
    """
    Force immediate score recomputation for a user.
    
    This bypasses normal background processing and runs synchronously.
    Use for debugging or when immediate update is required.
    """
    try:
        scores = await full_score_recomputation(user_id)
        
        return RecomputeResult(
            user_id=user_id,
            success=True,
            overall_capability_score=scores.overall_capability.value,
            profile_tier=scores.tier.value,
            message="Scores recomputed successfully"
        )
    except Exception as e:
        return RecomputeResult(
            user_id=user_id,
            success=False,
            message=f"Recomputation failed: {str(e)}"
        )


@router.post("/recompute/batch", response_model=BatchRecomputeResult)
@limiter.limit(admin_limiter)
async def batch_recompute(
    request: Request,
    user_ids: list[UUID],
    user: Annotated[CurrentUser, Depends(require_admin)]
):
    """
    Batch recompute scores for multiple users.
    
    Useful for:
    - Migrating to new scoring version
    - Fixing data issues
    - Regular maintenance
    """
    if len(user_ids) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 100 users per batch"
        )
    
    results = await batch_recompute_scores(user_ids)
    
    return BatchRecomputeResult(**results)


# ─────────────────────────────────────────────────────────────────────────────
# Event Viewing
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/users/{user_id}/events", response_model=EventStreamResponse)
@limiter.limit(standard_limiter)
async def get_raw_events(
    request: Request,
    user_id: UUID,
    user: Annotated[CurrentUser, Depends(require_admin)],
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    event_type: Optional[str] = Query(default=None)
):
    """
    View raw event stream for a user.
    
    **Admin only**: This exposes raw event payloads.
    For debugging and auditing purposes.
    """
    client = get_supabase_client()
    
    query = (
        client.table(TABLE_USER_EVENTS)
        .select("*", count="exact")
        .eq("user_id", str(user_id))
    )
    
    if event_type:
        query = query.eq("event_type", event_type)
    
    query = (
        query
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
    )
    
    response = query.execute()
    
    return EventStreamResponse(
        user_id=user_id,
        events=response.data,
        total_count=response.count or 0
    )


# ─────────────────────────────────────────────────────────────────────────────
# Score Debugging
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/scoring/debug/{user_id}", response_model=ScoreDebugInfo)
@limiter.limit(standard_limiter)
async def get_scoring_debug(
    request: Request,
    user_id: UUID,
    user: Annotated[CurrentUser, Depends(require_admin)]
):
    """
    Get detailed scoring debug information.
    
    Shows:
    - Raw event counts by category
    - Individual dimension breakdowns
    - Weights applied
    - Configuration at computation time
    """
    try:
        debug_info = await get_score_debug_info(user_id)
        return debug_info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Debug info generation failed: {str(e)}"
        )


@router.get("/users/{user_id}/snapshots", response_model=list[IntelligenceSnapshot])
@limiter.limit(standard_limiter)
async def get_score_history(
    request: Request,
    user_id: UUID,
    user: Annotated[CurrentUser, Depends(require_admin)],
    limit: int = Query(default=10, ge=1, le=100)
):
    """
    Get historical intelligence snapshots for a user.
    
    Shows score progression over time for trend analysis.
    """
    client = get_supabase_client()
    
    response = (
        client.table(TABLE_USER_INTELLIGENCE_SNAPSHOTS)
        .select("*")
        .eq("user_id", str(user_id))
        .order("computed_at", desc=True)
        .limit(limit)
        .execute()
    )
    
    return response.data


# ─────────────────────────────────────────────────────────────────────────────
# Scoring Version Management
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/scoring/version", response_model=ScoringVersionInfo)
@limiter.limit(standard_limiter)
async def get_scoring_version(
    request: Request,
    user: Annotated[CurrentUser, Depends(require_admin)]
):
    """
    Get current scoring version configuration.
    
    Shows:
    - Version string
    - Event window
    - Decay settings
    - Weight distribution
    """
    settings = get_settings()
    
    return ScoringVersionInfo(
        current_version=settings.scoring_version,
        event_window_days=settings.event_window_days,
        decay_half_life_days=settings.decay_half_life_days,
        weights={
            "engagement": settings.weight_engagement,
            "learning_velocity": settings.weight_learning_velocity,
            "commitment": settings.weight_commitment,
            "interview_readiness": settings.weight_interview_readiness,
            "professional_maturity": settings.weight_professional_maturity,
        }
    )


@router.get("/stats/overview")
@limiter.limit(standard_limiter)
async def get_system_stats(
    request: Request,
    user: Annotated[CurrentUser, Depends(require_admin)]
):
    """
    Get system-wide statistics.
    
    Provides overview of:
    - Total users by tier
    - Event counts
    - Scoring distribution
    """
    from app.db.queries import TABLE_USER_PROFILES
    
    client = get_supabase_client()
    
    # Count by tier
    tier_counts = {}
    for tier in [1, 2, 3]:
        response = (
            client.table(TABLE_USER_PROFILES)
            .select("id", count="exact")
            .eq("profile_tier", tier)
            .eq("onboarding_completed", True)
            .execute()
        )
        tier_counts[f"tier_{tier}"] = response.count or 0
    
    # Total events (last 30 days)
    from datetime import timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    event_response = (
        client.table(TABLE_USER_EVENTS)
        .select("id", count="exact")
        .gte("created_at", cutoff.isoformat())
        .execute()
    )
    
    return {
        "tier_distribution": tier_counts,
        "total_users": sum(tier_counts.values()),
        "events_last_30_days": event_response.count or 0,
        "scoring_version": get_settings().scoring_version,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }
