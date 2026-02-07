"""
Score aggregator functions for each intelligence dimension.

Each aggregator:
1. Filters events by relevant types
2. Applies time decay
3. Computes dimension-specific metrics
4. Returns explainable ScoreResult

All scores are normalized to 0-100 range.
"""

from datetime import datetime, timezone, timedelta
from typing import Any

from app.core.config import get_settings
from app.intelligence.decay import (
    exponential_decay,
    recency_bonus,
    calculate_weighted_event_value,
)
from app.schemas.events import EventType, EVENT_CATEGORIES
from app.schemas.intelligence import ScoreFactor, ScoreResult


# ─────────────────────────────────────────────────────────────────────────────
# Event Type Base Values
# ─────────────────────────────────────────────────────────────────────────────
# These define the inherent "worth" of each event type
# Higher values = more significant actions
# Range: 1-20 points base value

EVENT_BASE_VALUES: dict[EventType, int] = {
    # Engagement (1-15 range)
    EventType.PROFILE_VIEW: 1,
    EventType.PROFILE_UPDATE: 5,
    EventType.SKILL_ADDED: 8,
    EventType.SKILL_UPDATED: 3,
    EventType.PROJECT_ADDED: 15,
    EventType.PROJECT_UPDATED: 5,
    EventType.CERTIFICATION_ADDED: 12,
    EventType.EDUCATION_ADDED: 10,
    EventType.EXPERIENCE_ADDED: 12,
    EventType.RESUME_UPLOADED: 8,
    EventType.LINKEDIN_CONNECTED: 10,
    EventType.GITHUB_CONNECTED: 10,
    
    # Learning (5-20 range - learning is highly valued)
    EventType.COURSE_STARTED: 5,
    EventType.COURSE_COMPLETED: 20,
    EventType.COURSE_PROGRESS: 3,
    EventType.QUIZ_ATTEMPTED: 5,
    EventType.QUIZ_PASSED: 10,
    EventType.RESOURCE_VIEWED: 2,
    EventType.SKILL_VERIFIED: 18,
    EventType.ASSESSMENT_COMPLETED: 15,
    
    # Commitment (5-20 range)
    EventType.DAILY_LOGIN: 2,
    EventType.STREAK_ACHIEVED: 15,
    EventType.STREAK_BROKEN: -5,  # Negative impact
    EventType.GOAL_SET: 8,
    EventType.GOAL_UPDATED: 3,
    EventType.GOAL_COMPLETED: 20,
    EventType.APPLICATION_SUBMITTED: 15,
    EventType.APPLICATION_WITHDRAWN: -3,
    EventType.INTERVIEW_SCHEDULED: 18,
    
    # Interview Readiness (10-20 range - high value actions)
    EventType.MOCK_INTERVIEW_STARTED: 8,
    EventType.MOCK_INTERVIEW_COMPLETED: 18,
    EventType.FEEDBACK_RECEIVED: 12,
    EventType.FEEDBACK_APPLIED: 15,
    EventType.PRACTICE_SESSION: 10,
    EventType.BEHAVIORAL_PRACTICE: 12,
    EventType.TECHNICAL_PRACTICE: 12,
    EventType.MENTOR_SESSION: 16,
    
    # Professional Maturity (8-18 range)
    EventType.RECOMMENDATION_RECEIVED: 18,
    EventType.RECOMMENDATION_REQUESTED: 5,
    EventType.ENDORSEMENT_GIVEN: 8,
    EventType.ENDORSEMENT_RECEIVED: 12,
    EventType.COMMUNITY_CONTRIBUTION: 15,
    EventType.ARTICLE_PUBLISHED: 18,
    EventType.NETWORKING_EVENT: 10,
    EventType.MENTORED_PEER: 15,
}


def _filter_events_by_category(
    events: list[dict[str, Any]],
    category: str
) -> list[dict[str, Any]]:
    """Filter events to those in a specific scoring category."""
    valid_types = {et.value for et in EVENT_CATEGORIES[category]}
    return [e for e in events if e.get("event_type") in valid_types]


