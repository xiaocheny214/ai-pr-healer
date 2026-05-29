"""Hook script to check Bash commands for safety violations.

Exit 0 = allow, Exit 1 = block.
"""

import sys
import re


BLOCKED_PATTERNS = [
    # git push (any variant)
    (r"\bgit\s+push\b", "git push is not allowed during review"),
    # git commit --amend
    (r"\bgit\s+commit\b.*--amend", "git commit --amend is not allowed during review"),
    # rm -rf on root directories (Unix root, Windows C:\, Windows C:/)
    (r"\brm\s+(-[a-zA-Z]*\s+)*/\s*$", "rm -rf / is not allowed"),
    (r"\brm\s+(-[a-zA-Z]*\s+)*C:\\\s*$", r"rm -rf C:\\ is not allowed"),
    (r"\brm\s+(-[a-zA-Z]*\s+)*C:/\s*$", "rm -rf C:/ is not allowed"),
]


def check_command(command: str) -> tuple[bool, str]:
    """Check if a command is safe to execute.

    Returns:
        (is_safe, reason) tuple
    """
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return False, reason
    return True, ""


def main():
    if len(sys.argv) < 2:
        # No command provided, allow
        sys.exit(0)

    command = sys.argv[1]
    is_safe, reason = check_command(command)

    if not is_safe:
        print(f"BLOCKED: {reason}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
