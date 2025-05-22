from typing import Any, Dict, Optional
from fastapi import HTTPException, status
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class ErrorResponse(BaseModel):
    """Standard error response model."""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None

class BaseAppException(HTTPException):
    """Base exception class for the application."""
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=message)
        self.message = message
        self.details = details or {}
        logger.error(f"{self.__class__.__name__}: {message}", extra={"details": details})

class DatabaseException(BaseAppException):
    """Exception for database-related errors."""
    def __init__(
        self,
        message: str = "Database error occurred",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message=message, status_code=500, details=details)

class ValidationException(BaseAppException):
    """Exception for validation errors."""
    def __init__(
        self,
        message: str = "Validation error",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message=message, status_code=400, details=details)

class AuthenticationException(BaseAppException):
    """Exception for authentication errors."""
    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message=message, status_code=401, details=details)

class AuthorizationException(BaseAppException):
    """Exception for authorization errors."""
    def __init__(
        self,
        message: str = "Not authorized",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message=message, status_code=403, details=details)

class NotFoundException(BaseAppException):
    """Exception for resource not found errors."""
    def __init__(
        self,
        message: str = "Resource not found",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message=message, status_code=404, details=details)

class ConflictException(BaseAppException):
    """Exception for resource conflict errors."""
    def __init__(
        self,
        message: str = "Resource conflict",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message=message, status_code=409, details=details)

class RateLimitException(BaseAppException):
    """Exception for rate limiting errors."""
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message=message, status_code=429, details=details)

class ServiceUnavailableException(BaseAppException):
    """Exception for service unavailable errors."""
    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message=message, status_code=503, details=details)

class EventError(BaseAppException):
    """Exception raised for event-related errors."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=400, message=message, details=details)

def handle_exception(exc: Exception) -> BaseAppException:
    """Handle exceptions and convert them to appropriate application exceptions."""
    if isinstance(exc, BaseAppException):
        return exc
    
    if isinstance(exc, ValueError):
        return ValidationException(str(exc))
    
    if isinstance(exc, KeyError):
        return ValidationException(f"Missing required field: {str(exc)}")
    
    if isinstance(exc, AttributeError):
        return ValidationException(f"Invalid attribute: {str(exc)}")
    
    if isinstance(exc, TypeError):
        return ValidationException(f"Type error: {str(exc)}")
    
    if isinstance(exc, ConnectionError):
        return ServiceUnavailableException(
            "Service temporarily unavailable",
            {"error": str(exc)}
        )
    
    # Default to internal server error
    return DatabaseException(
        "An unexpected error occurred",
        {"error": str(exc), "type": exc.__class__.__name__}
    ) 