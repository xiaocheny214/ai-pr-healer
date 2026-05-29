# healpr

MCP-powered AI PR Reviewer with autonomous bug reproduction, issue creation, and self-healing workflow.

## Features

- Pull PR code locally for analysis
- Run linters and tests to verify bugs
- Post line-level review comments on GitHub
- Create issues for confirmed bugs
- Attempt auto-fix with test verification

## Architecture

healpr is a MCP Server that runs as a Claude Code plugin. It provides fine-grained tools for Claude to orchestrate the review workflow.

## Installation

```bash
pip install -e .
```

## Configuration

Add to your Claude Code MCP settings:

```json
{
  "mcpServers": {
    "healpr": {
      "command": "python",
      "args": ["-m", "healpr.server"],
      "env": {
        "HEALPR_GITHUB_TOKEN": "ghp_xxxxxxxxxxxx"
      }
    }
  }
}
```

## License

MIT
