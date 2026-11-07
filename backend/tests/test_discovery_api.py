from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from app.api.v1.endpoints.discovery import get_discovery_service
from app.core.exceptions import GitHubAuthenticationError, GitHubRateLimitError
from app.integrations.github.client import GitHubClient
from app.main import app
from app.schemas.github import (
    GitHubRateLimitInfo,
    NormalizedRepository,
    PaginationMetadata,
    ReadmeResponse,
    RepositorySearchResponse,
)
from app.services.discovery_service import RepositoryDiscoveryService
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def sample_normalized_repo() -> NormalizedRepository:
    return NormalizedRepository(
        github_id=55555,
        name="test-repo",
        full_name="curio/test-repo",
        owner_login="curio",
        owner_avatar_url="https://avatar.test/curio",
        owner_html_url="https://github.com/curio",
        description="A great test repo",
        html_url="https://github.com/curio/test-repo",
        language="TypeScript",
        topics=["testing", "curio"],
        stars=350,
        forks=25,
        open_issues=2,
        created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
        github_updated_at=datetime(2024, 1, 2, 12, 0, 0, tzinfo=UTC),
        pushed_at=datetime(2024, 1, 3, 12, 0, 0, tzinfo=UTC),
    )


@pytest.mark.asyncio
async def test_search_api_success(
    async_client: AsyncClient, sample_normalized_repo: NormalizedRepository
) -> None:
    mock_service = AsyncMock(spec=RepositoryDiscoveryService)
    mock_service.search_repositories.return_value = RepositorySearchResponse(
        items=[sample_normalized_repo],
        pagination=PaginationMetadata(
            page=1,
            per_page=10,
            total_count=1,
            total_pages=1,
            has_next_page=False,
            has_prev_page=False,
        ),
        rate_limit=GitHubRateLimitInfo(
            limit=5000,
            remaining=4990,
            reset_at=datetime.now(UTC),
            used=10,
            resource="search",
        ),
    )

    app.dependency_overrides[get_discovery_service] = lambda: mock_service
    try:
        response = await async_client.get(
            "/api/v1/discovery/search?language=TypeScript&min_stars=100"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["github_id"] == 55555
        assert data["pagination"]["total_count"] == 1
        assert data["rate_limit"]["remaining"] == 4990
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_search_api_no_criteria_returns_422(async_client: AsyncClient) -> None:
    # Service without overrides uses real build_search_query logic which rejects empty criteria
    client = GitHubClient(token="mock")
    real_service = RepositoryDiscoveryService(github_client=client)
    app.dependency_overrides[get_discovery_service] = lambda: real_service
    try:
        response = await async_client.get("/api/v1/discovery/search")
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "GitHubValidationError"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_ingest_api_success(
    async_client: AsyncClient, sample_normalized_repo: NormalizedRepository
) -> None:
    mock_service = AsyncMock(spec=RepositoryDiscoveryService)
    mock_service.discover_and_ingest.return_value = {
        "total_queries": 2,
        "total_discovered": 3,
        "unique_repositories": 2,
        "duplicates_identified": 1,
        "items": [sample_normalized_repo],
    }

    app.dependency_overrides[get_discovery_service] = lambda: mock_service
    try:
        payload = {
            "queries": [
                {"language": "Python", "topic": "fastapi"},
                {"language": "TypeScript", "topic": "fastapi"},
            ],
            "fetch_readmes": False,
        }
        response = await async_client.post("/api/v1/discovery/ingest", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["total_queries"] == 2
        assert data["total_discovered"] == 3
        assert data["unique_repositories"] == 2
        assert data["duplicates_identified"] == 1
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_readme_api_success(async_client: AsyncClient) -> None:
    mock_service = AsyncMock(spec=RepositoryDiscoveryService)
    mock_service.get_readme.return_value = ReadmeResponse(
        owner="tiangolo",
        repo="fastapi",
        content="# FastAPI\nHigh performance",
        size=26,
        encoding="utf-8",
    )

    app.dependency_overrides[get_discovery_service] = lambda: mock_service
    try:
        response = await async_client.get("/api/v1/discovery/readme/tiangolo/fastapi")
        assert response.status_code == 200
        data = response.json()
        assert data["owner"] == "tiangolo"
        assert data["repo"] == "fastapi"
        assert data["content"] == "# FastAPI\nHigh performance"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_rate_limit_api_success(async_client: AsyncClient) -> None:
    mock_service = AsyncMock(spec=RepositoryDiscoveryService)
    mock_service.get_rate_limit.return_value = GitHubRateLimitInfo(
        limit=5000,
        remaining=4950,
        reset_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
        used=50,
        resource="search",
    )

    app.dependency_overrides[get_discovery_service] = lambda: mock_service
    try:
        response = await async_client.get("/api/v1/discovery/rate-limit")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 5000
        assert data["remaining"] == 4950
        assert data["used"] == 50
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_api_rate_limit_exception_handling() -> None:
    mock_service = AsyncMock(spec=RepositoryDiscoveryService)
    mock_service.search_repositories.side_effect = GitHubRateLimitError(
        message="GitHub API rate limit reached",
        reset_at=1700000999,
        retry_after=60,
    )

    app.dependency_overrides[get_discovery_service] = lambda: mock_service
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/discovery/search?language=Java")
            assert response.status_code == 429
            assert response.headers.get("retry-after") == "60"
            data = response.json()
            assert data["error"]["code"] == "GitHubRateLimitError"
            assert data["error"]["message"] == "GitHub API rate limit reached"
            assert data["error"]["details"]["reset_at"] == 1700000999
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_api_authentication_exception_handling() -> None:
    mock_service = AsyncMock(spec=RepositoryDiscoveryService)
    mock_service.search_repositories.side_effect = GitHubAuthenticationError(
        message="Bad credentials"
    )

    app.dependency_overrides[get_discovery_service] = lambda: mock_service
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/discovery/search?language=Java")
            assert response.status_code == 401
            data = response.json()
            assert data["error"]["code"] == "GitHubAuthenticationError"
    finally:
        app.dependency_overrides.clear()
