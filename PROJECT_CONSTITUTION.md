# OpenStock AI Project Constitution

## AI 项目开发宪法（Project Constitution）

**Version:** v1.0

**Status:** Official

**Priority:** Highest

---

# 1. 文档目的

本文件是 OpenStock AI 项目的最高开发规范。

所有开发人员、AI Agent、自动化工具必须遵守本规范。

任何代码、架构、Agent、Workflow、数据库、Prompt、模型设计均不得违反本文件。

如果与其它文档冲突，本文件优先级最高。

---

# 2. 项目愿景（Vision）

OpenStock AI 不是一个股票软件。

OpenStock AI 是一个 AI Portfolio Operating System。

平台用于：

* 股票研究
* 投资组合研究
* AI 研究
* Portfolio Optimization
* Quant Strategy
* Workflow Automation
* Agent Collaboration

平台目标：

帮助用户建立完整的 AI 投资研究体系，而不是直接提供买卖建议。

本系统仅用于投资研究辅助，不构成任何投资建议。

---

# 3. 第一原则（First Principle）

所有开发必须围绕：

> Portfolio（投资组合）

而不是：

> Stock（单只股票）

股票只是数据。

Portfolio 才是系统真正的核心对象。

所有 Workflow、Strategy、AI Agent、Risk、Backtesting 均围绕 Portfolio 工作。

---

# 4. Workflow First

Workflow 是整个系统的核心。

所有业务流程必须经过 Workflow Engine。

禁止：

* 页面直接调用算法
* 页面直接访问数据库
* 页面直接调用 AI
* 页面直接执行 Strategy

所有业务必须：

```text
UI
↓
Workflow
↓
Service
↓
Engine
↓
Data
```

Workflow 是唯一业务入口。

---

# 5. Model Center Only

任何模型调用必须统一经过 Model Center。

禁止以下调用直接出现在业务代码：

```text
OpenAI()
Claude()
Gemini()
DeepSeek()
Qwen()
```

必须：

```text
Business
↓
Model Center
↓
Provider
↓
LLM
```

所有模型必须支持统一接口。

未来允许随时替换模型。

当前代码中 `packages/model_layer` 是 Model Center 的实现基础。

---

# 6. Agent Independent

每个 Agent 只能负责自己的职责。

例如：

* Research Agent 只能负责研究。
* Risk Agent 只能负责风险。
* Portfolio Agent 只能负责组合。

禁止一个 Agent 同时完成数据库、AI、策略、页面等所有工作。

Agent 必须低耦合。

---

# 7. Strategy Independent

策略必须插件化。

禁止把策略写死。

每一个策略都是 Strategy Object。

支持：

* 新增
* 删除
* 升级
* 版本管理
* 共享
* Marketplace

---

# 8. Algorithm Independent

算法必须独立。

包括：

* Factor
* Portfolio
* Risk
* Optimizer
* Backtesting
* Recommendation

算法禁止写入：

* 页面
* Agent
* 数据库
* Workflow

算法必须 Engine 化。

---

# 9. Explain Everything

所有 AI 输出必须能够解释。

包括：

* 为什么推荐？
* 为什么收益高？
* 为什么收益低？
* 为什么增加仓位？
* 为什么降低风险？

禁止输出无法解释的 AI 结论。

Explainability 是系统核心能力。

---

# 10. Test Everything

所有核心模块必须可测试。

至少：

* Unit Test
* Integration Test
* Regression Test

禁止 AI 自动生成代码但没有测试。

---

# 11. Version Everything

以下内容必须版本化：

* Prompt
* Model
* Strategy
* Workflow
* Portfolio
* Schema
* API
* Agent

禁止覆盖旧版本。

必须 Version Control。

---

# 12. Configuration First

所有参数必须配置化。

禁止 Magic Number。

禁止写死：

```text
0.15
0.25
365
```

所有参数必须由配置文件、数据库配置、Profile 或 Strategy Object 管理。

---

# 13. Data Source Independent

任何数据源必须抽象。

禁止页面直接调用：

* Yahoo
* Polygon
* Finnhub
* SEC

任何数据源未来必须可以替换。

---

# 14. Plugin Architecture

所有模块必须插件化。

包括：

* Strategy
* Model
* Prompt
* Workflow
* Data Source
* Risk
* Report

未来支持 Marketplace。

---

# 15. AI Development Rules

所有 AI 工具：

* Codex
* Claude Code
* Cursor
* Gemini
* Qwen

进入项目后第一件事是阅读：

```text
README
↓
PRD
↓
Architecture
↓
Project Constitution
↓
Current Module
```

然后才能开始开发。

---

# 16. Git Rules

禁止直接修改 `main`。

必须使用：

```text
feature/
fix/
docs/
refactor/
```

每一个 PR 必须说明：

* 为什么改
* 影响哪些模块
* 测试结果
* 风险

---

# 17. Financial Compliance

系统仅用于 Investment Research。

禁止：

* 保证收益
* 稳赚
* 立即买

必须输出风险提示。

所有 Recommendation 属于 Research，不是 Investment Advice。

标准风险提示：

```text
本系统仅用于投资研究辅助，不构成任何投资建议。
```

---

# 18. AI Output Audit

所有 AI 输出必须记录：

* Model
* Prompt
* Input
* Output
* Time
* Token
* Cost
* Latency
* Version

方便未来回放、审计和 Debug。

---

# 19. Security

禁止提交：

* API Key
* Token
* 真实账户
* 银行卡
* 身份证
* 真实交易记录

全部使用 Environment Variables。

---

# 20. Development Definition of Done

一个功能完成必须满足：

* PRD 已完成
* 架构符合规范
* Workflow 已接入
* Model Center 已调用
* Agent 解耦
* 单元测试通过
* 集成测试通过
* 文档更新
* Git Commit 合规
* AI 审查完成
* Code Review 完成
* 无敏感信息
* 满足金融免责声明

否则不得合并。

---

# 21. AI Coding Standard

AI 开发前必须完成：

1. 阅读项目文档
2. 阅读架构
3. 阅读 Workflow
4. 阅读当前模块
5. 输出开发计划
6. 再开始编码

编码完成后必须输出：

* 修改文件
* 修改原因
* 影响范围
* 测试方法
* 下一步建议

禁止直接生成大量代码。

---

# 22. Long-term Goal

OpenStock AI 不追求快速完成。

而追求：

* 长期可维护
* 长期可扩展
* 长期可测试
* 长期可替换
* 长期可解释

未来能够支撑：

* Portfolio OS
* AI Agent
* Strategy Marketplace
* Plugin Marketplace
* Workflow Marketplace

成为一个真正的 AI Native Investment Research Platform。
