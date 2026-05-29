"""Tests for GitHub API client."""

import pytest
from unittest.mock import MagicMock, patch

from healpr.github.auth import GitHubAuth
from healpr.github.client import GitHubClient


@pytest.fixture
def mock_auth():
    """Create a mock auth instance."""
    return GitHubAuth(token="test-token")


@pytest.fixture
def client(mock_auth):
    """Create a GitHubClient with mock auth."""
    with patch("healpr.github.client.httpx.Client") as mock_httpx:
        mock_client = MagicMock()
        mock_httpx.return_value = mock_client
        yield GitHubClient(auth=mock_auth)


def test_auth_headers(mock_auth):
    """Test that auth headers are correctly generated."""
    headers = mock_auth.get_headers()
    assert headers["Authorization"] == "Bearer test-token"
    assert "application/vnd.github.v3+json" in headers["Accept"]


def test_auth_from_env_missing():
    """Test that from_env raises error when token is missing."""
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError, match="GitHub token not found"):
            GitHubAuth.from_env()


def test_auth_from_env_healpr_token():
    """Test that from_env reads HEALPR_GITHUB_TOKEN."""
    with patch.dict("os.environ", {"HEALPR_GITHUB_TOKEN": "test-token"}):
        auth = GitHubAuth.from_env()
        assert auth.token == "test-token"


def test_auth_from_env_github_token():
    """Test that from_env reads GITHUB_TOKEN as fallback."""
    with patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}):
        auth = GitHubAuth.from_env()
        assert auth.token == "test-token"
