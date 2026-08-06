"""
Local embedding generation via sentence-transformers.

Loaded once and cached — the model (~1.3GB for bge-large-en-v1.5) is
downloaded on first use and cached locally by the library afterward.
"""

from __future__ import annotations

from functools import lru_cache

from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL_NAME = "BAAI/bge-large-en-v1.5"
EMBEDDING_DIMENSION = 1024  # bge-large-en-v1.5 output dimension


@lru_cache
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of text chunks. Returns one vector per input text."""
    if not texts:
        return []
    model = get_embedding_model()
    vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return [v.tolist() for v in vectors]


def embed_query(query: str) -> list[float]:
    """Embed a single query string for retrieval."""
    return embed_texts([query])[0]