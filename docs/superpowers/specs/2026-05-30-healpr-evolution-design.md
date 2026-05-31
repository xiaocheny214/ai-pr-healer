# healpr 演进设计：插件化 + 审查知识沉淀

## 概述

healpr 当前是一个功能完整的 MCP Server（10 个工具、三层安全架构、多语言支持）。本次演进聚焦两个方向：**插件化**（让审查能力可扩展）和**审查知识沉淀**（让审查有记忆）。不做 CI/CD，保持开发者主动触发模式。

## 决策记录

| 方向 | 决策 | 理由 |
|------|------|------|
| 插件化范围 | linter/test + 审查规则都可扩展 | 灵活性最高 |
| 插件发现 | 目录扫描 + 配置覆盖 | 零配置开箱即用，又能精细控制 |
| 插件接口 | Python 文件即插件 | 简单直接，插件作者需懂 Python |
| 知识存储 | 本地 JSONL + GitHub label 同步 | 兼顾离线和共享 |
| 知识使用 | 作为上下文注入，不作为硬规则 | 让 Claude 自行判断，避免误判 |
| CI/CD | 不做 | 与当前"开发者主动触发"定位不符 |

## 第一部分：插件系统

### 设计目标

将 `run_linter` 和 `run_test` 的内部实现从写死改为可扩展。Claude 调用方式不变，变的只是 server 内部的分发逻辑。

### 插件目录

```
~/.healpr/plugins/
├── mypy_plugin.py          # linter 插件
├── clippy_plugin.py        # test runner 插件
└── team_rules.yaml         # 审查规则插件（strict 模式自动加载）
```

### Linter/Test 插件接口

每个 `.py` 文件实现两个函数：

```python
def detect(work_dir: str) -> bool:
    """返回 True 表示此插件适用于该项目"""
    ...

def run(work_dir: str, file_path: str | None = None) -> dict:
    """执行检查，返回统一格式 {"success": bool, "issues": [...]}"""
    ...
```

### 插件加载流程

```
run_linter(work_dir) 被调用
  → PluginRegistry 扫描 ~/.healpr/plugins/*.py
  → 对每个插件调 detect(work_dir)
  → 适用的插件调 run(work_dir)，合并结果
  → 如果没有插件匹配，回退到内置逻辑（ruff/eslint/go vet）
```

插件优先级高于内置实现。

### 配置覆盖

环境变量：
- `HEALPR_PLUGINS_DIR` — 自定义插件目录，默认 `~/.healpr/plugins`
- `HEALPR_DISABLED_PLUGINS` — 逗号分隔的禁用插件列表

### 审查规则插件

strict 模式读取规则时，除内置 `*.yaml` 外，额外扫描 `~/.healpr/plugins/*.yaml`，合并到规则集。

## 第二部分：审查知识沉淀

### 设计目标

让审查有记忆：记录历史发现，自动提炼规则，作为上下文注入后续审查。

### 存储结构

```
项目根目录/
└── .healpr/
    ├── history.jsonl       # 审查历史（每条一行 JSON）
    └── auto_rules.yaml     # 自动提炼的规则
```

### 历史记录格式

```json
{
  "timestamp": "2026-05-30T14:30:00Z",
  "pr": "owner/repo#123",
  "findings": [
    {
      "file": "src/auth.py",
      "line": 42,
      "category": "security",
      "message": "eval() usage",
      "severity": "high"
    }
  ],
  "summary": "Found 3 issues: 1 security, 2 performance"
}
```

### 自动规则提炼

审查结束后扫描历史：
- 统计每个 category 出现次数
- 超过阈值（默认 3 次，可配置）自动生成 YAML 规则
- 存入 `.healpr/auto_rules.yaml`，strict 模式自动加载

### 上下文注入

`/pr-review` 流程中，步骤 1（获取 PR 信息）之后增加一步：
- 读取 `.healpr/history.jsonl` 最近 N 条记录（默认 10 条）
- 提取高频问题类别和高频文件
- 作为额外上下文："此项目历史上在 auth.py 多次发现安全问题，审查时多关注"

### GitHub 同步

审查完成后自动给 PR 打 label（如 `healpr:security`、`healpr:performance`），方便筛选。

## 第三部分：与现有代码的集成

### 新增文件

| 文件 | 用途 |
|------|------|
| `src/healpr/plugins.py` | PluginRegistry：扫描、加载、配置覆盖 |
| `src/healpr/history.py` | HistoryManager：追加记录、读取历史、规则提炼 |

### 修改文件

| 文件 | 改动内容 |
|------|---------|
| `src/healpr/tools/lint_tools.py` | `run_linter` 改为先查插件 registry，无匹配才走内置逻辑 |
| `src/healpr/tools/test_tools.py` | `run_test` 同上 |
| `src/healpr/server.py` | 启动时初始化 PluginRegistry；新增 2 个工具 |
| `src/healpr/config.py` | 新增插件和历史相关配置项 |
| `.claude/skills/pr-review/SKILL.md` | 步骤 1 后增加"加载历史上下文"步骤 |

### 新增 MCP 工具

| 工具 | 参数 | 返回 |
|------|------|------|
| `get_review_history` | `repo: str, limit: int = 10` | 最近 N 条审查记录摘要 |
| `save_review_result` | `repo: str, pr: str, findings: list` | 保存审查结果到历史库 |

### 不变的部分

- 现有 10 个工具的接口和行为不变
- 三层安全架构不变
- `/pr-review` 的 7 步流程不变（只在步骤 1 后加一步）
- Claude 调用方式不变

## 实现计划

### Phase 1：插件系统

1. 新增 `src/healpr/plugins.py` — PluginRegistry 类
2. 修改 `lint_tools.py` — 接入 PluginRegistry
3. 修改 `test_tools.py` — 接入 PluginRegistry
4. 修改 `config.py` — 插件配置项
5. 修改 `server.py` — 启动时初始化 registry
6. 单元测试：mock 插件文件，验证加载和分发逻辑

### Phase 2：知识沉淀

1. 新增 `src/healpr/history.py` — HistoryManager 类
2. 修改 `server.py` — 新增 `get_review_history` 和 `save_review_result` 工具
3. 修改 `SKILL.md` — 流程中加入历史上下文步骤
4. 单元测试：验证记录追加、规则提炼、上下文生成

### Phase 3：集成测试

1. 端到端测试：插件加载 → 审查 → 结果保存 → 下次审查读取历史
2. 验证配置覆盖（禁用插件、自定义目录）

## 验证方式

1. 写一个示例 linter 插件（如 `mypy_plugin.py`），放到插件目录，验证 `run_linter` 能调用它
2. 执行两次审查，验证 `history.jsonl` 有记录，第二次审查时 Claude 能看到历史上下文
3. 触发规则提炼阈值，验证 `auto_rules.yaml` 自动生成
4. 验证配置禁用插件后，插件不被加载
