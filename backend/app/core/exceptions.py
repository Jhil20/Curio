from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class CurioException(Exception):
    """Base exception for all Curio domain errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    ):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundException(CurioException):
    """Resource not found error."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND)


class DatabaseException(CurioException):
    """Database connection or query failure."""

    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


def setup_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(CurioException)
    async def curio_exception_handler(request: Request, exc: CurioException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.__class__.__name__,
                    "message": exc.message,
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "InternalServerError",
                    "message": "An unexpected server error occurred.",
                }
            },
        )
