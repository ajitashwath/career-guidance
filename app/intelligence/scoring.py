"""
Main scoring engine that orchestrates the intelligence computation.

This is the entry point for computing user intelligence scores.
It coordinates event fetching, aggregation, and snapshot creation.
"""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.core.config import get_settings
from app.db.supabase import get_supabase_client, fetch_many, insert_row, update_row
from app.db.queries import TABLE_USER_EVENTS, TABLE_USER_INTELLIGENCE_SNAPSHOTS, TABLE_USER_PROFILES
from app.intelligence.aggregators import (
    compute_engagement_score,
    compute_learning_velocity_score,
    compute_commitment_score,
    compute_interview_readiness_score,
    compute_professional_maturity_score,
    compute_overall_capability,
    assign_tier,
)
from app.schemas.intelligence import (
    IntelligenceScores,
    IntelligenceSnapshot,
    IntelligenceSnapshotCreate,
    ProfileTier,
    ScoreDebugInfo,
)


async def fetch_user_events(
    user_id: UUID,
    days: int | None = None
) -> list[dict[str, Any]]:
    """
    Fetch events for a user within the scoring window.
    
    Args:
        user_id: User to fetch events for
        days: Number of days of events (default: from config)
        
    Returns:
        List of event dictionaries sorted by created_at DESC
    """
    settings = get_settings()
    window_days = days or settings.event_window_days
    
    client = get_supabase_client()
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=window_days)
    
    response = (
        client.table(TABLE_USER_EVENTS)
        .select("*")
        .eq("user_id", str(user_id))
        .gte("created_at", cutoff_date.isoformat())
        .order("created_at", desc=True)
        .execute()
    )
    
    return response.data


async def compute_user_intelligence(
    user_id: UUID,
    events: list[dict[str, Any]] | None = None,
    reference_time: datetime | None = None
) -> IntelligenceScores:
    """
    Compute full intelligence scores for a user.
    
    This is the main scoring function that:
    1. Fetches events if not provided
    2. Computes all dimension scores
    3. Calculates weighted overall capability
    4. Assigns tier
    
    Args:
        user_id: User to compute scores for
        events: Optional pre-fetched events (optimization)
        reference_time: Reference time for decay (default: now)
        
    Returns:
        Complete IntelligenceScores with all dimensions
    """
    if reference_time is None:
        reference_time = datetime.now(timezone.utc)
    
    # Fetch events if not provided
    if events is None:
        events = await fetch_user_events(user_id)
    
    # Compute individual scores
    engagement = compute_engagement_score(events, reference_time)
    learning_velocity = compute_learning_velocity_score(events, reference_time)
    commitment = compute_commitment_score(events, reference_time)
    interview_readiness = compute_interview_readiness_score(events, reference_time)
    professional_maturity = compute_professional_maturity_score(events, reference_time)
    
    # Compute weighted overall
    overall = compute_overall_capability(
        engagement=engagement,
        learning_velocity=learning_velocity,
        commitment=commitment,
        interview_readiness=interview_readiness,
        professional_maturity=professional_maturity
    )
    
    # Assign tier
    tier_value = assign_tier(overall.value)
    tier = ProfileTier(tier_value)
    
    return IntelligenceScores(
        engagement=engagement,
        learning_velocity=learning_velocity,
        commitment=commitment,
        interview_readiness=interview_readiness,
        professional_maturity=professional_maturity,
        overall_capability=overall,
        tier=tier
    )