def _compute_score_from_events(
    events: list[dict[str, Any]],
    category: str,
    reference_time: datetime | None = None
) -> ScoreResult:
    """
    Generic score computation for a category of events.
    
    Score = sum of weighted event values, normalized to 0-100.
    Confidence increases with event count.
    """
    settings = get_settings()
    half_life = settings.decay_half_life_days
    
    if reference_time is None:
        reference_time = datetime.now(timezone.utc)
    
    # Filter to relevant events
    category_events = _filter_events_by_category(events, category)
    
    if not category_events:
        return ScoreResult(
            value=0,
            confidence=0.0,
            factors=[
                ScoreFactor(
                    factor_name="no_activity",
                    factor_value=0,
                    weight=1.0,
                    description=f"No {category.replace('_', ' ')} events recorded",
                    event_count=0
                )
            ],
            events_considered=0
        )
    
    # Calculate weighted sum
    total_value = 0.0
    factor_contributions: dict[str, dict] = {}
    
    for event in category_events:
        event_type_str = event.get("event_type")
        try:
            event_type = EventType(event_type_str)
        except ValueError:
            continue
        
        base_value = EVENT_BASE_VALUES.get(event_type, 5)
        
        # Parse timestamp
        created_at = event.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        elif created_at is None:
            continue
        
        # Calculate weighted value
        weighted_value = calculate_weighted_event_value(
            event_timestamp=created_at,
            base_value=base_value,
            half_life_days=half_life,
            reference_time=reference_time
        )
        
        total_value += weighted_value
        
        # Track for explainability
        if event_type_str not in factor_contributions:
            factor_contributions[event_type_str] = {
                "count": 0,
                "total_value": 0.0
            }
        factor_contributions[event_type_str]["count"] += 1
        factor_contributions[event_type_str]["total_value"] += weighted_value
    
    # Normalize to 0-100 scale
    # Max expected value scales with event window
    # Assume ~2 significant events per day over window = 180 events
    # With base value ~10, that's 1800 raw points
    # After decay, effective value is ~600 points
    max_expected_value = 600.0
    normalized_score = min(100, int((total_value / max_expected_value) * 100))
    
    # Calculate confidence based on event count
    # 30+ events = high confidence
    event_count = len(category_events)
    confidence = min(1.0, event_count / 30)
    
    # Build explainability factors
    factors = []
    for event_type_str, contrib in sorted(
        factor_contributions.items(),
        key=lambda x: x[1]["total_value"],
        reverse=True
    )[:5]:  # Top 5 contributors
        factors.append(ScoreFactor(
            factor_name=event_type_str,
            factor_value=round(contrib["total_value"], 2),
            weight=EVENT_BASE_VALUES.get(EventType(event_type_str), 5) / 20,
            description=f"{event_type_str.replace('_', ' ').title()} events",
            event_count=contrib["count"]
        ))
    
    return ScoreResult(
        value=normalized_score,
        confidence=round(confidence, 2),
        factors=factors,
        events_considered=event_count
    )


# ─────────────────────────────────────────────────────────────────────────────
# Public Aggregator Functions
# ─────────────────────────────────────────────────────────────────────────────

def compute_engagement_score(
    events: list[dict[str, Any]],
    reference_time: datetime | None = None
) -> ScoreResult:
    """
    Compute engagement score from user events.
    
    Measures:
    - Profile completeness actions
    - Platform activity frequency
    - Integration with external platforms
    """
    return _compute_score_from_events(events, "engagement", reference_time)


def compute_learning_velocity_score(
    events: list[dict[str, Any]],
    reference_time: datetime | None = None
) -> ScoreResult:
    """
    Compute learning velocity score from user events.
    
    Measures:
    - Rate of skill acquisition
    - Course completion rate
    - Assessment performance
    - Skill verification status
    """
    return _compute_score_from_events(events, "learning_velocity", reference_time)


def compute_commitment_score(
    events: list[dict[str, Any]],
    reference_time: datetime | None = None
) -> ScoreResult:
    """
    Compute commitment score from user events.
    
    Measures:
    - Consistency of activity (streaks)
    - Goal setting and completion
    - Application follow-through
    - Long-term engagement patterns
    """
    return _compute_score_from_events(events, "commitment", reference_time)


def compute_interview_readiness_score(
    events: list[dict[str, Any]],
    reference_time: datetime | None = None
) -> ScoreResult:
    """
    Compute interview readiness score from user events.
    
    Measures:
    - Mock interview participation
    - Practice session frequency
    - Feedback incorporation
    - Mentor engagement
    """
    return _compute_score_from_events(events, "interview_readiness", reference_time)


