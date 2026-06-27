# OpenStock AI Workflow Engine Standard v1.0

## 1. Module Vision

Workflow Engine is the business orchestrator of OpenStock AI.

It does not calculate factors directly, does not run portfolio optimization directly, and does not call model provider SDKs directly. Its job is to organize the full AI investment research lifecycle and coordinate independent modules.

Workflow Engine is the central layer that drives OpenStock AI from a stock analysis tool toward an **AI Portfolio Operating System**.

本系统仅用于投资研究辅助，不构成任何投资建议。

## 2. Architecture Position

```text
Application Layer
        |
Agent Layer
        |
Workflow Engine
        |
Universe Layer
        |
Portfolio Layer
        |
Factor / Algorithm Layer
        |
Strategy Layer
        |
Backtesting / Risk Layer
        |
Model Layer
        |
Data Layer
```

Workflow Engine may call Agent, Strategy, Backtesting, Risk and Report modules through explicit interfaces. It must not hide provider-specific model calls, broker order placement, or external API credentials inside workflow code.

## 3. Core Workflow

The long-term target workflow is:

```text
User
  -> Universe Builder
  -> Portfolio Builder
  -> Factor Engine
  -> Strategy Engine
  -> Constraint Engine
  -> Portfolio Optimizer
  -> Backtesting Engine
  -> Risk Engine
  -> AI Research Agent
  -> Recommendation Engine
  -> Report Engine
  -> Rebalance Engine
```

## 4. Workflow Modules

### 4.1 Universe Builder

Builds the research universe.

Supported universe types:

* Most Active
* AI Theme
* Semiconductor
* Momentum
* Growth
* Dividend
* ETF
* Crypto
* Healthcare
* Energy
* Custom Universe

Output:

```text
Universe
├── name
├── market
├── symbols
├── tags
└── created_time
```

### 4.2 Portfolio Builder

Creates and manages portfolios.

Supported operations:

* Create Portfolio
* Edit Portfolio
* Clone Portfolio
* Delete Portfolio
* Import Portfolio
* Export Portfolio

Output:

```text
Portfolio
├── name
├── stocks
├── weight
├── cash
├── benchmark
└── metadata
```

### 4.3 Factor Engine

Coordinates factor calculation through Algorithm Layer and related data modules.

Supported factors:

* Momentum
* Growth
* Value
* Quality
* Dividend
* Beta
* Volatility
* Liquidity
* Market Cap
* AI Score
* News Score

Output:

```text
Stock -> Factor -> Score
```

### 4.4 Strategy Engine

Calculates target portfolios from selected strategy rules.

Supported strategy families:

* Equal Weight
* Market Cap
* Dividend
* Growth
* Value
* Momentum
* Mean Variance
* Risk Parity
* HRP
* Black-Litterman
* Minimum Variance
* AI Score Strategy
* AI Ranking
* AI Dynamic Allocation

Output:

```text
Symbol
Weight
Expected Return
```

### 4.5 Constraint Engine

Manages portfolio constraints.

Supported constraints:

* Max position weight
* Max sector weight
* Max beta
* Max volatility
* Minimum cash
* Max holdings
* Minimum trade amount

Output:

```text
Constraint Object
```

### 4.6 Portfolio Optimizer

Generates optimal target weights from expected return, covariance matrix and constraints.

Output:

* Weight
* Expected Return
* Risk
* Sharpe

### 4.7 Backtesting Engine

Runs strategy backtests.

Supported windows:

* 1Y
* 3Y
* 5Y
* 10Y
* Custom

Output metrics:

* Total Return
* Annualized Return
* CAGR
* Sharpe
* Sortino
* Alpha
* Beta
* Win Rate
* Max Drawdown

### 4.8 Risk Engine

Analyzes portfolio risk.

Risk dimensions:

* Beta
* Volatility
* Drawdown
* VaR
* CVaR
* Correlation
* Sector Exposure
* Position Exposure
* Concentration Risk

Output:

```text
Risk Report
```

### 4.9 AI Research Agent

Explains workflow results through Agent Layer and Model Layer.

Questions it should answer:

* Why recommend this portfolio?
* Why did returns improve?
* Why is risk lower or higher?
* Why rebalance?
* What news, filings or macro events matter?

Output:

```text
AI Research Report
```

### 4.10 Recommendation Engine

Generates portfolio recommendations.

Examples:

```text
Increase NVDA
Decrease TSLA
Increase Cash
Reduce Technology Exposure
```

Output:

```text
Recommendation Report
```

### 4.11 Report Engine

