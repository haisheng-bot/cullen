from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel, Field

from packages.ai_agents.report_agent import ReportAgent
from packages.ai_agents.sec_filing_agent import SECFilingAgent
from packages.algorithm_layer.recommendation import TrendRecommendationAlgorithm
from packages.algorithm_layer.schemas import (
    AlgorithmPoint,
    FinancialFactorsInput,
    NewsSignalInput,
    RecommendationInput,
    TechnicalSeriesInput,
)
from packages.backtesting.engine import PortfolioBacktestEngine
from packages.backtesting.schemas import (
    AllocationConfig,
    EntryRules,
    ExitRules,
    RiskControls,
    StrategyConfig,
)
from packages.data_sources.market_trend import (
    MarketTrendError,
    YahooFinanceChartClient,
    normalize_symbol,
)
from packages.data_sources.fred import FREDClient, FREDError
from packages.data_sources.price_history import PriceHistoryError, YahooFinanceHistoryClient
from packages.data_sources.sec_filings import SECFilingClient, SECFilingError
from packages.data_sources.sec_financials import SECFinancialsClient, SECFinancialsError
from packages.data_sources.tiger_openapi import TigerOpenAPIClient, TigerOpenAPIError
from packages.db.backtest_runs import write_backtest_run
from packages.db.financial_facts_cache import get_or_fetch_annual_series
from packages.db.portfolios import add_symbol, ensure_default_portfolios, list_portfolios, remove_symbol
from packages.db.price_history_cache import get_or_fetch_closes
from packages.db.session import check_database_connection, session_scope
from packages.db.stock_scores import get_score_history, write_screening_result
from packages.model_layer.factory import build_default_router
from packages.model_layer.validator import OutputValidationError
from packages.news_layer.news_policy import NewsPolicyClient, NewsPolicyError
from packages.universe_layer.most_active import MostActiveUniverseScanner
from packages.workflow_layer.portfolio_research import (
    PortfolioResearchRequest,
    PortfolioResearchWorkflow,
)
from packages.workflow_layer.stock_screening import StockScreeningWorkflow


