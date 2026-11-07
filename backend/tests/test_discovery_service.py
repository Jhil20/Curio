from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from app.core.exceptions import GitHubValidationError
from app.integrations.github.client import GitHubClient
from app.schemas.github import (
    GitHubRateLimitInfo,
    NormalizedRepository,
    RepositorySearchParams,
)
from app.services.discovery_service import RepositoryDiscoveryService


@pytest.fixture
def mock_github_client() -> GitHubClient:
    client = GitHubClient(token="mock_token")
    client.search_repositories = AsyncMock()  # type: ignore[method-assign]
    client.get_readme = AsyncMock()  # type: ignore[method-assign]
    client.get_rate_limit = AsyncMock()  # type: ignore[method-assign]
    return client


def test_build_search_query_combined() -> None:
    service = RepositoryDiscoveryService(github_client=GitHubClient())
    params = RepositorySearchParams(
        language="Java",
        topic="database",
        min_stars=100,
    )
    query = service.build_search_query(params)
    assert query == "language:Java topic:database stars:>=100"


def test_build_search_query_all_filters() -> None:
    service = RepositoryDiscoveryService(github_client=GitHubClient())
    params = RepositorySearchParams(
        query="curio",
        language="Python",
        topic="ai",
        min_stars=50,
        min_forks=10,
        created_after="2023-01-01",
        updated_after="2024-01-01",
    )
    query = service.build_search_query(params)
    assert "curio" in query
    assert "language:Python" in query
    assert "topic:ai" in query
    assert "stars:>=50" in query
    assert "forks:>=10" in query
    assert "created:>=2023-01-01" in query
    assert "pushed:>=2024-01-01" in query


def test_build_search_query_empty_raises_error() -> None:
    service = RepositoryDiscoveryService(github_client=GitHubClient())
    params = RepositorySearchParams()
    with pytest.raises(GitHubValidationError, match="At least one search filter"):
        service.build_search_query(params)


def test_normalize_repository_complete() -> None:
    service = RepositoryDiscoveryService(github_client=GitHubClient())
    raw = {
        "id": 98765,
        "name": "my-tool",
        "full_name": "developer/my-tool",
        "owner": {
            "login": "developer",
            "avatar_url": "https://avatar.test/1",
            "html_url": "https://github.com/developer",
        },
        "description": "An awesome developer tool",
        "html_url": "https://github.com/developer/my-tool",
        "language": "Rust",
        "topics": ["cli", "devtools"],
        "stargazers_count": 1250,
        "forks_count": 80,
        "open_issues_count": 12,
        "created_at": "2023-05-10T10:00:00Z",
        "updated_at": "2024-02-15T12:00:00Z",
        "pushed_at": "2024-02-16T14:30:00Z",
    }
    repo = service.normalize_repository(raw)
    assert isinstance(repo, NormalizedRepository)
    assert repo.github_id == 98765
    assert repo.name == "my-tool"
    assert repo.full_name == "developer/my-tool"
    assert repo.owner_login == "developer"
    assert repo.owner_avatar_url == "https://avatar.test/1"
    assert repo.language == "Rust"
    assert repo.topics == ["cli", "devtools"]
    assert repo.stars == 1250
    assert repo.forks == 80
    assert repo.open_issues == 12
    assert repo.created_at.year == 2023


def test_normalize_repository_missing_optional_fields() -> None:
    service = RepositoryDiscoveryService(github_client=GitHubClient())
    raw = {
        "id": 11111,
        "name": "minimal",
        "full_name": "owner/minimal",
        "owner": None,
        "description": None,
        "html_url": "https://github.com/owner/minimal",
        "language": None,
        "topics": None,
        "stargazers_count": 0,
        "forks_count": 0,
        "open_issues_count": 0,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "pushed_at": None,
    }
    repo = service.normalize_repository(raw)
    assert repo.github_id == 11111
    assert repo.owner_login == ""
    assert repo.description is None
    assert repo.language is None
    assert repo.topics == []
    assert repo.pushed_at is None


@pytest.mark.asyncio
async def test_search_repositories_service(mock_github_client: GitHubClient) -> None:
    mock_github_client.search_repositories.return_value = {  # type: ignore[attr-defined]
        "total_count": 45,
        "items": [
            {
                "id": 1001,
                "name": "repo1",
                "full_name": "org/repo1",
                "owner": {"login": "org"},
                "html_url": "https://github.com/org/repo1",
                "stargazers_count": 500,
                "forks_count": 50,
                "open_issues_count": 5,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-02T00:00:00Z",
            }
        ],
    }
    mock_github_client._latest_rate_limit = GitHubRateLimitInfo(
        limit=5000,
        remaining=4995,
        reset_at=datetime.now(UTC),
        used=5,
        resource="search",
    )

    service = RepositoryDiscoveryService(github_client=mock_github_client)
    params = RepositorySearchParams(language="Go", page=1, per_page=10)
    response = await service.search_repositories(params)

    assert len(response.items) == 1
    assert response.pagination.total_count == 45
    assert response.pagination.total_pages == 5
    assert response.pagination.has_next_page is True
    assert response.pagination.has_prev_page is False
    assert response.rate_limit is not None
    assert response.rate_limit.remaining == 4995


@pytest.mark.asyncio
async def test_discover_and_ingest_deduplication(mock_github_client: GitHubClient) -> None:
    # Query 1 returns repo 101 and 102
    # Query 2 returns repo 102 and 103 (102 is a duplicate)
    query_1_result = {
        "total_count": 2,
        "items": [
            {
                "id": 101,
                "name": "repoA",
                "full_name": "org/repoA",
                "owner": {"login": "org"},
                "html_url": "https://github.com/org/repoA",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-02T00:00:00Z",
            },
            {
                "id": 102,
                "name": "repoB",
                "full_name": "org/repoB",
                "owner": {"login": "org"},
                "html_url": "https://github.com/org/repoB",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-02T00:00:00Z",
            },
        ],
    }

    query_2_result = {
        "total_count": 2,
        "items": [
            {
                "id": 102,
                "name": "repoB",
                "full_name": "org/repoB",
                "owner": {"login": "org"},
                "html_url": "https://github.com/org/repoB",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-02T00:00:00Z",
            },
            {
                "id": 103,
                "name": "repoC",
                "full_name": "org/repoC",
                "owner": {"login": "org"},
                "html_url": "https://github.com/org/repoC",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-02T00:00:00Z",
            },
        ],
    }

    mock_github_client.search_repositories.side_effect = [  # type: ignore[attr-defined]
        query_1_result,
        query_2_result,
    ]
    mock_github_client.get_readme.return_value = ("# Readme content", 16, "utf-8")  # type: ignore[attr-defined]

    service = RepositoryDiscoveryService(github_client=mock_github_client)
    queries = [
        RepositorySearchParams(language="Java", topic="database"),
        RepositorySearchParams(language="Python", topic="database"),
    ]

    summary = await service.discover_and_ingest(queries=queries, fetch_readmes=True)

    assert summary.total_queries == 2
    assert summary.total_discovered == 4  # 2 + 2
    assert summary.unique_repositories == 3  # 101, 102, 103
    assert summary.duplicates_identified == 1  # 4 - 3
    assert len(summary.items) == 3
    # Check that README was fetched
    for repo in summary.items:
        assert repo.readme_content == "# Readme content"
