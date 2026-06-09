# healpr - AI PR Review MCP Server

> MCP-powered AI PR Reviewer with autonomous bug reproduction, issue creation, and self-healing workflow.

## Overview

healpr 是一个手搓的 MCP Server，作为 Claude Code 的插件运行。它提供一组细粒度 Tools，让 Claude 自主编排"PR Review → 本地验证 → 提 issue → 尝试修复"的完整闭环工作流。

**比赛背景：** 七牛云 × XEngineer 暑期实训营，题目三：AI PR Review 助手，3 天 Hackathon（2026-05-29 ~ 2026-05-31）。

## 核心决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 技术栈 | Python | 用户偏好 |
| 架构 | MCP Server（Claude Code 插件） | 不重复造轮子，利用 Claude Code 作为 Host |
| Tool 粒度 | 细粒度（7 个原子 Tools） | 最简洁，Claude 足够智能来编排 |
| 认证方式 | GitHub PAT | 3 天内最简单，开发人员本地都有 git CLI |
| LLM 分工 | Claude 负责思考，Server 负责动手 | MCP Server 只提供纯工具，不调 LLM API |
| 本地代码操作 | git CLI | 开发人员本地环境已有 |

## 项目结构

```
healpr/
├── src/
│   └── healpr/
│       ├── __init__.py
│       ├── server.py          # MCP Server 入口，JSON-RPC 处理
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── registry.py    # Tool 注册与分发
│       │   ├── pr_tools.py    # get_pr_diff, get_pr_info
│       │   ├── git_tools.py   # clone_pr_branch
│       │   ├── lint_tools.py  # run_linter
│       │   ├── test_tools.py  # run_test
│       │   └── github_tools.py # create_issue, post_review_comment, close_issue
│       ├── github/
│       │   ├── __init__.py
│       │   ├── client.py      # GitHub API 封装（httpx）
│       │   └── auth.py        # PAT 认证
│       └── config.py          # 配置管理
├── pyproject.toml
└── README.md
```

## MCP Server 骨架

MCP 底层协议：JSON-RPC 2.0 over stdin/stdout。

```python
import sys
import json

def read_message():
    """从 stdin 读取 JSON-RPC 消息"""
    header = sys.stdin.readline()
    if not header:
        return None
    length = int(header.strip().split(":")[1])
    sys.stdin.readline()  # 空行
    return json.loads(sys.stdin.read(length))

def write_message(response):
    """向 stdout 写入 JSON-RPC 响应"""
    content = json.dumps(response)
    sys.stdout.write(f"Content-Length: {len(content)}\r\n\r\n{content}")
    sys.stdout.flush()

def main():
    while True:
        msg = read_message()
        if msg is None:
            break
        result = handle_message(msg)
        write_message(result)
```

## MCP Tools 定义

共 7 个 Tools，分三类：

### PR 信息类

```python
get_pr_diff(repo: str, pr_number: int) -> str
# 返回：PR 的完整 diff 文本（unified diff 格式）

get_pr_info(repo: str, pr_number: int) -> dict
# 返回：PR 标题、描述、作者、base/head 分支、changed_files 列表
```

### 本地操作类

```python
clone_pr_branch(repo: str, pr_number: int) -> str
# 动作：git clone --depth 1 + git fetch origin pull/{pr}/head
# 返回：本地工作目录路径（如 /tmp/healpr-workspace/{repo}-pr-{n}）

run_linter(work_dir: str, file_path: str = None) -> dict
# 动作：根据语言检测运行对应 linter（ruff/eslint/go vet）
# 返回：{issues: [{file, line, severity, message}]}

run_test(work_dir: str, test_command: str = None) -> dict
# 动作：运行测试命令（pytest/npm test/go test）
# 返回：{passed: bool, output: str, failures: [{file, line, message}]}
```

### GitHub 操作类

```python
create_issue(repo: str, title: str, body: str) -> dict
# 返回：{issue_number, url}

post_review_comment(repo: str, pr_number: int, file: str,
                    line: int, body: str, suggestion: str = None) -> dict
# 动作：行级 Review Comment，可带 suggested change
# 返回：{comment_id, url}

close_issue(repo: str, issue_number: int, comment: str = None) -> dict
# 返回：{success: bool}
```

## 闭环工作流

Claude 自主编排以下 6 步流程：

```
用户："帮我 review owner/repo #12"

Step 1: 获取信息
  → get_pr_info("owner/repo", 12)   # 了解 PR 概况
  → get_pr_diff("owner/repo", 12)   # 获取代码变更

Step 2: 拉取代码
  → clone_pr_branch("owner/repo", 12)  # 本地落盘

Step 3: 静态分析（降低误报）
  → run_linter(work_dir)            # 跑 linter
  → Claude 分析 diff + linter 结果，识别潜在 bug

Step 4: 验证 bug（关键创新点）
  → 如果发现可疑代码：
    → run_test(work_dir)             # 跑已有测试，看是否已覆盖
    → Claude 尝试编写能复现 bug 的测试代码
    → run_test(work_dir)             # 验证测试是否能捕获 bug

Step 5: 报告问题
  → post_review_comment(...)         # 行级评论到 PR
  → 如果确认 bug：create_issue(...) # 创建 issue 跟踪

Step 6: 尝试修复（可选）
  → Claude 直接编辑本地文件修复 bug
  → run_test(work_dir)              # 验证修复是否通过测试
  → 修复成功：在 issue 中留言 + close_issue
  → 修复失败：在 issue 中补充分析，保持 open
```

## 认证与配置

### MCP 配置示例

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

### 配置优先级

1. 环境变量 `HEALPR_GITHUB_TOKEN`（MCP 配置中设置）
2. 配置文件 `~/.healpr/config.toml`

### Token 权限要求（最小权限）

- `repo` — 读取 PR、发评论
- `issues` — 创建/关闭 issue

### 本地工作目录

- 默认：`/tmp/healpr-workspace/`
- 可通过 `HEALPR_WORK_DIR` 环境变量覆盖
- 每次 review 完自动清理

## 统一返回格式

```python
# 成功
{"success": true, "data": {...}}

# 失败
{"success": false, "error": "GitHub API rate limit exceeded", "code": "RATE_LIMIT"}
```

## 边界情况处理

| 场景 | 处理方式 |
|------|----------|
| PR diff 超大（>500 文件） | `get_pr_diff` 返回文件列表 + 摘要，不返回完整 diff，提示 Claude 分批获取 |
| git clone 失败 | 返回明确错误信息，Claude 决定是否用 API 获取文件内容作为降级 |
| linter 未安装 | 返回 `{success: false, "error": "ruff not found", "hint": "pip install ruff"}` |
| 测试超时（>60s） | 强制终止，返回 `{success: false, "error": "test timeout"}` |
| GitHub Token 无效/过期 | 返回 401 错误提示，引导用户检查 Token |
| 本地工作目录冲突 | 自动加时间戳后缀避免覆盖 |

## 清理策略

- `clone_pr_branch` 每次调用前检查并清理同名旧目录
- 可选：提供 `cleanup_work_dir(work_dir)` Tool 让 Claude 显式清理

## 后续演进方向

1. **Skill 文件** — 编写 `/review` Skill，规范 Claude 的调用策略和 Review 标准
2. **Hooks** — 设置 hooks 防止架构漂移，确保 Tool 调用符合预期模式
3. **插件化** — 支持自定义 linter、自定义测试命令、自定义 Review 规则
4. **多语言支持** — 扩展语言检测和 linter 映射
5. **GitHub App 认证** — 替代 PAT，支持组织级部署
