"""MCP Server for healpr - AI PR Review Assistant."""

import os
import sys
import asyncio
import logging
from typing import Any
from functools import partial

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    CallToolResult,
    ListToolsResult,
)

from .github import GitHubAuth, GitHubClient
from .config import Config
from .tools import (
    clone_pr_branch,
    cleanup_work_dir,
    run_linter,
    run_test,
    create_issue,
    post_review_comment,
    post_issue_comment,
    close_issue,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("healpr")


class HealprServer:
    """healpr MCP Server implementation."""

    def __init__(self):
        self.config = Config.from_env()
        self.auth = GitHubAuth.from_env()
        self.github_client = GitHubClient(auth=self.auth)
        self.server = Server("healpr")
        self.target_repo = None  # 目标仓库，首次调用 get_pr_info 时记录
        self._setup_handlers()

    def _is_target_repo(self, repo: str) -> bool:
        """Check if repo matches the target repository."""
        if self.target_repo is None:
            # First call: record and allow
            self.target_repo = repo
            return True
        return repo == self.target_repo

    def _validate_tool_args(self, name: str, arguments: dict) -> None:
        """Validate tool arguments before execution.

        Raises ValueError if validation fails.
        """
        if name in ("clone_pr_branch", "cleanup_work_dir"):
            work_dir = arguments.get("work_dir", "")
            if not work_dir:
                # clone_pr_branch doesn't require work_dir (has default)
                if name == "cleanup_work_dir":
                    raise ValueError("work_dir 参数不能为空")
                return
            # Root directory protection (check before path bounds)
            if work_dir in ("/", "C:\\", "C:/"):
                raise ValueError(f"禁止清理根目录: {work_dir}")
            # Path traversal check
            if ".." in work_dir:
                raise ValueError(f"路径禁止包含 ../: {work_dir}")
            # Path bounds check
            allowed = str(self.config.work_dir)
            real_work = os.path.realpath(work_dir)
            real_allowed = os.path.realpath(allowed)
            if not real_work.startswith(real_allowed):
                raise ValueError(f"路径越界: {work_dir} 不在允许范围 {allowed} 内")

        if name in ("get_pr_info", "get_pr_diff", "create_issue", "post_review_comment", "post_issue_comment", "close_issue"):
            repo = arguments.get("repo", "")
            if repo and not self._is_target_repo(repo):
                raise ValueError(f"非目标仓库: {repo}，当前审查目标: {self.target_repo}")

    def _setup_handlers(self):
        """Set up MCP request handlers."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="get_pr_info",
                    description="Get pull request information including title, description, author, and changed files.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo": {
                                "type": "string",
                                "description": "Repository in 'owner/repo' format",
                            },
                            "pr_number": {
                                "type": "integer",
                                "description": "Pull request number",
                            },
                        },
                        "required": ["repo", "pr_number"],
                    },
                ),
                Tool(
                    name="get_pr_diff",
                    description="Get the unified diff of a pull request.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo": {
                                "type": "string",
                                "description": "Repository in 'owner/repo' format",
                            },
                            "pr_number": {
                                "type": "integer",
                                "description": "Pull request number",
                            },
                        },
                        "required": ["repo", "pr_number"],
                    },
                ),
                Tool(
                    name="clone_pr_branch",
                    description="Clone a PR branch to local workspace for analysis.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo": {
                                "type": "string",
                                "description": "Repository in 'owner/repo' format",
                            },
                            "pr_number": {
                                "type": "integer",
                                "description": "Pull request number",
                            },
                        },
                        "required": ["repo", "pr_number"],
                    },
                ),
                Tool(
                    name="cleanup_work_dir",
                    description="Clean up a work directory after analysis.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "work_dir": {
                                "type": "string",
                                "description": "Path to the work directory to clean up",
                            },
                        },
                        "required": ["work_dir"],
                    },
                ),
                Tool(
                    name="run_linter",
                    description="Run linter on a project or specific file to detect code issues.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "work_dir": {
                                "type": "string",
                                "description": "Path to the project directory",
                            },
                            "file_path": {
                                "type": "string",
                                "description": "Optional specific file to lint",
                            },
                        },
                        "required": ["work_dir"],
                    },
                ),
                Tool(
                    name="run_test",
                    description="Run tests in a project to verify functionality.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "work_dir": {
                                "type": "string",
                                "description": "Path to the project directory",
                            },
                            "test_command": {
                                "type": "string",
                                "description": "Optional custom test command to run",
                            },
                        },
                        "required": ["work_dir"],
                    },
                ),
                Tool(
                    name="create_issue",
                    description="Create a new issue on GitHub.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo": {
                                "type": "string",
                                "description": "Repository in 'owner/repo' format",
                            },
                            "title": {
                                "type": "string",
                                "description": "Issue title",
                            },
                            "body": {
                                "type": "string",
                                "description": "Issue body (Markdown)",
                            },
                        },
                        "required": ["repo", "title", "body"],
                    },
                ),
                Tool(
                    name="post_review_comment",
                    description="Post a review comment on a specific line of a PR.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo": {
                                "type": "string",
                                "description": "Repository in 'owner/repo' format",
                            },
                            "pr_number": {
                                "type": "integer",
                                "description": "Pull request number",
                            },
                            "file": {
                                "type": "string",
                                "description": "File path relative to repo root",
                            },
                            "line": {
                                "type": "integer",
                                "description": "Line number to comment on",
                            },
                            "body": {
                                "type": "string",
                                "description": "Comment body (Markdown)",
                            },
                            "suggestion": {
                                "type": "string",
                                "description": "Optional suggested code change",
                            },
                        },
                        "required": ["repo", "pr_number", "file", "line", "body"],
                    },
                ),
                Tool(
                    name="post_issue_comment",
                    description="Post a comment on an issue or PR discussion.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo": {
                                "type": "string",
                                "description": "Repository in 'owner/repo' format",
                            },
                            "issue_number": {
                                "type": "integer",
                                "description": "Issue or PR number",
                            },
                            "body": {
                                "type": "string",
                                "description": "Comment body (Markdown)",
                            },
                        },
                        "required": ["repo", "issue_number", "body"],
                    },
                ),
                Tool(
                    name="close_issue",
                    description="Close an issue with optional comment.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo": {
                                "type": "string",
                                "description": "Repository in 'owner/repo' format",
                            },
                            "issue_number": {
                                "type": "integer",
                                "description": "Issue number to close",
                            },
                            "comment": {
                                "type": "string",
                                "description": "Optional closing comment",
                            },
                        },
                        "required": ["repo", "issue_number"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            """Handle tool calls."""
            loop = asyncio.get_event_loop()
            try:
                # Validate arguments before execution
                self._validate_tool_args(name, arguments)

                if name == "get_pr_info":
                    result = await loop.run_in_executor(
                        None,
                        partial(self.github_client.get_pr_info, arguments["repo"], arguments["pr_number"])
                    )
                    return [TextContent(type="text", text=str(result))]

                elif name == "get_pr_diff":
                    result = await loop.run_in_executor(
                        None,
                        partial(self.github_client.get_pr_diff, arguments["repo"], arguments["pr_number"])
                    )
                    return [TextContent(type="text", text=result)]

                elif name == "clone_pr_branch":
                    result = await loop.run_in_executor(
                        None,
                        partial(clone_pr_branch, arguments["repo"], arguments["pr_number"])
                    )
                    return [TextContent(type="text", text=str(result))]

                elif name == "cleanup_work_dir":
                    result = await loop.run_in_executor(
                        None,
                        partial(cleanup_work_dir, arguments["work_dir"])
                    )
                    return [TextContent(type="text", text=str(result))]

                elif name == "run_linter":
                    result = await loop.run_in_executor(
                        None,
                        partial(run_linter, arguments["work_dir"], arguments.get("file_path"))
                    )
                    return [TextContent(type="text", text=str(result))]

                elif name == "run_test":
                    result = await loop.run_in_executor(
                        None,
                        partial(run_test, arguments["work_dir"], arguments.get("test_command"))
                    )
                    return [TextContent(type="text", text=str(result))]

                elif name == "create_issue":
                    result = await loop.run_in_executor(
                        None,
                        partial(create_issue, arguments["repo"], arguments["title"], arguments["body"])
                    )
                    return [TextContent(type="text", text=str(result))]

                elif name == "post_review_comment":
                    result = await loop.run_in_executor(
                        None,
                        partial(
                            post_review_comment,
                            arguments["repo"],
                            arguments["pr_number"],
                            arguments["file"],
                            arguments["line"],
                            arguments["body"],
                            arguments.get("suggestion"),
                        )
                    )
                    return [TextContent(type="text", text=str(result))]

                elif name == "post_issue_comment":
                    result = await loop.run_in_executor(
                        None,
                        partial(post_issue_comment, arguments["repo"], arguments["issue_number"], arguments["body"])
                    )
                    return [TextContent(type="text", text=str(result))]

                elif name == "close_issue":
                    result = await loop.run_in_executor(
                        None,
                        partial(close_issue, arguments["repo"], arguments["issue_number"], arguments.get("comment"))
                    )
                    return [TextContent(type="text", text=str(result))]

                else:
                    raise ValueError(f"Unknown tool: {name}")

            except Exception as e:
                logger.error(f"Tool {name} failed: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def run(self):
        """Run the MCP server."""
        logger.info("Starting healpr MCP Server...")
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )


async def main():
    """Main entry point."""
    server = HealprServer()
    await server.run()


def cli_main():
    """CLI entry point for the server."""
    import asyncio
    asyncio.run(main())


if __name__ == "__main__":
    cli_main()
