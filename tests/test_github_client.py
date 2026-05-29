"""Tests for GitHub API client."""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
import httpx

from healpr.github.auth import (
    GitHubAuth,
    TokenType,
    detect_token_type,
    fetch_token_scopes,
    Scope,
    SCOPE_HIERARCHY,
    TokenInfo,
)


@pytest.fixture
def mock_auth():
    """Create a mock auth instance."""
    return GitHubAuth(token="ghp_test-token-1234567890abcdef12345678")


@pytest.fixture
def client(mock_auth):
    """Create a GitHubClient with mock auth."""
    with patch("healpr.github.client.httpx.Client") as mock_httpx:
        mock_client = MagicMock()
        mock_httpx.return_value = mock_client
        yield GitHubClient(auth=mock_auth)


# Token Type Detection Tests

def test_detect_token_type_classic_pat():
    """Test detection of classic Personal Access Token."""
    assert detect_token_type("ghp_abc123") == TokenType.PERSONAL_ACCESS_TOKEN


def test_detect_token_type_fine_grained_pat():
    """Test detection of fine-grained Personal Access Token."""
    assert detect_token_type("github_pat_abc123") == TokenType.FINE_GRAINED_PAT


def test_detect_token_type_oauth():
    """Test detection of OAuth access token."""
    assert detect_token_type("gho_abc123") == TokenType.OAUTH_ACCESS_TOKEN


def test_detect_token_type_user_app():
    """Test detection of GitHub App user token."""
    assert detect_token_type("ghu_abc123") == TokenType.USER_TO_SERVER_APP


def test_detect_token_type_server_app():
    """Test detection of GitHub App installation token."""
    assert detect_token_type("ghs_abc123") == TokenType.SERVER_TO_SERVER_APP


def test_detect_token_type_unknown():
    """Test detection of unknown token type."""
    assert detect_token_type("unknown_token") == TokenType.UNKNOWN


# Token Info Tests

def test_token_info_is_valid():
    """Test TokenInfo validity check."""
    info = TokenInfo(token="ghp_test", token_type=TokenType.PERSONAL_ACCESS_TOKEN, scopes=[])
    assert info.is_valid is True

    info_unknown = TokenInfo(token="test", token_type=TokenType.UNKNOWN, scopes=[])
    assert info_unknown.is_valid is False


def test_token_info_is_classic_pat():
    """Test TokenInfo classic PAT check."""
    info = TokenInfo(token="ghp_test", token_type=TokenType.PERSONAL_ACCESS_TOKEN, scopes=[])
    assert info.is_classic_pat is True

    info_fine = TokenInfo(token="github_pat_test", token_type=TokenType.FINE_GRAINED_PAT, scopes=[])
    assert info_fine.is_classic_pat is False


def test_token_info_has_scope_direct():
    """Test TokenInfo scope check with direct scope."""
    info = TokenInfo(token="ghp_test", token_type=TokenType.PERSONAL_ACCESS_TOKEN, scopes=["repo"])
    assert info.has_scope("repo") is True
    assert info.has_scope("public_repo") is True  # repo grants public_repo


def test_token_info_has_scope_hierarchy():
    """Test TokenInfo scope check with hierarchy."""
    info = TokenInfo(token="ghp_test", token_type=TokenType.PERSONAL_ACCESS_TOKEN, scopes=["repo"])
    # repo grants: public_repo, security_events
    assert info.has_scope("public_repo") is True
    assert info.has_scope("security_events") is True
    assert info.has_scope("gist") is False


def test_token_info_has_scope_no_scope_required():
    """Test TokenInfo scope check when no scope is required."""
    info = TokenInfo(token="ghp_test", token_type=TokenType.PERSONAL_ACCESS_TOKEN, scopes=[])
    assert info.has_scope("") is True


# GitHubAuth Tests

def test_auth_headers(mock_auth):
    """Test that auth headers are correctly generated."""
    headers = mock_auth.get_headers()
    assert "Bearer ghp_test-token" in headers["Authorization"]
    assert "application/vnd.github.v3+json" in headers["Accept"]


def test_auth_from_env_missing():
    """Test that from_env raises error when token is missing."""
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError, match="GitHub token not found"):
            GitHubAuth.from_env()


def test_auth_from_env_healpr_token():
    """Test that from_env reads HEALPR_GITHUB_TOKEN."""
    with patch.dict("os.environ", {"HEALPR_GITHUB_TOKEN": "ghp_test-token"}):
        auth = GitHubAuth.from_env()
        assert auth.token == "ghp_test-token"
        assert auth.token_type == TokenType.PERSONAL_ACCESS_TOKEN


def test_auth_from_env_github_token():
    """Test that from_env reads GITHUB_TOKEN as fallback."""
    with patch.dict("os.environ", {"GITHUB_TOKEN": "ghp_test-token"}):
        auth = GitHubAuth.from_env()
        assert auth.token == "ghp_test-token"


def test_auth_token_type_detection():
    """Test automatic token type detection."""
    auth = GitHubAuth(token="github_pat_test")
    assert auth.token_type == TokenType.FINE_GRAINED_PAT


def test_auth_validate_scopes():
    """Test scope validation."""
    auth = GitHubAuth(token="ghp_test")

    with patch.object(auth, 'get_token_info') as mock_get_info:
        mock_get_info.return_value = TokenInfo(
            token="ghp_test",
            token_type=TokenType.PERSONAL_ACCESS_TOKEN,
            scopes=["repo", "read:org"]
        )

        # Should pass with required scopes
        is_valid, missing = auth.validate_scopes(["repo", "read:org"])
        assert is_valid is True
        assert missing == []

        # Should fail with missing scopes
        is_valid, missing = auth.validate_scopes(["repo", "gist"])
        assert is_valid is False
        assert "gist" in missing


# Scope Tests

def test_scope_hierarchy():
    """Test scope hierarchy relationships."""
    assert Scope.PUBLIC_REPO in SCOPE_HIERARCHY[Scope.REPO]
    assert Scope.SECURITY_EVENTS in SCOPE_HIERARCHY[Scope.REPO]
    assert Scope.READ_ORG in SCOPE_HIERARCHY[Scope.WRITE_ORG]


def test_fetch_token_scopes_success():
    """Test successful token scope fetching."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"X-OAuth-Scopes": "repo, read:org, gist"}

    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.head.return_value = mock_response

        scopes = fetch_token_scopes("ghp_test-token")
        assert scopes == ["repo", "read:org", "gist"]


def test_fetch_token_scopes_unauthorized():
    """Test token scope fetching with invalid token."""
    mock_response = MagicMock()
    mock_response.status_code = 401

    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.head.return_value = mock_response

        with pytest.raises(ValueError, match="Invalid or expired token"):
            fetch_token_scopes("ghp_invalid-token")


def test_fetch_token_scopes_empty_header():
    """Test token scope fetching with empty scopes header."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"X-OAuth-Scopes": ""}

    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.head.return_value = mock_response

        scopes = fetch_token_scopes("ghp_test-token")
        assert scopes == []
