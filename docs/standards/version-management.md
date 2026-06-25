# 版本管理标准 v0.1

## 1. 目标

版本管理必须同时满足：

* GitHub 协作要求
* AI 开发工具约束
* 敏捷迭代
* 即开发，即使用
* 每个版本可追溯
* 每个版本可回滚

## 2. 分支

```text
main        稳定版本
develop     开发版本
feature/*   新功能
fix/*       修复
docs/*      文档
chore/*     工程配置
release/*   发布准备
```

AI 开发工具不得直接修改 main 分支。

## 3. 分支规则

* `main` 只保存稳定版本。
* `develop` 保存可运行的开发版本。
* 所有功能从 `develop` 创建分支。
* 所有合并必须通过 Pull Request。
* 每个 PR 必须有测试结果和文档说明。
* AI 工具不得绕过 PR 流程直接修改 `main`。

## 4. Commit 规范

```text
feat: add stock scoring module
fix: correct SEC parser error
docs: update architecture standard
test: add unit tests for scoring
refactor: simplify data source interface
chore: update github workflow
```

## 5. 版本号

使用语义化版本：

```text
MAJOR.MINOR.PATCH
```

第一阶段使用 `0.x`。

版本含义：

```text
MAJOR  不兼容的大版本变化
MINOR  新增可用能力或里程碑
PATCH  修复、文档、小改进
```

## 6. OpenStock AI 版本路线

```text
0.1.x  项目治理、需求、架构、GitHub、AI 开发标准
0.2.x  FastAPI 后端基础、配置、健康检查、数据库连接
0.3.x  美股数据源接入
0.4.x  AI 模型统一接口和 Agent 编排
0.5.x  股票评分和推荐等级
0.6.x  前端查询、分析和报告页面
0.7.x  模拟组合和回测
0.8.x  MVP 端到端可用
0.9.x  发布候选、修复和稳定性
1.0.0  第一个稳定版本
```

## 7. Tag 规范

发布版本必须打 tag：

```text
v0.1.0
v0.2.0
v1.0.0
```

## 8. CHANGELOG 要求

每次可用功能合并时必须更新 `CHANGELOG.md`。

CHANGELOG 至少包含：

* Added
* Changed
* Fixed
* Security
* Docs

## 9. 发布要求

发布前必须满足：

* 测试通过
* CI 通过
* README 已更新
* docs 已更新
* CHANGELOG 已更新
* 无敏感信息
* AI 输出包含风险提示
* audit_logs 相关设计或实现已同步
