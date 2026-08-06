import pandas as pd

from app.ml.features import (
    FEATURE_COLUMNS,
    build_labels,
    build_latest_features,
    build_training_dataset,
    compute_indicators,
)


def _fake_history(n: int = 60, trend: str = "up") -> list[dict]:
    """Synthetic OHLCV history with a clear upward or downward drift."""
    step = 1.0 if trend == "up" else -1.0
    records = []
    for i in range(n):
        close = 100 + i * step
        records.append(
            {
                "date": f"2026-01-{(i % 28) + 1:02d}",
                "open": close - 0.5,
                "high": close + 1,
                "low": close - 1,
                "close": close,
                "volume": 1_000_000 + i * 1000,
            }
        )
    return records


class TestComputeIndicators:
    def test_adds_expected_columns(self) -> None:
        df = pd.DataFrame(_fake_history())
        result = compute_indicators(df)
        for col in FEATURE_COLUMNS:
            assert col in result.columns

    def test_early_rows_have_nan_due_to_lookback(self) -> None:
        df = pd.DataFrame(_fake_history())
        result = compute_indicators(df)
        assert result["ma_20" if "ma_20" in result.columns else "price_to_ma20"].isna().iloc[0]


class TestBuildLabels:
    def test_strong_uptrend_labels_up(self) -> None:
        df = pd.DataFrame(_fake_history(n=30, trend="up"))
        labels = build_labels(df, horizon=5)
        non_null = labels.dropna()
        assert (non_null == "up").sum() > 0

    def test_strong_downtrend_labels_down(self) -> None:
        df = pd.DataFrame(_fake_history(n=30, trend="down"))
        labels = build_labels(df, horizon=5)
        non_null = labels.dropna()
        assert (non_null == "down").sum() > 0

    def test_last_rows_have_no_label(self) -> None:
        df = pd.DataFrame(_fake_history(n=30))
        labels = build_labels(df, horizon=5)
        assert labels.iloc[-1] is None or pd.isna(labels.iloc[-1])


class TestBuildTrainingDataset:
    def test_x_and_y_are_aligned_and_nan_free(self) -> None:
        history = _fake_history(n=100)
        X, y = build_training_dataset(history)
        assert len(X) == len(y)
        assert not X.isna().any().any()
        assert y.isna().sum() == 0


class TestBuildLatestFeatures:
    def test_returns_single_row(self) -> None:
        history = _fake_history(n=60)
        row = build_latest_features(history)
        assert len(row) == 1
        assert list(row.columns) == FEATURE_COLUMNS