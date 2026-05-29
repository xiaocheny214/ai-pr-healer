"""Git operations tools for MCP server."""

import os
import stat
import subprocess
import shutil
from pathlib import Path
from typing import Any


def _remove_readonly(func, path, excinfo):
    """Error handler for shutil.rmtree on Windows.

    Git creates read-only files in .git/objects/ that prevent deletion.
    This handler makes them writable and retries.
    """
    os.chmod(path, stat.S_IWRITE)
    func(path)


def clone_pr_branch(repo: str, pr_number: int, work_dir: str | None = None) -> dict[str, Any]:
    """Clone a PR branch to local workspace.

    Args:
        repo: Repository in 'owner/repo' format.
        pr_number: Pull request number.
        work_dir: Working directory path. Defaults to /tmp/healpr-workspace.

    Returns:
        Dictionary with work_dir path and success status.
    """
    if work_dir is None:
        work_dir = os.environ.get("HEALPR_WORK_DIR", "/tmp/healpr-workspace")

    # Create unique directory for this PR
    repo_name = repo.split("/")[-1]
    pr_dir = Path(work_dir) / f"{repo_name}-pr-{pr_number}"

    # Clean up existing directory if it exists
    if pr_dir.exists():
        shutil.rmtree(pr_dir, onerror=_remove_readonly)

    # Ensure parent directory exists
    pr_dir.parent.mkdir(parents=True, exist_ok=True)

    # Clone to a temporary directory first, then move
    temp_dir = pr_dir.parent / f"temp-{repo_name}-pr-{pr_number}"
    if temp_dir.exists():
        shutil.rmtree(temp_dir, onerror=_remove_readonly)

    try:
        # Set environment to prevent git from waiting for authentication input
        git_env = os.environ.copy()
        git_env["GIT_TERMINAL_PROMPT"] = "0"
        git_env["GIT_ASKPASS"] = "echo"

        # Clone the repository with depth 1 to temp directory
        clone_url = f"https://github.com/{repo}.git"
        subprocess.run(
            ["git", "clone", "--depth", "1", clone_url, str(temp_dir)],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
            env=git_env,
        )

        # Fetch the PR branch
        subprocess.run(
            ["git", "fetch", "origin", f"pull/{pr_number}/head:pr-{pr_number}"],
            check=True,
            capture_output=True,
            text=True,
            cwd=str(temp_dir),
            timeout=30,
            env=git_env,
        )

        # Checkout the PR branch
        subprocess.run(
            ["git", "checkout", f"pr-{pr_number}"],
            check=True,
            capture_output=True,
            text=True,
            cwd=str(temp_dir),
            timeout=10,
            env=git_env,
        )

        # Move to final directory
        if pr_dir.exists():
            shutil.rmtree(pr_dir, onerror=_remove_readonly)
        shutil.move(str(temp_dir), str(pr_dir))

        return {
            "success": True,
            "work_dir": str(pr_dir),
            "message": f"PR #{pr_number} cloned to {pr_dir}",
        }

    except subprocess.TimeoutExpired:
        # Clean up temp directory on failure
        if temp_dir.exists():
            shutil.rmtree(temp_dir, onerror=_remove_readonly)
        return {
            "success": False,
            "error": "Git operation timed out",
            "work_dir": str(pr_dir),
        }
    except subprocess.CalledProcessError as e:
        # Clean up temp directory on failure
        if temp_dir.exists():
            shutil.rmtree(temp_dir, onerror=_remove_readonly)
        return {
            "success": False,
            "error": f"Git command failed: {e.stderr}",
            "work_dir": str(pr_dir),
        }


def cleanup_work_dir(work_dir: str) -> dict[str, Any]:
    """Clean up a work directory.

    Args:
        work_dir: Path to the work directory to clean up.

    Returns:
        Dictionary with success status.
    """
    try:
        work_path = Path(work_dir)
        if work_path.exists():
            shutil.rmtree(work_path, onerror=_remove_readonly)
            return {"success": True, "message": f"Cleaned up {work_dir}"}
        else:
            return {"success": True, "message": f"Directory {work_dir} does not exist"}
    except Exception as e:
        return {"success": False, "error": str(e)}
