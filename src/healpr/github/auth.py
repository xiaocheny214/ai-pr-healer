"""GitHub authentication module."""

import os
from dataclasses import dataclass


@dataclass
class GitHubAuth:
    """GitHub authentication configuration."""

    token: str

    @classmethod
    def from_env(cls) -> "GitHubAuth":
        """Create auth from environment variables.

        Priority:
        1. HEALPR_GITHUB_TOKEN
        2. GITHUB_TOKEN
        """
        token = os.environ.get("HEALPR_GITHUB_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if not token:
            raise ValueError(
                "GitHub token not found. Set HEALPR_GITHUB_TOKEN or GITHUB_TOKEN environment variable."
            )
        return cls(token=token)

    def get_headers(self) -> dict[str, str]:
        """Get HTTP headers for GitHub API requests."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
