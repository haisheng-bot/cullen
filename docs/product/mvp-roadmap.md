# 第一阶段 MVP 路线图 v0.1

## 1. MVP 范围

第一阶段只做：

* 股票代码查询
* 美股基础数据
* 实时走势图
* 美股操作界面
* SEC 财报读取
* AI 财报总结
* 新闻摘要
* 股票评分
* 研究报告生成
* 本地数据库保存

## 2. 暂不做

* 自动交易
* 实盘下单
* 期权策略
* 杠杆交易
* 高频交易

## 3. 里程碑

### M0 项目重建

* 标准文档
* 需求分析
* 架构设计
* GitHub 协作配置
* 基础测试

### M1 后端基础

* FastAPI 初始化 [usable]
* 配置管理（`packages/config.py`，环境变量 + `.env`） [verified]
* 数据库连接（`packages/db/session.py`，SQLAlchemy，默认回退本地 SQLite） [verified]
* audit_logs 表（`packages/db/models.py` + `packages/db/audit.py`） [verified]
* Docker Compose 本地 Postgres + Redis（`docker/docker-compose.yml`） [usable]
* 数据库初始化脚本（`scripts/init_db.py`） [usable]

### M2 数据源

* yfinance（近 10 年免费历史日 / 周 / 月线，`packages/data_sources/price_history.py`） [verified]
* SEC EDGAR
* FRED
* 实时走势 API 接入 [usable]

### M3 AI 分析

* 模型统一接口
* SEC Filing Agent
* News Agent
* Report Agent

### M4 评分与报告

* Scoring Agent
* 评分模型
* 研究报告生成

### M5 前端展示

* 美股操作工作台
* 实时走势图页面
* 股票分析页面
* 研究报告页面
