"""Linter tools for MCP server."""

import subprocess
from pathlib import Path
from typing import Any


def detect_language(work_dir: str) -> str:
    """Detect the primary programming language of a project.

    Args:
        work_dir: Path to the project directory.

    Returns:
        Detected language name.
    """
    work_path = Path(work_dir)

    # Check for common project files
    if (work_path / "package.json").exists():
        return "javascript"
    if (work_path / "tsconfig.json").exists():
        return "typescript"
    if (work_path / "pyproject.toml").exists() or (work_path / "setup.py").exists():
        return "python"
    if (work_path / "go.mod").exists():
        return "go"
    if (work_path / "Cargo.toml").exists():
        return "rust"
    if (work_path / "pom.xml").exists() or (work_path / "build.gradle").exists():
        return "java"

    # Check for common file extensions
    extensions = set()
    for file in work_path.rglob("*"):
        if file.is_file():
            extensions.add(file.suffix)

    if ".py" in extensions:
        return "python"
    if ".js" in extensions:
        return "javascript"
    if ".ts" in extensions:
        return "typescript"
    if ".go" in extensions:
        return "go"
    if ".rs" in extensions:
        return "rust"
    if ".java" in extensions:
        return "java"

    return "unknown"


def run_linter(work_dir: str, file_path: str | None = None) -> dict[str, Any]:
    """Run linter on a project or specific file.

    Args:
        work_dir: Path to the project directory.
        file_path: Optional specific file to lint.

    Returns:
        Dictionary with lint results.
    """
    work_path = Path(work_dir)
    if not work_path.exists():
        return {"success": False, "error": f"Directory {work_dir} does not exist"}

    language = detect_language(work_dir)

    try:
        if language == "python":
            return _run_python_linter(work_path, file_path)
        elif language in ("javascript", "typescript"):
            return _run_js_linter(work_path, file_path)
        elif language == "go":
            return _run_go_linter(work_path, file_path)
        else:
            return {
                "success": False,
                "error": f"No linter configured for language: {language}",
                "language": language,
            }
    except Exception as e:
        return {"success": False, "error": str(e), "language": language}


def _run_python_linter(work_path: Path, file_path: str | None) -> dict[str, Any]:
    """Run Python linter (ruff)."""
    cmd = ["python", "-m", "ruff", "check", "--output-format=json"]
    if file_path:
        cmd.append(file_path)
    else:
        cmd.append(".")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(work_path),
        timeout=60,
    )

    # Parse ruff JSON output
    import json
    issues = []
    if result.stdout:
        try:
            ruff_output = json.loads(result.stdout)
            for item in ruff_output:
                issues.append({
                    "file": item.get("filename", ""),
                    "line": item.get("location", {}).get("row", 0),
                    "column": item.get("location", {}).get("column", 0),
                    "code": item.get("code", ""),
                    "message": item.get("message", ""),
                    "severity": "warning",
                })
        except json.JSONDecodeError:
            pass

    return {
        "success": True,
        "language": "python",
        "linter": "ruff",
        "issues": issues,
        "issue_count": len(issues),
        "output": result.stdout,
    }


def _run_js_linter(work_path: Path, file_path: str | None) -> dict[str, Any]:
    """Run JavaScript/TypeScript linter (eslint)."""
    cmd = ["npx", "eslint", "--format=json"]
    if file_path:
        cmd.append(file_path)
    else:
        cmd.append(".")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(work_path),
        timeout=60,
    )

    # Parse eslint JSON output
    import json
    issues = []
    if result.stdout:
        try:
            eslint_output = json.loads(result.stdout)
            for file_result in eslint_output:
                for message in file_result.get("messages", []):
                    issues.append({
                        "file": file_result.get("filePath", ""),
                        "line": message.get("line", 0),
                        "column": message.get("column", 0),
                        "code": message.get("ruleId", ""),
                        "message": message.get("message", ""),
                        "severity": "warning" if message.get("severity") == 1 else "error",
                    })
        except json.JSONDecodeError:
            pass

    return {
        "success": True,
        "language": "javascript",
        "linter": "eslint",
        "issues": issues,
        "issue_count": len(issues),
        "output": result.stdout,
    }


def _run_go_linter(work_path: Path, file_path: str | None) -> dict[str, Any]:
    """Run Go linter (go vet)."""
    cmd = ["go", "vet", "./..."]
    if file_path:
        cmd = ["go", "vet", file_path]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(work_path),
        timeout=60,
    )

    issues = []
    if result.stderr:
        for line in result.stderr.split("\n"):
            if ":" in line and ".go" in line:
                parts = line.split(":")
                if len(parts) >= 3:
                    issues.append({
                        "file": parts[0],
                        "line": int(parts[1]) if parts[1].isdigit() else 0,
                        "column": 0,
                        "code": "go vet",
                        "message": ":".join(parts[2:]).strip(),
                        "severity": "warning",
                    })

    return {
        "success": True,
        "language": "go",
        "linter": "go vet",
        "issues": issues,
        "issue_count": len(issues),
        "output": result.stderr,
    }
