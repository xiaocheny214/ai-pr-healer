"""Hook script to check file operations for safety violations.

Exit 0 = allow, Exit 1 = block.
"""

import sys
import os


# Files/directories that are always blocked during review
BLOCKED_PATHS = [
    "src/",
    "CLAUDE.md",
    "pyproject.toml",
    ".claude/",
]

# Work directory where file modifications are allowed
# Defaults to .test-workspace/ which is the default HEALPR_WORK_DIR
WORK_DIR = os.environ.get("HEALPR_WORK_DIR", ".test-workspace")


def normalize_path(path_str: str) -> str:
    """Normalize path for comparison."""
    return path_str.replace("\\", "/").strip()


def check_file_path(file_path: str) -> tuple[bool, str]:
    """Check if a file path is safe to modify.

    Returns:
        (is_safe, reason) tuple
    """
    if not file_path:
        return False, "Empty file path"

    normalized = normalize_path(file_path)
    work_dir_normalized = normalize_path(WORK_DIR)

    # Check if file is in allowed work directory
    if normalized.startswith(work_dir_normalized):
        return True, ""

    # Check if file matches blocked paths
    for blocked in BLOCKED_PATHS:
        blocked_normalized = normalize_path(blocked)
        if normalized.startswith(blocked_normalized) or normalized == blocked_normalized.rstrip("/"):
            return False, f"Modifying {blocked} is not allowed during review"

    # Default: block unknown paths
    return False, f"File {file_path} is outside allowed work directory"


def main():
    if len(sys.argv) < 2:
        # No path provided, block
        print("BLOCKED: No file path provided", file=sys.stderr)
        sys.exit(1)

    file_path = sys.argv[1]
    is_safe, reason = check_file_path(file_path)

    if not is_safe:
        print(f"BLOCKED: {reason}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
