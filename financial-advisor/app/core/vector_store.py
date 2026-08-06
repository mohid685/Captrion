"""
Pinecone client, index management, and vector operations.

Phase 0 only had a connection health check. Phase 1 adds index creation
(now that we know the embedding dimension), upsert, and query.
"""

from __future__ import annotations

import logging
from typing import Any

from pinecone import Pinecone, ServerlessSpec

from app.config import get_settings
from app.core.embeddings import EMBEDDING_DIMENSION

logger = logging.getLogger(__name__)


class VectorStoreError(Exception):
    """Raised when Pinecone isn't reachable or isn't configured."""


def get_pinecone_client() -> Pinecone:
    settings = get_settings()
    if not settings.pinecone_api_key:
        raise VectorStoreError(
            "PINECONE_API_KEY is not set. Add it to your .env file."
        )
    return Pinecone(api_key=settings.pinecone_api_key)


def check_connection() -> dict[str, object]:
    settings = get_settings()
    pc = get_pinecone_client()
    existing_indexes = [index["name"] for index in pc.list_indexes()]
    return {
        "connected": True,
        "existing_indexes": existing_indexes,
        "target_index": settings.pinecone_index_name,
        "target_index_exists": settings.pinecone_index_name in existing_indexes,
    }


def ensure_index() -> None:
    """Create the target Pinecone index if it doesn't already exist."""
    settings = get_settings()
    pc = get_pinecone_client()
    existing = [index["name"] for index in pc.list_indexes()]

    if settings.pinecone_index_name in existing:
        return

    pc.create_index(
        name=settings.pinecone_index_name,
        dimension=EMBEDDING_DIMENSION,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region=settings.pinecone_environment),
    )


def upsert_chunks(ticker: str, chunks: list[dict[str, Any]]) -> int:
    """
    Upsert embedded chunks into the ticker's namespace.

    Each chunk dict must have: id, values (embedding), and metadata
    (text, source, doc_type, date, ticker).
    """
    if not chunks:
        return 0

    ensure_index()
    settings = get_settings()
    pc = get_pinecone_client()
    index = pc.Index(settings.pinecone_index_name)

    index.upsert(vectors=chunks, namespace=ticker.upper())
    return len(chunks)


def query_similar(ticker: str, query_vector: list[float], top_k: int = 5) -> list[dict[str, Any]]:
    """Semantic search within a ticker's namespace."""
    settings = get_settings()
    pc = get_pinecone_client()
    index = pc.Index(settings.pinecone_index_name)

    results = index.query(
        vector=query_vector,
        top_k=top_k,
        namespace=ticker.upper(),
        include_metadata=True,
    )

    return [
        {
            "score": match["score"],
            "text": match["metadata"].get("text"),
            "source": match["metadata"].get("source"),
            "doc_type": match["metadata"].get("doc_type"),
            "date": match["metadata"].get("date"),
        }
        for match in results.get("matches", [])
    ]