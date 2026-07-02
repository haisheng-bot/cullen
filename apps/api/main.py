from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from datetime import date
from pydantic import BaseModel, Field
from sqlalchemy import select

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
    REBALANCE_FREQUENCIES,
    RiskControls,
    SIGNAL_MODES,
    StrategyConfig,
)
from packages.data_sources.market_trend import (
    MarketTrendError,
    YahooFinanceChartClient,
    normalize_symbol,
)
from packages.data_sources.fred import FREDClient, FREDError
from packages.data_sources.health import build_data_source_health
from packages.data_sources.price_history import PriceHistoryError, YahooFinanceHistoryClient
from packages.data_sources.quality import attach_data_quality
from packages.data_sources.sec_filings import SECFilingClient, SECFilingError
from packages.data_sources.sec_financials import SECFinancialsClient, SECFinancialsError
from packages.data_sources.tiger_openapi import TigerOpenAPIClient, TigerOpenAPIError
from packages.db.backtest_runs import write_backtest_run
from packages.db.financial_facts_cache import get_or_fetch_annual_series
from packages.db.models import Portfolio
from packages.db.portfolios import (
    add_symbol,
    ensure_default_portfolios,
    get_portfolio_config,
    list_portfolios,
    remove_symbol,
    save_portfolio_config,
)
from packages.db.price_history_cache import get_or_fetch_closes
from packages.db.report_archives import get_report_archive, list_report_archives, save_report_archive
from packages.db.session import check_database_connection, session_scope
from packages.db.stock_scores import get_score_history, write_screening_result
from packages.db.strategies import delete_strategy, get_strategy, list_strategies, save_strategy
from packages.db.workflow_runs import get_workflow_run_by_trace_id, list_workflow_runs, write_workflow_run
from packages.model_layer.factory import build_default_router
from packages.model_layer.validator import OutputValidationError
from packages.news_layer.news_policy import NewsPolicyClient, NewsPolicyError
from packages.portfolio_optimizer.engine import optimize_portfolio
from packages.portfolio_optimizer.schemas import OPTIMIZER_METHODS
from packages.portfolio_research.archive import get_portfolio_research_run, write_portfolio_research_run
from packages.portfolio_research.engine import PortfolioResearchEngine
from packages.portfolio_research.reports import build_report_from_run, report_detail, report_summary
from packages.portfolio_research.schemas import (
    PortfolioResearchRunRequest as PortfolioResearchModuleRequest,
    ResearchConstraints,
    StrategyPreferences,
)
from packages.research_history.schemas import RunHistoryResult
from packages.research_history.view_model import summarize_run
from packages.risk_engine.engine import analyze_portfolio_risk
from packages.scoring_profiles.profiles import get_profile
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


