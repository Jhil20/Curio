from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RepositorySearchParams(BaseModel):
    """Parameters for GitHub repository search (FR-007)."""

    model_config = ConfigDict(extra="ignore")

    language: str | None = Field(default=None, description="Primary programming language")
    topic: str | None = Field(default=None, description="Repository topic")
    min_stars: int | None = Field(default=None, ge=0, description="Minimum star count")
    min_forks: int | None = Field(default=None, ge=0, description="Minimum fork count")
    created_after: date | str | None = Field(
        default=None,
        description="Repository creation date (YYYY-MM-DD or ISO format)",
    )
    updated_after: date | str | None = Field(
        default=None,
        description="Repository last update/push date (YYYY-MM-DD or ISO format)",
    )
    sort: Literal["stars", "forks", "help-wanted-issues", "updated"] | None = Field(
        default=None,
        description="GitHub search sorting field",
    )
    order: Literal["asc", "desc"] = Field(
        default="desc",
        description="Sorting direction",
    )
    page: int = Field(default=1, ge=1, le=100, description="Pagination page")
    per_page: int = Field(
        default=30,
        ge=1,
        le=100,
        description="Number of results per page (GitHub max 100)",
    )
    query: str | None = Field(
        default=None,
        description="Optional custom query term or additional search keywords",
    )


class GitHubOwner(BaseModel):
    """Repository owner information."""

    model_config = ConfigDict(extra="ignore")

    login: str
    id: int | None = None
    avatar_url: str | None = None
    html_url: str | None = None
    type: str | None = None


class NormalizedRepository(BaseModel):
    """Normalized repository data matching Stage 3 persistence requirements (FR-008, 5.4)."""

    model_config = ConfigDict(extra="ignore")

    github_id: int = Field(description="Unique GitHub repository ID")
    name: str = Field(description="Repository name")
    full_name: str = Field(description="Full repository name (owner/repo)")
    owner_login: str = Field(description="Repository owner username")
    owner_avatar_url: str | None = Field(default=None, description="Owner avatar URL")
    owner_html_url: str | None = Field(default=None, description="Owner profile URL")
    description: str | None = Field(default=None, description="Repository description")
    html_url: str = Field(description="GitHub repository URL")
    language: str | None = Field(default=None, description="Primary programming language")
    topics: list[str] = Field(default_factory=list, description="Repository topics")
    stars: int = Field(default=0, ge=0, description="Current star count")
    forks: int = Field(default=0, ge=0, description="Current fork count")
    open_issues: int = Field(default=0, ge=0, description="Current open issue count")
    created_at: datetime = Field(description="Repository creation timestamp")
    github_updated_at: datetime = Field(description="Last update timestamp on GitHub")
    pushed_at: datetime | None = Field(default=None, description="Last push timestamp on GitHub")
    readme_content: str | None = Field(
        default=None,
        description="Retrieved README content if fetched",
    )


class GitHubRateLimitInfo(BaseModel):
    """GitHub rate-limit quota details (FR-011)."""

    model_config = ConfigDict(extra="ignore")

    limit: int = Field(description="Rate limit quota in current window")
    remaining: int = Field(description="Remaining requests in current window")
    reset_at: datetime = Field(description="Timestamp when quota window resets")
    used: int = Field(default=0, description="Requests used in current window")
    resource: str = Field(default="core", description="Rate-limited resource")


class PaginationMetadata(BaseModel):
    """Pagination tracking within GitHub limits (FR-010)."""

    model_config = ConfigDict(extra="ignore")

    page: int
    per_page: int
    total_count: int
    total_pages: int
    has_next_page: bool
    has_prev_page: bool


class RepositorySearchResponse(BaseModel):
    """Search response containing normalized repositories, pagination, and rate limit status."""

    model_config = ConfigDict(extra="ignore")

    items: list[NormalizedRepository]
    pagination: PaginationMetadata
    rate_limit: GitHubRateLimitInfo | None = None


class BatchDiscoveryRequest(BaseModel):
    """Request payload for manual administrative discovery/ingestion (FR-007, 5.5)."""

    model_config = ConfigDict(extra="ignore")

    queries: list[RepositorySearchParams] = Field(
        min_length=1,
        description="List of discovery query parameter sets to execute",
    )
    fetch_readmes: bool = Field(
        default=False,
        description="Whether to fetch README content for unique discovered repositories",
    )


class IngestionSummary(BaseModel):
    """Summary of discovery and normalization, with duplicate detection (FR-010, 5.5)."""

    model_config = ConfigDict(extra="ignore")

    total_queries: int
    total_discovered: int
    unique_repositories: int
    duplicates_identified: int
    items: list[NormalizedRepository]


class ReadmeResponse(BaseModel):
    """Retrieved README representation (FR-009)."""

    model_config = ConfigDict(extra="ignore")

    owner: str
    repo: str
    content: str | None = Field(default=None, description="Raw markdown content of README")
    size: int | None = Field(default=None, description="README file size in bytes")
    encoding: str | None = Field(default=None, description="Content encoding")
