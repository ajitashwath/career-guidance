import logging
from uuid import UUID

from app.intelligence.scoring import full_score_recomputation

logger = logging.getLogger(__name__)


async def trigger_score_recomputation(user_id: UUID) -> None:
    """
    Background task to recompute scores after event ingestion.
    
    This function is designed to be called from FastAPI BackgroundTasks:
    
        @router.post("/events")
        async def create_event(
            ...,
            background_tasks: BackgroundTasks
        ):
            # Insert event
            ...
            # Trigger background recomputation
            background_tasks.add_task(trigger_score_recomputation, user_id)
    
    Current implementation: Direct async execution
    Future: Queue to Celery/Temporal for scalability
    
    Args:
        user_id: User whose scores need recomputation
    """
    try:
        logger.info(f"Starting score recomputation for user {user_id}")
        
        scores = await full_score_recomputation(user_id)
        
        logger.info(
            f"Score recomputation complete for user {user_id}: "
            f"overall={scores.overall_capability.value}, "
            f"tier={scores.tier.value}"
        )
        
    except Exception as e:
        logger.error(
            f"Score recomputation failed for user {user_id}: {str(e)}",
            exc_info=True
        )


async def batch_recompute_scores(user_ids: list[UUID]) -> dict:
    """
    Batch recompute scores for multiple users.
    
    Used for:
    - Admin bulk recomputation
    - Scoring version migration
    - Daily/weekly scheduled jobs
    
    Args:
        user_ids: List of users to recompute
        
    Returns:
        Results summary with success/failure counts
    """
    results = {
        "total": len(user_ids),
        "success": 0,
        "failed": 0,
        "failures": []
    }
    
    for user_id in user_ids:
        try:
            await trigger_score_recomputation(user_id)
            results["success"] += 1
        except Exception as e:
            results["failed"] += 1
            results["failures"].append({
                "user_id": str(user_id),
                "error": str(e)
            })
    
    logger.info(
        f"Batch recomputation complete: "
        f"{results['success']}/{results['total']} succeeded"
    )
    
    return results


async def scheduled_daily_recompute() -> dict:
    """
    Scheduled job to recompute scores for all active users.
    
    "Active" = users with events in the last 7 days.
    
    This ensures scores stay fresh even for users who haven't
    triggered an event today. Important for:
    - Decay being properly applied
    - Consistency in recruiter searches
    - Tier recalculation with updated population data
    
    Should be called from a scheduler (e.g., APScheduler, cron).
    """
    from datetime import datetime, timezone, timedelta
    from app.db.supabase import get_supabase_client
    from app.db.queries import TABLE_USER_EVENTS
    
    client = get_supabase_client()
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)

    response = (
        client.table(TABLE_USER_EVENTS)
        .select("user_id")
        .gte("created_at", cutoff.isoformat())
        .execute()
    )

    user_ids = list(set(UUID(row["user_id"]) for row in response.data))    
    logger.info(f"Daily recompute: found {len(user_ids)} active users")
    return await batch_recompute_scores(user_ids)
