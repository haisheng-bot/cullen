# OpenStock AI Algorithm Layer 标准 v0.1

## 1. 定位

Algorithm Layer 是 OpenStock AI 的独立算法层，专门负责股票评分、推荐等级、候选股排序、风险因子和回测策略算法。

推荐算法不得写在前端页面、API endpoint、Agent 或 Model Layer 内部。界面只展示算法结果，API 只负责调用算法层和返回结果。

本系统仅用于投资研究辅助，不构成任何投资建议。

## 2. 架构位置

```text
Application Layer
        |
Agent Layer
        |
Workflow Layer
        |
Algorithm Layer
        |
Model Layer
        |
Knowledge Layer
        |
Data Layer
```

Algorithm Layer 与 Model Layer 分离：

* Algorithm Layer 负责可解释评分、规则、排序、推荐等级。
* Model Layer 负责大模型统一调用、模型路由、模型审计。
* Agent Layer 可以使用 Algorithm Layer 的结果，但不能把算法逻辑写入 Agent。

## 3. 目录规范

算法代码必须放在：

```text
packages/algorithm_layer/
```

建议结构：

```text
packages/algorithm_layer/
├── __init__.py
├── schemas.py
├── base.py
├── recommendation.py
├── ranking.py
├── risk.py
└── backtest_signals.py
```

## 4. 第一阶段算法范围

第一阶段先实现：

* 单只股票推荐评分
* 推荐等级
* 趋势因子
* 波动风险因子
* 成交量因子
* 可解释推荐理由
* 风险提示

暂不把第一阶段算法写成最终投资策略。

## 5. 推荐等级

推荐等级必须使用合规表述：

```text
85-100：强关注
70-84：观察
50-69：中性
0-49：回避
```

禁止输出：

* 必买
* 保证上涨
* 无风险
* 稳赚
* 立即买入
* 立即卖出

## 6. 输入标准

算法输入必须是结构化数据。

第一阶段允许输入：

* symbol
* latest_price
* previous_close
* trend_points
* volume
* source
* analysis_time

后续扩展：

* financial_metrics
* valuation_metrics
* sec_summary
* news_sentiment
* macro_context
* portfolio_context

## 7. 输出标准

算法输出必须包含：

* symbol
* total_score
* recommendation
* factors
* reasons
* risks
* source
* algorithm_version
* analysis_time
* risk_disclaimer

## 8. 独立开发要求

Algorithm Layer 必须可以单独开发和测试。

要求：

* 不依赖 FastAPI
* 不依赖前端
* 不依赖真实 API Key
* 不直接调用外部数据源
* 使用结构化输入
* 单元测试可独立运行

## 9. 版本管理

算法需要独立版本号。

```text
algorithm-v0.1  趋势型推荐算法 [released]
algorithm-v0.2  加入财务和估值因子（基于 SEC XBRL company facts） [released]
algorithm-v0.3  加入新闻情绪因子 [planned]
algorithm-v0.4  加入风险模型 [planned]
algorithm-v1.0  稳定推荐算法 [planned]
```

算法版本必须出现在 API 响应和 audit_logs 设计中。

### 9.1 algorithm-v0.2 权重说明

v0.2 在 v0.1 基础上加入基本面、成长性、估值三个真实数据因子，权重分配为：

```text
fundamentals (基本面，净利润率)   30%
growth (成长性，营收同比)         20%
valuation (估值，P/E 绝对档位)    20%
technical (技术面，原 trend/day_change/volume 合并)  20%
volatility_risk (风险，区间波动)  10%
```

这是 `project-standard-v0.1.md` 第 6 节目标权重（基本面30+成长性20+估值20+技术面10+新闻情绪10+风险10）在新闻情绪因子尚未接入前的过渡分配：技术面权重临时从 10% 提到 20% 吸收新闻情绪的份额，v0.3 接入新闻情绪因子后会重新拆分。

财务数据来自 SEC EDGAR XBRL company facts（`packages/data_sources/sec_financials.py`），免费、无需 Key。当某只股票缺少可用财务数据（例如新上市公司、非标准 XBRL 标签）时，三个因子退化为中性分（50分）并在 `risks` 字段中明确提示，不会导致接口报错。

