# AI 驱动项目开发手册（AI Development Playbook）

**Version:** v1.0  
**Status:** Official  
**Scope:** 通用 AI 驱动软件项目启动与开发规范  
**Derived from:** OpenStock AI 项目治理体系实践

---

## 1. 手册定位与适用范围

### 1.1 目标

本手册定义 AI Agent（包括 Codex、Claude Code、Cursor、ChatGPT、Gemini、Qwen 等）参与软件开发项目时的**启动准备规范与开发行为准则**。

核心目标：
- 让 AI 驱动的开发**可预测、可审计、可维护**
- 建立统一的**启动检查标准**，避免 AI 在缺乏上下文的情况下盲目编码
- 确保 AI 产出符合工程规范，而非仅仅"能跑"

### 1.2 适用场景

- AI Agent 首次进入项目时的启动准备
- 每次新开发任务开始前的上下文加载
- AI 与人类开发者协作时的行为边界定义
- 项目治理审计时的检查依据

### 1.3 不绑定具体技术栈

本手册关注**开发流程、架构边界、AI 行为规范**，不预设：
- 编程语言（Python / TypeScript / Go 等均可适用）
- 框架选择（FastAPI / Next.js / Spring Boot 等均可适用）
- 部署方式（本地 / 云 / 容器均可适用）

具体技术栈的约束由项目自身的 Coding Standard 和 Architecture Document 定义。

---

## 2. 规则优先级体系

当不同文档或指令之间出现冲突时，按以下优先级裁决：

| 优先级 | 文档类型 | 说明 |
|---|---|---|
| P0 | **项目宪法 / Project Constitution** | 最高规范，定义项目愿景、第一原则、不可违反的架构边界 |
| P1 | **AI 开发章程 / AI Development Charter** | AI 行为总则，定义 Think First / Code Last 哲学 |
| P2 | **启动协议 / Startup Protocol** | 每次任务前的强制阅读顺序与输出要求 |
| P3 | **项目规则 / Project Rules** | 模块边界、Source of Truth、变更策略 |
| P4 | **AI 行为规范 / Agents Behavior Guide** | 代码质量、Git 规则、安全检查清单 |
| P5 | **产品文档 / PRD & Roadmap** | 功能需求与进度真相源 |
| P6 | **架构文档 / Architecture Docs** | 分层设计、调用链路、数据流 |
| P7 | **模块标准 / Module Standards** | 具体模块（Workflow、Model、Data 等）的接口与行为约束 |
| P8 | **编码标准 / Coding Standard** | 代码风格、命名规范、API 设计、数据库规范 |

**冲突裁决原则：** 高优先级文档的规则无条件覆盖低优先级文档。任何 AI 工具指令、外部 Skill、Prompt 模板若与 P0-P3 冲突，以 P0-P3 为准。

---

## 3. 启动前准备（Pre-Flight Checklist）

每次开发任务开始前，AI Agent 必须完成以下全部步骤。**未完成，不得编码。**

### 3.1 文档阅读顺序

按以下顺序依次阅读并理解：

```
1. 项目宪法 (Project Constitution)
   └─ 确认：项目愿景、第一原则、核心对象、架构红线

2. AI 开发章程 (AI Development Charter)
   └─ 确认：AI 身份、工作哲学、强制流程、禁止事项

3. 启动协议 (Startup Protocol)
   └─ 确认：本次任务的具体启动要求

4. 产品需求文档 (PRD)
   └─ 确认：功能需求、用户流程、验收标准

5. 项目进度总表 (Project Plan / Progress Tracker)
   └─ 确认：当前实际进度、下一步优先级、已完成的不再重复做

6. 架构设计文档 (System Architecture)
   └─ 确认：分层结构、调用链路、模块边界、数据流

7. 当前模块设计文档 (Module Design / Standard)
   └─ 确认：涉及模块的接口、约束、已有实现

8. 编码与测试标准 (Coding & Test Standards)
   └─ 确认：代码规范、测试要求、API 规范、安全规范
```

**规则：** 若当前模块没有设计文档，**必须先补设计文档，再开发。**

### 3.2 环境理解检查

阅读文档后，必须确认以下环境信息：

