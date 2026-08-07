"""
Market data ingestion.

yfinance is the default source (free, no API key, good enough for
historical prices). Alpha Vantage is available as a fallback for when
yfinance rate-limits or a key is configured for higher-quality data.

Returns plain dicts/lists rather than pandas DataFrames at the boundary,
so downstream layers (RAG, ML, API responses) don't need to care which
library produced the data.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

import requests
import yfinance as yf

from app.config import get_settings

logger = logging.getLogger(__name__)

ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"


class MarketDataError(Exception):
    """Raised when no configured data source can fulfill the request."""


def get_historical_prices(
    ticker: str,
    period: str = "6mo",
    interval: str = "1d",
) -> list[dict[str, Any]]:
    """
    Fetch historical OHLCV data for a ticker.

    Tries yfinance first; falls back to Alpha Vantage if yfinance returns
    no data and an Alpha Vantage API key is configured.
    """
    try:
        data = _fetch_from_yfinance(ticker, period, interval)
        if data:
            return data
        logger.warning("yfinance returned no data for %s, trying fallback", ticker)
    except Exception:
        logger.exception("yfinance fetch failed for %s, trying fallback", ticker)

    settings = get_settings()
    if settings.alpha_vantage_api_key:
        try:
            data = _fetch_from_alpha_vantage(ticker, settings.alpha_vantage_api_key)
            if data:
                return data
        except Exception:
            logger.exception("Alpha Vantage fetch failed for %s", ticker)

    raise MarketDataError(f"No data available for ticker '{ticker}' from any source")


def _fetch_from_yfinance(
    ticker: str, period: str, interval: str
) -> list[dict[str, Any]]:
    history = yf.Ticker(ticker).history(period=period, interval=interval)
    if history.empty:
        return []

    records: list[dict[str, Any]] = []
    for index, row in history.iterrows():
        row_date = index.date() if hasattr(index, "date") else index
        records.append(
            {
                "date": row_date.isoformat() if isinstance(row_date, date) else str(row_date),
                "open": round(float(row["Open"]), 4),
                "high": round(float(row["High"]), 4),
                "low": round(float(row["Low"]), 4),
                "close": round(float(row["Close"]), 4),
                "volume": int(row["Volume"]),
            }
        )
    return records

def _fetch_from_alpha_vantage(ticker: str, api_key: str) -> list[dict[str, Any]]:
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": ticker,
        "apikey": api_key,
        "outputsize": "compact",  # "full" requires a paid Alpha Vantage plan
    }
    response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=10)
    response.raise_for_status()
    payload = response.json()

    series = payload.get("Time Series (Daily)")
    if not series:
        reason = (
            payload.get("Note")
            or payload.get("Information")
            or payload.get("Error Message")
            or str(payload)[:200]
        )
        logger.warning("Alpha Vantage returned no time series for %s: %s", ticker, reason)
        return []

    records: list[dict[str, Any]] = []
    for day, values in sorted(series.items()):
        records.append(
            {
                "date": day,
                "open": round(float(values["1. open"]), 4),
                "high": round(float(values["2. high"]), 4),
                "low": round(float(values["3. low"]), 4),
                "close": round(float(values["4. close"]), 4),
                "volume": int(values["5. volume"]),
            }
        )
    return records


def get_latest_price(ticker: str) -> dict[str, Any]:
    """Convenience wrapper returning just the most recent trading day."""
    history = get_historical_prices(ticker, period="5d", interval="1d")
    if not history:
        raise MarketDataError(f"No recent price data for ticker '{ticker}'")
    return history[-1]