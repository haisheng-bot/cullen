# Changelog

## [0.1.0] - Unreleased

### Added

* 重建 project5 为 OpenStock AI
* 项目标准文档 v0.1
* 需求分析 v0.1
* 系统设计框架
* AI 开发架构标准
* GitHub 协作标准
* 版本管理标准
* 敏捷迭代与即开发即使用标准
* 基础 CI 和治理测试
* 实时走势 API 和前端趋势图 MVP
* 独立 Model Layer 标准、目录和 mock provider
* AI 开发工具协作标准，支持 Codex、Claude Code、Cursor 混用开发
* 美股操作界面 MVP，包含热门美股、搜索、报价和实时走势
* 双击启动脚本 `open-app.command`
* 独立 Algorithm Layer 和趋势型推荐算法，并接入操作界面
* LiteLLM-compatible Model Layer provider 和标准
* 项目开发界面，展示版本、架构层和当前可用状态
* Universe Layer，用于每日扫描美股最活跃 Top 100 候选池
* 操作界面增加常用分析维度解读区域
* 后端基础：统一配置管理、数据库连接层、audit_logs 表，以及 Docker Compose（Postgres + Redis）和数据库初始化脚本
* yfinance 风格免费历史日线数据源（近 10 年日 / 周 / 月线 OHLCV），接入 `/stocks/{symbol}/history`
* SEC EDGAR 财报申报读取（免费，按代码解析 CIK，列出 10-K / 10-Q / 8-K 原文链接），接入 `/stocks/{symbol}/filings`
