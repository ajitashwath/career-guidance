"""
Events API routes.

Handles event ingestion and triggers background score recomputation.
Students emit events through this API.
"""

from typing import Annotated
from fastapi import APIRouter, BackgroundTasks, Depends, status
from starlette.requests import Request

# Security Imports
from app.middleware.rate_limiting import limiter, standard_limiter, write_limiter

from app.core.auth import require_student, CurrentUser
from app.db.supabase import insert_row
from app.db.queries import TABLE_USER_EVENTS
from app.schemas.events import (
    EventCreate,
    EventResponse,
    EventType,
    EventTypesResponse,
    EVENT_CATEGORIES,
)
from app.workers.recompute_scores import trigger_score_recomputation

router = APIRouter()


@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(write_limiter)
async def emit_event(
    request: Request,
    event: EventCreate,
    user: Annotated[CurrentUser, Depends(require_student)],
    background_tasks: BackgroundTasks
):
    """
    Emit a user event.
    
    Events are the primary input to the intelligence scoring system.
    After ingestion, a background task recomputes the user's scores.
    
    **Important**: Events are append-only. Once created, they cannot be
    modified or deleted. This ensures audit integrity.
    """
    # Prepare event data
    event_data = {
        "user_id": str(user.id),
        "event_type": event.event_type.value,
        "event_payload": event.event_payload,
    }
    
    # Insert event (synchronous - fast operation)
    created_event = await insert_row(TABLE_USER_EVENTS, event_data)
    
    # Trigger background score recomputation
    # This does NOT block the response
    background_tasks.add_task(trigger_score_recomputation, user.id)
    
    return created_event


@router.get("/types", response_model=EventTypesResponse)
@limiter.limit(standard_limiter)
async def list_event_types(
    request: Request
):
    """
    List all valid event types grouped by scoring category.
    
    Use this to discover available event types and understand
    which category each event contributes to.
    """
    return EventTypesResponse(
        engagement=[et.value for et in EVENT_CATEGORIES["engagement"]],
        learning_velocity=[et.value for et in EVENT_CATEGORIES["learning_velocity"]],
        commitment=[et.value for et in EVENT_CATEGORIES["commitment"]],
        interview_readiness=[et.value for et in EVENT_CATEGORIES["interview_readiness"]],
        professional_maturity=[et.value for et in EVENT_CATEGORIES["professional_maturity"]],
    )
