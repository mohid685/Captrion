"""
Pinecone client setup.

Phase 0 only needs a connection and a health check — no real embeddings
yet. The RAG layer (Phase 1) will add upsert/query methods and create
the actual index schema (dimension depends on the embedding model we
pick then, e.g. 1024 for BGE-M3).
"""

from __future__ import annotations

import logging

from pinecone import Pinecone

from app.config import get_settings

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
    """
    Confirms we can reach Pinecone and reports whether our target index
    already exists. Does NOT create the index — that happens in Phase 1
    once we know the embedding dimension.
    """
    settings = get_settings()
    pc = get_pinecone_client()

    existing_indexes = [index["name"] for index in pc.list_indexes()]
    target_exists = settings.pinecone_index_name in existing_indexes

    return {
        "connected": True,
        "existing_indexes": existing_indexes,
        "target_index": settings.pinecone_index_name,
        "target_index_exists": target_exists,
    }