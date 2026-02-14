import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.db.supabase import close_supabase_client

from app.api.students import router as students_router
from app.api.events import router as events_router
from app.api.recruiters import router as recruiters_router
from app.api.admin import router as admin_router
from app.api.ai import router as ai_router
from app.api.interview import router as interview_router

# Security middleware
from app.middleware.rate_limiting import limiter, rate_limit_exceeded_handler
from app.middleware.audit_logging import AuditLoggingMiddleware
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from slowapi.errors import RateLimitExceeded

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Know More Backend...")
    settings = get_settings()
    logger.info(f"Scoring version: {settings.scoring_version}")
    logger.info(f"Event window: {settings.event_window_days} days")
    
    yield
    logger.info("Shutting down...")
    await close_supabase_client()
    logger.info("Cleanup complete")

app = FastAPI(
    title="Career Intelligence API",
    version="1.0.0",
    lifespan=lifespan,
)

# Security settings
settings = get_settings()

# Add security middleware (order matters - first added = outermost)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(AuditLoggingMiddleware)

# CORS with explicit origin whitelist (SECURITY FIX)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,  # ✅ FIXED: No more allow_origins=["*"]
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

app.include_router(
    students_router,
    prefix="/students",
    tags=["Students"]
)

app.include_router(
    events_router,
    prefix="/events",
    tags=["Events"]
)

app.include_router(
    recruiters_router,
    prefix="/recruiters",
    tags=["Recruiters"]
)

app.include_router(
    admin_router,
    prefix="/admin",
    tags=["Admin"]
)

app.include_router(
    ai_router,
    prefix="/ai",
    tags=["AI"]
)

app.include_router(
    interview_router,
    prefix="/interview",
    tags=["Voice Interview"]
)

@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0"
    }


@app.get("/", tags=["System"])
async def root():
    return {
        "name": "Career Intelligence API",
        "version": "1.0.0",
        "docs": "/docs"
    }
