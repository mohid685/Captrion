"""
Feature engineering for the trend prediction model.

Builds technical indicators from OHLCV history and defines the label:
next-5-trading-day (roughly one week) price direction, with a 2%
deadband so small noise doesn't get labeled as a trend.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

HORIZON_DAYS = 5
TREND_THRESHOLD = 0.02  # 2% deadband

FEATURE_COLUMNS = [
    "return_1d",
    "return_5d",
    "return_10d",
    "return_20d",
    "price_to_ma5",
    "price_to_ma10",
    "price_to_ma20",
    "volatility_10d",
    "volume_change",
    "volume_ma_ratio",
    "rsi_14",
]


def _compute_rsi(closes: pd.Series, period: int = 14) -> pd.Series:
    delta = closes.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean().replace(0, 1e-10)
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Adds technical indicator columns to a DataFrame with an OHLCV shape."""
    df = df.copy()
    df["return_1d"] = df["close"].pct_change(1)
    df["return_5d"] = df["close"].pct_change(5)
    df["return_10d"] = df["close"].pct_change(10)
    df["return_20d"] = df["close"].pct_change(20)

    ma5 = df["close"].rolling(5).mean()
    ma10 = df["close"].rolling(10).mean()
    ma20 = df["close"].rolling(20).mean()
    df["price_to_ma5"] = df["close"] / ma5
    df["price_to_ma10"] = df["close"] / ma10
    df["price_to_ma20"] = df["close"] / ma20

    df["volatility_10d"] = df["return_1d"].rolling(10).std()
    df["volume_change"] = df["volume"].pct_change(1)
    df["volume_ma_ratio"] = df["volume"] / df["volume"].rolling(10).mean()
    df["rsi_14"] = _compute_rsi(df["close"], 14)

    return df


def _label_from_future_return(x: float) -> str | None:
    if pd.isna(x):
        return None
    if x > TREND_THRESHOLD:
        return "up"
    if x < -TREND_THRESHOLD:
        return "down"
    return "sideways"


def build_labels(df: pd.DataFrame, horizon: int = HORIZON_DAYS) -> pd.Series:
    """Labels each row by comparing price `horizon` days later to today's close."""
    future_return = df["close"].shift(-horizon) / df["close"] - 1
    return future_return.apply(_label_from_future_return)


def build_training_dataset(history: list[dict[str, Any]]) -> tuple[pd.DataFrame, pd.Series]:
    """
    Turns raw OHLCV history into (X, y) ready for training.
    Rows with insufficient lookback/lookahead (NaN features or label) are dropped.
    """
    df = pd.DataFrame(history)
    df = compute_indicators(df)
    df["label"] = build_labels(df)
    df = df.dropna(subset=FEATURE_COLUMNS + ["label"])
    return df[FEATURE_COLUMNS], df["label"]


def build_latest_features(history: list[dict[str, Any]]) -> pd.DataFrame:
    """Returns a single-row DataFrame of features for the most recent day, for inference."""
    df = pd.DataFrame(history)
    df = compute_indicators(df)
    df = df.dropna(subset=FEATURE_COLUMNS)
    if df.empty:
        raise ValueError("Not enough history to compute features for the latest day")
    return df[FEATURE_COLUMNS].iloc[[-1]]