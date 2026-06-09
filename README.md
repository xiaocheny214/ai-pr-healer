# healpr — AI PR 代码审查工具

> MCP-powered AI PR reviewer with autonomous bug reproduction, issue creation, and self-healing. [中文文档 ↓](#安装指南新手向)

healpr 是一个 MCP Server，作为 Claude Code 插件运行，提供自动化 PR 代码审查能力。它能自动拉取 PR 代码、运行 linter 和测试、在 GitHub 上发布行级审查评论、为确认的 bug 创建 issue。

## 产品介绍视频

> 视频演示了 healpr 的完整 PR 审查流程：从发起审查到自动运行 linter、测试、发布行级评论、创建 issue 的全过程。

[![产品介绍视频](https://img.shields.io/badge/📺_产品介绍视频-百度网盘-blue)](https://pan.baidu.com/s/1-9GrkibNoZB5KX9lqzCbbQ?pwd=kuxb)

🔗 **链接**: https://pan.baidu.com/s/1-9GrkibNoZB5KX9lqzCbbQ?pwd=kuxb
🔑 **提取码**: `kuxb`

---

## 安装指南（新手向）

### 第一步：环境准备

在安装 healpr 之前，请确认你的电脑上已经安装了以下软件：

**1. Python 3.10 或更高版本**

打开终端（Windows 用户打开 PowerShell 或 CMD），输入以下命令检查：

```bash
python --version
```

如果显示 `Python 3.10.x` 或更高版本（如 3.11、3.12、3.13），则满足要求。
如果提示找不到命令，请先安装 Python：https://www.python.org/downloads/

**2. Git**

```bash
git --version
```

如果显示版本号则满足要求。如果没有安装：https://git-scm.com/downloads

**3. Claude Code**

确保你已经安装并能正常使用 Claude Code CLI。如果还没有安装：

```bash
npm install -g @anthropic-ai/claude-code
```

**4. GitHub Personal Access Token (PAT)**

healpr 需要一个 GitHub Token 来访问 GitHub API（读取 PR、发布评论等）。

创建步骤：
1. 打开 https://github.com/settings/tokens
2. 点击 **"Generate new token"** → 选择 **"Fine-grained token"**（推荐）或 **"Classic token"**
3. 如果选择 Classic token，勾选以下权限：
   - `repo`（完整仓库访问权限）
   - `issues`（issue 管理权限）
4. 点击 **"Generate token"**
5. **立即复制生成的 token**（格式为 `github_pat_...` 或 `ghp_...`），页面刷新后将无法再次查看

> **安全提示**：不要将 token 提交到代码仓库中！不要分享给他人！

---

### 第二步：下载并安装 healpr

**1. 克隆仓库**

```bash
git clone https://github.com/xiaocheny214/ai-pr-healer.git
cd ai-pr-healer
```

**2. 安装 Python 依赖**

```bash
pip install -e .
```

这会以开发模式安装 healpr 及其依赖（httpx、mcp 等）。

**3. 验证安装**

```bash
python -c "import healpr; print('healpr 安装成功')"
```

---

### 第三步：配置 Claude Code（两种方式选一种）

#### 方式 A：项目级配置（推荐新手）

当你在 healpr 项目目录下使用 Claude Code 时，项目自带的 `.mcp.json` 会自动加载 MCP 服务器。

你只需要设置环境变量：

```bash
# Windows PowerShell
$env:HEALPR_GITHUB_TOKEN="你的GitHub Token"

# Windows CMD
set HEALPR_GITHUB_TOKEN=你的GitHub Token

# macOS / Linux
export HEALPR_GITHUB_TOKEN="你的GitHub Token"
```

然后在 healpr 项目目录下启动 Claude Code：

```bash
cd ai-pr-healer
claude
```

项目目录下包含：
- `.mcp.json` — MCP 服务器配置（项目级，自动加载）
- `.claude/settings.json` — 安全钩子 + 权限配置
- `.claude/skills/pr-review/` — `/pr-review` 命令定义 + 审查规则 YAML
- `.claude/hooks/` — 安全防护脚本

这些文件会自动被 Claude Code 加载，无需额外操作。

#### 方式 B：全局配置（所有项目通用）

如果你希望在任何项目目录下都能使用 healpr，需要完成以下 4 步。

**1. 创建全局目录结构并复制文件**

```bash
# 创建目录
mkdir -p ~/.claude/hooks
mkdir -p ~/.claude/skills/pr-review

# 复制文件（Windows 用户将 cp 改为 copy）
cp .claude/hooks/check_bash_safety.py ~/.claude/hooks/
cp .claude/hooks/check_file_safety.py ~/.claude/hooks/
cp .claude/skills/pr-review/SKILL.md ~/.claude/skills/pr-review/SKILL.md
cp .claude/skills/pr-review/*.yaml ~/.claude/skills/pr-review/
```

完成后，全局目录结构如下：

```
~/.claude/
├── hooks/
│   ├── check_bash_safety.py          # Bash 命令安全检查（阻止 git push 等）
│   └── check_file_safety.py          # 文件操作安全检查（阻止修改项目源码）
├── skills/
│   └── pr-review/
│       ├── SKILL.md                  # /pr-review 命令定义（审查流程 7 步）
│       ├── security.yaml             # 安全审查规则
│       ├── architecture.yaml         # 架构审查规则
│       └── performance.yaml          # 性能审查规则
└── settings.json                     # 环境变量 + hooks 配置
```

> **关键**：skill 文件必须命名为 `SKILL.md`，放在以 skill 名称命名的目录下（`skills/pr-review/SKILL.md`）。审查规则 YAML 也放在同一目录内，严格模式会从当前 skill 目录读取 `*.yaml`。

> **Windows 用户注意**：`~` 代表用户主目录，通常是 `C:\Users\你的用户名`。在 PowerShell 中可以用 `$HOME` 代替 `~`。

**2. 在 `~/.claude.json` 中添加 MCP Server 配置**

MCP Server 配置存储在 `~/.claude.json`（用户级），而不是 `.claude/settings.json`。

在 `~/.claude.json` 中添加 `mcpServers`：

```json
{
  "mcpServers": {
    "healpr": {
      "command": "python",
      "args": ["-m", "healpr.server"],
      "cwd": "/path/to/ai-pr-healer",
      "env": {
        "HEALPR_GITHUB_TOKEN": "你的GitHub Token",
        "HEALPR_WORK_DIR": "/path/to/healpr-workspace"
      }
    }
  }
}
```

| 字段 | 说明 |
|------|------|
| `command` | `python -m healpr.server`，以模块方式启动 MCP server |
| `cwd` | healpr 项目根目录的**绝对路径**（如 `D:/ai-pr-healer`） |
| `HEALPR_GITHUB_TOKEN` | 你在第一步创建的 GitHub Token |
| `HEALPR_WORK_DIR` | 工作目录，用于存放克隆的 PR 代码，建议使用独立目录 |

> **配置文件说明**：
> - `~/.claude.json` — MCP Server 配置（用户级，所有项目通用）
> - `.mcp.json` — MCP Server 配置（项目级，仅当前项目生效）
> - `.claude/settings.json` — 权限、Hooks、环境变量（不含 MCP Server 配置）

**3. 在 `~/.claude/settings.json` 中添加安全钩子**

在 `~/.claude/settings.json` 中添加 `hooks` 配置（此文件不含 MCP Server 配置）：

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python ~/.claude/hooks/check_bash_safety.py \"$TOOL_INPUT\""
          }
        ]
      },
      {
        "matcher": "Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python ~/.claude/hooks/check_file_safety.py \"$TOOL_INPUT\""
          }
        ]
      },
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "python ~/.claude/hooks/check_file_safety.py \"$TOOL_INPUT\""
          }
        ]
      }
    ]
  }
}
```

> **注意**：`PreToolUse` 的首字母必须大写！小写的 `preToolUse` 会导致钩子不生效。

**4. 重启 Claude Code**

配置修改后需要重启 Claude Code 才能生效。

---

### 第四步：验证安装

启动 Claude Code 后，输入以下命令验证 MCP 服务器是否正常运行：

```
/mcp
```

在弹出的面板中，应该能看到 `healpr` 服务器及其 10 个工具。

---

## 设计思路

### 单仓库锁定机制

healpr 的核心安全设计是**单仓库单会话**：在一个 Claude Code 会话中，一旦开始审查某个仓库的 PR，所有 GitHub 操作（获取 PR 信息、发布评论、创建 issue）都会被锁定到该仓库。如果尝试操作其他仓库，MCP server 会直接拒绝并返回错误。

```
# 会话中首次审查 facebook/react #123 → 锁定到 facebook/react
/pr-review facebook/react 123     ✅ 正常执行

