# OpenStock AI Model Layer 标准 v0.1

## 1. 重要性

Model Layer 是 OpenStock AI 的核心基础层之一。

本项目禁止把模型调用逻辑直接写入 Agent、Workflow、API 或业务代码中。所有大模型、本地模型、模型路由、模型配置、模型输出规范、成本统计和模型审计必须统一放在 Model Layer。

如果模型、业务和 Agent 耦合在一起，后期将难以替换模型、扩展供应商、控制成本、做评测和保证合规。因此 Model Layer 是 OpenStock AI 长期可演进能力的关键。

本系统仅用于投资研究辅助，不构成任何投资建议。

## 2. 架构位置

OpenStock AI 的核心分层如下：

```text
Application Layer
        |
Agent Layer
        |
Workflow Layer
        |
Model Layer
        |
Knowledge Layer
        |
Data Layer
```

Model Layer 位于 Workflow Layer 之下、Knowledge Layer 之上。

## 3. 分层职责

### 3.1 Application Layer

负责 API、前端页面、用户请求和响应展示。不得直接调用具体模型。

### 3.2 Agent Layer

负责定义角色和任务，例如 Market Data Agent、SEC Filing Agent、News Agent、Scoring Agent、Report Agent。

Agent 只描述任务、输入、输出和推理目标，不绑定具体模型供应商。

### 3.3 Workflow Layer

负责股票分析、AI 选股、财报总结、新闻情绪分析和研究报告生成等流程编排。

Workflow 可以调用 Model Layer，但不得直接调用 OpenAI、Claude、Gemini、DeepSeek、Qwen、Llama 或本地模型 SDK。

### 3.4 Model Layer

负责所有模型相关能力：

* 模型供应商适配
* 模型能力抽象
* 模型路由
* Prompt 输入封装
* 输出结构校验
* token 和成本统计
* 失败重试
* fallback 模型
* 本地模型接入
* 模型审计信息生成

### 3.5 Knowledge Layer

负责知识库、向量库、检索、财报片段、新闻片段和上下文构建。

Knowledge Layer 可以为 Model Layer 提供上下文，但不负责调用模型。

### 3.6 Data Layer

负责市场数据、SEC 数据、新闻数据、宏观数据、数据库和缓存。

Data Layer 不负责模型调用。

## 4. 目录规范

Model Layer 代码必须放在：

```text
packages/model_layer/
```

建议结构：

```text
packages/model_layer/
├── __init__.py
├── base.py
├── registry.py
├── router.py
├── schemas.py
├── providers/
│   ├── openai_provider.py
│   ├── claude_provider.py
│   ├── gemini_provider.py
│   ├── deepseek_provider.py
│   ├── qwen_provider.py
│   └── local_provider.py
└── tests/
```

第一阶段可以先实现接口和 mock provider，不要求一次性接入所有真实模型。

## 5. 支持模型

以下模型供应商只能在 Model Layer 中出现：

* OpenAI
* Claude
* Gemini
* DeepSeek
* Qwen
* Llama
* 本地模型

Agent、Workflow、API、Data Source 不得硬编码这些供应商 SDK 调用。

## 6. 统一模型请求

所有模型请求必须转换为统一结构。

```text
ModelRequest
  task_type
  model_provider
  model_name
  system_instruction
  user_input
  context
  output_schema
  temperature
  max_tokens
  trace_id
```

`context` 必须来自 Data Layer 或 Knowledge Layer 的可追溯数据。`trace_id` 必须进入 audit_logs。

## 7. 统一模型响应

所有模型响应必须转换为统一结构。

```text
ModelResponse
  provider
  model_name
  task_type
  output
  citations
  confidence
  token_usage
  cost_estimate
  latency_ms
  risk_disclaimer
  trace_id
```

所有投资相关输出必须包含：

> 本系统仅用于投资研究辅助，不构成任何投资建议。

## 8. 模型路由

Model Router 负责选择具体模型。

路由依据包括：

* 任务类型
* 成本
* 延迟
* 上下文长度
* 结构化输出能力
* 本地模型可用性
* API Key 可用性
* fallback 策略

## 9. Agent 与 Model Layer 边界

Agent 可以定义任务目标、准备任务输入、请求 Workflow 执行、使用 ModelResponse 的结果。

Agent 不可以：

* 直接调用模型 SDK
* 直接读取 API Key
* 硬编码模型名称
* 自己实现 fallback
* 绕过输出校验
* 绕过 audit_logs

## 10. Workflow 与 Model Layer 边界

Workflow 可以调用 Model Router、组合多个模型调用、处理步骤状态、传递 trace_id。

Workflow 不可以直接依赖某个模型 SDK，不可以把 provider 细节暴露给 Agent，不可以跳过 ModelResponse 标准结构。

## 11. 配置和密钥

模型 API Key 只能从环境变量读取。

禁止：

* 硬编码 API Key
* 将真实 key 写入测试
* 将 key 写入 docs
* 将 key 写入 commit

`.env.example` 只能保留空值示例。

## 12. 审计要求

每次模型调用必须生成审计字段：

* trace_id
* task_type
* provider
* model_name
* input_summary
* output_summary
* citations
* token_usage
* cost_estimate
* latency_ms
* risk_disclaimer
* created_at

这些字段必须能够写入 `audit_logs`。

## 13. 输出合规

Model Layer 必须在响应返回前检查：

* 是否包含风险提示
* 是否包含数据来源或 citations
* 是否包含模型信息
* 是否包含禁止词
* 是否存在收益承诺
* 是否诱导买卖股票

禁止输出：

* 必买
* 保证上涨
* 无风险
* 稳赚
* 立即买入
* 立即卖出

## 14. 测试要求

Model Layer 每个 provider、router 和 schema 必须有测试。

第一阶段至少测试：

* ModelRequest 结构
* ModelResponse 结构
* mock provider
* router fallback
* 风险提示检查
* 禁止词检查
* 不读取真实 API Key

## 15. 版本演进

Model Layer 单独记录能力版本。

```text
model-layer-v0.1  接口标准和 mock provider
model-layer-v0.2  OpenAI / 本地模型适配
model-layer-v0.3  Claude / Gemini / DeepSeek / Qwen 适配
model-layer-v0.4  模型路由和 fallback
model-layer-v0.5  成本统计和评测
model-layer-v1.0  稳定模型抽象层
```

任何模型层破坏性变更必须同步更新 docs、CHANGELOG 和 tests。

