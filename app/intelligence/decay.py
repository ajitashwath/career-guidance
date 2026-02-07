"""
Time-based decay functions for event scoring.

Decay functions determine how much weight an event contributes based on its age.
More recent events have higher impact on scores.

All functions return a multiplier between 0.0 and 1.0.
"""

import math
from datetime import datetime, timezone


def exponential_decay(
    event_timestamp: datetime,
    half_life_days: int = 30,
    reference_time: datetime | None = None
) -> float:
    """
    Calculate exponential decay factor for an event.
    
    Events lose half their weight every `half_life_days` days.
    This models the intuition that recent activity is more predictive
    of current capability than older activity.
    
    Args:
        event_timestamp: When the event occurred
        half_life_days: Days for weight to decay by half (default: 30)
        reference_time: Current time for comparison (default: now)
        
    Returns:
        Decay multiplier between 0.0 and 1.0
        
    Example:
        - Event from today: 1.0
        - Event from 30 days ago (half_life=30): 0.5
        - Event from 60 days ago (half_life=30): 0.25
        - Event from 90 days ago (half_life=30): 0.125
    """
    if reference_time is None:
        reference_time = datetime.now(timezone.utc)
    
    # Ensure both timestamps are timezone-aware
    if event_timestamp.tzinfo is None:
        event_timestamp = event_timestamp.replace(tzinfo=timezone.utc)
    if reference_time.tzinfo is None:
        reference_time = reference_time.replace(tzinfo=timezone.utc)
    
    # Calculate age in days
    age_delta = reference_time - event_timestamp
    age_days = age_delta.total_seconds() / (24 * 60 * 60)
    
    # Don't give bonus for future events
    if age_days < 0:
        age_days = 0
    
    # Exponential decay formula: 0.5 ^ (age / half_life)
    decay_factor = math.pow(0.5, age_days / half_life_days)
    
    return decay_factor


def recency_bonus(
    event_timestamp: datetime,
    bonus_hours: int = 48,
    max_bonus: float = 0.2,
    reference_time: datetime | None = None
) -> float:
    """
    Calculate bonus multiplier for very recent events.
    
    Events within the last `bonus_hours` receive a linear bonus
    that decreases to 0 as they age beyond that window.
    
    This encourages fresh activity and rewards users who are
    actively engaged right now.
    
    Args:
        event_timestamp: When the event occurred
        bonus_hours: Window for receiving bonus (default: 48 hours)
        max_bonus: Maximum bonus at time 0 (default: 0.2 = 20%)
        reference_time: Current time for comparison
        
    Returns:
        Bonus multiplier between 0.0 and max_bonus
        
    Example (max_bonus=0.2, bonus_hours=48):
        - Event from just now: 0.2
        - Event from 24 hours ago: 0.1
        - Event from 48 hours ago: 0.0
        - Event from 72 hours ago: 0.0
    """
    if reference_time is None:
        reference_time = datetime.now(timezone.utc)
    
    # Ensure timezone awareness
    if event_timestamp.tzinfo is None:
        event_timestamp = event_timestamp.replace(tzinfo=timezone.utc)
    if reference_time.tzinfo is None:
        reference_time = reference_time.replace(tzinfo=timezone.utc)
    
    # Calculate age in hours
    age_delta = reference_time - event_timestamp
    age_hours = age_delta.total_seconds() / 3600
    
    # No bonus for old events or future events
    if age_hours < 0 or age_hours > bonus_hours:
        return 0.0
    
    # Linear decay of bonus
    bonus = max_bonus * (1.0 - (age_hours / bonus_hours))
    
    return bonus


def consistency_multiplier(
    streak_days: int,
    max_multiplier: float = 1.5,
    ramp_up_days: int = 14
) -> float:
    """
    Calculate multiplier based on activity consistency.
    
    Users with longer active streaks get higher multipliers,
    rewarding sustained engagement over sporadic bursts.
    
    Args:
        streak_days: Current consecutive active days
        max_multiplier: Maximum multiplier at full ramp-up (default: 1.5)
        ramp_up_days: Days to reach max multiplier (default: 14)
        
    Returns:
        Multiplier between 1.0 and max_multiplier
        
    Example (max=1.5, ramp=14):
        - 0 day streak: 1.0
        - 7 day streak: 1.25
        - 14+ day streak: 1.5
    """
    if streak_days <= 0:
        return 1.0
    
    # Linear ramp-up to max
    ramp_progress = min(streak_days / ramp_up_days, 1.0)
    multiplier = 1.0 + (max_multiplier - 1.0) * ramp_progress
    
    return multiplier


def calculate_weighted_event_value(
    event_timestamp: datetime,
    base_value: float,
    half_life_days: int = 30,
    include_recency_bonus: bool = True,
    streak_days: int = 0,
    reference_time: datetime | None = None
) -> float:
    """
    Calculate the full weighted value of an event.
    
    Combines:
    1. Base value of the event type
    2. Exponential decay based on age
    3. Recency bonus for very recent events
    4. Consistency multiplier based on streak
    
    Args:
        event_timestamp: When the event occurred
        base_value: Inherent value of this event type (e.g., 10 points)
        half_life_days: Decay half-life
        include_recency_bonus: Whether to apply recency bonus
        streak_days: Current user streak for consistency multiplier
        reference_time: Reference time for decay calculations
        
    Returns:
        Final weighted value of the event
    """
    # Base decay
    decay = exponential_decay(event_timestamp, half_life_days, reference_time)
    value = base_value * decay
    
    # Recency bonus (additive)
    if include_recency_bonus:
        bonus = recency_bonus(event_timestamp, reference_time=reference_time)
        value = value * (1.0 + bonus)
    
    # Consistency multiplier
    if streak_days > 0:
        multiplier = consistency_multiplier(streak_days)
        value = value * multiplier
    
    return value