Generates research artifacts:

* Dashboard
* PDF
* Markdown
* HTML
* PPT later

Reports must include:

* Portfolio Summary
* Performance
* Risk
* AI Analysis
* Recommendation

### 4.12 Rebalance Engine

Runs periodic updates:

```text
Market Update
  -> Recalculate
  -> Re-optimize
  -> Re-backtest
  -> AI Explanation
  -> New Report
```

Supported schedules:

* Daily
* Weekly
* Monthly
* Custom

## 5. Workflow State Machine

All workflows use the same lifecycle:

```text
Created
  -> Configured
  -> Waiting
  -> Running
  -> Completed
  -> AI Reviewing
  -> Recommendation Ready
  -> Archived
```

Failure state:

```text
Failed
```

Every state transition must be explicit and testable.

## 6. Data Flow

```text
Universe
  -> Portfolio
  -> Factor
  -> Strategy
  -> Constraint
  -> Optimizer
  -> Backtesting
  -> Risk
  -> AI Research
  -> Recommendation
  -> Report
  -> Rebalance
```

## 7. Workflow And AI Agent Boundary

Workflow does not directly execute AI provider calls. It schedules Agent Layer tasks.

Agent chain:

```text
Research Agent
  -> News Agent
  -> Financial Agent
  -> Strategy Agent
  -> Risk Agent
  -> Portfolio Agent
  -> Macro Agent
  -> Report Agent
  -> Decision Agent
```

Workflow is responsible for:

* Agent ordering
* Agent input
* Agent output routing
* Agent state management
* Trace IDs
* Runtime metadata

Workflow is not responsible for:

* Provider SDK calls
* Prompt provider secrets
* Direct broker trading
* Hardcoded API keys

## 8. Observability And Audit

Each workflow run must record:

* Workflow name
* Workflow version
* Trace ID
* Node name
* Node status
* Input summary
* Output summary
* Duration
* Error message if failed
* Risk disclaimer

AI outputs must also be written to `audit_logs` through the Agent or Model auditing path.

### 8.1 Research Run History

`packages/db/workflow_runs.py::list_workflow_runs()` queries the same `workflow_runs` table both `/workflows/portfolio-research` and `/portfolio-research/run` already write to — no second history table. `packages/research_history` is the read-model layer on top: `view_model.py::summarize_run()` normalizes the two different persisted response shapes (`portfolio_research_workflow` vs `portfolio_research_module`) into one `RunSummary` (trace_id/portfolio/symbols/strategy_library_name/summary_text/state/timestamps). Exposed via `GET /research-runs`, filterable by `workflow_name`/`state` (SQL, indexed columns) and `portfolio_name`/`strategy_library_name`/date range (in-memory, since those live inside the JSON `request`/`response` columns).

## 9. Phase Roadmap

### Phase 1 MVP

* Universe
* Portfolio
* Strategy
* Constraint
* Backtest
* AI Report

### Phase 2

* Optimizer
* Risk Attribution
* Portfolio Comparison
* Multi Portfolio

### Phase 3

* Monte Carlo
* Stress Test
* Scenario Analysis
* Factor Attribution

### Phase 4

* Multi-Agent Workflow
* Auto Rebalance
* Auto Daily Report
* AI Investment Copilot

## 10. Design Principles

Workflow Engine must satisfy:

1. Module decoupling: every workflow can be developed and tested independently.
2. Plugin design: new strategies, agents and data sources can be added without rewriting the core engine.
3. Configurability: users can define workflow order and parameters.
4. Extensibility: multiple portfolios, markets and asset classes can be supported later.
5. Observability: every node records status, input, output, duration and errors.
6. Agent First: AI capabilities are scheduled by workflow, not coupled into UI code.

## 11. Code Location

```text
packages/workflow_layer/
├── engine.py
├── portfolio_research.py
├── stock_screening.py
└── schemas.py
```

The first reusable engine implementation is `packages/workflow_layer/engine.py`.

## 12. First Business Workflow

`PortfolioResearchWorkflow` is the first portfolio-level workflow implementation.

Code:

```text
packages/workflow_layer/portfolio_research.py
```

API:

```text
POST /workflows/portfolio-research
```

v0.1 node chain:

```text
Universe Builder
  -> Portfolio Builder
  -> Strategy Selector
  -> Constraint Config
  -> Backtest Runner
  -> AI Summary
  -> Portfolio Recommendation
```

The v0.1 AI Summary is deterministic and auditable. Later versions may replace it with Research Agent or Report Agent nodes while keeping the same Workflow Engine boundary.
