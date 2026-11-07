from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from app.core.exceptions import (
    GitHubAPIError,
    GitHubAuthenticationError,
    GitHubNetworkError,
    GitHubRateLimitError,
    GitHubValidationError,
)
from app.integrations.github.client import GitHubClient


@pytest.fixture
def sample_repo_data() -> dict[str, Any]:
    return {
        "total_count": 1,
        "incomplete_results": False,
        "items": [
            {
                "id": 123456,
                "name": "fastapi",
                "full_name": "tiangolo/fastapi",
                "owner": {
                    "login": "tiangolo",
                    "avatar_url": "https://avatars.githubusercontent.com/u/1326112",
                    "html_url": "https://github.com/tiangolo",
                },
                "html_url": "https://github.com/tiangolo/fastapi",
                "description": "FastAPI framework, high performance, easy to learn",
                "language": "Python",
                "topics": ["fastapi", "python", "api"],
                "stargazers_count": 75000,
                "forks_count": 6000,
                "open_issues_count": 250,
                "created_at": "2018-12-08T08:21:47Z",
                "updated_at": "2024-01-01T12:00:00Z",
                "pushed_at": "2024-01-02T15:30:00Z",
            }
        ],
    }


@pytest.mark.asyncio
async def test_client_headers_with_and_without_token() -> None:
    client_with_token = GitHubClient(token="ghp_test12345")
    headers = client_with_token._get_headers()
    assert headers["Authorization"] == "Bearer ghp_test12345"
    assert headers["Accept"] == "application/vnd.github+json"

    client_without_token = GitHubClient(token="")
    headers_no_token = client_without_token._get_headers()
    assert "Authorization" not in headers_no_token


@pytest.mark.asyncio
async def test_search_repositories_success(sample_repo_data: dict[str, Any]) -> None:
    client = GitHubClient(token="test_token")
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = sample_repo_data
    mock_response.headers = httpx.Headers(
        {
            "x-ratelimit-limit": "5000",
            "x-ratelimit-remaining": "4990",
            "x-ratelimit-reset": "1700000000",
            "x-ratelimit-used": "10",
            "x-ratelimit-resource": "search",
        }
    )

    with patch.object(
        httpx.AsyncClient, "get", new_callable=AsyncMock, return_value=mock_response
    ) as mock_get:
        result = await client.search_repositories(
            query="language:Python stars:>1000",
            sort="stars",
            order="desc",
            page=1,
            per_page=10,
        )

        assert result["total_count"] == 1
        assert len(result["items"]) == 1
        assert result["items"][0]["name"] == "fastapi"
        mock_get.assert_called_once()
        assert client.latest_rate_limit is not None
        assert client.latest_rate_limit.remaining == 4990
    await client.close()


@pytest.mark.asyncio
async def test_get_readme_raw_markdown() -> None:
    client = GitHubClient()
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.text = "# FastAPI\nAwesome framework"
    mock_response.headers = httpx.Headers(
        {
            "content-type": "text/plain; charset=utf-8",
            "x-ratelimit-limit": "60",
            "x-ratelimit-remaining": "55",
            "x-ratelimit-reset": "1700000000",
        }
    )

    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock, return_value=mock_response):
        content, size, encoding = await client.get_readme(owner="tiangolo", repo="fastapi")
        assert content == "# FastAPI\nAwesome framework"
        assert size is not None and size > 0
        assert encoding == "utf-8"
    await client.close()


@pytest.mark.asyncio
async def test_get_readme_base64_json() -> None:
    client = GitHubClient()
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.headers = httpx.Headers(
        {
            "content-type": "application/json; charset=utf-8",
            "x-ratelimit-limit": "60",
            "x-ratelimit-remaining": "50",
            "x-ratelimit-reset": "1700000000",
        }
    )
    mock_response.json.return_value = {
        "content": "IyBGYXN0QVBJCkF3ZXNvbWUgZnJhbWV3b3Jr",  # Base64 encoded "# FastAPI\nAwesome framework"
        "encoding": "base64",
        "size": 28,
    }

    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock, return_value=mock_response):
        content, size, encoding = await client.get_readme(owner="tiangolo", repo="fastapi")
        assert content == "# FastAPI\nAwesome framework"
        assert size == 28
        assert encoding == "base64"
    await client.close()


@pytest.mark.asyncio
async def test_get_readme_not_found() -> None:
    client = GitHubClient()
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 404
    mock_response.headers = httpx.Headers({})

    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock, return_value=mock_response):
        content, size, encoding = await client.get_readme(owner="nobody", repo="norepo")
        assert content is None
        assert size is None
        assert encoding is None
    await client.close()


@pytest.mark.asyncio
async def test_get_rate_limit() -> None:
    client = GitHubClient()
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.headers = httpx.Headers({})
    mock_response.json.return_value = {
        "resources": {
            "search": {
                "limit": 30,
                "remaining": 28,
                "reset": 1700000000,
                "used": 2,
            }
        }
    }

    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock, return_value=mock_response):
        info = await client.get_rate_limit()
        assert info.limit == 30
        assert info.remaining == 28
        assert info.used == 2
        assert info.resource == "search"
        assert info.reset_at == datetime.fromtimestamp(1700000000, tz=UTC)
    await client.close()


@pytest.mark.asyncio
async def test_error_handling_unauthorized() -> None:
    client = GitHubClient()
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 401
    mock_response.headers = httpx.Headers({})
    mock_response.json.return_value = {"message": "Bad credentials"}

    with (
        patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock, return_value=mock_response),
        pytest.raises(GitHubAuthenticationError, match="Bad credentials"),
    ):
        await client.search_repositories(query="test")
    await client.close()


@pytest.mark.asyncio
async def test_error_handling_rate_limit() -> None:
    client = GitHubClient()
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 403
    mock_response.headers = httpx.Headers(
        {
            "x-ratelimit-remaining": "0",
            "x-ratelimit-reset": "1700000500",
            "retry-after": "60",
        }
    )
    mock_response.json.return_value = {"message": "API rate limit exceeded"}

    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock, return_value=mock_response):
        with pytest.raises(GitHubRateLimitError) as exc_info:
            await client.search_repositories(query="test")
        assert exc_info.value.reset_at == 1700000500
        assert exc_info.value.retry_after == 60
    await client.close()


@pytest.mark.asyncio
async def test_error_handling_validation_error() -> None:
    client = GitHubClient()
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 422
    mock_response.headers = httpx.Headers({})
    mock_response.json.return_value = {"message": "Validation Failed"}

    with (
        patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock, return_value=mock_response),
        pytest.raises(GitHubValidationError),
    ):
        await client.search_repositories(query="invalid:qualifier")
    await client.close()


@pytest.mark.asyncio
async def test_error_handling_server_error() -> None:
    client = GitHubClient()
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 503
    mock_response.headers = httpx.Headers({})
    mock_response.json.return_value = {"message": "Service Unavailable"}

    with (
        patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock, return_value=mock_response),
        pytest.raises(GitHubAPIError),
    ):
        await client.search_repositories(query="test")
    await client.close()


@pytest.mark.asyncio
async def test_error_handling_network_timeout() -> None:
    client = GitHubClient()
    with (
        patch.object(
            httpx.AsyncClient,
            "get",
            new_callable=AsyncMock,
            side_effect=httpx.ReadTimeout("Connection timed out"),
        ),
        pytest.raises(GitHubNetworkError, match="timed out"),
    ):
        await client.search_repositories(query="test")
    await client.close()
