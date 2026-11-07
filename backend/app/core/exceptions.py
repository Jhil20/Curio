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


class GitHubException(CurioException):
    """Base exception for GitHub API integration errors."""

    def __init__(
        self,
        message: str = "GitHub integration error",
        status_code: int = status.HTTP_502_BAD_GATEWAY,
        details: dict[str, object] | None = None,
    ):
        super().__init__(message, status_code=status_code)
        self.details = details or {}


class GitHubAuthenticationError(GitHubException):
    """Raised when GitHub token authentication fails (401)."""

    def __init__(self, message: str = "Invalid or expired GitHub authentication token"):
        super().__init__(message, status_code=status.HTTP_401_UNAUTHORIZED)


class GitHubRateLimitError(GitHubException):
    """Raised when GitHub rate limit quota is exceeded (403/429)."""

    def __init__(
        self,
        message: str = "GitHub API rate limit exceeded",
        reset_at: int | None = None,
        retry_after: int | None = None,
    ):
        details: dict[str, object] = {}
        if reset_at is not None:
            details["reset_at"] = reset_at
        if retry_after is not None:
            details["retry_after"] = retry_after
        super().__init__(
            message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details,
        )
        self.reset_at = reset_at
        self.retry_after = retry_after


class GitHubNotFoundError(GitHubException):
    """Raised when a requested GitHub resource (e.g., repository or README) is not found (404)."""

    def __init__(self, message: str = "GitHub resource not found"):
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND)


class GitHubValidationError(GitHubException):
    """Raised when GitHub search qualifiers or input syntax is invalid (422)."""

    def __init__(self, message: str = "Invalid GitHub search parameters"):
        super().__init__(message, status_code=status.HTTP_422_UNPROCESSABLE_CONTENT)


class GitHubNetworkError(GitHubException):
    """Raised when connecting to GitHub encounters a network timeout or connection failure."""

    def __init__(
        self, message: str = "Network timeout or connection error while contacting GitHub"
    ):
        super().__init__(message, status_code=status.HTTP_504_GATEWAY_TIMEOUT)


class GitHubAPIError(GitHubException):
    """Raised on upstream 5xx errors or unexpected responses from GitHub."""

    def __init__(self, message: str = "GitHub upstream service error"):
        super().__init__(message, status_code=status.HTTP_502_BAD_GATEWAY)


def setup_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(CurioException)
    async def curio_exception_handler(request: Request, exc: CurioException) -> JSONResponse:
        content: dict[str, object] = {
            "error": {
                "code": exc.__class__.__name__,
                "message": exc.message,
            }
        }
        if isinstance(exc, GitHubException) and exc.details:
            error_dict = content["error"]
            if isinstance(error_dict, dict):
                error_dict["details"] = exc.details

        headers: dict[str, str] = {}
        if isinstance(exc, GitHubRateLimitError) and exc.retry_after is not None:
            headers["Retry-After"] = str(exc.retry_after)

        return JSONResponse(
            status_code=exc.status_code,
            content=content,
            headers=headers if headers else None,
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
