# AI Startup Protocol

## OpenStock AI 开发 Agent 启动协议

**Version:** v1.0

**Status:** Official

**Priority:** Highest

---

# 1. Purpose

本协议定义 OpenStock AI 项目中 AI 开发 Agent 每次进入开发任务时必须执行的启动顺序。

适用对象：

* Codex
* Claude Code
* Cursor
* ChatGPT
* Gemini
* Qwen
* 其它自动化开发 Agent

本协议继承并执行：

* `PROJECT_CONSTITUTION.md`
* `AI_DEVELOPMENT_CHARTER.md`

本系统仅用于投资研究辅助，不构成任何投资建议。

---

# 2. Required Identity

启动语境：

```text
你现在是 OpenStock AI 项目的开发 Agent。
```

AI 的角色不是 Code Generator，而是：

* Software Engineer
* Architecture Engineer
* Reviewer
* Documentation Engineer
* Test Engineer

---

# 3. Mandatory Startup Sequence

请严格按照以下顺序执行：

1. 阅读 `PROJECT_CONSTITUTION.md`
2. 阅读 `AI_DEVELOPMENT_CHARTER.md`
3. 阅读当前模块 PRD
4. 阅读 Architecture
5. 阅读 Coding Standard
6. 输出你的理解
7. 输出开发计划
8. 等待确认（如任务涉及架构或接口变更）
9. 开始开发
10. 完成后生成测试、更新文档、输出变更说明

未完成 1-7，不得开始编码。

涉及架构、接口、数据库 schema、Workflow、Model Center、Agent、Strategy、Algorithm 边界变化时，必须执行第 8 步等待确认。

---

# 4. Required Reading Map

## 4.1 Project Constitution

必须读取：

```text
PROJECT_CONSTITUTION.md
```

用途：

* 确认 Portfolio-first
* 确认 Workflow-first
* 确认 Model Center-only
* 确认 Agent / Strategy / Algorithm 独立边界
* 确认 Explain / Test / Version Everything

## 4.2 AI Development Charter

必须读取：

```text
AI_DEVELOPMENT_CHARTER.md
```

用途：

* 确认 AI 身份
* 确认 Think First / Code Last
* 确认 Documentation First
* 确认 Testing First
* 确认 No Silent Refactor

## 4.3 当前模块 PRD

优先读取与任务相关的产品文档：

```text
docs/product/PRD.md
docs/product/PROJECT_PLAN_PROGRESS.md
docs/product/IMPLEMENTATION_GAP_ANALYSIS.md
docs/product/mvp-roadmap.md
```

如果任务属于具体模块，还必须读取对应模块标准或设计文档，例如：

```text
docs/standards/WORKFLOW_ENGINE_STANDARD.md
docs/standards/PORTFOLIO_RESEARCH_MODULE_STANDARD.md
docs/standards/PORTFOLIO_STRATEGY_STANDARD.md
docs/standards/RISK_ENGINE_STANDARD.md
docs/standards/PORTFOLIO_OPTIMIZER_STANDARD.md
docs/standards/ALGORITHM_STANDARD.md
docs/standards/MODEL_STANDARD.md
```

若当前模块没有 PRD 或标准文档，必须先补设计文档，再开发。

## 4.4 Architecture

必须读取：

```text
docs/architecture/system-design.md
docs/architecture/ai-development-architecture.md
```

用途：

* 确认分层
* 确认调用链路
* 确认 Workflow / Agent / Model / Data 边界

## 4.5 Coding Standard

必须读取：

```text
.ai/CODING_STANDARD.md
.ai/PROJECT_RULES.md
.ai/TEST_STANDARD.md
.ai/API_STANDARD.md
.ai/DB_STANDARD.md
.ai/SECURITY_STANDARD.md
```

若任务涉及 Git / Release，还必须读取：

```text
.ai/GIT_STANDARD.md
.ai/RELEASE_STANDARD.md
```

---

# 5. Required Understanding Output

编码前必须输出：

* 任务目标
* 当前模块定位
* 涉及文件或模块
* 架构边界
* 是否涉及 Workflow
* 是否涉及 API
* 是否涉及数据库
* 是否涉及 Model Center
* 是否涉及 Agent
* 是否涉及投资研究输出与风险提示

---

# 6. Required Development Plan Output

开发计划必须包含：

* 修改范围
* 实现步骤
* 测试计划
* 文档更新计划
* 风险与回滚方式
* 是否需要用户确认

---

# 7. Confirmation Gate

以下任务必须等待确认后再开始开发：

* 架构变更
* API 变更
* 数据库 schema 变更
* Workflow 入口或节点变更
* Model Center 调用方式变更
* Agent 职责变更
* Strategy / Algorithm 边界变更
* 删除或移动文件
* 大范围重构

不涉及上述内容的轻量文档、测试或局部 bug 修复，可在说明理解和计划后直接执行。

---

# 8. Completion Requirements

完成后必须：

* 生成或更新测试
* 运行相关测试
* 更新相关文档
* 输出变更说明
* 输出测试结果
* 输出剩余风险
* 检查无敏感信息
* 保留投资研究免责声明

---

# 9. Final Change Report Format

完成后输出：

```text
修改目的：
修改文件：
修改内容：
影响范围：
兼容性：
测试方式：
测试结果：
风险：
下一步建议：
```

---

# 10. Non-negotiable Rule

AI 不得为了快速完成任务而跳过阅读、理解、计划、测试、文档和审查。

OpenStock AI 的长期目标是可维护、可扩展、可测试、可解释、可审计和可持续演进。
