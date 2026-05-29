"""Manual integration test for healpr MCP Server tools.

WARNING: This test writes to real GitHub repositories (posts comments,
creates and closes issues). Use --dry-run to preview without side effects.

Usage:
    export HEALPR_GITHUB_TOKEN='your_token'
    python manual_integration_test.py [--dry-run] [--repo owner/repo] [--pr 123]
"""

import argparse
import os
import sys

if "HEALPR_WORK_DIR" not in os.environ:
    os.environ["HEALPR_WORK_DIR"] = os.path.join(os.path.dirname(__file__), ".test-workspace")

if "HEALPR_GITHUB_TOKEN" not in os.environ:
    print("Error: HEALPR_GITHUB_TOKEN environment variable is required.")
    print("Set it with: export HEALPR_GITHUB_TOKEN='your_token_here'")
    sys.exit(1)

from healpr.github import GitHubClient, GitHubAuth
from healpr.tools import (
    clone_pr_branch,
    cleanup_work_dir,
    run_linter,
    run_test,
    create_issue,
    post_review_comment,
    post_issue_comment,
    close_issue,
)

DEFAULT_REPO = "xiaocheny214/ai-pr-healer"
DEFAULT_PR = 1


def test_mcp_tools(dry_run=False, repo=DEFAULT_REPO, pr_number=DEFAULT_PR):
    """Test all MCP tools."""
    print("=" * 60)
    print("Testing healpr MCP Server Tools")
    print(f"  Repo: {repo}")
    print(f"  PR: #{pr_number}")
    print(f"  Dry run: {dry_run}")
    print("=" * 60)

    work_dir = None
    issue_number = None
    passed = 0
    failed = 0

    try:
        auth = GitHubAuth.from_env()
        client = GitHubClient(auth=auth)

        # Test 1: Get PR info
        print("\n1. Testing get_pr_info:")
        try:
            result = client.get_pr_info(repo, pr_number)
            print(f"   [OK] PR #{result['number']}: {result['title']}")
            print(f"   [OK] Author: {result['author']}")
            print(f"   [OK] Changed files: {len(result['changed_files'])}")
            passed += 1
        except Exception as e:
            print(f"   [FAIL] {e}")
            failed += 1

        # Test 2: Get PR diff
        print("\n2. Testing get_pr_diff:")
        try:
            result = client.get_pr_diff(repo, pr_number)
            print(f"   [OK] Diff length: {len(result)} characters")
            passed += 1
        except Exception as e:
            print(f"   [FAIL] {e}")
            failed += 1

        client.close()

        # Test 3: Clone PR branch
        print("\n3. Testing clone_pr_branch:")
        try:
            result = clone_pr_branch(repo, pr_number)
            if result['success']:
                work_dir = result['work_dir']
                print(f"   [OK] Cloned to: {work_dir}")
                passed += 1
            else:
                print(f"   [FAIL] {result.get('error')}")
                failed += 1
        except Exception as e:
            print(f"   [FAIL] {e}")
            failed += 1

        # Test 4: Run linter (only if clone succeeded)
        if work_dir:
            print("\n4. Testing run_linter:")
            try:
                result = run_linter(work_dir)
                print(f"   [OK] Language: {result.get('language', 'N/A')}")
                print(f"   [OK] Issues found: {result.get('issue_count', 0)}")
                passed += 1
            except Exception as e:
                print(f"   [FAIL] {e}")
                failed += 1

            # Test 5: Run test
            print("\n5. Testing run_test:")
            try:
                result = run_test(work_dir)
                print(f"   [OK] Framework: {result.get('framework', 'N/A')}")
                print(f"   [OK] Passed: {result.get('passed', False)}")
                passed += 1
            except Exception as e:
                print(f"   [FAIL] {e}")
                failed += 1

        # Tests 6-9: GitHub write operations (skipped in dry-run)
        if dry_run:
            for i, name in enumerate(
                ["post_review_comment", "create_issue", "post_issue_comment", "close_issue"], 6
            ):
                print(f"\n{i}. Testing {name}:")
                print(f"   [SKIP] Dry run — would write to GitHub")
        else:
            # Test 6: Post review comment
            print("\n6. Testing post_review_comment:")
            try:
                result = post_review_comment(
                    repo, pr_number, "README.md", 1,
                    "Test review comment from healpr integration test.",
                    "This is an automated test comment."
                )
                if result['success']:
                    print(f"   [OK] Comment ID: {result.get('comment_id')}")
                    passed += 1
                else:
                    print(f"   [FAIL] {result.get('error')}")
                    failed += 1
            except Exception as e:
                print(f"   [FAIL] {e}")
                failed += 1

            # Test 7: Create issue
            print("\n7. Testing create_issue:")
            try:
                result = create_issue(
                    repo,
                    "[test] Integration test issue from healpr",
                    "This is a test issue created by healpr integration test."
                )
                if result['success']:
                    issue_number = result.get('issue_number')
                    print(f"   [OK] Issue #{issue_number}: {result.get('url')}")
                    passed += 1
                else:
                    print(f"   [FAIL] {result.get('error')}")
                    failed += 1
            except Exception as e:
                print(f"   [FAIL] {e}")
                failed += 1

            # Test 8: Post issue comment (only if issue was created)
            if issue_number:
                print("\n8. Testing post_issue_comment:")
                try:
                    result = post_issue_comment(
                        repo, issue_number,
                        "Test comment on issue from healpr integration test."
                    )
                    if result['success']:
                        print(f"   [OK] Comment posted")
                        passed += 1
                    else:
                        print(f"   [FAIL] {result.get('error')}")
                        failed += 1
                except Exception as e:
                    print(f"   [FAIL] {e}")
                    failed += 1

                # Test 9: Close issue
                print("\n9. Testing close_issue:")
                try:
                    result = close_issue(
                        repo, issue_number,
                        "Closing test issue from healpr integration test."
                    )
                    if result['success']:
                        print(f"   [OK] Issue closed")
                        passed += 1
                    else:
                        print(f"   [FAIL] {result.get('error')}")
                        failed += 1
                except Exception as e:
                    print(f"   [FAIL] {e}")
                    failed += 1
            else:
                print("\n8. Testing post_issue_comment:")
                print(f"   [SKIP] No issue created")
                print("\n9. Testing close_issue:")
                print(f"   [SKIP] No issue created")

        # Test 10: Cleanup
        if work_dir:
            print("\n10. Testing cleanup_work_dir:")
            try:
                result = cleanup_work_dir(work_dir)
                if result['success']:
                    print(f"   [OK] Cleaned up: {result.get('message', '')}")
                    passed += 1
                else:
                    print(f"   [FAIL] {result.get('error')}")
                    failed += 1
                work_dir = None
            except Exception as e:
                print(f"   [FAIL] {e}")
                failed += 1

    finally:
        # Always clean up work directory, even on failure
        if work_dir:
            print("\n[CLEANUP] Cleaning up work directory after failure...")
            try:
                cleanup_work_dir(work_dir)
                print(f"   [OK] Cleaned up: {work_dir}")
            except Exception as e:
                print(f"   [WARN] Cleanup failed: {e}")

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    return failed == 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="healpr MCP integration test")
    parser.add_argument("--dry-run", action="store_true", help="Skip GitHub write operations")
    parser.add_argument("--repo", default=DEFAULT_REPO, help="Target repo (owner/repo)")
    parser.add_argument("--pr", type=int, default=DEFAULT_PR, help="Target PR number")
    args = parser.parse_args()

    success = test_mcp_tools(dry_run=args.dry_run, repo=args.repo, pr_number=args.pr)
    sys.exit(0 if success else 1)