app = FastAPI(
    title="OpenStock AI API",
    version="0.1.0",
    description="AI US stock analysis and recommendation API.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

trend_client = YahooFinanceChartClient()
history_client = YahooFinanceHistoryClient()
sec_filing_client = SECFilingClient()
sec_financials_client = SECFinancialsClient(filing_client=sec_filing_client)
fred_client = FREDClient()
news_policy_client = NewsPolicyClient()
tiger_openapi_client = TigerOpenAPIClient.from_settings()
recommendation_algorithm = TrendRecommendationAlgorithm()
universe_scanner = MostActiveUniverseScanner()
model_router = build_default_router()
sec_filing_agent = SECFilingAgent(model_router)
WEB_ROOT = Path(__file__).resolve().parents[1] / "web"


def _fetch_financial_factors(symbol: str) -> FinancialFactorsInput | None:
    """Best-effort: a stock missing SEC XBRL data should not break recommendations."""
    try:
        facts = sec_financials_client.fetch_financial_facts(symbol)
    except SECFinancialsError:
        return None
    if facts.latest is None:
        return None
    return FinancialFactorsInput(
        revenue=facts.latest.revenue,
        previous_revenue=facts.previous.revenue if facts.previous else None,
        net_income=facts.latest.net_income,
        eps_diluted=facts.latest.eps_diluted,
        stockholders_equity=facts.latest.stockholders_equity,
        shares_outstanding=facts.latest.shares_outstanding,
        operating_income=facts.latest.operating_income,
        current_assets=facts.latest.current_assets,
        current_liabilities=facts.latest.current_liabilities,
        net_fixed_assets=facts.latest.net_fixed_assets,
        cash=facts.latest.cash,
        total_debt=facts.latest.total_debt,
    )


def _fetch_technical_series(symbol: str) -> TechnicalSeriesInput | None:
    """Best-effort: missing daily history falls back to the intraday-only
    technical estimate in TrendRecommendationAlgorithm rather than failing.
    """
    try:
        history = history_client.fetch_history(symbol, range_="1y", interval="1d")
    except PriceHistoryError:
        return None
    closes = [point.close for point in history.points]
    if not closes:
        return None
    return TechnicalSeriesInput(closes=closes)


def _fetch_news_signals(symbol: str) -> list[NewsSignalInput]:
    """Best-effort rule-based news sentiment inputs for algorithm-v0.3."""
    try:
        news = news_policy_client.fetch(symbol, years=3, limit=20)
    except NewsPolicyError:
        return []
    return [
        NewsSignalInput(
            title=item.title,
            summary=item.summary,
            category=item.category,
            source=item.source,
        )
        for item in news.items
    ]


screening_workflow = StockScreeningWorkflow(
    universe_scanner=universe_scanner,
    trend_client=trend_client,
    algorithm=recommendation_algorithm,
    financial_factors_fetcher=_fetch_financial_factors,
    technical_series_fetcher=_fetch_technical_series,
    news_signals_fetcher=_fetch_news_signals,
)

report_agent = ReportAgent(
    model_router,
    trend_client=trend_client,
    recommendation_algorithm=recommendation_algorithm,
    news_policy_client=news_policy_client,
    financial_factors_fetcher=_fetch_financial_factors,
    technical_series_fetcher=_fetch_technical_series,
    news_signals_fetcher=_fetch_news_signals,
)


def _fetch_cached_closes(symbol: str) -> list[tuple[str, float]]:
    with session_scope() as session:
        return get_or_fetch_closes(session, history_client, symbol, range_="10y", interval="1d")


def _fetch_shares_outstanding(symbol: str) -> float | None:
    """Best-effort, latest known share count (not point-in-time) — see
    docs/standards/PORTFOLIO_STRATEGY_STANDARD.md for why that's an
    acceptable approximation for market_cap_weighted allocation.

    Reuses the already-cached annual financials series (`get_or_fetch_annual_series`,
    24h TTL) instead of a second, uncached SEC EDGAR companyfacts fetch — the
    series already carries `shares_outstanding` per fiscal year, most recent first.
    """
    for year in _fetch_cached_annual_financials(symbol):
        if year.shares_outstanding is not None:
            return year.shares_outstanding
    return None


def _fetch_cached_annual_financials(symbol: str) -> list:
    """Best-effort: a stock missing SEC XBRL data degrades to an empty
    series (the engine then scores it with NO_DATA_SCORE neutrals), not a
    failed backtest — same convention as `_fetch_financial_factors`.
    """
    try:
        with session_scope() as session:
            return get_or_fetch_annual_series(session, sec_financials_client, symbol)
    except SECFinancialsError:
        return []


backtest_engine = PortfolioBacktestEngine(
    history_fetcher=_fetch_cached_closes,
    shares_outstanding_fetcher=_fetch_shares_outstanding,
    financials_fetcher=_fetch_cached_annual_financials,
)
portfolio_research_workflow = PortfolioResearchWorkflow(
    universe_scanner=universe_scanner,
    backtest_engine=backtest_engine,
)

POPULAR_US_STOCKS = [
    {"symbol": "AAPL", "name": "Apple Inc.", "sector": "Technology"},
    {"symbol": "MSFT", "name": "Microsoft Corporation", "sector": "Technology"},
    {"symbol": "NVDA", "name": "NVIDIA Corporation", "sector": "Semiconductors"},
    {"symbol": "TSLA", "name": "Tesla, Inc.", "sector": "Consumer Discretionary"},
    {"symbol": "AMZN", "name": "Amazon.com, Inc.", "sector": "Consumer Discretionary"},
    {"symbol": "GOOGL", "name": "Alphabet Inc.", "sector": "Communication Services"},
    {"symbol": "META", "name": "Meta Platforms, Inc.", "sector": "Communication Services"},
    {"symbol": "BRK-B", "name": "Berkshire Hathaway Inc.", "sector": "Financials"},
    {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "sector": "Financials"},
    {"symbol": "LLY", "name": "Eli Lilly and Company", "sector": "Health Care"},
]

app.mount("/static", StaticFiles(directory=WEB_ROOT), name="static")


@app.get("/")
def web_app() -> FileResponse:
    return FileResponse(WEB_ROOT / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "openstock-ai-api"}


@app.get("/health/db")
def health_db() -> dict[str, str]:
    return {"status": "ok" if check_database_connection() else "unavailable"}


@app.get("/integrations/tiger/status")
def get_tiger_openapi_status() -> dict:
    return tiger_openapi_client.status().to_dict()


@app.get("/stocks/popular")
def get_popular_us_stocks() -> dict:
    return {
        "market": "US",
        "items": POPULAR_US_STOCKS,
        "risk_disclaimer": "本系统仅用于投资研究辅助，不构成任何投资建议。",
    }


@app.get("/stocks/search")
def search_us_stocks(q: str = Query("", max_length=32)) -> dict:
    keyword = q.strip().upper()
    items = [
        item
        for item in POPULAR_US_STOCKS
        if not keyword
        or keyword in item["symbol"]
        or keyword in item["name"].upper()
        or keyword in item["sector"].upper()
    ]
    return {
        "market": "US",
        "query": q,
        "items": items,
        "risk_disclaimer": "本系统仅用于投资研究辅助，不构成任何投资建议。",
    }


@app.get("/stocks/universe/most-active")
def get_most_active_universe(limit: int = Query(100, ge=1, le=100)) -> dict:
    return universe_scanner.scan(limit=limit).to_dict()


@app.get("/stocks/{symbol}/quote")
def get_stock_quote(symbol: str) -> dict:
    try:
        normalized_symbol = normalize_symbol(symbol)
        trend = trend_client.fetch_trend(normalized_symbol, range_="1d", interval="1m")
        return trend.to_quote_dict()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except MarketTrendError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/stocks/{symbol}/tiger/quote")
def get_tiger_stock_quote(symbol: str) -> dict:
    try:
        normalized_symbol = normalize_symbol(symbol)
        return tiger_openapi_client.fetch_quote(normalized_symbol).to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except TigerOpenAPIError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/stocks/{symbol}/tiger/history")
def get_tiger_stock_history(
    symbol: str,
    years: int = Query(3, ge=1, le=3),
    period: str = Query("day"),
) -> dict:
    try:
        normalized_symbol = normalize_symbol(symbol)
        return tiger_openapi_client.fetch_kline(
            normalized_symbol, period=period, years=years
        ).to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except TigerOpenAPIError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/stocks/{symbol}/recommendation")
def get_stock_recommendation(symbol: str) -> dict:
    try:
        normalized_symbol = normalize_symbol(symbol)
        trend = trend_client.fetch_trend(normalized_symbol, range_="1d", interval="1m")
        algorithm_input = RecommendationInput(
            symbol=trend.symbol,
            latest_price=trend.regular_market_price or trend.latest_price,
            previous_close=trend.previous_close,
            points=[
                AlgorithmPoint(timestamp=point.timestamp, close=point.close, volume=point.volume)
                for point in trend.points
            ],
            source=trend.source,
            analysis_time=trend.analysis_time,
            financial_factors=_fetch_financial_factors(normalized_symbol),
            technical_series=_fetch_technical_series(normalized_symbol),
            news_signals=_fetch_news_signals(normalized_symbol),
        )
        return recommendation_algorithm.recommend(algorithm_input).to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except MarketTrendError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


def _persist_screening_result(result) -> None:
    with session_scope() as session:
        write_screening_result(session, result)


@app.get("/stocks/screening")
def get_stock_screening(limit: int = Query(20, ge=1, le=50)) -> dict:
    result = screening_workflow.screen(limit=limit)
    _persist_screening_result(result)
    return result.to_dict()


def _fetch_score_history(symbol: str, limit: int) -> list[dict]:
    with session_scope() as session:
        history = get_score_history(session, symbol, limit=limit)
        return [
            {
                "screened_at": record.screened_at.isoformat(),
                "rank": record.rank,
                "total_score": record.total_score,
                "recommendation": record.recommendation,
                "factors": record.factors,
                "reasons": record.reasons,
                "risks": record.risks,
                "algorithm_version": record.algorithm_version,
            }
            for record in history
        ]


@app.get("/stocks/{symbol}/score-history")
def get_stock_score_history(symbol: str, limit: int = Query(30, ge=1, le=200)) -> dict:
    try:
        normalized_symbol = normalize_symbol(symbol)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "symbol": normalized_symbol,
        "items": _fetch_score_history(normalized_symbol, limit),
        "risk_disclaimer": "本系统仅用于投资研究辅助，不构成任何投资建议。",
    }


