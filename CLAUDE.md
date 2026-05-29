# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

healpr is an MCP (Model Context Protocol) Server that acts as a Claude Code plugin for AI-powered PR review. It provides fine-grained tools that Claude orchestrates to review pull requests, reproduce bugs locally, post review comments, and create issues. The server communicates with Claude Code via JSON-RPC 2.0 over stdin/stdout.

## Commands

```bash
# Install (editable mode)
pip install -e ".[dev]"

# Run MCP server (used by Claude Code as MCP host)
python -m healpr.server

# Run all tests
pytest

# Run a single test file
pytest tests/test_github_client.py

# Run a single test
pytest tests/test_github_client.py::test_detect_token_type_classic_pat

# Lint
ruff check src/ tests/

# Format
ruff format src/ tests/
```

## Architecture

```
Claude Code (MCP Host)
    │ stdin/stdout (JSON-RPC 2.0)
    ▼
HealprServer (server.py)
    ├── github/
    │   ├── auth.py    — Token detection (ghp_/github_pat_/gho_/ghu_/ghs_), OAuth scope hierarchy
    │   └── client.py  — REST API client (httpx): PR info, diff, issues, review comments
    ├── tools/
    │   ├── git_tools.py     — clone_pr_branch (temp-dir strategy for Windows), cleanup_work_dir
    │   ├── lint_tools.py    — run_linter (auto-detects ruff/eslint/go vet)
    │   ├── test_tools.py    — run_test (auto-detects pytest/jest/vitest/go test)
    │   └── github_tools.py  — create_issue, post_review_comment, post_issue_comment, close_issue
    └── config.py — Env-based config (HEALPR_GITHUB_TOKEN, HEALPR_WORK_DIR)
```

The server registers 10 MCP tools. Claude Code calls these tools by name; the server executes them and returns results as `TextContent`.

## Key Design Decisions

- **Tool-per-concern pattern**: Each tool is a standalone function in `tools/` that accepts plain args and returns a dict. The server module (`server.py`) only maps MCP tool calls to these functions.
- **Windows compatibility**: `git_tools.py` uses `shutil.rmtree(onerror=_remove_readonly)` because git creates read-only files in `.git/objects/`. Clone uses a temp-then-move strategy to avoid partial directory states.
- **Token type auto-detection**: `auth.py` detects token type from prefix and applies OAuth scope hierarchy (e.g., `repo` grants `public_repo` and `security_events`).
- **GitHub client creates new instances per call**: `github_tools.py` functions create a fresh `GitHubClient` per invocation rather than sharing state.

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `HEALPR_GITHUB_TOKEN` | GitHub PAT (primary) | — |
| `GITHUB_TOKEN` | GitHub PAT (fallback) | — |
| `HEALPR_WORK_DIR` | Local workspace for cloned repos | `/tmp/healpr-workspace` |

## Testing

Tests are in `tests/` and use pytest with `unittest.mock` for mocking HTTP calls. The `test_mcp_voice_dna.py` script at the repo root is an integration test that runs against a real GitHub repository.
