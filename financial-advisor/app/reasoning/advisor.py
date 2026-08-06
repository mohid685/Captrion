"""
Reasoning orchestration: combines RAG context + mock ML signals into a
prompt, and asks the LLM to answer grounded only in that evidence.
"""

from __future__ import annotations

from typing import Any

from app.core.embeddings import embed_query
from app.core.llm_client import generate_response
from app.core.vector_store import query_similar
from app.ml.mock_predictor import get_mock_ml_signals

SYSTEM_PROMPT = """You are a financial investment advisor assistant. You must answer \
the user's question using ONLY the evidence provided below: retrieved document \
excerpts and quantitative model signals. Do not invent facts, figures, or events \
that are not present in the provided evidence.

If the evidence is insufficient to fully answer the question, say so explicitly \
rather than guessing. Always mention that quantitative signals are model \
estimates, not guarantees. Be concise, cite which type of source (SEC filing, \
news, or model signal) supports each claim you make, and never present this as \
personalized financial advice — frame it as informational analysis only."""


def build_user_prompt(
    question: str,
    ticker: str,
    rag_chunks: list[dict[str, Any]],
    ml_signals: dict[str, Any],
) -> str:
    context_lines = []
    for i, chunk in enumerate(rag_chunks, start=1):
        context_lines.append(
            f"[{i}] ({chunk['source']}, {chunk.get('doc_type', 'n/a')}, "
            f"{chunk.get('date', 'n/a')}): {chunk['text']}"
        )
    context_block = "\n\n".join(context_lines) if context_lines else "No relevant documents found."

    ml_block = (
        f"Trend prediction: {ml_signals['trend_prediction']} "
        f"(confidence: {ml_signals['trend_confidence']})\n"
        f"Risk level: {ml_signals['risk_level']} "
        f"(estimated Sharpe ratio: {ml_signals['sharpe_ratio_estimate']})\n"
        f"Volatility: {ml_signals['volatility']}\n"
        f"[{ml_signals['note']}]"
    )

    return f"""Ticker: {ticker.upper()}
User question: {question}

--- Retrieved document evidence ---
{context_block}

--- Quantitative model signals ---
{ml_block}

Answer the user's question using only the evidence above."""


def ask_advisor(ticker: str, question: str, top_k: int = 5) -> dict[str, Any]:
    """
    Full Phase 2 flow: retrieve RAG context, get mock ML signals, and
    generate a grounded LLM response.
    """
    query_vector = embed_query(question)
    rag_chunks = query_similar(ticker, query_vector, top_k=top_k)
    ml_signals = get_mock_ml_signals(ticker)

    user_prompt = build_user_prompt(question, ticker, rag_chunks, ml_signals)
    answer = generate_response(SYSTEM_PROMPT, user_prompt)

    return {
        "ticker": ticker.upper(),
        "question": question,
        "answer": answer,
        "sources_used": [
            {"source": c["source"], "doc_type": c.get("doc_type"), "date": c.get("date")}
            for c in rag_chunks
        ],
        "ml_signals": ml_signals,
    }