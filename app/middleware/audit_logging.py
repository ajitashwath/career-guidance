"""
Audit Logging Middleware.

Logs all API requests with:
- User ID (if authenticated)
- IP address
- Endpoint
- Method
- Status code
- Response time
- Request/response body (in debug mode)

Special logging for:
- Failed authentication attempts
- Admin actions
- Data modification operations
"""

import time
import logging
import json
from typing import Callable
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from pythonjsonlogger import jsonlogger

from app.core.config import get_settings


# Configure structured JSON logging
logger = logging.getLogger("audit")
log_handler = logging.StreamHandler()

# JSON formatter for structured logs
formatter = jsonlogger.JsonFormatter(
    '%(timestamp)s %(level)s %(name)s %(message)s %(request_id)s %(user_id)s %(ip)s %(method)s %(path)s %(status_code)s %(duration_ms)s'
)
log_handler.setFormatter(formatter)
logger.addHandler(log_handler)
logger.setLevel(logging.INFO)


# PII fields to redact from logs
PII_FIELDS = {
    "password", "token", "secret", "api_key", "authorization",
    "email", "phone", "ssn", "credit_card", "full_name"
}


def redact_pii(data: dict) -> dict:
    """Redact PII from dictionary for logging."""
    if not isinstance(data, dict):
        return data
    
    redacted = {}
    for key, value in data.items():
        if any(pii_field in key.lower() for pii_field in PII_FIELDS):
            redacted[key] = "[REDACTED]"
        elif isinstance(value, dict):
            redacted[key] = redact_pii(value)
        elif isinstance(value, list):
            redacted[key] = [redact_pii(item) if isinstance(item, dict) else item for item in value]
        else:
            redacted[key] = value
    return redacted


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all API requests and responses.
    
    Logs are structured JSON for easy parsing by SIEM systems.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log audit trail."""
        settings = get_settings()
        
        # Generate unique request ID
        request_id = str(uuid4())
        request.state.request_id = request_id
        
        # Extract user info if authenticated
        user_id = None
        if hasattr(request.state, 'user'):
            user_id = str(request.state.user.id)
        
        # Get client IP (handle proxy headers)
        client_ip = request.client.host if request.client else None
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        # Start timer
        start_time = time.time()
        
        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
            error = None
        except Exception as e:
            status_code = 500
            error = str(e)
            raise
        finally:
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Log the request
            log_data = {
                "timestamp": time.time(),
                "level": "INFO" if status_code < 400 else "WARNING" if status_code < 500 else "ERROR",
                "request_id": request_id,
                "user_id": user_id,
                "ip": client_ip,
                "method": request.method,
                "path": request.url.path,
                "query_params": redact_pii(dict(request.query_params)) if request.query_params else None,
                "status_code": status_code,
                "duration_ms": duration_ms,
            }
            
            # Add error if present
            if error:
                log_data["error"] = error
            
            # Log request body for POST/PUT/PATCH (only in debug mode, redacted)
            if settings.debug and request.method in ("POST", "PUT", "PATCH"):
                try:
                    body = await request.body()
                    if body:
                        body_data = json.loads(body.decode())
                        log_data["request_body"] = redact_pii(body_data)
                except:
                    pass
            
            # Special logging for sensitive operations
            if request.url.path.startswith("/admin"):
                log_data["admin_action"] = True
                logger.warning("Admin action", extra=log_data)
            elif status_code == 401:
                log_data["auth_failure"] = True
                logger.warning("Authentication failed", extra=log_data)
            elif request.method in ("POST", "PUT", "PATCH", "DELETE"):
                log_data["data_modification"] = True
                logger.info("Data modification", extra=log_data)
            else:
                logger.info("API request", extra=log_data)
        
        return response


def log_security_event(event_type: str, details: dict):
    """
    Log a security-specific event.
    
    Args:
        event_type: Type of security event (e.g., "failed_login", "privilege_escalation")
        details: Dictionary with event details
    """
    logger.warning(
        f"Security event: {event_type}",
        extra={
            "timestamp": time.time(),
            "level": "WARNING",
            "event_type": event_type,
            **redact_pii(details)
        }
    )
