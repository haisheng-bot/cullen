# 版本管理标准 v0.1

## 1. 分支

```text
main        稳定版本
develop     开发版本
feature/*   新功能
fix/*       修复
docs/*      文档
```

AI 开发工具不得直接修改 main 分支。

## 2. Commit 规范

```text
feat: add stock scoring module
fix: correct SEC parser error
docs: update architecture standard
test: add unit tests for scoring
refactor: simplify data source interface
```

## 3. 版本号

使用语义化版本：

```text
MAJOR.MINOR.PATCH
```

第一阶段使用 `0.x`。

