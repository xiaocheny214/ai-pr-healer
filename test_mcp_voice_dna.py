"""Test MCP Server with claude-skill-voice-dna repository."""

import os
import sys

# Set token and work directory for Windows
os.environ["HEALPR_GITHUB_TOKEN"] = "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"
os.environ["HEALPR_WORK_DIR"] = os.path.join(os.path.dirname(__file__), ".test-workspace")

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


def test_github_client():
    """Test GitHub client tools."""
    print("=" * 60)
    print("Testing GitHub Client with voice-dna repo")
    print("=" * 60)

    auth = GitHubAuth.from_env()
    client = GitHubClient(auth=auth)

    # Test 1: Get PR info
    print("\n1. Testing get_pr_info:")
    try:
        result = client.get_pr_info(REPO, PR_NUMBER)
        print(f"   PR #{result['number']}: {result['title']}")
        print(f"   Author: {result['author']}")
        print(f"   Changed files: {len(result['changed_files'])}")
        print("   [OK] get_pr_info passed")
    except Exception as e:
        print(f"   [FAIL] get_pr_info failed: {e}")
        return False

    # Test 2: Get PR diff
    print("\n2. Testing get_pr_diff:")
    try:
        result = client.get_pr_diff(REPO, PR_NUMBER)
        print(f"   Diff length: {len(result)} characters")
        print("   [OK] get_pr_diff passed")
    except Exception as e:
        print(f"   [FAIL] get_pr_diff failed: {e}")
        return False

    client.close()
    return True


def test_local_tools():
    """Test local operation tools."""
    print("\n" + "=" * 60)
    print("Testing Local Operation Tools")
    print("=" * 60)

    # Test 3: Clone PR branch
    print("\n3. Testing clone_pr_branch:")
    try:
        result = clone_pr_branch(REPO, PR_NUMBER)
        print(f"   Success: {result['success']}")
        print(f"   Work dir: {result.get('work_dir', 'N/A')}")
        if result['success']:
            print("   [OK] clone_pr_branch passed")
            work_dir = result['work_dir']
        else:
            print(f"   [FAIL] clone_pr_branch failed: {result.get('error')}")
            return False, None
    except Exception as e:
        print(f"   [FAIL] clone_pr_branch failed: {e}")
        return False, None

    # Test 4: Run linter
    print("\n4. Testing run_linter:")
    try:
        result = run_linter(work_dir)
        print(f"   Success: {result['success']}")
        print(f"   Language: {result.get('language', 'N/A')}")
        print(f"   Issues found: {result.get('issue_count', 0)}")
        print("   [OK] run_linter passed")
    except Exception as e:
        print(f"   [FAIL] run_linter failed: {e}")
        return False, work_dir

    # Test 5: Run test
    print("\n5. Testing run_test:")
    try:
        result = run_test(work_dir)
        print(f"   Success: {result['success']}")
        print(f"   Framework: {result.get('framework', 'N/A')}")
        print(f"   Passed: {result.get('passed', False)}")
        print("   [OK] run_test passed")
    except Exception as e:
        print(f"   [FAIL] run_test failed: {e}")
        return False, work_dir

    return True, work_dir


def test_github_operations():
    """Test GitHub operation tools."""
    print("\n" + "=" * 60)
    print("Testing GitHub Operation Tools")
    print("=" * 60)

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
        print(f"   Success: {result['success']}")
        if result['success']:
            print(f"   Comment ID: {result.get('comment_id')}")
            print("   [OK] post_review_comment passed")
        else:
            print(f"   [FAIL] post_review_comment failed: {result.get('error')}")
            return False
    except Exception as e:
        print(f"   [FAIL] post_review_comment failed: {e}")
        return False

    # Test 7: Create issue
    print("\n7. Testing create_issue:")
    try:
        result = create_issue(
            REPO,
            "Test Issue from healpr MCP",
            "This is a test issue created by healpr MCP server for testing purposes."
        )
        print(f"   Success: {result['success']}")
        if result['success']:
            print(f"   Issue #{result.get('issue_number')}: {result.get('url')}")
            print("   [OK] create_issue passed")
            issue_number = result.get('issue_number')
        else:
            print(f"   [FAIL] create_issue failed: {result.get('error')}")
            return False
    except Exception as e:
        print(f"   [FAIL] create_issue failed: {e}")
        return False

    # Test 8: Close issue
    print("\n8. Testing close_issue:")
    try:
        result = close_issue(
            REPO,
            issue_number,
            "Closing test issue from healpr MCP server."
        )
        print(f"   Success: {result['success']}")
        if result['success']:
            print("   [OK] close_issue passed")
        else:
            print(f"   [FAIL] close_issue failed: {result.get('error')}")
            return False
    except Exception as e:
        print(f"   [FAIL] close_issue failed: {e}")
        return False

    return True


def test_cleanup(work_dir):
    """Test cleanup tool."""
    print("\n" + "=" * 60)
    print("Testing Cleanup")
    print("=" * 60)

    print("\n9. Testing cleanup_work_dir:")
    try:
        result = cleanup_work_dir(work_dir)
        print(f"   Success: {result['success']}")
        print(f"   Message: {result.get('message', '')}")
        print("   [OK] cleanup_work_dir passed")
    except Exception as e:
        print(f"   [FAIL] cleanup_work_dir failed: {e}")
        return False

    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("healpr MCP Server Test - voice-dna repo")
    print("=" * 60)

    # Test GitHub client
    if not test_github_client():
        print("\n[FAIL] GitHub client tests failed")
        return 1

    # Test local tools
    success, work_dir = test_local_tools()
    if not success:
        print("\n[FAIL] Local tools tests failed")
        return 1

    # Test GitHub operations
    if not test_github_operations():
        print("\n[FAIL] GitHub operations tests failed")
        return 1

    # Test cleanup
    if work_dir and not test_cleanup(work_dir):
        print("\n[FAIL] Cleanup test failed")
        return 1

    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
