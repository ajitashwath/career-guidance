"""
Application configuration using Pydantic Settings.

Configuration is loaded from environment variables with sensible defaults.
All scoring-related parameters are configurable for easy tuning without code changes.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Supabase settings are required for database and authentication.
    Scoring settings control the intelligence computation pipeline.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # ─────────────────────────────────────────────────────────────────────────
    # Supabase Configuration
    # ─────────────────────────────────────────────────────────────────────────
    supabase_url: str = Field(
        ...,
        description="Supabase project URL"
    )
    supabase_key: str = Field(
        ...,
        description="Supabase service role key (NOT anon key)"
    )
    supabase_jwt_secret: str = Field(
        ...,
        description="Supabase JWT secret for token verification"
    )
    
    # ─────────────────────────────────────────────────────────────────────────
    # Server Configuration
    # ─────────────────────────────────────────────────────────────────────────
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    debug: bool = Field(default=False, description="Enable debug mode")
    
    # ─────────────────────────────────────────────────────────────────────────
    # Scoring Configuration
    # ─────────────────────────────────────────────────────────────────────────
    scoring_version: str = Field(
        default="v1.0",
        description="Current scoring algorithm version for snapshot tracking"
    )
    event_window_days: int = Field(
        default=90,
        description="Number of days of events to consider for scoring"
    )
    decay_half_life_days: int = Field(
        default=30,
        description="Half-life for exponential decay of event weights"
    )
    
    # ─────────────────────────────────────────────────────────────────────────
    # Score Weights (must sum to 1.0)
    # ─────────────────────────────────────────────────────────────────────────
    weight_engagement: float = Field(
        default=0.15,
        description="Weight for engagement score in overall capability"
    )
    weight_learning_velocity: float = Field(
        default=0.20,
        description="Weight for learning velocity score"
    )
    weight_commitment: float = Field(
        default=0.20,
        description="Weight for commitment score"
    )
    weight_interview_readiness: float = Field(
        default=0.25,
        description="Weight for interview readiness score"
    )
    weight_professional_maturity: float = Field(
        default=0.20,
        description="Weight for professional maturity score"
    )
    
    # ─────────────────────────────────────────────────────────────────────────
    # LLM Configuration
    # ─────────────────────────────────────────────────────────────────────────
    llm_provider: Literal["openai", "anthropic", "google", "openrouter"] = Field(
        default="openrouter",
        description="LLM provider to use"
    )
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key"
    )
    openai_model: str = Field(
        default="gpt-4o-mini",
        description="OpenAI model to use"
    )
    anthropic_api_key: str = Field(
        default="",
        description="Anthropic API key"
    )
    anthropic_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="Anthropic model to use"
    )
    google_api_key: str = Field(
        default="",
        description="Google API key"
    )
    google_model: str = Field(
        default="gemini-2.0-flash",
        description="Google model to use"
    )
    openrouter_api_key: str = Field(
        default="",
        description="OpenRouter API key"
    )
    openrouter_model: str = Field(
        default="anthropic/claude-3.5-sonnet",
        description="OpenRouter model to use"
    )

    
    # ─────────────────────────────────────────────────────────────────────────
    # Security Configuration
    # ─────────────────────────────────────────────────────────────────────────
    allowed_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins (production should be explicit domains)"
    )
    redis_url: str = Field(
        default="redis://localhost:6379",
        description="Redis URL for rate limiting and caching"
    )
    jwt_token_expire_minutes: int = Field(
        default=60,
        description="JWT token expiration time in minutes"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7,
        description="Refresh token expiration time in days"
    )
    
    # ─────────────────────────────────────────────────────────────────────────
    # Tier Thresholds (percentile-based)
    # ─────────────────────────────────────────────────────────────────────────
    tier_1_percentile: int = Field(
        default=80,
        description="Minimum percentile for Tier 1 (top 20%)"
    )
    tier_2_percentile: int = Field(
        default=20,
        description="Minimum percentile for Tier 2 (middle 60%)"
    )
    
    @property
    def total_weights(self) -> float:
        """Verify weights sum to 1.0 for sanity checking."""
        return (
            self.weight_engagement +
            self.weight_learning_velocity +
            self.weight_commitment +
            self.weight_interview_readiness +
            self.weight_professional_maturity
        )
    
    def validate_weights(self) -> None:
        """Raise an error if weights don't sum to 1.0."""
        if abs(self.total_weights - 1.0) > 0.001:
            raise ValueError(
                f"Score weights must sum to 1.0, got {self.total_weights}"
            )


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    Uses lru_cache to ensure settings are only loaded once from environment.
    """
    settings = Settings()
    settings.validate_weights()
    return settings
