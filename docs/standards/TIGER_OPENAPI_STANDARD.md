# OpenStock AI Tiger OpenAPI 接入标准 v0.1

## 1. 定位

Tiger OpenAPI 是 OpenStock AI 的可选外部数据源，用于在用户授权后接入老虎证券官方开放接口的只读行情数据。

本项目不得读取、抓取、逆向或自动操作用户已打开的老虎 App。所有数据必须通过官方 OpenAPI、用户授权凭证和明确的数据源模块接入。

本系统仅用于投资研究辅助，不构成任何投资建议。

## 2. 第一阶段范围

第一阶段只做只读研究数据：

* Tiger OpenAPI 配置状态检查
* 单股 quote 数据接口
* 单股近 3 年历史 K 线参考数据
* 后续可扩展盘口、自选股和持仓读取

第一阶段不做：

* 自动交易
* 真实下单
* App 界面抓取
* 本地缓存读取
* 绕过官方权限的数据访问
* 逐笔 tick 全量历史数据承诺

## 3. 架构位置

```text
Application Layer
        |
API Layer
        |
Data Layer
        |
Tiger OpenAPI
```

代码位置：

```text
packages/data_sources/tiger_openapi.py
```

API 入口：

```text
GET /integrations/tiger/status
GET /stocks/{symbol}/tiger/quote
GET /stocks/{symbol}/tiger/history?years=3&period=day
```

## 3.1 历史数据边界

近 3 年老虎数据在第一阶段定义为：

* K 线 / OHLCV
* 成交量
* 成交额
* 日线、周线、月线
* 数据来源
* 分析时间
* 风险提示

第一阶段不把 Tiger OpenAPI 定义为逐笔 tick 全量数据源。若未来官方权限允许更细粒度数据，必须在独立版本中升级，并补充缓存、限流、数据成本和合规标准。

## 4. 配置标准

所有凭证只能放在 `.env` 或部署环境变量中：

```text
TIGER_ID=
TIGER_ACCOUNT=
TIGER_LICENSE=
TIGER_PRIVATE_KEY_PATH=
TIGER_ENV=sandbox
```

禁止把以下内容写入代码、文档、测试或提交记录：

* Tiger ID 真实值
* Tiger Account 真实值
* License 真实值
* 私钥内容
* 真实账户资产、持仓或交易记录

## 5. 安全边界

Tiger OpenAPI 数据源必须遵守：

* 默认 `trading_enabled=false`
* API 只读
* 不提供下单接口
* 不自动执行交易
* 不把真实账户信息写入 audit_logs
* 出错时只返回缺失字段名称，不回显敏感值

## 6. 后续版本

```text
tiger-openapi-v0.1  配置状态 + 单股 quote 只读接口 [released]
tiger-openapi-v0.2  近 3 年历史 K 线参考数据 [released]
tiger-openapi-v0.3  盘口数据 [planned]
tiger-openapi-v0.4  自选股 / 持仓只读同步 [planned]
tiger-openapi-v1.0  稳定只读研究数据源 [planned]
```
