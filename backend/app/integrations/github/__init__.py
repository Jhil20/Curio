"""GitHub API integration package."""

from app.integrations.github.client import GitHubClient, get_github_client

__all__ = ["GitHubClient", "get_github_client"]
