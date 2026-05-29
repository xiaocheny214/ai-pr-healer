"""MCP Server for healpr - AI PR Review Assistant."""

import sys
import logging
from typing import Any

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
        self._setup_handlers()

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
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            """Handle tool calls."""
            try:
                if name == "get_pr_info":
                    result = self.github_client.get_pr_info(
                        arguments["repo"], arguments["pr_number"]
                    )
                    return [TextContent(type="text", text=str(result))]

                elif name == "get_pr_diff":
                    result = self.github_client.get_pr_diff(
                        arguments["repo"], arguments["pr_number"]
                    )
                    return [TextContent(type="text", text=result)]

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
