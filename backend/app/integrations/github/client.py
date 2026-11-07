import base64
from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.config import settings
from app.core.exceptions import (
    GitHubAPIError,
    GitHubAuthenticationError,
    GitHubException,
    GitHubNetworkError,
    GitHubNotFoundError,
    GitHubRateLimitError,
    GitHubValidationError,
)
from app.core.logging import logger
from app.schemas.github import GitHubRateLimitInfo


class GitHubClient:
    """Asynchronous client for interacting with the GitHub REST API (FR-006, FR-011, FR-012)."""

    def __init__(
        self,
        token: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self.token = token if token is not None else settings.GITHUB_TOKEN
        self.base_url = (base_url or settings.GITHUB_API_BASE_URL).rstrip("/")
        self.timeout = timeout or settings.GITHUB_TIMEOUT_SECONDS
        self._client: httpx.AsyncClient | None = None
        self._latest_rate_limit: GitHubRateLimitInfo | None = None

    @property
    def latest_rate_limit(self) -> GitHubRateLimitInfo | None:
        return self._latest_rate_limit

    def _get_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": settings.GITHUB_API_VERSION,
            "User-Agent": "Curio-App/0.1.0",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        else:
            logger.warning(
                "GitHub token is not configured. Requests will run unauthenticated with low rate limits (60 req/hr)."
            )
        return headers

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self._get_headers(),
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client

    def _extract_rate_limit(self, response: httpx.Response, resource: str = "core") -> None:
        headers = response.headers
        limit_str = headers.get("x-ratelimit-limit")
        remaining_str = headers.get("x-ratelimit-remaining")
        reset_str = headers.get("x-ratelimit-reset")
        used_str = headers.get("x-ratelimit-used", "0")

        if limit_str and remaining_str and reset_str:
            try:
                reset_timestamp = int(reset_str)
                self._latest_rate_limit = GitHubRateLimitInfo(
                    limit=int(limit_str),
                    remaining=int(remaining_str),
                    reset_at=datetime.fromtimestamp(reset_timestamp, tz=UTC),
                    used=int(used_str),
                    resource=headers.get("x-ratelimit-resource", resource),
                )
            except (ValueError, OSError) as e:
                logger.debug("Failed to parse rate limit headers: %s", e)

    def _handle_error_response(self, response: httpx.Response) -> None:
        status_code = response.status_code
        if status_code < 400:
            return

        error_data: dict[str, Any] = {}
        try:
            error_data = response.json()
        except Exception:
            error_data = {"message": response.text}

        msg = error_data.get("message", "GitHub API error")

        if status_code == 401:
            raise GitHubAuthenticationError(f"GitHub authentication failed: {msg}")

        if status_code in (403, 429):
            is_rate_limit = (
                response.headers.get("x-ratelimit-remaining") == "0"
                or "rate limit" in str(msg).lower()
                or "secondary rate limit" in str(msg).lower()
            )
            if is_rate_limit:
                reset_at = (
                    int(response.headers["x-ratelimit-reset"])
                    if "x-ratelimit-reset" in response.headers
                    else None
                )
                retry_after = (
                    int(response.headers["retry-after"])
                    if "retry-after" in response.headers
                    else None
                )
                raise GitHubRateLimitError(
                    f"GitHub rate limit exceeded: {msg}",
                    reset_at=reset_at,
                    retry_after=retry_after,
                )

        if status_code == 404:
            raise GitHubNotFoundError(f"Requested resource not found on GitHub: {msg}")

        if status_code == 422:
            raise GitHubValidationError(f"Invalid GitHub search query or parameters: {msg}")

        if status_code >= 500:
            raise GitHubAPIError(f"GitHub service error ({status_code}): {msg}")

        raise GitHubException(
            f"GitHub API error ({status_code}): {msg}",
            status_code=status_code,
            details=error_data,
        )

    async def search_repositories(
        self,
        query: str,
        sort: str | None = None,
        order: str | None = None,
        page: int = 1,
        per_page: int = 30,
    ) -> dict[str, Any]:
        """Execute a repository search query on GitHub (FR-007, FR-010)."""
        client = await self._get_client()
        params: dict[str, str | int] = {
            "q": query,
            "page": page,
            "per_page": per_page,
        }
        if sort:
            params["sort"] = sort
        if order:
            params["order"] = order

        try:
            response = await client.get("/search/repositories", params=params)
        except httpx.TimeoutException as e:
            raise GitHubNetworkError(f"GitHub search request timed out: {e}") from e
        except httpx.NetworkError as e:
            raise GitHubNetworkError(f"GitHub network connection error: {e}") from e

        self._extract_rate_limit(response, resource="search")
        self._handle_error_response(response)
        return response.json()  # type: ignore[no-any-return]

    async def get_readme(
        self,
        owner: str,
        repo: str,
    ) -> tuple[str | None, int | None, str | None]:
        """Retrieve README markdown content for a repository (FR-009).

        Returns tuple of (content, size, encoding). If repository has no README (404),
        returns (None, None, None) safely.
        """
        client = await self._get_client()
        try:
            response = await client.get(
                f"/repos/{owner}/{repo}/readme",
                headers={"Accept": "application/vnd.github.raw"},
            )
        except httpx.TimeoutException as e:
            raise GitHubNetworkError(f"GitHub README request timed out: {e}") from e
        except httpx.NetworkError as e:
            raise GitHubNetworkError(f"GitHub network connection error: {e}") from e

        self._extract_rate_limit(response, resource="core")

        if response.status_code == 404:
            logger.info("README not found for %s/%s", owner, repo)
            return None, None, None

        if response.status_code >= 400:
            self._handle_error_response(response)

        # Check if returned as JSON with base64 encoding or raw markdown
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            data = response.json()
            content_encoded = data.get("content", "")
            if data.get("encoding") == "base64" and content_encoded:
                raw_text = base64.b64decode(content_encoded).decode("utf-8", errors="replace")
                size = data.get("size", len(raw_text.encode("utf-8")))
                return raw_text, size, "base64"

        # Handle raw text response
        raw_text = response.text
        size = len(raw_text.encode("utf-8"))
        return raw_text, size, "utf-8"

    async def get_rate_limit(self) -> GitHubRateLimitInfo:
        """Fetch current rate limit status from GitHub API (FR-011)."""
        client = await self._get_client()
        try:
            response = await client.get("/rate_limit")
        except httpx.TimeoutException as e:
            raise GitHubNetworkError(f"GitHub rate limit request timed out: {e}") from e
        except httpx.NetworkError as e:
            raise GitHubNetworkError(f"GitHub network connection error: {e}") from e

        self._handle_error_response(response)
        data = response.json()
        search_quota = data.get("resources", {}).get("search", {})
        reset_ts = search_quota.get("reset", int(datetime.now(UTC).timestamp()))

        return GitHubRateLimitInfo(
            limit=search_quota.get("limit", 30),
            remaining=search_quota.get("remaining", 30),
            reset_at=datetime.fromtimestamp(reset_ts, tz=UTC),
            used=search_quota.get("used", 0),
            resource="search",
        )

    async def close(self) -> None:
        """Close the underlying HTTP client session."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "GitHubClient":
        await self._get_client()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()


async def get_github_client() -> GitHubClient:
    """FastAPI dependency for accessing GitHub client."""
    client = GitHubClient()
    try:
        return client
    finally:
        pass
