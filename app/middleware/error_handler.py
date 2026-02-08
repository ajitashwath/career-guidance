"""
Error Handling Middleware.

Provides:
- Global exception handling
- Production vs debug error modes
- Generic error messages in production (no stack leaks)
- Detailed error logging (but not in responses)
"""

import logging
import traceback
from typing import Callable

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings


logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle exceptions globally and prevent information leakage.
    
    In production mode:
    - Returns generic error messages
    - Logs detailed errors server-side
    - Includes request ID for correlation
    
    In debug mode:
    - Returns detailed error information
    - Includes stack traces
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        """Process request with error handling."""
        settings = get_settings()
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        try:
            response = await call_next(request)
            return response
        
        except ValueError as e:
            # Validation errors
            logger.warning(
                f"Validation error: {str(e)}",
                extra={"request_id": request_id, "path": request.url.path}
            )
            
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "validation_error",
                    "message": str(e) if settings.debug else "Invalid request data",
                    "request_id": request_id
                }
            )
        
        except PermissionError as e:
            # Authorization errors
            logger.warning(
                f"Permission denied: {str(e)}",
                extra={"request_id": request_id, "path": request.url.path}
            )
            
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "forbidden",
                    "message": "Access denied",
                    "request_id": request_id
                }
            )
        
        except RuntimeError as e:
            # Database and runtime errors
            error_msg = str(e)
            
            # Log detailed error
            logger.error(
                f"Runtime error: {error_msg}",
                extra={
                    "request_id": request_id,
                    "path": request.url.path,
                    "traceback": traceback.format_exc() if settings.debug else None
                }
            )
            
            # Return sanitized response
            if settings.debug:
                message = error_msg
            else:
                # Don't leak internal details in production
                message = "An error occurred while processing your request"
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "internal_error",
                    "message": message,
                    "request_id": request_id
                }
            )
        
        except Exception as e:
            # Catch-all for unexpected errors
            error_msg = str(e)
            
            # Log full error with stack trace
            logger.error(
                f"Unhandled exception: {error_msg}",
                extra={
                    "request_id": request_id,
                    "path": request.url.path,
                    "exception_type": type(e).__name__,
                    "traceback": traceback.format_exc()
                },
                exc_info=True
            )
            
            # Return generic error in production
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "internal_error",
                    "message": error_msg if settings.debug else "An unexpected error occurred",
                    "request_id": request_id,
                    "type": type(e).__name__ if settings.debug else None
                }
            )
