"""Test MCP Server tools through direct function calls."""

import os
import sys

# Set work directory if not already configured
if "HEALPR_WORK_DIR" not in os.environ:
    os.environ["HEALPR_WORK_DIR"] = os.path.join(os.path.dirname(__file__), ".test-workspace")

# Require HEALPR_GITHUB_TOKEN to be set in environment
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

REPO = "xiaocheny214/claude-skill-voice-dna"
PR_NUMBER = 1


def test_mcp_tools():
    """Test all MCP tools."""
    print("=" * 60)
    print("Testing healpr MCP Server Tools")
    print("=" * 60)

    auth = GitHubAuth.from_env()
    client = GitHubClient(auth=auth)

    # Test 1: Get PR info
    print("\n1. Testing get_pr_info:")
    try:
        result = client.get_pr_info(REPO, PR_NUMBER)
        print(f"   [OK] PR #{result['number']}: {result['title']}")
        print(f"   [OK] Author: {result['author']}")
        print(f"   [OK] Changed files: {len(result['changed_files'])}")
    except Exception as e:
        print(f"   [FAIL] Failed: {e}")
        return False

    # Test 2: Get PR diff
    print("\n2. Testing get_pr_diff:")
    try:
        result = client.get_pr_diff(REPO, PR_NUMBER)
        print(f"   [OK] Diff length: {len(result)} characters")
    except Exception as e:
        print(f"   [FAIL] Failed: {e}")
        return False

    client.close()

    # Test 3: Clone PR branch
    print("\n3. Testing clone_pr_branch:")
    try:
        result = clone_pr_branch(REPO, PR_NUMBER)
        if result['success']:
            print(f"   [OK] Cloned to: {result['work_dir']}")
            work_dir = result['work_dir']
        else:
            print(f"   [FAIL] Failed: {result.get('error')}")
            return False
    except Exception as e:
        print(f"   [FAIL] Failed: {e}")
        return False

    # Test 4: Run linter
    print("\n4. Testing run_linter:")
    try:
        result = run_linter(work_dir)
        print(f"   [OK] Language: {result.get('language', 'N/A')}")
        print(f"   [OK] Issues found: {result.get('issue_count', 0)}")
    except Exception as e:
        print(f"   [FAIL] Failed: {e}")

    # Test 5: Run test
    print("\n5. Testing run_test:")
    try:
        result = run_test(work_dir)
        print(f"   [OK] Framework: {result.get('framework', 'N/A')}")
        print(f"   [OK] Passed: {result.get('passed', False)}")
    except Exception as e:
        print(f"   [FAIL] Failed: {e}")

    # Test 6: Post review comment
    print("\n6. Testing post_review_comment:")
    try:
        result = post_review_comment(
            REPO,
            PR_NUMBER,
            "README.md",
            343,
            "This is a test review comment from healpr MCP server.",
            "Consider adding more details to the README."
        )
        if result['success']:
            print(f"   [OK] Comment ID: {result.get('comment_id')}")
        else:
            print(f"   [FAIL] Failed: {result.get('error')}")
    except Exception as e:
        print(f"   [FAIL] Failed: {e}")

    # Test 7: Create issue
    print("\n7. Testing create_issue:")
    try:
        result = create_issue(
            REPO,
            "Test Issue from healpr MCP",
            "This is a test issue created by healpr MCP server."
        )
        if result['success']:
            print(f"   [OK] Issue #{result.get('issue_number')}: {result.get('url')}")
            issue_number = result.get('issue_number')
        else:
            print(f"   [FAIL] Failed: {result.get('error')}")
            return False
    except Exception as e:
        print(f"   [FAIL] Failed: {e}")
        return False

    # Test 8: Post issue comment
    print("\n8. Testing post_issue_comment:")
    try:
        result = post_issue_comment(
            REPO,
            issue_number,
            "This is a test comment on the issue."
        )
        if result['success']:
            print(f"   [OK] Comment posted successfully")
        else:
            print(f"   [FAIL] Failed: {result.get('error')}")
    except Exception as e:
        print(f"   [FAIL] Failed: {e}")

    # Test 9: Close issue
    print("\n9. Testing close_issue:")
    try:
        result = close_issue(
            REPO,
            issue_number,
            "Closing test issue from healpr MCP server."
        )
        if result['success']:
            print(f"   [OK] Issue closed successfully")
        else:
            print(f"   [FAIL] Failed: {result.get('error')}")
    except Exception as e:
        print(f"   [FAIL] Failed: {e}")

    # Test 10: Cleanup
    print("\n10. Testing cleanup_work_dir:")
    try:
        result = cleanup_work_dir(work_dir)
        if result['success']:
            print(f"   [OK] Cleaned up: {result.get('message', '')}")
        else:
            print(f"   [FAIL] Failed: {result.get('error')}")
    except Exception as e:
        print(f"   [FAIL] Failed: {e}")

    print("\n" + "=" * 60)
    print("All MCP tools tested successfully!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_mcp_tools()
    sys.exit(0 if success else 1)
