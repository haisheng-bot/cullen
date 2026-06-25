# GitHub 协作标准 v0.1

## 1. 仓库基础文件

项目必须包含：

* README.md
* LICENSE
* CONTRIBUTING.md
* SECURITY.md
* CHANGELOG.md
* .gitignore
* .env.example
* Pull Request 模板
* Issue 模板
* Issue 模板配置
* CI 工作流

## 2. GitHub 分支保护要求

GitHub 仓库建议开启：

* 禁止直接 push 到 `main`
* PR 合并前必须通过 CI
* PR 合并前至少一次 review
* 线性历史或 squash merge
* 禁止提交敏感信息

分支约定：

```text
main        稳定版本
develop     开发集成分支
feature/*   新功能
fix/*       修复
docs/*      文档
```

## 3. Pull Request 要求

每个 PR 必须说明：

* AI 任务标识
* 使用的开发工具
* 修改范围
* 测试结果
* 文档是否更新
* 是否涉及外部 API
* 是否涉及 AI 输出
* 是否涉及投资结论
* 对应版本号或 CHANGELOG 条目
* 是否需要更新 README / PRD / API 文档

开发工具允许值：

```text
codex
claude-code
cursor
human
mixed
```

PR 模板必须包含以下检查区：

* 修改范围
* 关联任务
* AI 开发标识
* 版本与模块
* 测试结果
* 文档更新
* 外部 API / 数据源
* AI 输出与投资合规
* 安全检查
* 风险提示

## 4. Issue 要求

GitHub Issue 必须使用模板，不允许空白 Issue。

Issue 模板至少包含：

* Bug report
* Feature request

Bug report 必须包含：

* 问题描述
* 影响模块
* 复现步骤
* 期望结果
* 实际结果
* 测试或日志
* 环境
* 合规与安全检查

Feature request 必须包含：

* 功能描述
* 使用场景
* 产品模块
* 预期输入
* 预期输出
* 数据来源
* 验收标准
* 合规检查

## 5. CI 要求

CI 至少检查：

* Python 测试
* 项目结构
* 文档风险提示
* 后续加入 lint 和类型检查

## 6. 风险提示

所有投资相关输出必须包含：

> 本系统仅用于投资研究辅助，不构成任何投资建议。

## 7. 禁止事项

禁止提交：

* API Key
* Token
* 券商账户
* 身份证信息
* 银行卡信息
* 真实交易记录

禁止在 PR、Issue、README 或代码注释中承诺收益、诱导买卖或暗示无风险。
