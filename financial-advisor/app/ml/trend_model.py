"""
XGBoost trend prediction: train once, persist to disk, load for inference.

Predicts next-week (5 trading day) price direction: up / down / sideways.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd

import xgboost as xgb

from app.ingestion.market_data import get_historical_prices
from app.ml.features import build_latest_features, build_training_dataset

MODELS_DIR = Path("models")
MODELS_DIR.mkdir(exist_ok=True)

LABEL_TO_INT = {"down": 0, "sideways": 1, "up": 2}
INT_TO_LABEL = {v: k for k, v in LABEL_TO_INT.items()}

MIN_TRAINING_SAMPLES = 100


class TrendModelError(Exception):
    """Raised when a model can't be trained or isn't available for inference."""


def _model_path(ticker: str) -> Path:
    return MODELS_DIR / f"{ticker.upper()}_trend.json"


def train_trend_model(ticker: str, period: str = "2y") -> dict[str, Any]:
    """Fetches history, trains an XGBoost classifier, and persists it to disk."""
    history = get_historical_prices(ticker, period=period, interval="1d")
    X, y = build_training_dataset(history)

    if len(X) < MIN_TRAINING_SAMPLES:
        raise TrendModelError(
            f"Not enough data to train a model for '{ticker}' "
            f"({len(X)} usable rows, need at least {MIN_TRAINING_SAMPLES})"
        )

    y_encoded = y.map(LABEL_TO_INT)

    present_classes = set(y_encoded.unique())
    if len(present_classes) < 3:
        missing = set(LABEL_TO_INT.values()) - present_classes
        missing_labels = [INT_TO_LABEL[m] for m in missing]
        raise TrendModelError(
            f"Training data for '{ticker}' only contains {len(present_classes)} of 3 "
            f"trend classes (missing: {missing_labels}). Try a longer period."
        )

    # Time-based split: no shuffling, since shuffling would leak future
    # data into the training set.
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y_encoded.iloc[:split_idx], y_encoded.iloc[split_idx:]

    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        objective="multi:softprob",
        eval_metric="mlogloss",
    )
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    accuracy = float((predictions == y_test.to_numpy()).mean()) if len(X_test) else None

    model.save_model(str(_model_path(ticker)))

    return {
        "ticker": ticker.upper(),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "test_accuracy": round(accuracy, 4) if accuracy is not None else None,
        "diagnostics": _build_diagnostics(y_train, y_test, predictions),
    }


def _build_diagnostics(
    y_train: "pd.Series", y_test: "pd.Series", predictions: "np.ndarray"
) -> dict[str, Any]:
    """Class balance + confusion matrix, to sanity-check accuracy numbers."""
    import numpy as np
    import pandas as pd

    def _label_counts(series: pd.Series) -> dict[str, int]:
        counts = series.value_counts()
        return {INT_TO_LABEL[i]: int(counts.get(i, 0)) for i in range(3)}

    y_test_arr = y_test.to_numpy()
    labels_order = [0, 1, 2]  # down, sideways, up
    confusion = {INT_TO_LABEL[actual]: {INT_TO_LABEL[pred]: 0 for pred in labels_order} for actual in labels_order}
    for actual, predicted in zip(y_test_arr, predictions):
        confusion[INT_TO_LABEL[int(actual)]][INT_TO_LABEL[int(predicted)]] += 1

    naive_baseline_label = max(_label_counts(y_train), key=lambda k: _label_counts(y_train)[k])
    naive_baseline_accuracy = (
        round(float((y_test_arr == LABEL_TO_INT[naive_baseline_label]).mean()), 4)
        if len(y_test_arr)
        else None
    )

    return {
        "train_class_distribution": _label_counts(y_train),
        "test_class_distribution": _label_counts(y_test),
        "confusion_matrix": confusion,  # {actual_label: {predicted_label: count}}
        "naive_baseline": {
            "strategy": f"always predict '{naive_baseline_label}' (most common training class)",
            "accuracy": naive_baseline_accuracy,
        },
    }

def predict_trend(ticker: str) -> dict[str, Any]:
    """Loads the persisted model and predicts the current trend for a ticker."""
    path = _model_path(ticker)
    if not path.exists():
        raise TrendModelError(
            f"No trained model for '{ticker}'. POST /ml/{ticker.upper()}/train first."
        )

    # Load via the raw Booster rather than the sklearn XGBClassifier wrapper.
    # save_model()/load_model() only round-trip the Booster itself — the
    # wrapper's classes_/n_classes_ bookkeeping isn't persisted, and in
    # this xgboost version classes_ is a read-only property we can't
    # restore manually. DMatrix + Booster.predict() avoids that entirely.
    booster = xgb.Booster()
    booster.load_model(str(path))

    history = get_historical_prices(ticker, period="3mo", interval="1d")
    latest_features = build_latest_features(history)

    dmatrix = xgb.DMatrix(latest_features)
    probabilities = booster.predict(dmatrix)[0]
    top_idx = int(probabilities.argmax())

    return {
        "trend_prediction": INT_TO_LABEL[top_idx],
        "trend_confidence": round(float(probabilities[top_idx]), 4),
        "probabilities": {
            INT_TO_LABEL[i]: round(float(p), 4) for i, p in enumerate(probabilities)
        },
    }