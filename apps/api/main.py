from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from packages.ai_agents.sec_filing_agent import SECFilingAgent
from packages.algorithm_layer.recommendation import TrendRecommendationAlgorithm
from packages.algorithm_layer.schemas import (
    AlgorithmPoint,
    FinancialFactorsInput,
    RecommendationInput,
    TechnicalSeriesInput,
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
from packages.db.session import check_database_connection, session_scope
from packages.db.stock_scores import get_score_history, write_screening_result
from packages.model_layer.factory import build_default_router
from packages.model_layer.validator import OutputValidationError
from packages.news_layer.news_policy import NewsPolicyClient, NewsPolicyError
from packages.universe_layer.most_active import MostActiveUniverseScanner
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


screening_workflow = StockScreeningWorkflow(
    universe_scanner=universe_scanner,
    trend_client=trend_client,
    algorithm=recommendation_algorithm,
    financial_factors_fetcher=_fetch_financial_factors,
    technical_series_fetcher=_fetch_technical_series,
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
