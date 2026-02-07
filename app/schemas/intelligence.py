"""
Pydantic schemas for intelligence scoring.

These schemas support:
- Explainable score breakdowns
- Versioned snapshots for auditing
- Confidence bands for transparency
- Tier assignments
"""

from datetime import datetime
from decimal import Decimal
from enum import IntEnum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ProfileTier(IntEnum):
    """
    Profile tiers based on overall capability percentile.
    
    Tier 1: Top 20% (most capable)
    Tier 2: Middle 60% (average)
    Tier 3: Bottom 20% (needs development)
    """
    TIER_1 = 1
    TIER_2 = 2
    TIER_3 = 3


class ScoreFactor(BaseModel):
    """
    Individual factor contributing to a score.
    
    Used for explainability - shows users WHY they have a score.
    """
    factor_name: str = Field(..., description="Name of the contributing factor")
    factor_value: float = Field(..., description="Contribution to score (0-100)")
    weight: float = Field(..., description="Weight applied to this factor")
    description: str = Field(..., description="Human-readable explanation")
    event_count: int = Field(..., description="Number of events considered")


class ScoreResult(BaseModel):
    """
    Result of computing a single score dimension.
    
    Includes the score value, confidence level, and explainability factors.
    """
    value: int = Field(..., ge=0, le=100, description="Score value 0-100")
    confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description="Confidence in score (more events = higher confidence)"
    )
    factors: list[ScoreFactor] = Field(
        default_factory=list,
        description="Factors contributing to this score"
    )
    events_considered: int = Field(
        ..., ge=0,
        description="Total events analyzed for this score"
    )
    
    @property
    def confidence_band(self) -> tuple[int, int]:
        """
        Calculate confidence band around the score.
        
        Higher confidence = narrower band.
        Returns (lower_bound, upper_bound).
        """
        # Band width is inversely proportional to confidence
        # At 100% confidence, band width = 0
        # At 0% confidence, band width = 20 (±10)
        band_width = int(20 * (1 - self.confidence))
        half_band = band_width // 2
        
        lower = max(0, self.value - half_band)
        upper = min(100, self.value + half_band)
        
        return (lower, upper)


class IntelligenceScores(BaseModel):
    """
    Complete set of intelligence scores for a user.
    
    All scores are 0-100 integers with confidence levels.
    """
    engagement: ScoreResult
    learning_velocity: ScoreResult
    commitment: ScoreResult
    interview_readiness: ScoreResult
    professional_maturity: ScoreResult
    overall_capability: ScoreResult
    tier: ProfileTier


class IntelligenceSnapshot(BaseModel):
    """
    Versioned snapshot of a user's intelligence scores.
    
    Snapshots are immutable records for auditing and historical analysis.
    They enable:
    - Score trend analysis
    - Algorithm debugging
    - Bias detection
    - Historical recomputation
    """
    id: UUID
    user_id: UUID
    
    # Individual scores (0-100)
    engagement_score: int = Field(..., ge=0, le=100)
    learning_velocity_score: int = Field(..., ge=0, le=100)
    commitment_score: int = Field(..., ge=0, le=100)
    interview_readiness_score: int = Field(..., ge=0, le=100)
    professional_maturity_score: int = Field(..., ge=0, le=100)
    
    # Composite score
    overall_capability_score: int = Field(..., ge=0, le=100)
    
    # Tier assignment
    profile_tier: ProfileTier
    
    # Metadata
    scoring_version: str = Field(..., description="Version of scoring algorithm used")
    confidence_level: Decimal = Field(..., ge=0, le=1, description="Overall confidence 0-1")
    computed_at: datetime
    
    class Config:
        from_attributes = True


class IntelligenceSnapshotCreate(BaseModel):
    """Schema for creating a new intelligence snapshot."""
    user_id: UUID
    engagement_score: int = Field(..., ge=0, le=100)
    learning_velocity_score: int = Field(..., ge=0, le=100)
    commitment_score: int = Field(..., ge=0, le=100)
    interview_readiness_score: int = Field(..., ge=0, le=100)
    professional_maturity_score: int = Field(..., ge=0, le=100)
    overall_capability_score: int = Field(..., ge=0, le=100)
    profile_tier: int = Field(..., ge=1, le=3)
    scoring_version: str
    confidence_level: Decimal = Field(..., ge=0, le=1)


class IntelligenceSummary(BaseModel):
    """
    Lightweight intelligence summary for recruiter views.
    
    Provides scores without full explainability factors.
    """
    engagement_score: int
    learning_velocity_score: int
    commitment_score: int
    interview_readiness_score: int
    professional_maturity_score: int
    overall_capability_score: int
    profile_tier: ProfileTier
    confidence_level: float
    last_computed: datetime


class IntelligenceTimeline(BaseModel):
    """
    Historical intelligence snapshots for trend analysis.
    """
    user_id: UUID
    snapshots: list[IntelligenceSnapshot]
    trend_direction: str = Field(
        ...,
        description="Overall trend: 'improving', 'stable', 'declining'"
    )
    change_last_30_days: int = Field(
        ...,
        description="Change in overall capability score over 30 days"
    )


class ScoreDebugInfo(BaseModel):
    """
    Detailed debug information for admin score analysis.
    
    Includes raw event counts and intermediate calculations.
    """
    user_id: UUID
    scoring_version: str
    computed_at: datetime
    
    # Raw event counts by category
    event_counts: dict[str, int]
    
    # Individual dimension calculations
    engagement_breakdown: ScoreResult
    learning_velocity_breakdown: ScoreResult
    commitment_breakdown: ScoreResult
    interview_readiness_breakdown: ScoreResult
    professional_maturity_breakdown: ScoreResult
    
    # Weight application
    weights_applied: dict[str, float]
    
    # Final scores
    final_scores: IntelligenceScores
    
    # Configuration at time of computation
    config_snapshot: dict