@app.get("/data-sources/health")
def get_data_sources_health() -> dict:
    return build_data_source_health(tiger_status=tiger_openapi_client.status().to_dict())


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
        return attach_data_quality(
            trend.to_quote_dict(),
            fallback="Use Yahoo chart latest point when regular market price is unavailable.",
            required_fields=("price", "source", "analysis_time"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except MarketTrendError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/stocks/{symbol}/tiger/quote")
def get_tiger_stock_quote(symbol: str) -> dict:
    try:
        normalized_symbol = normalize_symbol(symbol)
        return attach_data_quality(
            tiger_openapi_client.fetch_quote(normalized_symbol).to_dict(),
            fallback="Use Yahoo market data when Tiger OpenAPI is not configured or unavailable.",
            required_fields=("price", "source", "analysis_time"),
        )
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
        return attach_data_quality(
            tiger_openapi_client.fetch_kline(normalized_symbol, period=period, years=years).to_dict(),
            fallback="Use Yahoo history when Tiger OpenAPI is not configured or unavailable.",
            required_fields=("points", "source", "analysis_time"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except TigerOpenAPIError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/stocks/{symbol}/recommendation")
def get_stock_recommendation(symbol: str, scoring_profile: str = "balanced") -> dict:
    try:
        normalized_symbol = normalize_symbol(symbol)
        profile = get_profile(scoring_profile)
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
        return recommendation_algorithm.recommend(algorithm_input, profile=profile).to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except MarketTrendError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


def _persist_screening_result(result) -> None:
    with session_scope() as session:
        write_screening_result(session, result)


@app.get("/stocks/screening")
def get_stock_screening(
    limit: int = Query(20, ge=1, le=50), scoring_profile: str = "balanced"
) -> dict:
    try:
        profile = get_profile(scoring_profile)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    result = screening_workflow.screen(limit=limit, profile=profile)
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


class PortfolioConfigRequest(BaseModel):
    target_weights: dict[str, float] = Field(default_factory=dict)
    cash_weight: float = Field(default=0.0, ge=0.0, le=1.0)


def _portfolio_config_to_dict(config) -> dict:
    if config is None:
        return {"target_weights": {}, "cash_weight": 0.0, "updated_at": None}
    return {
        "target_weights": config.target_weights,
        "cash_weight": config.cash_weight,
        "updated_at": config.updated_at.isoformat() if config.updated_at else None,
    }


def _portfolio_to_dict(portfolio, config=None) -> dict:
    return {
        "name": portfolio.name,
        "symbols": portfolio.symbols,
        "config": _portfolio_config_to_dict(config),
        "updated_at": portfolio.updated_at.isoformat() if portfolio.updated_at else None,
    }


def _list_portfolios() -> list[dict]:
    with session_scope() as session:
        ensure_default_portfolios(session)
        return [
            _portfolio_to_dict(portfolio, get_portfolio_config(session, portfolio.name))
            for portfolio in list_portfolios(session)
        ]


def _add_portfolio_symbol(name: str, symbol: str) -> dict:
    with session_scope() as session:
        portfolio = add_symbol(session, name, symbol)
        return _portfolio_to_dict(portfolio, get_portfolio_config(session, name))


def _remove_portfolio_symbol(name: str, symbol: str) -> dict | None:
    with session_scope() as session:
        portfolio = remove_symbol(session, name, symbol)
        return _portfolio_to_dict(portfolio, get_portfolio_config(session, name)) if portfolio else None


def _save_portfolio_config(name: str, request: PortfolioConfigRequest) -> dict:
    normalized_weights: dict[str, float] = {}
    for symbol, weight in request.target_weights.items():
        normalized_symbol = normalize_symbol(symbol)
        if weight < 0 or weight > 1:
            raise ValueError(f"target weight must be between 0 and 1: {normalized_symbol}")
        normalized_weights[normalized_symbol] = weight
    if sum(normalized_weights.values()) + request.cash_weight > 1.0001:
        raise ValueError("target weights plus cash_weight must be <= 1")

    with session_scope() as session:
        portfolio = session.scalar(select(Portfolio).where(Portfolio.name == name))
        if portfolio is None:
            portfolio = Portfolio(name=name, symbols=sorted(normalized_weights))
            session.add(portfolio)
        config = save_portfolio_config(
            session,
            name,
            normalized_weights,
            request.cash_weight,
        )
        return _portfolio_to_dict(portfolio, config)


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


@app.put("/portfolios/{name}/config")
def update_portfolio_config(name: str, request: PortfolioConfigRequest) -> dict:
    try:
        return _save_portfolio_config(name, request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


class StrategyRequest(BaseModel):
    preferences: dict = Field(default_factory=dict)
    constraints: dict = Field(default_factory=dict)


def _strategy_to_dict(strategy) -> dict:
    return {
        "name": strategy.name,
        "preferences": strategy.preferences,
        "constraints": strategy.constraints,
        "updated_at": strategy.updated_at.isoformat() if strategy.updated_at else None,
    }


def _list_strategies() -> list[dict]:
    with session_scope() as session:
        return [_strategy_to_dict(strategy) for strategy in list_strategies(session)]


def _save_strategy(name: str, request: StrategyRequest) -> dict:
    optimizer_method = request.preferences.get("optimizer_method")
    if optimizer_method is not None and optimizer_method not in OPTIMIZER_METHODS:
        raise ValueError(f"unknown optimizer_method: {optimizer_method}")
    backtest_mode = request.preferences.get("backtest_mode")
    if backtest_mode is not None and backtest_mode not in SIGNAL_MODES:
        raise ValueError(f"unknown backtest_mode: {backtest_mode}")
    rebalance_frequency = request.preferences.get("rebalance_frequency")
    if rebalance_frequency is not None and rebalance_frequency not in REBALANCE_FREQUENCIES:
        raise ValueError(f"unknown rebalance_frequency: {rebalance_frequency}")

    with session_scope() as session:
        strategy = save_strategy(session, name, request.preferences, request.constraints)
        return _strategy_to_dict(strategy)


def _delete_strategy(name: str) -> bool:
    with session_scope() as session:
        return delete_strategy(session, name)


@app.get("/strategies")
def get_strategies() -> dict:
    """Named, reusable strategy presets for the Portfolio Research
    Workbench's Strategy Library panel. Decoupled from Portfolio: any saved
    strategy can be applied to any portfolio's symbols at run time.
    """
    return {"items": _list_strategies()}


@app.put("/strategies/{name}")
def update_strategy(name: str, request: StrategyRequest) -> dict:
    try:
        return _save_strategy(name, request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/strategies/{name}")
def remove_strategy(name: str) -> dict:
    if not _delete_strategy(name):
        raise HTTPException(status_code=404, detail=f"strategy not found: {name}")
    return {"deleted": name}


@app.get("/stocks/{symbol}/trend")
def get_stock_trend(
    symbol: str,
    range_: str = Query("1d", alias="range"),
    interval: str = "1m",
) -> dict:
    try:
        normalized_symbol = normalize_symbol(symbol)
        return attach_data_quality(
            trend_client.fetch_trend(normalized_symbol, range_=range_, interval=interval).to_dict(),
            fallback="No fallback inside trend endpoint; caller should show source error.",
            required_fields=("points", "source", "analysis_time"),
        )
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
        return attach_data_quality(
            history_client.fetch_history(normalized_symbol, range_=range_, interval=interval).to_dict(),
            fallback="Use cached price history where available; otherwise show source error.",
            required_fields=("points", "source", "analysis_time"),
        )
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
        return attach_data_quality(
            sec_filing_client.list_filings(normalized_symbol, forms=form_types, limit=limit).to_dict(),
            fallback="SEC filings may be empty for symbols without a mapped CIK.",
            required_fields=("filings", "source", "analysis_time"),
        )
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
        return attach_data_quality(
            news_policy_client.fetch(normalized_symbol, years=years, limit=limit).to_dict(),
            fallback="News panel keeps SEC disclosure coverage when Yahoo RSS has no recent items.",
            required_fields=("items", "sources", "generated_at"),
        )
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
        return attach_data_quality(
            fred_client.fetch_observations(series_id, start_date=start_date, end_date=end_date, limit=limit).to_dict(),
            fallback="Macro data is unavailable until FRED_API_KEY is configured.",
            required_fields=("observations", "source", "analysis_time"),
        )
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


class PortfolioRiskRequest(BaseModel):
    symbols: list[str]
    weights: dict[str, float] = Field(default_factory=dict)
    benchmark_symbol: str = "SPY"
    sector_map: dict[str, str] = Field(default_factory=dict)


class PortfolioOptimizerRequest(BaseModel):
    symbols: list[str]
    method: str = "minimum_variance"
    max_position_weight: float = Field(default=0.25, ge=0.0, le=1.0)
    min_cash_weight: float = Field(default=0.10, ge=0.0, le=1.0)


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
    scoring_profile: str = "balanced"
    allocation: AllocationConfigRequest = Field(default_factory=AllocationConfigRequest)
    entry_rules: EntryRulesRequest = Field(default_factory=EntryRulesRequest)
    exit_rules: ExitRulesRequest = Field(default_factory=ExitRulesRequest)
    risk: RiskControlsRequest = Field(default_factory=RiskControlsRequest)
    sector_map: dict[str, str] = Field(default_factory=dict)


class PortfolioResearchWorkflowRequest(BaseModel):
    portfolio_name: str = "Workflow Portfolio"
    strategy_library_name: str | None = None
    universe_limit: int = Field(default=100, ge=1, le=100)
    selected_symbols: list[str] | None = None
    backtest: BacktestRunRequest


class PortfolioResearchConstraintsRequest(BaseModel):
    max_position_weight: float = Field(default=0.35, ge=0.0, le=1.0)
    min_cash_weight: float = Field(default=0.10, ge=0.0, le=1.0)
    max_drawdown: float = Field(default=0.20, ge=0.0, le=1.0)
    benchmark_symbol: str = "SPY"
    backtest_years: int = Field(default=3, ge=1, le=10)


class PortfolioResearchStrategyPreferencesRequest(BaseModel):
    scoring_mode: str = "algorithm_v0.3"
    scoring_profile: str = "balanced"
    backtest_mode: str = "ai_score"
    optimizer_method: str = "minimum_variance"
    rebalance_frequency: str = "monthly"


class PortfolioResearchRunRequest(BaseModel):
    portfolio_name: str = "Portfolio Research"
    symbols: list[str]
    research_goal: str = "balanced_growth"
    strategy_library_name: str | None = None
    constraints: PortfolioResearchConstraintsRequest = Field(default_factory=PortfolioResearchConstraintsRequest)
    strategy_preferences: PortfolioResearchStrategyPreferencesRequest = Field(
        default_factory=PortfolioResearchStrategyPreferencesRequest
    )


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
        scoring_profile=request.scoring_profile,
        allocation=AllocationConfig(**request.allocation.model_dump()),
        entry_rules=EntryRules(**request.entry_rules.model_dump()),
        exit_rules=ExitRules(**request.exit_rules.model_dump()),
        risk=RiskControls(**request.risk.model_dump()),
        sector_map=request.sector_map,
    )


def _to_module_request(request: PortfolioResearchRunRequest) -> PortfolioResearchModuleRequest:
    return PortfolioResearchModuleRequest(
        portfolio_name=request.portfolio_name,
        symbols=[normalize_symbol(symbol) for symbol in request.symbols],
        research_goal=request.research_goal,
        strategy_library_name=request.strategy_library_name,
        constraints=ResearchConstraints(**request.constraints.model_dump()),
        strategy_preferences=StrategyPreferences(**request.strategy_preferences.model_dump()),
    )


def _years_ago_date(years: int) -> str:
    today = date.today()
    try:
        return today.replace(year=today.year - years).isoformat()
    except ValueError:
        return today.replace(year=today.year - years, day=28).isoformat()


def _persist_backtest_run(config: StrategyConfig, result) -> None:
    with session_scope() as session:
        write_backtest_run(session, config, result)


def _persist_workflow_run(request: PortfolioResearchWorkflowRequest, response: dict) -> None:
    with session_scope() as session:
        write_workflow_run(session, request.model_dump(), response)


def _fetch_workflow_run(trace_id: str) -> dict | None:
    with session_scope() as session:
        record = get_workflow_run_by_trace_id(session, trace_id)
        return record.response if record else None


def _archive_portfolio_research_run(request: PortfolioResearchModuleRequest, response: dict) -> None:
    with session_scope() as session:
        write_portfolio_research_run(session, request, response)


def _fetch_portfolio_research_run(trace_id: str) -> dict | None:
    with session_scope() as session:
        return get_portfolio_research_run(session, trace_id)


def _save_report_for_trace_id(trace_id: str) -> dict:
    run = _fetch_portfolio_research_run(trace_id)
    if run is None:
        raise HTTPException(status_code=404, detail="portfolio research run not found")
    report = build_report_from_run(run)
    with session_scope() as session:
        record = save_report_archive(session, **report.to_dict())
        return report_detail(record)


def _list_reports(*, limit: int, offset: int, portfolio_name: str | None) -> dict:
    with session_scope() as session:
        reports = [report_summary(record) for record in list_report_archives(session, portfolio_name=portfolio_name)]
    total_count = len(reports)
    return {
        "items": reports[offset : offset + limit],
        "total_count": total_count,
        "limit": limit,
        "offset": offset,
        "risk_disclaimer": "本系统仅用于投资研究辅助，不构成任何投资建议。",
    }


def _get_report(trace_id: str) -> dict | None:
    with session_scope() as session:
        record = get_report_archive(session, trace_id)
        return report_detail(record) if record else None


def _portfolio_risk_response(request: PortfolioRiskRequest) -> dict:
    symbols = [normalize_symbol(symbol) for symbol in request.symbols]
    weights = {normalize_symbol(symbol): weight for symbol, weight in request.weights.items()}
    benchmark_symbol = normalize_symbol(request.benchmark_symbol)
    closes_by_symbol = {symbol: _fetch_cached_closes(symbol) for symbol in symbols}
    benchmark_closes = _fetch_cached_closes(benchmark_symbol)
    report = analyze_portfolio_risk(
        closes_by_symbol,
        weights=weights,
        benchmark_closes=benchmark_closes,
        sector_map={normalize_symbol(symbol): sector for symbol, sector in request.sector_map.items()},
    )
    return report.to_dict()


def _portfolio_optimizer_response(request: PortfolioOptimizerRequest) -> dict:
    symbols = [normalize_symbol(symbol) for symbol in request.symbols]
    closes_by_symbol = {symbol: _fetch_cached_closes(symbol) for symbol in symbols}
    market_caps = {
        symbol: (closes[-1][1] * shares if (shares := _fetch_shares_outstanding(symbol)) else None)
        for symbol, closes in closes_by_symbol.items()
        if closes
    }
    result = optimize_portfolio(
        method=request.method,
        closes_by_symbol=closes_by_symbol,
        market_caps=market_caps,
        max_position_weight=request.max_position_weight,
        min_cash_weight=request.min_cash_weight,
    )
    return result.to_dict()


def _module_workflow_response(request: PortfolioResearchModuleRequest) -> dict:
    constraints = request.constraints
    preferences = request.strategy_preferences
    backtest_request = BacktestRunRequest(
        strategy_name=f"{request.portfolio_name} · Portfolio Research",
        symbols=request.symbols,
        start_date=_years_ago_date(constraints.backtest_years),
        end_date=date.today().isoformat(),
        rebalance_frequency=preferences.rebalance_frequency,
        benchmark_symbol=constraints.benchmark_symbol,
        signal_mode="ai_score" if preferences.backtest_mode == "ai_score" else "technical",
        scoring_profile=preferences.scoring_profile,
        allocation=AllocationConfigRequest(
            method="equal_weight",
            max_position_weight=constraints.max_position_weight,
            min_cash_weight=constraints.min_cash_weight,
        ),
        entry_rules=EntryRulesRequest(min_technical_score=50, min_ai_score=55),
        exit_rules=ExitRulesRequest(max_technical_score=40, max_ai_score=35),
        risk=RiskControlsRequest(max_portfolio_drawdown=constraints.max_drawdown),
    )
    workflow_request = PortfolioResearchWorkflowRequest(
        portfolio_name=request.portfolio_name,
        strategy_library_name=request.strategy_library_name,
        universe_limit=100,
        selected_symbols=request.symbols,
        backtest=backtest_request,
    )
    config = _to_strategy_config(workflow_request.backtest)
    run_request = PortfolioResearchRequest(
        strategy_config=config,
        universe_limit=workflow_request.universe_limit,
        portfolio_name=workflow_request.portfolio_name,
        selected_symbols=workflow_request.selected_symbols,
    )
    result = portfolio_research_workflow.run(run_request)
    final_config = result.payload.get("final_strategy_config")
    backtest_result = result.payload.get("backtest_result")
    if final_config is not None and backtest_result is not None:
        _persist_backtest_run(final_config, backtest_result)
    return _portfolio_research_response(result)


def _module_risk_response(request: PortfolioResearchModuleRequest) -> dict:
    equal_weight = 1 / len(request.symbols) if request.symbols else 0
    return _portfolio_risk_response(
        PortfolioRiskRequest(
            symbols=request.symbols,
            weights={symbol: equal_weight for symbol in request.symbols},
            benchmark_symbol=request.constraints.benchmark_symbol,
        )
    )


def _module_optimizer_response(request: PortfolioResearchModuleRequest) -> dict:
    return _portfolio_optimizer_response(
        PortfolioOptimizerRequest(
            symbols=request.symbols,
            method=request.strategy_preferences.optimizer_method,
            max_position_weight=request.constraints.max_position_weight,
            min_cash_weight=request.constraints.min_cash_weight,
        )
    )


def _run_portfolio_research_module(request: PortfolioResearchRunRequest) -> dict:
    module_request = _to_module_request(request)
    engine = PortfolioResearchEngine(
        workflow_runner=_module_workflow_response,
        risk_runner=_module_risk_response,
        optimizer_runner=_module_optimizer_response,
        archive_writer=_archive_portfolio_research_run,
    )
    return engine.run(module_request)


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


@app.post("/risk/portfolio")
def analyze_portfolio_risk_endpoint(request: PortfolioRiskRequest) -> dict:
    if not request.symbols:
        raise HTTPException(status_code=400, detail="symbols are required")
    try:
        return _portfolio_risk_response(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PriceHistoryError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/optimizer/portfolio")
def optimize_portfolio_endpoint(request: PortfolioOptimizerRequest) -> dict:
    if not request.symbols:
        raise HTTPException(status_code=400, detail="symbols are required")
    try:
        return _portfolio_optimizer_response(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PriceHistoryError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/portfolio-research/run")
def run_portfolio_research(request: PortfolioResearchRunRequest) -> dict:
    if not request.symbols:
        raise HTTPException(status_code=400, detail="symbols are required")
    try:
        return _run_portfolio_research_module(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PriceHistoryError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


def _list_research_runs(
    *,
    limit: int,
    offset: int,
    workflow_name: str | None,
    state: str | None,
    portfolio_name: str | None,
    strategy_library_name: str | None,
    start_date: str | None,
    end_date: str | None,
) -> dict:
    with session_scope() as session:
        summaries = [
            summarize_run(
                trace_id=record.trace_id,
                workflow_name=record.workflow_name,
                workflow_version=record.workflow_version,
                state=record.state,
                request=record.request,
                response=record.response,
                started_at=record.started_at,
                completed_at=record.completed_at,
            )
            for record in list_workflow_runs(session, workflow_name=workflow_name, state=state)
        ]
    if portfolio_name is not None:
        summaries = [item for item in summaries if item.portfolio_name == portfolio_name]
    if strategy_library_name is not None:
        summaries = [item for item in summaries if item.strategy_library_name == strategy_library_name]
    if start_date is not None:
        summaries = [item for item in summaries if item.started_at[:10] >= start_date]
    if end_date is not None:
        summaries = [item for item in summaries if item.started_at[:10] <= end_date]
    total_count = len(summaries)
    page = summaries[offset : offset + limit]
    return RunHistoryResult(items=page, total_count=total_count, limit=limit, offset=offset).to_dict()


@app.get("/research-runs")
def get_research_run_history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    workflow_name: str | None = None,
    state: str | None = None,
    portfolio_name: str | None = None,
    strategy_library_name: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    return _list_research_runs(
        limit=limit,
        offset=offset,
        workflow_name=workflow_name,
        state=state,
        portfolio_name=portfolio_name,
        strategy_library_name=strategy_library_name,
        start_date=start_date,
        end_date=end_date,
    )


@app.get("/portfolio-research/{trace_id}")
def get_portfolio_research(trace_id: str) -> dict:
    response = _fetch_portfolio_research_run(trace_id)
    if response is None:
        raise HTTPException(status_code=404, detail="portfolio research run not found")
    return response


@app.post("/reports/from-trace/{trace_id}")
def create_report_from_trace(trace_id: str) -> dict:
    return _save_report_for_trace_id(trace_id)


@app.get("/reports")
def get_reports(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    portfolio_name: str | None = None,
) -> dict:
    return _list_reports(limit=limit, offset=offset, portfolio_name=portfolio_name)


@app.get("/reports/{trace_id}")
def get_report(trace_id: str) -> dict:
    report = _get_report(trace_id)
    if report is None:
        raise HTTPException(status_code=404, detail="report not found")
    return report


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
    response = _portfolio_research_response(result)
    _persist_workflow_run(request, response)
    return response


@app.get("/workflows/portfolio-research/{trace_id}")
def get_portfolio_research_workflow_run(trace_id: str) -> dict:
    response = _fetch_workflow_run(trace_id)
    if response is None:
        raise HTTPException(status_code=404, detail="workflow run not found")
    return response
