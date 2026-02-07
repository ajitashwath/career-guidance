"""
Test configuration and fixtures.
"""

import pytest
from datetime import datetime, timezone


@pytest.fixture
def sample_events():
    """Sample events for testing scoring."""
    base_time = datetime.now(timezone.utc)
    
    return [
        {
            "id": "event-1",
            "user_id": "user-123",
            "event_type": "skill_added",
            "event_payload": {"skill_name": "Python", "proficiency_level": 4},
            "created_at": base_time.isoformat()
        },
        {
            "id": "event-2",
            "user_id": "user-123",
            "event_type": "course_completed",
            "event_payload": {"course_name": "ML Fundamentals", "score": 92},
            "created_at": base_time.isoformat()
        },
        {
            "id": "event-3",
            "user_id": "user-123",
            "event_type": "mock_interview_completed",
            "event_payload": {"interview_type": "behavioral", "score": 78},
            "created_at": base_time.isoformat()
        },
        {
            "id": "event-4",
            "user_id": "user-123",
            "event_type": "daily_login",
            "event_payload": {},
            "created_at": base_time.isoformat()
        },
        {
            "id": "event-5",
            "user_id": "user-123",
            "event_type": "recommendation_received",
            "event_payload": {"recommender": "Prof. Smith"},
            "created_at": base_time.isoformat()
        },
    ]