def compute_professional_maturity_score(
    events: list[dict[str, Any]],
    reference_time: datetime | None = None
) -> ScoreResult:
    """
    Compute professional maturity score from user events.
    
    Measures:
    - Recommendations received
    - Community contributions
    - Peer mentorship
    - Thought leadership (articles)
    """
    return _compute_score_from_events(events, "professional_maturity", reference_time)


def compute_overall_capability(
    engagement: ScoreResult,
    learning_velocity: ScoreResult,
    commitment: ScoreResult,
    interview_readiness: ScoreResult,
    professional_maturity: ScoreResult
) -> ScoreResult:
    """
    Compute weighted overall capability score.
    
    Weights are configurable via environment variables.
    Overall confidence is the weighted average of component confidences.
    """
    settings = get_settings()
    
    # Apply weights
    weighted_sum = (
        engagement.value * settings.weight_engagement +
        learning_velocity.value * settings.weight_learning_velocity +
        commitment.value * settings.weight_commitment +
        interview_readiness.value * settings.weight_interview_readiness +
        professional_maturity.value * settings.weight_professional_maturity
    )
    
    # Weighted confidence
    weighted_confidence = (
        engagement.confidence * settings.weight_engagement +
        learning_velocity.confidence * settings.weight_learning_velocity +
        commitment.confidence * settings.weight_commitment +
        interview_readiness.confidence * settings.weight_interview_readiness +
        professional_maturity.confidence * settings.weight_professional_maturity
    )
    
    overall_score = int(round(weighted_sum))
    
    # Build factors showing contribution of each dimension
    factors = [
        ScoreFactor(
            factor_name="engagement",
            factor_value=engagement.value * settings.weight_engagement,
            weight=settings.weight_engagement,
            description=f"Engagement ({engagement.value}/100 × {settings.weight_engagement:.0%})",
            event_count=engagement.events_considered
        ),
        ScoreFactor(
            factor_name="learning_velocity",
            factor_value=learning_velocity.value * settings.weight_learning_velocity,
            weight=settings.weight_learning_velocity,
            description=f"Learning ({learning_velocity.value}/100 × {settings.weight_learning_velocity:.0%})",
            event_count=learning_velocity.events_considered
        ),
        ScoreFactor(
            factor_name="commitment",
            factor_value=commitment.value * settings.weight_commitment,
            weight=settings.weight_commitment,
            description=f"Commitment ({commitment.value}/100 × {settings.weight_commitment:.0%})",
            event_count=commitment.events_considered
        ),
        ScoreFactor(
            factor_name="interview_readiness",
            factor_value=interview_readiness.value * settings.weight_interview_readiness,
            weight=settings.weight_interview_readiness,
            description=f"Interview Ready ({interview_readiness.value}/100 × {settings.weight_interview_readiness:.0%})",
            event_count=interview_readiness.events_considered
        ),
        ScoreFactor(
            factor_name="professional_maturity",
            factor_value=professional_maturity.value * settings.weight_professional_maturity,
            weight=settings.weight_professional_maturity,
            description=f"Professional ({professional_maturity.value}/100 × {settings.weight_professional_maturity:.0%})",
            event_count=professional_maturity.events_considered
        ),
    ]
    
    total_events = (
        engagement.events_considered +
        learning_velocity.events_considered +
        commitment.events_considered +
        interview_readiness.events_considered +
        professional_maturity.events_considered
    )
    
    return ScoreResult(
        value=overall_score,
        confidence=round(weighted_confidence, 2),
        factors=factors,
        events_considered=total_events
    )


def assign_tier(
    overall_score: int,
    tier_1_threshold: int = 80,
    tier_3_threshold: int = 40
) -> int:
    """
    Assign profile tier based on overall capability score.
    
    For MVP, uses fixed thresholds:
    - Tier 1: score >= 80 (top performers)
    - Tier 2: 40 <= score < 80 (average)
    - Tier 3: score < 40 (needs development)
    
    Future: Use percentile-based thresholds computed from population.
    
    Returns:
        Tier as integer (1, 2, or 3)
    """
    if overall_score >= tier_1_threshold:
        return 1
    elif overall_score >= tier_3_threshold:
        return 2
    else:
        return 3
