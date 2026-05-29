# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**healpr** is an MCP (Model Context Protocol) server that runs as a Claude Code plugin for autonomous PR review with bug reproduction, issue creation, and self-healing. It exposes 10 atomic tools; Claude (the host) orchestrates the review logic — the server itself never calls an LLM API.

## Commands

```bash
pip install -e .                          # Install in editable mode (hatchling)
python -m healpr.server                   # Run MCP server (stdio transport)
pytest tests/test_github_client.py        # Unit tests
python test_mcp_tools.py                  # Integration tests (requires live GitHub token)
ruff check src/                           # Lint
```

## Architecture

Three-layer defense architecture:

- **Skill layer** (`.claude/skills/review.md`) — `/review` command with dual mode:
  - Default mode: Claude autonomous review
  - Strict mode (`/review --strict`): loads rules from `.claude/review-rules/*.yaml`
- **Hooks layer** (`.claude/settings.json` hooks) — preToolUse guards:
  - Blocks `git push`, `git commit --amend`, `rm -rf /`
  - Blocks file edits outside `.test-workspace/`
- **MCP Server layer** (`src/healpr/server.py`) — tool argument validation:
  - Path whitelist: `clone_pr_branch`/`cleanup_work_dir` restricted to `HEALPR_WORK_DIR`
  - Repo whitelist: GitHub operations locked to target repo after first call

Core server has three layers under `src/healpr/`:

- **server.py** — `HealprServer` class: MCP tool registration (`@server.list_tools()`) and dispatch (`@server.call_tool()`). Uses `asyncio.run_in_executor()` to run blocking tool functions off the event loop. Includes `_validate_tool_args` for argument safety checks.
- **github/** — `GitHubAuth` (token type detection, scope fetching) and `GitHubClient` (httpx wrapper for PR info, diff, issues, comments).
- **tools/** — Four modules exposing the 10 MCP tools:
  - `git_tools.py` — `clone_pr_branch`, `cleanup_work_dir` (includes Windows `_remove_readonly` handler)
  - `lint_tools.py` — `run_linter`, `detect_language` (ruff / eslint / go vet)
  - `test_tools.py` — `run_test`, `detect_test_framework` (pytest / jest / vitest / go test / cargo test)
  - `github_tools.py` — `create_issue`, `post_review_comment`, `post_issue_comment`, `close_issue`

## Configuration

- `HEALPR_GITHUB_TOKEN` (or `GITHUB_TOKEN`) — required GitHub PAT
- `HEALPR_WORK_DIR` — workspace for cloned repos, defaults to `/tmp/healpr-workspace`

## Key Conventions

- Python 3.10+, hatchling build backend
- MCP protocol over JSON-RPC 2.0 via stdio
- GitHub API calls use synchronous httpx with 30s timeout
- Tool functions in `tools/` are plain `async def` that accept `**kwargs` from MCP tool call arguments
- `github_tools.py` creates a fresh `GitHubClient` per call (stateless)
- Language/test framework detection is file-based (checks for `pyproject.toml`, `package.json`, `go.mod`, etc.)

## Rules
1. 不要在代码中添加模型署名。
2. 不要在代码中添加任何关于模型的信息。