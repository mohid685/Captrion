"""
Document ingestion: SEC EDGAR (latest 10-K/10-Q) and Alpha Vantage news.

SEC EDGAR requires a descriptive User-Agent header on every request
(their policy, not optional) and has no API key.
"""

from __future__ import annotations

import logging
from typing import Any

import requests

from app.config import get_settings

logger = logging.getLogger(__name__)

SEC_TICKER_MAP_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
SEC_ARCHIVES_BASE = "https://www.sec.gov/Archives/edgar/data"
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

# SEC requires a real identifying User-Agent — replace with your own contact.
SEC_HEADERS = {"User-Agent": "Captrion Research Bot contact@example.com"}


class DocumentIngestionError(Exception):
    """Raised when a document source can't be fetched."""


def _get_cik_for_ticker(ticker: str) -> str:
    response = requests.get(SEC_TICKER_MAP_URL, headers=SEC_HEADERS, timeout=10)
    response.raise_for_status()
    data = response.json()

    ticker_upper = ticker.upper()
    for entry in data.values():
        if entry["ticker"].upper() == ticker_upper:
            return str(entry["cik_str"]).zfill(10)

    raise DocumentIngestionError(f"No CIK found for ticker '{ticker}'")


def fetch_latest_sec_filings(ticker: str) -> list[dict[str, Any]]:
    """
    Fetch the most recent 10-K and 10-Q filing text for a ticker.

    Returns a list of up to 2 documents (one 10-K, one 10-Q), each with
    the raw filing text and metadata.
    """
    try:
        cik = _get_cik_for_ticker(ticker)
    except Exception as exc:
        raise DocumentIngestionError(f"CIK lookup failed for '{ticker}': {exc}") from exc

    submissions_url = SEC_SUBMISSIONS_URL.format(cik=cik)
    response = requests.get(submissions_url, headers=SEC_HEADERS, timeout=10)
    response.raise_for_status()
    filings = response.json().get("filings", {}).get("recent", {})

    forms = filings.get("form", [])
    accession_numbers = filings.get("accessionNumber", [])
    primary_documents = filings.get("primaryDocument", [])
    filing_dates = filings.get("filingDate", [])

    documents: list[dict[str, Any]] = []
    for form_type in ("10-K", "10-Q"):
        for i, form in enumerate(forms):
            if form != form_type:
                continue
            accession_no_dashes = accession_numbers[i].replace("-", "")
            filing_url = (
                f"{SEC_ARCHIVES_BASE}/{int(cik)}/{accession_no_dashes}/"
                f"{primary_documents[i]}"
            )
            try:
                filing_response = requests.get(filing_url, headers=SEC_HEADERS, timeout=15)
                filing_response.raise_for_status()
            except Exception:
                logger.exception("Failed to fetch filing %s for %s", filing_url, ticker)
                continue

            documents.append(
                {
                    "source": "sec_filing",
                    "doc_type": form_type,
                    "ticker": ticker.upper(),
                    "date": filing_dates[i],
                    "raw_text": filing_response.text,
                    "doc_id": f"{ticker.upper()}-{form_type}-{accession_numbers[i]}",
                }
            )
            break  # only the most recent of this form type

    if not documents:
        raise DocumentIngestionError(f"No 10-K/10-Q filings found for '{ticker}'")

    return documents


def fetch_recent_news(ticker: str, limit: int = 20) -> list[dict[str, Any]]:
    """Fetch recent news + sentiment for a ticker via Alpha Vantage."""
    settings = get_settings()
    if not settings.alpha_vantage_api_key:
        raise DocumentIngestionError("ALPHA_VANTAGE_API_KEY is not set")

    params = {
        "function": "NEWS_SENTIMENT",
        "tickers": ticker.upper(),
        "apikey": settings.alpha_vantage_api_key,
        "limit": str(limit),
    }
    response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=15)
    response.raise_for_status()
    payload = response.json()

    feed = payload.get("feed", [])
    documents: list[dict[str, Any]] = []
    for i, item in enumerate(feed):
        text = f"{item.get('title', '')}. {item.get('summary', '')}"
        documents.append(
            {
                "source": "news",
                "doc_type": "news_article",
                "ticker": ticker.upper(),
                "date": item.get("time_published", "")[:8],
                "raw_text": text,
                "doc_id": f"{ticker.upper()}-news-{i}-{item.get('title', '')[:30]}",
            }
        )
    return documents


def fetch_all_documents(ticker: str) -> list[dict[str, Any]]:
    """
    Fetch everything Phase 1 ingests for a ticker: latest SEC filings +
    recent news. Partial failures (e.g. news source down) don't block
    the whole ingestion — we log and continue with what we have.
    """
    documents: list[dict[str, Any]] = []

    try:
        documents.extend(fetch_latest_sec_filings(ticker))
    except DocumentIngestionError:
        logger.exception("SEC filing fetch failed for %s", ticker)

    try:
        documents.extend(fetch_recent_news(ticker))
    except DocumentIngestionError:
        logger.exception("News fetch failed for %s", ticker)

    if not documents:
        raise DocumentIngestionError(f"No documents could be fetched for '{ticker}'")

    return documents