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
* CI 工作流

## 2. GitHub 分支保护要求

GitHub 仓库建议开启：

* 禁止直接 push 到 `main`
* PR 合并前必须通过 CI
* PR 合并前至少一次 review
* 线性历史或 squash merge
* 禁止提交敏感信息

## 3. Pull Request 要求

每个 PR 必须说明：

* 修改范围
* 测试结果
* 文档是否更新
* 是否涉及外部 API
* 是否涉及 AI 输出
* 是否涉及投资结论
* 对应版本号或 CHANGELOG 条目

## 4. CI 要求

CI 至少检查：

* Python 测试
* 项目结构
* 文档风险提示
* 后续加入 lint 和类型检查

## 5. 风险提示

所有投资相关输出必须包含：

> 本系统仅用于投资研究辅助，不构成任何投资建议。
