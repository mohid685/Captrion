"""
Financial sentiment analysis via FinBERT.

FinBERT (ProsusAI/finbert) is a BERT model fine-tuned specifically on
financial text, outputting positive/negative/neutral labels with
confidence scores. Runs locally via transformers — no API key, no cost.
Loaded once and cached, same pattern as the Phase 1 embedding model.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch

FINBERT_MODEL_NAME = "ProsusAI/finbert"


@lru_cache
def _get_finbert() -> tuple[Any, Any]:
    tokenizer = AutoTokenizer.from_pretrained(FINBERT_MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(FINBERT_MODEL_NAME)
    model.eval()
    return tokenizer, model


def score_texts(texts: list[str]) -> list[dict[str, Any]]:
    """
    Score a batch of texts for financial sentiment.

    Returns one dict per input text: {"label": "positive"|"negative"|"neutral",
    "confidence": float}. Texts are truncated to FinBERT's 512-token limit.
    """
    if not texts:
        return []

    tokenizer, model = _get_finbert()
    labels = ["positive", "negative", "neutral"]  # FinBERT's label order

    inputs = tokenizer(
        texts, padding=True, truncation=True, max_length=512, return_tensors="pt"
    )
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)

    results: list[dict[str, Any]] = []
    for prob_row in probs:
        top_idx = int(torch.argmax(prob_row))
        results.append(
            {
                "label": labels[top_idx],
                "confidence": round(float(prob_row[top_idx]), 4),
            }
        )
    return results


def aggregate_sentiment(scored: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Aggregate per-text sentiment scores into an overall label (majority
    vote) and average confidence for that label.
    """
    if not scored:
        return {"overall_label": "neutral", "overall_confidence": 0.0}

    label_counts: dict[str, int] = {}
    label_confidence_sums: dict[str, float] = {}
    for item in scored:
        label = item["label"]
        label_counts[label] = label_counts.get(label, 0) + 1
        label_confidence_sums[label] = label_confidence_sums.get(label, 0.0) + item["confidence"]

    overall_label = max(label_counts, key=lambda l: label_counts[l])
    overall_confidence = round(
        label_confidence_sums[overall_label] / label_counts[overall_label], 4
    )

    return {"overall_label": overall_label, "overall_confidence": overall_confidence}