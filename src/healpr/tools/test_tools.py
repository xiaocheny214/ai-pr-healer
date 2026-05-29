"""Test runner tools for MCP server."""

import subprocess
from pathlib import Path
from typing import Any


def detect_test_framework(work_dir: str) -> tuple[str, str]:
    """Detect the test framework and command for a project.

    Args:
        work_dir: Path to the project directory.

    Returns:
        Tuple of (framework_name, test_command).
    """
    work_path = Path(work_dir)

    # Python
    if (work_path / "pyproject.toml").exists():
        # Check for pytest in dependencies
        pyproject = (work_path / "pyproject.toml").read_text()
        if "pytest" in pyproject:
            return "pytest", "python -m pytest"
        return "unittest", "python -m unittest discover"

    if (work_path / "setup.py").exists():
        return "pytest", "python -m pytest"

    # JavaScript/TypeScript
    if (work_path / "package.json").exists():
        package_json = (work_path / "package.json").read_text()
        if '"vitest"' in package_json:
            return "vitest", "npx vitest run"
        if '"jest"' in package_json:
            return "jest", "npx jest"
        if '"mocha"' in package_json:
            return "mocha", "npx mocha"
        return "npm", "npm test"

    # Go
    if (work_path / "go.mod").exists():
        return "go test", "go test ./..."

    # Rust
    if (work_path / "Cargo.toml").exists():
        return "cargo test", "cargo test"

    return "unknown", ""


def run_test(work_dir: str, test_command: str | None = None) -> dict[str, Any]:
    """Run tests in a project.

    Args:
        work_dir: Path to the project directory.
        test_command: Optional custom test command to run.

    Returns:
        Dictionary with test results.
    """
    work_path = Path(work_dir)
    if not work_path.exists():
        return {"success": False, "error": f"Directory {work_dir} does not exist"}

    # Detect test framework if no command provided
    if test_command is None:
        framework, default_command = detect_test_framework(work_dir)
        if not default_command:
            return {
                "success": False,
                "error": "Could not detect test framework",
                "language": "unknown",
            }
        test_command = default_command
    else:
        framework = "custom"

    try:
        # Run the test command
        result = subprocess.run(
            test_command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=str(work_path),
            timeout=120,  # 2 minute timeout
        )

        # Parse test output
        output = result.stdout + result.stderr
        passed = result.returncode == 0

        # Try to extract test counts from output
        test_counts = _parse_test_counts(output, framework)

        return {
            "success": True,
            "passed": passed,
            "framework": framework,
            "command": test_command,
            "return_code": result.returncode,
            "output": output,
            "test_counts": test_counts,
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Test execution timed out (120 seconds)",
            "framework": framework,
            "command": test_command,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "framework": framework,
            "command": test_command,
        }


def _parse_test_counts(output: str, framework: str) -> dict[str, int]:
    """Parse test counts from test output.

    Args:
        output: Test output string.
        framework: Test framework name.

    Returns:
        Dictionary with test counts.
    """
    counts = {"passed": 0, "failed": 0, "skipped": 0, "total": 0}

    if framework == "pytest":
        # Parse pytest output: "X passed, Y failed, Z skipped"
        import re
        match = re.search(r"(\d+) passed", output)
        if match:
            counts["passed"] = int(match.group(1))
        match = re.search(r"(\d+) failed", output)
        if match:
            counts["failed"] = int(match.group(1))
        match = re.search(r"(\d+) skipped", output)
        if match:
            counts["skipped"] = int(match.group(1))
        counts["total"] = counts["passed"] + counts["failed"] + counts["skipped"]

    elif framework in ("jest", "vitest"):
        # Parse jest/vitest output: "Tests: X passed, Y failed, Z total"
        import re
        match = re.search(r"Tests:\s+(\d+) passed", output)
        if match:
            counts["passed"] = int(match.group(1))
        match = re.search(r"(\d+) failed", output)
        if match:
            counts["failed"] = int(match.group(1))
        match = re.search(r"(\d+) total", output)
        if match:
            counts["total"] = int(match.group(1))

    elif framework == "go test":
        # Parse go test output: "ok" or "FAIL"
        if "FAIL" in output:
            counts["failed"] = 1
            counts["total"] = 1
        elif "ok" in output:
            counts["passed"] = 1
            counts["total"] = 1

    return counts
