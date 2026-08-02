# OpenStock AI Scoring Profiles 标准 v0.1

## 1. 定位

Scoring Profiles 是 Algorithm Layer 因子权重的独立配置层，解决 Project Constitution 第12条（Configuration First，禁止 Magic Number）的一个具体违规：`packages/algorithm_layer/recommendation.py` 和 `packages/backtesting/signals.py` 此前各自硬编码一套 v0.3 六因子权重。

本系统仅用于投资研究辅助，不构成任何投资建议。

## 2. 目录规范

```text
packages/scoring_profiles/
├── __init__.py
├── schemas.py            # ScoringProfile dataclass
├── profiles.py            # 5 个内置 profile + get_profile/list_profiles
└── backtest_weights.py    # renormalize_excluding，供回测排除 news_sentiment 后重新归一化
```

不依赖 FastAPI、前端或数据库，纯函数模块，可独立单测（`tests/test_scoring_profiles.py`）。

## 3. 内置 Profile（v0.1，只读，不支持用户自定义保存）

六因子覆盖：`fundamentals`、`growth`、`valuation`、`technical`、`news_sentiment`、`volatility_risk`，每个 profile 权重总和为 1.0。

| Profile | fundamentals | growth | valuation | technical | news_sentiment | volatility_risk |
|---|---|---|---|---|---|---|
| balanced（默认，= algorithm-v0.3 原硬编码值） | 30% | 20% | 20% | 10% | 10% | 10% |
| growth | 20% | 35% | 10% | 15% | 10% | 10% |
| value | 35% | 10% | 35% | 5% | 5% | 10% |
| defensive | 30% | 10% | 15% | 5% | 10% | 30% |
| momentum | 15% | 15% | 10% | 35% | 15% | 10% |

## 4. 消费方

* `packages/algorithm_layer/recommendation.py::TrendRecommendationAlgorithm.recommend(data, profile=None)`：默认 Balanced。
* `packages/backtesting/signals.py::ai_score(latest, previous, closes, profile_name="balanced")`：回测场景排除 `news_sentiment`（无历史新闻归档，引入会造成 lookahead bias），通过 `renormalize_excluding` 重新归一化剩余 5 个因子，不维护第二套硬编码权重。
* `packages/backtesting/schemas.py::StrategyConfig.scoring_profile`：贯穿 `/backtests/run` 和 Portfolio Research 的回测路径。

## 5. API 接入

* `GET /stocks/{symbol}/recommendation?scoring_profile=growth`
* `GET /stocks/screening?scoring_profile=value`
* `POST /portfolio-research/run`：`strategy_preferences.scoring_profile`

未知 profile 名一律返回 400，错误信息为 `unknown scoring profile: <name>`。

## 6. 不在 v0.1 范围内

* 不支持用户自定义权重组保存——仍是 5 个内置只读 profile；注意这和 Strategy Library v0.2（已完成，见 `docs/product/PROJECT_PLAN_PROGRESS.md` P9）不是一回事：v0.2 只是让策略可以绑定并校验某个*已有*的 profile 名字，不涉及创建自定义权重组，该能力目前未排期。
* 不在前端加 profile 选择 UI（本次只做 API 层，前端选择器留作后续任务）。

## 7. 版本管理

```text
scoring-profiles-v0.1   内置 5 个只读 profile，接入 recommendation/screening/portfolio-research [released]
```
