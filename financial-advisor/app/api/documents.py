import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.core.embeddings import embed_query, embed_texts
from app.core.vector_store import VectorStoreError, query_similar, upsert_chunks
from app.ingestion.chunking import chunk_text, clean_text
from app.ingestion.documents import DocumentIngestionError, fetch_all_documents

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/{ticker}/ingest")
def ingest_documents(ticker: str) -> dict[str, Any]:
    """Fetch, clean, chunk, embed, and index documents for a ticker."""
    try:
        raw_documents = fetch_all_documents(ticker)
    except DocumentIngestionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    all_chunk_texts: list[str] = []
    all_chunk_metadata: list[dict[str, Any]] = []

    for doc in raw_documents:
        cleaned = clean_text(doc["raw_text"])
        pieces = chunk_text(cleaned)
        for piece in pieces:
            all_chunk_texts.append(piece)
            all_chunk_metadata.append(
                {
                    "text": piece,
                    "source": doc["source"],
                    "doc_type": doc["doc_type"],
                    "date": doc["date"],
                    "doc_id": doc["doc_id"],
                }
            )

    if not all_chunk_texts:
        raise HTTPException(status_code=422, detail="No text extracted from fetched documents")

    vectors = embed_texts(all_chunk_texts)

    pinecone_chunks = [
        {
            "id": f"{ticker.upper()}-{uuid.uuid4().hex[:12]}",
            "values": vector,
            "metadata": metadata,
        }
        for vector, metadata in zip(vectors, all_chunk_metadata)
    ]

    try:
        upserted_count = upsert_chunks(ticker, pinecone_chunks)
    except VectorStoreError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return {
        "ticker": ticker.upper(),
        "documents_fetched": len(raw_documents),
        "chunks_indexed": upserted_count,
    }


@router.get("/{ticker}/search")
def search_documents(
    ticker: str,
    query: str = Query(..., min_length=1),
    top_k: int = Query(5, ge=1, le=20),
) -> list[dict[str, Any]]:
    """Semantic search over previously ingested documents for a ticker."""
    query_vector = embed_query(query)
    try:
        return query_similar(ticker, query_vector, top_k=top_k)
    except VectorStoreError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc