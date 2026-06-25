from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from packages.data_sources.market_trend import (
    MarketTrendError,
    YahooFinanceChartClient,
    normalize_symbol,
)


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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "openstock-ai-api"}


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