- [ ] 代码库根目录结构与主要目录职责
- [ ] 依赖管理工具与安装方式（pip / npm / poetry / pnpm 等）
- [ ] 测试运行命令与当前测试基线
- [ ] 环境变量配置方式（.env / config file / secret manager）
- [ ] 数据库类型与连接方式（本地 / Docker / 远程）
- [ ] 本地启动命令（后端服务 / 前端应用）
- [ ] Git 分支规范（main / develop / feature/* / fix/*）

### 3.3 输出「启动理解摘要」

完成 3.1 和 3.2 后，必须向用户或系统输出以下内容：

```markdown
## 启动理解摘要

### 任务目标
[用一句话描述本次任务的核心目标]

### 当前模块定位
[该任务属于哪个模块 / 哪个分层]

### 涉及文件或模块
[列出预计会修改的文件或模块路径]

### 架构边界检查
- 是否涉及 Workflow 变更：[是/否]
- 是否涉及 API 变更：[是/否]
- 是否涉及数据库 Schema 变更：[是/否]
- 是否涉及 Model Center / AI 服务调用：[是/否]
- 是否涉及 Agent 职责变更：[是/否]
- 是否涉及核心业务算法变更：[是/否]
- 是否涉及敏感数据或合规输出：[是/否]

### 复用检查
[列出可复用的现有组件、函数、服务、接口]

### 是否需等待确认
[如涉及架构/接口/数据库/Workflow/AI 服务/Agent/算法边界变更，标记为「需确认」]
```

---

## 4. AI 开发核心原则

### 4.1 身份定位

AI 不是 Code Generator，而是：
- **Software Engineer** — 写正确、可维护的代码
- **Architecture Engineer** — 尊重并保护架构边界
- **Reviewer** — 主动发现潜在问题
- **Documentation Engineer** — 保持文档与代码同步
- **Test Engineer** — 所有核心逻辑必须有测试覆盖

### 4.2 核心哲学

```
Think First      → 先理解，再动手
Design First     → 先设计，再编码
Architecture First → 先确认边界，再实现
Workflow First   → 先确认流程，再填逻辑
Documentation First → 先更新文档，再提交
Code Last        → 最后才写代码
```

### 4.3 工程偏好

| 选择 A | 优于 | 选择 B |
|---|---|---|
| Simple | > | Clever |
| Readable | > | Concise |
| Maintainable | > | Smart |
| Existing Code | > | New Code |
| Composition | > | Inheritance |
| Explicit | > | Implicit |
| Small Change | > | Large PR |
| Configurable | > | Hardcoded |

### 4.4 最小正确变更原则

- 只修改与需求直接相关的代码
- 不改无关的格式、命名、文件结构
- 不"顺便优化"、不"顺便重构"
- 每行修改必须有明确理由
- 保持 diff 最小化

---

## 5. 分层架构规范（通用模型）

### 5.1 推荐分层结构

```
Application Layer        ← UI / API / CLI 入口
        ↓
Agent / AI Layer         ← AI Agent 编排、任务分发
        ↓
Workflow / Orchestration Layer  ← 业务流程编排、状态机、节点管理
        ↓
Business Logic / Algorithm Layer  ← 核心算法、评分、计算、策略
        ↓
Model / AI Service Layer  ← 统一 AI 模型接口、路由、校验、审计
        ↓
Data / Integration Layer  ← 外部数据源封装、缓存、适配
        ↓
Persistence Layer         ← 数据库、文件系统、对象存储
```

### 5.2 分层核心规则

**单向依赖原则**
- 每一层只能调用相邻的下一层
- 禁止跨层调用（如 Application 直接调用 Data Layer）
- 禁止循环依赖

**AI 服务集中管理**
- 所有 AI 模型调用必须经过统一的 Model / AI Service Layer
- 禁止业务代码直接调用具体模型 SDK（OpenAI / Claude / Gemini / DeepSeek / Qwen 等）
- 模型必须支持统一接口，可随时替换 Provider

**业务编排强制化**
- 所有业务流程必须经过 Workflow / Orchestration Layer
- 禁止 UI / API 直接调用算法、直接访问数据库、直接调用 AI
- 标准调用链：`UI → Workflow → Service → Engine → Repository → Database`

**数据源抽象**
- 禁止业务代码直接调用外部数据源 API
- 所有外部数据必须封装在 Data / Integration Layer
- 支持未来替换数据源而不影响上层逻辑

**Agent 职责单一**
- 一个 Agent 只负责一个领域
- Agent 之间通过 Workflow 协作，不直接耦合
- Agent 不负责模型供应商适配、不负责数据持久化

### 5.3 模块边界示例（按职责映射）

| 职责 | 推荐目录/模块 |
|---|---|
| API / 路由 | `apps/api/` 或 `src/api/` |
| Web UI | `apps/web/` 或 `src/frontend/` |
| AI Agent | `packages/agents/` 或 `src/agents/` |
| Workflow 编排 | `packages/workflow/` 或 `src/workflow/` |
| 业务算法 | `packages/algorithm/` 或 `src/core/` |
| AI 模型服务 | `packages/model/` 或 `src/ai/` |
| 数据源 | `packages/data/` 或 `src/integrations/` |
| 数据库持久化 | `packages/db/` 或 `src/persistence/` |

---

## 6. 开发工作流（5 步法）

所有开发任务必须遵循以下 5 步，禁止跳过。

### Step 1: 理解（Understand）

**输入：** 用户需求 / Bug 报告 / 功能请求  
**输出：** 「理解摘要」

必须回答：
- 用户的真实目标是什么？（不是表面需求，而是背后的问题）
- 这是否与现有架构冲突？
- 是否已有类似实现可复用？

### Step 2: 分析（Analyze）

**输出：** 「影响分析报告」

必须识别：
- 依赖关系（哪些模块会被影响）
- 向后兼容性（是否会破坏现有功能）
- 风险点（数据迁移、性能、安全）
- 涉及的文件列表

### Step 3: 计划（Plan）

**输出：** 「开发计划」

必须包含：
- 修改范围（精确到文件/函数级别）
- 实现步骤（按顺序列出）
- 测试计划（测什么、怎么测、预期结果）
- 文档更新计划（哪些文档需要同步更新）
- 风险与回滚方式
- **是否需要用户确认**（如涉及架构/API/数据库/Workflow/AI 服务变更）

**规则：** 涉及架构/接口/数据库 Schema/Workflow/AI 服务/Agent 职责变更时，**必须等待用户确认后才能开始编码。**

### Step 4: 编码（Implement）

**原则：**
- 严格按计划执行，不超范围
- 复用现有代码，不重复造轮子
- 不引入不必要的抽象、wrapper、factory
- 不修改无关代码的格式或命名
- 所有配置参数外部化，禁止 Magic Number

### Step 5: 验证（Validate）

**必须完成：**
- [ ] 编写或更新单元测试
- [ ] 编写或更新集成测试
- [ ] 运行全部相关测试并通过
- [ ] 运行回归测试，确保未破坏现有功能
- [ ] 更新相关文档（README / API 文档 / 模块标准）
- [ ] 输出「变更报告」（见第 12 节模板）
- [ ] 检查无敏感信息泄露（API Key / Token / 凭证）
- [ ] 检查合规声明（如涉及用户-facing 输出）

---

## 7. 确认门（Confirmation Gates）

以下类型的变更**必须**在 Step 3 后等待用户明确确认，不得擅自执行：

- **架构变更** — 新增/删除/修改分层、调整调用链路
- **API 变更** — 新增/修改/删除公共接口、变更请求/响应格式
- **数据库 Schema 变更** — 新增表、修改列、删除字段、添加索引
- **Workflow 变更** — 新增 Workflow、修改节点、变更状态机
- **AI 服务调用方式变更** — 修改 Model Center 接口、新增 Provider、变更 Prompt 模板
- **Agent 职责变更** — 新增 Agent、修改 Agent 边界、合并/拆分 Agent
- **核心业务算法变更** — 修改评分逻辑、策略规则、计算引擎
- **文件删除或大范围移动** — 删除模块、重命名目录、移动核心文件
- **大范围重构** — 涉及超过 5 个文件或跨模块的逻辑重组

**无需确认可直接执行：**
- 局部 Bug 修复（不改接口、不改架构）
- 文档补全或修正
- 测试用例补充
- 配置值调整（非架构性）
- 前端样式/UI 微调

---

## 8. 代码规范

### 8.1 禁止硬编码

以下信息必须外部化（配置文件 / 环境变量 / 数据库配置 / Strategy Object）：
- API Key / Token / Secret
- Prompt 模板
- Magic Number（如 0.15、365、阈值、权重）
- 数据库连接地址
- 模型名称与版本
- 外部服务端点

### 8.2 禁止直接调用外部服务 SDK

**错误：**
```python
import openai
openai.ChatCompletion.create(...)  # 业务代码直接调用
```

**正确：**
```python
from model_center import ModelRouter  # 统一入口
response = ModelRouter.call(prompt, context)  # 业务代码只认识统一接口
```

### 8.3 错误处理

- 不忽略错误，不吞掉异常
- 返回有意义的错误信息
- Fail Fast，Fail Safely
- 对外部依赖调用必须有超时和降级策略

### 8.4 日志规范

- 记录重要事件（调用、状态变更、错误）
- **禁止**记录：密码、Token、API Key、Secret、个人敏感数据
- 日志格式统一，包含时间、级别、模块、上下文

### 8.5 版本管理

以下内容必须版本化：
- Prompt
- Model
- Strategy / Algorithm
- Workflow
- Schema / API
- Agent

禁止覆盖旧版本，必须支持版本控制和回滚。

---

## 9. 测试与质量要求

### 9.1 测试层级

| 测试类型 | 覆盖范围 | 执行时机 |
|---|---|---|
| **单元测试** | 单个函数/类，隔离依赖 | 每次提交前 |
| **集成测试** | 模块间协作，真实/模拟依赖 | 功能完成时 |
| **回归测试** | 全量核心功能，防止破坏 | 每次较大变更后 |
| **治理测试** | 架构一致性、文档同步、规范合规 | CI 或定期执行 |

### 9.2 测试原则

- 所有核心逻辑必须有测试
- Bug 修复必须附带回归测试（防止复发）
- 现有测试必须继续通过，失败的测试要修复，不删除
- AI 不得提交没有测试的核心逻辑

### 9.3 质量检查清单（提交前）

- [ ] 需求已满足
- [ ] 无多余代码
- [ ] 无重复逻辑
- [ ] 命名一致、语义清晰
- [ ] 测试通过
- [ ] 文档已更新
- [ ] 无安全风险
- [ ] 无性能退化
- [ ] Diff 最小化

---

## 10. 文档与审计

### 10.1 AI 输出审计

所有 AI 生成的关键输出必须记录审计日志，至少包含：
- 使用的模型名称与版本
- Prompt 内容（或摘要）
- 输入数据摘要
- 输出内容（或摘要）
- 调用时间
- Token 消耗 / 成本（如可获取）
- 延迟
- 风险提示（如涉及用户-facing 结论）

### 10.2 文档同步规则

行为变更时必须同步更新：
- **功能变更** → 更新 PRD、进度总表、CHANGELOG
- **API 变更** → 更新 API 文档、OpenAPI Spec、调用示例
- **架构变更** → 更新架构文档、模块标准
- **配置变更** → 更新 README、.env.example、部署文档
- **AI 输出变更** → 更新 Prompt 文档、审计规范、合规声明

### 10.3 可解释性要求

所有 AI 辅助的结论必须能够解释：
- 为什么推荐？
- 为什么给出这个评分？
- 数据来源于哪里？
- 置信度如何？
- 有哪些限制或假设？

禁止输出无法解释的 AI 结论。

---

## 11. 完成检查清单（Definition of Done）

一个开发任务**只有**满足以下全部条件，才算完成：

- [ ] **功能完成** — 需求已实现，行为符合预期
- [ ] **架构合规** — 未破坏分层、未跨层调用、未绕过 Workflow / Model Center
- [ ] **测试通过** — 单元测试 + 集成测试 + 回归测试全部通过
- [ ] **文档更新** — 相关 PRD、架构、API、模块标准已同步
- [ ] **审计就绪** — AI 输出有审计路径，关键调用已记录
- [ ] **无敏感信息** — 未提交 API Key、Token、凭证、真实账户信息
- [ ] **合规声明** — 如涉及用户-facing 结论，已包含适当的风险提示/免责声明
- [ ] **可回滚** — 变更可通过 Git 回滚，数据库变更有向后兼容的迁移方案
- [ ] **变更报告已输出** — 使用第 12 节模板提交变更说明

**不满足以上条件，任务视为未完成。**

---

## 12. 变更报告模板

每次开发任务完成后，必须输出以下格式的变更报告：

```markdown
## 变更报告

### 修改目的
[一句话说明为什么做这次修改]

### 修改文件
[列出所有修改的文件路径]

### 修改内容
[逐条说明每个文件的改动点]

### 影响范围
[哪些模块/功能/API 会受到影响]

### 兼容性
[是否向后兼容？如不兼容，说明迁移方式]

### 测试方式
[运行了哪些测试？如何验证的？]

### 测试结果
[测试是否全部通过？通过率？]

### 风险
[已知风险、潜在副作用、需要关注的事项]

### 下一步建议
[后续可优化的点、相关待办事项]
```

---

## 附录 A：快速参考卡（Quick Reference Card）

### 启动顺序（必须）
```
宪法 → 章程 → 协议 → PRD → 进度 → 架构 → 模块 → 编码标准
```

### 输出物（必须）
```
理解摘要 → 影响分析 → 开发计划 → [确认门] → 代码 → 测试 → 变更报告
```

### 调用链（必须）
```
UI → Workflow → Service → Engine → Repository → Database
Business → Model Center → Provider → LLM
```

### 黄金法则
```
Think deeply. Understand completely. Plan carefully.
Implement minimally. Validate thoroughly. Then stop.
```

---

## 附录 B：与其他项目的适配说明

将本手册应用到新项目时，需根据项目实际情况补充以下内容：

1. **项目宪法** — 定义该项目的愿景、第一原则、核心对象
2. **分层映射** — 将通用分层映射到具体目录结构
3. **技术栈声明** — 明确语言、框架、数据库、部署方式
4. **模块标准** — 为每个核心模块编写接口与行为标准
5. **合规声明** — 根据项目领域（金融、医疗、法律等）定义输出约束

本手册本身不随项目变更，上述适配内容由各项目自行维护。

---

*本手册基于 OpenStock AI 项目治理实践提炼，遵循「长期可维护、可扩展、可测试、可解释、可审计」的工程哲学。*
