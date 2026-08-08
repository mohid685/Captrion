from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agentic.agent import ask_agentic_advisor
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


@router.post("/{ticker}/ask-agentic")
def ask_agentic(ticker: str, request: AskRequest) -> dict[str, Any]:
    try:
        return ask_agentic_advisor(ticker, request.question)
    except LLMClientError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc