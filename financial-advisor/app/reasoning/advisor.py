"""
Reasoning orchestration: combines RAG context + real sentiment analysis
+ mock ML signals into a prompt, and asks the LLM to answer grounded
only in that evidence.
"""

from __future__ import annotations

from typing import Any

from app.core.embeddings import embed_query
from app.core.llm_client import generate_response
from app.core.vector_store import query_similar
# from app.ml.mock_predictor import get_mock_ml_signals
from app.ml.predictor import get_ml_signals
from app.ml.sentiment import aggregate_sentiment, score_texts

SYSTEM_PROMPT = """You are a financial investment advisor assistant. You must answer \
the user's question using ONLY the evidence provided below: retrieved document \
excerpts, real sentiment analysis, and quantitative model signals. Do not invent \
facts, figures, or events that are not present in the provided evidence.

The trend prediction signal includes a reliability rating. When that rating is \
"very low" or "low," treat the trend prediction as a weak, exploratory data point \
rather than a strong indicator — lean more heavily on the document evidence and \
sentiment analysis in that case, and say so explicitly in your answer.

If the evidence is insufficient to fully answer the question, say so explicitly \
rather than guessing. Always mention that quantitative signals are model \
estimates, not guarantees. Be concise, cite which type of source (SEC filing, \
news, sentiment analysis, or model signal) supports each claim you make, and \
never present this as personalized financial advice — frame it as informational \
analysis only."""

VOICE_SYSTEM_PROMPT = """You are a sharp, human financial advisor in a live conversation.
Speak naturally like a person, not like a report. Give a direct view in 2-4 short
sentences, using plain language and concrete numbers when available.

Rules:
- No markdown, no bullets, no headings, no disclaimers list.
- Keep under 450 characters.
- If data is limited, say that briefly and still give a practical next step.
- If risk is high, mention position sizing or staged entry in one short phrase.
- Never claim certainty; sound confident but realistic."""


def _score_chunk_sentiment(rag_chunks: list[dict[str, Any]]) -> dict[str, Any]:
    """Run FinBERT over the retrieved chunk texts and aggregate the result."""
    texts = [chunk["text"] for chunk in rag_chunks]
    scored = score_texts(texts)
    aggregate = aggregate_sentiment(scored)

    per_chunk = [
        {
            "label": scored[i]["label"],
            "confidence": scored[i]["confidence"],
            "source": rag_chunks[i]["source"],
            "date": rag_chunks[i].get("date"),
        }
        for i in range(len(rag_chunks))
    ]

    return {
        "overall_label": aggregate["overall_label"],
        "overall_confidence": aggregate["overall_confidence"],
        "source": "FinBERT (real model — not mocked)",
        "per_chunk": per_chunk,
    }


def build_user_prompt(
    question: str,
    ticker: str,
    rag_chunks: list[dict[str, Any]],
    ml_signals: dict[str, Any],
    sentiment: dict[str, Any],
    user_context: dict[str, Any] | None = None,
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
        f"(model confidence: {ml_signals['trend_confidence']})\n"
        f"Trend model reliability: {ml_signals.get('trend_reliability_tier', 'unknown')}\n"
        f"Risk level: {ml_signals['risk_level']} "
        f"(Sharpe ratio: {ml_signals.get('sharpe_ratio_estimate', 'n/a')}, "
        f"annualized volatility: {ml_signals.get('annualized_volatility', 'n/a')}, "
        f"max drawdown: {ml_signals.get('max_drawdown', 'n/a')}, "
        f"Beta vs. SPY: {ml_signals.get('beta', 'n/a')})\n"
        f"Risk metrics source: {ml_signals.get('risk_source', 'unknown')}\n"
        f"[{ml_signals['note']}]"
    )

    sentiment_block = (
        f"Overall sentiment: {sentiment['overall_label']} "
        f"(confidence: {sentiment['overall_confidence']})\n"
        f"[Computed by real FinBERT model over the retrieved evidence above]"
    )

    user_block = ""
    if user_context:
        parts = []
        if user_context.get("risk_tolerance"):
            parts.append(f"Stated risk tolerance: {user_context['risk_tolerance']}")
        if user_context.get("investment_goals"):
            parts.append(f"Stated investment goals: {user_context['investment_goals']}")
        if user_context.get("holding"):
            h = user_context["holding"]
            parts.append(
                f"Currently holds {h['shares']} shares of {ticker.upper()} "
                f"at a cost basis of ${h['cost_basis']:.2f}/share"
            )
        if parts:
            user_block = "\n--- User context ---\n" + "\n".join(parts) + "\n"

    return f"""Ticker: {ticker.upper()}
User question: {question}
{user_block}
--- Retrieved document evidence ---
{context_block}

--- Sentiment analysis (real model) ---
{sentiment_block}

--- Quantitative model signals ---
{ml_block}

Answer the user's question using only the evidence above. If user context is provided, \
tailor your framing to their stated risk tolerance and goals where relevant, and \
acknowledge their existing position if they hold this ticker."""


