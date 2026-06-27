# Project Rules

## Purpose

OpenStock AI is an AI investment research platform for US stock research, portfolio analysis, backtesting, AI explanations, and report generation.

The system is research assistance only. It must not present outputs as investment advice.

Required disclaimer for investment-related outputs:

```text
本系统仅用于投资研究辅助，不构成任何投资建议。
```

## Source Of Truth

Before changing behavior, read:

* `README.md`
* `docs/product/PROJECT_PLAN_PROGRESS.md`
* `docs/product/IMPLEMENTATION_GAP_ANALYSIS.md`
* `docs/architecture/system-design.md`
* Related standard under `docs/standards/`

Use `docs/product/PROJECT_PLAN_PROGRESS.md` as the current progress source when documents disagree.

## Architecture Boundaries

Respect the existing layers:

```text
Application Layer
Agent Layer
Workflow Layer
Universe Layer
Algorithm Layer
Model Layer
News / Policy Layer
Data Layer
Database Layer
```

Rules:

* API code belongs in `apps/api`.
* Web UI belongs in `apps/web`.
* Data source code belongs in `packages/data_sources`.
* AI agent code belongs in `packages/ai_agents`.
* Workflow orchestration belongs in `packages/workflow_layer`.
* Recommendation and factor logic belongs in `packages/algorithm_layer`.
* Model provider calls belong only in `packages/model_layer`.
* Database persistence belongs in `packages/db`.

## Change Policy

* Keep every change small and traceable.
* Do not introduce trading automation.
* Do not bypass official APIs for broker or market data.
* Do not add speculative architecture.
* Update docs and tests with behavior changes.
