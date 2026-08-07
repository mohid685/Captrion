from unittest.mock import patch

import pytest

from app.ingestion.market_data import MarketDataError
from app.ml.risk_metrics import RiskMetricsError, compute_risk_metrics


def _fake_history(n: int = 500, volatility: float = 0.01, drift: float = 0.0003) -> list[dict]:
    """Synthetic OHLCV with controllable daily volatility and drift, seeded for determinism."""
    import numpy as np

    rng = np.random.default_rng(42)
    price = 100.0
    records = []
    for i in range(n):
        daily_return = rng.normal(drift, volatility)
        price *= 1 + daily_return
        records.append(
            {
                "date": f"day{i}",
                "open": price * 0.995,
                "high": price * 1.01,
                "low": price * 0.99,
                "close": price,
                "volume": 1_000_000,
            }
        )
    return records


class TestComputeRiskMetrics:
    def test_raises_on_insufficient_history(self) -> None:
        with patch("app.ml.risk_metrics.get_historical_prices", return_value=_fake_history(n=10)):
            with pytest.raises(RiskMetricsError):
                compute_risk_metrics("FAKE")

    def test_raises_when_market_data_unavailable(self) -> None:
        with patch(
            "app.ml.risk_metrics.get_historical_prices",
            side_effect=MarketDataError("no data"),
        ):
            with pytest.raises(RiskMetricsError):
                compute_risk_metrics("FAKE")

    def test_returns_expected_shape(self) -> None:
        ticker_history = _fake_history(n=500, volatility=0.015)
        benchmark_history = _fake_history(n=500, volatility=0.01)

        def fake_fetch(ticker, period="2y", interval="1d"):
            return benchmark_history if ticker == "SPY" else ticker_history

        with patch("app.ml.risk_metrics.get_historical_prices", side_effect=fake_fetch):
            result = compute_risk_metrics("FAKE")

        assert result["ticker"] == "FAKE"
        assert result["annualized_volatility"] > 0
        assert result["risk_level"] in {"low", "moderate", "high"}
        assert result["benchmark"] == "SPY"
        assert result["beta"] is not None

    def test_higher_volatility_input_yields_higher_output(self) -> None:
        low_vol_history = _fake_history(n=500, volatility=0.005)
        high_vol_history = _fake_history(n=500, volatility=0.05)

        def fake_fetch_low(ticker, period="2y", interval="1d"):
            return low_vol_history

        def fake_fetch_high(ticker, period="2y", interval="1d"):
            return high_vol_history

        with patch("app.ml.risk_metrics.get_historical_prices", side_effect=fake_fetch_low):
            low_result = compute_risk_metrics("LOW")
        with patch("app.ml.risk_metrics.get_historical_prices", side_effect=fake_fetch_high):
            high_result = compute_risk_metrics("HIGH")

        assert high_result["annualized_volatility"] > low_result["annualized_volatility"]

    def test_skips_beta_gracefully_when_benchmark_unavailable(self) -> None:
        ticker_history = _fake_history(n=500)

        def fake_fetch(ticker, period="2y", interval="1d"):
            if ticker == "SPY":
                raise MarketDataError("benchmark unavailable")
            return ticker_history

        with patch("app.ml.risk_metrics.get_historical_prices", side_effect=fake_fetch):
            result = compute_risk_metrics("FAKE")

        assert result["beta"] is None
        # everything else should still compute fine
        assert result["annualized_volatility"] > 0

    def test_risk_level_thresholds(self) -> None:
        from app.ml.risk_metrics import _risk_level

        assert _risk_level(0.10) == "low"
        assert _risk_level(0.25) == "moderate"
        assert _risk_level(0.50) == "high"