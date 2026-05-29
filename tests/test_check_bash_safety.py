"""Tests for check_bash_safety.py hook script."""

import subprocess
import sys
from pathlib import Path

HOOK_SCRIPT = Path(__file__).parent.parent / ".claude" / "hooks" / "check_bash_safety.py"


def run_hook(command: str) -> int:
    """Run the hook script with a command string, return exit code."""
    result = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT), command],
        capture_output=True,
        text=True,
    )
    return result.returncode


class TestGitPushBlocked:
    def test_git_push_blocked(self):
        assert run_hook("git push origin main") == 1

    def test_git_push_force_blocked(self):
        assert run_hook("git push --force origin main") == 1

    def test_git_push_short_blocked(self):
        assert run_hook("git push") == 1


class TestGitAmendBlocked:
    def test_git_commit_amend_blocked(self):
        assert run_hook("git commit --amend -m 'fix'") == 1

    def test_amend_only_blocked(self):
        assert run_hook("git commit --amend") == 1


class TestRmRfRootBlocked:
    def test_rm_rf_root_blocked(self):
        assert run_hook("rm -rf /") == 1

    def test_rm_rf_root_backslash_blocked(self):
        assert run_hook("rm -rf C:\\") == 1

    def test_rm_rf_root_drive_c_blocked(self):
        assert run_hook("rm -rf C:/") == 1


class TestSafeCommandsAllowed:
    def test_git_status_allowed(self):
        assert run_hook("git status") == 0

    def test_git_diff_allowed(self):
        assert run_hook("git diff") == 0

    def test_git_commit_allowed(self):
        assert run_hook("git commit -m 'test'") == 0

    def test_ls_allowed(self):
        assert run_hook("ls -la") == 0

    def test_rm_non_root_allowed(self):
        assert run_hook("rm -rf /tmp/test") == 0

    def test_git_clone_allowed(self):
        assert run_hook("git clone https://github.com/user/repo.git") == 0