def ask_advisor(
    ticker: str, question: str, top_k: int = 5, user_context: dict[str, Any] | None = None
) -> dict[str, Any]:
    query_vector = embed_query(question)
    rag_chunks = query_similar(ticker, query_vector, top_k=top_k)
    ml_signals = get_ml_signals(ticker)
    sentiment = _score_chunk_sentiment(rag_chunks)

    user_prompt = build_user_prompt(question, ticker, rag_chunks, ml_signals, sentiment, user_context)
    answer = generate_response(SYSTEM_PROMPT, user_prompt)

    return {
        "ticker": ticker.upper(),
        "question": question,
        "answer": answer,
        "sources_used": [
            {"source": c["source"], "doc_type": c.get("doc_type"), "date": c.get("date")}
            for c in rag_chunks
        ],
        "sentiment_analysis": sentiment,
        "ml_signals": ml_signals,
    }


def _compact_voice_context(rag_chunks: list[dict[str, Any]]) -> str:
    if not rag_chunks:
        return "No retrieved filings/news context available for this ticker right now."

    snippets: list[str] = []
    for chunk in rag_chunks[:3]:
        source = chunk.get("source", "unknown source")
        date = chunk.get("date", "n/a")
        text = (chunk.get("text") or "").replace("\n", " ").strip()
        snippets.append(f"{source} ({date}): {text[:220]}")
    return " | ".join(snippets)


def ask_advisor_voice(
    ticker: str, question: str, top_k: int = 5, user_context: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Fast conversational variant of ask_advisor for voice UX."""
    query_vector = embed_query(question)
    rag_chunks = query_similar(ticker, query_vector, top_k=top_k)
    ml_signals = get_ml_signals(ticker)
    sentiment = _score_chunk_sentiment(rag_chunks)

    context_note = ""
    if user_context:
        parts = []
        if user_context.get("risk_tolerance"):
            parts.append(f"risk tolerance: {user_context['risk_tolerance']}")
        if user_context.get("investment_goals"):
            parts.append(f"goals: {user_context['investment_goals']}")
        if user_context.get("holding"):
            h = user_context["holding"]
            parts.append(f"holding: {h['shares']} shares at {h['cost_basis']:.2f}")
        if parts:
            context_note = "Client context: " + ", ".join(parts)

    voice_user_prompt = (
        f"Ticker: {ticker.upper()}\n"
        f"Question: {question}\n"
        f"{context_note}\n"
        f"Retrieved context: {_compact_voice_context(rag_chunks)}\n"
        f"Sentiment: {sentiment['overall_label']} (confidence {sentiment['overall_confidence']})\n"
        f"Trend: {ml_signals['trend_prediction']} ({ml_signals['trend_confidence']})\n"
        f"Trend reliability: {ml_signals.get('trend_reliability_tier', 'unknown')}\n"
        f"Risk: volatility {ml_signals.get('annualized_volatility', 'n/a')}, "
        f"Sharpe {ml_signals.get('sharpe_ratio_estimate', 'n/a')}, "
        f"max drawdown {ml_signals.get('max_drawdown', 'n/a')}, "
        f"beta {ml_signals.get('beta', 'n/a')}\n"
        "Reply conversationally in 2-4 short sentences under 450 characters."
    )

    answer = generate_response(VOICE_SYSTEM_PROMPT, voice_user_prompt).strip()
    if len(answer) > 450:
        answer = answer[:450].rsplit(" ", 1)[0].rstrip(".,;: ") + "."

    return {
        "ticker": ticker.upper(),
        "question": question,
        "answer": answer,
        "sources_used": [
            {"source": c["source"], "doc_type": c.get("doc_type"), "date": c.get("date")}
            for c in rag_chunks
        ],
        "sentiment_analysis": sentiment,
        "ml_signals": ml_signals,
    }