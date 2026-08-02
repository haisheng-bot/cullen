# OpenStock AI Job Queue 标准 v0.1

## 1. 定位

Job Queue 位于 `packages/job_queue`，为耗时较长的操作（候选池 screening、Portfolio Research Workflow）提供异步提交/轮询入口，避免长任务阻塞 HTTP worker。是同步接口（`/stocks/screening`、`/workflows/portfolio-research`）之外新增的并行入口，不替换、不修改同步接口行为。

本系统仅用于投资研究辅助，不构成任何投资建议。

## 2. 目录规范

```text
packages/job_queue/
├── __init__.py
├── engine.py     # JobQueueEngine（APScheduler BackgroundScheduler 封装）+ 后台执行函数
└── schemas.py    # JobSubmissionResponse / JobDetailResponse / JobListResponse

packages/db/job_queue.py   # JobRecord CRUD（session 参数化，与 packages/db/workflow_runs.py 等其余持久化模块写法一致）
```

`JobRecord` 模型定义在 `packages/db/models.py`（与其余表一致，不在 `packages/db/job_queue.py` 里定义后反向 import）。

## 3. 执行机制

* `JobQueueEngine`（`packages/job_queue/engine.py`）内部持有一个 `apscheduler.schedulers.background.BackgroundScheduler`，懒启动（首次访问 `.scheduler` 属性时才 `start()`），避免 import 该模块就产生后台线程，方便测试。
* `submit_screening()`/`submit_portfolio_research()` 先同步写入一条 `pending` 的 `JobRecord`（拿到 `job_id` 立即返回给调用方），再把实际执行 `_run_screening()`/`_run_portfolio_research()` 交给 scheduler 异步跑。
* 后台函数流程：`update_job_status(..., "running")` → 执行 `workflow.screen(...)`/`workflow.run(...)` → 成功则持久化结果并 `update_job_status(..., "completed", result=...)`；抛异常则 `update_job_status(..., "failed", error_message=str(exc))`。
* Portfolio Research 任务复用 `packages/workflow_layer/portfolio_research.py::build_response()` 构造响应体——与同步端点 `/workflows/portfolio-research` 共用同一个函数，保证两条路径产出结构完全一致；同时复用 `packages/db/backtest_runs.py::write_backtest_run()` 和 `packages/db/workflow_runs.py::write_workflow_run()` 落库，`job_id` 即 `workflow_runs.trace_id`，可用 `GET /workflows/portfolio-research/{trace_id}` 或 `GET /research-runs` 复盘。
* Screening 任务复用 `packages/db/stock_scores.py::write_screening_result()`，持久化路径与同步端点 `/stocks/screening` 完全一致。

## 4. API

```text
POST /jobs/screening?limit=20&scoring_profile=balanced
POST /jobs/portfolio-research
GET /jobs/{job_id}
GET /jobs?job_type=&status=&limit=20&offset=0
```

* `POST /jobs/screening`：`scoring_profile` 未知返回 400（提交阶段同步校验，复用 `get_profile()`）。
* `POST /jobs/portfolio-research`：请求体与 `POST /workflows/portfolio-research` 相同（`PortfolioResearchWorkflowRequest`）。
* `GET /jobs/{job_id}`：未找到返回 404。
* `GET /jobs`：`job_type`/`status` 过滤，SQL 层 `limit`/`offset` 分页，`total_count` 由独立的 `count_jobs()` 查询给出（不是页内条数）。

详细请求/响应示例见 `docs/api/api-design-v0.1.md` §4.12。

## 5. 状态机

```text
pending -> running -> completed
                    -> failed
         -> cancelled（预留，v0.1 无取消接口）
```

`started_at` 在首次转入 `running` 时写入；`completed_at` 在转入任一终态（`completed`/`failed`/`cancelled`）时写入。

## 6. 边界（v0.1 不做）

* 无鉴权
* 无取消接口（`cancelled` 状态值已预留，但没有能把任务改成这个状态的入口）
* 无重试和超时策略——一次执行失败即终态 `failed`，不自动重试
* 无更细粒度的进度上报（`progress_percent` 目前只有 0/100 两档，`increment_job_progress()` 已提供但未被调用）
* 仅覆盖 `screening`、`portfolio_research` 两种 `job_type`；新增任务类型需要新增对应的 `submit_*`/`_run_*` 函数对

## 7. 测试

```text
tests/test_db.py::JobQueuePersistenceTest        # JobRecord CRUD，隔离内存 sqlite
tests/test_job_queue.py                          # 后台执行函数（成功/失败路径）+ 一次真实 BackgroundScheduler 提交-轮询集成测试
tests/test_api_endpoints.py（ApiEndpointsTest）   # /jobs/* 端点，复用既有 Fake screening/portfolio-research workflow
```

## 8. 版本管理

```text
job-queue-v0.1   APScheduler 后台执行 + POST/GET /jobs/*，覆盖 screening 和 portfolio-research [usable]
```
