from fastapi import HTTPException
from app.core import ServiceResponse 


class BaseService:
    """Provides a common method for handling service logic with exception handling."""
    
    @staticmethod
    def execute(service_function, *args, **kwargs) -> ServiceResponse:
        """Executes a service function, handling all exceptions in a structured way."""
        try:
            return service_function(*args, **kwargs)
        except HTTPException as he:
            return ServiceResponse.failure(error=he.detail, status_code=he.status_code)
        except Exception as e:
            return ServiceResponse.failure(error=str(e), status_code=500)