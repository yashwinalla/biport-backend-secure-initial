from fastapi import HTTPException
from typing import Optional


class BaseAppException(HTTPException):
    """Base class for all custom application exceptions."""

    def __init__(self, status_code: int, detail: Optional[str] = None, default_message: str = "An error occurred"):
        """Initialize exception with a default message if no detail is provided."""
        super().__init__(status_code=status_code, detail=detail or default_message)


class NotFoundError(BaseAppException):
    """Exception for missing resources (404)."""
    
    def __init__(self, detail: Optional[str] = None):
        super().__init__(status_code=404, detail=detail, default_message="Resource not found")


class AuthenticationError(BaseAppException):
    """Exception for authentication failures (401)."""
    
    def __init__(self, detail: Optional[str] = None):
        super().__init__(status_code=401, detail=detail, default_message="Invalid credentials")


class AuthorizationError(BaseAppException):
    """Exception for permission issues (403)."""
    
    def __init__(self, detail: Optional[str] = None):
        super().__init__(status_code=403, detail=detail, default_message="You do not have permission to perform this action")


class ConflictError(BaseAppException):
    """Exception for conflicts like duplicate records (409)."""
    
    def __init__(self, detail: Optional[str] = None):
        super().__init__(status_code=409, detail=detail, default_message="Conflict: Resource already exists")


class ServerError(BaseAppException):
    """Exception for internal server errors (500)."""
    
    def __init__(self, detail: Optional[str] = None):
        super().__init__(status_code=500, detail=detail, default_message="Internal Server Error")



class BadRequestError(BaseAppException):
    """Exception for bad requests (400)."""
    
    def __init__(self, detail: Optional[str] = None):
        super().__init__(status_code=400, detail=detail, default_message="Bad request")


class ValidationError(BaseAppException):
    """Exception for validation errors (400)."""
    
    def __init__(self, detail: Optional[str] = None):
        super().__init__(status_code=400, detail=detail, default_message="Validation error")
