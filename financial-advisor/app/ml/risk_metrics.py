"""
Risk metrics: volatility, Sharpe ratio, max drawdown, and Beta.

Unlike the trend model, these are direct statistical calculations with
no training step — computed fresh from price history on every call,
same pattern as the sentiment scorer.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.ingestion.market_data import MarketDataError, get_historical_prices

TRADING_DAYS_PER_YEAR = 252
RISK_FREE_RATE = 0.045  # ~short-term Treasury yield assumption; revisit periodically
BENCHMARK_TICKER = "SPY"


class RiskMetricsError(Exception):
    """Raised when risk metrics can't be computed (insufficient or missing data)."""


def _daily_returns(history: list[dict[str, Any]]) -> pd.Series:
    closes = pd.Series([row["close"] for row in history])
    return closes.pct_change().dropna()


def _annualized_volatility(returns: pd.Series) -> float:
    return float(returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR))


def _annualized_return(returns: pd.Series) -> float:
    total_return = float((1 + returns).prod() - 1)
    years = len(returns) / TRADING_DAYS_PER_YEAR
    if years <= 0:
        return 0.0
    return (1 + total_return) ** (1 / years) - 1


def _sharpe_ratio(annualized_return: float, annualized_volatility: float) -> float | None:
    if annualized_volatility == 0:
        return None
    return (annualized_return - RISK_FREE_RATE) / annualized_volatility


def _max_drawdown(history: list[dict[str, Any]]) -> float:
    closes = pd.Series([row["close"] for row in history])
    running_max = closes.cummax()
    drawdowns = (closes - running_max) / running_max
    return float(drawdowns.min())  # most negative value = largest drawdown


def _beta(ticker_returns: pd.Series, benchmark_returns: pd.Series) -> float | None:
    aligned_len = min(len(ticker_returns), len(benchmark_returns))
    if aligned_len < 2:
        return None
    t = ticker_returns.iloc[-aligned_len:].reset_index(drop=True)
    b = benchmark_returns.iloc[-aligned_len:].reset_index(drop=True)
    covariance = float(np.cov(t, b)[0][1])
    benchmark_variance = float(np.var(b))
    if benchmark_variance == 0:
        return None
    return covariance / benchmark_variance


def _risk_level(volatility: float) -> str:
    if volatility < 0.20:
        return "low"
    if volatility < 0.40:
        return "moderate"
    return "high"


def compute_risk_metrics(ticker: str, period: str = "2y") -> dict[str, Any]:
    """
    Computes volatility, Sharpe ratio, max drawdown, and Beta (vs. SPY)
    for a ticker over the given lookback period.
    """
    try:
        history = get_historical_prices(ticker, period=period, interval="1d")
    except MarketDataError as exc:
        raise RiskMetricsError(f"Could not fetch price history for '{ticker}': {exc}") from exc

    if len(history) < 30:
        raise RiskMetricsError(
            f"Not enough price history for '{ticker}' to compute risk metrics "
            f"({len(history)} days, need at least 30)"
        )

    returns = _daily_returns(history)
    volatility = _annualized_volatility(returns)
    ann_return = _annualized_return(returns)
    sharpe = _sharpe_ratio(ann_return, volatility)
    max_dd = _max_drawdown(history)

    beta: float | None = None
    if ticker.upper() != BENCHMARK_TICKER:
        try:
            benchmark_history = get_historical_prices(BENCHMARK_TICKER, period=period, interval="1d")
            benchmark_returns = _daily_returns(benchmark_history)
            beta = _beta(returns, benchmark_returns)
        except MarketDataError:
            beta = None  # Beta is a nice-to-have; don't fail the whole calculation over it

    return {
        "ticker": ticker.upper(),
        "annualized_volatility": round(volatility, 4),
        "annualized_return": round(ann_return, 4),
        "sharpe_ratio": round(sharpe, 4) if sharpe is not None else None,
        "max_drawdown": round(max_dd, 4),
        "beta": round(beta, 4) if beta is not None else None,
        "risk_level": _risk_level(volatility),
        "risk_free_rate_assumption": RISK_FREE_RATE,
        "benchmark": BENCHMARK_TICKER,
    }