class PortfolioSymbolRequest(BaseModel):
    symbol: str


def _portfolio_to_dict(portfolio) -> dict:
    return {
        "name": portfolio.name,
        "symbols": portfolio.symbols,
        "updated_at": portfolio.updated_at.isoformat() if portfolio.updated_at else None,
    }


def _list_portfolios() -> list[dict]:
    with session_scope() as session:
        ensure_default_portfolios(session)
        return [_portfolio_to_dict(portfolio) for portfolio in list_portfolios(session)]


def _add_portfolio_symbol(name: str, symbol: str) -> dict:
    with session_scope() as session:
        portfolio = add_symbol(session, name, symbol)
        return _portfolio_to_dict(portfolio)


def _remove_portfolio_symbol(name: str, symbol: str) -> dict | None:
    with session_scope() as session:
        portfolio = remove_symbol(session, name, symbol)
        return _portfolio_to_dict(portfolio) if portfolio else None


@app.get("/portfolios")
def get_portfolios() -> dict:
    """Named watchlists used by the workbench's Portfolio Strategy panel,
    persisted so they survive page reloads instead of resetting to defaults.
    """
    return {"items": _list_portfolios()}


@app.post("/portfolios/{name}/symbols")
def add_portfolio_symbol(name: str, request: PortfolioSymbolRequest) -> dict:
    try:
        normalized_symbol = normalize_symbol(request.symbol)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _add_portfolio_symbol(name, normalized_symbol)


