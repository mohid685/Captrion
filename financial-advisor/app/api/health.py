from fastapi import APIRouter, HTTPException

from app.core.vector_store import VectorStoreError, check_connection

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    """Basic liveness check — no dependencies."""
    return {"status": "ok"}


@router.get("/health/vector-store")
def health_check_vector_store() -> dict[str, object]:
    """Confirms the app can reach Pinecone."""
    try:
        return check_connection()
    except VectorStoreError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc