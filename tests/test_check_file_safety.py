"""Tests for check_file_safety.py hook script."""

import subprocess
import sys
from pathlib import Path

HOOK_SCRIPT = Path(__file__).parent.parent / ".claude" / "hooks" / "check_file_safety.py"


def run_hook(file_path: str) -> int:
    """Run the hook script with a file path, return exit code."""
    result = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT), file_path],
        capture_output=True,
        text=True,
    )
    return result.returncode


class TestProjectFilesBlocked:
    def test_src_file_blocked(self):
        assert run_hook("src/healpr/server.py") == 1

    def test_claude_md_blocked(self):
        assert run_hook("CLAUDE.md") == 1

    def test_pyproject_blocked(self):
        assert run_hook("pyproject.toml") == 1

    def test_claude_dir_blocked(self):
        assert run_hook(".claude/settings.json") == 1


class TestWorkDirAllowed:
    def test_work_dir_file_allowed(self):
        assert run_hook(".test-workspace/repo-pr-1/file.py") == 0

    def test_work_dir_subdir_allowed(self):
        assert run_hook(".test-workspace/repo-pr-1/src/main.py") == 0


class TestOtherPathsBlocked:
    def test_random_path_blocked(self):
        assert run_hook("/etc/passwd") == 1

    def test_home_dir_blocked(self):
        assert run_hook("~/.bashrc") == 1

    def test_empty_path_blocked(self):
        assert run_hook("") == 1
