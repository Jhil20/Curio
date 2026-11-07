from typing import Literal

from fastapi import APIRouter, Depends, Query, status

from app.integrations.github.client import GitHubClient, get_github_client
from app.schemas.github import (
    BatchDiscoveryRequest,
    GitHubRateLimitInfo,
    IngestionSummary,
    ReadmeResponse,
    RepositorySearchParams,
    RepositorySearchResponse,
)
from app.services.discovery_service import RepositoryDiscoveryService

router = APIRouter()


def get_discovery_service(
    client: GitHubClient = Depends(get_github_client),
) -> RepositoryDiscoveryService:
    return RepositoryDiscoveryService(github_client=client)


@router.get(
    "/search",
    response_model=RepositorySearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search repositories on GitHub",
    description="Discover GitHub repositories using language, topic, stars, forks, and date qualifiers.",
)
async def search_repositories(
    language: str | None = Query(None, description="Programming language"),
    topic: str | None = Query(None, description="Repository topic"),
    min_stars: int | None = Query(None, ge=0, description="Minimum star count"),
    min_forks: int | None = Query(None, ge=0, description="Minimum fork count"),
    created_after: str | None = Query(None, description="Created after date (YYYY-MM-DD)"),
    updated_after: str | None = Query(None, description="Updated after date (YYYY-MM-DD)"),
    sort: Literal["stars", "forks", "help-wanted-issues", "updated"] | None = Query(
        None, description="Sort field"
    ),
    order: Literal["asc", "desc"] = Query("desc", description="Sort order (asc/desc)"),
    page: int = Query(1, ge=1, le=100, description="Page number"),
    per_page: int = Query(30, ge=1, le=100, description="Results per page"),
    q: str | None = Query(None, description="Custom keywords or search term"),
    service: RepositoryDiscoveryService = Depends(get_discovery_service),
) -> RepositorySearchResponse:
    params = RepositorySearchParams(
        language=language,
        topic=topic,
        min_stars=min_stars,
        min_forks=min_forks,
        created_after=created_after,
        updated_after=updated_after,
        sort=sort,
        order=order,
        page=page,
        per_page=per_page,
        query=q,
    )
    return await service.search_repositories(params)


@router.post(
    "/ingest",
    response_model=IngestionSummary,
    status_code=status.HTTP_200_OK,
    summary="Batch discovery and normalization",
    description="Execute multiple discovery queries, normalize metadata, and identify duplicates by GitHub ID.",
)
async def ingest_repositories(
    payload: BatchDiscoveryRequest,
    service: RepositoryDiscoveryService = Depends(get_discovery_service),
) -> IngestionSummary:
    return await service.discover_and_ingest(
        queries=payload.queries,
        fetch_readmes=payload.fetch_readmes,
    )


@router.get(
    "/readme/{owner}/{repo}",
    response_model=ReadmeResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve repository README",
    description="Fetch raw markdown README content for a specified GitHub repository.",
)
async def get_readme(
    owner: str,
    repo: str,
    service: RepositoryDiscoveryService = Depends(get_discovery_service),
) -> ReadmeResponse:
    return await service.get_readme(owner=owner, repo=repo)


@router.get(
    "/rate-limit",
    response_model=GitHubRateLimitInfo,
    status_code=status.HTTP_200_OK,
    summary="GitHub rate limit status",
    description="Query current GitHub API rate limit quota.",
)
async def get_rate_limit(
    service: RepositoryDiscoveryService = Depends(get_discovery_service),
) -> GitHubRateLimitInfo:
    return await service.get_rate_limit()
