"""
JWT Authentication and Role-Based Access Control.

This module provides:
- JWT token validation using Supabase Auth
- Role extraction from JWT claims
- Dependency injection for protected routes
- Role-specific access guards (student, recruiter, admin)

Security model:
- Tokens are validated against Supabase JWT secret
- Roles are embedded in JWT claims by Supabase Auth
- RLS policies in Postgres provide additional security layer
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, Field

from app.core.config import get_settings

# HTTP Bearer token extractor
security = HTTPBearer(auto_error=True)


class UserRole(str, Enum):
    """
    User roles in the system.
    
    Roles are hierarchical:
    - STUDENT: Can manage own profile and emit events
    - RECRUITER: Can view candidate profiles (read-only)
    - ADMIN: Full access including debug and recomputation
    """
    STUDENT = "student"
    RECRUITER = "recruiter"
    ADMIN = "admin"


class CurrentUser(BaseModel):
    """
    Authenticated user context extracted from JWT.
    
    This is injected into route handlers via dependency injection.
    Contains all information needed for RLS and authorization.
    """
    id: UUID = Field(..., description="User's Supabase Auth UUID")
    email: str = Field(..., description="User's email address")
    role: UserRole = Field(default=UserRole.STUDENT, description="User's role")
    
    # Optional metadata from claims
    full_name: Optional[str] = Field(default=None, description="User's full name")
    university_id: Optional[UUID] = Field(default=None, description="Associated university")


class TokenPayload(BaseModel):
    """JWT token payload structure from Supabase Auth."""
    sub: str  # User ID
    email: str
    role: Optional[str] = None
    exp: int  # Expiration timestamp
    aud: str  # Audience
    iat: int  # Issued at
    
    # Custom claims
    user_metadata: Optional[dict] = None
    app_metadata: Optional[dict] = None


def decode_token(token: str) -> TokenPayload:
    """
    Decode and validate a JWT token.
    
    Args:
        token: Raw JWT string from Authorization header
        
    Returns:
        TokenPayload with validated claims
        
    Raises:
        HTTPException: If token is invalid, expired, or malformed
    """
    settings = get_settings()
    
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated"
        )
        return TokenPayload(**payload)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )


def extract_role(payload: TokenPayload) -> UserRole:
    """
    Extract user role from JWT claims.
    
    Role priority:
    1. app_metadata.role (set by admin)
    2. user_metadata.role (set during signup)
    3. Default to STUDENT
    
    Args:
        payload: Decoded JWT token payload
        
    Returns:
        UserRole enum value
    """
    # Check app_metadata first (admin-assigned roles take priority)
    if payload.app_metadata and "role" in payload.app_metadata:
        role_str = payload.app_metadata["role"]
        try:
            return UserRole(role_str)
        except ValueError:
            pass
    
    # Check user_metadata
    if payload.user_metadata and "role" in payload.user_metadata:
        role_str = payload.user_metadata["role"]
        try:
            return UserRole(role_str)
        except ValueError:
            pass
    
    # Check direct role claim
    if payload.role:
        try:
            return UserRole(payload.role)
        except ValueError:
            pass
    
    # Default to student
    return UserRole.STUDENT


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> CurrentUser:
    """
    Dependency to get the current authenticated user.
    
    Usage:
        @router.get("/me")
        async def get_me(user: CurrentUser = Depends(get_current_user)):
            return user
            
    Returns:
        CurrentUser with validated identity and role
        
    Raises:
        HTTPException: If not authenticated or token invalid
    """
    token = credentials.credentials
    payload = decode_token(token)
    
    # Check expiration
    now = datetime.now(timezone.utc).timestamp()
    if payload.exp < now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Extract role
    role = extract_role(payload)
    
    # Build user context
    full_name = None
    if payload.user_metadata:
        full_name = payload.user_metadata.get("full_name")
    
    return CurrentUser(
        id=UUID(payload.sub),
        email=payload.email,
        role=role,
        full_name=full_name
    )


# ─────────────────────────────────────────────────────────────────────────────
# Role-Specific Dependencies
# ─────────────────────────────────────────────────────────────────────────────

async def require_student(
    user: Annotated[CurrentUser, Depends(get_current_user)]
) -> CurrentUser:
    """
    Require user to have STUDENT role.
    
    Note: Admins can also access student endpoints.
    """
    if user.role not in (UserRole.STUDENT, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required"
        )
    return user


async def require_recruiter(
    user: Annotated[CurrentUser, Depends(get_current_user)]
) -> CurrentUser:
    """
    Require user to have RECRUITER role.
    
    Note: Admins can also access recruiter endpoints.
    """
    if user.role not in (UserRole.RECRUITER, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Recruiter access required"
        )
    return user


async def require_admin(
    user: Annotated[CurrentUser, Depends(get_current_user)]
) -> CurrentUser:
    """
    Require user to have ADMIN role.
    
    This is the strictest check - only admins pass.
    """
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user
