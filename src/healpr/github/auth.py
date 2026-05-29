"""GitHub authentication module with token type detection and scope management."""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import httpx


class TokenType(Enum):
    """GitHub token types based on prefix."""

    PERSONAL_ACCESS_TOKEN = "ghp_"           # Classic PAT
    FINE_GRAINED_PAT = "github_pat_"         # Fine-grained PAT
    OAUTH_ACCESS_TOKEN = "gho_"              # OAuth access token
    USER_TO_SERVER_APP = "ghu_"              # GitHub App user token
    SERVER_TO_SERVER_APP = "ghs_"            # GitHub App installation token
    UNKNOWN = "unknown"


# Token prefix mapping
TOKEN_PREFIXES = {
    "ghp_": TokenType.PERSONAL_ACCESS_TOKEN,
    "github_pat_": TokenType.FINE_GRAINED_PAT,
    "gho_": TokenType.OAUTH_ACCESS_TOKEN,
    "ghu_": TokenType.USER_TO_SERVER_APP,
    "ghs_": TokenType.SERVER_TO_SERVER_APP,
}


class Scope:
    """GitHub OAuth scopes."""

    NO_SCOPE = ""
    REPO = "repo"
    PUBLIC_REPO = "public_repo"
    READ_ORG = "read:org"
    WRITE_ORG = "write:org"
    ADMIN_ORG = "admin:org"
    GIST = "gist"
    NOTIFICATIONS = "notifications"
    READ_PROJECT = "read:project"
    PROJECT = "project"
    SECURITY_EVENTS = "security_events"
    USER = "user"
    READ_USER = "read:user"
    USER_EMAIL = "user:email"
    READ_PACKAGES = "read:packages"
    WRITE_PACKAGES = "write:packages"


# Scope hierarchy: parent scope grants access to child scopes
SCOPE_HIERARCHY = {
    Scope.REPO: [Scope.PUBLIC_REPO, Scope.SECURITY_EVENTS],
    Scope.ADMIN_ORG: [Scope.WRITE_ORG, Scope.READ_ORG],
    Scope.WRITE_ORG: [Scope.READ_ORG],
    Scope.PROJECT: [Scope.READ_PROJECT],
    Scope.WRITE_PACKAGES: [Scope.READ_PACKAGES],
    Scope.USER: [Scope.READ_USER, Scope.USER_EMAIL],
}


@dataclass
class TokenInfo:
    """Token information including type and scopes."""

    token: str
    token_type: TokenType
    scopes: list[str]

    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not unknown type)."""
        return self.token_type != TokenType.UNKNOWN

    @property
    def is_classic_pat(self) -> bool:
        """Check if token is a classic Personal Access Token."""
        return self.token_type == TokenType.PERSONAL_ACCESS_TOKEN

    def has_scope(self, required_scope: str) -> bool:
        """Check if token has the required scope.

        Considers scope hierarchy - if token has 'repo', it also has 'public_repo'.
        """
        if required_scope == Scope.NO_SCOPE:
            return True

        # Check direct scope
        if required_scope in self.scopes:
            return True

        # Check if any parent scope grants the required scope
        for parent, children in SCOPE_HIERARCHY.items():
            if parent in self.scopes and required_scope in children:
                return True

        return False


def detect_token_type(token: str) -> TokenType:
    """Detect token type based on prefix."""
    for prefix, token_type in TOKEN_PREFIXES.items():
        if token.startswith(prefix):
            return token_type
    return TokenType.UNKNOWN


def fetch_token_scopes(token: str, api_host: str = "https://api.github.com") -> list[str]:
    """Fetch OAuth scopes for a token by making a HEAD request to GitHub API.

    Note: Only classic PATs return OAuth scopes via X-OAuth-Scopes header.
    Fine-grained PATs and other token types return empty scopes.
    """
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.head(
                f"{api_host}/",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )

            if response.status_code == 401:
                raise ValueError("Invalid or expired token")

            if response.status_code != 200:
                raise ValueError(f"Unexpected status code: {response.status_code}")

            # Parse X-OAuth-Scopes header
            scopes_header = response.headers.get("X-OAuth-Scopes", "")
            if not scopes_header:
                return []

            return [scope.strip() for scope in scopes_header.split(",") if scope.strip()]

    except httpx.RequestError as e:
        raise ValueError(f"Failed to fetch token scopes: {e}")


@dataclass
class GitHubAuth:
    """GitHub authentication configuration."""

    token: str
    token_type: Optional[TokenType] = None
    _scopes: Optional[list[str]] = None

    def __post_init__(self):
        """Initialize token type if not provided."""
        if self.token_type is None:
            self.token_type = detect_token_type(self.token)

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

    def get_token_info(self) -> TokenInfo:
        """Get complete token information including scopes."""
        if self._scopes is None:
            # Only fetch scopes for classic PATs
            if self.token_type == TokenType.PERSONAL_ACCESS_TOKEN:
                try:
                    self._scopes = fetch_token_scopes(self.token)
                except ValueError:
                    self._scopes = []
            else:
                self._scopes = []

        return TokenInfo(
            token=self.token,
            token_type=self.token_type,
            scopes=self._scopes,
        )

    def validate_scopes(self, required_scopes: list[str]) -> tuple[bool, list[str]]:
        """Validate that token has required scopes.

        Returns:
            Tuple of (is_valid, missing_scopes)
        """
        token_info = self.get_token_info()
        missing = []

        for scope in required_scopes:
            if not token_info.has_scope(scope):
                missing.append(scope)

        return len(missing) == 0, missing
