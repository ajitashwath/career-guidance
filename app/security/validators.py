"""
Input Validation and Sanitization Utilities.

Provides validators for:
- Email addresses
- UUIDs
- String sanitization (XSS prevention)
- Length limits
- Pattern matching
"""

import re
import uuid
from typing import Optional

import bleach
from pydantic import EmailStr, field_validator, Field
from pydantic.functional_validators import AfterValidator
from typing_extensions import Annotated


# Regex patterns
UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
SAFE_STRING_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-_.,!?()]+$')


def validate_uuid(v: str) -> str:
    """
    Validate UUID format.
    
    Args:
        v: String to validate
        
    Returns:
        Valid UUID string
        
    Raises:
        ValueError: If not a valid UUID
    """
    try:
        uuid.UUID(v)
        return v
    except (ValueError, AttributeError):
        raise ValueError(f"Invalid UUID format: {v}")


def sanitize_string(v: str, max_length: int = 1000) -> str:
    """
    Sanitize string input to prevent XSS and injection.
    
    Args:
        v: String to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not v:
        return v
    
    # Trim to max length
    v = v[:max_length]
    
    # Remove HTML tags and scripts
    v = bleach.clean(v, tags=[], strip=True)
    
    # Decode HTML entities
    import html
    v = html.unescape(v)
    
    # Normalize whitespace
    v = " ".join(v.split())
    
    return v.strip()


def validate_no_sql_injection(v: str) -> str:
    """
    Check for SQL injection patterns.
    
    Args:
        v: String to check
        
    Returns:
        Original string if safe
        
    Raises:
        ValueError: If SQL injection detected
    """
    if not v:
        return v
    
    # Common SQL injection patterns
    sql_patterns = [
        r"(\bOR\b|\bAND\b)\s+\d+\s*=\s*\d+",
        r";\s*DROP\s+TABLE",
        r";\s*DELETE\s+FROM",
        r"UNION\s+SELECT",
        r"--\s*$",
        r"\/\*.*\*\/",
        r"xp_cmdshell",
    ]
    
    for pattern in sql_patterns:
        if re.search(pattern, v, re.IGNORECASE):
            raise ValueError("Input contains potentially unsafe SQL patterns")
    
    return v


def validate_url(v: Optional[str]) -> Optional[str]:
    """
    Validate URL format and safety.
    
    Args:
        v: URL string
        
    Returns:
        Valid URL
        
    Raises:
        ValueError: If URL is invalid or unsafe
    """
    if not v:
        return v
    
    # Allow only http/https
    if not v.startswith(('http://', 'https://')):
        raise ValueError("URL must start with http:// or https://")
    
    # Block localhost and private IPs (SSRF prevention)
    parsed_url = v.lower()
    if any(x in parsed_url for x in ['localhost', '127.0.0.1', '0.0.0.0', '::1', '192.168.', '10.', '172.16.']):
        raise ValueError("URLs pointing to private networks are not allowed")
    
    return v


# Annotated types for common validations
SafeString = Annotated[str, AfterValidator(lambda v: sanitize_string(v, 1000))]
ShortString = Annotated[str, AfterValidator(lambda v: sanitize_string(v, 255))]
LongText = Annotated[str, AfterValidator(lambda v: sanitize_string(v, 10000))]
ValidUUID = Annotated[str, AfterValidator(validate_uuid)]
SafeURL = Annotated[Optional[str], AfterValidator(validate_url)]


class SecureBaseModel:
    """
    Base model with security validators.
    
    Use this as a mixin for Pydantic models that need input sanitization.
    """
    
    @field_validator('*', mode='before')
    @classmethod
    def sanitize_strings(cls, v):
        """Automatically sanitize all string fields."""
        if isinstance(v, str):
            return sanitize_string(v)
        return v
