# AI 开发架构标准 v0.1

## 1. AI 开发原则

Codex / Claude Code / Cursor 在本项目中必须遵守：

* 不直接修改 main 分支
* 修改前说明范围
* 修改后生成测试
* 不删除核心文档
* 不绕过类型检查
* 不硬编码 API Key
* 不写入真实账户信息
* 外部 API 调用必须封装
* 投资结论必须带风险提示
* 新增模块必须更新 docs
* 每次迭代必须保持项目可运行或可测试
* 不能把未实现功能描述为已发布功能
* 多工具混用时必须标识任务、工具和交接记录

## 2. AI 开发流程

```text
读取需求和标准文档
  -> 明确修改范围
  -> 在 develop 或 feature/* 分支开发
  -> 先更新设计或接口约定
  -> 编写测试
  -> 运行检查
  -> 更新 docs
  -> 更新 CHANGELOG
  -> 提交 Pull Request
```

## 3. AI 架构开发要求

AI 相关功能必须按以下结构开发：

```text
Policy Guard
  -> Data Context Builder
  -> Workflow Executor
  -> Model Layer
  -> Agent Executor
  -> Output Validator
  -> Audit Logger
```

模型供应商适配不属于 Agent Layer，必须放入独立 Model Layer。

每个 AI Agent 必须明确：

* 输入数据
* 输出结构
* 使用模型
* 数据来源
* 风险提示
* 错误处理
* audit_logs 写入字段
* 测试用例

## 4. 模型调用架构

系统不得绑定单一模型。

模型调用必须经过 `packages/model_layer` 统一接口，支持：

* OpenAI
* Claude
* Gemini
* DeepSeek
* Qwen
* Llama
* 本地模型

模型层标准以 `docs/standards/MODEL_STANDARD.md` 为准。

## 5. AI 输出校验

AI 输出必须检查：

* 是否包含数据来源
* 是否包含分析时间
* 是否包含使用模型
* 是否包含输入数据摘要
* 是否包含风险提示
* 是否包含禁止词

本系统仅用于投资研究辅助，不构成任何投资建议。

## 6. 即开发即使用要求

AI 开发工具完成一个功能后，必须留下可执行入口或验证方式。

允许的验证方式包括：

* API 测试
* 单元测试
* 集成测试
* 本地脚本
* 前端页面
* 示例输入输出

没有验证方式的功能不得标记为完成。

## 7. 多 AI 工具协作

本项目允许 Codex、Claude Code、Cursor 混用开发。

混用时必须遵守：

* `docs/standards/AI_TOOL_COLLABORATION.md`
* 同一任务使用唯一任务标识
* 同一时间只允许一个工具负责提交
* 每个工具必须说明修改范围和测试结果
* 不得覆盖其他工具或人工未提交改动
* 交接时必须留下任务、工具、文件、测试和风险说明
