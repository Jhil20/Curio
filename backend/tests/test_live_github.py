import pytest
from app.integrations.github.client import GitHubClient
from app.main import app
from app.schemas.github import RepositorySearchParams
from app.services.discovery_service import RepositoryDiscoveryService
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_live_github_rate_limit() -> None:
    """Live call to GitHub to verify token authentication and retrieve rate limit quota."""
    async with GitHubClient() as client:
        service = RepositoryDiscoveryService(github_client=client)
        rate_info = await service.get_rate_limit()
        assert rate_info.limit > 0
        assert rate_info.remaining >= 0
        assert rate_info.resource in ("core", "search")


@pytest.mark.asyncio
async def test_live_github_search_repositories() -> None:
    """Live call to GitHub search API to verify real repository discovery and normalization."""
    async with GitHubClient() as client:
        service = RepositoryDiscoveryService(github_client=client)
        params = RepositorySearchParams(
            language="Python",
            topic="fastapi",
            min_stars=5000,
            per_page=5,
        )
        response = await service.search_repositories(params)
        assert response.pagination.total_count > 0
        assert len(response.items) > 0
        # Verify first repo is normalized properly from real GitHub data
        first = response.items[0]
        assert first.github_id > 0
        assert len(first.full_name) > 0
        assert first.stars >= 5000
        assert first.language == "Python"


@pytest.mark.asyncio
async def test_live_github_get_readme() -> None:
    """Live call to GitHub to fetch and decode README for fastapi/fastapi."""
    async with GitHubClient() as client:
        service = RepositoryDiscoveryService(github_client=client)
        readme = await service.get_readme(owner="fastapi", repo="fastapi")
        assert readme.content is not None
        assert "FastAPI" in readme.content
        assert readme.size is not None and readme.size > 0


@pytest.mark.asyncio
async def test_live_api_endpoints_via_fastapi() -> None:
    """Live HTTP request through the FastAPI app down to GitHub (no dependency overrides or mocks)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test Search Endpoint
        search_res = await client.get(
            "/api/v1/discovery/search",
            params={"language": "Python", "min_stars": 50000, "per_page": 2},
        )
        assert search_res.status_code == 200
        data = search_res.json()
        assert len(data["items"]) > 0

        # Test Rate Limit Endpoint
        rate_res = await client.get("/api/v1/discovery/rate-limit")
        assert rate_res.status_code == 200
        rate_data = rate_res.json()
        assert rate_data["limit"] > 0

        # Test Readme Endpoint
        readme_res = await client.get("/api/v1/discovery/readme/fastapi/fastapi")
        assert readme_res.status_code == 200
        assert "FastAPI" in readme_res.json()["content"]
