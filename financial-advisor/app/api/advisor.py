from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.llm_client import LLMClientError
from app.core.vector_store import VectorStoreError
from app.reasoning.advisor import ask_advisor

router = APIRouter(prefix="/advisor", tags=["advisor"])


class AskRequest(BaseModel):
    question: str


@router.post("/{ticker}/ask")
def ask(ticker: str, request: AskRequest) -> dict[str, Any]:
    try:
        return ask_advisor(ticker, request.question)
    except LLMClientError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except VectorStoreError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc