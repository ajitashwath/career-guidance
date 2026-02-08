"""
Rate Limiting Middleware using SlowAPI with Redis backend.

Implements per-endpoint rate limiting:
- Authentication: 5 req/min
- LLM/AI endpoints: 10 req/hour
- Standard API: 60 req/min
- Admin: 30 req/min

Usage:
    from app.middleware.rate_limiting import limiter, rate_limit_exceeded_handler
    
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
"""

import redis.asyncio as redis
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import get_settings


def get_redis_client():
    """Get Redis client for rate limiting storage."""
    settings = get_settings()
    
    # Use Redis if available, otherwise in-memory (development only)
    redis_url = getattr(settings, 'redis_url', None)
    
    if redis_url:
        return redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True
        )
    return None  # SlowAPI will use in-memory storage


# Initialize limiter with Redis backend
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=getattr(get_settings(), 'redis_url', 'memory://'),
    default_limits=["60/minute"],  # Default limit for all endpoints
    headers_enabled=True,  # Send rate limit headers
)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Custom handler for rate limit exceeded errors.
    
    Returns a standardized JSON response with retry-after header.
    """
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please try again later.",
            "retry_after": exc.retry_after if hasattr(exc, 'retry_after') else None
        },
        headers={"Retry-After": str(int(exc.retry_after))} if hasattr(exc, 'retry_after') else {}
    )


# Rate limit decorators for different endpoint categories

# Authentication endpoints (stricter)
auth_limiter = "5/minute"

# LLM/AI endpoints (very strict to prevent cost abuse)
llm_limiter = "10/hour, 3/minute"

# Standard API endpoints
standard_limiter = "60/minute, 1000/hour"

# Admin endpoints (moderate)
admin_limiter = "30/minute"

# Read-only recruiter endpoints
recruiter_read_limiter = "100/minute"

# Write operations (stricter)
write_limiter = "30/minute"
