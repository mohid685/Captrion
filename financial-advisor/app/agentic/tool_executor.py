"""
Executes a tool call requested by the LLM against the real underlying
functions built in Phases 0-3, and returns a JSON-serializable result.
"""

from __future__ import annotations

import json
from typing import Any

from app.core.embeddings import embed_query
from app.core.vector_store import VectorStoreError, query_similar
from app.finance.calculator import CalculatorError, calculate_financial_metric
from app.ingestion.market_data import MarketDataError, get_latest_price
from app.ml.risk_metrics import RiskMetricsError, compute_risk_metrics
from app.ml.sentiment import aggregate_sentiment, score_texts
from app.ml.trend_model import TrendModelError, predict_trend


class ToolExecutionError(Exception):
    """Raised when a requested tool fails to execute."""


def _tool_search_documents(ticker: str, query: str) -> dict[str, Any]:
    query_vector = embed_query(query)
    chunks = query_similar(ticker, query_vector, top_k=5)
    return {"ticker": ticker.upper(), "query": query, "results": chunks}


def _tool_get_sentiment(ticker: str, query: str) -> dict[str, Any]:
    query_vector = embed_query(query)
    chunks = query_similar(ticker, query_vector, top_k=5)
    texts = [c["text"] for c in chunks]
    scored = score_texts(texts)
    aggregate = aggregate_sentiment(scored)
    return {"ticker": ticker.upper(), **aggregate, "num_documents_analyzed": len(texts)}


def _tool_get_trend_prediction(ticker: str) -> dict[str, Any]:
    return predict_trend(ticker)


def _tool_get_risk_metrics(ticker: str) -> dict[str, Any]:
    return compute_risk_metrics(ticker)


def _tool_get_current_price(ticker: str) -> dict[str, Any]:
    return get_latest_price(ticker)


def _tool_calculate_financial_metric(**kwargs: Any) -> dict[str, Any]:
    metric = kwargs.pop("metric")
    # Drop None values the LLM may have included for irrelevant fields.
    clean_kwargs = {k: v for k, v in kwargs.items() if v is not None}
    return calculate_financial_metric(metric, **clean_kwargs)


TOOL_DISPATCH = {
    "search_documents": _tool_search_documents,
    "get_sentiment": _tool_get_sentiment,
    "get_trend_prediction": _tool_get_trend_prediction,
    "get_risk_metrics": _tool_get_risk_metrics,
    "get_current_price": _tool_get_current_price,
    "calculate_financial_metric": _tool_calculate_financial_metric,
}


def execute_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Executes a named tool with the given arguments, catching known errors."""
    handler = TOOL_DISPATCH.get(name)
    if handler is None:
        raise ToolExecutionError(f"Unknown tool: '{name}'")

    try:
        return handler(**arguments)
    except (
        VectorStoreError,
        TrendModelError,
        RiskMetricsError,
        MarketDataError,
        CalculatorError,
    ) as exc:
        return {"error": str(exc)}


def parse_tool_call_arguments(raw_arguments: str) -> dict[str, Any]:
    """Parses the JSON string arguments an LLM tool_call provides."""
    try:
        return json.loads(raw_arguments)
    except json.JSONDecodeError as exc:
        raise ToolExecutionError(f"Could not parse tool arguments: {raw_arguments}") from exc