async def create_intelligence_snapshot(
    user_id: UUID,
    scores: IntelligenceScores
) -> dict:
    """
    Create an immutable snapshot of user intelligence scores.
    
    Snapshots are versioned and timestamped for auditing.
    
    Args:
        user_id: User the snapshot is for
        scores: Computed intelligence scores
        
    Returns:
        Created snapshot record
    """
    settings = get_settings()
    
    snapshot_data = {
        "user_id": str(user_id),
        "engagement_score": scores.engagement.value,
        "learning_velocity_score": scores.learning_velocity.value,
        "commitment_score": scores.commitment.value,
        "interview_readiness_score": scores.interview_readiness.value,
        "professional_maturity_score": scores.professional_maturity.value,
        "overall_capability_score": scores.overall_capability.value,
        "profile_tier": scores.tier.value,
        "scoring_version": settings.scoring_version,
        "confidence_level": float(scores.overall_capability.confidence),
    }
    
    return await insert_row(TABLE_USER_INTELLIGENCE_SNAPSHOTS, snapshot_data)


async def sync_profile_scores(
    user_id: UUID,
    scores: IntelligenceScores
) -> dict:
    """
    Sync computed scores to user profile for fast querying.
    
    Profile scores are denormalized for recruiter search performance.
    The source of truth remains the snapshot table.
    
    Args:
        user_id: User to update
        scores: Current intelligence scores
        
    Returns:
        Updated profile record
    """
    profile_update = {
        "engagement_score": scores.engagement.value,
        "learning_velocity_score": scores.learning_velocity.value,
        "commitment_score": scores.commitment.value,
        "interview_readiness_score": scores.interview_readiness.value,
        "professional_maturity_score": scores.professional_maturity.value,
        "overall_capability_score": scores.overall_capability.value,
        "profile_tier": scores.tier.value,
        "last_active_at": datetime.now(timezone.utc).isoformat(),
    }
    
    return await update_row(TABLE_USER_PROFILES, str(user_id), profile_update)


async def full_score_recomputation(user_id: UUID) -> IntelligenceScores:
    """
    Perform full score recomputation pipeline.
    
    This is the complete flow:
    1. Fetch all events in window
    2. Compute all scores
    3. Create versioned snapshot
    4. Sync to profile
    
    Called by background workers and admin force-recompute.
    
    Args:
        user_id: User to recompute scores for
        
    Returns:
        Newly computed intelligence scores
    """
    # Compute scores
    scores = await compute_user_intelligence(user_id)
    
    # Create snapshot for audit trail
    await create_intelligence_snapshot(user_id, scores)
    
    # Sync to profile for fast queries
    await sync_profile_scores(user_id, scores)
    
    return scores


async def get_score_debug_info(user_id: UUID) -> ScoreDebugInfo:
    """
    Get detailed debug information for admin analysis.
    
    Includes raw event counts, intermediate calculations,
    and configuration at time of computation.
    """
    settings = get_settings()
    events = await fetch_user_events(user_id)
    scores = await compute_user_intelligence(user_id, events)
    
    # Count events by category
    from app.schemas.events import EVENT_CATEGORIES
    
    event_counts = {}
    for category in EVENT_CATEGORIES:
        valid_types = {et.value for et in EVENT_CATEGORIES[category]}
        count = sum(1 for e in events if e.get("event_type") in valid_types)
        event_counts[category] = count
    
    return ScoreDebugInfo(
        user_id=user_id,
        scoring_version=settings.scoring_version,
        computed_at=datetime.now(timezone.utc),
        event_counts=event_counts,
        engagement_breakdown=scores.engagement,
        learning_velocity_breakdown=scores.learning_velocity,
        commitment_breakdown=scores.commitment,
        interview_readiness_breakdown=scores.interview_readiness,
        professional_maturity_breakdown=scores.professional_maturity,
        weights_applied={
            "engagement": settings.weight_engagement,
            "learning_velocity": settings.weight_learning_velocity,
            "commitment": settings.weight_commitment,
            "interview_readiness": settings.weight_interview_readiness,
            "professional_maturity": settings.weight_professional_maturity,
        },
        final_scores=scores,
        config_snapshot={
            "scoring_version": settings.scoring_version,
            "event_window_days": settings.event_window_days,
            "decay_half_life_days": settings.decay_half_life_days,
            "tier_1_percentile": settings.tier_1_percentile,
            "tier_2_percentile": settings.tier_2_percentile,
        }
    )
