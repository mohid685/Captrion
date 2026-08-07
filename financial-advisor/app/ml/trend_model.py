"""
XGBoost trend prediction: train once, persist to disk, load for inference.

Predicts next-week (5 trading day) price direction: up / down / sideways.

Alongside the model, we persist a small metadata file recording how much
the model actually beat a naive "always guess the majority class"
baseline. That reliability figure travels with every prediction, so
downstream consumers (the LLM prompt) can weight the signal honestly
instead of treating it as authoritative by default.
"""

from __future__ import annotations

import json
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


def _meta_path(ticker: str) -> Path:
    return MODELS_DIR / f"{ticker.upper()}_trend_meta.json"


def _label_counts(series: pd.Series) -> dict[str, int]:
    counts = series.value_counts()
    return {INT_TO_LABEL[i]: int(counts.get(i, 0)) for i in range(3)}


def _build_diagnostics(
    y_train: pd.Series, y_test: pd.Series, predictions: np.ndarray
) -> dict[str, Any]:
    """Class balance + confusion matrix, to sanity-check accuracy numbers."""
    y_test_arr = y_test.to_numpy()
    labels_order = [0, 1, 2]  # down, sideways, up
    confusion = {
        INT_TO_LABEL[actual]: {INT_TO_LABEL[pred]: 0 for pred in labels_order}
        for actual in labels_order
    }
    for actual, predicted in zip(y_test_arr, predictions):
        confusion[INT_TO_LABEL[int(actual)]][INT_TO_LABEL[int(predicted)]] += 1

    train_counts = _label_counts(y_train)
    naive_baseline_label = max(train_counts, key=lambda k: train_counts[k])
    naive_baseline_accuracy = (
        round(float((y_test_arr == LABEL_TO_INT[naive_baseline_label]).mean()), 4)
        if len(y_test_arr)
        else None
    )

    return {
        "train_class_distribution": train_counts,
        "test_class_distribution": _label_counts(y_test),
        "confusion_matrix": confusion,
        "naive_baseline": {
            "strategy": f"always predict '{naive_baseline_label}' (most common training class)",
            "accuracy": naive_baseline_accuracy,
        },
    }


def _reliability_tier(edge: float | None) -> str:
    """
    Translate accuracy-over-baseline into a plain-language reliability
    label, so the LLM prompt doesn't have to interpret raw numbers.
    """
    if edge is None:
        return "unknown"
    if edge < 0.03:
        return "very low — barely distinguishable from random guessing"
    if edge < 0.08:
        return "low — modest edge over guessing the majority class"
    if edge < 0.15:
        return "moderate — meaningfully outperforms the naive baseline"
    return "high — substantially outperforms the naive baseline"


def train_trend_model(ticker: str, period: str = "2y") -> dict[str, Any]:
    """Fetches history, trains an XGBoost classifier, and persists it + reliability metadata."""
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
    diagnostics = _build_diagnostics(y_train, y_test, predictions)

    naive_accuracy = diagnostics["naive_baseline"]["accuracy"]
    edge_over_baseline = (
        round(accuracy - naive_accuracy, 4) if accuracy is not None and naive_accuracy is not None else None
    )

    model.save_model(str(_model_path(ticker)))

    metadata = {
        "ticker": ticker.upper(),
        "test_accuracy": round(accuracy, 4) if accuracy is not None else None,
        "naive_baseline_accuracy": naive_accuracy,
        "edge_over_baseline": edge_over_baseline,
        "reliability_tier": _reliability_tier(edge_over_baseline),
    }
    _meta_path(ticker).write_text(json.dumps(metadata))

    return {
        "ticker": ticker.upper(),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "test_accuracy": metadata["test_accuracy"],
        "reliability": {
            "naive_baseline_accuracy": naive_accuracy,
            "edge_over_baseline": edge_over_baseline,
            "reliability_tier": metadata["reliability_tier"],
        },
        "diagnostics": diagnostics,
    }


def predict_trend(ticker: str) -> dict[str, Any]:
    """Loads the persisted model + reliability metadata and predicts the current trend."""
    path = _model_path(ticker)
    meta_path = _meta_path(ticker)
    if not path.exists():
        raise TrendModelError(
            f"No trained model for '{ticker}'. POST /ml/{ticker.upper()}/train first."
        )

    booster = xgb.Booster()
    booster.load_model(str(path))

    history = get_historical_prices(ticker, period="3mo", interval="1d")
    latest_features = build_latest_features(history)

    dmatrix = xgb.DMatrix(latest_features)
    probabilities = booster.predict(dmatrix)[0]
    top_idx = int(probabilities.argmax())

    reliability: dict[str, Any] = {
        "naive_baseline_accuracy": None,
        "edge_over_baseline": None,
        "reliability_tier": "unknown — model trained before reliability tracking was added",
    }
    if meta_path.exists():
        try:
            metadata = json.loads(meta_path.read_text())
            reliability = {
                "naive_baseline_accuracy": metadata.get("naive_baseline_accuracy"),
                "edge_over_baseline": metadata.get("edge_over_baseline"),
                "reliability_tier": metadata.get("reliability_tier", "unknown"),
            }
        except (json.JSONDecodeError, OSError):
            pass

    return {
        "trend_prediction": INT_TO_LABEL[top_idx],
        "trend_confidence": round(float(probabilities[top_idx]), 4),
        "probabilities": {
            INT_TO_LABEL[i]: round(float(p), 4) for i, p in enumerate(probabilities)
        },
        "reliability": reliability,
    }