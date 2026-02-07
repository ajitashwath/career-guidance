"""
Pydantic schemas for user events (event sourcing).

Event types are strictly enumerated and validated.
Payloads are flexible JSONB with type-specific validators.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class EventType(str, Enum):
    """
    Valid event types for the intelligence system.
    
    Events are categorized by the type of signal they represent:
    - ENGAGEMENT: Profile activity and platform usage
    - LEARNING: Skill acquisition and course progress
    - COMMITMENT: Consistency and goal achievement
    - INTERVIEW_READINESS: Practice and preparation
    - PROFESSIONAL_MATURITY: Community and networking
    """
    
    # ─────────────────────────────────────────────────────────────────────────
    # Engagement Signals
    # ─────────────────────────────────────────────────────────────────────────
    PROFILE_VIEW = "profile_view"                    # Someone viewed profile
    PROFILE_UPDATE = "profile_update"                # User updated profile
    SKILL_ADDED = "skill_added"                      # New skill claimed
    SKILL_UPDATED = "skill_updated"                  # Skill details changed
    PROJECT_ADDED = "project_added"                  # New project added
    PROJECT_UPDATED = "project_updated"              # Project details updated
    CERTIFICATION_ADDED = "certification_added"      # New certification
    EDUCATION_ADDED = "education_added"              # Education entry added
    EXPERIENCE_ADDED = "experience_added"            # Work experience added
    RESUME_UPLOADED = "resume_uploaded"              # Resume file uploaded
    LINKEDIN_CONNECTED = "linkedin_connected"        # LinkedIn account linked
    GITHUB_CONNECTED = "github_connected"            # GitHub account linked
    
    # ─────────────────────────────────────────────────────────────────────────
    # Learning Signals
    # ─────────────────────────────────────────────────────────────────────────
    COURSE_STARTED = "course_started"                # Started a course
    COURSE_COMPLETED = "course_completed"            # Finished a course
    COURSE_PROGRESS = "course_progress"              # Made progress in course
    QUIZ_ATTEMPTED = "quiz_attempted"                # Took a quiz
    QUIZ_PASSED = "quiz_passed"                      # Passed a quiz
    RESOURCE_VIEWED = "resource_viewed"              # Viewed learning resource
    SKILL_VERIFIED = "skill_verified"                # Skill externally verified
    ASSESSMENT_COMPLETED = "assessment_completed"    # Completed skill assessment
    
    # ─────────────────────────────────────────────────────────────────────────
    # Commitment Signals
    # ─────────────────────────────────────────────────────────────────────────
    DAILY_LOGIN = "daily_login"                      # Logged in for the day
    STREAK_ACHIEVED = "streak_achieved"              # Reached login streak
    STREAK_BROKEN = "streak_broken"                  # Lost login streak
    GOAL_SET = "goal_set"                            # Set a career goal
    GOAL_UPDATED = "goal_updated"                    # Updated goal details
    GOAL_COMPLETED = "goal_completed"                # Completed a goal
    APPLICATION_SUBMITTED = "application_submitted"  # Applied to a job
    APPLICATION_WITHDRAWN = "application_withdrawn"  # Withdrew application
    INTERVIEW_SCHEDULED = "interview_scheduled"      # Interview scheduled
    
    # ─────────────────────────────────────────────────────────────────────────
    # Interview Readiness Signals
    # ─────────────────────────────────────────────────────────────────────────
    MOCK_INTERVIEW_STARTED = "mock_interview_started"
    MOCK_INTERVIEW_COMPLETED = "mock_interview_completed"
    FEEDBACK_RECEIVED = "feedback_received"          # Got interview feedback
    FEEDBACK_APPLIED = "feedback_applied"            # Applied feedback
    PRACTICE_SESSION = "practice_session"            # General practice
    BEHAVIORAL_PRACTICE = "behavioral_practice"      # Behavioral Q practice
    TECHNICAL_PRACTICE = "technical_practice"        # Technical Q practice
    MENTOR_SESSION = "mentor_session"                # Met with mentor
    
    # ─────────────────────────────────────────────────────────────────────────
    # Professional Maturity Signals
    # ─────────────────────────────────────────────────────────────────────────
    RECOMMENDATION_RECEIVED = "recommendation_received"
    RECOMMENDATION_REQUESTED = "recommendation_requested"
    ENDORSEMENT_GIVEN = "endorsement_given"          # Endorsed another user
    ENDORSEMENT_RECEIVED = "endorsement_received"    # Received endorsement
    COMMUNITY_CONTRIBUTION = "community_contribution"  # Forum/community help
    ARTICLE_PUBLISHED = "article_published"          # Published content
    NETWORKING_EVENT = "networking_event"            # Attended event
    MENTORED_PEER = "mentored_peer"                  # Helped another student


# Event type to category mapping for scoring
EVENT_CATEGORIES = {
    "engagement": [
        EventType.PROFILE_VIEW,
        EventType.PROFILE_UPDATE,
        EventType.SKILL_ADDED,
        EventType.SKILL_UPDATED,
        EventType.PROJECT_ADDED,
        EventType.PROJECT_UPDATED,
        EventType.CERTIFICATION_ADDED,
        EventType.EDUCATION_ADDED,
        EventType.EXPERIENCE_ADDED,
        EventType.RESUME_UPLOADED,
        EventType.LINKEDIN_CONNECTED,
        EventType.GITHUB_CONNECTED,
    ],
    "learning_velocity": [
        EventType.COURSE_STARTED,
        EventType.COURSE_COMPLETED,
        EventType.COURSE_PROGRESS,
        EventType.QUIZ_ATTEMPTED,
        EventType.QUIZ_PASSED,
        EventType.RESOURCE_VIEWED,
        EventType.SKILL_VERIFIED,
        EventType.ASSESSMENT_COMPLETED,
    ],
    "commitment": [
        EventType.DAILY_LOGIN,
        EventType.STREAK_ACHIEVED,
        EventType.STREAK_BROKEN,
        EventType.GOAL_SET,
        EventType.GOAL_UPDATED,
        EventType.GOAL_COMPLETED,
        EventType.APPLICATION_SUBMITTED,
        EventType.APPLICATION_WITHDRAWN,
        EventType.INTERVIEW_SCHEDULED,
    ],
    "interview_readiness": [
        EventType.MOCK_INTERVIEW_STARTED,
        EventType.MOCK_INTERVIEW_COMPLETED,
        EventType.FEEDBACK_RECEIVED,
        EventType.FEEDBACK_APPLIED,
        EventType.PRACTICE_SESSION,
        EventType.BEHAVIORAL_PRACTICE,
        EventType.TECHNICAL_PRACTICE,
        EventType.MENTOR_SESSION,
    ],
    "professional_maturity": [
        EventType.RECOMMENDATION_RECEIVED,
        EventType.RECOMMENDATION_REQUESTED,
        EventType.ENDORSEMENT_GIVEN,
        EventType.ENDORSEMENT_RECEIVED,
        EventType.COMMUNITY_CONTRIBUTION,
        EventType.ARTICLE_PUBLISHED,
        EventType.NETWORKING_EVENT,
        EventType.MENTORED_PEER,
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# Event Schemas
# ─────────────────────────────────────────────────────────────────────────────

class EventCreate(BaseModel):
    """
    Schema for creating a new event.
    
    Event payload is flexible JSONB but should follow conventions
    based on event type for proper scoring.
    """
    event_type: EventType = Field(..., description="Type of event being recorded")
    event_payload: Optional[dict[str, Any]] = Field(
        default=None,
        description="Optional event-specific data (e.g., skill_name, course_id)"
    )
    
    @field_validator("event_payload")
    @classmethod
    def validate_payload_size(cls, v: Optional[dict]) -> Optional[dict]:
        """Ensure payload isn't excessively large."""
        if v is not None:
            import json
            payload_str = json.dumps(v)
            # Limit to 10KB
            if len(payload_str) > 10240:
                raise ValueError("Event payload must be less than 10KB")
        return v


