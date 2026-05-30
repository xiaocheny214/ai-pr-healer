---
name: pr-review
description: PR 代码审查工具（使用 healpr MCP）。支持默认模式和严格模式。触发方式：/pr-review 或 /pr-review --strict
---

# PR 代码审查

## 使用方式

- `/pr-review` — 默认模式，Claude 自主判断审查重点
- `/pr-review --strict` — 严格模式，加载当前目录下 `review-rules/*.yaml` 逐规则检查

## 审查流程

收到审查请求后，按以下 7 步执行：

### 步骤 1: 获取 PR 信息

调用 `mcp__healpr__get_pr_info` 获取 PR 元数据（标题、描述、作者、变更文件列表）。
调用 `mcp__healpr__get_pr_diff` 获取完整 diff。

如果用户未指定 PR，提示用户提供 `owner/repo` 和 PR 编号。

### 步骤 2: Clone PR 分支

调用 `mcp__healpr__clone_pr_branch` 将 PR 分支 clone 到工作目录。

记录返回的 `work_dir` 路径，后续步骤使用。

### 步骤 3: 运行 Linter

调用 `mcp__healpr__run_linter`，传入步骤 2 的 `work_dir`。

记录 linter 输出结果。

### 步骤 4: 运行测试

调用 `mcp__healpr__run_test`，传入步骤 2 的 `work_dir`。

记录测试结果。

### 步骤 5: 执行审查

根据模式执行不同逻辑：

#### 默认模式

基于 diff 内容，Claude 自主分析：
- 代码逻辑错误
- 潜在安全问题
- 性能隐患
- 架构设计问题
- 代码风格问题

#### 严格模式

1. 读取当前 skill 目录下 `review-rules/` 中所有 `.yaml` 文件
2. 对每条规则，检查 diff 中是否存在违规
3. 按 severity 排序输出（critical > high > medium > low）

严格模式输出格式：
```
[规则ID][severity] 文件路径:行号
问题描述: ...
建议: ...
```

### 步骤 6: 输出结果

根据审查发现的问题：

- **有行级问题**：调用 `mcp__healpr__post_review_comment` 在具体代码行添加评论
- **有通用问题**：调用 `mcp__healpr__post_issue_comment` 在 PR 讨论区添加评论
- **有严重 bug**：调用 `mcp__healpr__create_issue` 创建 issue 跟踪

评论格式：
```
## 审查发现

### [severity] 问题标题

问题描述...

**文件**: `path/to/file.py:42`

**建议修复**:
\`\`\`python
# 修复代码
\`\`\`
```

### 步骤 7: 清理工作目录

调用 `mcp__healpr__cleanup_work_dir` 清理步骤 2 的 `work_dir`。

输出审查总结：
- 审查了多少个文件
- 发现了多少个问题（按 severity 分类）
- 创建了多少个 issue

## 注意事项

- 审查过程中禁止直接修改项目源码
- 审查过程中禁止推送到远程仓库
- 所有操作仅限于 MCP 工具提供的能力
