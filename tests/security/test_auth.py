"""
Authentication security tests.

Tests for:
- JWT token validation
- Token expiration
- Invalid token handling
- Missing/malformed tokens
"""

import pytest
from fastapi.test import TestClient
from jose import jwt
from datetime import datetime, timedelta

from app.main import app
from app.core.config import get_settings


client = TestClient(app)
settings = get_settings()


def test_missing_auth_token():
    """Test that endpoints reject missing auth tokens."""
    response = client.get("/students/me")
    assert response.status_code == 403  # HTTPBearer returns 403 for missing auth


def test_invalid_auth_token():
    """Test that invalid tokens are rejected."""
    response = client.get(
        "/students/me",
        headers={"Authorization": "Bearer invalid_token_here"}
    )
    assert response.status_code == 401
    assert "Invalid authentication token" in response.json().get("detail", "")


def test_expired_token():
    """Test that expired tokens are rejected."""
    # Create an expired token
    expired_payload = {
        "sub": "00000000-0000-0000-0000-000000000001",
        "email": "test@example.com",
        "aud": "authenticated",
        "exp": int((datetime.utcnow() - timedelta(hours=1)).timestamp()),  # Expired 1 hour ago
        "iat": int((datetime.utcnow() - timedelta(hours=2)).timestamp()),
    }
    
    expired_token = jwt.encode(
        expired_payload,
        settings.supabase_jwt_secret,
        algorithm="HS256"
    )
    
    response = client.get(
        "/students/me",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    
    assert response.status_code == 401
    assert "expired" in response.json().get("detail", "").lower()


def test_malformed_token():
    """Test that malformed tokens are rejected."""
    response = client.get(
        "/students/me",
        headers={"Authorization": "Bearer not.a.jwt"}
    )
    assert response.status_code == 401


def test_wrong_algorithm_token():
    """Test that tokens signed with wrong algorithm are rejected."""
    # Try to create token with HS512 instead of HS256
    payload = {
        "sub": "00000000-0000-0000-0000-000000000001",
        "email": "test@example.com",
        "aud": "authenticated",
        "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
        "iat": int(datetime.utcnow().timestamp()),
    }
    
    wrong_algo_token = jwt.encode(
        payload,
        settings.supabase_jwt_secret,
        algorithm="HS512"  # Wrong algorithm
    )
    
    response = client.get(
        "/students/me",
        headers={"Authorization": f"Bearer {wrong_algo_token}"}
    )
    
    assert response.status_code == 401


def test_wrong_audience_token():
    """Test that tokens with wrong audience are rejected."""
    payload = {
        "sub": "00000000-0000-0000-0000-000000000001",
        "email": "test@example.com",
        "aud": "wrong_audience",  # Wrong audience
        "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
        "iat": int(datetime.utcnow().timestamp()),
    }
    
    wrong_aud_token = jwt.encode(
        payload,
        settings.supabase_jwt_secret,
        algorithm="HS256"
    )
    
    response = client.get(
        "/students/me",
        headers={"Authorization": f"Bearer {wrong_aud_token}"}
    )
    
    assert response.status_code == 401


@pytest.mark.skip(reason="Requires valid Supabase credentials and test user")
def test_valid_token_accepted():
    """Test that valid tokens are accepted (requires test setup)."""
    # This would require creating a valid Supabase user and token
    pass
