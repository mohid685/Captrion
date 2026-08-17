"""
OpenAI-compatible tool schemas for the agentic advisor. These are sent
to the LLM so it can decide which, if any, to call for a given question.
"""

from __future__ import annotations

from typing import Any

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_documents",
            "description": (
                "Semantic search over previously ingested SEC filings and news "
                "for a ticker. Use this for questions about a company's financials, "
                "business commentary, or recent news."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker, e.g. AAPL"},
                    "query": {"type": "string", "description": "What to search for"},
                },
                "required": ["ticker", "query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_sentiment",
            "description": (
                "Get real FinBERT sentiment analysis over a ticker's most recently "
                "retrieved documents. Use for questions about market mood or sentiment."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker, e.g. AAPL"},
                    "query": {
                        "type": "string",
                        "description": "Topic to focus the underlying document search on",
                    },
                },
                "required": ["ticker", "query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_trend_prediction",
            "description": (
                "Get the trained XGBoost model's next-week price direction prediction "
                "for a ticker, including its honest reliability rating. Use for questions "
                "about future price direction."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker, e.g. AAPL"},
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_risk_metrics",
            "description": (
                "Get real risk statistics for a ticker: annualized volatility, Sharpe "
                "ratio, max drawdown, and Beta vs. SPY. Use for questions about risk."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker, e.g. AAPL"},
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_price",
            "description": "Get the most recent trading day's OHLCV price data for a ticker.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker, e.g. AAPL"},
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_financial_metric",
            "description": (
                "Compute a financial metric: CAGR, ROI, or a simplified DCF. "
                "Use when the user asks for a specific calculation rather than "
                "a general question. Provide only the parameters relevant to "
                "the chosen metric."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "metric": {
                        "type": "string",
                        "enum": ["CAGR", "ROI", "DCF"],
                        "description": "Which calculation to perform",
                    },
                    "beginning_value": {"type": "number", "description": "CAGR: starting value"},
                    "ending_value": {"type": "number", "description": "CAGR: ending value"},
                    "years": {"type": "number", "description": "CAGR: number of years"},
                    "cost": {"type": "number", "description": "ROI: initial cost"},
                    "gain": {"type": "number", "description": "ROI: total value gained"},
                    "cash_flows": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "DCF: projected cash flows, one per year",
                    },
                    "discount_rate": {"type": "number", "description": "DCF: discount rate, e.g. 0.08"},
                    "terminal_value": {"type": "number", "description": "DCF: optional terminal value"},
                },
                "required": ["metric"],
            },
        },
    },
]

def get_all_tool_definitions() -> list[dict[str, Any]]:
    """
    Combines our internal tools with the curated Alpha Vantage MCP
    tools. Internal tools are always available; MCP tools are added
    if the remote server is reachable (fails gracefully otherwise).
    """
    from app.agentic.mcp_client import get_curated_tool_definitions

    return TOOL_DEFINITIONS + get_curated_tool_definitions()

def get_voice_tool_definitions() -> list[dict[str, Any]]:
    """
    Tool set for the voice agent: the calculator plus a single live web
    search tool (Tavily), replacing Alpha Vantage entirely for voice.
    The agent builds a targeted search query itself at call time from
    the user's actual question — works for any company or topic, not
    limited to a curated Alpha Vantage tool list or ticker coverage.
    """
    calculator = [t for t in TOOL_DEFINITIONS if t["function"]["name"] == "calculate_financial_metric"]

    web_search_tool = {
        "type": "function",
        "function": {
            "name": "search_financial_web",
            "description": (
                "Search the live web for current financial information: prices, news, company "
                "fundamentals, earnings, analyst views, or anything else needed to answer the "
                "client's question. Build a specific, targeted query — include the company name "
                "and what you actually need (e.g. 'Samsung Electronics stock price today', "
                "'Apple Q3 2026 earnings results')."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Specific search query"},
                },
                "required": ["query"],
            },
        },
    }

    return calculator + [web_search_tool]