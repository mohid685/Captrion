from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.ingestion.market_data import MarketDataError, get_historical_prices, get_latest_price

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/{ticker}/history")
def historical_prices(
    ticker: str,
    period: str = Query("6mo", description="e.g. 1mo, 6mo, 1y, 5y"),
    interval: str = Query("1d", description="e.g. 1d, 1wk, 1mo"),
) -> list[dict[str, Any]]:
    try:
        return get_historical_prices(ticker.upper(), period=period, interval=interval)
    except MarketDataError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{ticker}/latest")
def latest_price(ticker: str) -> dict[str, Any]:
    try:
        return get_latest_price(ticker.upper())
    except MarketDataError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc