import math
from datetime import UTC, date, datetime
from typing import Any

from app.core.exceptions import GitHubValidationError
from app.core.logging import logger
from app.integrations.github.client import GitHubClient
from app.schemas.github import (
    GitHubRateLimitInfo,
    IngestionSummary,
    NormalizedRepository,
    PaginationMetadata,
    ReadmeResponse,
    RepositorySearchParams,
    RepositorySearchResponse,
)


class RepositoryDiscoveryService:
    """Service orchestrating GitHub repository discovery, normalization, and deduplication (FR-007, FR-008, 5.3, 5.4, 5.5)."""

    def __init__(self, github_client: GitHubClient) -> None:
        self.client = github_client

    def build_search_query(self, params: RepositorySearchParams) -> str:
        """Construct a validated GitHub search query string from search parameters (FR-007, 5.3)."""
        qualifiers: list[str] = []

        if params.query and params.query.strip():
            qualifiers.append(params.query.strip())

        if params.language and params.language.strip():
            qualifiers.append(f"language:{params.language.strip()}")

        if params.topic and params.topic.strip():
            qualifiers.append(f"topic:{params.topic.strip()}")

        if params.min_stars is not None:
            qualifiers.append(f"stars:>={params.min_stars}")

        if params.min_forks is not None:
            qualifiers.append(f"forks:>={params.min_forks}")

        if params.created_after is not None:
            created_str = (
                params.created_after.isoformat()
                if isinstance(params.created_after, date | datetime)
                else str(params.created_after).strip()
            )
            qualifiers.append(f"created:>={created_str}")

        if params.updated_after is not None:
            updated_str = (
                params.updated_after.isoformat()
                if isinstance(params.updated_after, date | datetime)
                else str(params.updated_after).strip()
            )
            # GitHub search uses pushed:>= or updated:>=
            qualifiers.append(f"pushed:>={updated_str}")

        if not qualifiers:
            raise GitHubValidationError(
                "At least one search filter (language, topic, min_stars, min_forks, created_after, updated_after, or query) must be provided."
            )

        return " ".join(qualifiers)

    def normalize_repository(self, raw: dict[str, Any]) -> NormalizedRepository:
        """Transform raw GitHub repository JSON into decoupled NormalizedRepository schema (FR-008, 5.4)."""
        owner_data = raw.get("owner") or {}

        # Safe datetime parsing
        def parse_dt(val: Any) -> datetime:
            if isinstance(val, datetime):
                return val
            if isinstance(val, str):
                try:
                    return datetime.fromisoformat(val.replace("Z", "+00:00"))
                except ValueError:
                    pass
            return datetime.now(UTC)

        def parse_optional_dt(val: Any) -> datetime | None:
            if not val:
                return None
            if isinstance(val, datetime):
                return val
            if isinstance(val, str):
                try:
                    return datetime.fromisoformat(val.replace("Z", "+00:00"))
                except ValueError:
                    pass
            return None

        topics: list[str] = []
        raw_topics = raw.get("topics")
        if isinstance(raw_topics, list):
            topics = [str(t) for t in raw_topics if t]

        return NormalizedRepository(
            github_id=int(raw["id"]),
            name=str(raw.get("name", "")),
            full_name=str(raw.get("full_name", "")),
            owner_login=str(owner_data.get("login", "")),
            owner_avatar_url=owner_data.get("avatar_url"),
            owner_html_url=owner_data.get("html_url"),
            description=raw.get("description"),
            html_url=str(raw.get("html_url", "")),
            language=raw.get("language"),
            topics=topics,
            stars=int(raw.get("stargazers_count", 0)),
            forks=int(raw.get("forks_count", 0)),
            open_issues=int(raw.get("open_issues_count", 0)),
            created_at=parse_dt(raw.get("created_at")),
            github_updated_at=parse_dt(raw.get("updated_at")),
            pushed_at=parse_optional_dt(raw.get("pushed_at")),
            readme_content=None,
        )

    async def search_repositories(self, params: RepositorySearchParams) -> RepositorySearchResponse:
        """Execute search, normalize results, and build pagination metadata (FR-007, FR-010)."""
        query_str = self.build_search_query(params)
        raw_response = await self.client.search_repositories(
            query=query_str,
            sort=params.sort,
            order=params.order,
            page=params.page,
            per_page=params.per_page,
        )

        raw_items: list[dict[str, Any]] = raw_response.get("items", [])
        normalized_items = [self.normalize_repository(item) for item in raw_items]

        total_count = int(raw_response.get("total_count", 0))
        # GitHub search is capped at 1000 accessible results
        capped_total = min(total_count, 1000)
        total_pages = max(1, math.ceil(capped_total / params.per_page))

        pagination = PaginationMetadata(
            page=params.page,
            per_page=params.per_page,
            total_count=total_count,
            total_pages=total_pages,
            has_next_page=params.page < total_pages,
            has_prev_page=params.page > 1,
        )

        return RepositorySearchResponse(
            items=normalized_items,
            pagination=pagination,
            rate_limit=self.client.latest_rate_limit,
        )

    async def get_readme(self, owner: str, repo: str) -> ReadmeResponse:
        """Retrieve README content for a given repository (FR-009)."""
        content, size, encoding = await self.client.get_readme(owner=owner, repo=repo)
        return ReadmeResponse(
            owner=owner,
            repo=repo,
            content=content,
            size=size,
            encoding=encoding,
        )

    async def discover_and_ingest(
        self,
        queries: list[RepositorySearchParams],
        fetch_readmes: bool = False,
    ) -> IngestionSummary:
        """Execute multiple discovery queries, normalize repositories, and identify duplicates (FR-010, 5.5)."""
        unique_repos_by_id: dict[int, NormalizedRepository] = {}
        total_discovered = 0

        for idx, query_params in enumerate(queries, start=1):
            logger.info("Executing discovery query %d of %d...", idx, len(queries))
            try:
                search_response = await self.search_repositories(query_params)
                total_discovered += len(search_response.items)

                for repo in search_response.items:
                    if repo.github_id not in unique_repos_by_id:
                        unique_repos_by_id[repo.github_id] = repo
            except Exception as e:
                logger.error("Discovery query %d failed: %s", idx, e)
                raise

        unique_repositories = list(unique_repos_by_id.values())
        duplicates_identified = total_discovered - len(unique_repositories)

        # Optionally enrich unique repositories with README content
        if fetch_readmes:
            for repo in unique_repositories:
                try:
                    content, _, _ = await self.client.get_readme(
                        owner=repo.owner_login,
                        repo=repo.name,
                    )
                    repo.readme_content = content
                except Exception as e:
                    logger.warning(
                        "Failed to fetch README during ingestion for %s/%s: %s",
                        repo.owner_login,
                        repo.name,
                        e,
                    )

        return IngestionSummary(
            total_queries=len(queries),
            total_discovered=total_discovered,
            unique_repositories=len(unique_repositories),
            duplicates_identified=duplicates_identified,
            items=unique_repositories,
        )

    async def get_rate_limit(self) -> GitHubRateLimitInfo:
        """Check current GitHub API rate limit status (FR-011)."""
        return await self.client.get_rate_limit()
