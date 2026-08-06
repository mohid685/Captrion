"""
Text cleaning and chunking.

Strips HTML/boilerplate from raw source text, then splits into
overlapping chunks sized for retrieval (roughly 300-500 tokens, using
a word-count proxy since we don't need exact tokenizer parity here).
"""

from __future__ import annotations

import re

_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")


def clean_text(raw: str) -> str:
    """Strip HTML tags and collapse whitespace."""
    no_tags = _TAG_RE.sub(" ", raw)
    return _WHITESPACE_RE.sub(" ", no_tags).strip()


def chunk_text(
    text: str,
    chunk_size_words: int = 400,
    overlap_words: int = 50,
) -> list[str]:
    """
    Split cleaned text into overlapping word-count chunks.

    Overlap preserves context across chunk boundaries so a fact split
    across two chunks is still retrievable from either.
    """
    words = text.split()
    if not words:
        return []

    if chunk_size_words <= overlap_words:
        raise ValueError("chunk_size_words must be greater than overlap_words")

    chunks: list[str] = []
    step = chunk_size_words - overlap_words
    for start in range(0, len(words), step):
        chunk_words = words[start : start + chunk_size_words]
        if not chunk_words:
            break
        chunks.append(" ".join(chunk_words))
        if start + chunk_size_words >= len(words):
            break
    return chunks