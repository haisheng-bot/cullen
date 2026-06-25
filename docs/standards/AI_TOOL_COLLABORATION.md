# AI 开发工具协作标准 v0.1

## 1. 目标

OpenStock AI 允许同时使用多个 AI 开发工具，例如 Codex、Claude Code、Cursor。

多工具协作的目标是提升开发效率，但必须避免：

* 多个工具重复修改同一文件
* 改动来源不清
* 测试责任不清
* 文档更新遗漏
* Agent、Model Layer、业务代码边界混乱
* 未经确认直接改 main

本系统仅用于投资研究辅助，不构成任何投资建议。

## 2. 工具定位

### 2.1 Codex

推荐负责：

* 项目结构
* 代码实现
* 测试
* 本地运行验证
* Git 状态检查
* 文档同步
* 小步提交

### 2.2 Claude Code

推荐负责：

* 架构设计
* 需求拆解
* 复杂逻辑审查
* 文档草案
* Prompt 和 Agent 设计
* 代码 review

### 2.3 Cursor

推荐负责：

* 局部文件编辑
* 前端页面微调
* 类型修复
* 快速补全
* 人工交互式修改

## 3. 混用原则

允许混用，但必须满足：

* 同一时间只允许一个工具负责提交
* 同一任务必须有唯一任务标识
* 改动前必须说明修改范围
* 改动后必须说明测试结果
* 每个工具必须尊重当前 Git 状态
* 不得覆盖其他工具或人工未提交改动
* 不得直接修改 `main`

## 4. 任务标识

每个 AI 协作任务必须使用任务标识。

格式：

```text
AI-YYYYMMDD-NNN
```

示例：

```text
AI-20260625-001
```

任务标识应出现在：

* PR 描述
* CHANGELOG 条目
* 关键文档更新
* 必要时出现在 commit body

## 5. 开发者标识

AI 工具需要在 PR 或交接记录中标识自己。

允许值：

```text
codex
claude-code
cursor
human
mixed
```

如果多个工具参与，标记为 `mixed`，并在说明中列出分工。

## 6. 推荐协作流程

```text
Human 定义目标
  -> Claude Code 拆需求和架构
  -> Codex 落地代码、测试和文档
  -> Cursor 做局部编辑或 UI 微调
  -> Codex 跑测试和 Git 检查
  -> Human review
  -> PR 合并
```

## 7. 文件所有权建议

### 7.1 架构与标准

优先由 Claude Code 起草，Codex 负责落盘和测试同步。

### 7.2 后端和数据源

优先由 Codex 实现和验证。

### 7.3 前端交互

Codex 可实现基础页面，Cursor 可做细节调整。

### 7.4 Prompt 和 Agent 设计

Claude Code 可负责设计，Codex 负责结构化到 `docs`、`packages` 和测试。

### 7.5 Model Layer

Model Layer 是核心基础层，任何工具修改前必须阅读：

* `docs/standards/MODEL_STANDARD.md`
* `docs/architecture/system-design.md`
* `docs/architecture/ai-development-architecture.md`

## 8. 交接记录

当一个工具完成工作，必须留下交接信息：

```text
Task ID:
Tool:
Scope:
Files changed:
Tests run:
Known risks:
Next step:
```

## 9. Commit 和 PR 标识

Commit message 继续使用 Conventional Commits。

建议 commit body 或 PR 描述包含：

```text
Task: AI-20260625-001
Tool: codex
```

如果是混用：

```text
Task: AI-20260625-001
Tool: mixed
Tools:
- claude-code: architecture review
- codex: implementation and tests
- cursor: UI adjustment
```

## 10. 冲突处理

发生冲突时：

* 先停止继续编辑
* 检查 `git status`
* 确认哪些改动来自哪个工具
* 保留人工改动优先
* 只解决当前任务相关冲突
* 不使用破坏性命令清空工作区

## 11. 完成标准

AI 工具协作任务完成必须满足：

* 代码或文档已落盘
* 测试已运行
* Git 状态已检查
* CHANGELOG 已更新
* README 或 docs 已同步
* 没有敏感信息
* 投资相关输出有风险提示