# 同一会话中尝试审查另一个仓库 → 被拒绝
/pr-review google/gson 456        ❌ "非目标仓库: google/gson，当前审查目标: facebook/react"
```

**为什么这样设计？**

代码审查是一个高风险操作——它涉及读取代码、在 GitHub 上发布评论、创建 issue。如果允许同一个会话随意切换仓库，会带来两个问题：

1. **误操作风险**：审查 A 仓库时产生的评论或 issue 可能误发到 B 仓库
2. **上下文污染**：Claude 的上下文中混入了多个仓库的代码和 diff，可能导致审查结论张冠李戴

单仓库锁定确保了审查会话的**原子性**——一次只专注于一个仓库，所有操作都在该仓库的上下文中完成。

**切换审查仓库**：关闭当前会话，开一个新的 Claude Code session 即可。

---

### 三层安全防护架构

```
┌─────────────────────────────────────────────────┐
│  Skill 层 (.claude/skills/pr-review/)            │
│  /pr-review 命令 → 定义审查流程（7 步）           │
├─────────────────────────────────────────────────┤
│  Hooks 层 (.claude/settings.json → hooks)        │
│  PreToolUse 拦截 → 阻止危险命令和越界文件操作      │
├─────────────────────────────────────────────────┤
│  MCP Server 层 (src/healpr/server.py)            │
│  参数校验 → 路径白名单 + 仓库白名单               │
└─────────────────────────────────────────────────┘
```

| 层级 | 防护内容 |
|------|---------|
| **Skill** | 定义审查流程，约束 Claude 按步骤执行，禁止修改项目源码 |
| **Hooks** | 阻止 `git push`、`git commit --amend`、`rm -rf /`；阻止编辑 `src/`、`CLAUDE.md`、`.claude/` 等关键文件 |
| **MCP Server** | `clone_pr_branch`/`cleanup_work_dir` 限制在 `HEALPR_WORK_DIR` 内；GitHub 操作锁定到首次调用的目标仓库 |

---

## 使用方法

### 基本用法

在 Claude Code 中输入：

```
/pr-review owner/repo 123
```

其中 `owner/repo` 是 GitHub 仓库名（如 `facebook/react`），`123` 是 PR 编号。

### 审查流程

`/pr-review` 会自动执行以下 7 个步骤：

1. **获取 PR 信息** — 读取 PR 标题、描述、变更文件列表和 diff
2. **克隆 PR 分支** — 将 PR 代码拉取到本地工作目录
3. **运行 Linter** — 自动检测语言并运行对应的 linter（ruff/eslint/go vet）
4. **运行测试** — 自动检测测试框架并运行测试（pytest/jest/vitest/go test）
5. **执行审查** — 分析代码问题（安全漏洞、性能问题、逻辑错误等）
6. **发布结果** — 在 GitHub PR 上发布行级评论，严重问题会自动创建 issue
7. **清理工作目录** — 删除克隆的代码

### 严格模式

```
/pr-review --strict
```

严格模式会加载 `.claude/skills/pr-review/*.yaml` 中的规则，逐条检查代码是否违规。

默认包含 3 类规则：
- **安全审查** (security.yaml) — SQL 注入、eval/exec、鉴权中间件
- **架构审查** (architecture.yaml) — Repository 层、循环依赖、类型标注
- **性能审查** (performance.yaml) — N+1 查询、流式处理、缓存 TTL

你可以编辑这些 YAML 文件来自定义审查规则。

---

## 工具列表

healpr 提供 10 个 MCP 工具：

| 工具 | 功能 |
|------|------|
| `get_pr_info` | 获取 PR 信息（标题、描述、作者、变更文件） |
| `get_pr_diff` | 获取 PR 的完整 diff |
| `clone_pr_branch` | 克隆 PR 分支到本地工作目录 |
| `cleanup_work_dir` | 清理克隆的工作目录 |
| `run_linter` | 运行代码 linter |
| `run_test` | 运行项目测试 |
| `create_issue` | 在 GitHub 创建 issue |
| `post_review_comment` | 在 PR 的特定代码行发布评论 |
| `post_issue_comment` | 在 PR 讨论区发布评论 |
| `close_issue` | 关闭 GitHub issue |

---

## 安全防护

healpr 内置三层安全防护：

### 钩子层（Hooks）

- **Bash 钩子** — 阻止 `git push`、`git commit --amend`、`rm -rf /` 等危险命令
- **文件钩子** — 阻止修改项目源码（`src/`、`CLAUDE.md`、`pyproject.toml`、`.claude/`），只允许在工作目录中操作

### MCP 服务器层

- **路径白名单** — `clone_pr_branch` 和 `cleanup_work_dir` 只能在指定工作目录内操作
- **仓库白名单** — GitHub 操作锁定到首次调用的目标仓库

---

## 常见问题

### Q: `clone_pr_branch` 被阻塞怎么办？

A: 确保 `HEALPR_WORK_DIR` 环境变量已正确设置，且 Claude Code 已重启。工作目录必须存在且可写。

### Q: MCP 服务器没有出现在 `/mcp` 列表中？

A: 检查以下几点：
1. `pip install -e .` 是否成功执行（全局模式下必须安装）
2. 项目级：`.mcp.json` 文件是否存在且格式正确
3. 全局级：`~/.claude.json` 的 `mcpServers` 中是否添加了 `healpr`
4. `HEALPR_GITHUB_TOKEN` 环境变量是否已设置
5. 尝试重启 Claude Code

### Q: 审查规则怎么自定义？

A: 编辑 `.claude/skills/pr-review/` 目录下的 YAML 文件，按照已有格式添加新规则即可。每条规则包含 `id`、`check`（检查内容）和 `severity`（严重程度：critical/high/medium/low）。

### Q: 为什么同一会话中不能审查不同仓库的 PR？

A: 这是有意设计的安全机制。MCP server 会在首次 GitHub 操作时锁定目标仓库，后续所有操作必须针对同一仓库。这样可以防止审查 A 仓库时误将评论发到 B 仓库，也避免上下文中混入多个仓库的代码导致审查结论混乱。如果需要审查其他仓库的 PR，关闭当前会话开一个新的即可。

### Q: Windows 用户有什么注意事项？

A:
- 路径使用正斜杠 `/` 或双反斜杠 `\\`
- 钩子脚本中的 Python 路径可能需要调整
- `.git/objects/` 下的只读文件会自动处理（已内置 Windows 兼容逻辑）

---

## 开发者指南

### 运行测试

```bash
# 单元测试
pip install -e ".[dev]"
pytest tests/

# 集成测试（需要有效的 GitHub Token）
python test_mcp_tools.py
```

### 代码检查

```bash
ruff check src/
```

### 项目结构

```
ai-pr-healer/
├── .claude/                        # Claude Code 配置
│   ├── settings.json               # hooks + 权限配置
│   ├── settings.local.json         # 本地权限配置（不提交）
│   ├── skills/
│   │   └── pr-review/
│   │       ├── SKILL.md            # /pr-review 命令定义（审查流程 7 步）
│   │       ├── security.yaml       # 安全审查规则
│   │       ├── architecture.yaml   # 架构审查规则
│   │       └── performance.yaml    # 性能审查规则
│   └── hooks/
│       ├── check_bash_safety.py    # Bash 命令安全检查
│       └── check_file_safety.py    # 文件操作安全检查
├── src/healpr/                     # 核心代码
│   ├── server.py                   # MCP 服务器主类（工具注册 + 参数校验）
│   ├── config.py                   # 配置管理
│   ├── github/                     # GitHub API 客户端
│   │   ├── auth.py                 # Token 认证
│   │   └── client.py               # API 请求封装
│   └── tools/                      # MCP 工具实现
│       ├── git_tools.py            # git 克隆/清理
│       ├── lint_tools.py           # linter 运行
│       ├── test_tools.py           # 测试运行
│       └── github_tools.py         # GitHub 操作
├── tests/                          # 单元测试
├── .mcp.json                       # 项目级 MCP 配置（仅当前项目生效）
├── pyproject.toml                  # Python 项目配置
└── README.md                       # 本文件
```

**全局配置文件位置（不在项目目录内）：**

| 文件 | 位置 | 作用 |
|------|------|------|
| MCP Server 配置 | `~/.claude.json` | 全局 MCP server 配置（所有项目通用） |
| Hooks + 权限 | `~/.claude/settings.json` | 安全钩子、权限控制、环境变量 |
| Skill + 审查规则 | `~/.claude/skills/pr-review/` | `SKILL.md`（命令定义）+ `*.yaml`（审查规则） |

---

## 未来架构演进

healpr 当前已完成 MCP Server 核心能力，未来将沿以下方向持续演进：

### 第一阶段：平台增强

| 方向 | 目标 | 说明 |
|------|------|------|
| **Skill 文件** | 标准化审查策略 | 编写 `/review` Skill，规范 Claude 的调用策略和 Review 标准 |
| **Hooks 完善** | 防止架构漂移 | 设置 hooks 确保 Tool 调用符合预期模式，拦截越权操作 |
| **插件化** | 自定义扩展 | 支持自定义 linter、自定义测试命令、自定义 Review 规则 |

### 第二阶段：能力扩展

| 方向 | 目标 | 说明 |
|------|------|------|
| **多语言支持** | 覆盖更多技术栈 | 扩展语言检测和 linter 映射，支持更多编程语言 |
| **GitHub App 认证** | 组织级部署 | 替代 PAT，支持 GitHub App 安装到组织，团队共享使用 |
| **Review 规则市场** | 社区共享 | 支持从远程加载和分享 YAML 审查规则集 |

### 第三阶段：智能化闭环

```
┌─────────────────────────────────────────────────────────┐
│                    healpr 演进架构                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐          │
│  │ PR 审查   │───▶│ Bug 复现  │───▶│ 自动修复  │          │
│  └──────────┘    └──────────┘    └──────────┘          │
│       │               │               │                │
│       ▼               ▼               ▼                │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐          │
│  │ 行级评论  │    │ Issue 创建│    │ PR 提交   │          │
│  └──────────┘    └──────────┘    └──────────┘          │
│                        │               │                │
│                        ▼               ▼                │
│                  ┌──────────────────────┐               │
│                  │   Review 历史追踪     │               │
│                  │   (知识库 + 统计)     │               │
│                  └──────────────────────┘               │
│                                                         │
│  MCP Tools: 10 个原子工具                                │
│  安全防护: 三层防御（Skill / Hooks / MCP Server）         │
│  认证方式: PAT → GitHub App（演进中）                     │
└─────────────────────────────────────────────────────────┘
```

**核心演进理念：** healpr 始终保持"MCP Server 只提供工具，Claude 负责编排"的架构原则。Server 不调用任何 LLM API，所有智能决策由 Claude（Host）完成，确保架构简洁、可扩展、可测试。

---

## 许可证

MIT License
