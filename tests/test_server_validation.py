"""Tests for MCP server tool argument validation."""

import os
import pytest
from pathlib import Path
from unittest.mock import patch


@pytest.fixture
def server(monkeypatch):
    """Create a test server instance with isolated env vars."""
    monkeypatch.setenv("HEALPR_GITHUB_TOKEN", "test-token")
    monkeypatch.setenv("HEALPR_WORK_DIR", "/tmp/test-workspace")
    with patch("healpr.server.GitHubAuth"):
        from healpr.server import HealprServer
        srv = HealprServer()
    return srv


class TestPathValidation:
    def test_clone_to_allowed_dir(self, server):
        """clone_pr_branch to allowed work_dir should pass."""
        server._validate_tool_args("clone_pr_branch", {
            "repo": "user/repo",
            "pr_number": 1,
        })

    def test_cleanup_root_blocked(self, server):
        """cleanup_work_dir with root path should be blocked."""
        with pytest.raises(ValueError, match="禁止清理根目录"):
            server._validate_tool_args("cleanup_work_dir", {
                "work_dir": "/",
            })

    def test_cleanup_windows_root_blocked(self, server):
        """cleanup_work_dir with Windows root should be blocked."""
        with pytest.raises(ValueError, match="禁止清理根目录"):
            server._validate_tool_args("cleanup_work_dir", {
                "work_dir": "C:\\",
            })

    def test_cleanup_traversal_blocked(self, server):
        """cleanup_work_dir with path traversal should be blocked."""
        with pytest.raises(ValueError, match="路径禁止包含"):
            server._validate_tool_args("cleanup_work_dir", {
                "work_dir": "/tmp/test-workspace/../../../etc",
            })


class TestRepoValidation:
    def test_first_call_records_repo(self, server):
        """First get_pr_info call should record target repo."""
        server._validate_tool_args("get_pr_info", {
            "repo": "user/repo",
            "pr_number": 1,
        })
        assert server.target_repo == "user/repo"

    def test_mismatched_repo_blocked(self, server):
        """GitHub operations with mismatched repo should be blocked."""
        server.target_repo = "user/repo"
        with pytest.raises(ValueError, match="非目标仓库"):
            server._validate_tool_args("create_issue", {
                "repo": "other/repo",
                "title": "test",
                "body": "test",
            })

    def test_matched_repo_allowed(self, server):
        """GitHub operations with matched repo should pass."""
        server.target_repo = "user/repo"
        server._validate_tool_args("create_issue", {
            "repo": "user/repo",
            "title": "test",
            "body": "test",
        })

    def test_unset_target_repo_allows_first_call(self, server):
        """When target_repo is not set, allow and record."""
        assert server.target_repo is None
        server._validate_tool_args("create_issue", {
            "repo": "user/repo",
            "title": "test",
            "body": "test",
        })
        assert server.target_repo == "user/repo"