@app.delete("/portfolios/{name}/symbols/{symbol}")
def remove_portfolio_symbol(name: str, symbol: str) -> dict:
    try:
        normalized_symbol = normalize_symbol(symbol)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    result = _remove_portfolio_symbol(name, normalized_symbol)
    if result is None:
        raise HTTPException(status_code=404, detail=f"portfolio not found: {name}")
    return result


@app.get("/stocks/{symbol}/trend")
def get_stock_trend(
    symbol: str,
    range_: str = Query("1d", alias="range"),
    interval: str = "1m",
) -> dict:
    try:
        normalized_symbol = normalize_symbol(symbol)
        return trend_client.fetch_trend(normalized_symbol, range_=range_, interval=interval).to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except MarketTrendError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/stocks/{symbol}/history")
def get_stock_price_history(
    symbol: str,
    range_: str = Query("10y", alias="range"),
    interval: str = "1d",
) -> dict:
    try:
        normalized_symbol = normalize_symbol(symbol)
        return history_client.fetch_history(
            normalized_symbol, range_=range_, interval=interval
        ).to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PriceHistoryError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/stocks/{symbol}/filings")
def get_stock_sec_filings(
    symbol: str,
    forms: str = Query("10-K,10-Q,8-K"),
    limit: int = Query(10, ge=1, le=50),
) -> dict:
    try:
        normalized_symbol = normalize_symbol(symbol)
        form_types = tuple(form.strip() for form in forms.split(",") if form.strip())
        return sec_filing_client.list_filings(
            normalized_symbol, forms=form_types, limit=limit
        ).to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except SECFilingError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/stocks/{symbol}/sec-summary")
