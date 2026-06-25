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
algorithm-v0.1    趋势型推荐算法 [released]
algorithm-v0.2    加入财务和估值因子（基于 SEC XBRL company facts） [released]
algorithm-v0.2.1  技术面因子升级为真实技术指标（RSI/均线金死叉/动量） [released]
algorithm-v0.2.2  基本面/估值因子加入 Magic Formula 指标（ROC、EV/EBIT） [released]
algorithm-v0.3    加入新闻情绪因子 [released]
algorithm-v0.4    加入风险模型 [planned]
algorithm-v1.0    稳定推荐算法 [planned]
```

算法版本必须出现在 API 响应和 audit_logs 设计中。

### 9.1 algorithm-v0.2 权重说明

v0.2 在 v0.1 基础上加入基本面、成长性、估值三个真实数据因子，权重分配为：

```text
fundamentals (基本面，净利润率)   30%
growth (成长性，营收同比)         20%
valuation (估值，P/E 绝对档位)    20%
technical (技术面)                20%
volatility_risk (风险，区间波动)  10%
```

这是 `project-standard-v0.1.md` 第 6 节目标权重（基本面30+成长性20+估值20+技术面10+新闻情绪10+风险10）在新闻情绪因子尚未接入前的过渡分配。v0.3 已接入新闻情绪因子，技术面权重回到 10%，新闻情绪使用 10%。

财务数据来自 SEC EDGAR XBRL company facts（`packages/data_sources/sec_financials.py`），免费、无需 Key。当某只股票缺少可用财务数据（例如新上市公司、非标准 XBRL 标签）时，三个因子退化为中性分（50分）并在 `risks` 字段中明确提示，不会导致接口报错。

### 9.2 algorithm-v0.2.1 技术面因子说明

v0.2 的 technical 因子原本只是把区间涨跌幅、相对前收盘涨跌幅、成交量活跃度三个粗略指标加权合并。v0.2.1 改为使用日线收盘价（`packages/data_sources/price_history.py` 拉取近 1 年，`packages/algorithm_layer/technical_indicators.py` 计算）算出的真实技术指标：

```text
momentum（10 日价格动量）   40%
RSI(14)                     30%
MA(5/20) 金叉/死叉状态      30%
```

当日线收盘价少于 `MIN_CLOSES_FOR_INDICATORS`（25 条，约一个半月）时——例如新上市股票——退化为 v0.2 之前基于当日内走势的粗略估算，并在 `explanation` 字段中说明"日线数据不足"，不影响接口可用性。RSI/均线状态等中间值通过 `factors[].explanation` 暴露，供未来前端替换面板上的占位 RSI/均线标签使用。

### 9.3 algorithm-v0.2.2 Magic Formula 指标说明

`fundamentals`（净利润率）和 `valuation`（P/E）单看都偏单一维度：净利润率不反映资本使用效率，P/E 不反映负债和现金对企业真实估值的影响。v0.2.2 引入 Joel Greenblatt「Magic Formula」用的两个经典指标，跟原有指标各占 50% 权重：

```text
fundamentals = 净利润率 50% + ROC（资本回报率）50%
valuation    = P/E 50% + EV/EBIT 50%
```

* **ROC** = 营业利润(EBIT) / (净营运资本 + 净固定资产)，净营运资本 = 流动资产 − 流动负债。衡量赚一块钱营业利润占用了多少资本，跟净利润率（赚一块钱收入剩多少利润）是两个独立维度。资本极轻的公司（比如净营运资本为负、固定资产很少）ROC 可能算出几百%，这是公式本身的真实特征（Magic Formula 对轻资产公司一向如此），不是计算错误，分数会按下面的带宽封顶。
* **EV/EBIT** = 企业价值(市值 + 总负债 − 现金) / 营业利润(EBIT)，跟 P/E 的差别是把负债和现金也计入，复用 P/E 的绝对档位评分函数（`_pe_band_score`）。

两个新指标都依赖 SEC XBRL 的 `OperatingIncomeLoss`/`AssetsCurrent`/`LiabilitiesCurrent`/`PropertyPlantAndEquipmentNet`/`CashAndCashEquivalentsAtCarryingValue`/`LongTermDebtNoncurrent` 等标签，覆盖率低于营收/净利润（部分行业，例如金融类公司，不一定有标准的 `OperatingIncomeLoss`）。任一指标缺数据时该因子自动退化为只用另一个指标，并在 `explanation` 中注明"缺 ROC 数据"/"缺企业价值数据"；两个都缺时退化为中性分 50，跟 v0.2 行为一致，不影响接口可用性。

### 9.4 algorithm-v0.3 新闻情绪因子说明

v0.3 接入 News / Policy Layer，新增 `news_sentiment` 因子，权重 10%。

```text
fundamentals       30%
growth             20%
valuation          20%
technical          10%
news_sentiment     10%
volatility_risk    10%
```

第一阶段新闻情绪为规则化估算：

* 输入来自 Yahoo Finance RSS 最近新闻和 SEC EDGAR 披露线索。
* 使用正向/负向关键词和治理、政策、任免类披露进行打分。
* 没有新闻信号时按 50 分中性处理，并在风险提示中说明。
* 后续可替换为 FinBERT、LLM 或专业新闻情绪数据源，算法输入接口保持不变。
