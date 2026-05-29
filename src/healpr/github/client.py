"""GitHub API client."""

from typing import Any

import httpx

from .auth import GitHubAuth

GITHUB_API_BASE = "https://api.github.com"


class GitHubClient:
    """GitHub API client for PR review operations."""

    def __init__(self, auth: GitHubAuth | None = None):
        self.auth = auth or GitHubAuth.from_env()
        self.client = httpx.Client(
            base_url=GITHUB_API_BASE,
            headers=self.auth.get_headers(),
            timeout=30.0,
        )

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def _request(self, method: str, path: str, **kwargs) -> dict[str, Any]:
        """Make a request to GitHub API."""
        response = self.client.request(method, path, **kwargs)
        response.raise_for_status()
        return response.json() if response.content else {}

    def get_pr_info(self, repo: str, pr_number: int) -> dict[str, Any]:
        """Get pull request information.

        Args:
            repo: Repository in "owner/repo" format.
            pr_number: Pull request number.

        Returns:
            PR information including title, description, author, base/head branches, and changed files.
        """
        pr_data = self._request("GET", f"/repos/{repo}/pulls/{pr_number}")

        # Get changed files
        files_data = self._request("GET", f"/repos/{repo}/pulls/{pr_number}/files")

        return {
            "number": pr_data["number"],
            "title": pr_data["title"],
            "body": pr_data.get("body", ""),
            "author": pr_data["user"]["login"],
            "state": pr_data["state"],
            "base_branch": pr_data["base"]["ref"],
            "head_branch": pr_data["head"]["ref"],
            "head_sha": pr_data["head"]["sha"],
            "changed_files": [
                {
                    "filename": f["filename"],
                    "status": f["status"],
                    "additions": f["additions"],
                    "deletions": f["deletions"],
                }
                for f in files_data
            ],
            "url": pr_data["html_url"],
        }

    def get_pr_diff(self, repo: str, pr_number: int) -> str:
        """Get pull request diff.

        Args:
            repo: Repository in "owner/repo" format.
            pr_number: Pull request number.

        Returns:
            Unified diff text of the PR.
        """
        response = self.client.request(
            "GET",
            f"/repos/{repo}/pulls/{pr_number}",
            headers={"Accept": "application/vnd.github.v3.diff"},
        )
        response.raise_for_status()
        return response.text

    def create_issue(self, repo: str, title: str, body: str) -> dict[str, Any]:
        """Create a new issue.

        Args:
            repo: Repository in "owner/repo" format.
            title: Issue title.
            body: Issue body (Markdown).

        Returns:
            Created issue information.
        """
        data = self._request(
            "POST",
            f"/repos/{repo}/issues",
            json={"title": title, "body": body},
        )
        return {
            "issue_number": data["number"],
            "url": data["html_url"],
        }

    def post_review_comment(
        self,
        repo: str,
        pr_number: int,
        file: str,
        line: int,
        body: str,
        suggestion: str | None = None,
    ) -> dict[str, Any]:
        """Post a review comment on a specific line of a PR.

        Args:
            repo: Repository in "owner/repo" format.
            pr_number: Pull request number.
            file: File path relative to repo root.
            line: Line number to comment on.
            body: Comment body (Markdown).
            suggestion: Optional suggested code change.

        Returns:
            Created comment information.
        """
        # Get the latest commit SHA for the PR
        pr_data = self._request("GET", f"/repos/{repo}/pulls/{pr_number}")
        commit_id = pr_data["head"]["sha"]

        comment_body = body
        if suggestion:
            comment_body += f"\n\n```suggestion\n{suggestion}\n```"

        data = self._request(
            "POST",
            f"/repos/{repo}/pulls/{pr_number}/comments",
            json={
                "body": comment_body,
                "commit_id": commit_id,
                "path": file,
                "line": line,
            },
        )
        return {
            "comment_id": data["id"],
            "url": data["html_url"],
        }

    def post_issue_comment(self, repo: str, issue_number: int, body: str) -> dict[str, Any]:
        """Post a comment on an issue (or PR discussion).

        Args:
            repo: Repository in "owner/repo" format.
            issue_number: Issue or PR number.
            body: Comment body (Markdown).

        Returns:
            Created comment information.
        """
        data = self._request(
            "POST",
            f"/repos/{repo}/issues/{issue_number}/comments",
            json={"body": body},
        )
        return {
            "comment_id": data["id"],
            "url": data["html_url"],
        }

    def close_issue(self, repo: str, issue_number: int, comment: str | None = None) -> dict[str, Any]:
        """Close an issue with optional comment.

        Args:
            repo: Repository in "owner/repo" format.
            issue_number: Issue number to close.
            comment: Optional closing comment.

        Returns:
            Result with success status.
        """
        if comment:
            self.post_issue_comment(repo, issue_number, comment)

        self._request(
            "PATCH",
            f"/repos/{repo}/issues/{issue_number}",
            json={"state": "closed"},
        )
        return {"success": True}