def get_stock_sec_summary(symbol: str) -> dict:
    try:
        return sec_filing_agent.run(symbol).to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (SECFilingError, OutputValidationError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/stocks/{symbol}/report")
def get_stock_report(symbol: str) -> dict:
    try:
        return report_agent.run(symbol).to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (MarketTrendError, NewsPolicyError, OutputValidationError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/stocks/{symbol}/news")
def get_stock_news_policy(
    symbol: str,
    years: int = Query(3, ge=1, le=3),
    limit: int = Query(30, ge=1, le=100),
) -> dict:
    try:
        normalized_symbol = normalize_symbol(symbol)
        return news_policy_client.fetch(normalized_symbol, years=years, limit=limit).to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except NewsPolicyError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/macro/{series_id}/observations")
def get_fred_observations(
    series_id: str,
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
) -> dict:
    try:
        return fred_client.fetch_observations(
            series_id, start_date=start_date, end_date=end_date, limit=limit
        ).to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FREDError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


class AllocationConfigRequest(BaseModel):
    method: str = "equal_weight"
    max_position_weight: float = 0.25
    min_cash_weight: float = 0.10


class EntryRulesRequest(BaseModel):
    min_technical_score: int = 60
    min_momentum_percent: float | None = None
    require_ma_cross: str | None = None
    min_ai_score: int | None = None


class ExitRulesRequest(BaseModel):
    max_technical_score: int = 40
    stop_loss_percent: float | None = 0.08
    require_ma_cross: str | None = None
    max_ai_score: int | None = None


class RiskControlsRequest(BaseModel):
    max_portfolio_drawdown: float | None = 0.12
    max_sector_exposure: float | None = None


class BacktestRunRequest(BaseModel):
    """Request body for POST /backtests/run. Mirrors
    packages.backtesting.schemas.StrategyConfig field-for-field; the engine
    itself stays a plain dataclass, framework-free like every other layer.
    """

    strategy_name: str
    symbols: list[str]
    start_date: str
    end_date: str
    initial_cash: float = 10_000.0
    rebalance_frequency: str = "monthly"
    benchmark_symbol: str = "SPY"
    signal_mode: str = "technical"
    allocation: AllocationConfigRequest = Field(default_factory=AllocationConfigRequest)
    entry_rules: EntryRulesRequest = Field(default_factory=EntryRulesRequest)
    exit_rules: ExitRulesRequest = Field(default_factory=ExitRulesRequest)
    risk: RiskControlsRequest = Field(default_factory=RiskControlsRequest)
    sector_map: dict[str, str] = Field(default_factory=dict)


class PortfolioResearchWorkflowRequest(BaseModel):
    portfolio_name: str = "Workflow Portfolio"
    universe_limit: int = Field(default=100, ge=1, le=100)
    selected_symbols: list[str] | None = None
    backtest: BacktestRunRequest


def _to_strategy_config(request: BacktestRunRequest) -> StrategyConfig:
    return StrategyConfig(
        strategy_name=request.strategy_name,
        symbols=[symbol.upper() for symbol in request.symbols],
        start_date=request.start_date,
        end_date=request.end_date,
        initial_cash=request.initial_cash,
        rebalance_frequency=request.rebalance_frequency,
        benchmark_symbol=request.benchmark_symbol.upper(),
        signal_mode=request.signal_mode,
        allocation=AllocationConfig(**request.allocation.model_dump()),
        entry_rules=EntryRules(**request.entry_rules.model_dump()),
        exit_rules=ExitRules(**request.exit_rules.model_dump()),
        risk=RiskControls(**request.risk.model_dump()),
        sector_map=request.sector_map,
    )


def _persist_backtest_run(config: StrategyConfig, result) -> None:
    with session_scope() as session:
        write_backtest_run(session, config, result)


def _portfolio_research_response(run_result) -> dict:
    payload = run_result.payload
    strategy_config = payload.get("final_strategy_config")
    backtest_result = payload.get("backtest_result")
    return {
        "workflow_name": run_result.workflow_name,
        "workflow_version": run_result.workflow_version,
        "trace_id": run_result.trace_id,
        "state": run_result.state.value,
        "started_at": run_result.started_at,
        "completed_at": run_result.completed_at,
        "node_results": [node.to_dict() for node in run_result.node_results],
        "universe": payload.get("universe"),
        "portfolio": payload.get("portfolio"),
        "strategy": payload.get("strategy"),
        "constraints": payload.get("constraints"),
        "backtest": backtest_result.to_dict() if backtest_result else payload.get("backtest"),
        "ai_summary": payload.get("ai_summary"),
        "portfolio_recommendation": payload.get("portfolio_recommendation"),
        "strategy_config": strategy_config.to_dict() if strategy_config else None,
        "risk_disclaimer": run_result.risk_disclaimer,
    }


@app.post("/backtests/run")
def run_backtest(request: BacktestRunRequest) -> dict:
    config = _to_strategy_config(request)
    try:
        result = backtest_engine.run(config)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PriceHistoryError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    _persist_backtest_run(config, result)
    return result.to_dict()


@app.post("/workflows/portfolio-research")
def run_portfolio_research_workflow(request: PortfolioResearchWorkflowRequest) -> dict:
    config = _to_strategy_config(request.backtest)
    workflow_request = PortfolioResearchRequest(
        strategy_config=config,
        universe_limit=request.universe_limit,
        portfolio_name=request.portfolio_name,
        selected_symbols=request.selected_symbols,
    )
    try:
        result = portfolio_research_workflow.run(workflow_request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PriceHistoryError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    final_config = result.payload.get("final_strategy_config")
    backtest_result = result.payload.get("backtest_result")
    if final_config is not None and backtest_result is not None:
        _persist_backtest_run(final_config, backtest_result)
    return _portfolio_research_response(result)