class EventResponse(BaseModel):
    """Event response with all fields."""
    id: UUID
    user_id: UUID
    event_type: EventType
    event_payload: Optional[dict[str, Any]]
    created_at: datetime
    
    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    """Paginated event list response."""
    events: list[EventResponse]
    total_count: int
    has_more: bool


class EventTypesResponse(BaseModel):
    """Response listing all valid event types grouped by category."""
    engagement: list[str]
    learning_velocity: list[str]
    commitment: list[str]
    interview_readiness: list[str]
    professional_maturity: list[str]


# ─────────────────────────────────────────────────────────────────────────────
# Event Payload Examples (for documentation)
# ─────────────────────────────────────────────────────────────────────────────

PAYLOAD_EXAMPLES = {
    EventType.SKILL_ADDED: {
        "skill_name": "Python",
        "proficiency_level": 4,
        "source": "profile_update"
    },
    EventType.COURSE_COMPLETED: {
        "course_id": "uuid-here",
        "course_name": "Machine Learning Fundamentals",
        "provider": "Coursera",
        "duration_hours": 40,
        "score": 92
    },
    EventType.MOCK_INTERVIEW_COMPLETED: {
        "session_id": "uuid-here",
        "interview_type": "behavioral",
        "duration_minutes": 30,
        "score": 78,
        "feedback_summary": "Good STAR format, needs more specific examples"
    },
    EventType.STREAK_ACHIEVED: {
        "streak_days": 7,
        "streak_type": "daily_activity"
    },
    EventType.GOAL_COMPLETED: {
        "goal_id": "uuid-here",
        "goal_type": "skill_acquisition",
        "goal_description": "Learn React.js basics",
        "days_to_complete": 14
    }
}
