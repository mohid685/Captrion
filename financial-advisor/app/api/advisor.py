from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agentic.agent import ask_agentic_advisor
from app.api.deps import get_current_user
from app.core.db import get_db
from app.core.llm_client import LLMClientError
from app.core.vector_store import VectorStoreError
from app.models.memory import Conversation, PortfolioItem
from app.models.user import User, UserProfile
from app.reasoning.advisor import ask_advisor

router = APIRouter(prefix="/advisor", tags=["advisor"])


class AskRequest(BaseModel):
    question: str


def _build_user_context(current_user: User, ticker: str, db: Session) -> dict[str, Any]:
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    holding = (
        db.query(PortfolioItem)
        .filter(PortfolioItem.user_id == current_user.id, PortfolioItem.ticker == ticker.upper())
        .first()
    )

    context: dict[str, Any] = {}
    if profile:
        context["risk_tolerance"] = profile.risk_tolerance
        context["investment_goals"] = profile.investment_goals
    if holding:
        context["holding"] = {"shares": holding.shares, "cost_basis": holding.cost_basis}
    return context


def _log_conversation(
    db: Session, user_id: str, ticker: str, question: str, answer: str, endpoint_used: str
) -> str:
    conversation = Conversation(
        user_id=user_id,
        ticker=ticker.upper(),
        question=question,
        answer=answer,
        endpoint_used=endpoint_used,
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation.id


@router.post("/{ticker}/ask")
def ask(
    ticker: str,
    request: AskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    user_context = _build_user_context(current_user, ticker, db)
    try:
        result = ask_advisor(ticker, request.question, user_context=user_context)
    except LLMClientError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except VectorStoreError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    _log_conversation(db, current_user.id, ticker, request.question, result["answer"], "ask")
    return result


@router.post("/{ticker}/ask-agentic")
def ask_agentic(
    ticker: str,
    request: AskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    user_context = _build_user_context(current_user, ticker, db)
    try:
        result = ask_agentic_advisor(ticker, request.question, user_context=user_context)
    except LLMClientError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    _log_conversation(db, current_user.id, ticker, request.question, result["answer"], "ask-agentic")
    return result