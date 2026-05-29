"""GitHub API module."""

from .auth import (
    GitHubAuth,
    TokenType,
    TokenInfo,
    Scope,
    detect_token_type,
    fetch_token_scopes,
)
from .client import GitHubClient

__all__ = [
    "GitHubAuth",
    "GitHubClient",
    "TokenType",
    "TokenInfo",
    "Scope",
    "detect_token_type",
    "fetch_token_scopes",
]
