"""GitHub tools for MCP server."""

from typing import Any

from ..github import GitHubClient, GitHubAuth


def create_issue(
    repo: str,
    title: str,
    body: str,
    auth: GitHubAuth | None = None,
) -> dict[str, Any]:
    """Create a new issue on GitHub.

    Args:
        repo: Repository in 'owner/repo' format.
        title: Issue title.
        body: Issue body (Markdown).
        auth: Optional GitHub authentication. Uses default if not provided.

    Returns:
        Dictionary with issue information.
    """
    try:
        client = GitHubClient(auth=auth)
        result = client.create_issue(repo, title, body)
        client.close()
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


def post_review_comment(
    repo: str,
    pr_number: int,
    file: str,
    line: int,
    body: str,
    suggestion: str | None = None,
    auth: GitHubAuth | None = None,
) -> dict[str, Any]:
    """Post a review comment on a specific line of a PR.

    Args:
        repo: Repository in 'owner/repo' format.
        pr_number: Pull request number.
        file: File path relative to repo root.
        line: Line number to comment on.
        body: Comment body (Markdown).
        suggestion: Optional suggested code change.
        auth: Optional GitHub authentication. Uses default if not provided.

    Returns:
        Dictionary with comment information.
    """
    try:
        client = GitHubClient(auth=auth)
        result = client.post_review_comment(
            repo, pr_number, file, line, body, suggestion
        )
        client.close()
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


def post_issue_comment(
    repo: str,
    issue_number: int,
    body: str,
    auth: GitHubAuth | None = None,
) -> dict[str, Any]:
    """Post a comment on an issue or PR discussion.

    Args:
        repo: Repository in 'owner/repo' format.
        issue_number: Issue or PR number.
        body: Comment body (Markdown).
        auth: Optional GitHub authentication. Uses default if not provided.

    Returns:
        Dictionary with comment information.
    """
    try:
        client = GitHubClient(auth=auth)
        result = client.post_issue_comment(repo, issue_number, body)
        client.close()
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


def close_issue(
    repo: str,
    issue_number: int,
    comment: str | None = None,
    auth: GitHubAuth | None = None,
) -> dict[str, Any]:
    """Close an issue with optional comment.

    Args:
        repo: Repository in 'owner/repo' format.
        issue_number: Issue number to close.
        comment: Optional closing comment.
        auth: Optional GitHub authentication. Uses default if not provided.

    Returns:
        Dictionary with success status.
    """
    try:
        client = GitHubClient(auth=auth)
        result = client.close_issue(repo, issue_number, comment)
        client.close()
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}
