from typing import (
    Any, NamedTuple, Optional
)

from app.core import logger


class ServiceResponse(NamedTuple):
    """Standard response structure for APIs."""
    data: Optional[Any]
    error: Optional[str]
    status_code: int

    @staticmethod
    def success(data: Any, status_code: int = 200) -> "ServiceResponse":
        """Returns a success response."""
        return ServiceResponse(data=data, error=None, status_code=status_code)

    @staticmethod
    def failure(error: str, status_code: int) -> "ServiceResponse":
        """Returns an error response."""
        logger.error(error)
        return ServiceResponse(data=None, error=error, status_code=status_code)