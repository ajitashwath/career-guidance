"""
Tests for intelligence scoring logic.
"""

import pytest
from datetime import datetime, timezone, timedelta

from app.intelligence.decay import (
    exponential_decay,
    recency_bonus,
    consistency_multiplier,
    calculate_weighted_event_value,
)
from app.intelligence.aggregators import (
    compute_engagement_score,
    compute_learning_velocity_score,
    compute_commitment_score,
    compute_interview_readiness_score,
    compute_professional_maturity_score,
    compute_overall_capability,
    assign_tier,
)


class TestDecayFunctions:
    """Tests for time-based decay functions."""
    
    def test_exponential_decay_current_event(self):
        """Event from now should have full weight."""
        now = datetime.now(timezone.utc)
        decay = exponential_decay(now, half_life_days=30, reference_time=now)
        assert abs(decay - 1.0) < 0.01
    
    def test_exponential_decay_half_life(self):
        """Event from half-life ago should have 0.5 weight."""
        now = datetime.now(timezone.utc)
        event_time = now - timedelta(days=30)
        decay = exponential_decay(event_time, half_life_days=30, reference_time=now)
        assert abs(decay - 0.5) < 0.01
    
    def test_exponential_decay_double_half_life(self):
        """Event from 2x half-life ago should have 0.25 weight."""
        now = datetime.now(timezone.utc)
        event_time = now - timedelta(days=60)
        decay = exponential_decay(event_time, half_life_days=30, reference_time=now)
        assert abs(decay - 0.25) < 0.01
    
    def test_recency_bonus_recent_event(self):
        """Very recent event should get max bonus."""
        now = datetime.now(timezone.utc)
        bonus = recency_bonus(now, bonus_hours=48, max_bonus=0.2, reference_time=now)
        assert abs(bonus - 0.2) < 0.01
    
    def test_recency_bonus_old_event(self):
        """Old event should get no bonus."""
        now = datetime.now(timezone.utc)
        event_time = now - timedelta(hours=72)
        bonus = recency_bonus(event_time, bonus_hours=48, max_bonus=0.2, reference_time=now)
        assert bonus == 0.0
    
    def test_consistency_multiplier_no_streak(self):
        """No streak should give multiplier of 1.0."""
        mult = consistency_multiplier(0)
        assert mult == 1.0
    
    def test_consistency_multiplier_max_streak(self):
        """Max streak should give max multiplier."""
        mult = consistency_multiplier(14, max_multiplier=1.5, ramp_up_days=14)
        assert abs(mult - 1.5) < 0.01


class TestAggregators:
    """Tests for score aggregation functions."""
    
    def test_engagement_score_no_events(self):
        """No events should give zero score."""
        result = compute_engagement_score([])
        assert result.value == 0
        assert result.confidence == 0.0
        assert result.events_considered == 0
    
    def test_engagement_score_with_events(self, sample_events):
        """Events should contribute to score."""
        result = compute_engagement_score(sample_events)
        assert result.value >= 0
        assert result.value <= 100
        assert result.events_considered >= 0
    
    def test_learning_velocity_score(self, sample_events):
        """Learning events should contribute to learning velocity."""
        result = compute_learning_velocity_score(sample_events)
        assert result.value >= 0
        assert result.value <= 100
    
    def test_overall_capability_weighted(self, sample_events):
        """Overall capability should be weighted sum."""
        now = datetime.now(timezone.utc)
        
        engagement = compute_engagement_score(sample_events, now)
        learning = compute_learning_velocity_score(sample_events, now)
        commitment = compute_commitment_score(sample_events, now)
        interview = compute_interview_readiness_score(sample_events, now)
        professional = compute_professional_maturity_score(sample_events, now)
        
        overall = compute_overall_capability(
            engagement, learning, commitment, interview, professional
        )
        
        assert overall.value >= 0
        assert overall.value <= 100
        assert len(overall.factors) == 5  # One per dimension


class TestTierAssignment:
    """Tests for tier assignment logic."""
    
    def test_tier_1_high_score(self):
        """High score should be Tier 1."""
        tier = assign_tier(85)
        assert tier == 1
    
    def test_tier_2_medium_score(self):
        """Medium score should be Tier 2."""
        tier = assign_tier(50)
        assert tier == 2
    
    def test_tier_3_low_score(self):
        """Low score should be Tier 3."""
        tier = assign_tier(30)
        assert tier == 3
    
    def test_tier_boundary_80(self):
        """Score of 80 should be Tier 1."""
        tier = assign_tier(80)
        assert tier == 1
    
    def test_tier_boundary_40(self):
        """Score of 40 should be Tier 2."""
        tier = assign_tier(40)
        assert tier == 2
